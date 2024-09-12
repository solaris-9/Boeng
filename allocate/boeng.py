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

import allocate.utils as u
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename='C:/reqLog/boengLog.txt', level=logging.DEBUG)

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

    SQLConn = analyzer_db()
    # 0 select menu
    if sType == '0':
        SQLCur = SQLConn.dcur
        sql = 'select {fields} from tblBoengRule where `B_ID` = "{b_id}" '.format(
            fields=','.join(['`{field}`'.format(field=f) for f in boengrule_fields.keys()]),
            b_id=b_id
        )
        logger.debug(sql)
        SQLCur.execute(sql)
        SQLResult = SQLCur.fetchall()
        SQLConn.close()
        for row in SQLResult:
            dItem = {}
            for field in boengrule_fields.keys():
                if type(row[field]) == datetime:
                    dItem[field] = row[field].__str__()
                else:
                    dItem[field] = row[field]
            dResult['data']['items'].append(dItem)
    return HttpResponse(simplejson.dumps(dResult), content_type='application/json')

def new_boeng_info(request):
        # ud = request.get_full_path()
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
        cmd = 'SELECT {fields} FROM tblBoengRule ORDER BY `Customer`'.format(
            fields=','.join(
                ['`{field}`'.format(field=f) for f in boengrule_fields.keys()]
            )
        )
        # if sLevel < '5':
        #     sRule = """WHERE Creator='%s' or Modifier='%s' """ % (sMail, sMail)
        # else:
        #     sRule = ''
        SQLConn = analyzer_db()
        logger.debug('new_boeng_info, sql = {}'.format(cmd))
        SQLConn.dcur.execute(cmd)
        SQLResult = SQLConn.dcur.fetchall()
        SQLConn.close()

        for row in SQLResult:
            dItem = {}
            for field in boengrule_fields.keys():
                if field in ['root_beacon_model']:
                    beacons = row[field].split('###')
                    for i in range(len(beacons)):
                        dItem['root_beacon_extender_{}'.format(i+1)] = beacons[i]
                else:
                    match boengrule_fields[field]['type']:
                        case 'str':
                            if type(row[field]) == str:
                                dItem[field] = row[field]
                            else:
                                dItem[field] = row[field].__str__()
                        case 'bool':
                            if field in ['separate_license', 'used_as_extender']:
                                dItem[field] = "Yes" if row[field] else "No"
                            else:
                                dItem[field] = "True" if row[field] else "False"
                    
                    #dItem[field] = row[field]
            
            dResult['data']['items'].append(dItem)
    logger.debug(dResult)

    return HttpResponse(simplejson.dumps(dResult), content_type='application/json')
    pass

def handle_boeng_rule_edit(tbl, data):
    conn = analyzer_db()

    generated_str = u.generate_update_sql(boengrule_fields, data, ['creator', 'createon'])

    sql = 'update {tbl} set {fields} where `B_ID` = "{B_ID}"'.format(
        tbl=tbl,
        fields=generated_str,
        B_ID=data['B_ID']
    )
    logger.debug('handle_boeng_rule_edit, sql = {sql}'.format(sql=sql))
    conn.dcur.execute(sql)
    conn.commit()
    conn.close()

    pass

def handle_boeng_rule_delete(tbl, llist):
    conn = analyzer_db()

    sql = 'delete from {tbl} where `B_ID` in ({B_LIST})'.format(
        tbl=tbl,
        B_LIST=u.generate_delete_sql(llist)
    )
    logger.debug('handle_boeng_rule_delete, sql = {sql}'.format(sql=sql))
    conn.dcur.execute(sql)
    conn.commit()
    conn.close()

    pass

def handle_boeng_rule_add(tbl, data):
    l_data = data
    conn = analyzer_db()
    tbl = 'tblBoengRule'
    # check if exists
    sql = "select count(Customer) as count from {} where customer='{}'".format(
        tbl, 
        l_data['Customer']
    )
    conn.dcur.execute(sql)
    res = conn.dcur.fetchall()

    # to add
    if res[0]['count'] == 0 or l_data['Customer'] == '':
        l_data['B_ID'] = u.strNum(u.tbl_index(tbl, 'B_ID', conn), 'B', 10)

        generated_str = u.generate_insert_sql(boengrule_fields, l_data, ['modifier', 'modifiedon'])

        sql = """insert into {tbl} (
                {fields}
            ) values (
                {values}
            )""".format(
                tbl=tbl,
                fields=generated_str[0],
                values=generated_str[1]
            )
        logger.debug('handle_boeng_rule_add: sql = {}\n'.format(sql))
        conn.dcur.execute(sql)
        rt =  'Add successful, back and refresh page to show it'
    else:
        rt = "The customer is already added, don't create again."


    conn.commit()
    conn.close()
    return rt
    pass

def new_boeng_edit(request):
    logger.debug('request.body:', request.body.decode('utf-8'))
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
        logger.debug('Invalid Parameters: {}'.format(e))
        dResult['data']['status'] = "Invalid Parameters"
        return HttpResponse(simplejson.dumps(dResult), content_type='application/json')

    # 1x add
    if sType[:1] == '1':
        rt = handle_boeng_rule_add('tblBoengRule', l_data)
        dResult['data']['status'] = "Edit successful"
            
    # 2 edit
    elif sType == '2':
        handle_boeng_rule_edit('tblBoengRule', l_data)
        dResult['data']['status'] = "Edit successful"
        pass

    # 3 delete
    elif sType == '3':
        handle_boeng_rule_delete('tblBoengRule', l_delete_list)
        pass
        dResult['data']['status'] = "Delete successful"


    return HttpResponse(simplejson.dumps(dResult), content_type='application/json')
