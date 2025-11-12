import pandas as pd
import numpy as np
import fredapi as fred
from ta.momentum import RSIIndicator
from ta.volume import MFIIndicator
from ta.trend import ADXIndicator
from main import TF_MAP
fredapi_key = "e16626c91fa2b1af27704a783939bf72"


def _rsi(df, window=14,timeframe=float):
    df_strat = df.copy()
    rsi_indicator = RSIIndicator(close=df_strat['close'], window=window)
    df_strat[f'RSI_{timeframe}'] = rsi_indicator.rsi()
    return df_strat

def _adx(df, window=14,timeframe=float):
    df_strat = df.copy()
    adx_indicator = ADXIndicator(
        high=df_strat['high'],
        low=df_strat['low'],
        close=df_strat['close'],
        window=window
    )
    df_strat[f'ADX_{timeframe}'] = adx_indicator.adx()
    df_strat[f'DI_Pos_{timeframe}'] = adx_indicator.adx_pos()
    df_strat[f'DI_Neg_{timeframe}'] = adx_indicator.adx_neg()
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

def _LONGSMA(df, window=50,timeframe=float):
    df_strat = df.copy()
    df_strat[f'SMA_{window}_{timeframe}'] = df_strat['close'].rolling(window=window).mean()
    return df_strat

def _SHORTSMA(df, window=20,timeframe=float):
    df_strat = df.copy()
    df_strat[f'SMA_{window}_{timeframe}'] = df_strat['close'].rolling(window=window).mean()
    return df_strat



def Strategy(df, symbol):
    df_strategy = df.copy()
    #defaut time frame
    df_strategy = _rsi(df_strategy, timeframe='Base')
    df_strategy = _adx(df_strategy, timeframe='Base')
    #boucle pour charger les indicateurs de toutes les timeframes
    for timeframe, _ in TF_MAP.items():
        df_strategy = _rsi(df_strategy, timeframe=timeframe)
        df_strategy = _adx(df_strategy, timeframe=timeframe)
        df_strategy = _LONGSMA(df_strategy, timeframe=timeframe)
        df_strategy = _SHORTSMA(df_strategy, timeframe=timeframe)
    df_strategy = _mfi(df_strategy)
    df_strategy = _LONGSMA(df_strategy, timeframe='Base')
    df_strategy = _SHORTSMA(df_strategy, timeframe='Base')

    
    
    buy_conditions = (
        #(df_strategy['Macro_Bias'] == 1) &
        (df_strategy[f'ADX_Base'] > 25) &
        (df_strategy[f'RSI_Base'] < 35) & 
        (df_strategy['MFI'] > 50) &
        (df_strategy['Vol_Filter']) &
        (df_strategy[f'SMA_20_Base'] > df_strategy[f'SMA_50_Base'])
    )
    
    sell_conditions = (
        #(df_strategy['Macro_Bias'] == -1) & 
        (df_strategy[f'ADX_Base'] > 25) &
        (df_strategy[f'RSI_Base'] > 65) &
        (df_strategy['MFI'] < 50) &
        (df_strategy['Vol_Filter']) &
        (df_strategy['SMA_20'] < df_strategy['SMA_50'])
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