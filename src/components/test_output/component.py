import os
import yaml
from pathlib import Path
from typing import List

from src.components import base
from src.functions import test_output
from src.formats import RequestTestOutput, ResponseTestOutput, ResponseMessage

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

    def call(self, message: RequestTestOutput,
             *, upstream_events: List[ResponseMessage] = []) -> ResponseTestOutput:
        if upstream_events:
            print("# [INFO] upstream_events: ", upstream_events)
        return test_output(message)