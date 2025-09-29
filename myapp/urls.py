from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.Home, name='home'),
    path('server/', views.Server_View),
    path('download/', views.Download),
    path('db/', views.DB_View),
]