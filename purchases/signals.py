from django.db.models.signals import post_save
from django.dispatch import receiver
from purchases.models import PurchaseOrder
from inventory.models import Inventory, StockMovement

@receiver(post_save, sender=PurchaseOrder)
def receive_stock(sender, instance, created, **kwargs):
    if instance.status == 'RECEIVED':
        for item in instance.items.all():
            inventory, _ = Inventory.objects.get_or_create(
                product=item.product,
                warehouse=instance.warehouse,
                defaults={'quantity': 0}
            )
            inventory.quantity += item.quantity
            inventory.save()

            StockMovement.objects.create(
                product=item.product,
                warehouse=instance.warehouse,
                movement_type='IN',
                quantity=item.quantity
            )
