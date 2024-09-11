from datetime import datetime
import simplejson
import pymysql
from django.http import HttpResponse
from django.http import JsonResponse  
import json

File_address = r'C:/btmLog/printlog.txt'
fa = open(File_address,'a')

# from django.conf import settings
# def getConnection():
#     SQLBConn = pymysql.connect(host  = settings.BBD_DB['host'],
#                             port     = settings.BBD_DB['port'],
#                             user     = settings.BBD_DB['username'],
#                             password = settings.BBD_DB['password'],
#                             database = settings.BBD_DB['name'],
#                             charset  = settings.BBD_DB['charset']
#                         )
#     return SQLBConn

BBD_DB = {
    'host':'10.74.97.87',
    'port':3306,
    'username':'btmadmin',
    'password':'BBD@2024',
    'name':'btmdb',
    'charset':'utf8mb4',
}

def getConnection():
    SQLBConn = pymysql.connect(host  = BBD_DB['host'],
                            port     = BBD_DB['port'],
                            user     = BBD_DB['username'],
                            password = BBD_DB['password'],
                            database = BBD_DB['name'],
                            charset  = BBD_DB['charset']
                        )
    return SQLBConn


def SLIC_create(request):
    ud = request.get_full_path()
    sLastupdate = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    print("@@@@", sLastupdate, ud ) 
    try:  
        SLIC_Value = request.GET.get('SLIC')  
        SLICIPN_Value = request.GET.get('SLICIPN')  
        Supplier_Value = request.GET.get('Supplier')  
        SLICQTY_Value = request.GET.get('SLICQTY')  
    except Exception as e:  
        return HttpResponse(simplejson.dumps({"error": "Invalid Parameters"}), content_type='application/json')  
    
    cmd = f"""  
        INSERT INTO tblslic 
        ( SLIC, SLICIPN, Supplier, SLICQTY)
        VALUES( '{SLIC_Value}', '{SLICIPN_Value}', '{Supplier_Value}', '{SLICQTY_Value}')
    """  
    print(cmd)
    SQLBConn = getConnection()
    SQLBCur = SQLBConn.cursor()
    SQLBCur.execute(cmd) 
    SQLBConn.commit()
    SQLBConn.close()

    return HttpResponse(simplejson.dumps("Complete successfully!"), content_type='application/json')  

def SLIC_retrieve(request):
    ud = request.get_full_path()
    sLastupdate = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    print("@@@@", sLastupdate, ud ) 
   
    params = []    
    where_clauses = []    
    try:  
        SLICID_Value = request.GET.get('SLICID')  
        if SLICID_Value != '':  
            where_clauses.append("SLICID = %s")  
            params.append(SLICID_Value) 
  
        SLIC_Value = request.GET.get('SLIC')  
        if SLIC_Value != '':   
            where_clauses.append("SLIC = %s")  
            params.append(SLIC_Value)  
  
        SLICIPN_Value = request.GET.get('SLICIPN')  
        if SLICIPN_Value != '':  
            where_clauses.append("SLICIPN = %s")  
            params.append(SLICIPN_Value)  
  
        Supplier_Value = request.GET.get('Supplier')  
        if Supplier_Value !='': 
            where_clauses.append("Supplier = %s")  
            params.append(Supplier_Value)   

        SLICQTY_Value = request.GET.get('SLICQTY')  
        if SLICQTY_Value != '': 
            where_clauses.append("SLICQTY = %s")  
            params.append(SLICQTY_Value) 
    except Exception as e:  
        return HttpResponse(simplejson.dumps({"error": "Invalid Parameters"}), content_type='application/json')  

    where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""    
    cmd = f"""  
        SELECT SLICID, SLIC, SLICIPN, Supplier, SLICQTY  
        FROM tblslic {where_clause}  
        ORDER BY SLIC  
        LIMIT 1000  
    """  
  
    SQLBConn = getConnection()
    SQLBCur = SQLBConn.cursor()
    SQLBCur.execute(cmd, params) 
    SQLBResult = SQLBCur.fetchall()
    SQLBConn.close()

    column_names = [col[0] for col in SQLBCur.description]  
    data = [dict(zip(column_names, row)) for row in SQLBResult]  

    return HttpResponse(simplejson.dumps(data), content_type='application/json')

def SLIC_update(request):
    ud = request.get_full_path()
    sLastupdate = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    print("@@@@", sLastupdate, ud ) 
    params = []    
    where_clauses = []    

    try:  
        SLIC_Value = request.GET.get('SLIC')  
        if SLIC_Value != '':   
            where_clauses.append("SLIC = %s")  
            params.append(SLIC_Value)  
  
        SLICIPN_Value = request.GET.get('SLICIPN')  
        if SLICIPN_Value != '':  
            where_clauses.append("SLICIPN = %s")  
            params.append(SLICIPN_Value)  
  
        Supplier_Value = request.GET.get('Supplier')  
        if Supplier_Value !='': 
            where_clauses.append("Supplier = %s")  
            params.append(Supplier_Value)   
        
        SLICQTY_Value = request.GET.get('SLICQTY')  
        if SLICQTY_Value !='': 
            where_clauses.append("SLICQTY = %s")  
            params.append(SLICQTY_Value) 

        SLICID_Value = request.GET.get('SLICID')  

    except Exception as e:  
        return HttpResponse(simplejson.dumps({"error": "Invalid Parameters"}), content_type='application/json')  

    set_clause = "set " + " , ".join(where_clauses) if where_clauses else ""    
    cmd = f"""  
        UPDATE tblslic {set_clause}  WHERE SLICID= {SLICID_Value};
    """ 
    print(cmd)
    SQLBConn = getConnection()
    SQLBCur = SQLBConn.cursor()
    SQLBCur.execute(cmd,params) 
    SQLBConn.commit()
    SQLBConn.close()

    return HttpResponse(simplejson.dumps("Complete successfully!"), content_type='application/json')  

def SLIC_delete(request):  
    ud = request.get_full_path()
    sLastupdate = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    print("@@@@", sLastupdate, ud ) 
    if request.method == 'POST':  
        # slic_ids = request.POST.getlist('SLICIDs')  # 获取SLICIDs列表  
        data = json.loads(request.body)  
        slic_ids = data.get('SLICIDs', [])  
        
        print (len(slic_ids))
        placeholders = ', '.join(['%s'] * len(slic_ids))  
        cmd = f"DELETE FROM tblslic WHERE SLICID IN ({placeholders})"  
        print(cmd)
        SQLBConn = getConnection()
        SQLBCur = SQLBConn.cursor()
        SQLBCur.execute(cmd,slic_ids) 
        SQLBConn.commit()
        SQLBConn.close()
  
        # 返回响应  
        return JsonResponse({'message': 'SLICs deleted successfully', 'deleted_ids': slic_ids})  
    else:  
        return JsonResponse({'error': 'Method not allowed'}, status=405)

# class DummyRequest:  
#     def __init__(self, method='GET', path='/', GET=None):  
#         self.method = method  
#         self.path = path  
#         # 可以根据需要添加其他模拟的属性，比如GET、POST、user等  
#         self.GET =  GET or {}  # 模拟GET请求的数据          
#         # self.user = None  # 模拟用户对象，可以根据需要设置  
#     def get_full_path(self):
#         return "sssspath"
#     # 假设你的视图函数需要访问类似request.GET['some_key']这样的东西  
#     # 你可以添加更多的方法来模拟这些行为  
  
  
# 创建一个dummy request对象  
# dummy_request = DummyRequest(method='GET', path='/slic/', GET={'SLICID': '123', 'SLIC': 'example','SLICIPN': 'SLICIPN_Value', 'Supplier': 'Supplier_Value'})   

# # 调用SLIC_retrieve函数并打印结果  
# SLIC_retrieve(dummy_request) 
# dummy_request = DummyRequest(method='GET', path='/slic/', GET={ 'SLIC': 'example2','SLICIPN': 'SLICIPN_Value', 'Supplier': 'Supplier_Value','SLICQTY': '123'}) 
# SLIC_create(dummy_request)  
