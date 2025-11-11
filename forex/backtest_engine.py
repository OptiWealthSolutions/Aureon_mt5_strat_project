import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from strategy import Strategy
from data_fetcher import get_data_from_mt5, initialize_mt5, shutdown_mt5

def calculate_performance_metrics(df, periods_per_year=252):
    
    if 'strategy_return' not in df or df['strategy_return'].empty:
        return {}

    total_return = df['strategy_equity'].iloc[-1] - 1
    
    daily_returns = df['strategy_return'].resample('D').sum()
    
    mean_daily_return = daily_returns.mean()
    std_daily_return = daily_returns.std()
    
    sharpe_ratio = (mean_daily_return / std_daily_return) if std_daily_return != 0 else 0
    sharpe_ratio_annualized = sharpe_ratio * np.sqrt(periods_per_year)

    rolling_max = df['strategy_equity'].cummax()
    drawdown = df['strategy_equity'] / rolling_max - 1
    max_drawdown = drawdown.min()

    trades = df['position'].diff().fillna(0)
    num_trades = (trades != 0).sum()

    metrics = {
        'total_return_pct': total_return * 100,
        'annualized_sharpe_ratio': sharpe_ratio_annualized,
        'max_drawdown_pct': max_drawdown * 100,
        'number_of_trades': num_trades
    }
    return metrics

def backtestEngine(df, symbol, transaction_cost_pct=0.0001):
    
    df_strategy = Strategy(df, symbol)
    
    if df_strategy is None or df_strategy.empty:
        print(f"La stratégie n'a généré aucun signal pour {symbol}.")
        return None, None

    positions = df_strategy['signal'].replace(0, np.nan).ffill().fillna(0)
    
    market_returns = df_strategy['close'].pct_change()
    strategy_returns = market_returns * positions.shift(1)

    trades = positions.diff().fillna(0)
    transaction_costs = abs(trades) * transaction_cost_pct
    strategy_returns -= transaction_costs

    buy_and_hold_equity = (1 + market_returns.fillna(0)).cumprod()
    strategy_equity = (1 + strategy_returns.fillna(0)).cumprod()
    
    df_strategy['position'] = positions
    df_strategy['market_return'] = market_returns
    df_strategy['strategy_return'] = strategy_returns
    df_strategy['buy_and_hold_equity'] = buy_and_hold_equity
    df_strategy['strategy_equity'] = strategy_equity
    
    metrics = calculate_performance_metrics(df_strategy)
    
    print(f"Moteur de backtest (Long/Short) exécuté pour {symbol}.")
    
    return df_strategy, metrics


if __name__ == "__main__":

    if initialize_mt5():
        print("--- Lancement du Backtest (Script) ---")
        
        symbol = "EURUSD"
        timeframe = mt5.TIMEFRAME_H1
        num_bars = 5000

        data = get_data_from_mt5(symbol, timeframe, num_bars)
        
        if data is not None and not data.empty:
            
            data.index = pd.to_datetime(data.index)
            
            backtest_result, metrics = backtestEngine(data, symbol, transaction_cost_pct=0.0001)
            
            if backtest_result is not None:
                print("\n--- Résultats du Backtest (Dernières 5 lignes) ---")
                print(backtest_result[['close', 'signal', 'position', 'buy_and_hold_equity', 'strategy_equity']].tail())
                
                print("\n--- Métriques de Performance ---")
                for key, value in metrics.items():
                    print(f"{key.replace('_', ' ').capitalize()}: {value:.2f}")
        
        else:
            print(f"Aucune donnée reçue pour {symbol}.")

        shutdown_mt5()
    else:
        print("Échec de l'initialisation de MT5. Fin du backtest.")