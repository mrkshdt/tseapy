import pandas as pd


def validate_dataframe(df: pd.DataFrame):
    """
    Performs a series of checks on the DataFrame df

    Parameters
    ----------
    df : the pandas.DataFrame to be checked

    Returns
    -------

    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError('The dataframe index should contain only dates')
    if not df.index.is_monotonic_increasing:
        raise ValueError('The dataframe index should contain dates in increasing order')
