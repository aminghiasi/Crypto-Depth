import boto3
import ccxt
import config
import datetime
import itertools
import json
import logging
import threading

"""
Gets market depth from 10 markets simultaneously using multithreading
"""

# Setting up Kinesis
try:
    kinesis_client = boto3.client('kinesis', region_name=config.region_name)
except Exception as e:
    logging.error(json.dumps({'incident': 'Can not connect to Kinesis', 'error': str(e)}))


def calculate_middle_price(orders):
    return (float(orders['bids'][0][0]) + float(orders['asks'][0][0]))/2


def send_to_klinesis(payload, exchange, symbol):
    payload['exchange'] = exchange
    payload['symbol'] = symbol
    payload['date_time'] = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")

    try:
        # Sending information to Kinesis
        kinesis_client.put_record(
            StreamName=config.kinesis_stream_name,
            Data=json.dumps(payload),
            PartitionKey='aa-bb'
        )
    except Exception as e:
        logging.error(json.dumps({'incident': 'Can not send to Kinesis', 'error': str(e)}))


def symmetrize_market_depth(orders):
    """
    Coins are traded at different prices in different markets. In order to have
    more precise results, this function calculates the relative ask/bid
    price (in %) wrt the coin price.

    Also, it is possible that for example bids are extended to 30% of the
    coin price while asks only 15%. We want to have a symmetrical market depth.
    Therefore, this function truncates the more extended side

    :param event: Market depth from a market.
    Format: {'bids':{price: amount, ...}, 'asks':{price: amount, ...}}
    """
    middle_price = calculate_middle_price(orders)

    payload = {'orders': {}}
    max_bid_percentage = 0
    max_ask_percentage = 0
    for order in itertools.chain(orders['bids'], orders['asks']):
        is_ask = (float(order[0]) > middle_price)

        # Bin market depth in increments of config.market_depth_increment
        relative_price_percent = int(100. / config.market_depth_increment * (float(order[0]) - middle_price)/middle_price)
        relative_price_percent = float(relative_price_percent)*config.market_depth_increment
        relative_price_percent += config.market_depth_increment * (2 * is_ask - 1)

        # Only keep asks/bids up to the percentage defined in the config file
        if abs(relative_price_percent) > config.market_depth_max_percentage:
            continue
        amount = float(order[0]) * float(order[1])
        # Count up amount in each relative price bin
        payload['orders'][relative_price_percent] = payload['orders'].get(relative_price_percent, 0.) + amount
        # Calculating how extended the market is in either direction
        if is_ask and max_ask_percentage < relative_price_percent:
            max_ask_percentage = relative_price_percent
        if not is_ask and abs(max_bid_percentage) < abs(relative_price_percent):
            max_bid_percentage = abs(relative_price_percent)

    min_max_percentage = min(max_bid_percentage, max_ask_percentage)
    symmetrical_payload = {'orders': {}}

    for relative_price_percent, amount in payload['orders'].items():
        is_ask = (relative_price_percent > 0)
        # Doing two things:
        # 1- Truncating the more extended side
        # 2- Accumulatively adding orders
        percent = relative_price_percent
        while abs(percent) <= min_max_percentage:
            # increment up if ask and increment down if bid
            symmetrical_payload['orders']['%.2f' % percent] = symmetrical_payload['orders'].get('%.2f' % percent, 0.) + amount
            percent += config.market_depth_increment * (2 * is_ask - 1)
    return symmetrical_payload


def fetch_orders(exchange, symbol):
    """
    This function gets the market depth of a single market from its API
    and sends the result to AWS Kenises in config.market_depth_increment granularity.

    :param exchange: Name of exchange
    :param symbol: Name of symbol
    """
    try:
        exchange_fn = getattr(ccxt, exchange)
        exchange_client = exchange_fn()
        exchange_client.load_markets()  # Loading the market
        # Binance gives an error if the number of requested
        # orders is more than 1000
        if exchange == 'binance':
            orders = exchange_client.fetch_l2_order_book(symbol, 1000)
        else:
            orders = exchange_client.fetch_l2_order_book(symbol, 2500)
    except Exception as e:
        # I have to check the errors I recieve. However, doing it for
        # 5000 markets is tedious and not my focus right now.
        logging.error(json.dumps({'incident': 'Error getting market depth',
                                  'excahnge': exchange,
                                  'symbol': symbol,
                                  'error': str(e)
                                  }))
    else:
        if 'bids' in orders and 'asks' in orders and orders['bids'] and orders['asks']:
            payload = symmetrize_market_depth(orders)
            send_to_klinesis(payload, exchange, symbol)


def lambda_handler(event, context):
    """
    This AWS lambda function receives a list of 10 markets and calls 10
    fetch_orders fucntions simultaneously using multithreading

    :param event: 10 market names. Format: {'exchange': 'symbol', ...}
    :param context: Runtime information from AWS Lambda service
    """

    jobs = []
    for exchange, symbol in event.items():
        thread = threading.Thread(target=fetch_orders, args=(exchange, symbol))
        jobs.append(thread)

    # Start the threads
    for j in jobs:
        j.start()

    # Ensure all of the threads have finished
    for j in jobs:
        j.join()


if __name__ == '__main__':
    # Debug statement for devs
    lambda_handler({'bitfinex': 'BTC/USD'}, '')
