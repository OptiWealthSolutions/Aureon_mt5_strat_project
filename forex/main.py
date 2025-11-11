import MetaTrader5 as mt5
import time
from datetime import datetime

from data_fetcher import initialize_mt5, get_data_from_mt5, shutdown_mt5
from strategy import Strategy
from trade_executor import place_market_order, close_all_positions_for_symbol, check_open_positions

# univers de trading :
FOREX_UNIVERSE = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "USDCHF",
    "EURGBP", "EURJPY", "EURAUD", "EURCAD", "EURNZD", "EURCHF",
    "GBPJPY", "GBPAUD", "GBPCAD", "GBPNZD", "GBPCHF",
    "AUDJPY", "AUDCAD", "AUDNZD", "AUDCHF",
    "NZDJPY", "NZDCAD", "NZDCHF",
    "CADJPY", "CADCHF",
    "CHFJPY",
]
# Strategy Params 
TIMEFRAME = mt5.TIMEFRAME_H1 
Risk_max = 0.02
LOT_SIZE = 0.03 
sleeping_time = 60
window = 14

def check_symbol_for_signal(symbol):
    print(f"\n--- Vérification de {symbol} ---")
    try:
   
        n_bars = window + 50    
        df_raw = get_data_from_mt5(symbol, TIMEFRAME, n_bars)
        
        if df_raw is None:
            print(f"Impossible de récupérer les données pour {symbol}.")
            return
        df_strategy = Strategy(df_raw)
        
        last_signal = df_strategy['signal'].iloc[-1]
        current_position = check_open_positions(symbol) # 0=Flat, 1=Long, -1=Short

        print(f"[{symbol}] Dernier signal: {last_signal} | Position actuelle: {current_position}")

        
        # CAS 1: Signal d'ACHAT (1)
        if last_signal == 1:
            if current_position == 0:
                # On est FLAT -> On ouvre LONG
                print(f"ACTION ({symbol}): Signal d'achat détecté. Ouverture d'une position LONG.")
                place_market_order(symbol, mt5.ORDER_TYPE_BUY, LOT_SIZE)
            elif current_position == -1:
                # On est SHORT -> On ferme le SHORT
                print(f"ACTION ({symbol}): Signal d'achat (inverse) détecté. Fermeture de la position SHORT.")
                close_all_positions_for_symbol(symbol)
            else: # current_position == 1
                print(f"ACTION ({symbol}): Signal d'achat, mais déjà LONG. On ne fait rien.")
            # CAS 2: Signal de VENTE (-1)
        elif last_signal == -1:
            if current_position == 0:
                # On est FLAT -> On ouvre SHORT
                print(f"ACTION ({symbol}): Signal de vente détecté. Ouverture d'une position SHORT.")
                place_market_order(symbol, mt5.ORDER_TYPE_SELL, LOT_SIZE)
            elif current_position == 1:
                print(f"ACTION ({symbol}): Signal de vente (inverse) détecté. Fermeture de la position LONG.")
                close_all_positions_for_symbol(symbol)
            else: # current_position == -1
                print(f"ACTION ({symbol}): Signal de vente, mais déjà SHORT. On ne fait rien.")
        else:
            print(f"ACTION ({symbol}): Signal neutre. Maintien de la position ({current_position}).")
            
    except Exception as e:
        print(f"ERREUR lors du traitement de {symbol}: {e}")


def run_bot():
    print("Démarrage de Aureon FX ")
    
    if not initialize_mt5():
        print("Échec de l'initialisation de MT5. Arrêt du bot.")
        return
        
    while True:
        try:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] --- NOUVEAU CYCLE DE SCAN ---")

            for symbol in FOREX_UNIVERSE:
                check_symbol_for_signal(symbol)
                time.sleep(1) # Petite pause entre chaque symbole

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