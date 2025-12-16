from .models import Inventory
from inventory import models
from django.core.mail import send_mail

def send_low_stock_alert(product):
    send_mail(
        'Low Stock Alert',
        f'{product.name} is below reorder level.',
        'mutukudancan6@gmail.com',
        ['mutukudancan6@gmail.com']
    )

def get_low_stock_items():
    return Inventory.objects.filter(
        quantity__lte=models.F('product__reorder_level')
    )
