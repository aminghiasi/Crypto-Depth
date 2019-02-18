import boto3
import config
import json
import logging

"""
Gets market list from master lambda function and distributes them to lambda workers
"""


def lambda_handler(event, context):
    """
    This AWS steward lambda function receives a list of 100 markets from the
    master lambda function to distribute each 10 to a lambda workers

    :param event: 100 market names. Format: {'exchanges': 100 market names}
    :param context: Runtime information from AWS Lambda service
    """

    # Connecting to AWS Lambda
    client = boto3.client('lambda')

    market_it = 0
    payload = {}
    for exchange_symbol in event['exchanges'].split(';'):
        if ' ' in exchange_symbol:
            payload[exchange_symbol.split(' ')[0]] = exchange_symbol.split(' ')[1]
            market_it += 1
            if market_it % 10 == 0:
                try:
                    # Automatic retry on failure
                    client.invoke(FunctionName=config.worker_arn,
                                  InvocationType='Event',
                                  Payload=json.dumps(payload)
                                  )
                    payload = {}
                except Exception as e:
                    logging.error(json.dumps({'incident': 'Failed to start a Lambda worker', 'error': str(e)}))
                    # Continue with other markets
                    continue

    if payload:
        try:
            # Automatic retry on failure
            client.invoke(FunctionName=config.worker_arn,
                          InvocationType='Event',
                          Payload=json.dumps(payload)
                          )
        except Exception as e:
            # Continue with other markets
            logging.error(json.dumps({'incident': 'Failed to start a Lambda worker', 'error': str(e)}))


if __name__ == '__main__':
    # Debug statement for devs
    lambda_handler({'exchanges': 'bitfinex BTC/USD'}, '')
