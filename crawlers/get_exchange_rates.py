import json
import config
import credentials
import currencylayer
import logging
import redis
import requests

"""
Gettig current exchange rates from APIs and writing them in Redis
"""

# Loading Redis
redit_db = redis.StrictRedis(host=config.redis_endpoint, port=6379, db=0)


def get_currency_rates():
    # Connecting to currencyl ayer API
    exchange_rate = currencylayer.Client(access_key=credentials.currencylayer_access_key)

    # Getting currency exchange rates
    try:
        rates = exchange_rate.live_rates(base_currency='USD')['quotes']
    except Exception as e:
        logging.warning(json.dumps({'incident': 'Failed to get rates from currencylayer', 'error': str(e)}))
    else:
        # Putting rates in Redis
        for currency, rate in rates.items():
            currency = currency.split('USD')[1]
            redit_db.set('rate_' + currency + '/USD', str(rate))


def get_stablecoin_rates():
    stable_coins = ['USDT', 'USDC', 'TUSD', 'PAX', 'GUSD', 'DAI',
                    'EURS', 'BITCNY', 'BITUSD', 'USNBT', 'SUSD',
                    'WSD', 'BITEUR', 'USC', 'SDS', 'COR']
    #  Getting stablecoins exchange rates
    for stable_coin in stable_coins:
        # Getting rates from coinmarketcap API
        coinmarketcap_url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol=' + stable_coin + '&convert=USD'
        r = requests.get(coinmarketcap_url, headers=credentials.coinmarketcap_headers)

        # Putting rates in Redis
        if r.status_code >= 200 and r.status_code < 300:
            rate = json.loads(r.text)['data'][stable_coin]['quote']['USD']['price']
            redit_db.set('rate_' + stable_coin + '/USD', str(rate))
        else:
            logging.warning(json.dumps({"incident": "Failed to get stable coin rates from coinmarketcap", "response": r.text, "status code": r.status_code}))


if __name__ == '__main__':
    get_currency_rates()
    get_stablecoin_rates()
