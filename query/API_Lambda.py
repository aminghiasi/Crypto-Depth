import boto3
import config
from datetime import datetime, timedelta
import json
from boto3.dynamodb.conditions import Key, Attr
import logging

"""
API for getting historical data
"""

# Connceting to DynamoDB
try:
    dynamodb = boto3.resource('dynamodb', region_name=config.region_name)
    table = dynamodb.Table('crypto_market_depth')
except Exception as e:
    logging.error(json.dumps({'incident': 'Failed to connect to DynamoDB', 'error': str(e)}))
    exit()


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
    returns MDR, Buy Pressure, and Sell Pressure over the duration specified by the users.
    """

    output = {}

    items = table.query(
        KeyConditionExpression=Key('exchange_base_quote').eq(primary_key) &
        Key('time').between(input['start_time'], input['end_time'])
        )
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
    returns market depth integrated over the duration specified by the user
    """

    output = {'orders': {}}
    items = table.query(
        KeyConditionExpression=Key('exchange_base_quote').eq(primary_key) &
        Key('time').between(input['start_time'], input['end_time'])
        )

    buy_pressure = 0.
    sell_pressure = 0.

    # Adding the orders from different markets
    for item in items['Items']:
        percent = -1 * float(input['percent'])
        while percent <= float(input['percent']):
            if ('%.2f' % percent) in item['Market_Depth']:
                output['orders']['%.2f' % percent] = output['orders'].get('%.2f' % percent, 0) + float(item['Market_Depth']['%.2f' % percent])
            percent += config.market_depth_increment
        if input['percent'] in item['Market_Depth']:
            sell_pressure += float(item['Market_Depth'][input['percent']])
        if ('-' + input['percent']) in item['Market_Depth']:
            buy_pressure += float(item['Market_Depth']['-' + input['percent']])

    # Writing Buy Pressure, Sell Pressure and MDR to the output
    if buy_pressure and sell_pressure:
        output['Buy Pressure'] = '%.0f' % buy_pressure
        output['Sell Pressure'] = '%.0f' % sell_pressure
        output['MDR'] = '%.2f' % (100 * (buy_pressure - sell_pressure) / (buy_pressure + sell_pressure))
    if not output:
        return('500: Service unavailable')
    return(output)


def validate_input(input):
    if 'output' not in input:
        return True, ('400: Bad Request. Can not recognize the plot type you want to get.', input)
    if 'start_time' in input and 'end_time' in input and input['start_time'] > input['end_time']:
        return True, ('400: Bad Request. Start time cannot be greater than end time', input)

    # Defaults to 5%
    if 'percent' not in input:
        input['percent'] = '20.0'

    if float(input['percent']) < 0.:
        return True, ('400: Bad Request. Percentage to consider in market depth can not be negative', input)

    # Defaults to realtime
    if 'realtime' not in input:
        input['realtime'] = 'true'
    try:
        input['percent'] = '%.2f' % float(input['percent'])
    else:
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
    if 'market' in input:
        primary_key += input['exchange']
        if 'exchange' in input:
            primary_key += ';' + input['market']

    # Get data from dynamo based on plot type
    if input['output'] == 'marketdepth':
        if input['realtime'] == 'true':
            input['end_time'] = (datetime.utcnow() - timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M")
            input['start_time'] = (datetime.utcnow() - timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M")
        return(market_depth(input, primary_key))
    elif input['output'] == 'mdr':
        if input['realtime'] == 'true':
            input['end_time'] = (datetime.utcnow() - timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M")
            input['start_time'] = (datetime.utcnow() - timedelta(minutes=120)).strftime("%Y-%m-%d %H:%M")
        return(mdr(input, primary_key))
    else:
        return(input)


if __name__ == '__main__':
    # Debug statement for devs
    print(lambda_handler({'params': {'querystring': {'realtime': 'true',
                                                     'output': 'marketdepth',
                                                     'percent': '20',
                                                     'start_time': '2019-02-12 23:23',
                                                     'end_time': '2019-02-12 23:29'
                                                     }}}, ""))
