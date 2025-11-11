import pandas as pd
import numpy as np
import fredapi as fred
from ta.momentum import RSIIndicator
from ta.trend import ADXIndicator
from features_engineer.alternative_features import sentiment

fredapi_key = "e16626c91fa2b1af27704a783939bf72"

def Strategy(df,symbol):
    df_strategy = df.copy()
    df_strategy = RSI(df_strategy, window=14)
    #df_strategy = ADX(df_strategy, window=14)
    #df_strategy = YieldSpread(symbol, df_strategy)
    df_strategy = vol(df_strategy, window=14)
    vol_threshold = df_strategy['Volatility'].mean()
    df_strategy['signal'] = np.where(
        df_strategy['RSI'] < 30,  # Condition 1 (SI)
        1,                        # Si C1 est Vraie -> 1
        np.where(                 # Si C1 est Fausse (SINON...)
            df_strategy['RSI'] > 70,  # Condition 2 (SI)
            -1,                       # Si C2 est Vraie -> -1
            0                         # Si C2 est Fausse -> 0
        )
    )
    

    return df_strategy

def RSI(df, window=14):
    df_strat = df.copy()
    rsi_indicator = RSIIndicator(close=df_strat['close'], window=window)
    df_strat['RSI'] = rsi_indicator.rsi()
    return df_strat

def ADX(df, window=14):
    df_strat = df.copy()
    adx_indicator = ADXIndicator(
        high=df_strat['high'],
        low=df_strat['low'],
        close=df_strat['close'],
        window=window
    )
    df_strat['ADX'] = adx_indicator.adx()
    df_strat['+DI'] = adx_indicator.adx_pos()
    df_strat['-DI'] = adx_indicator.adx_neg() 
    print(f"ADX (période={window}) calculé avec succès.")
    return df_strat


def YieldSpread(symbol, data):
    fr = fred.Fred(api_key=fredapi_key)
    fred_yield_tickers = {
        'US_10Y': 'DGS10',
        'EUR_10Y': 'IRLTLT01DEM156N',
        'GBP_10Y': 'IRLTLT01GBM156N',
        'JPY_10Y': 'IRLTLT01JPM156N',
        'CAD_10Y': 'IRLTLT01CAM156N'
    }
    start_date = data.index.min()
    end_date = data.index.max()
    all_yield_data = []

    for name, series_id in fred_yield_tickers.items():
        try:
            series = fr.get_series(series_id, 
                                   observation_start=start_date, 
                                   observation_end=end_date)
            series.name = name
            all_yield_data.append(series)
        except:
            pass

    yield_data = pd.concat(all_yield_data, axis=1)

    data_index = pd.to_datetime(data.index).tz_localize(None)
    yield_data.index = pd.to_datetime(yield_data.index).tz_localize(None)

    yield_data_aligned = yield_data.reindex(data_index, method='ffill').ffill().bfill()
    
    data_out = data.copy()
    data_out['US_10Y_Yield'] = yield_data_aligned['US_10Y']

    spread_value = 0.0
    if "EUR" in symbol:
        spread_value = yield_data_aligned['EUR_10Y'] - yield_data_aligned['US_10Y']
    elif "GBP" in symbol:
        spread_value = yield_data_aligned['GBP_10Y'] - yield_data_aligned['US_10Y']
    elif "JPY" in symbol:
        spread_value = yield_data_aligned['US_10Y'] - yield_data_aligned['JPY_10Y']
    elif "CAD" in symbol:
        spread_value = yield_data_aligned['US_10Y'] - yield_data_aligned['CAD_10Y']
    
    data_out['Ticker_Yield_Spread'] = spread_value
    data_out['Ticker_Yield_Spread'] = data_out['Ticker_Yield_Spread'].ffill().bfill()
    return data_out

def vol(data, window=14):
    data['Volatility'] = data['close'].rolling(window=window).std()
    return data