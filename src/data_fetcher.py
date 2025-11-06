import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

def initialize_mt5():
    if not mt5.initialize():
        print("init failed, error code =", mt5.last_error())
        return False
    print("MT5 initialized successfully")
    return True

def getDataFromMT5(symbol, timeframe,n_bars):
    if not mt5.initialize():
        print("MT5 initialization failed")
        return None
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_bars)

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)

def shutdown_mt5():
    mt5.shutdown()
    print("Connexion à MetaTrader 5 fermée.")