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
#logging.basicConfig(filename='C:/reqLog/boengLog.txt', level=logging.DEBUG, format='%(asctime)s')
logging.basicConfig(
    filename='C:/reqLog/boengLog.txt', 
    level=logging.DEBUG,
    format="{asctime}::{message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S"
)

db = dc('requestdb')
tbl = 'tblboengrule'

boengrule_fields = {
	'B_ID': {'show': True, 'type': 'str'},
	'Customer': {'show': True, 'type': 'str'},
	'device': {'show': True, 'type': 'str'},
	'OPID': {'show': True, 'type': 'str'},
	'whitelistmethod': {'show': True, 'type': 'str'},
	'country_id': {'show': False, 'type': 'bool'},
	'countryid': {'show': True, 'type': 'str'},
	'ip_range': {'show': False, 'type': 'bool'},
	'iprange': {'show': True, 'type': 'str'},
	'serial_number': {'show': False, 'type': 'bool'},
	'customer_name': {'show': True, 'type': 'str'},
	'csv_file': {'show': True, 'type': 'str'},
	'tr069': {'show': True, 'type': 'bool'},
	'home_controller': {'show': True, 'type': 'bool'},
	'rd_party_controller': {'show': True, 'type': 'bool'},
	'tr069_acs': {'show': False, 'type': 'bool'},
	'acs_url': {'show': True, 'type': 'str'},
	'acs_username': {'show': True, 'type': 'str'},
	'acs_password': {'show': True, 'type': 'str'},
	'home_controller_usp': {'show': False, 'type': 'bool'},
	'tenant_ref': {'show': True, 'type': 'str'},
	'rd_party_usp': {'show': False, 'type': 'bool'},
	'usp_addr': {'show': True, 'type': 'str'},
	'usp_port': {'show': True, 'type': 'str'},
	'auto_upgrade': {'show': True, 'type': 'bool'},
	'ota_yes_1': {'show': False, 'type': 'bool'},
	'separate_license': {'show': True, 'type': 'bool'},
	'ota_yes_2': {'show': False, 'type': 'bool'},
	'used_as_extender': {'show': True, 'type': 'bool'},
	'root_beacon_flags': {'show': False, 'type': 'str'},
    'root_beacon_model': {'show': True, 'type': 'str'},
	'additional': {'show': True, 'type': 'str'},
    'creator': {'show': True, 'type': 'str'},
    'createon': {'show': True, 'type': 'str'},
    'modifier': {'show': True, 'type': 'str'},
    'modifiedon': {'show': True, 'type': 'str'},
}

def fetch_boengrule(request):
    try:
        sType = request.GET['type']
        b_id = request.GET['B_ID']
    except:
        return HttpResponse('Invalid Parameters', content_type='application/json')

    dResult = {}
    dResult['code'] = 20000
    dResult['data'] = {}
    dResult['data']['items'] = []

    #SQLConn = analyzer_db()
    # 0 select menu
    if sType == '0':
        #SQLCur = SQLConn.dcur
        sql = 'select {fields} from {tbl} where `B_ID` = "{b_id}" '.format(
            fields=','.join(['`{field}`'.format(field=f) for f in boengrule_fields.keys()]),
            tbl=tbl,
            b_id=b_id
        )
        logger.debug(f'fetch_boengrule, sql = {sql}')
        #SQLCur.execute(sql)
        #SQLResult = SQLCur.fetchall()
        #SQLConn.close()
        df = db.read_query(sql)
        for i_index in df.index:
            dItem = {}
            for field in boengrule_fields.keys():
                if type(df.at[i_index, field]) == pd.Timestamp:
                    dItem[field] = str(df.at[i_index, field])
                elif type(df.at[i_index, field]) == np.int64:
                    dItem[field] = int(df.at[i_index, field])
                else:
                    dItem[field] = df.at[i_index, field]
            dResult['data']['items'].append(dItem)
        #logger.debug(dResult)
    return HttpResponse(simplejson.dumps(dResult), content_type='application/json')

def new_boeng_info(request):
    try:
        sMail = request.GET['mail']
        sLevel = request.GET['level']
    except:
        return HttpResponse('Invalid Parameters', content_type='application/json')

    dResult = {}
    dResult['code'] = 20000
    dResult['data'] = {}
    dResult['data']['items'] = []

    if sLevel != 'undefined':
        cmd = 'SELECT {fields} FROM {tbl} ORDER BY `Customer`'.format(
            fields=','.join(
                ['`{field}`'.format(field=f) for f in boengrule_fields.keys()]
            ),
            tbl=tbl
        )
        # if sLevel < '5':
        #     sRule = """WHERE Creator='%s' or Modifier='%s' """ % (sMail, sMail)
        # else:
        #     sRule = ''


        logger.debug(f'new_boeng_info, sql = {cmd}')

        df = db.read_table(tbl)
        df = df.replace({np.nan: None}).fillna('')
        for i_index in df.index:
            dItem = {}
            for field in boengrule_fields.keys():
                if field in ['root_beacon_model']:
                    beacons = df.at[i_index, field].split('###')
                    for i in range(len(beacons)):
                        dItem['root_beacon_extender_{}'.format(i+1)] = beacons[i]
                else:
                    match boengrule_fields[field]['type']:
                        case 'str':
                            dItem[field] = str(df.at[i_index, field])
                        case 'bool':
                            if field in ['separate_license', 'used_as_extender']:
                                dItem[field] = "Yes" if df.at[i_index, field] else "No"
                            else:
                                dItem[field] = "True" if df.at[i_index, field] else "False"
            
            dResult['data']['items'].append(dItem)
    #logger.debug(dResult)

    return HttpResponse(simplejson.dumps(dResult), content_type='application/json')
    pass

def handle_boeng_rule_edit(tbl, data):
    generated_str = u.generate_update_sql(boengrule_fields, data, ['creator', 'createon'])

    sql = 'update {tbl} set {fields} where `B_ID` = "{B_ID}"'.format(
        tbl=tbl,
        fields=generated_str,
        B_ID=data['B_ID']
    )
    logger.debug(f'handle_boeng_rule_edit, sql = {sql}')
    db.execute(sql)

    pass

def handle_boeng_rule_delete(tbl, llist):
    sql = 'delete from {tbl} where `B_ID` in ({B_LIST})'.format(
        tbl=tbl,
        B_LIST=u.generate_delete_sql(llist)
    )
    logger.debug(f'handle_boeng_rule_delete, sql = {sql}')
    db.execute(sql)

    pass

def handle_boeng_rule_add(tbl, data):
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
    l_data['B_ID'] = u.strNum(u.gen_tbl_index(tbl, 'B_ID', db), 'B', 10)

    generated_str = u.generate_insert_sql(boengrule_fields, l_data, skip=['modifier', 'modifiedon'])

    sql = "insert into {tbl} ({fields}) values ({values})".format(
            tbl=tbl,
            fields=generated_str[0],
            values=generated_str[1]
        )
    logger.debug(f'handle_boeng_rule_add: sql = {sql}')
    db.execute(sql)
    rt =  'Add successful, back and refresh page to show it'
    # else:
    #     rt = "The customer has already been added, unabled to be added again!"

    return rt
    pass

def new_boeng_edit(request):
    logger.debug('new_boeng_edit, request.body:', request.body.decode('utf-8'))
    dResult = {}
    dResult['code'] = 20000
    dResult['data'] = {}
    dResult['data']['status'] = []

    try:
        sType = ''
        sLastupdate = datetime.today().strftime('%Y-%m-%d')
        if request.method == 'POST':
            data = json.loads(request.body)
            if data:
                sType = data.get('type')
                sMail = data.get('mail')

                if sType[:1] == '1' or sType == '2':
                    l_data = {}
                    for field in [f for f in boengrule_fields.keys() if f != 'B_ID']:
                        l_data[field] = data.get(field)
                if sType == '2':
                    l_data['B_ID'] = data.get('B_ID')
                elif sType == '3':
                    l_delete_list = data.get('deletelist')

    except Exception as e:
        logger.debug(f'new_boeng_edit, Invalid Parameters: {e}')
        dResult['data']['status'] = "Invalid Parameters"
        return HttpResponse(simplejson.dumps(dResult), content_type='application/json')

    # 1x add
    if sType[:1] == '1':
        rt = handle_boeng_rule_add(tbl, l_data)
        dResult['data']['status'] = rt
            
    # 2 edit
    elif sType == '2':
        handle_boeng_rule_edit(tbl, l_data)
        dResult['data']['status'] = "Edit successful"
        pass

    # 3 delete
    elif sType == '3':
        handle_boeng_rule_delete(tbl, l_delete_list)
        pass
        dResult['data']['status'] = "Delete successful"


    return HttpResponse(simplejson.dumps(dResult), content_type='application/json')


def nwcc_list(request):
    logger.debug('nwcc_list')
    cus = dc('customerdb')
    nwcc_fields = [
        'Customer',
        'OPID',
        'Platform',
        'TenantID'
    ]
    df = cus.read_query(
        'select {fields} from `cdb_issues_saas`'.format(
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

def csv_upload(request):
    res = {}
    res['code'] = 20000
    res['data'] = {}
    logger.debug('csv_upload, start: {}, {}'.format(request.method, request.FILES.get('file')))
    if request.method == 'POST' and request.FILES.get('file'):
        upload_file = request.FILES['file']
        save_path = os.path.join(rs.UPLOAD_ROOT, upload_file.name)
        logger.debug(f'csv_upload, save_path = {save_path}')
        with open(save_path, 'wb+') as destination:
            for chunk in upload_file.chunks():
                destination.write(chunk)

    res['data']['status'] = 'File uploaded OK'
    logger.debug(f'csv_upload, end: {res}')
    return HttpResponse(simplejson.dumps(res), content_type='application/json')
    pass

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

def fetch_customer(request):
    res = {
        'code': 20000,
        'data': {
            'items': [],
        },
    }
    cus = dc('customerdb')
    sql = "SELECT `Summary` FROM `jira_issues_cust` ORDER BY `Summary`"
    logger.debug('fetch_customer', f'{sql}')
    df = cus.read_query(sql)
    l_customers = []
    for i_index in df.index:
        l_customers.append(df.at[i_index, 'Summary'])

    local_sql = 'SELECT `Customer` FROM `tbl_local_customers` ORDER BY `Customer`'
    logger.debug('fetch_customer', f'{local_sql}')
    local_df = db.read_query(local_sql)
    for i_index in local_df.index:
        l_customer = local_df.at[i_index, 'Customer']
        if l_customer not in l_customers:
            l_customers.append(l_customer)
    
    for cus in l_customers:
            res['data']['items'].append(
                {
                    'Customer': cus
                }
            )
    return HttpResponse(simplejson.dumps(res), content_type='application/json')

tbl_local_customers_field = [
    'Customer', 'Description', 'Source', 'AddedBy', 'AddedOn'
]

def handle_new_customer_add_jira(data, uname):
    logger.debug(f'handle_new_customer_add: {data.__str__()}')
    customer = data["Customer"]
    desc = data["Description"]
    #mail = data["AddedBy"]
    logger.debug(f'handle_new_customer_add, {customer}')
    jira = Jira()
    param = {
        "fields": {
            "project": {"key": "BBDCUST"},
            "summary": f"{customer}",
            "description": f"{desc}",
            "issuetype": {"id": "15401"},
            "reporter": {"name": f"{uname}"}
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
    logger.debug('handle_new_customer_add ...', data)
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
    logger.debug('handle_new_customer_add', f'{sql}')
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
