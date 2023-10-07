import ccxt
from datetime import datetime
from binance_api import api_key, api_secret
# Place order: {'info': {'orderId': '1181914767', 'symbol': 'ETHUSDT', 'status': 'FILLED', 'clientOrderId': 'x-xcKtGhcuc97390e896fa0ba7cc9792', 'price': '0.00', 'avgPrice': '1632.91000', 'origQty': '6.002', 'executedQty': '6.002', 'cumQty': '6.002', 'cumQuote': '9800.72582', 'timeInForce': 'GTC', 'type': 'MARKET', 'reduceOnly': False, 'closePosition': False, 'side': 'SELL', 'positionSide': 'BOTH', 'stopPrice': '0.00', 'workingType': 'CONTRACT_PRICE', 'priceProtect': False, 'origType': 'MARKET', 'priceMatch': 'NONE', 'selfTradePreventionMode': 'NONE', 'goodTillDate': '0', 'updateTime': '1696583689637'}, 'id': '1181914767', 'clientOrderId': 'x-xcKtGhcuc97390e896fa0ba7cc9792', 'timestamp': 1696583689637, 'datetime': '2023-10-06T09:14:49.637Z', 'lastTradeTimestamp': 1696583689637, 'lastUpdateTimestamp': 1696583689637, 'symbol': 'ETH/USDT:USDT', 'type': 'market', 'timeInForce': 'GTC', 'postOnly': False, 'reduceOnly': False, 'side': 'sell', 'price': 1632.91, 'triggerPrice': None, 'amount': 6.002, 'cost': 9800.72582, 'average': 1632.91, 'filled': 6.002, 'remaining': 0.0, 'status': 'closed', 'fee': {'currency': None, 'cost': None, 'rate': None}, 'trades': [], 'fees': [{'currency': None, 'cost': None, 'rate': None}], 'stopPrice': None, 'takeProfitPrice': None, 'stopLossPrice': None}
class Whale:
    def __init__(self, exchange, symbol, leverage=100):
        self.exchange = exchange
        self.symbol = symbol
        self.leverage = leverage
        self.test_mode = True
    def get_account_balance(self):
        if self.test_mode:
            return 100
        balance = self.exchange.fetch_balance()
        return balance['total']['USDT']
    
    def get_last_price(self):
        ticker = self.exchange.fetch_ticker(self.symbol)
        return ticker['last']

    def get_order_book(self):
        order_book = self.exchange.fetch_order_book(self.symbol)
        return order_book

    def get_best_bid_and_ask(self):
        order_book = self.get_order_book()
        return order_book['bids'][0][0], order_book['asks'][0][0]

    def calculate_trade_quantity(self):
        balance = self.get_account_balance()
        leveraged_balance = min(balance * self.leverage, 100000)
        quantity = leveraged_balance / self.get_last_price()
        return quantity

    def place_trailing_stop_order(self, side):
        # Side could be 'buy' or 'sell'
        quantity = self.calculate_trade_quantity()
        best_bid, best_ask = self.get_best_bid_and_ask()
        price = best_bid if side == 'buy' else best_ask

        try:
            order = self.exchange.create_order(
                self.symbol,
                'trailing_stop',
                side,
                quantity,
                {
                    'stopPrice': price,
                    'reduceOnly': True
                }
            )
        except ccxt.BaseError as e:
            print(f"An error occurred: {e}")

        return order

    def place_first_post_only_order(self, side):
        # Side could be 'buy' or 'sell'
        quantity = self.calculate_trade_quantity()
        best_bid, best_ask = self.get_best_bid_and_ask()
        price = best_bid if side == 'buy' else best_ask

        try:
            order = self.exchange.create_limit_order(
                self.symbol,
                side,
                quantity,
                price,
                {
                    'postOnly': True,
                    'timeInForce': 'PO'  
                }
            )
        except ccxt.BaseError as e:
            print(f"An error occurred: {e}")

        return order

    def place_first_market_order(self, side):
        # Side could be 'buy' or 'sell'
        quantity = self.calculate_trade_quantity()
        order = self.exchange.create_market_order(
            self.symbol,
            side,
            quantity,
            {
                'reduceOnly': False
            }
        )
        return order

    def is_position_open(self):
        # position = self.exchange.fetch_positions([self.symbol])
        positions = self.exchange.fetch_positions([symbol])
        current_position_Amt_abs = abs(float(positions[0]['info']['positionAmt']))
        position_exists = (current_position_Amt_abs > 0 or current_position_Amt_abs < 0)
        return position_exists

    def place_second_take_profit_and_stop_loss_orders(self):
        try:
            if self.is_position_open():
                position = self.exchange.fetch_positions([self.symbol])
                if not position:
                    raise Exception("No position information found.")

                quantity = abs(float(position[0]['info']['positionAmt']))
                side = 'sell' if position[0]['side'] == 'long' else 'buy'

                entry_price = float(position[0]['info']['entryPrice'])
                take_profit_price = entry_price * (1.0006 if side == 'sell' else 0.9994)
                stop_loss_price = entry_price * (0.9996 if side == 'sell' else 1.0004)

                try:
                    take_profit_order = self.exchange.create_limit_order(
                        symbol=self.symbol,
                        side=side,
                        price=take_profit_price,
                        amount=quantity,
                        params={
                            'postOnly': True,
                            'timeInForce': 'PO',
                            'reduceOnly': True
                        }
                    )
                except ccxt.BaseError as e:
                    print(f"An error occurred in creating take-profit order: {e}")

                try:
                    stop_loss_order = self.exchange.create_order(
                        symbol=self.symbol,
                        type='stop_market',
                        side=side,
                        amount=quantity,
                        params={
                            'stopPrice': stop_loss_price,
                            'reduceOnly': True
                        }
                    )
                    
                except ccxt.BaseError as e:
                    print(f"An error occurred in creating stop-loss order: {e}")

            return take_profit_order, stop_loss_order

        except Exception as e:
            print(f"Error in placing second orders: {str(e)}")
            return None, None

    def close_open_orders(self):
        open_orders = self.exchange.fetch_open_orders(self.symbol)
        for order in open_orders:
            self.exchange.cancel_order(order['id'], self.symbol)
        return open_orders

    def close_position_with_market_order(self):
        position = self.exchange.fetch_positions([self.symbol])
        quantity = abs(float(position[0]['info']['positionAmt']))
        side = 'sell' if position[0]['side'] == 'long' else 'buy'
        order = self.exchange.create_market_order(
            self.symbol,
            side,
            quantity,
            {
                'reduceOnly': True
            }
        )
        return order

    def close_position_and_orders(self):
        try:
            self.close_open_orders()
        except Exception as e:
            print(f"Error in closing open orders: {str(e)}")

        try:
            self.close_position_with_market_order()
        except Exception as e:
            print(f"Error in closing position: {str(e)}")


# Replace with your API key and secret
symbol = 'ETH/USDT'

exchange = ccxt.binance({
    'options': {
        'defaultType': 'future',
        'newUpdates': True 
    },
    'apiKey': api_key,
    'secret': api_secret
})
# binance = exchange.load_markets()
exchange.set_sandbox_mode(True)

# Create an instance of the Whale class
whale_1 = Whale(exchange, symbol)
whale_1.calculate_trade_quantity()
