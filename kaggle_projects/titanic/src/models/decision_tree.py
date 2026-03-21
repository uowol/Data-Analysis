import os
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from titanic.src.formats import (
    RequestModeling, ResponseModeling
)


def predict(message: RequestModeling, params: dict = {}) -> ResponseModeling:
    base_dir = Path('./')
    output_filepath = base_dir / message.output_filepath
    train_filepath = base_dir / message.train_filepath
    test_filepath = base_dir / message.test_filepath

    os.makedirs(output_filepath.parent, exist_ok=True)
    assert os.path.exists(train_filepath), f"Train file {train_filepath} does not exist"
    assert os.path.exists(test_filepath), f"Test file {test_filepath} does not exist"
    
    train = pd.read_csv(train_filepath)
    X_train, y_train = train.drop(columns=['Survived']), train['Survived']

    # PassengerId와 Name 모두 고유값이나, PassengerId는 단순한 인덱스이므로 제거
    X_train = X_train.drop(columns=['PassengerId'], axis=1)

    # 결정트리는 연속형 변수에 대한 최적의 분할을 찾기 때문에 Age는 연속형 변수로 유지
    # 결측값은 이름의 title을 이용하여 채우고, title이 Unseen인 경우가 있을 수 있으므로 이 경우 Pclass의 평균값으로 채운다.
    X_train['Title'] = X_train['Name'].str.split(',', expand=True)[1].str.split('.', expand=True)[0].str.strip()
    X_train['Age'].fillna(X_train.groupby('Title').Age.transform('mean'), inplace=True)
    X_train['Age'].fillna(X_train.groupby('Pclass').Age.transform('mean'), inplace=True)
    age_bins = [0, 10, 20, 30, 40, 50, 60, 100]
    age_labels = ['0-10', '10-20', '20-30', '30-40', '40-50', '50-60', '60+']
    X_train['AgeGroup'] = pd.cut(X_train['Age'], bins=age_bins, labels=age_labels)
    
    # SibSp와 Parch를 그대로 사용하되, 동반자 여부 변수를 하나 추가
    X_train['HasFamily'] = np.where((X_train['SibSp'] > 0) | (X_train['Parch'] > 0), 1, 0)
    X_train['FamilySize'] = X_train['SibSp'] + X_train['Parch']
    X_train['FamilySize'] = X_train['FamilySize'].replace([x for x in range(4, 11)], 4)
    
    # Fare은 신분을 간접적으로 설명할 수 있을 것이라 생각하여 사용, 그러나 한 번에 결제한 경우 중복 기록해두었기 때문에 수정이 필요
    cleansed_ticket = X_train.Ticket.str.replace('.', '').str.upper()
    ticket_counts = cleansed_ticket.value_counts()
    X_train['DividedFare'] = cleansed_ticket.map(ticket_counts)
    
    # Ticket은 객실, 동행자, 요금, 어디서 탑승했는지에 대한 정보를 포함, 샘플이 너무 적은 경우는 Unknown으로 대체
    X_train['TicketCleansed'] = cleansed_ticket
    X_train['TicketHeader'] = X_train['TicketCleansed'].apply(
        lambda x: x.split(' ')[0] if len(x.split(' ')) > 1 else 'Unknown'
    )
    header_counts = X_train['TicketHeader'].value_counts()
    rare_headers = header_counts[header_counts < 5].index
    X_train['TicketHeader'] = X_train['TicketHeader'].replace(list(rare_headers), 'Unknown')
    known_headers = set(X_train['TicketHeader'].unique())
    
    num_cols = ['DividedFare', 'SibSp', 'Parch', 'Age']
    cat_cols = ['Sex', 'AgeGroup', 'FamilySize', 'Pclass', 'TicketHeader']
        
    X_train_dummies = pd.get_dummies(X_train[cat_cols], columns=cat_cols, drop_first=True)
    dummy_cat_cols = X_train_dummies.columns.tolist()
    X_train = pd.concat([X_train[num_cols], X_train_dummies], axis=1)

    preprocess = ColumnTransformer(
        [('num', StandardScaler(), num_cols),
        ('cat', 'passthrough', dummy_cat_cols)]
    )

    model = Pipeline([
        ('prep', preprocess),
        ('dt', DecisionTreeClassifier(
            criterion=params.get('criterion', 'entropy'),
            max_depth=params.get('max_depth', None),
            min_samples_split=params.get('min_samples_split', 2),
            min_samples_leaf=params.get('min_samples_leaf', 1),
            random_state=params.get('random_state', 42)
        ))
    ])
    
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=params.get('random_state', 42))
    cv_scores = cross_val_score(model, X_train, y_train, cv=skf, scoring='accuracy', error_score="raise",)
    print(f"Cross-validation Accuracy Scores: {cv_scores}")
    print(f"Mean Accuracy: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    
    model.fit(X_train, y_train)
    importance = pd.Series(
        model.named_steps['dt'].feature_importances_,
        index=X_train.columns
    ).sort_values(ascending=False)
    print(importance)

    X_test = pd.read_csv(test_filepath)
    X_test_PassengerId = X_test['PassengerId']
    X_test['Title'] = X_test['Name'].str.split(',', expand=True)[1].str.split('.', expand=True)[0].str.strip()
    X_test['Age'].fillna(X_test.groupby('Title').Age.transform('mean'), inplace=True)
    X_test['Age'].fillna(X_test.groupby('Pclass').Age.transform('mean'), inplace=True)
    X_test['AgeGroup'] = pd.cut(X_test['Age'], bins=age_bins, labels=age_labels)
    X_test['HasFamily'] = np.where((X_test['SibSp'] > 0) | (X_test['Parch'] > 0), 1, 0)  
    X_test['FamilySize'] = X_test['SibSp'] + X_test['Parch']
    X_test['FamilySize'] = X_test['FamilySize'].replace([x for x in range(4, 11)], 4)  
    cleansed_ticket = X_test.Ticket.str.replace('.', '').str.upper()
    ticket_counts = cleansed_ticket.value_counts()
    X_test['DividedFare'] = cleansed_ticket.map(ticket_counts)
    X_test['TicketCleansed'] = cleansed_ticket
    X_test['TicketHeader'] = X_test['TicketCleansed'].apply(
        lambda x: x.split(' ')[0] if len(x.split(' ')) > 1 else 'Unknown'
    )
    X_test['TicketHeader'] = X_test['TicketHeader'].apply(
        lambda x: x if x in known_headers else 'Unknown'
    )
    
    X_test_dummies = pd.get_dummies(X_test[cat_cols], columns=cat_cols, drop_first=True)
    X_test = pd.concat([X_test[num_cols], X_test_dummies], axis=1)
    y_pred = model.predict(X_test)
    response = pd.DataFrame({
        'PassengerId': X_test_PassengerId,
        'Survived': y_pred
    })
    response.to_csv(output_filepath, index=False)

    return ResponseModeling(
        status="success",
        **message.model_dump()
    )