import ast
import boto3
import config
from datetime import datetime
import json
from boto3.dynamodb.conditions import Key
import logging
from multiprocessing import Process
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
    table = dynamodb.Table(config.dynamodb_table_name)

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


def write_to_DynamoDB(data):

    exchange_rate = find_exchange_rate(data['symbol'].split('/')[1])
    if not exchange_rate:
        logging.error(json.dumps({'incident': 'Failed to find the rate of ' + data['symbol'].split('/')[1] + '/USD'}))
        # Process next record
        return

    # Applying currency conversion rates and saving in Redis
    for price_diff_percent, amount in data['orders'].items():
        amount_in_USD = float(amount)/exchange_rate
        data['orders'][price_diff_percent] = '%.2f' % amount_in_USD
        redis_db.set(price_diff_percent + '_' + data['exchange'] + '_' + data['symbol'], amount_in_USD)
    # Redis is used for real-time queries. Therefore, it is important
    # to know the time of last update
    redis_db.set('last_update', datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
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


if __name__ == '__main__':
    """
    Kinesis consumer. Writes the stream into dynamodb and redis
    """

    # Do until no stream
    while 'NextShardIterator' in record_response:
        # Get a batch of records
        record_response = kinesis_client.get_records(ShardIterator=record_response['NextShardIterator'],
                                                     Limit=10000)
        jobs = []
        count = 0
        for rec in record_response['Records']:
            data = ast.literal_eval(rec['Data'].decode("utf-8"))
            job = Process(target=write_to_DynamoDB, args=(data,))
            job.start()
            jobs.append(job)
            count += 1
            if count > 19:
                for j in jobs:
                    j.join()
                count = 0
                jobs =[]

        for j in jobs:
            j.join()
        print(count)
        if 'Data' not in record_response['Records']:
            time.sleep(0.21)
