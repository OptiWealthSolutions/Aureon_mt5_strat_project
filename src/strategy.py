import pandas as pd
import numpy as np

def add_moving_average_signals(df, short_window=20, long_window=50):

    if 'close' not in df.columns:
        raise ValueError("Le DataFrame doit contenir une colonne 'close'.")

    df_strat = df.copy()


    df_strat['SMA_short'] = df_strat['close'].rolling(window=short_window).mean()
    df_strat['SMA_long'] = df_strat['close'].rolling(window=long_window).mean()
    
    print(f"Moyennes mobiles (Courte={short_window}, Longue={long_window}) calculées avec pandas.")


    df_strat['signal'] = 0
   

    condition_achat = (df_strat['SMA_short'] > df_strat['SMA_long']) & \
                      (df_strat['SMA_short'].shift(1) <= df_strat['SMA_long'].shift(1))
    

    condition_vente = (df_strat['SMA_short'] < df_strat['SMA_long']) & \
                      (df_strat['SMA_short'].shift(1) >= df_strat['SMA_long'].shift(1))


    df_strat['signal'] = np.where(condition_achat, 1, 0)
    df_strat['signal'] = np.where(condition_vente, -1, df_strat['signal'])
    

    df_strat.dropna(inplace=True)

    print("Signaux de croisement générés.")
    return df_strat