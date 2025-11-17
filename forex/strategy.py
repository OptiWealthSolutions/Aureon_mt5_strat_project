import pandas as pd
import numpy as np
import fredapi as fred
from ta.momentum import RSIIndicator
from ta.momentum import TDIIndicator
import MetaTrader5 as mt5

# Configuration
pd.set_option('future.no_silent_downcasting', True)

def get_col_name(base_name, timeframe):
    if timeframe == 'Base':
        return base_name
    return f"{base_name}_{timeframe}"

# --- FONCTIONS INDICATEURS ---

def _rsi(df, window=14, timeframe='Base'):
    df_strat = df.copy()
    col_close = get_col_name('close', timeframe)
    
    if col_close in df_strat.columns:
        rsi_indicator = RSIIndicator(close=df_strat[col_close], window=window)
        df_strat[f'RSI_{timeframe}'] = rsi_indicator.rsi()
    else:
        # Sécurité si la colonne n'existe pas
        df_strat[f'RSI_{timeframe}'] = np.nan
    return df_strat

def _LONGSMA(df, window=50, timeframe='Base'):
    df_strat = df.copy()
    col_close = get_col_name('close', timeframe)
    
    if col_close in df_strat.columns:
        df_strat[f'SMA_{window}_{timeframe}'] = df_strat[col_close].rolling(window=window).mean()
    else:
        df_strat[f'SMA_{window}_{timeframe}'] = np.nan
    return df_strat

def _SHORTSMA(df, window=20, timeframe='Base'):
    df_strat = df.copy()
    col_close = get_col_name('close', timeframe)
    
    if col_close in df_strat.columns:
        df_strat[f'SMA_{window}_{timeframe}'] = df_strat[col_close].rolling(window=window).mean()
    else:
        df_strat[f'SMA_{window}_{timeframe}'] = np.nan
    return df_strat


#appel des fonctions et creation de la logique 

def Strategy(df, symbol):
    df_strategy = df.copy()
    #faire les appels pour chaque fonctions des features
    #M15

    #M30

    #H1

    #H4

    #D1



    buy_conditions = (

    )
    
    sell_conditions = (
       
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
    
    # Sauvegarde pour debug si nécessaire
    # df_strategy.to_csv("debug_strategy_output.csv")
    
    return df_strategy.dropna()

