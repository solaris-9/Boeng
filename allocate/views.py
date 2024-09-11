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

File_address = r'C:/reqLog/printlog1.txt'
fa = open(File_address,'a')


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


def history(sID,sYID,sMail):
    pass


def customerlist(request):
    # ud = request.get_full_path()
    # print(ud, file=fa, flush=True )
    try:
        sType = request.GET['type']
    except:
        return HttpResponse('Invalid Parameters', content_type='application/json')

    dResult = {}
    dResult['code'] = 20000
    dResult['data'] = {}
    dResult['data']['items'] = []

    SQLConn = pymysql.connect(host=settings.BC_DB['host'],
                              port=settings.BC_DB['port'],
                              user=settings.BC_DB['username'],
                              password=settings.BC_DB['password'],
                              database=settings.BC_DB['name'],
                              charset=settings.BC_DB['charset'],
                              autocommit=True
                              )
    # 0 select menu
    if sType == '0':
        SQLCur = SQLConn.cursor()
        sql = "SELECT filelocat,customer FROM tblpublic"
        SQLCur.execute(sql)
        SQLResult = SQLCur.fetchall()
        SQLConn.close()
        for row in SQLResult:
            dItem = {}
            dItem['filelocat'] = row[0]
            dItem['customer'] = row[1]
            dResult['data']['items'].append(dItem)
    return HttpResponse(simplejson.dumps(dResult), content_type='application/json')


def getCustomerList(SQLConn,SQLCur):
    dResult = {}
    dResult['code'] = 20000
    dResult['data'] = {}
    dResult['data']['items'] = []

    sql="SELECT customer,status FROM tblrequest WHERE status = 'Queried' ORDER BY customer"
    SQLCur.execute(sql)
    SQLResult = SQLCur.fetchall()
    SQLConn.close()
    for row in SQLResult:
        dItem = {}
        dItem['Customer'] = row[0]
        dResult['data']['items'].append(dItem)
    return dResult
def customerid(request):
    # ud = request.get_full_path()
    # print(ud, file=fa,flush=True )
    try:
        sType = request.GET['type']
        if sType == '4':
            sCustomerid = request.GET['customerid']
            lCustomerid = sCustomerid.split(',')
    except:
        return HttpResponse('Invalid Parameters', content_type='application/json')

    dResult = {}
    dResult['code'] = 20000
    dResult['data'] = {}
    dResult['data']['items'] = []

    SQLConn = analyzer_db()
    if sType == '3':
        cmd = """
        SELECT customer_name,customer_id 
        FROM customer_id_map 
         %s
        ORDER BY customer_name"""
        # sRule = "WHERE customer_id IN %s" % List2String(lCustomerid)
        sRule = ''
        SQLConn.cur.execute(cmd % sRule)
        SQLResult = SQLConn.cur.fetchall()
        SQLConn.close()

        for row in SQLResult:
            dItem = {}
            dItem['Namesc'] = row[0]
            dItem['Customerid'] = row[1]
            dResult['data']['items'].append(dItem)
    if sType == '4':
        cmd = """
        SELECT customer_name,customer_id 
        FROM customer_id_map 
         %s
        ORDER BY customer_name"""
        sRule = "WHERE customer_id IN %s" % List2String(lCustomerid)
        SQLConn.cur.execute(cmd % sRule)
        SQLResult = SQLConn.cur.fetchall()
        SQLConn.close()
        for row in SQLResult:
            dItem = {}
            dItem['Customerid'] = row[0] + '  (' + row[1] + ')  '

            dResult['data']['items'].append(dItem)
    return HttpResponse(simplejson.dumps(dResult), content_type='application/json')


def customer_list(request):
    try:
        sType = request.GET['type']
        if sType == '4':
            sCustomer = request.GET['customer']
            lCustomer = '%' + sCustomer + '%'
    except:
        return HttpResponse('Invalid Parameters', content_type='application/json')

    dResult = {}
    dResult['code'] = 20000
    dResult['data'] = {}
    dResult['data']['items'] = []
    SQLBConn = pymysql.connect(host=settings.BBD_DB['host'],
                               port=settings.BBD_DB['port'],
                               user=settings.BBD_DB['username'],
                               password=settings.BBD_DB['password'],
                               database=settings.BBD_DB['name'],
                               charset=settings.BBD_DB['charset']
                               )
    SQLBCur = SQLBConn.cursor()

    # 0 select menu
    if sType == '0':

        sql = "SELECT Summary FROM jira_issues_cust ORDER BY Summary"
        SQLBCur.execute(sql)
        SQLBResult = SQLBCur.fetchall()
        SQLBConn.close()
        for row in SQLBResult:
            dItem = {}
            dItem['Customer'] = row[0]
            dResult['data']['items'].append(dItem)
    if sType == '4':

        sql = "SELECT Summary FROM jira_issues_cust WHERE Summary NOT LIKE '%s' ORDER BY Summary" % lCustomer
        SQLBCur.execute(sql)
        SQLBResult = SQLBCur.fetchall()
        SQLBConn.close()
        for row in SQLBResult:
            dItem = {}
            dItem['Summary'] = row[0]
            dResult['data']['items'].append(dItem)
    return HttpResponse(simplejson.dumps(dResult), content_type='application/json')


def devicelist(request):
    try:
        sType = request.GET['type']
    except:
        return HttpResponse('Invalid Parameters', content_type='application/json')

    dResult = {}
    dResult['code'] = 20000
    dResult['data'] = {}
    dResult['data']['items'] = []

    SQLConn = pymysql.connect(host=settings.BC_DB['host'],
                              port=settings.BC_DB['port'],
                              user=settings.BC_DB['username'],
                              password=settings.BC_DB['password'],
                              database=settings.BC_DB['name'],
                              charset=settings.BC_DB['charset'],
                              autocommit=True
                              )

    SQLCur = SQLConn.cursor()
    sql = """
        SELECT Summary FROM jira_issues_product 
        WHERE Left(Summary,1) = 'G' OR Left(Summary,1) = 'X' OR Left(Summary,3) = 'HA-'
        OR Left(Summary,6) = 'Beacon' 
        ORDER BY Summary
        """
    SQLCur.execute(sql)
    SQLResult = SQLCur.fetchall()
    SQLConn.close()
    for row in SQLResult:
        dItem = {}
        dItem['Product'] = row[0]

        dResult['data']['items'].append(dItem)
    return HttpResponse(simplejson.dumps(dResult), content_type='application/json')


def customer_id(request):
    try:
        sCustomer = request.GET['customer']
        sRoles = request.GET['roles']

    except:
        return HttpResponse('Invalid Parameters', content_type='application/json')

    dResult = {}
    dResult['code'] = 20000
    dResult['data'] = {}
    dResult['data']['items'] = []
    lCustomer = sCustomer.split(',')

    cmd = """
        SELECT
            customer_id,customer_name,data_source        
        FROM 
           customer_id_map        
        ORDER BY customer_name
    """

    SQLConn = analyzer_db()
    SQLConn.cur.execute(cmd)
    SQLResult = SQLConn.cur.fetchall()
    SQLConn.close()

    for row in SQLResult:
        if sRoles == 'Administrator':
            product = row[2]
        else:
            product = ''
        dItem = {}
        dItem['customer_id'] = row[0]
        dItem['customer_name'] = row[1]
        dItem['data_source'] = row[2]
        dResult['data']['items'].append(dItem)

    return HttpResponse(simplejson.dumps(dResult), content_type='application/json')


def customer_id_edit(request):
    ud = request.get_full_path()
    print(ud, file=fa, flush=True)
    dResult = {}
    dResult['code'] = 20000
    dResult['data'] = {}
    dResult['data']['status'] = []
    dResult['data']['items'] = []
    try:
        sType = request.GET['type']
        sCustomerid = request.GET['customerid']
        sCustomername = request.GET['customername']
        sLastupdate = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        print(sType,sCustomername,sCustomerid,file=fa, flush=True)
    except:
        dResult['data']['status'] = "Invalid Parameters"
        return HttpResponse(simplejson.dumps(dResult), content_type='application/json')



    SQLConn = analyzer_db()
    # 1 add
    if sType == '1':
        sqlt = """insert into customer_id_map (customer_id,customer_name,date_entered ) 
            values(%s,%s,%s) ON DUPLICATE KEY UPDATE customer_id=customer_id"""
        values = (sCustomerid, sCustomername, sLastupdate)
        SQLConn.cur.execute(sqlt, values)
        SQLConn.conn.commit()
        SQLConn.close()
        dItem = {}
        dItem['Result'] = "Add Successful"
        dResult['data']['items'].append(dItem)

    # 2 edit
    if sType == '2':
        sql = """update customer_id_map set customer_name = '%s',date_entered ='%s'
        where customer_id =  '%s'""" % (sCustomername, sLastupdate, sCustomerid)
        print(sql, file=fa, flush=True)
        SQLConn.cur.execute(sql)
        SQLConn.conn.commit()
        SQLConn.close()
        dItem = {}
        dItem['Result'] = "Edit Successful"
        dResult['data']['items'].append(dItem)

    return HttpResponse(simplejson.dumps(dResult), content_type='application/json')


def request_info(request):
    # ud = request.get_full_path()
    # print(ud, file=fa, flush=True)
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
        cmd = """
            SELECT
                customer,customerid,country,licensetype,plateform,
                alivedate,region,legal,multi_region,multi_legal,
                tenant_platform,traildate,trailnumber,trailplan,
                devicenumber,devicenumber3,devicenumber6,
                volume,area,FCC,SLAlevel,HDM,HDMpo,fingerprinting,
                response_person,WBSnumber,device,OPID,countryid,Container,
                application,SWupdate,beaconexp,rootbeacon,rootbeacon2,
                BoENG,BoENG_ACS,ACS_URL,ACS_username,ACS_key,
                additional,Creator,RecordTime,Modifier,REID,ID,customersc
            FROM
                tblrequest a
            JOIN
                tbldevice b
            WHERE  
              a.REID = Right(b.ID,6)    
                 %s
            ORDER BY customer 
        """
        if sLevel < '5':
            sRule = """WHERE Creator='%s' or Modifier='%s' """ % (sMail, sMail)
        else:
            sRule = ''
        SQLConn = analyzer_db()
        # print(cmd % sRule, file=fa,flush=True )
        SQLConn.cur.execute(cmd % sRule)
        SQLResult = SQLConn.cur.fetchall()
        SQLConn.close()

        for row in SQLResult:
            dItem = {}
            dItem['customer'] = row[0]
            dItem['customerid'] = row[1]
            dItem['country'] = row[2]
            dItem['licensetype'] = row[3]
            dItem['plateform'] = row[4]
            dItem['alivedate'] = row[5]
            dItem['region'] = row[6]
            dItem['legal'] = row[7]
            dItem['multi_region'] = row[8]
            dItem['multi_legal'] = row[9]
            dItem['tenant_platform'] = row[10]
            dItem['traildate'] = row[11]
            dItem['trailnumber'] = row[12]
            dItem['trailplan'] = row[13]
            dItem['devicenumber'] = row[14]
            dItem['devicenumber3'] = row[15]
            dItem['devicenumber6'] = row[16]
            dItem['volume'] = row[17]
            dItem['area'] = row[18]
            dItem['FCC'] = row[19]
            dItem['SLAlevel'] = row[20]
            dItem['HDM'] = row[21]
            dItem['HDMpo'] = row[22]
            dItem['fingerprinting'] = row[23]
            dItem['response_person'] = row[24]
            dItem['WBSnumber'] = row[25]
            dItem['device'] = row[26]
            dItem['OPID'] = row[27]
            dItem['countryid'] = row[28]
            dItem['container'] = row[29]
            dItem['application'] = row[30]
            dItem['SWupdate'] = row[31]
            dItem['beaconexp'] = row[32]
            dItem['rootbeacon'] = row[33]
            dItem['rootbeacon2'] = row[34]
            dItem['BoENG'] = row[35]
            dItem['BoENG_ACS'] = row[36]
            dItem['ACS_URL'] = row[37]
            dItem['ACS_username'] = row[38]
            dItem['ACS_key'] = row[39]
            dItem['additional'] = row[40]
            dItem['Creator'] = row[41]
            dItem['RecordTime'] = str(row[42])[:10]
            dItem['Modifier'] = row[43]
            dItem['REID'] = row[44]
            dItem['ID'] = row[45]
            dItem['customersc'] = row[46]
            dResult['data']['items'].append(dItem)

    return HttpResponse(simplejson.dumps(dResult), content_type='application/json')


def request_edit(request):
    print('request.body:', request.body.decode('utf-8'),file=fa,flush=True )
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
                    sCustomer = data.get('customer')
                    sCustomersc = data.get('customersc')
                    sCustomerid = data.get('customerid')
                    sCountry = data.get('country')
                    sLicensetype = data.get('licensetype')
                    sPlateform = data.get('plateform')
                    sAlivedate = data.get('alivedate')
                    sRegion = data.get('region')
                    sLegal = data.get('legal')
                    sMulti_region = data.get('multi_region')
                    sMulti_legal = data.get('multi_legal')
                    sTenant_platform = data.get('tenant_platform')
                    sTraildate = data.get('traildate')
                    sTrailnumber = data.get('trailnumber')
                    sTrailplan = data.get('trailplan')
                    sDevicenumber = data.get('devicenumber')
                    sDevicenumber3 = data.get('devicenumber3')
                    sDevicenumber6 = data.get('devicenumber6')
                    sVolume = data.get('volume')
                    sArea = data.get('area')
                    sFCC = data.get('FCC')
                    sSLAlevel = data.get('SLAlevel')
                    sHDM = data.get('HDM')
                    sHDMpo = data.get('HDMpo')
                    sFingerprinting = data.get('fingerprinting')
                    sResponse_person = data.get('response_person')
                    sWBSnumber = data.get('WBSnumber')
                    sDevice = data.get('device')
                    sOPID = data.get('OPID')
                    sCountryid = data.get('countryid')
                    sContainer = data.get('container')
                    sApplication = data.get('application')
                    sSWupdate = data.get('SWupdate')
                    sBeaconexp = data.get('beaconexp')
                    sRootbeacon = data.get('rootbeacon')
                    sRootbeacon2 = data.get('rootbeacon2')
                    sBoENG = data.get('BoENG')
                    sBoENG_ACS = data.get('BoENG_ACS')
                    sACS_URL = data.get('ACS_URL')
                    sACS_username= data.get('ACS_username')
                    sACS_key = data.get('ACS_key')
                    sAdditional = data.get('additional')
                if sType == '11' or sType == '12' or sType == '13':
                    sDevice1 = data.get('device1')
                    sOPID1 = data.get('OPID1')
                    sCountryid1 = data.get('countryid1')
                    sContainer1 = data.get('container1')
                    sApplication1 = data.get('application1')
                    sSWupdate1 = data.get('SWupdate1')
                    sBeaconexp1 = data.get('beaconexp1')
                    sRootbeacon1 = data.get('rootbeacon1')
                    sRootbeacon21 = data.get('rootbeacon21')
                    sBoENG1 = data.get('BoENG1')
                    sBoENG_ACS1 = data.get('BoENG_ACS1')
                    sACS_URL1 = data.get('ACS_URL1')
                    sACS_username1 = data.get('ACS_username1')
                    sACS_key1 = data.get('ACS_key1')
                if sType == '12' or sType == '13':
                    sDevice2 = data.get('device2')
                    sOPID2 = data.get('OPID2')
                    sCountryid2 = data.get('countryid2')
                    sContainer2 = data.get('container2')
                    sApplication2 = data.get('application2')
                    sSWupdate2 = data.get('SWupdate2')
                    sBeaconexp2 = data.get('beaconexp2')
                    sRootbeacon12 = data.get('rootbeacon12')
                    sRootbeacon22 = data.get('rootbeacon22')
                    sBoENG2 = data.get('BoENG2')
                    sBoENG_ACS2 = data.get('BoENG_ACS2')
                    sACS_URL2 = data.get('ACS_URL2')
                    sACS_username2 = data.get('ACS_username2')
                    sACS_key2 = data.get('ACS_key2')
                if sType == '13':
                    sDevice3 = data.get('device3')
                    sOPID3 = data.get('OPID3')
                    sCountryid3 = data.get('countryid3')
                    sContainer3 = data.get('container3')
                    sApplication3 = data.get('application3')
                    sSWupdate3 = data.get('SWupdate3')
                    sBeaconexp3 = data.get('beaconexp3')
                    sRootbeacon3 = data.get('rootbeacon3')
                    sRootbeacon23 = data.get('rootbeacon23')
                    sBoENG3 = data.get('BoENG3')
                    sBoENG_ACS3 = data.get('BoENG_ACS3')
                    sACS_URL3 = data.get('ACS_URL3')
                    sACS_username3 = data.get('ACS_username3')
                    sACS_key3 = data.get('ACS_key3')
                if sType == '2':
                    sID = data.get('ID')
                elif sType == '3':
                    sDeletelist = data.get('deletelist')

    except:
        dResult['data']['status'] = "Invalid Parameters"
        return HttpResponse(simplejson.dumps(dResult), content_type='application/json')

    # 1x add
    if sType[:1] == '1':
        SQLConn = analyzer_db()
        SQL = "select count(Customer) as num from tblrequest where customer='%s'" % sCustomer
        SQLConn.cur.execute(SQL)
        SQLResult = SQLConn.cur.fetchall()
        count = SQLResult[0][0]

        if count == 0 or sCustomer == '':
            tblname = 'tblrequest'
            ID = 'REID'
            strN = tbl_index(tblname, ID, SQLConn)
            sID = strNum(strN, 'B', 5)
            sqlt1 = """insert into tblrequest (REID,customer,customersc,customerid,country,licensetype,plateform,alivedate,region,
            legal,multi_region,multi_legal,tenant_platform,traildate,trailnumber,devicenumber,devicenumber3,
            devicenumber6,volume,area,FCC,SLAlevel,HDM,HDMpo,fingerprinting,response_person,WBSnumber,additional) 
            values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            values1 = (
            sID,sCustomer,sCustomersc,sCustomerid,sCountry,sLicensetype,sPlateform,sAlivedate,sRegion,sLegal,sMulti_region,sMulti_legal,sTenant_platform,sTraildate,sTrailnumber,sDevicenumber,sDevicenumber3,sDevicenumber6,sVolume,sArea,sFCC,sSLAlevel,sHDM,sHDMpo,sFingerprinting,sResponse_person,sWBSnumber, sAdditional)
            print(values1, file=fa, flush=True)
            SQLConn.cur.execute(sqlt1, values1)
            YID = '1' + sID
            sqlt2 = """insert into tbldevice (ID,device,OPID,countryid,container,application,SWupdate,beaconexp,
                                        rootbeacon,rootbeacon2,BoENG,BoENG_ACS,ACS_URL,ACS_username,ACS_key,
                                        Creator,RecordTime,Modifier) 
                                        values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            values2 = (
                YID, sDevice, sOPID, sCountryid, sContainer, sApplication, sSWupdate, sBeaconexp, sRootbeacon,
                sRootbeacon2, sBoENG, sBoENG_ACS, sACS_URL, sACS_username, sACS_key, sMail,
                sLastupdate, sMail)
            print(values2, file=fa, flush=True)
            SQLConn.cur.execute(sqlt2, values2)
            if sType == '11' or sType == '12' or sType == '13':
                YID = '2' + sID
                sqlt2 = """insert into tbldevice (ID,device,OPID,countryid,container,application,SWupdate,beaconexp,
                            rootbeacon,rootbeacon2,BoENG,BoENG_ACS,ACS_URL,ACS_username,ACS_key,
                            Creator,RecordTime,Modifier) 
                            values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                values2 = (
                    YID, sDevice1, sOPID1, sCountryid1, sContainer1, sApplication1, sSWupdate1, sBeaconexp1, sRootbeacon1,
                    sRootbeacon21, sBoENG1, sBoENG_ACS1, sACS_URL1, sACS_username1, sACS_key1, sMail,
                    sLastupdate, sMail)
                print(values2, file=fa, flush=True)
                SQLConn.cur.execute(sqlt2, values2)
            if sType == '12' or sType == '13':
                YID = '3' + sID
                sqlt2 = """insert into tbldevice (ID,device,OPID,countryid,container,application,SWupdate,beaconexp,
                                            rootbeacon,rootbeacon2,BoENG,BoENG_ACS,ACS_URL,ACS_username,ACS_key,
                                            Creator,RecordTime,Modifier) 
                                            values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                values2 = (
                    YID, sDevice2, sOPID2, sCountryid2, sContainer2, sApplication2, sSWupdate2, sBeaconexp2, sRootbeacon12,
                    sRootbeacon22, sBoENG2, sBoENG_ACS2, sACS_URL2, sACS_username2, sACS_key2, sMail,
                    sLastupdate, sMail)
                print(values2, file=fa, flush=True)
                SQLConn.cur.execute(sqlt2, values2)
            if sType == '13':
                YID = '4' + sID
                sqlt2 = """insert into tbldevice (ID,device,OPID,countryid,container,application,SWupdate,beaconexp,
                                            rootbeacon,rootbeacon2,BoENG,BoENG_ACS,ACS_URL,ACS_username,ACS_key,
                                            Creator,RecordTime,Modifier) 
                                            values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                values2 = (
                    YID, sDevice3, sOPID3, sCountryid3, sContainer3, sApplication3, sSWupdate3, sBeaconexp3, sRootbeacon3,
                    sRootbeacon23, sBoENG3, sBoENG_ACS3, sACS_URL3, sACS_username3, sACS_key3, sMail,
                    sLastupdate, sMail)
                print(values2, file=fa, flush=True)
                SQLConn.cur.execute(sqlt2, values2)

            SQLConn.commit()
            SQLConn.close()
            dResult['data']['status'] = "Add successful, back and refresh page to show it"

        else:
            dResult['data']['status'] = "The customer is already added,don't create again."

            # 2 edit
    elif sType == '2':
        SQLConn = analyzer_db()
        sql = """
            UPDATE tblrequest set customer='%s',customersc='%s',customerid='%s',country='%s',licensetype='%s',plateform='%s',
            alivedate='%s',region='%s',legal='%s',multi_region='%s',multi_legal='%s',tenant_platform='%s',
            traildate='%s',trailnumber='%s',trailplan='%s',devicenumber='%s',devicenumber3='%s',devicenumber6='%s',
            volume='%s',area='%s',FCC='%s',SLAlevel='%s',HDM='%s',HDMpo='%s',fingerprinting='%s',response_person='%s',
            WBSnumber='%s',device='%s',OPID='%s',countryid='%s',container='%s',application='%s',SWupdate='%s',
            beaconexp='%s',rootbeacon='%s',rootbeacon2='%s',BoENG='%s',BoENG_ACS='%s',ACS_URL='%s',ACS_username='%s',
            ACS_key='%s',additional='%s',RecordTime='%s',Modifier='%s'
            WHERE REID = '%s'
            """ % (
        sCustomer,sCustomersc,sCustomerid,sCountry,sLicensetype,sPlateform,sAlivedate,sRegion,sLegal,sMulti_region,sMulti_legal,sTenant_platform,sTraildate,sTrailnumber,sTrailplan,sDevicenumber,sDevicenumber3,sDevicenumber6,sVolume,sArea,sFCC,sSLAlevel,sHDM,sHDMpo,sFingerprinting,sResponse_person,sWBSnumber,sDevice,sOPID,sCountryid,sContainer,sApplication,sSWupdate,sBeaconexp,sRootbeacon,sRootbeacon2,sBoENG,sBoENG_ACS,sACS_URL,sACS_username,sACS_key,sAdditional,sLastupdate,sMail,sID)
        # print (sql, file=fa,flush=True)
        SQLConn.cur.execute(sql)
        SQLConn.commit()
        SQLConn.close()
        dResult['data']['status'] = "Edit successful"

        # 3 delete
    elif sType == '3':
        lYID = sDeletelist.split(',')
        SQLConn = analyzer_db()
        sql = "DELETE FROM tbldevice WHERE ID IN %s" % List2String(lYID)
        print('delete ef =', sql, sMail, sLastupdate, file=fa, flush=True)
        SQLConn.cur.execute(sql)
        SQLConn.conn.commit()
        for td in lYID:
            sql = """
                       SELECT
                          count(REID) as num 
                       FROM 
                         tblrequest a
                       JOIN
                         tbldevice b
                       ON
                         a.REID = Right(b.ID,6)
                       WHERE  
                         a.REID = '%s'
                    """ % td[-6:]
            SQLConn.cur.execute(sql)
            SQLResult = SQLConn.cur.fetchall()
            count = SQLResult[0][0]
            # print('count=',str(count),sql,file=fa, flush=True )
            if count == 0:
                sqlt = "DELETE FROM tblrequest WHERE REID = '%s'" % td[-6:]
                print('delete rqt=', sqlt, sMail, sLastupdate, file=fa, flush=True)
                SQLConn.cur.execute(sqlt)
            SQLConn.conn.commit()
        SQLConn.conn.close()
        dResult['data']['status'] = "Delete successful"

    # 4 check
    elif sType == '4':
        SQLConn = analyzer_db()
        sql = "select count(customer) as num from tblrequest WHERE customer = '%s' " % sCustomer
        SQLConn.cur.execute(sql)
        SQLResult = SQLConn.cur.fetchall()
        count = SQLResult[0][0]
        if count > 0:
            dResult = {}
            dResult['status'] = "successful"
        else:
            dResult = {}
            dResult['status'] = "failure"
        SQLConn.close()

    return HttpResponse(simplejson.dumps(dResult), content_type='application/json')

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
}

def generate_long_sql(fields, data):
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
        print(sql, file=fa, flush=True)
        SQLCur.execute(sql)
        SQLResult = SQLCur.fetchall()
        SQLConn.close()
        for row in SQLResult:
            dItem = {}
            for field in boengrule_fields.keys():
                dItem[field] = row[field]
            dResult['data']['items'].append(dItem)
    return HttpResponse(simplejson.dumps(dResult), content_type='application/json')

def new_boeng_info(request):
        # ud = request.get_full_path()
    # print(ud, file=fa, flush=True)
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
        cmd = """
            SELECT
                {fields}
            FROM
                tblBoengRule 
            ORDER BY `Customer` 
        """.format(
            fields=','.join(['`{field}`'.format(field=f) for f in boengrule_fields.keys()])
        )
        # if sLevel < '5':
        #     sRule = """WHERE Creator='%s' or Modifier='%s' """ % (sMail, sMail)
        # else:
        #     sRule = ''
        SQLConn = analyzer_db()
        print('new_boeng_info, sql = {}'.format(cmd), file=fa,flush=True )
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
                    dItem[field] = row[field]
            
            dResult['data']['items'].append(dItem)

    return HttpResponse(simplejson.dumps(dResult), content_type='application/json')
    pass

def handle_boeng_rule_edit(tbl, data):
    conn = analyzer_db()

    sql = 'update {tbl} set {fields} where `B_ID` = "{B_ID}"'.format(
        tbl=tbl,
        fields=generate_update_sql(boengrule_fields, data),
        B_ID=data['B_ID']
    )
    print('handle_boeng_rule_edit, sql = {sql}'.format(sql=sql), file=fa, flush=True)
    conn.dcur.execute(sql)
    conn.commit()
    conn.close()

    pass

def handle_boeng_rule_delete(tbl, llist):
    conn = analyzer_db()

    sql = 'delete from {tbl} where `B_ID` in ({B_LIST})'.format(
        tbl=tbl,
        B_LIST=generate_delete_sql(llist)
    )
    print('handle_boeng_rule_delete, sql = {sql}'.format(sql=sql), file=fa, flush=True)
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
        l_data['B_ID'] = strNum(tbl_index(tbl, 'B_ID', conn), 'B', 10)

        sql = """insert into {tbl} (
                {fields}
            ) values (
                {values}
            )""".format(
                tbl=tbl,
                fields=generate_long_sql(boengrule_fields, l_data)[0],
                values=generate_long_sql(boengrule_fields, l_data)[1]
            )
        print('handle_boeng_rule_add: sql = {}\n'.format(sql), file=fa, flush=True)
        conn.dcur.execute(sql)
        rt =  'Add successful, back and refresh page to show it'
    else:
        rt = "The customer is already added, don't create again."


    conn.commit()
    conn.close()
    return rt
    pass

def new_boeng_edit(request):
    print('request.body:', request.body.decode('utf-8'),file=fa,flush=True )
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
        print('Invalid Parameters:', e, file=fa,flush=True )
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


def release_list(request):
    try:
        sType = request.GET['type']
    except:
        return HttpResponse('Invalid Parameters', content_type='application/json')
    dResult = {}
    dResult['code'] = 20000
    dResult['data'] = {}
    dResult['data']['items'] = []
    cmd = """
          SELECT 
            FixVersions 
          FROM 
            jira_issues_rcr 
          WHERE 
               Left(FixVersions,5) ='BBDR2' 
              OR Left(FixVersions,5) ='BBDR3' 
             
         ORDER BY FixVersions DESC
         """
    SQLBConn = pymysql.connect(host  = settings.BBD_DB['host'],
                            port     = settings.BBD_DB['port'],
                            user     = settings.BBD_DB['username'],
                            password = settings.BBD_DB['password'],
                            database = settings.BBD_DB['name'],
                            charset  = settings.BBD_DB['charset']
                        )
    SQLBCur = SQLBConn.cursor()
    SQLBCur.execute(cmd)                
    SQLBResult = SQLBCur.fetchall()
    SQLBConn.close()
    rellist =[]
    for row in SQLBResult:        
        relv = row[0].split(',')        
        for r in relv:
            rellist.append(r)
    relset = set(rellist)
    releaselist = sorted(list(relset))

    for rel in releaselist:        
        dItem = {}
        dItem['Release'] = rel
        dResult['data']['items'].append(dItem)
    return HttpResponse(simplejson.dumps(dResult), content_type='application/json')


def device_type(request):
    # print('request.body:', request.body.decode('utf-8'), file=fa, flush=True)
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
                # print('sType=', sMail, file=fa, flush=True)
    except:
        dResult['data']['status'] = "Invalid Parameters"
        return HttpResponse(simplejson.dumps(dResult), content_type='application/json')

    cmd = """
            SELECT
               DeviceName, MACNUM, Class,DHistory,Modifier,RecordTime,DeviceId
            FROM
              tbldevicetype
            """

    SQLConn = analyzer_db()
    SQLConn.cur.execute(cmd)
    SQLResult = SQLConn.cur.fetchall()
    SQLConn.close()

    for row in SQLResult:
        dItem = {}
        dItem['DeviceName'] = row[0]
        dItem['MACNUM'] = row[1]
        dItem['Class'] = row[2]
        dItem['DHistory'] = row[3]
        dItem['Modifier'] = row[4]
        dItem['RecordTime'] = str(row[5])
        dItem['DeviceId'] = row[6]
        dResult['data']['items'].append(dItem)
    return HttpResponse(simplejson.dumps(dResult), content_type='application/json')

def devicetype_edit(request):
    # print('request.body:', request.body.decode('utf-8'),file=fa,flush=True )

    dResult = {}
    dResult['code'] = 20000
    dResult['data'] = {}
    dResult['data']['status'] = []

    try:
        sType =''
        sLevel =''
        if request.method == 'POST':
            data = json.loads(request.body)
            if data:
                sType = data.get('type')
                if sType != '0' and sType != '4':
                    sGrade = data.get('grade')
                    sMail = data.get('mail')
                    sLevel = data.get('level')

                    if sType == '1' or sType == '2':
                        sDevicename = data.get('devicename')
                        sMACNUM = data.get('macnum')
                        sClass = data.get('class')
                        sDHistory = data.get('dhistory')
                        sRecordTime = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                    if sType == '2' :
                        sDeviceid = data.get('deviceid')
                    elif sType == '3':
                        sDeletelist = data.get('deletelist')
                elif sType == '4':
                    sDevicename = data.get('devicename')
    except:
        dResult['data']['status'] = "Invalid Parameters"
        return HttpResponse(simplejson.dumps(dResult), content_type='application/json')

    if sType == '0':
        cmd = """
                    SELECT
                       DeviceName
                    FROM
                      tbldevicetype
                    ORDER BY DeviceName
                    """
        SQLConn = analyzer_db()
        SQLConn.cur.execute(cmd)
        SQLResult = SQLConn.cur.fetchall()
        SQLConn.close()
        devicelist = []
        for row in SQLResult:
            devicelist.append(row[0])
        for dev in devicelist:
            dItem = {}
            dItem['devicename'] = dev
            dResult['data']['items'].append(dItem)

    elif sType == '4':
        SQLConn = analyzer_db()
        sql = "select count(DeviceName) as num from tbldevicetype WHERE DeviceName = '%s' " % sDevicename
        SQLConn.cur.execute(sql)
        SQLResult = SQLConn.cur.fetchall()
        count = SQLResult[0][0]
        if count > 0:
            dResult['data']['status'] = "successful"
        else:
            dResult['data']['status'] = "not exist"
        SQLConn.close()
    else:
        if sLevel > '4':
            # 1 add
            if sType == '1':
                SQLConn = analyzer_db()
                tblname = 'tbldevicetype'
                ID = 'DeviceId'
                strN = tbl_index(tblname,ID,SQLConn)
                sID = strNum(strN,'D',5)
                sqlt = """insert into tbldevicetype (DeviceId, DeviceName, MACNUM, Class,DHistory,Modifier, RecordTime) 
                        values(%s,%s,%s,%s,%s,%s,%s)"""
                values = (sID, sDevicename, sMACNUM, sClass, sDHistory, sMail, sRecordTime)
                SQLConn.cur.execute(sqlt, values)
                SQLConn.commit()
                SQLConn.close()
                dResult['data']['status'] = "successful"

                # 2 edit
            elif sType == '2':
                SQLConn = analyzer_db()
                sql = """
                        UPDATE tbldevicetype set DeviceName= '%s', MACNUM= '%s', Class= '%s',DHistory= '%s',
                        Modifier= '%s', RecordTime= '%s'
                        WHERE DeviceId = '%s'                
                        """ % ( sDevicename, sMACNUM, sClass, sDHistory, sMail, sRecordTime, sDeviceid)

                SQLConn.cur.execute(sql)
                SQLConn.commit()
                SQLConn.close()
                dResult['data']['status'] = "successful"

                # 3 delete
            elif sType == '3':
                lNTID = sDeletelist.split(',')
                SQLConn = analyzer_db()
                sql = "DELETE FROM tbldevicetype WHERE DeviceId IN %s" % List2String(lNTID)
                SQLConn.cur.execute(sql)
                SQLConn.commit()
                SQLConn.close()
                dResult['data']['status'] = "successful"
        else:
            dResult['data']['status'] = "sorry, you have no operating rights."
    return HttpResponse(simplejson.dumps(dResult), content_type='application/json')

def hardware(request):
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