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
from django.http import HttpResponse, Http404
from pymysql.converters import escape_string
from django.conf import settings
from utils import analyzer_db
from utils import DatabaseConnector as dc
from utils import Jira as Jira
import pandas as pd
import numpy as np
import allocate.utils as u
import logging
from request import settings as rs

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename='C:/reqLog/gradeLog.txt', 
    level=logging.DEBUG,
    format="{asctime}::{message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S"
)

db = dc('requestdb')
tbl = 'auth_grade'

grade_fields = {
	'GID': {'show': True, 'type': 'str'},
	'Grade': {'show': True, 'type': 'str'},
	'Add': {'show': True, 'type': 'str'},
	'Edit': {'show': True, 'type': 'str'},
	'Delete': {'show': True, 'type': 'str'},
	'Search': {'show': True, 'type': 'str'},
	'View': {'show': True, 'type': 'str'},
	'Export': {'show': True, 'type': 'str'},
	'Download': {'show': True, 'type': 'str'},
	'RecordTime': {'show': True, 'type': 'str'},
}

def grade_fetch(request):
    try:
        ttype = request.GET['type']
        if ttype == '0':
            gid = request.GET['GID']
    except:
        return HttpResponse('Invalid Parameters', content_type='application/json')

    res = {
        'code': 20000,
        'data': {
            'items': [],
        },
    }

    sql = 'select {fields} from {tbl}'.format(
        fields=','.join([f'`{field}`' for field in grade_fields.keys()]),
        tbl=tbl
    )

    # Type == 0: Fetch a single Grade
    # Type == 1: Fech all Grades
    if ttype == '0':
        sql = f'{sql} where `GID` = "{gid}" '

    logger.debug(f'fetch_grade, sql = {sql}')

    df = db.read_query(sql)
    for i_index in df.index:
        item = {}
        for field in grade_fields.keys():
            if type(df.at[i_index, field]) == pd.Timestamp:
                item[field] = str(df.at[i_index, field])
            elif type(df.at[i_index, field]) == np.int64:
                item[field] = int(df.at[i_index, field])
            else:
                item[field] = df.at[i_index, field]
        res['data']['items'].append(item)

    return HttpResponse(simplejson.dumps(res), content_type='application/json')


def handle_grade_edit(tbl, data):
    generated_str = u.generate_update_sql(grade_fields, data, ['RecordTime'])

    sql = 'update {tbl} set {fields} where `GID` = "{GID}"'.format(
        tbl=tbl,
        fields=generated_str,
        GID=data['GID']
    )
    logger.debug(f'handle_grade_edit, sql = {sql}')
    db.execute(sql)

    pass

def handle_grade_delete(tbl, llist):
    sql = 'delete from {tbl} where `GID` in ({B_LIST})'.format(
        tbl=tbl,
        B_LIST=u.generate_delete_sql(llist)
    )
    logger.debug(f'handle_grade_delete, sql = {sql}')
    db.execute(sql)

    pass

def handle_grade_add(tbl, data):
    l_data = data
    
    l_data['GID'] = u.strNum(u.gen_tbl_index(tbl, 'GID', db), 'G', 6)

    generated_str = u.generate_insert_sql(grade_fields, l_data, skip=['RecordTime'])

    sql = "insert into {tbl} ({fields}) values ({values})".format(
            tbl=tbl,
            fields=generated_str[0],
            values=generated_str[1]
        )
    logger.debug(f'handle_grade_add: sql = {sql}')
    db.execute(sql)
    rt =  'Add successful, back and refresh page to show it'

    return rt
    pass

def grade_edit(request):
    logger.debug('grade_edit')
    res = {
        'code': 20000,
        'data': {
            'items': [],
        },
    }

    try:
        #ttype = request.GET['type']
        #logger.debug(f'ttype = {ttype}')
        #mail = request.GET['mail']
        #level = request.GET['level']
        data = json.loads(request.body)
        # Type = 1: Add
        # Type = 2: Update
        # Type = 3: Delete
        if data:
            ttype = data.get('type')
            if ttype in ['1', '2']:
                l_data = {}
                for field in [f for f in grade_fields.keys() if f != 'GID']:
                    l_data[field] = data.get(field)
            if ttype == '2':
                l_data['GID'] = data.get('GID')
            elif ttype == '3':
                l_delete_list = data.get('deletelist')
    except:
        return HttpResponse('Invalid Parameters', content_type='application/json')

    # 1 add
    if ttype == '1':
        rt = handle_grade_add(tbl, l_data)
        res['data']['status'] = rt  
    # 2 update
    elif ttype == '2':
        handle_grade_edit(tbl, l_data)
        res['data']['status'] = "Edit successful"
        pass
    # 3 delete
    elif ttype == '3':
        handle_grade_delete(tbl, l_delete_list)
        res['data']['status'] = "Delete successful"


    return HttpResponse(simplejson.dumps(res), content_type='application/json')



def download(request):
    #logger.debug('download, request.body:', request.body.decode('utf-8'))
    name = request.GET['file']
    full_path = os.path.join(rs.UPLOAD_ROOT, name)
    logger.debug(f'download, file name: {name}, full path: {full_path}')
    if os.path.exists(full_path):
        with open(full_path, 'rb') as fh:
            content = "application/vnd.ms-excel"
            if 'pdf' in name.lower():
                content = "application/pdf"
            res = HttpResponse(fh.read(), content_type=content)
            res['Content-Disposition'] = 'inline; filename=' + name
            return res
    raise Http404
    pass

