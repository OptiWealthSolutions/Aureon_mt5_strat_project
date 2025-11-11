import MetaTrader5 as mt5
import matplotlib.pyplot as plt
from data_fetcher import get_data_from_mt5, initialize_mt5, shutdown_mt5
from strategy import Strategy


SYMBOL = "EURUSD"
TIMEFRAME = mt5.TIMEFRAME_H1
N_BARS = 50000

INITIAL_CAPITAL = 10000
LOT_SIZE = 0.03
SPREAD_PIPS = 0.6
COMMISSION_PER_LOT = 3.5
PIP_VALUE_USD_PER_LOT = 10.0


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from strategy import Strategy

class EventDrivenBacktester:
    def __init__(self, df, symbol, strategy_func, initial_capital, lot_size_fixed, spread_pips, commission_per_lot, pip_value_usd):
        self.data_raw = df
        self.symbol = symbol
        self.strategy_func = strategy_func
        self.initial_capital = initial_capital
        self.lot_size_fixed = lot_size_fixed
        self.spread_in_price = spread_pips * 0.0001
        self.commission_cost = commission_per_lot * lot_size_fixed
        self.pip_value_usd = pip_value_usd
        self.current_position = 0
        self.entry_price = 0.0
        self.equity_curve = []
        self.data = pd.DataFrame()

    def calculate_pnl_usd(self, entry_price, exit_price, position_type, lot_size):
        pips = (exit_price - entry_price) * 10000
        if position_type == -1:
            pips = (entry_price - exit_price) * 10000
        
        usd_pnl = pips * self.pip_value_usd * lot_size
        return usd_pnl

    def run_backtest(self):
        self.data = self.strategy_func(self.data_raw, self.symbol)
        if self.data.empty:
            print(f"La stratégie n'a généré aucune donnée pour {self.symbol}.")
            return False
        
        self.data = self.data.dropna()
        self.equity_curve = [self.initial_capital]
        self.current_position = 0
        self.entry_price = 0.0

        for i in range(1, len(self.data)):
            signal = self.data['signal'].iloc[i]
            close_price = self.data['close'].iloc[i]
            
            ask_price = close_price + self.spread_in_price
            bid_price = close_price
            
            capital = self.equity_curve[-1]

            if self.current_position == 0:
                if signal == 1:
                    self.current_position = 1
                    self.entry_price = ask_price
                    capital -= self.commission_cost
                elif signal == -1:
                    self.current_position = -1
                    self.entry_price = bid_price
                    capital -= self.commission_cost
            
            elif self.current_position == 1:
                if signal == -1 or signal == 0:
                    exit_price = bid_price
                    pnl = self.calculate_pnl_usd(self.entry_price, exit_price, 1, self.lot_size_fixed)
                    capital += pnl
                    capital -= self.commission_cost
                    
                    self.current_position = 0
                    self.entry_price = 0.0
                    
                    if signal == -1:
                        self.current_position = -1
                        self.entry_price = bid_price
                        capital -= self.commission_cost

            elif self.current_position == -1:
                if signal == 1 or signal == 0:
                    exit_price = ask_price
                    pnl = self.calculate_pnl_usd(self.entry_price, exit_price, -1, self.lot_size_fixed)
                    capital += pnl
                    capital -= self.commission_cost
                    
                    self.current_position = 0
                    self.entry_price = 0.0
                    
                    if signal == 1:
                        self.current_position = 1
                        self.entry_price = ask_price
                        capital -= self.commission_cost
                        
            self.equity_curve.append(capital)
        
        self.data['equity'] = self.equity_curve
        return True

    def plot_equity_curve(self):
        plt.figure(figsize=(12, 7))
        plt.plot(self.data.index, self.data['equity'], label='Capital Stratégie')
        plt.title(f'Courbe de Capital (Equity Curve) pour {self.symbol}')
        plt.ylabel('Capital (USD)')
        plt.xlabel('Date')
        plt.legend()
        plt.grid(True)
        plt.show()

    def get_stats(self):
        total_return = (self.equity_curve[-1] / self.initial_capital - 1) * 100
        print(f"--- Statistiques du Backtest Événementiel ---")
        print(f"Capital Initial: {self.initial_capital:,.2f} USD")
        print(f"Capital Final: {self.equity_curve[-1]:,.2f} USD")
        print(f"Retour Total: {total_return:.2f}%")

if __name__ == "__main__":
    
    if initialize_mt5():
        print(f"--- Lancement du Backtest Événementiel pour {SYMBOL} ---")
        
        data = get_data_from_mt5(SYMBOL, TIMEFRAME, N_BARS)
        
        if data is not None:
            
            backtester = EventDrivenBacktester(
                df=data,
                symbol=SYMBOL,
                strategy_func=Strategy,
                initial_capital=INITIAL_CAPITAL,
                lot_size_fixed=LOT_SIZE,
                spread_pips=SPREAD_PIPS,
                commission_per_lot=COMMISSION_PER_LOT,
                pip_value_usd=PIP_VALUE_USD_PER_LOT
            )
            
            success = backtester.run_backtest()
            
            if success:
                backtester.get_stats()
                backtester.plot_equity_curve()
            else:
                print("Échec de l'exécution du backtest.")
                
        else:
            print("Impossible de récupérer les données pour le backtest.")

        shutdown_mt5()
    else:
        print("Impossible d'initialiser MT5. Vérifiez que le terminal est lancé.")