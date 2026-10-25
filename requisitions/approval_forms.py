
from django import forms

from .models import PRApprovalHistory


class PRApprovalForm(forms.Form):
    decision = forms.ChoiceField(
        choices=PRApprovalHistory.Decision.choices,
        widget=forms.RadioSelect,
    )
    comments = forms.CharField(
        label="Komentar",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": (
                    "Masukkan alasan keputusan atau "
                    "catatan revisi..."
                ),
            }
        ),
    )
