import MetaTrader5 as mt5
import time
from datetime import datetime
import pandas as pd
from data_fetcher import initialize_mt5, get_data_from_mt5, shutdown_mt5
from strategy import Strategy
from trade_executor import place_market_order, close_all_positions_for_symbol, check_open_positions
from risk_manager import risk_manager # Le nouveau module

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
TIMEFRAME = mt5.TIMEFRAME_M1 
RISK_MAX = 0.02
CONFIDENCE_INDEX = 1.0

# Bot Params
sleeping_time = 60
window = 14

def check_symbol_for_signal(symbol):
    print(f"\n--- Vérification de {symbol} ---")
    try:
        # Assurez-vous d'avoir assez de barres pour les indicateurs (window)
        n_bars = window + 50     
        
        # --- FETCH 1 UNIQUE FOIS ---
        df_raw = get_data_from_mt5(symbol, TIMEFRAME, n_bars)
        
        if df_raw is None:
            print(f"Impossible de récupérer les données pour {symbol}.")
            return

        # 1. Calcul de la Stratégie (Signaux)
        df_strategy = Strategy(df_raw, symbol)

        # 2. Calcul du Lot Size (Gestion du Risque)
        # --- CORRECTION DE LA REDONDANCE : UTILISE DF_RAW ---
        # Le 1000 est une valeur à remplacer par le capital actuel si vous le pouvez
        LOT_SIZE_DF = risk_manager(df_raw, 10000, RISK_MAX, CONFIDENCE_INDEX) 

        if LOT_SIZE_DF.empty or 'Lot_Size' not in LOT_SIZE_DF.columns:
            print(f"ERREUR: Lot size non calculé pour {symbol}.")
            return
            
        final_lot_size = LOT_SIZE_DF['Lot_Size'].iloc[-1]

        # 3. Prise de Décision
        last_signal = df_strategy['signal'].iloc[-1]
        current_position = check_open_positions(symbol) # 0=Flat, 1=Long, -1=Short

        print(f"[{symbol}] Dernier signal: {last_signal} | Position actuelle: {current_position}")
        
        # --- 4. EXÉCUTION DES ORDRES ---
        
        # CAS 1: Signal d'ACHAT (1)
        if last_signal == 1:
            if current_position == 0:
                # Flat -> Ouvrir LONG
                print(f"ACTION ({symbol}): Signal d'achat détecté. Ouverture d'une position LONG.")
                print(f"LOT SIZE CALCULÉ: {final_lot_size} lots")
                place_market_order(symbol, mt5.ORDER_TYPE_BUY, final_lot_size)
            elif current_position == -1:
                # Short -> Fermer SHORT (Renversement)
                print(f"ACTION ({symbol}): Renversement. Fermeture de la position SHORT.")
                close_all_positions_for_symbol(symbol)
            # Sinon (current_position == 1): Maintien
        
        # CAS 2: Signal de VENTE (-1)
        elif last_signal == -1:
            if current_position == 0:
                # Flat -> Ouvrir SHORT
                print(f"ACTION ({symbol}): Signal de vente détecté. Ouverture d'une position SHORT.")
                print(f"LOT SIZE CALCULÉ: {final_lot_size} lots")
                place_market_order(symbol, mt5.ORDER_TYPE_SELL, final_lot_size)
            elif current_position == 1:
                # Long -> Fermer LONG (Renversement)
                print(f"ACTION ({symbol}): Renversement. Fermeture de la position LONG.")
                close_all_positions_for_symbol(symbol)
            # Sinon (current_position == -1): Maintien
        
        # CAS 3: Signal NEUTRE (0)
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