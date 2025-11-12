import pandas as pd
import numpy as np
import fredapi as fred
from ta.momentum import RSIIndicator
from ta.volume import MFIIndicator
from ta.trend import ADXIndicator

# [Correction de la Future Warning de Pandas]
pd.set_option('future.no_silent_downcasting', True)
fredapi_key = "e16626c91fa2b1af27704a783939bf72"


# --- FONCTIONS INDICATEURS MTF FLEXIBLES ---

def _calc_rsi(df, price_col, output_name, window=14):
    """Calcule le RSI sur une colonne de prix spécifique (MTF compatible)."""
    df_strat = df.copy()
    if price_col not in df_strat.columns:
        df_strat[output_name] = np.nan
        return df_strat
        
    rsi_indicator = RSIIndicator(close=df_strat[price_col], window=window)
    df_strat[output_name] = rsi_indicator.rsi()
    return df_strat

def _calc_adx(df, high_col, low_col, close_col, output_prefix, window=14):
    """Calcule l'ADX sur des colonnes OHLC spécifiques (MTF compatible)."""
    df_strat = df.copy()
    # Vérifie si toutes les colonnes requises existent
    if not all(col in df_strat.columns for col in [high_col, low_col, close_col]):
        df_strat[f'{output_prefix}_ADX'] = np.nan
        df_strat[f'{output_prefix}_DI_Pos'] = np.nan
        df_strat[f'{output_prefix}_DI_Neg'] = np.nan
        return df_strat

    adx_indicator = ADXIndicator(
        high=df_strat[high_col],
        low=df_strat[low_col],
        close=df_strat[close_col],
        window=window
    )
    df_strat[f'{output_prefix}_ADX'] = adx_indicator.adx()
    df_strat[f'{output_prefix}_DI_Pos'] = adx_indicator.adx_pos()
    df_strat[f'{output_prefix}_DI_Neg'] = adx_indicator.adx_neg()
    return df_strat

def _mfi(df, window=14):
    """Calcule le MFI sur le TF de base (sans suffixe de colonne)."""
    df_strat = df.copy()
    volume_col = 'tick_volume' 
    if volume_col not in df_strat.columns:
         df_strat['MFI'] = np.nan
         return df_strat

    mfi_indicator = MFIIndicator(
        high=df_strat['high'], low=df_strat['low'], close=df_strat['close'],
        volume=df_strat[volume_col],
        window=window
    )
    df_strat['MFI'] = mfi_indicator.money_flow_index()
    return df_strat

def _volatility(data, window=14):
    data['Volatility'] = data['close'].rolling(window=window).std()
    return data

def _yield_spread(symbol, data):
    # Logique complexe de FRED (laissé inchangé)
    try:
        fr = fred.Fred(api_key=fredapi_key)
    except ValueError:
        data['Ticker_Yield_Spread'] = np.nan
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

def _calc_sma(df, window, price_col='close'):
    """Calcule une SMA sur une colonne de prix spécifique."""
    df_strat = df.copy()
    output_suffix = price_col.split('_')[-1]
    
    if price_col not in df_strat.columns:
        df_strat[f'SMA_{window}_{output_suffix}'] = np.nan
        return df_strat
        
    df_strat[f'SMA_{window}_{output_suffix}'] = df_strat[price_col].rolling(window=window).mean()
    return df_strat

# --- FONCTION PRINCIPALE DE STRATÉGIE (MTF) ---

def Strategy(df, symbol):
    # Vous pouvez décommenter la ligne de débogage si vous le souhaitez:
    # print("DEBUG: Colonnes reçues dans Strategy():", df.columns.tolist()) 
    df_strategy = df.copy()
    
    # 1. CALCUL DES INDICATEURS DE BASE (TF M15, colonnes sans suffixe)
    df_strategy = _calc_rsi(df_strategy, price_col='close', output_name='RSI_M15')
    df_strategy = _calc_adx(df_strategy, high_col='high', low_col='low', close_col='close', output_prefix='M15', window=14)
    #df_strategy = _calc_mfi(df_strategy)
    df_strategy = _volatility(df_strategy)
    df_strategy = _calc_sma(df_strategy, window=20, price_col='close')
    df_strategy = _calc_sma(df_strategy, window=50, price_col='close')

    # 2. CALCUL DES INDICATEURS MTF (TF H4)
    # Les colonnes sont nommées 'close_H4', 'high_H4', etc. grâce à main.py
    df_strategy = _calc_rsi(df_strategy, price_col='close_H4', output_name='RSI_H4')
    df_strategy = _calc_adx(df_strategy, high_col='high_H4', low_col='low_H4', close_col='close_H4', output_prefix='H4', window=14)

    # 3. CALCUL MACRO (Yield Spread)
    df_strategy = _yield_spread(symbol, df_strategy)
    
    # --- LOGIQUE DE SIGNAL ---
    
    # Logique Macro
    df_strategy['Macro_Bias'] = np.where(df_strategy['Ticker_Yield_Spread'] > 0, 1, 
                                          np.where(df_strategy['Ticker_Yield_Spread'] < 0, -1, 0))
    
    # Filtre de Volatilité
    vol_threshold = df_strategy['Volatility'].mean() 
    df_strategy['Vol_Filter'] = df_strategy['Volatility'] > vol_threshold
    
    # Conditions de Trading MTF
    
    buy_conditions = (
        (df_strategy['Macro_Bias'] == 1) & 
        (df_strategy['M15_ADX'] > 25) &
        (df_strategy['M15_DI_Pos'] > df_strategy['M15_DI_Neg']) & 
        (df_strategy['RSI_M15'] < 35) & 
        (df_strategy['MFI'] > 50) &
        (df_strategy['Vol_Filter']) &
        (df_strategy['SMA_20_close'] > df_strategy['SMA_50_close']) &
        
        # FILTRE MTF : Confirmation de tendance haussière sur H4 (RSI non baissier)
        (df_strategy['RSI_H4'] > 50) &
        (df_strategy['H4_DI_Pos'] > df_strategy['H4_DI_Neg'])
    )
    
    sell_conditions = (
        (df_strategy['Macro_Bias'] == -1) & 
        (df_strategy['M15_ADX'] > 25) &
        (df_strategy['M15_DI_Neg'] > df_strategy['M15_DI_Pos']) & 
        (df_strategy['RSI_M15'] > 65) &
        (df_strategy['MFI'] < 50) &
        (df_strategy['Vol_Filter']) &
        (df_strategy['SMA_20_close'] < df_strategy['SMA_50_close']) &
        
        # FILTRE MTF : Confirmation de tendance baissière sur H4 (RSI non haussier)
        (df_strategy['RSI_H4'] < 50) &
        (df_strategy['H4_DI_Neg'] > df_strategy['H4_DI_Pos'])
    )
    
    # Génération du signal
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