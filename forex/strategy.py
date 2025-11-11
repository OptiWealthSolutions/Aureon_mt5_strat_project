import pandas as pd
import numpy as np
import fredapi as fred
from ta.momentum import RSIIndicator
from ta.volume import MFIIndicator
from ta.trend import ADXIndicator

fredapi_key = "e16626c91fa2b1af27704a783939bf72"


def _rsi(df, window=14):
    df_strat = df.copy()
    rsi_indicator = RSIIndicator(close=df_strat['close'], window=window)
    df_strat['RSI'] = rsi_indicator.rsi()
    return df_strat

def _adx(df, window=14):
    df_strat = df.copy()
    adx_indicator = ADXIndicator(
        high=df_strat['high'],
        low=df_strat['low'],
        close=df_strat['close'],
        window=window
    )
    df_strat['ADX'] = adx_indicator.adx()
    df_strat['DI_Pos'] = adx_indicator.adx_pos()
    df_strat['DI_Neg'] = adx_indicator.adx_neg()
    return df_strat

def _mfi(df, window=14):
    df_strat = df.copy()
    
    volume_col = 'tick_volume' 
    if volume_col not in df_strat.columns:
         df_strat['MFI'] = np.nan
         return df_strat

    mfi_indicator = MFIIndicator(
        high=df_strat['high'],
        low=df_strat['low'],
        close=df_strat['close'],
        volume=df_strat[volume_col],
        window=window
    )
    df_strat['MFI'] = mfi_indicator.money_flow_index()
    return df_strat

def _volatility(data, window=14):
    data['Volatility'] = data['close'].rolling(window=window).std()
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
        data['Ticker_Yield_Spread'] = np.nan
        return data

    yield_data = pd.concat(all_yield_data, axis=1)
    data_index = pd.to_datetime(data.index).tz_localize(None)
    yield_data.index = pd.to_datetime(yield_data.index).tz_localize(None)
    
    yield_data_aligned = yield_data.reindex(data_index, method='ffill').ffill().bfill()
    
    data_out = data.copy()
    spread_value = np.nan 
    
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

def _LONGSMA(df, window=200):
    df_strat = df.copy()
    df_strat[f'SMA_{window}'] = df_strat['close'].rolling(window=window).mean()
    return df_strat

def _SHORTSMA(df, window=50):
    df_strat = df.copy()
    df_strat[f'SMA_{window}'] = df_strat['close'].rolling(window=window).mean()
    return df_strat


def Strategy(df, symbol):
    df_strategy = df.copy()
    
    df_strategy = _rsi(df_strategy)
    df_strategy = _adx(df_strategy)
    df_strategy = _mfi(df_strategy)
    df_strategy = _yield_spread(symbol, df_strategy)
    df_strategy = _volatility(df_strategy)
    df_strategy = _LONGSMA(df_strategy)
    df_strategy = _SHORTSMA(df_strategy)
    df_strategy['Macro_Bias'] = np.where(df_strategy['Ticker_Yield_Spread'] > 0, 1, 
                                         np.where(df_strategy['Ticker_Yield_Spread'] < 0, -1, 0))
    
    vol_threshold = df_strategy['Volatility'].mean() 
    df_strategy['Vol_Filter'] = df_strategy['Volatility'] > vol_threshold
    
    
    buy_conditions = (
        #(df_strategy['Macro_Bias'] == 1) & 
        (df_strategy['ADX'] > 25) &
        (df_strategy['RSI'] < 35) & 
        (df_strategy['MFI'] > 50) &
        (df_strategy['Vol_Filter']) &
        (df_strategy['SMA_50'] > df_strategy['SMA_200'])
    )
    
    sell_conditions = (
        #(df_strategy['Macro_Bias'] == -1) & 
        (df_strategy['ADX'] > 25) &
        (df_strategy['RSI'] > 65) &
        (df_strategy['MFI'] < 50) &
        (df_strategy['Vol_Filter']) &
        (df_strategy['SMA_50'] < df_strategy['SMA_200'])
    )
    

    df_strategy['signal'] = np.where(
        buy_conditions, 
        1,
        np.where(
            sell_conditions,
            -1,
            0
        )
    )

    df_strategy = df_strategy.drop(columns=['Macro_Bias', 'Vol_Filter'], errors='ignore')
    df_strategy.to_csv("debug_strategy_output.csv")
    return df_strategy.dropna()