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
from utils import mail
import pandas as pd
import numpy as np
import allocate.utils as u
import logging
from request import settings as rs

app = 'devicedp'

logger = logging.getLogger(app)
logging.basicConfig(
    filename=f'C:/reqLog/{app}Log.txt', 
    level=logging.DEBUG,
    format="{asctime}::{message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S"
)

db = dc('requestdb')
tbl = 'tbl_devicedp'

devicedp_fields = {
	'ID': {'type': 'str'},
	'field_customer': {'type': 'str'},
    'field_status': {'type': 'str'},
    'field_assignee': {'type': 'str'},
    'field_mail': {'type': 'str'},
    'field_jira_id': {'type': 'str'},
    'field_root_device': {'type': 'str'},
    'field_product_variant': {'type': 'str'},
    'field_managed_by_hc': {'type': 'str'},
    'field_managed_by_hdm': {'type': 'str'},
    'field_home_controller': {'type': 'str'},
    # 'field_speedtest_needed': {'type': 'str'},
    # 'field_speedtest': {'type': 'str'},
    # 'field_activate_container': {'type': 'str'},
    # 'field_container_devices': {'type': 'str'},
    'field_root_update_method': {'type': 'str'},
    'field_separate_license': {'type': 'str'},
    'field_auto_ota': {'type': 'str'},
    'field_waiver': {'type': 'str'},
    'field_boeng_rule': {'type': 'str'},
    'field_whitelisting_method': {'type': 'str'},
    'field_ip_ranges': {'type': 'str'},
    'field_customer_id': {'type': 'str'},
    'field_csv_file': {'type': 'str'},
    'field_boeng_options': {'type': 'str'},
    'field_acs_url': {'type': 'str'},
    'field_acs_username': {'type': 'str'},
    'field_acs_password': {'type': 'str'},
    'field_usp_addr': {'type': 'str'},
    'field_usp_port': {'type': 'str'},
    'field_mesh_extended': {'type': 'str'},
    'field_extender_beacon': {'type': 'str'},
    'field_extender_update_method': {'type': 'str'},
    'field_extender_separate_license': {'type': 'str'},
    'field_extender_auto_ota': {'type': 'str'},
    'field_extender_waiver': {'type': 'str'},
	'field_additional': {'type': 'str'},
    'creator': {'type': 'str'},
    'createon': {'type': 'str'},
    'modifier': {'type': 'str'},
    'modifiedon': {'type': 'str'},
}


def devicedp_list(request):
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
            fields=','.join(
                ['`{field}`'.format(field=f) for f in devicedp_fields.keys()]
            ),
            tbl=tbl
        )

        if ttype == 'all':
            cmd = f'{cmd} ORDER BY `ID`'
        elif ttype == 'single':
            cmd = f'{cmd} WHERE `ID` = "{id}" '

        logger.debug(f'devicedp_list, sql = {cmd}')

        df = db.read_query(cmd)
        df = df.replace({np.nan: None}).fillna('')
        for i_index in df.index:
            item = {}
            for field in devicedp_fields.keys():
                match devicedp_fields[field]['type']:
                    case 'str':
                        item[field] = str(df.at[i_index, field])
        
            res['data']['items'].append(item)

    return HttpResponse(simplejson.dumps(res), content_type='application/json')
    pass

def handle_devicedp_edit(tbl, data):
    generated_str = u.generate_update_sql(devicedp_fields, data, ['creator', 'createon'])

    sql = 'update {tbl} set {fields} where `ID` = "{ID}"'.format(
        tbl=tbl,
        fields=generated_str,
        ID=data['ID']
    )
    logger.debug(f'handle_devicedp_edit, sql = {sql}')
    db.execute(sql)

    # sending email
    tto = []
    if 'modifier' in data.keys() and data['modifier'] is not None:
        tto.append(data['modifier'])
    if 'creator' in data.keys() and data['creator'] is not None:
        tto.append(data['creator'])
    if 'field_assignee' in data.keys() and data['field_assignee'] is not None and len(data['field_assignee']) > 0:
        tto.append(data['field_assignee'])

    logging.debug(f'tto = {tto}')

    subject = f"{data['ID']}: updated"
    body = f"""
    ID: {data['ID']}
    Modifier: {data['modifier']}
    Status: {data['field_status']}
    Assignee: {data['field_assignee']}
    """
    mail(tto, subject, body)
    pass

def handle_devicedp_delete(tbl, llist, mmail):
    sql = 'delete from {tbl} where `ID` in ({B_LIST})'.format(
        tbl=tbl,
        B_LIST=u.generate_delete_sql(llist)
    )
    logger.debug(f'handle_devicedp_delete, sql = {sql}')
    db.execute(sql)

    # sending email
    tto = [mmail]
    logging.debug(f'tto = {tto}')

    subject = f'{llist}: deleted'
    body = f"""
    Tickets deleted: {llist}
    Deleted by: {mmail}
    """
    logging.debug(f'subject = {subject}')
    logging.debug(f'boday = {body}')

    mail(tto, subject, body)

    pass

def handle_devicedp_add(tbl, data):
    l_data = data
    
    #check if exists
    # sql = "select count(Customer) as count from {} where customer='{}'".format(
    #     tbl, 
    #     l_data['Customer']
    # )
    # count = db.read_query(sql).at[0, 'count']

    # logger.debug(f'handle_boeng_rule_add, count = {count}')
    # # to add
    # if count == 0 or l_data['Customer'] == '':
    l_data['ID'] = u.strNum(u.gen_tbl_index(tbl, 'ID', db), 'DEVICEDP-', 10)

    generated_str = u.generate_insert_sql(devicedp_fields, l_data, skip=['modifier', 'modifiedon'])

    sql = "insert into {tbl} ({fields}) values ({values})".format(
            tbl=tbl,
            fields=generated_str[0],
            values=generated_str[1]
        )
    logger.debug(f'handle_devicedp_add: sql = {sql}')
    db.execute(sql)
    rt =  'Add successful, back and refresh page to show it'
    # else:
    #     rt = "The customer has already been added, unabled to be added again!"

    # sending email
    tto = []
    if 'creator' in data.keys() and data['creator'] is not None:
        tto.append(data['creator'])
    if 'field_assignee' in data.keys() and data['field_assignee'] is not None and len(data['field_assignee']) > 0:
        tto.append(data['field_assignee'])

    logging.debug(f'tto = {tto}')

    subject = f"{data['ID']}: created"
    body = f"""
    ID: {data['ID']}
    Creator: {data['creator']}
    Status: {data['field_status']}
    Assignee: {data['field_assignee']}
    """
    mail(tto, subject, body)

    return rt
    pass

def devicedp_edit(request):
    logger.debug('devicedp_edit, request.body:', request.body.decode('utf-8'))
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

                if ttype in ['add', 'edit']:
                    l_data = {}
                    for field in [f for f in devicedp_fields.keys() if f != 'ID']:
                        l_data[field] = data.get(field)
                if ttype == 'edit':
                    l_data['ID'] = data.get('ID')
                elif ttype == 'delete':
                    l_delete_list = data.get('deletelist')

    except Exception as e:
        logger.debug(f'devicedp_edit, Invalid Parameters: {e}')
        res['data']['status'] = "Invalid Parameters"
        return HttpResponse(simplejson.dumps(res), content_type='application/json')

    # 1x add
    if ttype == 'add':
        rt = handle_devicedp_add(tbl, l_data)
        res['data']['status'] = rt
            
    # 2 edit
    elif ttype == 'edit':
        handle_devicedp_edit(tbl, l_data)
        res['data']['status'] = "Edit successful"
        pass

    # 3 delete
    elif ttype == 'delete':
        handle_devicedp_delete(tbl, l_delete_list, mail)
        pass
        res['data']['status'] = "Delete successful"


    return HttpResponse(simplejson.dumps(res), content_type='application/json')


# def nwcc_list(request):
#     logger.debug('nwcc_list')
#     cus = dc('customerdb')
#     nwcc_fields = [
#         'Customer',
#         'OPID',
#         'Platform',
#         'TenantID'
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

# def opid_list(request):
#     cus = dc('customerdb')
#     sql = "select distinct `OPID` from `cdb_issues_preconfig` where `BusinessLine` = 'BBD-NWF' order by `OPID` ASC"
#     logger.debug('opid_list', f'sql = {sql}')
#     df = cus.read_query(sql)

#     res = {}
#     res['code'] = 20000
#     res['data'] = {}
#     res['data']['items'] = []
#     for i_index in df.index:
#         item = {}
#         item['OPID'] = df.at[i_index, 'OPID']
#         res['data']['items'].append(item)
    
#     return HttpResponse(simplejson.dumps(res), content_type='application/json')
#     pass

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

# def fetch_customer(request):
#     res = {
#         'code': 20000,
#         'data': {
#             'items': [],
#         },
#     }
#     cus = dc('customerdb')
#     sql = "SELECT `Summary` FROM `jira_issues_cust` ORDER BY `Summary`"
#     logger.debug('fetch_customer', f'{sql}')
#     df = cus.read_query(sql)
#     l_customers = []
#     for i_index in df.index:
#         l_customers.append(df.at[i_index, 'Summary'])

#     local_sql = 'SELECT `Customer` FROM `tbl_local_customers` ORDER BY `Customer`'
#     logger.debug('fetch_customer', f'{local_sql}')
#     local_df = db.read_query(local_sql)
#     for i_index in local_df.index:
#         l_customer = local_df.at[i_index, 'Customer']
#         if l_customer not in l_customers:
#             l_customers.append(l_customer)
    
#     for cus in l_customers:
#             res['data']['items'].append(
#                 {
#                     'Customer': cus
#                 }
#             )
#     return HttpResponse(simplejson.dumps(res), content_type='application/json')

# tbl_local_customers_field = [
#     'Customer', 'Description', 'Source', 'AddedBy', 'AddedOn'
# ]

# def handle_new_customer_add_jira(data, uname):
#     logger.debug(f'handle_new_customer_add: {data.__str__()}')
#     customer = data["Customer"]
#     desc = data["Description"]
#     #mail = data["AddedBy"]
#     logger.debug(f'handle_new_customer_add, {customer}')
#     jira = Jira()
#     param = {
#         "fields": {
#             "project": {"key": "BBDCUST"},
#             "summary": f"{customer}",
#             "description": f"{desc}",
#             "issuetype": {"id": "15401"},
#             "reporter": {"name": f"{uname}"}
#         }
#     }
#     logger.debug(f'handle_new_customer_add, param= {param.__str__()}')
#     rsp = jira.post_with_resp('rest/api/latest/issue', param)
#     if rsp.ok:
#         new_key = rsp.json()['key']
#         logger.debug(f'handle_new_customer_add, Created new key = {new_key}')
#         return new_key
#     else:
#         logger.debug(f'handle_new_customer_add failed: {rsp.json()}')
#         return None
#     pass

# def handle_new_customer_add(tbl, data, uname):
#     logger.debug('handle_new_customer_add ...', data)
#     rsp = handle_new_customer_add_jira(data, uname)
#     if rsp is None:
#         logger.debug('handle_new_customer_add failed!!!')
#         return 'New Customer Add failed'
#     l_fields = ','.join([f'`{f}`' for f in tbl_local_customers_field] + ['`Key`'])
#     l_values = ','.join([f'"{v}"' for v in [data[k] for k in tbl_local_customers_field]] + [f'"{rsp}"'])
#     sql = "insert into {tbl} ({fields}) values ({values})".format(
#         tbl=tbl,
#         fields=l_fields,
#         values=l_values
#     )
#     logger.debug('handle_new_customer_add', f'{sql}')
#     db.execute(sql)
#     return 'New Customer Add successful'
#     pass

# def new_customer_add(request):
#     res = {
#         'code': 20000,
#         'data': {
#             'items': [],
#         },
#     }

#     try:
#         if request.method == 'POST':
#             data = json.loads(request.body)
#             if data:
#                 l_data = {}
#                 for field in tbl_local_customers_field:
#                     l_data[field] = data.get(field)
#                 uname = data.get('uname')
#     except Exception as e:
#         logger.debug(f'new_customer_add, Invalid Parameters: {e}')
#         res['data']['status'] = "Invalid Parameters"
#         return HttpResponse(simplejson.dumps(res), content_type='application/json')

#     res['data']['status'] = handle_new_customer_add('tbl_local_customers', l_data, uname)
#     return HttpResponse(simplejson.dumps(res), content_type='application/json')
