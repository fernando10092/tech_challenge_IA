from django.urls import path
from . import views

urlpatterns = [
    path('', views.Home, name='home'),
    #path('server/', views.Server_View, name='server_view'),
    path('download/', views.Download, name='download'),
    path('db/', views.DB_View, name='db_view'),
    #path('teste/', views.Teste_View, name='teste_view'),
]
