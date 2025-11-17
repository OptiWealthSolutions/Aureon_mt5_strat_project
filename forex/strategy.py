import pandas as pd
import numpy as np
import fredapi as fred
from ta.momentum import RSIIndicator
from ta.momentum import TDIIndicator
import MetaTrader5 as mt5
from ta.volatility import BollingerBands
# Configuration
pd.set_option('future.no_silent_downcasting', True)

def get_col_name(base_name, timeframe):
    if timeframe == 'Base':
        return base_name
    return f"{base_name}_{timeframe}"

# --- FONCTIONS INDICATEURS ---
def _TDI(df, rsi_period=21, bb_period=34, bb_std=1.6185, fast_ma=2, slow_ma=7):
    df_tdi = df.copy()
    df_tdi['TDI_RSI'] = RSIIndicator(close=df_tdi['close'], window=rsi_period).rsi()
    bb = BollingerBands(
        close=df_tdi['TDI_RSI'], 
        window=bb_period, 
        window_dev=bb_std
    )
    df_tdi['TDI_BB_High'] = bb.bollinger_hband()
    df_tdi['TDI_BB_Low'] = bb.bollinger_lband()
    df_tdi['TDI_BB_Mid'] = bb.bollinger_mavg() 
    df_tdi['TDI_Slow_MA'] = df_tdi['TDI_RSI'].rolling(window=slow_ma).mean()
    df_tdi['TDI_Fast_MA'] = df_tdi['TDI_RSI'].rolling(window=fast_ma).mean()
    
    return df_tdi.dropna()

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
    df_ = get_col_name('close', timeframe)
    if df_ in df_strat.columns:
        df_strat[f'SMA_{window}_{timeframe}'] = df_strat[df_].rolling(window=window).mean()
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

#logique de la fonction : identifiacation de trend et prise de position (long/short) selon les conditions des indicateurs
# D1-H4 : SMA 200 < SM50 --> tendance haussière
# H4- H1 : TDI en zone haussière  
# M30 - M15 : TDI en zone haussière 

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

