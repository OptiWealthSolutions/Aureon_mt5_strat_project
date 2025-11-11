import pandas as pd
import numpy as np
import fredapi as fred
from ta.momentum import RSIIndicator
from ta.volume import MFIIndicator
from ta.trend import ADXIndicator
from features_engineer.alternative_features import sentiment

fredapi_key = "e16626c91fa2b1af27704a783939bf72"

def _rsi(df, window=14):
    df_strat = df.copy()
    rsi_indicator = RSIIndicator(close=df_strat['Close'], window=window)
    df_strat['RSI'] = rsi_indicator.rsi()
    return df_strat

def _adx(df, window=14):
    df_strat = df.copy()
    adx_indicator = ADXIndicator(
        high=df_strat['High'],
        low=df_strat['Low'],
        close=df_strat['Close'],
        window=window
    )
    df_strat['ADX'] = adx_indicator.adx()
    df_strat['DI_Pos'] = adx_indicator.adx_pos()
    df_strat['DI_Neg'] = adx_indicator.adx_neg()
    return df_strat

def _mfi(df, window=14):
    df_strat = df.copy()
    mfi_indicator = MFIIndicator(
        high=df_strat['High'],
        low=df_strat['Low'],
        close=df_strat['Close'],
        volume=df_strat['Volume'],
        window=window
    )
    df_strat['MFI'] = mfi_indicator.money_flow_index()
    return df_strat

def _volatility(data, window=14):
    data['Volatility'] = data['Close'].rolling(window=window).std()
    return data

def _yield_spread(symbol, data):
    try:
        fr = fred.Fred(api_key=fredapi_key)
    except ValueError:
        return data

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
            series = fr.get_series(series_id, observation_start=start_date, observation_end=end_date)
            series.name = name
            all_yield_data.append(series)
        except:
            pass

    if not all_yield_data:
        return data

    yield_data = pd.concat(all_yield_data, axis=1)
    data_index = pd.to_datetime(data.index).tz_localize(None)
    yield_data.index = pd.to_datetime(yield_data.index).tz_localize(None)
    yield_data_aligned = yield_data.reindex(data_index, method='ffill').ffill().bfill()
    
    data_out = data.copy()
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

def Strategy(df, symbol):
    df_strategy = df.copy()
    
    df_strategy = _rsi(df_strategy)
    df_strategy = _adx(df_strategy)
    df_strategy = _mfi(df_strategy)
    df_strategy = _yield_spread(symbol, df_strategy)
    df_strategy = _volatility(df_strategy)
    
    df_strategy = df_strategy.dropna()
    
    df_strategy['Macro_Bias'] = np.where(df_strategy['Ticker_Yield_Spread'] > 0, 1, 
                                        np.where(df_strategy['Ticker_Yield_Spread'] < 0, -1, 0))
    
    vol_threshold = df_strategy['Volatility'].mean()
    df_strategy['Vol_Filter'] = df_strategy['Volatility'] > vol_threshold
    
    buy_conditions = (
        (df_strategy['Macro_Bias'] == 1) & 
        (df_strategy['ADX'] > 25) &
        (df_strategy['DI_Pos'] > df_strategy['DI_Neg']) &
        (df_strategy['RSI'] < 30) & 
        (df_strategy['MFI'] > 50) &
        (df_strategy['Vol_Filter'])
    )
    
    sell_conditions = (
        (df_strategy['Macro_Bias'] == -1) & 
        (df_strategy['ADX'] > 25) &
        (df_strategy['DI_Neg'] > df_strategy['DI_Pos']) &
        (df_strategy['RSI'] > 70) &
        (df_strategy['MFI'] < 50) &
        (df_strategy['Vol_Filter'])
    )
    
    df_strategy['Signal'] = np.where(
        buy_conditions, 
        1,
        np.where(
            sell_conditions,
            -1,
            0
        )
    )

    df_strategy = df_strategy.drop(columns=['Macro_Bias', 'Vol_Filter', 'Sentiment_Filter'], errors='ignore')

    return df_strategy