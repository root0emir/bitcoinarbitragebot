import requests
from flask import Flask, render_template, jsonify, request
from itertools import combinations
import threading
import time

app = Flask(__name__)

# supported crypto coins
API_URLS = {
    'Binance': {
        'BTC': 'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT',
        'ETH': 'https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT',
        'LTC': 'https://api.binance.com/api/v3/ticker/price?symbol=LTCUSDT'
    },
    'Kraken': {
        'BTC': 'https://api.kraken.com/0/public/Ticker?pair=XBTUSD',
        'ETH': 'https://api.kraken.com/0/public/Ticker?pair=ETHUSD',
        'LTC': 'https://api.kraken.com/0/public/Ticker?pair=LTCUSD'
    },
    'Coinbase': {
        'BTC': 'https://api.coinbase.com/v2/prices/BTC-USD/spot',
        'ETH': 'https://api.coinbase.com/v2/prices/ETH-USD/spot',
        'LTC': 'https://api.coinbase.com/v2/prices/LTC-USD/spot'
    },
    'Bitstamp': {
        'BTC': 'https://www.bitstamp.net/api/v2/ticker/btcusd/',
        'ETH': 'https://www.bitstamp.net/api/v2/ticker/ethusd/',
        'LTC': 'https://www.bitstamp.net/api/v2/ticker/ltcusd/'
    }
}


current_prices = {}


# api
def get_price(exchange, coin):
    try:
        url = API_URLS[exchange][coin]
        response = requests.get(url)
        data = response.json()

        if exchange == 'Binance':
            return float(data['price'])
        elif exchange == 'Kraken':
            pair = {'BTC': 'XXBTZUSD', 'ETH': 'XETHZUSD', 'LTC': 'XLTCZUSD'}[coin]
            return float(data['result'][pair]['c'][0])
        elif exchange == 'Coinbase':
            return float(data['data']['amount'])
        elif exchange == 'Bitstamp':
            return float(data['last'])
    except Exception as e:
        print(f"{exchange} {coin} fiyat verisi çekilemedi: {e}")
        return None


# all 
def fetch_all_prices(coins=['BTC', 'ETH', 'LTC']):
    prices = {}
    for coin in coins:
        prices[coin] = {}
        for exchange in API_URLS.keys():
            price = get_price(exchange, coin)
            if price:
                prices[coin][exchange] = price
    return prices


# check the arbitage
def check_arbitrage_opportunities():
    global current_prices
    coins = ['BTC', 'ETH', 'LTC']
    prices = fetch_all_prices(coins)
    opportunities = {}

    for coin in coins:
        opportunities[coin] = []
        if len(prices[coin]) < 2:
            continue

        for (exchange1, price1), (exchange2, price2) in combinations(prices[coin].items(), 2):
            if price1 > price2:
                profit = price1 - price2
                percent_diff = (profit / price2) * 100
                if percent_diff >= 1:
                    opportunities[coin].append({
                        'buy': exchange2,
                        'sell': exchange1,
                        'profit': round(profit, 2),
                        'percent_diff': round(percent_diff, 2)
                    })
            elif price2 > price1:
                profit = price2 - price1
                percent_diff = (profit / price1) * 100
                if percent_diff >= 1:
                    opportunities[coin].append({
                        'buy': exchange1,
                        'sell': exchange2,
                        'profit': round(profit, 2),
                        'percent_diff': round(percent_diff, 2)
                    })

    current_prices = {'prices': prices, 'opportunities': opportunities}


# real-time threading
def update_prices_periodically(interval=30):
    while True:
        check_arbitrage_opportunities()
        time.sleep(interval)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/data')
def get_data():
    return jsonify(current_prices)


if __name__ == '__main__':
    # threading
    threading.Thread(target=update_prices_periodically, daemon=True).start()
    # Flask server
    app.run(debug=True, port=5000)

