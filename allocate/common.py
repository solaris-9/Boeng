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
import uuid

app = 'common'

logger = logging.getLogger(app)
logging.basicConfig(
    filename=f'C:/reqLog/{app}Log.txt', 
    level=logging.DEBUG,
    format="{asctime}::{message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S"
)

db = dc('requestdb')


# def nwcc_list(request):
#     logger.debug('nwcc_list')
#     cus = dc('customerdb')
#     nwcc_fields = [
#         'Customer',
#         'OPID',
#         'Platform',
#         'TenantID',
#         'HDM'
#     ]
#     df = cus.read_query(
#         'select {fields} from `cdb_issues_saas`'.format(
#             fields=','.join(
#                 [f'`{field}`' for field in nwcc_fields]
#             )
#         )
#     )

#     res = {
#         'code': 20000,
#         'data': {
#             'items': [],
#         },
#     }
#     for i_index in df.index:
#         item = {}
#         for field in nwcc_fields:
#             item[field] = df.at[i_index, field]
#         res['data']['items'].append(item)
    
#     return HttpResponse(simplejson.dumps(res), content_type='application/json')
#     pass
def nwcc_list(request):
    logger.debug('nwcc_list')
    # cus = dc('customerdb')
    nwcc_fields = [
        'ID',
        'field_customer',
        'field_status'
    ]
    df = db.read_query(
        'select {fields} from `tbl_nwcc`'.format(
            fields=','.join(
                [f'`{field}`' for field in nwcc_fields]
            )
        )
    )

    res = {
        'code': 20000,
        'data': {
            'items': [],
        },
    }
    for i_index in df.index:
        item = {}
        for field in nwcc_fields:
            item[field] = df.at[i_index, field]
        res['data']['items'].append(item)
    
    return HttpResponse(simplejson.dumps(res), content_type='application/json')
    pass
def opid_list(request):
    cus = dc('customerdb')
    sql = "select distinct `OPID` from `cdb_issues_preconfig` where `BusinessLine` = 'BBD-NWF' order by `OPID` ASC"
    logger.debug('opid_list', f'sql = {sql}')
    df = cus.read_query(sql)

    res = {}
    res['code'] = 20000
    res['data'] = {}
    res['data']['items'] = []
    for i_index in df.index:
        item = {}
        item['OPID'] = df.at[i_index, 'OPID']
        res['data']['items'].append(item)
    
    return HttpResponse(simplejson.dumps(res), content_type='application/json')
    pass

def country_list(request):
    sql = "select `country`,`iso` from `tbl_country` order by `iso` ASC"
    logger.debug(f'sql = {sql}')
    df = db.read_query(sql)

    res = {}
    res['code'] = 20000
    res['data'] = {}
    res['data']['items'] = []
    for i_index in df.index:
        item = {}
        item['country'] = df.at[i_index, 'country']
        item['iso'] = df.at[i_index, 'iso']
        res['data']['items'].append(item)
    
    return HttpResponse(simplejson.dumps(res), content_type='application/json')
    pass

def hosting_list(request):
    sql = "select `field_public_cloud` as cloud,`field_region` as region from `tbl_platform`"
    logger.debug(f'sql = {sql}')
    df = db.read_query(sql)

    res = {}
    res['code'] = 20000
    res['data'] = {}
    res['data']['items'] = []
    for i_index in df.index:
        item = {}
        item['cloud'] = df.at[i_index, 'cloud']
        item['region'] = df.at[i_index, 'region']
        res['data']['items'].append(item)
    
    return HttpResponse(simplejson.dumps(res), content_type='application/json')
    pass

# def csv_upload(request):
#     res = {}
#     res['code'] = 20000
#     res['data'] = {}
#     logger.debug('csv_upload, start: {}, {}'.format(request.method, request.FILES.get('file')))
#     if request.method == 'POST' and request.FILES.get('file'):
#         upload_file = request.FILES['file']
#         save_path = os.path.join(rs.UPLOAD_ROOT, upload_file.name)
#         logger.debug(f'csv_upload, save_path = {save_path}')
#         with open(save_path, 'wb+') as destination:
#             for chunk in upload_file.chunks():
#                 destination.write(chunk)

#     res['data']['status'] = 'File uploaded OK'
#     logger.debug(f'csv_upload, end: {res}')
#     return HttpResponse(simplejson.dumps(res), content_type='application/json')
#     pass

# def download(request):
#     #logger.debug('download, request.body:', request.body.decode('utf-8'))
#     name = request.GET['file']
#     full_path = os.path.join(rs.UPLOAD_ROOT, name)
#     logger.debug(f'download, file name: {name}, full path: {full_path}')
#     if os.path.exists(full_path):
#         with open(full_path, 'rb') as fh:
#             content = "application/vnd.ms-excel"
#             if 'pdf' in name.lower():
#                 content = "application/pdf"
#             res = HttpResponse(fh.read(), content_type=content)
#             res['Content-Disposition'] = 'inline; filename=' + name
#             return res
#     raise Http404
#     pass

def customer_list(request):
    res = {
        'code': 20000,
        'data': {
            'items': [],
        },
    }
    cus = dc('bbddb')
    sql = "SELECT `Summary` as customer, `Key` as id, `CustomerReferenceNumber` as `cid` FROM `jira_issues_cust`"
    logger.debug('fetch_customer', f'{sql}')
    df = cus.read_query(sql)
    l_customers = {}
    for i_index in df.index:
        #l_customers.append({'customer': df.at[i_index, 'customer'], 'key': df.at[i_index, 'key']})
        l_customers[df.at[i_index, 'customer']] = {
            'id': df.at[i_index, 'id'],
            'cid': df.at[i_index, 'cid']
        }

    local_sql = 'SELECT `Customer` as customer, `Key` as id FROM `tbl_local_customers`'
    logger.debug('fetch_customer', f'{local_sql}')
    local_df = db.read_query(local_sql)
    for i_index in local_df.index:
        l_cus = local_df.at[i_index, 'customer']
        if l_cus not in l_customers.keys():
            #l_customers.append({'customer': l_customer, 'key': local_df.at[i_index, 'key']})
            l_customers[l_cus] = {
                'id': local_df.at[i_index, 'id'],
                'cid': ''
            }
    
    for cus in l_customers.keys():
            res['data']['items'].append({
                'customer': cus,
                'key': l_customers[cus]['id'],
                'cid': l_customers[cus]['cid']
            })
    return HttpResponse(simplejson.dumps(res), content_type='application/json')

tbl_local_customers_field = [
    'Customer', 'Description', 'Id', 'ONT','NWF','FWA','Local','Source', 'AddedBy', 'AddedOn'
]

def handle_new_customer_add_jira(data, uname):
    logger.debug(f'handle_new_customer_add: {data.__str__()}')
    customer = data["Customer"]
    desc = data["Description"]
    #mail = data["AddedBy"]
    logger.debug(f'handle_new_customer_add, {customer}')
    jira = Jira()

    # email -> uname mapping
    d_cus = dc('customerdb')
    df = d_cus.read_table('file_issues_engineer')
    mail_map = {}
    for i_index in df.index:
        mail_map[df.at[i_index, 'Email'].strip().lower()] = df.at[i_index, 'CSL'].strip()

    ont = ""
    logger.debug(f'{data["ONT"].strip().lower()}')
    if data['ONT'].strip().lower() in mail_map.keys():
        logger.debug(f'{data["ONT"].strip().lower()} in mail_map.keys')
        ont = mail_map[data['ONT'].strip().lower()]
    ont = ""
    if data['NWF'].strip().lower() in mail_map.keys():
        nwf = mail_map[data['NWF'].strip().lower()]
    ont = ""
    if data['FWA'].strip().lower() in mail_map.keys():
        fwa = mail_map[data['FWA'].strip().lower()]
    ont = ""
    if data['Local'].strip().lower() in mail_map.keys():
        local = mail_map[data['Local'].strip().lower()]
    param = {
        "fields": {
            "project": {"key": "BBDCUST"},
            "summary": f"{customer}",
            "description": f"{desc}",
            "issuetype": {"id": "15401"},
            "reporter": {"name": f"{uname}"},
            "customfield_14555": f"{data['Id']}",
            "customfield_18893": {"name": f"{ont}"},
            "customfield_37445": {"name": f"{nwf}"},
            "customfield_37783": {"name": f"{fwa}"},
            "customfield_38490": {"name": f"{local}"},
        }
    }
    logger.debug(f'handle_new_customer_add, param= {param.__str__()}')
    rsp = jira.post_with_resp('rest/api/latest/issue', param)
    if rsp.ok:
        new_key = rsp.json()['key']
        logger.debug(f'handle_new_customer_add, Created new key = {new_key}')
        return new_key
    else:
        logger.debug(f'handle_new_customer_add failed: {rsp.json()}')
        return None
    pass

def handle_new_customer_add(tbl, data, uname):
    logger.debug(data)
    rsp = handle_new_customer_add_jira(data, uname)
    if rsp is None:
        logger.debug('handle_new_customer_add failed!!!')
        return 'New Customer Add failed'
    l_fields = ','.join([f'`{f}`' for f in tbl_local_customers_field] + ['`Key`'])
    l_values = ','.join([f'"{v}"' for v in [data[k] for k in tbl_local_customers_field]] + [f'"{rsp}"'])
    sql = "insert into {tbl} ({fields}) values ({values})".format(
        tbl=tbl,
        fields=l_fields,
        values=l_values
    )
    logger.debug(f'handle_new_customer_add: sql')
    db.execute(sql)
    return 'New Customer Add successful'
    pass

def new_customer_add(request):
    res = {
        'code': 20000,
        'data': {
            'items': [],
        },
    }

    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            if data:
                l_data = {}
                for field in tbl_local_customers_field:
                    l_data[field] = data.get(field)
                uname = data.get('uname')
    except Exception as e:
        logger.debug(f'new_customer_add, Invalid Parameters: {e}')
        res['data']['status'] = "Invalid Parameters"
        return HttpResponse(simplejson.dumps(res), content_type='application/json')

    res['data']['status'] = handle_new_customer_add('tbl_local_customers', l_data, uname)
    return HttpResponse(simplejson.dumps(res), content_type='application/json')


def device_list(request):
    res = {
        'code': 20000,
        'data': {
            'items': [],
        },
    }

    try:
        ttype = request.GET['type']
        logger.debug(f'type = {ttype}')
    except:
        return HttpResponse('Invalid Parameters', content_type='application/json')


    cus = dc('customerdb')
    sql = """
        SELECT `Product`, LEFT(`KitCode`, 10) AS Code, `Businessline` AS Bizline 
        FROM `btm_issues_device` AS bid 
        WHERE LEFT(`KitCode`, 10) NOT LIKE '%%ZZ' 
        AND NOT EXISTS (
            SELECT * FROM file_issues_erp AS fie 
            WHERE LEFT(bid.KitCode, 10) = fie.KitCode 
            AND fie.`CommercialStatus` IN ('CE', 'PO', 'SD')
        )
        """
    if ttype == 'beacon':
        sql = f"{sql} and `Product` LIKE 'Beacon%%'"
    
    logger.debug(f'sql = {sql}')
    df = cus.read_query(sql)

    for i_index in df.index:
        res['data']['items'].append(
            {
                'Product': df.at[i_index, 'Product'],
                'Code': df.at[i_index, 'Code'],
                'Bizline': df.at[i_index, 'Bizline'],
            }
        )
        
    logger.debug('device_list.size = %s', len(res['data']['items']))

    return HttpResponse(simplejson.dumps(res), content_type='application/json')


def file_upload(request):
    res = {}
    res['code'] = 20000
    res['data'] = {}
    logger.debug('file_upload, start: {}, {}'.format(request.method, request.FILES.get('file')))
    if request.method == 'POST' and request.FILES.get('file'):
        upload_file = request.FILES['file']
        file_name = "{}____{}".format(uuid.uuid4().hex, upload_file.name)
        save_path = os.path.join(rs.UPLOAD_ROOT, file_name)
        logger.debug(f'csv_upload, save_path = {save_path}')
        with open(save_path, 'wb+') as destination:
            for chunk in upload_file.chunks():
                destination.write(chunk)

    res['data']['status'] = 'File uploaded OK'
    res['data']['name'] = file_name
    logger.debug(f'csv_upload, end: {res}')
    return HttpResponse(simplejson.dumps(res), content_type='application/json')
    pass

def file_download(request):
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
    else:
        raise Http404
    pass
