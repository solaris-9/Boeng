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

app = 'customer'

logger = logging.getLogger(app)
logging.basicConfig(
    filename=f'C:/reqLog/{app}Log.txt', 
    level=logging.DEBUG,
    format="{asctime}::{message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S"
)

db = dc('bbddb')
tbl = 'jira_issues_cust'

customer_fields = {
	'field_jira_id': {'col': 'Key', 'jira': 'key', 'update': 'none'},
	'field_customer_name': {'col': 'Summary', 'jira': 'summary', 'update': 'text'},
    'field_description': {'col': 'Description', 'jira': 'description', 'update': 'text'},
    'field_customer_olcs': {'col': 'CustomerReference', 'jira': 'customfield_51694', 'update': 'text'},
    'field_customer_impact': {'col': 'CustomerImpact', 'jira': 'customfield_46695', 'update': 'text'},
    'field_ont_plm': {'col': 'PLMPrime', 'jira': 'customfield_18893', 'update': 'none'},
    'field_nwf_plm': {'col': 'PLMContact', 'jira': 'customfield_37445', 'update': 'none'},
    'field_fwa_plm': {'col': 'ProductManager', 'jira': 'customfield_37783', 'update': 'none'},
    'field_local_contact': {'col': 'ContactPerson', 'jira': 'customfield_38490', 'update': 'none'},
}


def customer_list(request):
    try:
        mail = request.GET['mail']
        level = request.GET['level']
        ttype = request.GET['type']
        logger.debug(f'mail = {mail}, level = {level}, type = {ttype}')
        if ttype == 'single':
            id = request.GET['ID']
            logger.debug(f'id = {id}')
    except:
        return HttpResponse('Invalid Parameters', content_type='application/json')

    res = {
        'code': 20000,
        'data': {
            'items': [],
        },
    }

    if level != 'undefined':
        cmd = 'SELECT {fields} FROM {tbl} '.format(
            fields=u.generate_select_as_sql(customer_fields),
            tbl=tbl
        )

        if ttype == 'all':
            cmd = f'{cmd} ORDER BY field_jira_id'
        elif ttype == 'single':
            cmd = f"{cmd} WHERE `Key` = '{id}' "

        logger.debug(f'customer_list, sql = {cmd}')

        df = db.read_query(cmd)
        df = df.replace({np.nan: None}).fillna('')
        logger.debug(df)
        for i_index in df.index:
            item = {}
            for field in customer_fields.keys():
                item[field] = df.at[i_index, field]
        
            res['data']['items'].append(item)

    return HttpResponse(simplejson.dumps(res), content_type='application/json')
    pass

def handle_customer_edit(tbl, data):
    ### To save to Jira
    #JSON = {"update":{"customfield_37499":[{"set":"fwajira, 23/Oct/24 12:14 PM"}],"customfield_28692":[{"set":"1234"}]}}
    param = {
        'update': {}
    }
    for l_key in data.keys():
        if customer_fields[l_key]['update'] == 'none':
            continue
        elif customer_fields[l_key]['update'] == 'text':
            param["update"][customer_fields[l_key]['jira']] = [{"set": "{}".format(data[l_key])}]
        elif customer_fields[l_key]['update'] == 'name':
            param["update"][customer_fields[l_key]['jira']] = [{"set": {"emailAddress": "{}".format(data[l_key])}}]
        

    logger.debug(param)
    jira = Jira()
    rsp = jira.put_with_resp('rest/api/latest/issue/{}'.format(data['field_jira_id']), param)
    if rsp.ok:
        logger.debug('handle_customer_edit, success')
        return True
    else:
        logger.debug('handle_customer_edit failed: {}'.format(rsp.json()))
        return False
    pass

def customer_edit(request):
    logger.debug('customer_edit, request.body:', request.body.decode('utf-8'))
    res = {
        'code': 20000,
        'data': {
            'items': [],
        },
    }

    try:
        ttype = ''
        sLastupdate = datetime.today().strftime('%Y-%m-%d')
        if request.method == 'POST':
            data = json.loads(request.body)
            if data:
                ttype = data.get('type')
                mail = data.get('mail')

                if ttype in ['edit']:
                    l_data = {}
                    for field in customer_fields.keys():
                        l_data[field] = data.get(field)

    except Exception as e:
        logger.debug(f'customer_edit, Invalid Parameters: {e}')
        res['data']['status'] = "Invalid Parameters"
        return HttpResponse(simplejson.dumps(res), content_type='application/json')

    if ttype == 'edit':
        ret = handle_customer_edit(tbl, l_data)
        if ret:
            res['data']['status'] = "Edit successful"
        else:
            res['data']['status'] = "Edit failed"
        pass

    return HttpResponse(simplejson.dumps(res), content_type='application/json')


