"""Resource URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from django.contrib import admin
from django.urls import path, include
from allocate import views as alloc_views
from user import views as user_views
from allocate import boeng as bv

urlpatterns = [
    path('admin/', admin.site.urls),
    path('request/gpi/user/login', user_views.login),
    path('request/gpi/user/info', user_views.info),
    path('request/gpi/user/logout', user_views.logout),
    path('request/gpi/user/user_manage', user_views.user_manage),
    path('request/gpi/user/user_edit', user_views.user_edit),
    path('request/gpi/allocate/customerid', alloc_views.customerid),
    path('request/gpi/allocate/customer_list', alloc_views.customer_list),
    path('request/gpi/allocate/customerlist', alloc_views.customerlist),
    path('request/gpi/allocate/request_info', alloc_views.request_info),
    path('request/gpi/allocate/request_edit', alloc_views.request_edit),
    path('request/gpi/allocate/fetch_customer', bv.fetch_customer),
    path('request/gpi/allocate/new_boeng_info', bv.new_boeng_info),
    path('request/gpi/allocate/new_boeng_edit', bv.new_boeng_edit),
    path('request/gpi/allocate/fetch_boengrule', bv.fetch_boengrule),
    path('request/gpi/allocate/nwcc_list', bv.nwcc_list),
    path('request/gpi/allocate/opid_list', bv.opid_list),
    path('request/gpi/allocate/opid_list', bv.opid_list),
    path('request/gpi/allocate/csv_upload', bv.csv_upload),
    path('request/gpi/allocate/download', bv.download),
    path('request/gpi/allocate/new_customer_add', bv.new_customer_add),
    path('request/gpi/allocate/customer_id_edit', alloc_views.customer_id_edit),
    path('request/gpi/allocate/customerid', alloc_views.customerid),
    path('request/gpi/allocate/devicelist', alloc_views.devicelist),
]
