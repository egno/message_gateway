import psycopg2
from psycopg2.extras import DictCursor
import json
import os
from config import CONFIG as config

DB_CONFIG = config['DB_LOG']


def db_query(sql, params):
  with psycopg2.connect(host=DB_CONFIG['PGHOST'], dbname=DB_CONFIG['PGDATABASE'], user=DB_CONFIG['PGUSER'], password=DB_CONFIG['PGPASSWORD']) as conn:
    with conn.cursor(cursor_factory=DictCursor) as cursor:
      cursor.execute(sql, params)
      row = cursor.fetchone()
      return row


def db_account(id):
  return db_query('''select public.notification_settings((%s)::uuid)''', (id,))


def db_log(id, details, amount = 0):
  return db_query('''
insert into billing.transactions (account, amount, details) 
values (%s, %s, (%s)::jsonb) returning id
''', (id, amount, json.dumps(details)))


def db_log_update(transaction_id, details):
  return db_query('''
update billing.transactions
set details = details || (%s)::jsonb 
where id = %s
returning id
''', (json.dumps(details), transaction_id))

