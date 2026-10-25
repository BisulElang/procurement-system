from django.contrib import admin
from .models import (PurchaseRequest, 
                     PurchaseRequestItem, 
                     PRApprovalHistory, 
                     Vendor, 
                     VendorInvitation, 
                     Quotation, 
                     VendorSelection,
                     PurchaseOrder, 
                     PurchaseOrderItem,
                     )

class PurchaseRequestItemInline(admin.TabularInline):
    model = PurchaseRequestItem
    extra = 1

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0
    readonly_fields = (
        "item_name",
        "specification",
        "quantity",
        "unit",
    )

@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = (
        "pr_number",
        "title",
        "requester",
        "needed_by",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("pr_number", "title", "requester__username")
    inlines = [PurchaseRequestItemInline]

@admin.register(PRApprovalHistory)
class PRApprovalHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "purchase_request",
        "approver",
        "decision",
        "created_at",
    )

    list_filter = ("decision", "created_at")

    search_fields = (
        "purchase_request__pr_number",
        "approver__username",
        "comments",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_person", "email", "is_active")
    search_fields = ("name", "email")
    list_filter = ("is_active",)

@admin.register(VendorInvitation)
class VendorInvitationAdmin(admin.ModelAdmin):
    list_display = (
        "purchase_request",
        "vendor",
        "status",
        "invited_at",
    )
    list_filter = ("status",)
    search_fields = (
        "purchase_request__pr_number",
        "vendor__name",
    )

@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = (
        "invitation",
        "quotation_number",
        "quotation_date",
        "valid_until",
        "total_price",
    )
    search_fields = (
        "quotation_number",
        "invitation__vendor__name",
    )

@admin.register(VendorSelection)
class VendorSelectionAdmin(admin.ModelAdmin):
    list_display = (
        "purchase_request",
        "quotation",
        "submitted_by",
        "status",
        "submitted_at",
        "decided_by",
        "decided_at",
    )
    list_filter = ("status",)
    search_fields = (
        "purchase_request__pr_number",
        "quotation__invitation__vendor__name",
    )

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = (
        "po_number",
        "vendor_selection",
        "order_date",
        "expected_delivery_date",
        "status",
        "created_by",
    )
    list_filter = ("status", "order_date")
    search_fields = (
        "po_number",
        "vendor_selection__purchase_request__pr_number",
        "vendor_selection__quotation__invitation__vendor__name",
    )
    readonly_fields = ("po_number", "created_at", "updated_at")
    inlines = [PurchaseOrderItemInline]