import os
import zipfile
import subprocess
import glob
import pandas as pd
import logging
import ydata_profiling
from pathlib import Path

from base.src.formats import (
    RequestDownloadData, ResponseDownloadData,
    RequestExtractInfo, ResponseExtractInfo,
)


def get_logger() -> logging.Logger:
    base_dir = Path('./')
    log_dir = base_dir / 'outputs/logs'

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    
    logger = logging.getLogger(name="kaggle")
    logger.setLevel(logging.INFO)
    
    os.makedirs(log_dir, exist_ok=True)

    file_handler = logging.FileHandler(os.path.join(log_dir, f"info.log"))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    
    return logger


def download_data(message: RequestDownloadData) -> ResponseDownloadData:
    base_dir = Path('./')
    local_path = base_dir / message.local_path

    os.makedirs(local_path, exist_ok=True)

    if message.is_competition:
        subprocess.run(["kaggle", "competitions", "download", "-c", message.url, "-p", local_path])
    else:
        subprocess.run(["kaggle", "datasets", "download", message.url, "-p", local_path])
    local_zip_files = glob.glob(f"{local_path}/*.zip")
    for file_path in local_zip_files:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(local_path)
        subprocess.run(["rm", file_path])
    return ResponseDownloadData(
        status="success",
        **message.model_dump()
    )
    
    
def extract_data_info(message: RequestExtractInfo) -> ResponseExtractInfo:
    base_dir = Path('./')
    local_path = base_dir / message.local_path
    output_path = base_dir / message.output_path

    os.makedirs(output_path, exist_ok=True)

    local_csv_files = glob.glob(f"{local_path}/*.csv")
    for file_path in local_csv_files:
        if 'test' in file_path or 'submission' in file_path:
            continue
        df = pd.read_csv(file_path)
        profile = ydata_profiling.ProfileReport(df)
        profile.to_file(os.path.join(output_path, f"{os.path.basename(file_path).replace(".csv", '')}_profile.html"))
        json_data = profile.to_json()
        with open(os.path.join(output_path, f"{os.path.basename(file_path).replace(".csv", '')}_profile.json"), "w") as f:
            f.write(json_data)
    return ResponseExtractInfo(
        status="success",
        **message.model_dump()
    )   
    