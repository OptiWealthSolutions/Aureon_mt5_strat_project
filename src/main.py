import MetaTrader5 as mt5
import time
from datetime import datetime

# Importer nos modules personnalisés
from data_fetcher import initialize_mt5, get_data_from_mt5, shutdown_mt5
from strategy import add_moving_average_signals
from trade_executor import place_market_order, close_all_positions_for_symbol, check_open_positions

# --- Paramètres du Bot ---

# 1. DÉFINISSEZ VOTRE UNIVERS FOREX ICI
# Commencez par les paires majeures
FOREX_UNIVERSE = [
    "EURUSD", 
    "GBPUSD", 
    "USDJPY", 
    "AUDUSD", 
    "USDCAD", 
    "NZDUSD", 
    "USDCHF"
]
# Vous pouvez ajouter autant de paires que vous le souhaitez :
# "EURGBP", "EURJPY", "GBPJPY", "AUDJPY", etc.

TIMEFRAME = mt5.TIMEFRAME_M1 # Timeframe M1
SMA_SHORT = 7
SMA_LONG = 20
LOT_SIZE = 0.03 # Taille de lot fixe (simplifié)

def check_symbol_for_signal(symbol):
    """_
    Exécute toute la logique de vérification pour UN SEUL symbole.
    """
    print(f"\n--- Vérification de {symbol} ---")
    try:
        # --- 1. Récupérer les Données ---
        n_bars = SMA_LONG + 50 
        df_raw = get_data_from_mt5(symbol, TIMEFRAME, n_bars)
        
        if df_raw is None:
            print(f"Impossible de récupérer les données pour {symbol}.")
            return # Passe au symbole suivant

        # --- 2. Calculer la Stratégie ---
        df_strategy = add_moving_average_signals(df_raw, SMA_SHORT, SMA_LONG)
        
        if df_strategy.empty:
            print(f"DataFrame de stratégie vide pour {symbol}.")
            return # Passe au symbole suivant
            
        # --- 3. Prendre la Décision ---
        last_signal = df_strategy['signal'].iloc[-1]
        current_position = check_open_positions(symbol) 

        print(f"[{symbol}] Dernier signal: {last_signal} | Position actuelle: {current_position}")

        # --- 4. Exécuter les Ordres ---
        
        # CAS 1: Signal d'ACHAT (1) et nous sommes FLAT (0)
        if last_signal == 1 and current_position == 0:
            print(f"ACTION ({symbol}): Signal d'achat détecté. Ouverture d'une position LONG.")
            place_market_order(symbol, mt5.ORDER_TYPE_BUY, LOT_SIZE)
        
        # CAS 2: Signal de VENTE (-1) et nous sommes LONG (1)
        elif last_signal == -1 and current_position == 1:
            print(f"ACTION ({symbol}): Signal de vente détecté. Fermeture de la position LONG.")
            close_all_positions_for_symbol(symbol)
        
        # Autres cas: Ne rien faire
        else:
            print(f"ACTION ({symbol}): Ne rien faire.")
            
    except Exception as e:
        print(f"ERREUR lors du traitement de {symbol}: {e}")
        # Continue au symbole suivant même en cas d'erreur


def run_bot():
    """
    La fonction principale qui exécute la boucle du bot sur TOUS les symboles.
    """
    print("Démarrage du Bot Scanner de Marché (Multi-Symboles)")
    
    if not initialize_mt5():
        print("Échec de l'initialisation de MT5. Arrêt du bot.")
        return

    # Boucle principale du bot
    while True:
        try:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] --- NOUVEAU CYCLE DE SCAN ---")
            
            # Boucle sur chaque symbole de notre univers
            for symbol in FOREX_UNIVERSE:
                check_symbol_for_signal(symbol)
                time.sleep(1) # Petite pause pour ne pas surcharger l'API MT5

            # --- 5. Attendre ---
            # Attend 60 secondes APRÈS avoir scanné tous les symboles
            print("\n--- Cycle de scan terminé. Attente de 60 secondes... ---")
            time.sleep(60) 

        except KeyboardInterrupt:
            # Permet d'arrêter le bot proprement avec Ctrl+C
            print("\nArrêt du bot demandé par l'utilisateur.")
            break
        except Exception as e:
            # Gestion des erreurs inconnues
            print(f"Une erreur critique est survenue dans la boucle principale: {e}")
            break 

    # Fermer la connexion MT5 en sortant de la boucle
    shutdown_mt5()
    print("Bot arrêté.")

# --- Point d'entrée du script ---
if __name__ == "__main__":
    run_bot()