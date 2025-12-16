from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.contrib import messages

# Import your models
from products.models import Product, Category
from warehouses.models import Warehouse
from inventory.models import Inventory, StockMovement
from purchases.models import PurchaseItem, PurchaseOrder
from sales.models import SalesOrder, SalesItem

from django.contrib.auth import logout
from django.shortcuts import redirect
from suppliers.models import Supplier 
from django.db import transaction
from decimal import Decimal



def user_logout(request):
    """Logs out any user and redirects them to the appropriate login page based on role."""
    role = getattr(request.user, 'role', None)
    logout(request)

    if role == 'MANAGER':
        return redirect('manager_login')
    elif role == 'STOREKEEPER':
        return redirect('storekeeper_login')
    else:
        return redirect('manager_login')  # default fallback

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


# Dashboards
from django.db.models import Sum, F
from django.shortcuts import render
from sales.models import SalesOrder, SalesItem
from warehouses.models import Warehouse
from inventory.models import Inventory, StockMovement
from products.models import Product
from django.utils.timezone import now
from datetime import timedelta


@login_required
def manager_dashboard(request):
    # Basic data for cards
    products = Product.objects.all()
    warehouses = Warehouse.objects.all()
    inventory = Inventory.objects.all()
    total_stock_value = inventory.aggregate(
        total_value=Sum(F('quantity') * F('product__cost_price'))
    )['total_value']

    # Recent Stock Activity (Last 10)
    recent_received = StockMovement.objects.filter(movement_type='IN')\
        .select_related('product', 'warehouse').order_by('-created_at')[:10]
    recent_sold = StockMovement.objects.filter(movement_type='OUT')\
        .select_related('product', 'warehouse').order_by('-created_at')[:10]

    # ----- Analytics & Reports -----
    # 1. Total Sales per Warehouse
    sales_per_warehouse = StockMovement.objects.filter(movement_type='OUT')\
        .values('warehouse__name')\
        .annotate(num_sales=Sum('quantity'))
    sales_per_warehouse_labels = [s['warehouse__name'] for s in sales_per_warehouse]
    sales_per_warehouse_data = [s['num_sales'] or 0 for s in sales_per_warehouse]

    # 2. Revenue per Warehouse
    revenue_per_warehouse_labels = []
    revenue_per_warehouse_data = []
    for warehouse in warehouses:
        sold_items = StockMovement.objects.filter(
            movement_type='OUT', warehouse=warehouse
        ).select_related('product')
        revenue = sum(item.product.selling_price * item.quantity for item in sold_items)
        revenue_per_warehouse_labels.append(warehouse.name)
        revenue_per_warehouse_data.append(revenue)

    # 3. Top Selling Products
    top_products = StockMovement.objects.filter(movement_type='OUT')\
        .values('product__name')\
        .annotate(units_sold=Sum('quantity'))\
        .order_by('-units_sold')[:10]
    top_products_labels = [p['product__name'] for p in top_products]
    top_products_data = [p['units_sold'] or 0 for p in top_products]

    # 4. Stock Movement Over Time (Last 6 months)
    months = []
    stock_received_data = []
    stock_sold_data = []

    for i in range(5, -1, -1):
        month_start = (now() - timedelta(days=i*30)).replace(day=1)
        month_label = month_start.strftime('%b %Y')
        months.append(month_label)

        # Stock Received
        received = StockMovement.objects.filter(
            movement_type='IN',
            created_at__year=month_start.year,
            created_at__month=month_start.month
        ).aggregate(total=Sum('quantity'))['total'] or 0
        stock_received_data.append(received)

        # Stock Sold
        sold = StockMovement.objects.filter(
            movement_type='OUT',
            created_at__year=month_start.year,
            created_at__month=month_start.month
        ).aggregate(total=Sum('quantity'))['total'] or 0
        stock_sold_data.append(sold)

    context = {
        'products': products,
        'warehouses': warehouses,
        'inventory': inventory,
        'total_stock_value': total_stock_value,
        'recent_received': recent_received,
        'recent_sold': recent_sold,
        'sales_per_warehouse_labels': sales_per_warehouse_labels,
        'sales_per_warehouse_data': sales_per_warehouse_data,
        'revenue_per_warehouse_labels': revenue_per_warehouse_labels,
        'revenue_per_warehouse_data': revenue_per_warehouse_data,
        'top_products_labels': top_products_labels,
        'top_products_data': top_products_data,
        'stock_movement_labels': months,
        'stock_received_data': stock_received_data,
        'stock_sold_data': stock_sold_data,
    }

    return render(request, 'users/manager_dashboard.html', context)

@login_required
@user_passes_test(is_storekeeper)
def storekeeper_dashboard(request):
    # Inventory visible to storekeeper
    inventory = Inventory.objects.select_related('product', 'warehouse').all()
    
    # Products list (for CRUD)
    products = Product.objects.all()
    
    # Summary calculations
    total_products = products.count()
    total_stock = sum(item.quantity for item in inventory)
    low_stock_count = sum(1 for item in inventory if item.quantity < 10)  # threshold = 10
    
    context = {
        'inventory': inventory,
        'products': products,
        'total_products': total_products,
        'total_stock': total_stock,
        'low_stock_count': low_stock_count,
    }
    
    return render(request, 'users/storekeeper_dashboard.html', context)

# -------------------------
# Manager: Product CRUD
# -------------------------
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from products.models import Product, Category
from django.contrib.auth.decorators import login_required

@login_required
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

        # Redirect to respective dashboard
        if request.user.role == 'MANAGER':
            return redirect('manager_dashboard')
        else:
            return redirect('storekeeper_dashboard')

    # Choose base template dynamically
    base_template = 'users/base_manager.html' if request.user.role == 'MANAGER' else 'users/base_storekeeper.html'
    
    return render(request, 'users/add_product.html', {'categories': categories, 'base_template': base_template})


@login_required
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

        if request.user.role == 'MANAGER':
            return redirect('manager_dashboard')
        else:
            return redirect('storekeeper_dashboard')

    base_template = 'users/base_manager.html' if request.user.role == 'MANAGER' else 'users/base_storekeeper.html'

    return render(request, 'users/edit_product.html', {'product': product, 'categories': categories, 'base_template': base_template})


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
def is_storekeeper(user):
    return user.role == 'STOREKEEPER'

# -------------------------
# Receive Stock
@login_required
@user_passes_test(is_storekeeper)
@transaction.atomic
def receive_stock(request):
    products = Product.objects.all()
    warehouses = Warehouse.objects.all()
    suppliers = Supplier.objects.all()

    if request.method == 'POST':
        product = get_object_or_404(Product, id=request.POST['product'])
        warehouse = get_object_or_404(Warehouse, id=request.POST['warehouse'])
        supplier = get_object_or_404(Supplier, id=request.POST['supplier'])

        quantity = int(request.POST['quantity'])
        unit_cost = Decimal(request.POST['unit_cost'])

        if quantity <= 0:
            messages.error(request, 'Quantity must be greater than zero.')
            return redirect('receive_stock')

        if unit_cost <= 0:
            messages.error(request, 'Unit cost must be greater than zero.')
            return redirect('receive_stock')

        # 1. Create Purchase Order
        purchase_order = PurchaseOrder.objects.create(
            supplier=supplier,
            warehouse=warehouse,
            status='RECEIVED',
            total_cost=unit_cost * quantity
        )

        # 2. Create Purchase Item
        PurchaseItem.objects.create(
            purchase_order=purchase_order,
            product=product,
            quantity=quantity,
            unit_cost=unit_cost
        )

        # 3. Update Inventory
        inventory, _ = Inventory.objects.get_or_create(
            product=product,
            warehouse=warehouse,
            defaults={'quantity': 0}
        )
        inventory.quantity += quantity
        inventory.save()

        # 4. Record Stock Movement
        StockMovement.objects.create(
            product=product,
            warehouse=warehouse,
            movement_type='IN',
            quantity=quantity
        )

        messages.success(request, 'Stock received successfully.')
        return redirect('storekeeper_dashboard')

    return render(request, 'users/receive_stock.html', {
        'products': products,
        'warehouses': warehouses,
        'suppliers': suppliers
    })

# -------------------------
# Record Sale
@login_required
@user_passes_test(is_storekeeper)
def record_sale(request):
    products = Product.objects.all()
    warehouses = Warehouse.objects.all()

    if request.method == 'POST':
        product_id = request.POST.get('product')
        warehouse_id = request.POST.get('warehouse')
        quantity = int(request.POST.get('quantity'))
        unit_price = float(request.POST.get('unit_price'))
        customer_name = request.POST.get('customer_name', 'Walk-in Customer')

        product = get_object_or_404(Product, id=product_id)
        warehouse = get_object_or_404(Warehouse, id=warehouse_id)

        # Get inventory
        inventory = Inventory.objects.filter(
            product=product,
            warehouse=warehouse
        ).first()

        if not inventory:
            messages.error(request, 'Product not found in this warehouse.')
            return redirect('record_sale')

        if quantity > inventory.quantity:
            messages.error(request, 'Not enough stock available.')
            return redirect('record_sale')

        # Reduce inventory
        inventory.quantity -= quantity
        inventory.save()

        # Record stock movement (OUT)
        StockMovement.objects.create(
            product=product,
            warehouse=warehouse,
            quantity=quantity,
            movement_type='OUT'
        )

        # Optional: Sales Order (recommended for reports)
        sales_order = SalesOrder.objects.create(
            customer_name=customer_name,
            warehouse=warehouse,
            total_amount=unit_price * quantity
        )

        SalesItem.objects.create(
            sales_order=sales_order,
            product=product,
            quantity=quantity,
            unit_price=unit_price
        )

        messages.success(request, 'Sale recorded successfully.')
        return redirect('storekeeper_dashboard')

    context = {
        'products': products,
        'warehouses': warehouses
    }
    return render(request, 'users/record_sale.html', context)

@login_required
@user_passes_test(is_storekeeper)
def move_stock(request):
    products = Product.objects.all()
    warehouses = Warehouse.objects.all()

    if request.method == 'POST':
        product_id = request.POST['product']
        from_warehouse_id = request.POST['from_warehouse']
        to_warehouse_id = request.POST['to_warehouse']
        quantity = int(request.POST['quantity'])

        product = get_object_or_404(Product, id=product_id)
        from_wh = get_object_or_404(Warehouse, id=from_warehouse_id)
        to_wh = get_object_or_404(Warehouse, id=to_warehouse_id)

        from_inventory = get_object_or_404(Inventory, product=product, warehouse=from_wh)
        to_inventory, created = Inventory.objects.get_or_create(product=product, warehouse=to_wh, defaults={'quantity': 0})

        if quantity > from_inventory.quantity:
            messages.error(request, "Not enough stock to transfer!")
            return redirect('move_stock')

        # Update inventories
        from_inventory.quantity -= quantity
        from_inventory.save()
        to_inventory.quantity += quantity
        to_inventory.save()

        # Record stock movements
        StockMovement.objects.create(product=product, warehouse=from_wh, quantity=quantity, movement_type='OUT')
        StockMovement.objects.create(product=product, warehouse=to_wh, quantity=quantity, movement_type='IN')

        messages.success(request, "Stock moved successfully!")
        return redirect('move_stock')

    context = {
        'products': products,
        'warehouses': warehouses,
    }
    return render(request, 'users/move_stock.html', context)
