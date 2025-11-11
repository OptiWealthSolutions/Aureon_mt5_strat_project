import pandas as pd
import numpy as np

account_balance = 1000   # Exemple de solde du compte

def risk_manager(df_risk, account_balance, risk_max, confidence_index):
    df_risk = computeATR(df_risk, window=14)
    df_risk['Position_Risk_USD'] = df_risk['ATR'] * confidence_index * 10  # Valeur pip pour 1 lot standard
    df_risk['Lot_Size'] = (account_balance * risk_max) / df_risk['Position_Risk_USD']
    return df_risk

def computeATR(df, window=14):
    df_risk = df.copy()
    df_risk['H-L'] = df_risk['high'] - df_risk['low']
    df_risk['H-PC'] = abs(df_risk['high'] - df_risk['close'].shift(1))
    df_risk['L-PC'] = abs(df_risk['low'] - df_risk['close'].shift(1))
    df_risk['TR'] = df_risk[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df_risk['ATR'] = df_risk['TR'].rolling(window=window).mean()
    df_risk.drop(['H-L', 'H-PC', 'L-PC', 'TR'], axis=1, inplace=True)
    return df_risk