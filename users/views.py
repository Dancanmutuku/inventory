from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.contrib import messages

# Import your models
from products.models import Product, Category
from warehouses.models import Warehouse
from inventory.models import Inventory
from purchases.models import PurchaseOrder, PurchaseItem
from sales.models import SalesOrder, SalesItem

# -------------------------
# Helper functions for roles
# -------------------------
def is_manager(user):
    return user.role == 'MANAGER'

def is_storekeeper(user):
    return user.role == 'STOREKEEPER'


# -------------------------
# Manager login
# -------------------------
def manager_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user and is_manager(user):
            login(request, user)
            return redirect('manager_dashboard')
        return render(request, 'users/manager_login.html', {'error': 'Invalid credentials'})
    return render(request, 'users/manager_login.html')


# -------------------------
# Storekeeper login
# -------------------------
def storekeeper_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user and is_storekeeper(user):
            login(request, user)
            return redirect('storekeeper_dashboard')
        return render(request, 'users/storekeeper_login.html', {'error': 'Invalid credentials'})
    return render(request, 'users/storekeeper_login.html')


# -------------------------
# Dashboards
# -------------------------
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
    context = {'inventory': inventory}
    return render(request, 'users/storekeeper_dashboard.html', context)


# -------------------------
# Manager: Product CRUD
# -------------------------
@login_required
@user_passes_test(is_manager)
def add_product(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        name = request.POST['name']
        sku = request.POST['sku']
        category_id = request.POST['category']
        cost_price = request.POST['cost_price']
        selling_price = request.POST['selling_price']
        category = get_object_or_404(Category, id=category_id)
        Product.objects.create(
            name=name, sku=sku, category=category,
            cost_price=cost_price, selling_price=selling_price
        )
        messages.success(request, 'Product added successfully.')
        return redirect('manager_dashboard')
    return render(request, 'users/add_product.html', {'categories': categories})


@login_required
@user_passes_test(is_manager)
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()
    if request.method == 'POST':
        product.name = request.POST['name']
        product.sku = request.POST['sku']
        product.category = get_object_or_404(Category, id=request.POST['category'])
        product.cost_price = request.POST['cost_price']
        product.selling_price = request.POST['selling_price']
        product.save()
        messages.success(request, 'Product updated successfully.')
        return redirect('manager_dashboard')
    return render(request, 'users/edit_product.html', {'product': product, 'categories': categories})


@login_required
@user_passes_test(is_manager)
@require_POST
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, 'Product deleted successfully.')
    return redirect('manager_dashboard')


# -------------------------
# Manager: Warehouse CRUD
# -------------------------
@login_required
@user_passes_test(is_manager)
def add_warehouse(request):
    if request.method == 'POST':
        name = request.POST['name']
        location = request.POST['location']
        Warehouse.objects.create(name=name, location=location)
        messages.success(request, 'Warehouse added successfully.')
        return redirect('manager_dashboard')
    return render(request, 'users/add_warehouse.html')


@login_required
@user_passes_test(is_manager)
def edit_warehouse(request, warehouse_id):
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)
    if request.method == 'POST':
        warehouse.name = request.POST['name']
        warehouse.location = request.POST['location']
        warehouse.save()
        messages.success(request, 'Warehouse updated successfully.')
        return redirect('manager_dashboard')
    return render(request, 'users/edit_warehouse.html', {'warehouse': warehouse})


@login_required
@user_passes_test(is_manager)
@require_POST
def delete_warehouse(request, warehouse_id):
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)
    warehouse.delete()
    messages.success(request, 'Warehouse deleted successfully.')
    return redirect('manager_dashboard')


# -------------------------
# Storekeeper: Stock Operations
# -------------------------
@login_required
@user_passes_test(is_storekeeper)
def receive_stock(request):
    products = Product.objects.all()
    warehouses = Warehouse.objects.all()
    if request.method == 'POST':
        product_id = request.POST['product']
        warehouse_id = request.POST['warehouse']
        quantity = int(request.POST['quantity'])
        product = get_object_or_404(Product, id=product_id)
        warehouse = get_object_or_404(Warehouse, id=warehouse_id)
        inventory, created = Inventory.objects.get_or_create(
            product=product, warehouse=warehouse, defaults={'quantity': 0}
        )
        inventory.quantity += quantity
        inventory.save()
        messages.success(request, 'Stock updated successfully.')
        return redirect('storekeeper_dashboard')
    return render(request, 'users/receive_stock.html', {'products': products, 'warehouses': warehouses})


@login_required
@user_passes_test(is_storekeeper)
def record_sale(request):
    products = Product.objects.all()
    warehouses = Warehouse.objects.all()
    if request.method == 'POST':
        product_id = int(request.POST['product'])
        warehouse_id = int(request.POST['warehouse'])
        quantity = int(request.POST['quantity'])
        product = get_object_or_404(Product, id=product_id)
        warehouse = get_object_or_404(Warehouse, id=warehouse_id)
        inventory = get_object_or_404(Inventory, product=product, warehouse=warehouse)
        if quantity > inventory.quantity:
            messages.error(request, 'Not enough stock!')
            return redirect('storekeeper_dashboard')
        inventory.quantity -= quantity
        inventory.save()
        messages.success(request, 'Sale recorded successfully.')
        return redirect('storekeeper_dashboard')
    return render(request, 'users/record_sale.html', {'products': products, 'warehouses': warehouses})
