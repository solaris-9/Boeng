from django.shortcuts import render,redirect

# Create your views here.

from datetime import datetime, timedelta
import simplejson
import pymysql
from decimal import Decimal
import json
import os
import xlrd
# import difflib
import shutil
from openpyxl import Workbook
from openpyxl.styles import Alignment
import smtplib 
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.http import HttpResponse
from pymysql.converters import escape_string
from django.conf import settings
from utils import analyzer_db

def GetJSONList(lTitle, lIssue):
    lResult = []
    for row in lIssue:
        dIssue = {}
        for t, c in zip(lTitle, row):
            dIssue[t] = c
            lResult.append(dIssue)
    return lResult


def List2String(lList):
    sResult = "("
    for i in lList:
        m = escape_string(i)
        m = "'" + m + "'"
        sResult = sResult + m + "," 
    sResult = sResult[:-1] + ")"
    return sResult

def repspecial(string):
    sString = string.strip().replace('\u200b','')
    return sString

def strNum(strN,prefix,num):
    strN += 1
    sID = prefix + str(strN).zfill(num)
    return sID


def tbl_index(tblname,ID,SQLConn):
    sql = "select count(%s) as num from %s " % (ID,tblname)
    SQLConn.cur.execute(sql)      
    SQLResult = SQLConn.cur.fetchall()    
    count = SQLResult[0][0]
    if count > 0 :    
        sql="SELECT %s FROM %s ORDER BY %s" % (ID,tblname,ID)
        SQLConn.cur.execute(sql)
        SQLConn.conn.commit() 
        last_result = [x[0] for x in SQLConn.cur.fetchall()][-1]
        ST = last_result[1:]
        strN = int(ST)
    else:
        strN = 0
    return strN

def check_numeric(input_str):
    val = 0
    input_str1 = input_str.replace(".","")
    if input_str1.isdigit() or (input_str1[0] == '-' and input_str1[1:].isdigit()):
        # 如果字符串只包含数字字符或者以负号开头并且剩余部分只包含数字字符，则认为是数值
        return float(input_str)  # 返回数值表示
    else:
        return val

    print('request.body:', request.body.decode('utf-8'), file=fa, flush=True)
    dResult = {}
    dResult['code'] = 20000
    dResult['data'] = {}
    dResult['data']['status'] = []
    dResult['data']['items'] = []
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            if data:
                sMail = data.get('mail')
                print('Mail=', sMail, file=fa, flush=True)
    except:
        dResult['data']['status'] = "Invalid Parameters"
        return HttpResponse(simplejson.dumps(dResult), content_type='application/json')

    cmd = """
            SELECT
               Code,DeviceName,Description,CodeId
            FROM
              v_code
            """

    SQLConn = analyzer_db()
    SQLConn.cur.execute(cmd)
    SQLResult = SQLConn.cur.fetchall()
    SQLConn.close()

    for row in SQLResult:
        dItem = {}
        dItem['Code'] = row[0]
        dItem['DeviceName'] = row[1]
        dItem['Description'] = row[2]
        dItem['CodeId'] = row[3]
        dResult['data']['items'].append(dItem)
    return HttpResponse(simplejson.dumps(dResult), content_type='application/json')