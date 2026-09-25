from django.urls import path

from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_center, name='center'),
    path('print/', views.print_report, name='print'),
    path('sales.csv', views.sales_export_csv, name='sales_csv'),
    path('sales.xlsx', views.sales_export_xlsx, name='sales_xlsx'),
]