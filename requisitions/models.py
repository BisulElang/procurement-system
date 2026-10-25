
from django.conf import settings
from django.db import models
import uuid


class PurchaseRequest(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        REVISION_REQUIRED = (
            "REVISION_REQUIRED",
            "Revision Required",
        )
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    pr_number = models.CharField(
        max_length=30,
        unique=True,
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="purchase_requests",
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    justification = models.TextField()
    needed_by = models.DateField()
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.pr_number


class PurchaseRequestItem(models.Model):
    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name="items",
    )
    item_name = models.CharField(max_length=200)
    specification = models.TextField(blank=True)
    quantity = models.PositiveIntegerField()
    unit = models.CharField(max_length=30)
    estimated_unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    def __str__(self):
        return (
            f"{self.item_name} "
            f"(PR: {self.purchase_request.pr_number})"
        )


class PRApprovalHistory(models.Model):
    class Decision(models.TextChoices):
        APPROVED = "APPROVED", "Approved"
        REVISION_REQUIRED = (
            "REVISION_REQUIRED",
            "Revision Required",
        )
        REJECTED = "REJECTED", "Rejected"

    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.PROTECT,
        related_name="approval_histories",
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pr_approval_histories",
    )
    decision = models.CharField(
        max_length=30,
        choices=Decision.choices,
    )
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.purchase_request.pr_number} - "
            f"{self.get_decision_display()}"
        )


class Vendor(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class VendorInvitation(models.Model):
    class Status(models.TextChoices):
        INVITED = "INVITED", "Invited"
        RESPONDED = "RESPONDED", "Responded"
        DECLINED = "DECLINED", "Declined"

    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.PROTECT,
        related_name="vendor_invitations",
    )
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.PROTECT,
        related_name="invitations",
    )
    invited_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.INVITED,
    )
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["purchase_request", "vendor"],
                name="unique_vendor_invitation_per_pr",
            )
        ]

    def __str__(self):
        return (
            f"{self.purchase_request.pr_number} - "
            f"{self.vendor.name}"
        )


class Quotation(models.Model):
    invitation = models.OneToOneField(
        VendorInvitation,
        on_delete=models.PROTECT,
        related_name="quotation",
    )
    quotation_number = models.CharField(max_length=100, blank=True)
    quotation_date = models.DateField()
    valid_until = models.DateField()
    total_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.invitation.vendor.name} - "
            f"{self.invitation.purchase_request.pr_number}"
        )

class VendorSelection(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Menunggu Persetujuan"
        REVISION_REQUIRED = (
        "REVISION_REQUIRED",
        "Perlu Revisi",
        )
        APPROVED = "APPROVED", "Disetujui"
        REJECTED = "REJECTED", "Ditolak"

    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.PROTECT,
        related_name="vendor_selections",
    )
    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.PROTECT,
        related_name="vendor_selections",
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_vendor_selections",
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="decided_vendor_selections",
        null=True,
        blank=True,
    )
    selection_reason = models.TextField()
    manager_comments = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return (
            f"{self.purchase_request.pr_number} - "
            f"{self.quotation.invitation.vendor.name} - "
            f"{self.get_status_display()}"
        )

class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ISSUED = "ISSUED", "Diterbitkan"
        PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED", "Diterima Sebagian"
        COMPLETED = "COMPLETED", "Selesai Diterima"
        CANCELLED = "CANCELLED", "Dibatalkan"

    po_number = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
    )
    vendor_selection = models.OneToOneField(
        VendorSelection,
        on_delete=models.PROTECT,
        related_name="purchase_order",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_purchase_orders",
    )
    order_date = models.DateField()
    expected_delivery_date = models.DateField(
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.po_number:
            self.po_number = f"T-{uuid.uuid4().hex[:20]}"

            super().save(*args, **kwargs)

            self.po_number = f"PO-{self.pk:06d}"
            super().save(update_fields=["po_number"])
        else:
            super().save(*args, **kwargs)
    def __str__(self):
        return self.po_number or f"PO (baru) - {self.pk}"


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="items",
    )
    purchase_request_item = models.ForeignKey(
        PurchaseRequestItem,
        on_delete=models.PROTECT,
        related_name="purchase_order_items",
    )
    item_name = models.CharField(max_length=200)
    specification = models.TextField(blank=True)
    quantity = models.PositiveIntegerField()
    unit = models.CharField(max_length=30)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.item_name} - {self.purchase_order.po_number}"
    
class GoodsReceipt(models.Model):
    class Status(models.TextChoices):
        PARTIAL = "PARTIAL", "Diterima Sebagian"
        COMPLETED = "COMPLETED", "Selesai Diterima"

    gr_number = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
    )
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.PROTECT,
        related_name="goods_receipts",
    )
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="goods_receipts",
    )
    receipt_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PARTIAL,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-receipt_date", "-created_at"]

    def save(self, *args, **kwargs):
        if not self.gr_number:
            self.gr_number = f"T-{uuid.uuid4().hex[:20]}"
            super().save(*args, **kwargs)

            self.gr_number = f"GR-{self.pk:06d}"
            super().save(update_fields=["gr_number"])
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.gr_number


class GoodsReceiptItem(models.Model):
    class Condition(models.TextChoices):
        GOOD = "GOOD", "Baik"
        DAMAGED = "DAMAGED", "Rusak"
        INCOMPLETE = "INCOMPLETE", "Tidak Lengkap"

    goods_receipt = models.ForeignKey(
        GoodsReceipt,
        on_delete=models.CASCADE,
        related_name="items",
    )
    purchase_order_item = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.PROTECT,
        related_name="goods_receipt_items",
    )
    quantity_received = models.PositiveIntegerField()
    condition = models.CharField(
        max_length=20,
        choices=Condition.choices,
        default=Condition.GOOD,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["goods_receipt", "purchase_order_item"],
                name="unique_gr_item_per_po_item",
            ),
        ]

    def __str__(self):
        return (
            f"{self.goods_receipt.gr_number} - "
            f"{self.purchase_order_item.item_name}"
        )