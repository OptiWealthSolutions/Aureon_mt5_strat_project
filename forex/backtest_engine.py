import pandas as pd
import numpy as np
import MetaTrader5 as mt5

from strategy import Strategy 
from data_fetcher import get_data_from_mt5, initialize_mt5, shutdown_mt5

def backtestEngine(df, symbol):
    """
    Moteur de backtest vectorisé simple (Long/Short).
    """
    
    # 1. Calculer les signaux de la stratégie
    df_strategy = Strategy(df, symbol)
    
    if df_strategy is None or df_strategy.empty:
        print(f"La stratégie n'a généré aucun signal pour {symbol}.")
        return None

    # 2. Déterminer les positions
    positions = df_strategy['signal'].replace(0, np.nan).ffill().fillna(0)

    # 3. Calculer les retours
    market_returns = df_strategy['close'].pct_change()
    strategy_returns = market_returns * positions.shift(1)

    # 4. Calculer l'equity
    buy_and_hold_equity = (1 + market_returns.fillna(0)).cumprod()
    strategy_equity = (1 + strategy_returns.fillna(0)).cumprod()
    
    # 5. Ajouter les résultats au DataFrame
    df_strategy['position'] = positions
    df_strategy['market_return'] = market_returns
    df_strategy['strategy_return'] = strategy_returns
    df_strategy['buy_and_hold_equity'] = buy_and_hold_equity
    df_strategy['strategy_equity'] = strategy_equity
    
    print(f"Moteur de backtest (Long/Short) exécuté pour {symbol}.")
    
    return df_strategy


if __name__ == "__main__":

    if initialize_mt5():
        print("--- Lancement du Backtest (Script) ---")
        
        data = get_data_from_mt5("EURUSD", mt5.TIMEFRAME_H1, 5000)
 
        backtest_result = backtestEngine(data, "EURUSD")
            
        print("\n--- Résultats du Backtest (Dernières 5 lignes) ---")
        print(backtest_result[['close', 'signal', 'position', 'buy_and_hold_equity', 'strategy_equity']])
                
        final_return = (backtest_result['strategy_equity'].iloc[-1] - 1) * 100
        print(f"\nRetour final de la stratégie: {final_return:.2f}%")
  
        shutdown_mt5()
    else:
        print("Échec de l'initialisation de MT5. Fin du backtest.")