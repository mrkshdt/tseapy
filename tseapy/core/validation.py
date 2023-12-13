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
    assert df.index.is_all_dates, 'The dataframe index should only contains dates'
    assert df.index.is_monotonic_increasing, 'The dataframe index should only contains dates in an increasing order'
