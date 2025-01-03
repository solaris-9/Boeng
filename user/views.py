from django.shortcuts import render

# Create your views here.
import datetime
import simplejson
import json
import ldap
import logging
import numpy as np

from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from utils import analyzer_db, create_token
from utils import DatabaseConnector as dc

File_address = r'C:/reqLog/printlog.txt'
fa = open(File_address,'a')
# LDAP_HOST = 'ldap://10.152.138.3:389' 
LDAP_HOST = 'ldap://10.158.52.11:389' 
LDAP_BASE_DN = 'OU=Users,OU=UserAccounts,DC=nsn-intra,DC=net'

def ldap_auth(username, password):
  try:
       
    conn = ldap.initialize(LDAP_HOST)        
    conn.simple_bind_s('nsn-intra\\' + username, password)
    #conn.simple_bind_s(username, password)
    result = conn.search_s(LDAP_BASE_DN, ldap.SCOPE_SUBTREE, 'sAMAccountName=' + username)
    #print('--> result:', conn.__dict__, file=fa, flush=True) 
    #print('--> result:', result, file=fa, flush=True)
    result = result[0][1]
    #print('--> result:', result, file=fa, flush=True)
    user_info = {
      'full_name': result['cn'][0].decode('utf-8'),
      'f_name': result['givenName'][0].decode('utf-8'),
      'l_name': result['sn'][0].decode('utf-8'),
      'mail': result['mail'][0].decode('utf-8')}
    return user_info
   
  except Exception as e:
    print('--> ldap_auth Err:', e, file=fa, flush=True)
    return False


@csrf_exempt
def login(request): 
  sLastupdate = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')  
  if 'HTTP_X_FORWARDED_FOR' in request.META:
    print('--> rocklog login ip:', sLastupdate,request.META.get('HTTP_X_FORWARDED_FOR'),file=fa,flush=True )
  else:
    print('--> rocklog login ip:', sLastupdate,request.META.get('REMOTE_ADDR'),file=fa,flush=True )
  print('request.body:', request.body.decode('utf-8'),file=fa,flush=True )
  info = json.loads(request.body.decode('utf-8'))
  username = info['username']
  password = info['password'] 
  ldap_user = ldap_auth(username, password)  
  token, exp_time = create_token(username)
  
  print(sLastupdate,ldap_user, file=fa,flush=True )
  if ldap_user:
    print('user1-1=', sLastupdate, username, file=fa, flush=True)
    sql = analyzer_db()
    print('user1=',sLastupdate,username, file=fa,flush=True )
    old_user = sql.search_user(key=username)
    print('user2=',sLastupdate,username, file=fa,flush=True )
    if old_user:
      print('user3=', sLastupdate, username, file=fa, flush=True)
      user = sql.update_user(
        old_user['id'], ldap_user['full_name'], ldap_user['f_name'],
        ldap_user['l_name'], ldap_user['mail'], token, exp_time,sLastupdate)
      roles = old_user['roles']
      level = old_user['level']  
      # print(roles,level,ldap_user['mail'],file=fa,flush=True )
    else:
      user = sql.insert_user(
        username, ldap_user['mail'], token,
        f_name = ldap_user['f_name'],
        l_name = ldap_user['l_name'],
        full_name = ldap_user['full_name'],
        roles = 'Viewer',
        level = '1',
        exp_time = exp_time,
        login_time = sLastupdate)
      roles = 'Viewer'
      level = '1'
        
    log1 = sql.search_log(key1=username,key2='',key3='Login',key4=sLastupdate,key5='login success') 
    if not log1:
        log2=sql.insert_log(
            username = username,
            accweb='',
            operation='login',
            accdate=sLastupdate,
            status ='login success'
            )
    grade = sql.get_grades(roles)
    print('grade = ', grade, file=fa, flush=True)
    sql.close()
    data = {
      'name': username,
      'mail': ldap_user['mail'],      
      'token': user['token'],      
      'roles': roles,
      'level': level,
      'Add': grade['Add'],
      'Edit': grade['Edit'],
      'Delete': grade['Delete'],
      'Search': grade['Search'],
      'View': grade['View'],
      'Export': grade['Export'],
      'Download': grade['Download'],
    }
    resp = {
      'code': 20000,
      'mes': 'login success',
      'data': data
    }    
    return HttpResponse(json.dumps(resp), content_type='application/json')
  else:
      sql = analyzer_db()
      print('user4=', sLastupdate, username, file=fa, flush=True)
      log1 = sql.search_log(key1=username,key2='',key3='Login',key4=sLastupdate,key5='login failure') 
      if not log1:
          log2=sql.insert_log(
              username = username,
              accweb='',
              operation='login',
              accdate=sLastupdate,
              status ='login failure'
              )
      data = {
        'name': username        
      }
      resp = {
        'code': 20000,
        'mes': 'login failure,username or password error ',
        'data': data
      } 
      return HttpResponse(json.dumps(resp), content_type='application/json')


@csrf_exempt
def info(request):
  token = request.GET.get('token', None)  
  sql = analyzer_db()
  user_info = sql.search_user(key=token)
  sql.close()
  if user_info:
    data = {
      'name': user_info['username'],
      'avatar': 'http://135.251.207.221/images/avatar.gif',
      'mail': user_info['mail'],
      'roles': user_info['roles'],
      'level': user_info['level']
    }
    resp = {
      'code': 20000,
      'mes': 'get user info success',
      'data': data
    }
    return HttpResponse(json.dumps(resp), content_type='application/json')
  else:
    return HttpResponse('token error', status=405)


@csrf_exempt
def logout(request):
  # token = request.COOKIES['encodedAuth']
  username = request.COOKIES['username'] 
  sql = analyzer_db()  
  sLastupdate = datetime.datetime.today().strftime('%Y-%m-%d')
  log1 = sql.search_log(key1=username,key2='',key3='Logout',key4=sLastupdate,key5='logout success') 
  if not log1:
    log2=sql.insert_log(
        username = username,
        accweb='',
        operation='logout',
        accdate=sLastupdate,
        status ='logout success'
        )
  print('name=',username,file=fa,flush=True )  
  sql.close()
  # sql.delete_user(Id=user_info['id'])
  resp = {
    'code': 20000,
    'mes': 'Logout success',
  }
  return HttpResponse(json.dumps(resp), content_type='application/json')

def user_manage(request):
    dResult = {}
    dResult['code'] = 20000
    dResult['data'] = {}
    dResult['data']['status'] = []
    dResult['data']['items'] = []
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            if data:
                sUsername = data.get('username')
        else:
            sUsername = request.GET['username']
    except:
        dResult['data']['status'] = "Invalid Parameters"
        return HttpResponse(simplejson.dumps(dResult), content_type='application/json')

    cmd = """
        SELECT
            ID,Username, Email, Roles, Level, FirstName, LastName, FullName, LastLogin
        FROM
            auth_user
            %s
            
    """
    if sUsername == 'all':       
        sRule = ''
    else:
        sRule = "WHERE Username = '%s'" % sUsername       
        
    SQLConn = analyzer_db() 
    SQLConn.cur.execute(cmd % sRule)
    SQLResult = SQLConn.cur.fetchall()
    SQLConn.close()
        
    for row in SQLResult:        
        dItem = {}
        dItem['ID'] = row[0]        
        dItem['Username'] = row[1]
        dItem['Email'] = row[2]
        dItem['Roles'] = row[3]
        dItem['Level'] = row[4]        
        dItem['FirstName'] = row[5]
        dItem['LastName'] = row[6]
        dItem['FullName'] = row[7]
        dItem['LastLogin'] = str(row[8])
        dResult['data']['items'].append(dItem)
    
    return HttpResponse(simplejson.dumps(dResult), content_type='application/json')

def user_edit(request):
    
    try:
        sType = request.GET['type'] 
        sLastupdate = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        if sType == '1':
            sUsername = request.GET['Username']  
            sMail = request.GET['Mail'] 
            sLevel = request.GET['Level'] 
            sGrade = request.GET['Roles']            
        elif sType == '2':
            sUSID = request.GET['ID']
            sMail = request.GET['Mail']
            sLevel = request.GET['Level'] 
            sGrade = request.GET['Roles'] 
                        
    except:
        return HttpResponse('Invalid Parameters', content_type='application/json')
    
    dResult = {}
    dResult['code'] = 20000
    dResult['data'] = {}
    dResult['data']['items'] = []    
    Result ='' 
    
    # 1 add
    if sType == '1': 
        token, exp_time = create_token(sUsername)
        sql = analyzer_db()    
        old_user = sql.search_user(key=sUsername) 
        if old_user:           
            Result = 'The user is exist, do not add again.'    
        else:          
          user = sql.insert_user(
            sUsername, sMail, token,
            f_name ='',
            l_name ='',
            full_name ='',
            roles = sGrade,
            level = sLevel,
            exp_time = exp_time,
            login_time = sLastupdate)
          logging.debug(f'user = {user}')
          Result = 'Add user successful' 
        sql.close()   
    # 2 edit
    elif sType == '2': 
        sql = analyzer_db()        
        cmd="update auth_user set  Email ='%s', Level= '%s', Roles= '%s' where ID =  '%s'" % (sMail, sLevel, sGrade, sUSID) 
        
        sql.cur.execute(cmd)
        sql.conn.commit()
        Result = 'Modify user successful' 
        sql.close()
    dItem = {}
    dItem['Result'] = Result                
    dResult['data']['items'].append(dItem)
    return HttpResponse(simplejson.dumps(dResult), content_type='application/json')

tbl = 'auth_user'
db = dc('requestdb')
def delete(request):
    logging.info(f'executing delte {request.method}:  {request.body} ......')
    res = {
        'code': 20000
    }

    try:
        req = json.loads(request.body.decode('utf-8'))
        mail = req['mail']
        ids = req['ids']

        sql = 'delete from {tbl} where `Id` in ({LIST})'.format(
            tbl=tbl,
            LIST=ids
        )
        logging.info(f'delete, sql = {sql}')

        db.execute(sql)
    except Exception as e:
        logging.info(f"exception caught: {e}")
        res['code'] = 20001

    return HttpResponse(simplejson.dumps(res), content_type='application/json')


def role_list(request):
    try:
        ttype = request.GET['type']
        logging.debug(f'type = {ttype}')
    except:
        return HttpResponse('Invalid Parameters', content_type='application/json')

    res = {
        'code': 20000,
        'data': {
            'items': [],
        },
    }
    db = dc('requestdb')
    cmd = 'SELECT distinct `Grade` FROM `auth_grade` '
    logging.debug(f'devicedp_list, sql = {cmd}')

    df = db.read_query(cmd)
    df = df.replace({np.nan: None}).fillna('')
    for i_index in df.index:
        item = {}
        item['Grade'] = str(df.at[i_index, 'Grade'])
    
        res['data']['items'].append(item)

    return HttpResponse(simplejson.dumps(res), content_type='application/json')
    pass
