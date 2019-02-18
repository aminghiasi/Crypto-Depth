import config
import boto3
import json
import logging

"""
Distributes the markets among other lambda functions to the market depth
"""


def lambda_handler(event='', context=''):
    """
    This master lambda function sends every 100 markets to a "steward" lambda
    function to be sent to workers (parallelization). Sending all markets at
    once to workers is time-consuming.

    :param event: Inputs of the function just in case. Empty!
    :param context: Runtime information from AWS Lambda service
    """

    # Connecting to AWS Lambda
    client = boto3.client('lambda')

    try:
        # File "BTC_markets.txt" contains all market info
        # in 'exchange coin' format
        market_names = open('BTC_markets.txt', 'r').read().split('\n')
    except Exception as e:
        logging.error(e)
        # If not possible to open the file containing market details,
        # the function stops
        return

    else:
        market_it = 0
        markets = {'exchanges': ''}
        for line in market_names:
            if ' ' not in line:
                continue
            markets['exchanges'] += ';' + line
            market_it += 1
            if market_it % 100 == 0:
                try:
                    # Automatic retry on failure
                    client.invoke(FunctionName=config.steward_arn,
                                  InvocationType='Event',
                                  Payload=json.dumps(markets)
                                  )
                    markets = {'exchanges': ''}
                except Exception as e:
                    logging.error(json.dumps({'incident': 'Failed to start a lambda steward', 'error': str(e)}))
                    # Continue with other markets
                    continue
        if markets['exchanges']:
            try:
                client.invoke(FunctionName=config.steward_arn,
                              InvocationType='Event',
                              Payload=json.dumps(markets)
                              )
            except Exception as e:
                logging.error(json.dumps({'incident': 'Failed to start a lambda steward', 'error': str(e)}))


if __name__ == '__main__':
    # Debug statement for devs
    lambda_handler('', '')
