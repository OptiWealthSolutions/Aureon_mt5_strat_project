import MetaTrader5 as mt5
import time
from datetime import datetime

# Importer nos modules personnalisés
# (Nous avons data_fetcher.py et strategy.py)
from data_fetcher import initialize_mt5, get_data_from_mt5, shutdown_mt5
from strategy import add_moving_average_signals
# (Nous venons de créer trade_executor.py)
from trade_executor import place_market_order, close_all_positions_for_symbol, check_open_positions

# --- Paramètres du Bot ---
SYMBOL = "EURUSD"
TIMEFRAME = mt5.TIMEFRAME_H1 # Timeframe H1
SMA_SHORT = 50
SMA_LONG = 200
LOT_SIZE = 0.01 # Taille de lot fixe (simplifié)

def run_bot():
    """
    La fonction principale qui exécute la boucle du bot.
    """
    print(f"Démarrage du Bot de trading ({SYMBOL}, {TIMEFRAME})")
    
    if not initialize_mt5():
        print("Échec de l'initialisation de MT5. Arrêt du bot.")
        return

    # Boucle principale du bot
    while True:
        try:
            # --- 1. Récupérer les Données ---
            # Assez de données pour la MM longue
            n_bars = SMA_LONG + 50 
            df_raw = get_data_from_mt5(SYMBOL, TIMEFRAME, n_bars)
            
            if df_raw is None:
                print("Impossible de récupérer les données, nouvelle tentative dans 30s...")
                time.sleep(30) # Attend avant de réessayer
                continue # Redémarre la boucle

            # --- 2. Calculer la Stratégie ---
            df_strategy = add_moving_average_signals(df_raw, SMA_SHORT, SMA_LONG)
            
            if df_strategy.empty:
                print("DataFrame de stratégie vide (pas assez de données ?), nouvelle tentative dans 30s...")
                time.sleep(30)
                continue
                
            # --- 3. Prendre la Décision ---
            
            # Obtenir le TOUT DERNIER signal (-1, 0, ou 1)
            last_signal = df_strategy['signal'].iloc[-1]
            
            # Obtenir la position actuelle (0=Flat, 1=Long)
            current_position = check_open_positions(SYMBOL) 

            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Dernier signal: {last_signal} | Position actuelle: {current_position}")

            # --- 4. Exécuter les Ordres ---
            # Stratégie Long-Only
            
            # CAS 1: Signal d'ACHAT (1) et nous sommes FLAT (0)
            if last_signal == 1 and current_position == 0:
                print("ACTION: Signal d'achat détecté. Ouverture d'une position LONG.")
                place_market_order(SYMBOL, mt5.ORDER_TYPE_BUY, LOT_SIZE)
            
            # CAS 2: Signal de VENTE (-1) et nous sommes LONG (1)
            elif last_signal == -1 and current_position == 1:
                print("ACTION: Signal de vente détecté. Fermeture de la position LONG.")
                close_all_positions_for_symbol(SYMBOL)
            
            # Autres cas: Ne rien faire (Hold)
            else:
                print("ACTION: Ne rien faire.")

            # --- 5. Attendre ---
            # Attend 60 secondes avant de revérifier.
            print("Attente de 60 secondes avant la prochaine vérification...")
            time.sleep(60) 

        except KeyboardInterrupt:
            # Permet d'arrêter le bot proprement avec Ctrl+C
            print("\nArrêt du bot demandé par l'utilisateur.")
            break
        except Exception as e:
            # Gestion des erreurs inconnues
            print(f"Une erreur critique est survenue: {e}")
            break 

    # Fermer la connexion MT5 en sortant de la boucle
    shutdown_mt5()
    print("Bot arrêté.")

# --- Point d'entrée du script ---
if __name__ == "__main__":
    # Pour exécuter le bot, lancez ce fichier depuis votre terminal:
    # (assurez-vous que votre .venv est activé)
    # python src/main.py
    run_bot()