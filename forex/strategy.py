import pandas as pd
import numpy as np
import fredapi as fred
from ta.momentum import RSIIndicator
from ta.volume import MFIIndicator
from ta.trend import ADXIndicator
from ta.volatility import BollingerBands
import MetaTrader5 as mt5

pd.set_option('future.no_silent_downcasting', True)
fredapi_key = "e16626c91fa2b1af27704a783939bf72"

timeframes = ['Base', 'M30', 'H1', 'H4', 'D1']

def get_col_name(base_name, timeframe):
    if timeframe == 'Base':
        return base_name
    return f"{base_name}_{timeframe}"

def _TDI(df, timeframe='Base', rsi_period=21, bb_period=34, bb_std=1.6185, fast_ma=2, slow_ma=7):
    df_tdi = df.copy()
    col_close = get_col_name('close', timeframe)

    if col_close not in df_tdi.columns:
        df_tdi[f'TDI_RSI_{timeframe}'] = np.nan
        df_tdi[f'TDI_Fast_MA_{timeframe}'] = np.nan
        df_tdi[f'TDI_Slow_MA_{timeframe}'] = np.nan
        df_tdi[f'TDI_BB_High_{timeframe}'] = np.nan
        df_tdi[f'TDI_BB_Low_{timeframe}'] = np.nan
        df_tdi[f'TDI_BB_Mid_{timeframe}'] = np.nan
        return df_tdi

    tdi_rsi = RSIIndicator(close=df_tdi[col_close], window=rsi_period).rsi()
    df_tdi[f'TDI_RSI_{timeframe}'] = tdi_rsi

    bb = BollingerBands(
        close=tdi_rsi, 
        window=bb_period, 
        window_dev=bb_std
    )
    df_tdi[f'TDI_BB_High_{timeframe}'] = bb.bollinger_hband()
    df_tdi[f'TDI_BB_Low_{timeframe}'] = bb.bollinger_lband()
    df_tdi[f'TDI_BB_Mid_{timeframe}'] = bb.bollinger_mavg()
    
    df_tdi[f'TDI_Slow_MA_{timeframe}'] = tdi_rsi.rolling(window=slow_ma).mean()
    df_tdi[f'TDI_Fast_MA_{timeframe}'] = tdi_rsi.rolling(window=fast_ma).mean()
    
    return df_tdi

def _rsi(df, window=14, timeframe='Base'):
    df_strat = df.copy()
    col_close = get_col_name('close', timeframe)
    
    if col_close in df_strat.columns:
        rsi_indicator = RSIIndicator(close=df_strat[col_close], window=window)
        df_strat[f'RSI_{timeframe}'] = rsi_indicator.rsi()
    else:
        df_strat[f'RSI_{timeframe}'] = np.nan
    return df_strat

def _LONGSMA(df, window=200, timeframe='Base'):
    df_strat = df.copy()
    col_close = get_col_name('close', timeframe)
    if col_close in df_strat.columns:
        df_strat[f'SMA_{window}_{timeframe}'] = df_strat[col_close].rolling(window=window).mean()
    else:
        df_strat[f'SMA_{window}_{timeframe}'] = np.nan
    return df_strat

def _SHORTSMA(df, window=50, timeframe='Base'):
    df_strat = df.copy()
    col_close = get_col_name('close', timeframe)
    
    if col_close in df_strat.columns:
        df_strat[f'SMA_{window}_{timeframe}'] = df_strat[col_close].rolling(window=window).mean()
    else:
        df_strat[f'SMA_{window}_{timeframe}'] = np.nan
    return df_strat

def Strategy(df, symbol):
    df_strategy = df.copy()
    
    timeframes_for_logic = ['Base', 'M30', 'H1', 'H4', 'D1']
    
    for tf in timeframes_for_logic:
        if tf in ['D1', 'H4']:
            df_strategy = _LONGSMA(df_strategy, window=200, timeframe=tf)
            df_strategy = _SHORTSMA(df_strategy, window=50, timeframe=tf)
        
        if tf in ['Base', 'M30', 'H1', 'H4']:
            df_strategy = _TDI(df_strategy, timeframe=tf)

    buy_trend_filter = (
        (df_strategy['SMA_50_D1'] > df_strategy['SMA_200_D1']) &
        (df_strategy['SMA_50_H4'] > df_strategy['SMA_200_H4'])
    )
    
    sell_trend_filter = (
        (df_strategy['SMA_50_D1'] < df_strategy['SMA_200_D1']) &
        (df_strategy['SMA_50_H4'] < df_strategy['SMA_200_H4'])
    )

    validation_buy = (
        (df_strategy['TDI_Fast_MA_H4'] > df_strategy['TDI_Slow_MA_H4']) &
        (df_strategy['TDI_Fast_MA_H1'] > df_strategy['TDI_Slow_MA_H1'])
    )
    
    validation_sell = (
        (df_strategy['TDI_Fast_MA_H4'] < df_strategy['TDI_Slow_MA_H4']) &
        (df_strategy['TDI_Fast_MA_H1'] < df_strategy['TDI_Slow_MA_H1'])
    )
    
    entry_buy = (
        (df_strategy['TDI_Fast_MA_M30'] > df_strategy['TDI_Slow_MA_M30']) &
        (df_strategy['TDI_Fast_MA_Base'] > df_strategy['TDI_Slow_MA_Base'])
    )
    
    entry_sell = (
        (df_strategy['TDI_Fast_MA_M30'] < df_strategy['TDI_Slow_MA_M30']) &
        (df_strategy['TDI_Fast_MA_Base'] < df_strategy['TDI_Slow_MA_Base'])
    )
    
    buy_conditions = buy_trend_filter & validation_buy & entry_buy
    sell_conditions = sell_trend_filter & validation_sell & entry_sell
    
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
    
    return df_strategy.dropna()