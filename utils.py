import os
import json
import pymysql
import openai
import time, base64, hmac
from django.conf import settings
import pandas as pd
from sqlalchemy import create_engine, MetaData, text
from urllib.parse import quote_plus
import logging
from request import settings as rs

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import urllib.parse

class vue_response:

  def success(msg='', data={}):
    result = {}
    result['code'] = 20000
    result['message'] = msg
    result['data'] = data
    return json.dumps(result)

  def illegal_token():
    result = {}
    result['code'] = 50008
    result['message'] = 'illegal token'
    return json.dumps(result)

  def internal_error(msg=''):
    result = {}
    result['code'] = 50000
    result['message'] = msg
    return json.dumps(result)

class analyzer_db:

  def __init__(self):
    self.conn = pymysql.connect(
      # host=os.getenv('A_DB_HOST'),
      host = os.getenv('E_DB_HOST'),
      port = int(os.getenv('C_DB_PORT')),
      database = os.getenv('H_DB_NAME'),
      user = os.getenv('H_DB_USERNAME'),
      password = os.getenv('H_DB_PASSWORD'),
      charset = 'utf8mb4')
    
    self.cur = self.conn.cursor()
    self.dcur = self.conn.cursor(pymysql.cursors.DictCursor)
    
  def search_user(self, key):
    cmd = """
          SELECT
            a.Id, a.Username, a.FullName, a.Email, a.Roles, a.Level, b.Token, b.ExpireTime
          FROM
            auth_user a LEFT JOIN auth_token b ON a.Id = b.Id
          WHERE
            a.Username = %s
            OR
            a.Email = %s
            OR
            b.Token = %s
          ;
          """
    result = self.cur.execute(cmd, (key, key, key))
    if result > 0:
      sql_result = self.cur.fetchall()
      user_info = {
        'id': sql_result[0][0],
        'username': sql_result[0][1],
        'full_name': sql_result[0][2],
        'mail': sql_result[0][3],
        'roles': sql_result[0][4],
        'level': sql_result[0][5],
        'token': sql_result[0][6],
        'exp_time': sql_result[0][7]
      }
      return user_info
    else:
      return False

  def insert_user(self, username, mail, token, **other_info):
    cmd = """
          INSERT INTO
            auth_user (Username, FirstName, LastName, FullName, Email, Roles, Level,LastLogin)
          VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s)
          ;
          """
    if 'f_name' in other_info:
      _f_name = other_info['f_name']
    else:
      _f_name = ''
    if 'l_name' in other_info:
      _l_name = other_info['l_name']
    else:
      _l_name = ''
    if 'full_name' in other_info:
      _full_name = other_info['full_name']
    else:
      _full_name = ''
    if 'roles' in other_info:
      _roles = other_info['roles']
    else:
      _roles = ''
    if 'level' in other_info:
      _level = other_info['level']
    else:
      _level = ''
    if 'exp_time' in other_info:
      _exp_time = other_info['exp_time']
    else:
      _exp_time = ''
    if 'login_time' in other_info:
      _login_time = other_info['login_time']
    else:
      _login_time = ''
    try:
      values = (username, _f_name, _l_name, _full_name, mail, _roles, _level,_login_time)
      self.cur.execute(cmd, values)
      _id = self.conn.insert_id()
      cmd = """
            INSERT INTO
              auth_token (Id, Token, ExpireTime)
            VALUES
              (%s, %s, %s)
            ;
            """
      values = (_id, token, _exp_time)
      self.cur.execute(cmd, values)
      self.conn.commit()
      user_info = {
        'id': _id,
        'username': username,
        'full_name': _full_name,
        'mail': mail,
        'roles': _roles,
        'level': _level,
        'token': token,
        'exp_time': _exp_time
      }
      return user_info
    except Exception as e:
      self.conn.rollback()
      print('--> analyzer_db insert_user err:', e)
      return False

  def update_user(self, Id, full_name, f_name, l_name, mail, token, exp_time,login_time):
    try:
      cmd = """
            UPDATE
              auth_user
            SET
              FullName = %s, FirstName = %s, LastName= %s , Email = %s, LastLogin = %s
            WHERE
              Id = %s
            ;
            """
      values = (full_name, f_name, l_name, mail,login_time, Id)
      self.cur.execute(cmd, values)
      cmd = """
            UPDATE
              auth_token
            SET
              Token = %s, ExpireTime = %s
            WHERE
              Id = %s
            ;
            """
      values = (token, exp_time , Id)
      self.cur.execute(cmd, values)
      self.conn.commit()
      user_info = {
        'id': Id,
        'full_name': full_name,
        'mail': mail,
        'token': token,
        'exp_time': exp_time
      }
      return user_info
    except Exception as e:
      self.conn.rollback()
      print('--> analyzer_db update_user err:', e)
      return False

  def delete_user(self, Id):
    try:
      cmd = """
            DELETE FROM
              auth_user
            WHERE
              Id = %s
            ;
            """
      self.cur.execute(cmd, Id)
      cmd = """
            DELETE FROM
              auth_token
            WHERE
              Id = %s
            ;
            """
      self.cur.execute(cmd, Id)
      self.conn.commit()
      return True
    except Exception as e:
      self.conn.rollback()
      print('--> analyzer_db delete_user err:', e)
      return False

  
  def executemany(self, cmd,rowvalues):
    self.cur.executemany(cmd,rowvalues)

  def close(self):
    self.conn.close()
    
  def commit(self):
    self.conn.commit()

  def search_log(self, key1, key2, key3,key4,key5):
    cmd = """
          SELECT
            Author, Accweb, Operation, CreatedTime, AccStatus
          FROM
            histories_issues
          WHERE
            Author = %s
            AND 
            Accweb = %s
            AND
            Operation = %s
            AND
            CreatedTime = %s
            AND
            AccStatus = %s
          
          """
    result = self.cur.execute(cmd, (key1, key2, key3,key4,key5))
    if result > 0:
      # sql_result = self.cur.fetchall()      
      return True
    else:
      return False

  def insert_log(self, username, accweb, operation, accdate, status):
    cmd = """
          INSERT INTO
            histories_issues (Author, Accweb, Operation, CreatedTime, AccStatus)
          VALUES
            (%s, %s, %s, %s, %s)
          
          """    
    try:
      values = (username, accweb, operation, accdate, status)
      self.cur.execute(cmd, values)      
      self.conn.commit()      
      return True
    except Exception as e:
      self.conn.rollback()
      print('--> analyzer_db insert_log err:', e)
      return False

  def get_grades(self, role):
      sql = f'select * from auth_grade where `Grade` = "{role}"'
      self.dcur.execute(sql)
      return self.dcur.fetchall()[0]
      pass


def create_token(key, expire=7200):
    
  ts = time.time() + expire
  ts_str = str(ts)
  ts_byte = ts_str.encode('utf-8')
  sha1_tshexstr = hmac.new(key.encode('utf-8'),ts_byte,'sha1').hexdigest()
  token = ts_str+':'+sha1_tshexstr
  b64_token = base64.urlsafe_b64encode(token.encode('utf-8'))
  exp_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))
  return b64_token.decode('utf-8'), exp_time

def verify_token(key, token):
  token_str = base64.urlsafe_b64decode(token).decode('utf-8')
  token_list = token_str.split(':')
  if len(token_list) != 2:
    return False
  ts_str = token_list[0]
  if float(ts_str) < time.time():
    # token expired
    return False
  known_sha1_tsstr = token_list[1]
  sha1 = hmac.new(key.encode('utf-8'),ts_str.encode('utf-8'),'sha1')
  calc_sha1_tsstr = sha1.hexdigest()
  if calc_sha1_tsstr != known_sha1_tsstr:
    # token certification failed
    return False
  # token certification success
  return True


class DatabaseConnector:
    metadata = None
    engine = None
    connection = None
    count = 0
    _db = None
    _cs = None
    def __init__(self, db):
        self._db = db
        if db == 'requestdb':
            self._cs = 'mysql+pymysql://{}:{}@{}:{}/'.format(
                os.getenv('H_DB_USERNAME'),
                quote_plus(os.getenv('H_DB_PASSWORD')),
                os.getenv('E_DB_HOST'),
                os.getenv('C_DB_PORT')
            )
        elif db == 'customerdb':
            self._cs = 'mysql+pymysql://{}:{}@{}:{}/'.format(
                rs.BC_DB['username'],
                quote_plus(rs.BC_DB['password']),
                rs.BC_DB['host'],
                rs.BC_DB['port']
            )

        print(self._cs)
        self.metadata = MetaData()
        self.engine = create_engine('{}{}'.format(self._cs, self._db))
        self.connection = self.engine.connect()
    def read_table(self, name):
        return pd.read_sql(name, self.engine)
        pass
    def read_query(self, query):
        return pd.read_sql_query(query, self.engine)
        pass
    def execute(self, cmd):
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    text(cmd)
                )
                conn.commit()
        except Exception as e:
            logging.getLogger(__name__).debug('!!! ERROR: {}'.format(e))
        pass
    


class Jira:
    session = None
    u_auth = 'rest/auth/1/session'
    server = None
    def __init__(self, sever=None):
        self.server = sever or 'https://jiradc2.ext.net.nokia.com/'
        self._headers = {
            "Content-Type": "application/json",
            'Authorization': 'Bearer MDExNDAwMTUxMjg1OkwRsKNWe/tAXMvZG9zdQ9UX9jqf'
        }
        requests.packages.urllib3.disable_warnings(
            InsecureRequestWarning
            )
        self.session = requests.Session()
        pass

    def get(self, url, params = None):
        u = '{}{}'.format(self.server, url)
        if params:
            u += '?%s' % urllib.parse.urlencode(params) 
        logging.debug('url = %s' % u)
        resp = self.session.get(
            url=u,
            headers=self._headers,
            verify=False
        )
        logging.debug('resp = %s' % resp.text)
        return  resp

    def post(self, url, data):
        resp = self.session.post(
            '{}{}'.format(self.server, url), 
            data=json.dumps(data), 
            headers=self._headers,
            verify = False
        )
        return resp.ok
        pass
        
    def post_with_resp(self, url, data):
        resp = self.session.post(
            '{}{}'.format(self.server, url), 
            data=json.dumps(data), 
            headers=self._headers,
            verify = False
        )
        return resp
        pass
        
    def put(self, url, data):
        resp = self.session.put(
            '{}{}'.format(self.server, url), 
            data=data, 
            headers=self._headers,
            verify=False
        )
        return resp.ok
        pass
    def put_with_resp(self, url, data):
        resp = self.session.put(
            '{}{}'.format(self.server, url), 
            data=json.dumps(data), 
            headers=self._headers,
            verify=False
        )
        return resp
        pass

    def delete(self, url):
        resp = self.session.delete(
            '{}{}'.format(self.server, url),
            headers=self._headers
        )
        return resp
        pass



