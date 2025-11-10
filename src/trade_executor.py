import MetaTrader5 as mt5

def check_open_positions(symbol):
    """
    Vérifie s'il y a une position ouverte pour ce symbole.
    Renvoie:
     0 = Pas de position (Flat)
     1 = Position Long
    -1 = Position Short (Non géré dans ce bot simple)
    """
    positions = mt5.positions_get(symbol=symbol)
    
    if positions is None or len(positions) == 0:
        return 0 # Pas de position
    
    # S'il y a des positions, on regarde la première
    pos = positions[0]
    if pos.type == mt5.POSITION_TYPE_BUY:
        return 1  # Long
    elif pos.type == mt5.POSITION_TYPE_SELL:
        return -1 # Short
    
    return 0

def place_market_order(symbol, order_type, lot_size, sl_price=None, tp_price=None):
    """
    Envoie un ordre au marché (Achat ou Vente) à MT5.
    
    :param symbol: Le symbole à trader
    :param order_type: mt5.ORDER_TYPE_BUY ou mt5.ORDER_TYPE_SELL
    :param lot_size: Taille du lot
    :param sl_price: Prix du Stop Loss
    :param tp_price: Prix du Take Profit
    :return: True si succès, False si échec
    """
    print(f"Tentative d'envoi d'ordre : {order_type} {lot_size} lot(s) de {symbol}")

    # Déterminer le prix d'entrée
    if order_type == mt5.ORDER_TYPE_BUY:
        price = mt5.symbol_info_tick(symbol).ask
    else: # ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid

    # Préparation de la requête
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(lot_size),
        "type": order_type,
        "price": price,
        "magic": 123456,  # "Magic Number" pour identifier les ordres de ce bot
        "comment": "Bot MM Crossover",
        "type_time": mt5.ORDER_TIME_GTC, # Good till cancelled
        "type_filling": mt5.ORDER_FILLING_FOK, # Fill or Kill
    }
    
    # Ajout du SL et TP s'ils sont fournis (non utilisé dans main.py pour l'instant)
    if sl_price:
        request["sl"] = float(sl_price)
    if tp_price:
        request["tp"] = float(tp_price)

    # Envoi de l'ordre
    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"--- ÉCHEC de l'envoi de l'ordre ---")
        print(f"Code de retour: {result.retcode} - {result.comment}")
        return False
    else:
        print(f"--- SUCCÈS de l'ordre ---")
        print(f"Ticket: {result.order}")
        return True

def close_all_positions_for_symbol(symbol):
    """
    Ferme toutes les positions ouvertes pour un symbole donné.
    """
    positions = mt5.positions_get(symbol=symbol)
    if positions is None or len(positions) == 0:
        print(f"Pas de position ouverte à fermer pour {symbol}.")
        return

    print(f"Fermeture de {len(positions)} position(s) pour {symbol}...")
    
    for pos in positions:
        # Déterminer l'ordre inverse
        if pos.type == mt5.POSITION_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(symbol).bid
        else: # POSITION_TYPE_SELL
            order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol).ask
            
        lot_size = pos.volume
        
        # Création d'un ordre inverse pour fermer la position
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(lot_size),
            "type": order_type,
            "position": pos.ticket, # Spécifie la position à fermer
            "price": price,
            "magic": 123456,
            "comment": "Fermeture Bot MM",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Échec de la fermeture du ticket {pos.ticket}: {result.comment}")
        else:
            print(f"Position {pos.ticket} fermée avec succès.")