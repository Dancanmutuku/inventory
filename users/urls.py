from django.urls import path
from . import views 

urlpatterns = [
    # Login URLs
    path('manager/login/', views.manager_login, name='manager_login'),
    path('storekeeper/login/', views.storekeeper_login, name='storekeeper_login'),

    # Dashboards
    path('manager/dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('storekeeper/dashboard/', views.storekeeper_dashboard, name='storekeeper_dashboard'),

    # Logout
    path('logout/', views.user_logout, name='logout'),

    # Products (Manager)
    path('manager/product/add/', views.add_product, name='add_product'),
    path('manager/product/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('manager/product/delete/<int:product_id>/', views.delete_product, name='delete_product'),

    # Warehouses (Manager)
    path('manager/warehouse/add/', views.add_warehouse, name='add_warehouse'),
    path('manager/warehouse/edit/<int:warehouse_id>/', views.edit_warehouse, name='edit_warehouse'),
    path('manager/warehouse/delete/<int:warehouse_id>/', views.delete_warehouse, name='delete_warehouse'),

    # Inventory / Sales (Storekeeper)
    path('storekeeper/receive_stock/', views.receive_stock, name='receive_stock'),
    path('storekeeper/record_sale/', views.record_sale, name='record_sale'),
]
