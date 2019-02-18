import ast
import boto3
import config
import json
from boto3.dynamodb.conditions import Key
import logging
import redis
import time

"""
Loads kinesis stream into dynamodb and redis
"""
try:
    # Connecting to Redis
    redis_db = redis.StrictRedis(host=config.redis_endpoint, port=6379, db=0)

    # Connecting to DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name=config.region_name)
    table = dynamodb.Table('crypto_market_depth')

    # Connecting to Kinesis
    kinesis_client = boto3.client('kinesis', region_name=config.region_name)
    response = kinesis_client.describe_stream(StreamName=config.kinesis_stream_name)
    my_shard_id = response['StreamDescription']['Shards'][0]['ShardId']
    shard_iterator = kinesis_client.get_shard_iterator(StreamName=config.kinesis_stream_name,
                                                       ShardId=my_shard_id,
                                                       ShardIteratorType='LATEST'
                                                       )

    my_shard_iterator = shard_iterator['ShardIterator']
    record_response = kinesis_client.get_records(ShardIterator=my_shard_iterator,
                                                 Limit=10000)
except Exception as e:
    logging.error(json.dumps({'incident': 'Failed to connect to an AWS tool', 'error': str(e)}))
    exit(1)


def find_exchange_rate(currency):
    """
    Gets the conversion rate of other currencies (EUR, CHR,
    etc) vs USD from the database (Redis)
    """
    if currency == 'USD':
        return 1.0
    rate = redis_db.get('rate_' + currency + '/USD')
    if rate is not None:
        return float(rate)
    else:
        return None


def maintain_overal_market_depth(data):
    """
    This function adds the asks/bids to "overall" and symbol (e.g. BTC) keys
    in DynamoDB for faster queries if the user has no coin or exchange in
    mind and wants the overall market depth.
    """

    for primary_key in ['overall', data['symbol'].split('/')[0]]:
        # Query the row corresponding to 'overall' or synmbol
        items = table.query(
            KeyConditionExpression=Key('exchange_base_quote').eq(primary_key) &
            Key('time').eq(data['date_time'])
        )
        # if 'overall' or symbol key does not exist in DynamoDB,
        # create an empty dictionary
        if not items['Items']:
            items = {'Items': [{'Market_Depth': {}}]}
        item = items['Items'][0]

        # Adding this market orders to overall market depth
        for price_diff_percent, amount_in_USD in data['orders'].items():
            if price_diff_percent in item['Market_Depth']:
                item['Market_Depth'][price_diff_percent] = "%.2f" % (float(item['Market_Depth'][price_diff_percent]) + float(data['orders'][price_diff_percent]))
            else:
                item['Market_Depth'][price_diff_percent] = data['orders'][price_diff_percent]

        # Putting the new overall market depth in DynamoDB
        table.delete_item(  # Deletes only if it exists
            Key={
                'exchange_base_quote': primary_key,
                'time': data['date_time']
            }
        )
        table.put_item(
            Item={
                'exchange_base_quote': primary_key,
                'exchange': 'overall',
                'base': 'overall',
                'quote': 'overall',
                'time': data['date_time'],
                'Market_Depth': item['Market_Depth']
            }
        )


if __name__ == '__main__':
    """
    Kinesis consumer. Writes the stream into dynamodb and redis
    """

    # Do until no stream
    while 'NextShardIterator' in record_response:
        # Get a batch of records
        record_response = kinesis_client.get_records(ShardIterator=record_response['NextShardIterator'],
                                                     Limit=10000)
        for rec in record_response['Records']:
            data = ast.literal_eval(rec['Data'].decode("utf-8"))

            exchange_rate = find_exchange_rate(data['symbol'].split('/')[1])
            if not exchange_rate:
                logging.error(json.dumps({'incident': 'Failed to find the rate of ' + data['symbol'].split('/')[1] + '/USD'}))
                # Process next record
                continue
            new_data = {'orders': {}}

            # Applying currency conversion rates and saving in Redis
            for price_diff_percent, amount in data['orders'].items():
                amount_in_USD = float(amount)/exchange_rate
                price_diff = "%.2f" % float(price_diff_percent)
                data['orders'][price_diff_percent] = '%.2f' % amount_in_USD
                redis_db.set(price_diff + '_' + data['exchange'] + '_' + data['symbol'], amount_in_USD)

            # Putting data in DynamoDB
            table.put_item(
                Item={
                    'exchange_base_quote': data['exchange'] + ';' + data['symbol'],
                    'exchange': data['exchange'],
                    'base': data['symbol'].split('/')[0],
                    'quote': data['symbol'].split('/')[1],
                    'time': data['date_time'],
                    'Market_Depth': data['orders']
                    }
            )
            maintain_overal_market_depth(data)

        if 'Data' not in record_response['Records']:
            time.sleep(0.21)
