import os
import zipfile
import subprocess
import ydata_profiling
import time
import glob
import pandas as pd

from src.formats import (
    RequestDownloadData, ResponseDownloadData,
    RequestExtractInfo, ResponseExtractInfo,
    RequestPreprocessData, ResponsePreprocessData,
)


def download_data(message: RequestDownloadData) -> ResponseDownloadData:
    subprocess.run(["kaggle", "datasets", "download", message.url, "-p", message.local_path])
    local_zip_files = glob.glob(f"{message.local_path}/*.zip")
    for file_path in local_zip_files:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(message.local_path)
        subprocess.run(["rm", file_path])
    return ResponseDownloadData(
        status="success",
        url=message.url,
        local_path=message.local_path
    )
    
    
def extract_data_info(message: RequestExtractInfo) -> ResponseExtractInfo:
    local_csv_files = glob.glob(f"{message.local_path}/*.csv")
    for file_path in local_csv_files:
        df = pd.read_csv(file_path)
        profile = ydata_profiling.ProfileReport(df)
        profile.to_file(os.path.join(message.output_path, f"{os.path.basename(file_path).replace(".csv", '')}_profile.html"))
        json_data = profile.to_json()
        with open(os.path.join(message.output_path, f"{os.path.basename(file_path).replace(".csv", '')}_profile.json"), "w") as f:
            f.write(json_data)
    return ResponseExtractInfo(
        status="success",
        local_path=message.local_path,
        output_path=message.output_path
    )   
    
    
def preprocess_data(message: RequestPreprocessData) -> ResponsePreprocessData:
    local_csv_files = glob.glob(f"{message.local_path}/*.csv")
    log_output_path = os.path.join(message.output_path, "log.txt")
    for file_path in local_csv_files:
        df = pd.read_csv(file_path)
        log_message = f"Preprocess data: {file_path}\n"
        if message.target_columns:
            _removed_columns = [column for column in df.columns if column not in message.target_columns]
            log_message += f"Removed non-target columns, #: {len(_removed_columns)}\n"
            for column in _removed_columns:
                log_message += f"\t{column}\n"
            df = df[message.target_columns]
        if message.outlier:
            for outlier in message.outlier:
                assert 'method' in outlier, "'method' field is required"
                assert 'value' in outlier, "'value' field is required"
                assert 'columns' in outlier, "'columns' field is required"
                if outlier["method"] == "remove-top-k":
                    log_message += f"Removed top {outlier['value']} rows based on {outlier['columns']}\n"
                    for temp in df.sort_values(by=outlier["columns"], ascending=False).iloc[:outlier["value"]].to_dict(orient="records"):
                        log_message += f"\t{temp}\n"
                    df = df.sort_values(by=outlier["columns"], ascending=False).iloc[outlier["value"]:].sort_index()
                elif outlier["method"] == "remove-bottom-k":
                    log_message += f"Removed bottom {outlier['value']} rows based on {outlier['columns']}\n"
                    for temp in df.sort_values(by=outlier["columns"], ascending=True).iloc[:outlier["value"]].to_dict(orient="records"):
                        log_message += f"\t{temp}\n"
                    df = df.sort_values(by=outlier["columns"], ascending=True).iloc[outlier["value"]:].sort_index()
                elif outlier["method"] == "remove-top-percent":
                    log_message += f"Removed top {outlier['value']}% rows based on {outlier['columns']}, #: {int(len(df) * outlier['value'])}\n"
                    for temp in df.sort_values(by=outlier["columns"], ascending=False).iloc[:int(len(df) * outlier["value"])].to_dict(orient="records"):
                        log_message += f"\t{temp}\n"
                    df = df.sort_values(by=outlier["columns"], ascending=False).iloc[int(len(df) * outlier["value"]):].sort_index()
                elif outlier["method"] == "remove-bottom-percent":
                    log_message += f"Removed bottom {outlier['value']}% rows based on {outlier['columns']}, #: {int(len(df) * outlier['value'])}\n"
                    for temp in df.sort_values(by=outlier["columns"], ascending=True).iloc[:int(len(df) * outlier["value"])].to_dict(orient="records"):
                        log_message += f"\t{temp}\n"
                    df = df.sort_values(by=outlier["columns"], ascending=True).iloc[int(len(df) * outlier["value"]):].sort_index()
                else:
                    raise ValueError(f"Unknown outlier method: {outlier['method']}")
            for missing in message.missing:
                assert 'method' in missing, "'method' field is required"
                assert 'columns' in missing, "'columns' field is required"
                if missing['columns'] == ['all']:
                    missing['columns'] = df.columns.values
                if missing["method"] == "drop-row":
                    log_message += f"Drop rows with missing values based on {missing['columns']}, #: {len(df) - len(df.dropna(subset=missing['columns']))}\n"
                    for temp in df[df[missing["columns"]].isnull().any(axis=1)].to_dict(orient="records"):
                        log_message += f"\t{temp}\n"
                    df = df.dropna(subset=missing["columns"])
                elif missing["method"] == "drop-column":
                    log_message += f"Drop columns with missing values, #: {len(df.columns) - len(df.dropna(axis=1).columns)}\n"
                    for temp in df.loc[:, df.isnull().any()].columns:
                        log_message += f"\t{temp}\n"
                    df = df.dropna(axis=1)
                elif missing["method"] == "fill-mean":
                    log_message += f"Fill missing values with mean based on {missing['columns']}\n"
                    for column in missing["columns"]:
                        log_message += f"\t{column}: {df[column].mean()}, #: {len(df[df[column].isnull()])}\n"
                        df[column].fillna(df[column].mean(), inplace=True)
                elif missing["method"] == "fill-median":
                    log_message += f"Fill missing values with median based on {missing['columns']}\n"
                    for column in missing["columns"]:
                        log_message += f"\t{column}: {df[column].median()}, #: {len(df[df[column].isnull()])}\n"
                        df[column].fillna(df[column].median(), inplace=True)
                elif missing["method"] == "fill-mode":
                    log_message += f"Fill missing values with mode based on {missing['columns']}\n"
                    for column in missing["columns"]:
                        log_message += f"\t{column}: {df[column].mode()[0]}, #: {len(df[df[column].isnull()])}\n"
                        df[column].fillna(df[column].mode()[0], inplace=True)
                elif missing["method"] == "fill-constant":
                    assert 'value' in missing, "'value' field is required"
                    log_message += f"Fill missing values with constant {missing['value']} based on {missing['columns']}\n"
                    for column in missing["columns"]:
                        log_message += f"\t{column}: {missing['value']}, #: {len(df[df[column].isnull()])}\n"
                        df[column].fillna(missing['value'], inplace=True)
                elif missing["method"] == "fill-forward":
                    log_message += f"Fill missing values with forward based on {missing['columns']}\n"
                    for column in missing["columns"]:
                        log_message += f"\t{column}, #: {len(df[df[column].isnull()])}\n"
                        df[column].fillna(method='ffill', inplace=True)
                elif missing["method"] == "fill-backward":
                    log_message += f"Fill missing values with backward based on {missing['columns']}\n"
                    for column in missing["columns"]:
                        log_message += f"\t{column}, #: {len(df[df[column].isnull()])}\n"
                        df[column].fillna(method='bfill', inplace=True)
                elif missing["method"] == "fill-interpolate":
                    log_message += f"Fill missing values with interpolate based on {missing['columns']}\n"
                    for column in missing["columns"]:
                        log_message += f"\t{column}, #: {len(df[df[column].isnull()])}\n"
                        df[column].interpolate(method='linear', inplace=True)
                else:
                    raise ValueError(f"Unknown missing method: {missing['method']}")
        df.to_csv(os.path.join(message.output_path, os.path.basename(file_path)), index=False)
    with open(log_output_path, "w") as f:
        f.write(log_message)
    return ResponsePreprocessData(
        status="success",
        local_path=message.local_path,
        output_path=message.output_path
    )