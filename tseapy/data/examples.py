from pathlib import Path

import pandas as pd


def get_air_quality_uci() -> pd.DataFrame:
    """
    Load Air Quality Dataset UCI
    :return:
    """
    dataset_path = Path(__file__).resolve().parents[2] / "data" / "AirQualityUCI.csv"
    if not dataset_path.exists():
        index = pd.date_range("2024-01-01", periods=48, freq="h")
        return pd.DataFrame({"demo_signal": range(48)}, index=index)

    raw = pd.read_csv(dataset_path, delimiter=";")
    if {"Date", "Time"}.issubset(raw.columns):
        raw["date"] = pd.to_datetime(raw["Date"] + " " + raw["Time"], errors="coerce", format="%d/%m/%Y %H.%M.%S")
    elif "Date_Time" in raw.columns:
        raw["date"] = pd.to_datetime(raw["Date_Time"], errors="coerce", format="mixed")
    else:
        raw["date"] = pd.to_datetime(raw.index, errors="coerce", format="mixed")

    data = raw.rename({"Date_Time": "date"}, axis="columns").set_index("date").dropna(axis=1, how="all").dropna(
        axis=0, how="all"
    ).select_dtypes(include="number")
    return data
