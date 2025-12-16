from django.urls import path
from .views import (
    add_product, add_warehouse, delete_product, delete_warehouse, edit_product, edit_warehouse, manager_login, receive_stock, record_sale, storekeeper_login, 
    manager_dashboard, storekeeper_dashboard
)

urlpatterns = [
    path('manager/login/', manager_login, name='manager_login'),
    path('storekeeper/login/', storekeeper_login, name='storekeeper_login'),
    path('manager/dashboard/', manager_dashboard, name='manager_dashboard'),
    path('storekeeper/dashboard/', storekeeper_dashboard, name='storekeeper_dashboard'),
    # Products
    path('manager/product/add/', add_product, name='add_product'),
    path('manager/product/edit/<int:product_id>/', edit_product, name='edit_product'),
    path('manager/product/delete/<int:product_id>/', delete_product, name='delete_product'),

    # Warehouses
    path('manager/warehouse/add/', add_warehouse, name='add_warehouse'),
    path('manager/warehouse/edit/<int:warehouse_id>/', edit_warehouse, name='edit_warehouse'),
    path('manager/warehouse/delete/<int:warehouse_id>/', delete_warehouse, name='delete_warehouse'),
    path('storekeeper/receive_stock/', receive_stock, name='receive_stock'),
    path('storekeeper/record_sale/', record_sale, name='record_sale'),


]
