import json
import os
import requests
import datetime

iex_url = os.environ['API_URL']
api_key = os.environ['API_KEY']

def lambda_handler(event, context):
  if not event.get('queryStringParameters'):
    return {
      'statusCode': 400,
      'headers': {'Content-Type': 'application/json'},
      'body': json.dumps({'error': 'No parameters specfied'})
    }

  ticker = event['queryStringParameters'].get('ticker')
  if not ticker:
    return {
      'statusCode': 400,
      'headers': {'Content-Type': 'application/json'},
      'body': json.dumps({'error': 'Ticker must be specified'})
    }

  try:
    from_date, to_date = get_date_range(event)
  except Exception as e:
    return {
      'statusCode': 400,
      'headers': {'Content-Type': 'application/json'},
      'body': json.dumps({'error': f'Invalid dates: {str(e)}'})
    }
  
  return {
    'statusCode': 200,
    'headers': {'Content-Type': 'application/json'},
    'body': json.dumps(get_ticker_data(ticker, from_date, to_date))
  }

def get_date_range(event):
  to_date_raw = event['queryStringParameters'].get('to_date')
  from_date_raw = event['queryStringParameters'].get('from_date')

  if (not from_date_raw) != (not to_date_raw):
    raise Exception("Both or neither from_date and to_date must be specified")
  
  if not to_date_raw:
    to_date = datetime.date.today()
    from_date = to_date.replace(month=1).replace(day=1)
  else:
    try:
      to_date = datetime.date.fromisoformat(to_date_raw)
      from_date = datetime.date.fromisoformat(from_date_raw)
    except:
      raise Exception("Dates should be in the format 'YYYY-MM-DD'")
  
  if to_date < from_date:
    raise Exception('To date cannot be before the from date')
  
  if from_date.year < 2007:
    raise Exception('Data only available from 2007 onward')

  
  if to_date - from_date > datetime.timedelta(days=365):
    raise Exception('date range cannot exceed 365 days')
  
  return from_date, to_date

def get_ticker_data(ticker, from_date, to_date):
  url = f'{iex_url}/v1/data/core/historical_prices/{ticker}?token={api_key}&from={from_date.isoformat()}&to={to_date.isoformat()}'
  response = requests.get(url)
  data = [{'date': d['priceDate'], 'return': get_return(d['open'], d['close'])} for d in response.json()]
  return data

def get_return(start_price, end_price):
  r = 100 * ((end_price - start_price) / start_price)
  return str(f'{round(r, 2)}%')