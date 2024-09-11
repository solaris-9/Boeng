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



def generate_insert_sql(fields, data):
    field_str = []
    value_str = []
    for f in fields.keys():
        field_str.append('`{}`'.format(f))
        if fields[f]['type'] == 'str':
            value_str.append("'{}'".format(data[f]))
        elif fields[f]['type'] == 'bool':
            value_str.append('{}'.format(data[f]))

    return (
        ',\n'.join(field_str),
        ',\n'.join(value_str)
    )
    pass

def generate_update_sql(fields, data):
    field_str = []
    for f in fields.keys():
        if fields[f]['type'] == 'str':
            field_str.append("`{field}` = '{value}'".format(field=f, value=data[f]))
        elif fields[f]['type'] == 'bool':
            field_str.append("`{field}` = {value}".format(field=f, value=data[f]))

    return ',\n'.join(field_str)
    pass

def generate_delete_sql(llist):
    values = []
    for val in llist.split(','):
        values.append('"{}"'.format(val))
    return ',\n'.join(values)
    pass

