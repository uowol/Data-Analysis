import os
import re
import time
import pandas as pd
import numpy as np
from pathlib import Path
import xgboost as xgb

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
    test = pd.read_csv(test_filepath)

    PassengerId = test['PassengerId']
    
    np.random.seed(params.get('random_state', 42))
    
    def get_title(name):
        title_search = re.search(r' ([A-Za-z]+)\.', name)
        if title_search:
            return title_search.group(1)
        return ""
    
    ticket_cleansed = train.Ticket.str.replace('.', '').str.upper()
    ticket_header = ticket_cleansed.apply(
        lambda x: x.split(' ')[0] if len(x.split(' ')) > 1 else 'Unknown'
    )
    header_counts = ticket_header.value_counts()
    rare_headers = header_counts[header_counts < 5].index
    ticket_header = ticket_header.replace(list(rare_headers), 'Unknown')
    known_headers = set(ticket_header.unique())
    train['TicketHeader'] = ticket_header
    test_ticket_cleansed = test.Ticket.str.replace('.', '').str.upper()
    test_ticket_header = test_ticket_cleansed.apply(
        lambda x: x.split(' ')[0] if len(x.split(' ')) > 1 else 'Unknown'
    )
    test_ticket_header = test_ticket_header.apply(
        lambda x: x if x in known_headers else 'Unknown'
    )
    test['TicketHeader'] = test_ticket_header
    
    full_data = [train, test]
    ticket_cat_dtype = ticket_header_cat_dtype = None
    for data in full_data:
        data['TicketType'] = data['Ticket'].apply(lambda x: x[0:3])
        if ticket_cat_dtype is None:
            ticket_cat_dtype = pd.CategoricalDtype(
                categories=sorted(data['TicketType'].unique()),
                ordered=True
            )
        data['TicketType'] = data['TicketType'].astype(ticket_cat_dtype)
        data['TicketType'] = data['TicketType'].cat.codes
        
        if ticket_header_cat_dtype is None:
            ticket_header_cat_dtype = pd.CategoricalDtype(
                categories=sorted(data['TicketHeader'].unique()),
                ordered=True
            )
        data['TicketHeader'] = data['TicketHeader'].astype(ticket_header_cat_dtype)
        data['TicketHeader'] = data['TicketHeader'].cat.codes
        
        data['WordsCount'] = data['Name'].apply(lambda x: len(x.split()))
        
        data['HasCabin'] = data['Cabin'].apply(lambda x: 0 if pd.isnull(x) else 1)
        
        data['FamilySize'] = data['SibSp'] + data['Parch'] + 1
        data['IsAlone'] = data['FamilySize'].apply(lambda x: 1 if x == 1 else 0)
        
        data['Embarked'] = data['Embarked'].fillna('S')
        
        data['Fare'] = data['Fare'].fillna(data['Fare'].median())
        
        data['CategoricalFare'] = pd.qcut(data['Fare'], 4)
        data['CategoricalFare'] = data['CategoricalFare'].cat.codes
        # train과 test 동일한 범주로 변환하기 위해 아래와 같이 수동으로 범주를 지정
        data.loc[ data['Fare'] <= 7.91, 'CategoricalFare'] = 0
        data.loc[(data['Fare'] > 7.91) & (data['Fare'] <= 14.454), 'CategoricalFare'] = 1
        data.loc[(data['Fare'] > 14.454) & (data['Fare'] <= 31), 'CategoricalFare'] = 2
        data.loc[ data['Fare'] > 31, 'CategoricalFare'] = 3
        
        age_avg = data['Age'].mean()
        age_std = data['Age'].std()
        age_null_count = data['Age'].isnull().sum()
        age_null_random_list = np.random.randint(int(age_avg - age_std), int(age_avg + age_std), size=age_null_count)
        data.loc[np.isnan(data['Age']), 'Age'] = age_null_random_list
        data['Age'] = data['Age'].astype(int)
        
        data['CategoricalAge'] = pd.cut(data['Age'], 5)
        data['CategoricalAge'] = data['CategoricalAge'].cat.codes
        # train과 test 동일한 범주로 변환하기 위해 아래와 같이 수동으로 범주를 지정
        data.loc[ data['Age'] <= 16, 'CategoricalAge'] = 0
        data.loc[(data['Age'] > 16) & (data['Age'] <= 32), 'CategoricalAge'] = 1
        data.loc[(data['Age'] > 32) & (data['Age'] <= 48), 'CategoricalAge'] = 2
        data.loc[(data['Age'] > 48) & (data['Age'] <= 64), 'CategoricalAge'] = 3
        data.loc[ data['Age'] > 64, 'CategoricalAge'] = 4
                
        data['Title'] = data['Name'].apply(get_title)
        data['Title'] = data['Title'].replace(['Lady', 'Countess','Capt', 'Col','Don', 'Dr', 'Major', 'Rev', 'Sir', 'Jonkheer', 'Dona'], 'Rare')
        data['Title'] = data['Title'].replace('Mlle', 'Miss')
        data['Title'] = data['Title'].replace('Ms', 'Miss')
        data['Title'] = data['Title'].replace('Mme', 'Mrs')

        data['Sex'] = data['Sex'].map({
            'female': 0, 'male': 1
        }).astype(int)
        
        title_mapping = {"Mr": 1, "Miss": 2, "Mrs": 3, "Master": 4, "Rare": 5}
        data['Title'] = data['Title'].map(title_mapping)
        data['Title'] = data['Title'].fillna(0)
        
        data['Embarked'] = data['Embarked'].map({
            'S': 0, 'C': 1, 'Q': 2
        }).astype(int)
        
    drop_elements = [
        "PassengerId", "Name", "Ticket", "Cabin", "SibSp", "TicketType"
    ]
    train = train.drop(drop_elements, axis=1)
    test = test.drop(drop_elements, axis=1)
    print("Train columns:", train.columns.tolist())
    print("Test columns:", test.columns.tolist())
    
    y_train = train['Survived'].values
    x_train = train.drop(['Survived'], axis=1).values
    x_test = test.values

    model = xgb.XGBClassifier(
        n_estimators=params.get('n_estimators', 100),
        learning_rate=params.get('learning_rate', 0.1),
        max_depth=params.get('max_depth', 4),
        min_child_weight=params.get('min_child_weight', 2),
        gamma=params.get('gamma', 0.9),
        subsample=params.get('subsample', 0.8),
        colsample_bytree=params.get('colsample_bytree', 0.8),
        scale_pos_weight=params.get('scale_pos_weight', 1),
        random_state=params.get('random_state', 42),
        objective='binary:logistic',
        verbosity=1
    ).fit(x_train, y_train)

    y_pred = model.predict(x_test)

    feature_importances = model.feature_importances_
    feature_names = test.columns.tolist()
    feature_importance_df = pd.DataFrame({
        'Feature': feature_names,
        'Importance': feature_importances
    }).sort_values(by='Importance', ascending=False).reset_index(drop=True)
    print("Feature Importances:")
    print(feature_importance_df)

    response = pd.DataFrame({
        'PassengerId': PassengerId,
        'Survived': y_pred
    })

    response.to_csv(output_filepath, index=False)
        
    return ResponseModeling(
        status="success",
        **message.model_dump()
    )


if __name__ == "__main__":    
    message = RequestModeling(
        train_filepath="data/titanic/raw/train.csv",
        test_filepath="data/titanic/raw/test.csv",
        output_filepath="data/titanic/raw/output.csv",
        model_type="xgboost",
    )
    predict(message, params={})
    
