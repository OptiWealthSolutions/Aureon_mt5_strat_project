import MetaTrader5 as mt5
import time
from datetime import datetime
import pandas as pd
from data_fetcher import initialize_mt5, get_data_from_mt5, shutdown_mt5
from strategy import Strategy
from trade_executor import place_market_order, close_all_positions_for_symbol, check_open_positions
from risk_manager import risk_manager 

# --- PARAMÈTRES GLOBAUX ---
FOREX_UNIVERSE = ["EURUSD"] # Ajoutez vos paires ici

# Configuration MTF
TIMEFRAME_BASE = mt5.TIMEFRAME_M15
# Clé = Enum MT5 (Entier), Valeur = Suffixe (Chaîne)
TF_MAP = {
    mt5.TIMEFRAME_M30: 'M30',
    mt5.TIMEFRAME_H1: 'H1',
    mt5.TIMEFRAME_H4: 'H4',
    mt5.TIMEFRAME_D1: 'D1'
}

RISK_MAX = 0.02
CONFIDENCE_INDEX = 1.0
sleeping_time = 900  # 15 minutes
window = 14
N_BARS_FETCH = 1000

def check_symbol_for_signal(symbol):
    try:
        print(f"\n--- Vérification de {symbol} ---")
        
        # 1. FETCH ET FUSION DES DONNÉES MTF
        
        # Récupération de la base (M15)
        df_base = get_data_from_mt5(symbol, TIMEFRAME_BASE, N_BARS_FETCH)           
        if df_base is None:
            print(f"Impossible de récupérer les données de base pour {symbol}.")
            return
            
        df_raw = df_base.copy()

        # Boucle pour récupérer et fusionner les timeframes supérieures
        # tf_mt5_enum = L'entier (ex: 16388) -> Pour la requête MT5
        # tf_name_str = La chaîne (ex: 'H4') -> Pour le nom des colonnes
        for tf_mt5_enum, tf_name_str in TF_MAP.items():
            
            # Utilisation de l'ENUM pour la requête (Correct)
            df_high_tf = get_data_from_mt5(symbol, tf_mt5_enum, N_BARS_FETCH)
            
            if df_high_tf is not None and not df_high_tf.empty:
                
                # Sélection des colonnes à garder
                cols_to_merge = ['open', 'high', 'low', 'close', 'tick_volume']
                cols_to_merge = [col for col in cols_to_merge if col in df_high_tf.columns]
                
                # Renommage avec la CHAÎNE (Correct: crée 'close_H4')
                df_high_tf_clean = df_high_tf[cols_to_merge].rename(
                    columns={col: f'{col}_{tf_name_str}' for col in cols_to_merge}
                )

                # Alignement sur l'index de base (M15)
                df_high_tf_clean = df_high_tf_clean.reindex(df_raw.index, method='ffill')

                # Fusion
                df_raw = df_raw.merge(
                    df_high_tf_clean, 
                    left_index=True, 
                    right_index=True, 
                    how='left'
                )
            else:
                print(f"Avertissement: Échec de la récupération des données pour le TF {tf_name_str}.")
        
        # --- 2. CALCUL DE LA STRATÉGIE ET DU RISQUE ---
        
        # df_raw contient maintenant 'close', 'close_H4', etc.
        df_strategy = Strategy(df_raw, symbol)
        
        # Gestion du risque
        LOT_SIZE_DF = risk_manager(df_raw, 10000, RISK_MAX, CONFIDENCE_INDEX) 
        
        if df_strategy.empty or 'signal' not in df_strategy.columns:
            print(f"ERREUR: Stratégie n'a pas retourné de signal pour {symbol}.")
            return
            
        if LOT_SIZE_DF.empty or 'Lot_Size' not in LOT_SIZE_DF.columns:
            print(f"ERREUR: Risk Manager n'a pas retourné de taille de lot pour {symbol}.")
            final_lot_size = 0.01 # Fallback sécurité
        else:
            final_lot_size = LOT_SIZE_DF['Lot_Size'].iloc[-1]

        # 3. Prise de Décision
        last_signal = df_strategy['signal'].iloc[-1]
        current_position = check_open_positions(symbol) 

        print(f"[{symbol}] Dernier signal: {last_signal} | Position actuelle: {current_position}")
        
        # --- 4. EXÉCUTION DES ORDRES ---
        
        if last_signal == 1:
            if current_position == 0:
                print(f"ACTION ({symbol}): Signal d'achat détecté. Ouverture LONG.")
                print(f"LOT SIZE CALCULÉ: {final_lot_size} lots")
                place_market_order(symbol, mt5.ORDER_TYPE_BUY, final_lot_size)
            elif current_position == -1:
                print(f"ACTION ({symbol}): Renversement. Fermeture SHORT...")
                close_all_positions_for_symbol(symbol)
                time.sleep(1)
                place_market_order(symbol, mt5.ORDER_TYPE_BUY, final_lot_size)
            
        elif last_signal == -1:
            if current_position == 0:
                print(f"ACTION ({symbol}): Signal de vente détecté. Ouverture SHORT.")
                print(f"LOT SIZE CALCULÉ: {final_lot_size} lots")
                place_market_order(symbol, mt5.ORDER_TYPE_SELL, final_lot_size)
            elif current_position == 1:
                print(f"ACTION ({symbol}): Renversement. Fermeture LONG...")
                close_all_positions_for_symbol(symbol)
                time.sleep(1)
                place_market_order(symbol, mt5.ORDER_TYPE_SELL, final_lot_size)
            
        else:
            print(f"ACTION ({symbol}): Signal neutre. Maintien.")
            
    except Exception as e:
        print(f"ERREUR CRITIQUE lors du traitement de {symbol}: {e}")
        import traceback
        traceback.print_exc() # Affiche les détails pour comprendre


def run_bot():
    print("Démarrage de Aureon FX - Scanner MTF")
    
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
            print("\nArrêt du bot demandé par l'utilisateur.")
            break
        except Exception as e:
            print(f"Une erreur critique est survenue dans la boucle principale: {e}")
            break 

    shutdown_mt5()
    print("Bot arrêté.")

if __name__ == "__main__":
    run_bot()