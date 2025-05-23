import os
import time
import pandas as pd
from pathlib import Path
from src.formats import (
    RequestModeling, ResponseModeling
)


def predict(message: RequestModeling, params: dict = None) -> ResponseModeling:
    os.makedirs(Path(message.output_filepath).parent, exist_ok=True)
    assert os.path.exists(message.train_filepath), f"Train file {message.train_filepath} does not exist"
    assert os.path.exists(message.test_filepath), f"Test file {message.test_filepath} does not exist"
    
    response = None
    train = pd.read_csv(message.train_filepath)
    test = pd.read_csv(message.test_filepath)

    train['Title'] = train['Name'].str.split(',', expand=True)[1].str.split('.', expand=True)[0].str.strip()
    title_survived = (train.groupby('Title')['Survived'].mean() > 0.6).reset_index().rename(
        columns={0:'title', 'Survived': 'Predicted_Survived'}
    )

    test['Title'] = test['Name'].str.split(',', expand=True)[1].str.split('.', expand=True)[0].str.strip()
    test = test.merge(title_survived, on='Title', how='left')
    test['Predicted_Survived'] = test['Predicted_Survived'].fillna(
        test['Sex'].map({'female': True, 'male': False})
    ).infer_objects(copy=False)
    test['Predicted_Survived'] = test['Predicted_Survived'].astype(int)

    response = test[['PassengerId', 'Predicted_Survived']].rename(
        columns={'Predicted_Survived': 'Survived'}
    )
    response.to_csv(os.path.join(message.output_filepath), index=False)

    return ResponseModeling(
        status="success",
        **message.model_dump()
    )