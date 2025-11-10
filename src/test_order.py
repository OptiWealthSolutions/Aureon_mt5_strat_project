import MetaTrader5 as mt5
import time

# Importer les modules dont nous avons besoin
from data_fetcher import initialize_mt5, shutdown_mt5
from trade_executor import place_market_order, close_all_positions_for_symbol

# --- Paramètres du Test ---
SYMBOL_TO_TEST = "EURUSD"
LOT_SIZE_TO_TEST = 0.01

def run_order_test():
    """
    Script de test pour valider l'envoi d'ordres.
    Il va :
    1. Se connecter à MT5.
    2. Envoyer un ordre d'achat au marché.
    3. Attendre 10 secondes.
    4. Fermer toutes les positions pour ce symbole.
    """
    print("--- DÉMARRAGE DU TEST D'ORDRE ---")
    
    if not initialize_mt5():
        print("Échec de l'initialisation de MT5. Le test ne peut pas continuer.")
        return

    # S'assurer que le symbole est bien visible
    # (Copie de la logique de data_fetcher)
    symbol_info = mt5.symbol_info(SYMBOL_TO_TEST)
    if not symbol_info.visible:
        print(f"Le symbole {SYMBOL_TO_TEST} n'est pas visible, tentative d'ajout...")
        if not mt5.symbol_select(SYMBOL_TO_TEST, True):
            print(f"Échec de l'ajout du symbole {SYMBOL_TO_TEST}. Vérifiez le nom et l'Obs. du Marché.")
            shutdown_mt5()
            return
    
    print(f"\nSymbole {SYMBOL_TO_TEST} prêt.")

    # --- Étape 1 : Envoyer un ordre d'achat ---
    print("\n--- Étape 1 : Envoi d'un ordre d'achat test (BUY)... ---")
    
    # Note: On doit utiliser mt5.ORDER_TYPE_BUY
    success = place_market_order(
        symbol=SYMBOL_TO_TEST,
        order_type=mt5.ORDER_TYPE_BUY,
        lot_size=LOT_SIZE_TO_TEST
    )
    
    if not success:
        print(">>> L'ordre d'achat test a échoué. Vérifiez les messages ci-dessus.")
        print(">>> Causes possibles : 'Algo Trading' non activé (bouton vert), compte démo expiré, lot_size invalide, pas assez de marge.")
        shutdown_mt5()
        return

    print("\n>>> Ordre d'achat test envoyé avec succès.")
    
    # --- Étape 2 : Pause ---
    print("\n--- Étape 2 : Attente de 10 secondes... (Vérifiez votre terminal MT5 !) ---")
    time.sleep(10)

    # --- Étape 3 : Fermer la position ---
    print("\n--- Étape 3 : Tentative de fermeture de la position... ---")
    
    close_all_positions_for_symbol(SYMBOL_TO_TEST)
    
    print("\n>>> Test de fermeture terminé.")

    # --- Fin ---
    shutdown_mt5()
    print("\n--- TEST TERMINÉ ---")

# --- Point d'entrée du script de test ---
if __name__ == "__main__":
    # Pour exécuter le test :
    # python src/test_order.py
    run_order_test()