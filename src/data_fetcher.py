import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

def initialize_mt5():
    """
    Initialise la connexion au terminal MetaTrader 5.
    """
    if not mt5.initialize():
        print(f"initialize() a échoué, code d'erreur = {mt5.last_error()}")
        return False
    
    # Optionnel : vérifier les informations de connexion
    account_info = mt5.account_info()
    if account_info:
        print(f"Connexion réussie au compte #{account_info.login} sur {account_info.server}")
    else:
        print(f"Connexion réussie, mais impossible de récupérer les infos du compte. Erreur: {mt5.last_error()}")
        
    return True

def get_data_from_mt5(symbol, timeframe, n_bars):
    """
    Récupère les données de barres (OHLC) depuis MT5 pour un symbole donné,
    en s'assurant que le symbole est visible.
    
    :param symbol: Le nom du symbole (ex: "EURUSD")
    :param timeframe: La timeframe (ex: mt5.TIMEFRAME_H1)
    :param n_bars: Le nombre de barres à récupérer
    :return: un DataFrame pandas avec les données OHLC, ou None si échec
    """
    
    # 1. Vérifier si le symbole existe
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"ERREUR : Le symbole '{symbol}' n'existe pas chez votre courtier.")
        print("Vérifiez l'orthographe exacte (ex: 'EURUSDm' ?) dans votre terminal MT5.")
        return None

    # 2. S'assurer que le symbole est visible (dans l'Observatoire du marché)
    if not symbol_info.visible:
        print(f"Le symbole '{symbol}' n'est pas visible. Tentative d'ajout...")
        if not mt5.symbol_select(symbol, True):
            print(f"Échec de l'ajout du symbole '{symbol}' à l'Observatoire du marché.")
            print(f"Veuillez l'ajouter manuellement dans MT5. Erreur: {mt5.last_error()}")
            return None
        else:
            print(f"Symbole '{symbol}' ajouté avec succès.")
            
    # 3. Tenter de récupérer les données
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_bars)
    
    if rates is None or len(rates) == 0:
        print(f"Échec de la récupération des données pour '{symbol}'. rates est vide.")
        print(f"Cause possible : pas d'historique pour ce symbole/timeframe. Erreur MT5: {mt5.last_error()}")
        return None

    # 4. Conversion en DataFrame pandas
    df = pd.DataFrame(rates)
    
    # Conversion de la colonne 'time' en datetime (lisible par l'homme)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    
    print(f"Données pour {symbol} récupérées avec succès ({len(df)} barres).")
    return df

def shutdown_mt5():
    """
    Ferme proprement la connexion à MT5.
    """
    mt5.shutdown()
    print("Connexion à MetaTrader 5 fermée.")