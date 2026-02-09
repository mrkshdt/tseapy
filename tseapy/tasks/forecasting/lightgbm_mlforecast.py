import pandas as pd

from tseapy.core import create_callback_url
from tseapy.core.parameters import NumberParameter
from tseapy.tasks.forecasting import ForecastingBackend
from tseapy.tasks.forecasting.common import infer_series_freq, make_result_frame, to_statsforecast_df


class LightGBMMLForecastBackend(ForecastingBackend):
    def __init__(self):
        short_description = "MLForecast with LightGBM and auto-generated lag/date features."
        long_description = ""
        super().__init__(
            'lightgbm-mlforecast',
            short_description=short_description,
            long_description=long_description,
            callback_url=create_callback_url('forecasting', 'lightgbm-mlforecast'),
            parameters=[
                NumberParameter(
                    name='horizon',
                    label='Forecast Horizon',
                    description='Number of steps to forecast',
                    minimum=1,
                    maximum=365,
                    step=1,
                    default=30,
                    onclick='',
                    disabled=False,
                ),
                NumberParameter(
                    name='season_length',
                    label='Season Length',
                    description='Used to define seasonal lag features',
                    minimum=1,
                    maximum=365,
                    step=1,
                    default=12,
                    onclick='',
                    disabled=False,
                ),
            ],
        )

    def do_analysis(self, data: pd.DataFrame, feature: str, **kwargs):
        horizon = int(kwargs['horizon'])
        season_length = int(kwargs['season_length'])
        series = data[feature].dropna()
        if len(series) < 10:
            raise ValueError('Need at least 10 non-null samples for ML forecasting.')

        try:
            from lightgbm import LGBMRegressor
            from mlforecast import MLForecast
        except Exception as exc:
            raise ValueError(f'LightGBM MLForecast dependencies are not available: {exc}') from exc

        sf_df = to_statsforecast_df(data.loc[series.index], feature)
        freq = infer_series_freq(series.index)

        base_lags = [1, 2, 3, 6, 12, 24]
        if season_length not in base_lags:
            base_lags.append(season_length)
        lags = sorted(set([lag for lag in base_lags if lag < len(series)]))
        if not lags:
            lags = [1]

        date_features = ['dayofweek', 'month'] if isinstance(series.index, pd.DatetimeIndex) else None

        model = LGBMRegressor(n_estimators=300, learning_rate=0.05, random_state=42)
        fcst = MLForecast(models=[model], freq=freq, lags=lags, date_features=date_features)

        try:
            fcst.fit(sf_df)
            pred = fcst.predict(h=horizon)
        except Exception as exc:
            raise ValueError(f'Forecasting failed: {exc}')

        model_col = [c for c in pred.columns if c not in {'unique_id', 'ds'}]
        if not model_col:
            raise ValueError('LightGBM forecast output did not contain prediction values.')

        return make_result_frame(ds=pred['ds'].values, forecast=pred[model_col[0]].values)
