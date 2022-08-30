DEBUG = True
import pymysql
from sqlalchemy import create_engine, text
from flask import Flask


db = {
  'user' : 'root',
  'password' : 'rkdgustjs132!',
  'host' : 'backend-test.ccsksqt9q6aw.ap-northeast-2.rds.amazonaws.com',
  'port' : 3306,
  'database' : 'backend_test'  
}

DB_URL = f"mysql+pymysql://{db['user']}:{db['password']}@{db['host']}/{db['database']}"
JWT_SECRET_KEY = 'SOME_SUPER_SECRET_KEY'
JWT_EXP_DELTA_SECONDS =7*24*60*60

test_db = {
  'user' : 'root',
  'password' : 'rkdgustjs132!',
  'host' : 'backend-test.ccsksqt9q6aw.ap-northeast-2.rds.amazonaws.com',
  'port' : 3306,
  'database' : 'test_db'  
}


test_config = {
  'DB_URL' : f"mysql+pymysql://{test_db['user']}:{test_db['password']}@{test_db['host']}/{test_db['database']}?charset=utf8",
  'JWT_SECRET_KEY' : 'SOME_SUPER_SECRET_KEY',
  'JWT_EXP_DELTA_SECONDS' : 7*24*60*60 
}

  