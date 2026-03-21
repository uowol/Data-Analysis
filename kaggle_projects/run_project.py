import argparse
import importlib.util
import subprocess
import sys
import yaml
from pathlib import Path

# kaggle_projects/ 를 sys.path에 추가하여 base.*, titanic.* 등의 import를 가능하게 함
sys.path.insert(0, str(Path(__file__).resolve().parent))


def init():
    parser = argparse.ArgumentParser(description='Run a project')
    parser.add_argument('--project_name', type=str, metavar="NAME", required=True, help='Name of the project to run')
    parser.add_argument('--pipeline_name', type=str, metavar="NAME", default="default", help='Name of the pipeline to run (default: default)')
    args = parser.parse_args()

    return args


def main():
    args = init()

    base_dir = Path(__file__).resolve().parent / args.project_name
    pipeline_path = base_dir / "src" / "pipelines" / args.pipeline_name / "pipeline.py"
    config_path = base_dir / "src" / "pipelines" / args.pipeline_name / "pipeline.yaml"
    with open(config_path, 'r') as fp:
        config = yaml.safe_load(fp)
        config = config if config is not None else {}

    # -- install dependencies
    requirements_path = base_dir / "requirements.txt"
    if requirements_path.exists():
        subprocess.check_call(["uv", "pip", "install", "-r", str(requirements_path)])

    # -- run pipeline module
    spec = importlib.util.spec_from_file_location("pipeline", pipeline_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pipeline = module.Pipeline(**config)
    pipeline()


if __name__ == '__main__':
    main()
