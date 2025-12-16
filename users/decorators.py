from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from products.models import Product
from users.views import is_manager, is_storekeeper
from warehouses.models import Warehouse
from inventory.models import Inventory

@login_required
@user_passes_test(is_manager)
def manager_dashboard(request):
    products = Product.objects.all()
    warehouses = Warehouse.objects.all()
    inventory = Inventory.objects.select_related('product', 'warehouse').all()
    
    context = {
        'products': products,
        'warehouses': warehouses,
        'inventory': inventory
    }
    return render(request, 'users/manager_dashboard.html', context)


@login_required
@user_passes_test(is_storekeeper)
def storekeeper_dashboard(request):
    inventory = Inventory.objects.select_related('product', 'warehouse').all()
    context = {
        'inventory': inventory
    }
    return render(request, 'users/storekeeper_dashboard.html', context)
