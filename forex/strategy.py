import pandas as pd
import numpy as np
import fredapi as fred
from ta.momentum import RSIIndicator
from ta.volume import MFIIndicator
from ta.trend import ADXIndicator
from data_fetcher import get_data_from_mt5
import MetaTrader5 as mt5

fredapi_key = "e16626c91fa2b1af27704a783939bf72"

TIMEFRAME_Base = mt5.TIMEFRAME_M15
TF_MAP = {
    mt5.TIMEFRAME_M30: 'M30',
    mt5.TIMEFRAME_H1: 'H1',
    mt5.TIMEFRAME_H4: 'H4',
    mt5.TIMEFRAME_D1: 'D1'
}

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
    df_strategy = _mfi(df_strategy)
    df_strategy = _LONGSMA(df_strategy, timeframe='Base')
    df_strategy = _SHORTSMA(df_strategy, timeframe='Base')
    df_tf = pd.DataFrame()
    for timeframe in TF_MAP.keys():
        df_tf[f"{timeframe}"] = get_data_from_mt5(symbol, timeframe, len(df_strategy))
        df_tf = _rsi(df_tf, timeframe=timeframe)
        df_tf = _adx(df_tf, timeframe=timeframe)
        df_tf = _LONGSMA(df_tf, timeframe=timeframe)
        df_tf = _SHORTSMA(df_tf, timeframe=timeframe)
        # Merge des indicateurs de la timeframe actuelle dans le DataFrame principal
        df_strategy = df_strategy.join(df_tf, rsuffix=f"_{timeframe}")
    
    buy_conditions = (
        #(df_strategy['Macro_Bias'] == 1) &
        (df_strategy[f'ADX_Base'] > 25) &
        (df_strategy['MFI'] > 50) &
        (df_strategy[f'SMA_20_H4'] > df_strategy[f'SMA_50_H4']) &
        (df_strategy[f'RSI_H4'] < 35)

    )
    
    sell_conditions = (
        #(df_strategy['Macro_Bias'] == -1) & 
        (df_strategy[f'ADX_Base'] > 25) &
        (df_strategy[f'RSI_Base'] > 65) &
        (df_strategy['MFI'] < 50) &
        (df_strategy[f'SMA_20_H4'] < df_strategy[f'SMA_50_H4'])&
        (df_strategy[f'RSI_H4'] > 65)
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