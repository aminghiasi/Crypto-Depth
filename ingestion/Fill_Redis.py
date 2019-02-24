import ast
import boto3
import config
from datetime import datetime
import json
from boto3.dynamodb.conditions import Key
import logging
import redis

time_now = datetime.utcnow()
"""
Writes overal market depth to Redis and DynamoDB for faster Query
"""


def write_in_DynamoDB(redis_db):
    """"
    Writes overal and symbol (e.g. BTC) asks/bids in DynamoDB
    """
    try:

        # Connecting to DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name=config.region_name)
        table = dynamodb.Table(config.dynamodb_table_name)

    except Exception as e:
        logging.error(json.dumps({'incident': 'Failed to connect to DynamoDB', 'error': str(e)}))
        exit(1)

    # When putting data in Redis, last_update contains the time.
    # It is used to add the time tag when calculating overall market depth
    if not redis_db.get('last_update') or (time_now - datetime.strptime(redis_db.get('last_update').decode("utf-8"), "%Y-%m-%d %H:%M")).seconds > 90:
        # If the data on Redis is not recently updated, quit
        exit()

    overal_market_depth = {'overall': {}}

    for key in redis_db.keys():
        key_str = key.decode("utf-8")
        if key_str.count('_') < 2:
            # Several data is kept in the same database. If the pattern is
            # wrong, then this key, value does not belog to the data we are
            # interested in. Continue with the next key, value
            continue

        price_diff_percent, exchange, symbol = key_str.split('_')
        amount = float(redis_db.get(key))
        coin = symbol.split('/')[0]
        if coin not in overal_market_depth:
            overal_market_depth[coin] = {}
        # Add asks/bids
        overal_market_depth[coin][price_diff_percent] = '%.2f' % (float(overal_market_depth[coin].get(price_diff_percent, 0.)) + amount)
        overal_market_depth['overall'][price_diff_percent] = '%.2f' % (float(overal_market_depth['overall'].get(price_diff_percent, 0.)) + amount)

    # Write in DynamoDB
    for key, value in overal_market_depth.items():
        table.put_item(
            Item={
                'exchange_base_quote': key,
                'exchange': 'overall',
                'base': 'overall',
                'quote': 'overall',
                'time': time_now.strftime("%Y-%m-%d %H:%M"),
                'Market_Depth': value
            }
        )


def write_in_Redis(overal_market_depth, redis_db):
    """
    Creates a dictionary that contains the buy/sell pressure of the last 48
    hours to let the dafault plot in the website load fast.
    """
    historical_overal_market_depth = {}
    for coin in overal_market_depth:
        coin_history_ = redis_db.get(coin+'_History')
        if coin_history_:
            coin_history = ast.literal_eval(coin_history_.decode("utf-8"))
        else:
            coin_history = {}
        updated_coin_history = {time_now.strftime("%Y-%m-%d %H:%M"): overal_market_depth[coin]}
        for time in coin_history:
            # Remove if older than 48 hours
            if (time_now - datetime.strptime(time, "%Y-%m-%d %H:%M")).total_seconds() < 48 * 60 * 60:
                updated_coin_history[time] = coin_history[time]

        historical_overal_market_depth[coin+'_History'] = updated_coin_history

    for key, value in historical_overal_market_depth.items():
        redis_db.set(key, json.dumps(value))


if __name__ == '__main__':
    """
    Runs every minute by cron to add the asks/bids to "overall" and
    symbol (e.g. BTC) keys in DynamoDB and Redis for faster queries if the user
    has no coin or exchange in mind and wants the overall market depth.
    """
    try:
        # Connecting to Redis
        redis_db = redis.StrictRedis(host=config.redis_endpoint, port=6379, db=0)

    except Exception as e:
        logging.error(json.dumps({'incident': 'Failed to connect to Redis', 'error': str(e)}))
        exit(1)

    overal_market_depth = write_in_DynamoDB(redis_db)
    write_in_Redis(overal_market_depth, redis_db)
