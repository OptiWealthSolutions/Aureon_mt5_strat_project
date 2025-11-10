import MetaTrader5 as mt5
import time
from datetime import datetime

from data_fetcher import initialize_mt5, get_data_from_mt5, shutdown_mt5

# univers de trading :
FOREX_UNIVERSE = [
    "EURUSD", 
    "GBPUSD", 
    "USDJPY", 
    "AUDUSD", 
    "USDCAD", 
    "NZDUSD", 
    "USDCHF"
]

# Strategy Params 

TIMEFRAME = mt5.TIMEFRAME_M1 
SMA_SHORT = 7
SMA_LONG = 20
LOT_SIZE = 0.03 
sleeping_time = 60
def check_symbol_for_signal(symbol):
    """_
    Exécute toute la logique de vérification pour UN SEUL symbole.
    """
    print(f"\n--- Vérification de {symbol} ---")
    try:

        n_bars = SMA_LONG + 50 
        df_raw = get_data_from_mt5(symbol, TIMEFRAME, n_bars)
        


        # df_strategy = add_moving_average_signals(df_raw, SMA_SHORT, SMA_LONG)


        last_signal = df_strategy['signal'].iloc[-1]
        # current_position = check_open_positions(symbol) 

        print(f"[{symbol}] Dernier signal: {last_signal} | Position actuelle: {current_position}")


        if last_signal == 1 and current_position == 0:
            print(f"ACTION ({symbol}): Signal d'achat détecté. Ouverture d'une position LONG.")
            place_market_order(symbol, mt5.ORDER_TYPE_BUY, LOT_SIZE)
        
        elif last_signal == -1 and current_position == 1:
            print(f"ACTION ({symbol}): Signal de vente détecté. Fermeture de la position LONG.")
            close_all_positions_for_symbol(symbol)
        
        else:
            print(f"ACTION ({symbol}): Ne rien faire.")
            
    except Exception as e:
        print(f"ERREUR lors du traitement de {symbol}: {e}")


def run_bot():
    print("Démarrage de Areon FX ")
    
    if not initialize_mt5():
        print("Échec de l'initialisation de MT5. Arrêt du bot.")
        return
    while True:
        try:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] --- NOUVEAU CYCLE DE SCAN ---")

            for symbol in FOREX_UNIVERSE:
                check_symbol_for_signal(symbol)
                time.sleep(1)

            print(f"\n--- Cycle de scan terminé. Attente de {sleeping_time} secondes... ---")
            time.sleep(sleeping_time) 

        except KeyboardInterrupt:
            # Crtl + C pour arrêter le bot
            print("\nArrêt du bot demandé par l'utilisateur.")
            break
        except Exception as e:
            # Gestion des erreurs inconnues
            print(f"Une erreur critique est survenue dans la boucle principale: {e}")
            break 

    shutdown_mt5()
    print("Bot arrêté.")

if __name__ == "__main__":
    run_bot()