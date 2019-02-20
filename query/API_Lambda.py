import ast
import boto3
import config
from datetime import datetime, timedelta
import json
from boto3.dynamodb.conditions import Key, Attr
import logging
import redis

"""
API for getting historical data
"""


try:
    # Connecting to Redis
    redis_db = redis.StrictRedis(host=config.redis_endpoint, port=6379, db=0)

    # Connecting to DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name=config.region_name)
    table = dynamodb.Table('crypto_market_depth')

except Exception as e:
    logging.error(json.dumps({'incident': 'Failed to connect to an AWS tool', 'error': str(e)}))
    exit(1)


def find_buy_and_sell_pressures(item, percent_given_by_user):
    """
    Finds the buy and sell pressure in a DynamoDB item.
    Returns zero if no asks/bids in the specified percentage of price
    """

    if ('%.2f' % percent_given_by_user) in item['Market_Depth']:
        sell_pressure = float(item['Market_Depth']['%.2f' % percent_given_by_user])
    else:
        sell_pressure = 0.0

    if ('%.2f' % -percent_given_by_user) in item['Market_Depth']:
        buy_pressure = float(item['Market_Depth']['%.2f' % -percent_given_by_user])
    else:
        buy_pressure = 0.0

    return buy_pressure, sell_pressure


def mdr(input, primary_key):
    """
    Returns MDR, Buy Pressure, and Sell Pressure over the duration specified by the users.
    """

    output = {}

    try:
        items = table.query(
            KeyConditionExpression=Key('exchange_base_quote').eq(primary_key) &
            Key('time').between(input['start_time'], input['end_time'])
            )
    except Exception as e:
        return ('Cannot find any data related to your request', e)

    for item in items['Items']:
        buy_pressure, sell_pressure = find_buy_and_sell_pressures(item, float(input['percent']))
        output[item['time']] = {'Buy Pressure': str(buy_pressure),
                                'Sell Pressure': str(sell_pressure),
                                'MDR': '%.2f' % (100 * (buy_pressure - sell_pressure) / (buy_pressure + sell_pressure))
                                }

    if not output:
        return('500: Service unavailable')
    return(output)


def market_depth(input, primary_key):
    """
    Returns coin depth integrated over the duration specified by the user
    """

    output = {'orders': {}}
    try:
        items = table.query(
            KeyConditionExpression=Key('exchange_base_quote').eq(primary_key) &
            Key('time').between(input['start_time'], input['end_time'])
            )
    except Exception as e:
        return ('Cannot find any data related to your request', e)
    buy_pressure = 0.
    sell_pressure = 0.
    print(items['Items'])
    # Adding the orders from different coins
    for item in items['Items']:
        percent = -1 * float(input['percent'])
        while percent <= float(input['percent']):
            if ('%.2f' % percent) in item['Market_Depth']:
                output['orders']['%.2f' % percent] = output['orders'].get('%.2f' % percent, 0) + float(item['Market_Depth']['%.2f' % percent]) / len(items['Items'])
            percent += config.market_depth_increment
        if input['percent'] in item['Market_Depth']:
            sell_pressure += float(item['Market_Depth'][input['percent']])
        if ('-' + input['percent']) in item['Market_Depth']:
            buy_pressure += float(item['Market_Depth']['-' + input['percent']])
    # Writing Buy Pressure, Sell Pressure and MDR to the output
    if buy_pressure and sell_pressure:
        output['Buy Pressure'] = '%.0f' % (buy_pressure / len(items['Items']))
        output['Sell Pressure'] = '%.0f' % (sell_pressure / len(items['Items']))
        output['MDR'] = '%.2f' % (100 * (buy_pressure - sell_pressure) / (buy_pressure + sell_pressure))
    if not output:
        return('500: Service unavailable')
    return(output)


def realtime(input, primary_key):
    """
    Handles real time queries. Reading data from Redis and sending
    the result to the user
    """
    primary_key += '_History'
    now = datetime.utcnow()
    data = ast.literal_eval(redis_db.get(primary_key).decode("utf-8"))
    if 'start_time' not in input:
        input['start_time'] = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M")
    output = {}
    time = datetime.strptime(input['start_time'], "%Y-%m-%d %H:%M")
    while time < now:
        time_str = time.strftime("%Y-%m-%d %H:%M")
        if time_str > input['start_time'] and time_str in data:
            output[time_str] = {'Buy Pressure': data[time_str]['-'+input['percent']],
                                'Sell Pressure': data[time_str][input['percent']]}
        time += timedelta(minutes=1)
    return output


def validate_input(input):
    if 'type' not in input:
        return True, ('400: Bad Request. Can not recognize the plot type you want to get.', input)
    if 'start_time' in input and 'end_time' in input and input['start_time'] > input['end_time']:
        return True, ('400: Bad Request. Start time cannot be greater than end time', input)

    # Defaults to 5%
    if 'percent' not in input:
        input['percent'] = '20.0'

    if float(input['percent']) < 0.:
        return True, ('400: Bad Request. Percentage to consider in coin depth can not be negative', input)

    # Defaults to realtime
    if 'realtime' not in input:
        input['realtime'] = 'true'
    try:
        input['percent'] = '%.2f' % float(input['percent'])
    except Exception:
        return True, ('400: Bad Request. Percentage should be a number', input)
    return False, input


def lambda_handler(event, context):
    """
    Calls the right fucntion according to query parameters
    """
    input = event["params"]["querystring"]
    bad_request, input = validate_input(input)
    if bad_request:
        return input
    # Generate dynamo query primary key
    # Defaults to 'overall' (no specific coin or exchange)
    primary_key = 'overall'
    if 'coin' in input:
        primary_key = input['coin']
        if 'exchange' in input:
            primary_key = input['exchange'] + ';' + input['coin']

    if input['realtime'] == 'true' and 'exchange' not in input and input['type'] == 'mdr':
        if 'start_time' in input and (datetime.utcnow() - datetime.strptime(input['start_time'], "%Y-%m-%d %H:%M")).total_seconds() > 48 * 60 * 60:
            return('400: Bad Request. Real-time mode cannot go back more than two days.')
        return(realtime(input, primary_key))
    # Get data from dynamo based on plot type
    if input['type'] == 'marketdepth':
        if input['realtime'] == 'true':
            input['end_time'] = (datetime.utcnow() - timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M")
            input['start_time'] = (datetime.utcnow() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M")
        return(market_depth(input, primary_key))
    elif input['type'] == 'mdr':
        if input['realtime'] == 'true':
            input['end_time'] = (datetime.utcnow() - timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M")
            input['start_time'] = (datetime.utcnow() - timedelta(minutes=1440)).strftime("%Y-%m-%d %H:%M")
        return(mdr(input, primary_key))
    else:
        return(input)


if __name__ == '__main__':
    # Debug statement for devs
    print(lambda_handler({'params': {'querystring': {'realtime': 'true',
                                                     'type': 'marketdepth',
                                                     'percent': '20',
                                                     'start_time': '2019-02-12 23:23',
                                                     'end_time': '2019-02-12 23:29'
                                                     }}}, ""))
