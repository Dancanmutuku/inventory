from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SalesItem
from inventory.models import Inventory, StockMovement

@receiver(post_save, sender=SalesItem)
def deduct_stock(sender, instance, created, **kwargs):
    if created:
        inventory = Inventory.objects.get(
            product=instance.product,
            warehouse=instance.sales_order.warehouse
        )
        inventory.quantity -= instance.quantity
        inventory.save()

        StockMovement.objects.create(
            product=instance.product,
            warehouse=instance.sales_order.warehouse,
            movement_type='OUT',
            quantity=instance.quantity
        )
