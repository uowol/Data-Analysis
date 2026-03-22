import os
import time
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier

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
    train['Sex'] = train['Sex'].apply(lambda x: 1 if x == 'male' else 0)
    test = pd.read_csv(test_filepath)
    test['Sex'] = test['Sex'].apply(lambda x: 1 if x == 'male' else 0)
    
    features = ["Pclass", "Sex", "SibSp", "Parch"]
    X_train, y_train = train[features], train['Survived']
    X_test = test[features]
    
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=5,
        random_state=42,
        verbose=1
    )
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    
    output = pd.DataFrame({'PassengerId': test.PassengerId, 'Survived': predictions})
    output.to_csv(output_filepath, index=False)
    print("Your submission was successfully saved!")
    
    
    return ResponseModeling(
        status="success",
        **message.model_dump()
    )


if __name__ == "__main__":    
    message = RequestModeling(
        train_filepath="data/titanic/raw/train.csv",
        test_filepath="data/titanic/raw/test.csv",
        output_filepath="data/titanic/raw/output.csv",
        model_type="randomforest",
    )
    predict(message)
    
