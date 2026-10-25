from django import forms
from django.forms import formset_factory
from .models import (PurchaseRequest, 
                     PurchaseRequestItem, 
                     Vendor, 
                     VendorInvitation, 
                     VendorSelection, 
                     Quotation, 
                     PurchaseOrder,
                     PurchaseOrderItem,
                     GoodsReceipt, 
                     GoodsReceiptItem,)

class PurchaseRequestForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequest
        fields = [
            "pr_number",
            "title",
            "description",
            "justification",
            "needed_by",
        ]

        widgets = {
            "needed_by": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "pr_number": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "title": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "justification": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }


class PurchaseRequestItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequestItem
        fields = [
            "item_name",
            "specification",
            "quantity",
            "unit",
            "estimated_unit_price",
        ]

        widgets = {
            "item_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "specification": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "quantity": forms.NumberInput(
                attrs={"class": "form-control", "min": 1}
            ),
            "unit": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "estimated_unit_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                }
            ),
        }

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = [
            "name",
            "contact_person",
            "email",
            "phone",
            "address",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "contact_person": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "address": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }
        
class VendorInvitationForm(forms.ModelForm):
    class Meta:
        model = VendorInvitation
        fields = ["vendor", "notes"]
        widgets = {
            "vendor": forms.Select(
                attrs={"class": "form-select"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Catatan undangan (opsional)",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vendor"].queryset = Vendor.objects.filter(
            is_active=True
        ).order_by("name")

class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = [
            "quotation_number",
            "quotation_date",
            "valid_until",
            "total_price",
            "notes",
        ]
        widgets = {
            "quotation_number": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "quotation_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "valid_until": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "total_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0.01",
                    "step": "0.01",
                }
            ),
            "notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        quotation_date = cleaned_data.get("quotation_date")
        valid_until = cleaned_data.get("valid_until")
        total_price = cleaned_data.get("total_price")

        if quotation_date and valid_until:
            if valid_until < quotation_date:
                self.add_error(
                    "valid_until",
                    "Masa berlaku tidak boleh sebelum tanggal quotation.",
                )

        if total_price is not None and total_price <= 0:
            self.add_error(
                "total_price",
                "Total harga harus lebih besar dari nol.",
            )

        return cleaned_data

class VendorSelectionForm(forms.Form):
    quotation = forms.ModelChoiceField(
        queryset=Quotation.objects.none(),
        label="Quotation yang dipilih",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    selection_reason = forms.CharField(
        label="Alasan Pemilihan Vendor",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": (
                    "Jelaskan pertimbangan harga, kualitas, "
                    "spesifikasi, atau waktu pengiriman."
                ),
            }
        ),
    )

    def __init__(self, *args, purchase_request=None, **kwargs):
        super().__init__(*args, **kwargs)

        if purchase_request is not None:
            self.fields["quotation"].queryset = (
                Quotation.objects.filter(
                    invitation__purchase_request=purchase_request,
                    invitation__status=VendorInvitation.Status.RESPONDED,
                )
                .select_related("invitation__vendor")
                .order_by("total_price")
            )

            self.fields["quotation"].label_from_instance = (
                lambda quotation: (
                    f"{quotation.invitation.vendor.name} — "
                    f"Rp {quotation.total_price:,.2f}"
                )
            )


class VendorSelectionDecisionForm(forms.Form):
    decision = forms.ChoiceField(
        label="Keputusan",
        choices=[
            (
                VendorSelection.Status.APPROVED,
                "Setujui Pemilihan Vendor",
            ),
            (
                VendorSelection.Status.REVISION_REQUIRED,
                "Minta Revisi",
            ),
            (
                VendorSelection.Status.REJECTED,
                "Tolak Pemilihan Vendor",
            ),
        ],
        widget=forms.RadioSelect,
    )

    manager_comments = forms.CharField(
        label="Komentar Manager",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Masukkan komentar atau alasan keputusan.",
            }
        ),
    )

from django import forms
from .models import PurchaseOrder


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = [
            "order_date",
            "expected_delivery_date",
            "notes",
        ]
        widgets = {
            "order_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "expected_delivery_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Catatan tambahan untuk PO",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        order_date = cleaned_data.get("order_date")
        expected_date = cleaned_data.get("expected_delivery_date")

        if order_date and expected_date and expected_date < order_date:
            self.add_error(
                "expected_delivery_date",
                "Tanggal pengiriman tidak boleh sebelum tanggal PO.",
            )

        return cleaned_data
    
class GoodsReceiptForm(forms.ModelForm):
    class Meta:
        model = GoodsReceipt
        fields = ["receipt_date", "notes"]
        widgets = {
            "receipt_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Catatan penerimaan barang",
                }
            ),
        }


class GoodsReceiptItemForm(forms.Form):
    purchase_order_item_id = forms.IntegerField(
        widget=forms.HiddenInput()
    )
    quantity_received = forms.IntegerField(
        label="Jumlah Diterima",
        min_value=1,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": 1,
            }
        ),
    )
    condition = forms.ChoiceField(
        label="Kondisi Barang",
        choices=GoodsReceiptItem.Condition.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    notes = forms.CharField(
        label="Catatan",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Catatan kondisi atau selisih barang",
            }
        ),
    )


GoodsReceiptItemFormSet = formset_factory(
    GoodsReceiptItemForm,
    extra=0,
)