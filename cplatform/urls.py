from django.urls import path
from cplatform import views

urlpatterns = [
    path('list', views.list),
    path('edit', views.edit),
    path('delete', views.delete),
]