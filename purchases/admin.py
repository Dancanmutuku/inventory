# purchases/admin.py
from django.contrib import admin
from .models import PurchaseOrder, PurchaseItem

class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem

class PurchaseOrderAdmin(admin.ModelAdmin):
    inlines = [PurchaseItemInline]

admin.site.register(PurchaseOrder, PurchaseOrderAdmin)
