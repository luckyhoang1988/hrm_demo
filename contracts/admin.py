from django.contrib import admin
from .models import Contract


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display  = ['contract_number', 'employee', 'contract_type', 'status', 'start_date', 'end_date']
    list_filter   = ['status', 'contract_type']
    search_fields = ['contract_number', 'employee__full_name']
