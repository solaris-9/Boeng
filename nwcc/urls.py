from django.urls import path
from nwcc import views

urlpatterns = [
    path('list', views.nwcc_list),
    path('edit', views.nwcc_edit),
    path('delete', views.nwcc_edit),
]