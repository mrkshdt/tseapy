import pandas as pd


def get_air_quality_uci() -> pd.DataFrame:
    """
    Load Air Quality Dataset UCI
    :return:
    """
    data = pd.read_csv(
        'data/AirQualityUCI.csv',
        delimiter=";",
        parse_dates=[[0, 1]],
        infer_datetime_format=True,
    ).rename(
        {'Date_Time': 'date'}, axis='columns'
    ).set_index(
        'date'
    ).dropna(
        axis=1, how='all'
    ).dropna(
        axis=0, how='all'
    ).select_dtypes(
        include='number'
    )
    data.index = pd.to_datetime(data.index, format="%d/%m/%Y %H.%M.%S")
    return data
