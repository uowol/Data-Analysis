import os
import yaml
from pathlib import Path
from typing import List

if __name__ == "__main__":    
    # Test the component
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from src.components import base
from src.models.base import predict as BasePredict
from src.models.title_prediction import predict as TitlePredictionPredict
from src.models.logistic_regression import predict as LogisticRegressionPredict
from src.formats import RequestModeling, ResponseModeling, ResponseMessage

class ComponentType(base.ComponentType):
    pass    

class Component(base.Component):
    def init(self, **config):
        if config:
            self.config = ComponentType(**config)
        else:
            with open(os.path.join(Path(__file__).parent, "component.yaml"), "r") as fp:
                self.config = yaml.safe_load(fp)
                self.config = self.config if self.config is not None else {}

    def call(self, message: RequestModeling,
             *, upstream_events: List[ResponseMessage] = []) -> ResponseModeling:
        if upstream_events:
            print("# [INFO] upstream_events: ", upstream_events)
            
        if message.model_type == "title_prediction":
            return TitlePredictionPredict(message, self.config[message.model_type]['params'])
        if message.model_type == 'logistic_regression':
            return LogisticRegressionPredict(message, self.config[message.model_type]['params'])
        
        return BasePredict(message)


if __name__ == "__main__":    
    # Test the component
    message = RequestModeling(
        train_filepath="data/titanic/raw/train.csv",
        test_filepath="data/titanic/raw/test.csv",
        output_filepath="data/titanic/raw/output.csv",
        model_type="logistic_regression",
    )
    component = Component()
    response = component(message)
    print(response)