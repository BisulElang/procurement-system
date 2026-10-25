from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from django.forms import inlineformset_factory
from django.shortcuts import render, redirect
from django.db.models import Sum

from .forms import (
                    PurchaseRequestForm, 
                    PurchaseRequestItemForm, 
                    VendorForm, 
                    VendorInvitationForm, 
                    VendorSelectionForm, 
                    VendorSelectionDecisionForm, 
                    VendorSelection, 
                    QuotationForm,
                    PurchaseOrderForm,
                    GoodsReceiptForm, 
                    GoodsReceiptItemFormSet,
                    )
from .models import (
                    PurchaseRequest, 
                    PurchaseRequestItem, 
                    PRApprovalHistory, 
                    Vendor, 
                    VendorInvitation, 
                    VendorSelection, 
                    Quotation,
                    PurchaseOrder,
                    PurchaseOrderItem,
                    GoodsReceipt,
                    GoodsReceiptItem,
)

from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden

from django.shortcuts import get_object_or_404, render, redirect
from .approval_forms import PRApprovalForm

from django.contrib import messages

from django.utils import timezone


PurchaseRequestItemFormSet = inlineformset_factory(
    PurchaseRequest,
    PurchaseRequestItem,
    form=PurchaseRequestItemForm,
    extra=1,
    can_delete=True,
)


@login_required
def pr_list(request):
    purchase_requests = PurchaseRequest.objects.filter(
        requester=request.user
    ).order_by("-created_at")

    return render(
        request,
        "requisitions/pr_list.html",
        {"purchase_requests": purchase_requests},
    )


@login_required
def pr_create(request):
    if request.method == "POST":
        form = PurchaseRequestForm(request.POST)
        formset = PurchaseRequestItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                purchase_request = form.save(commit=False)
                purchase_request.requester = request.user
                purchase_request.status = (
                    PurchaseRequest.Status.DRAFT
                )
                purchase_request.save()

                formset.instance = purchase_request
                formset.save()

            return redirect("requisitions:pr_list")
    else:
        form = PurchaseRequestForm()
        formset = PurchaseRequestItemFormSet()

    return render(
        request,
        "requisitions/pr_form.html",
        {"form": form, "formset": formset},
    )


@login_required
def pr_edit(request, pk):
    if request.user.role != "REQUESTER":
        return HttpResponseForbidden(
            "Hanya Requester yang dapat mengedit PR."
        )

    purchase_request = get_object_or_404(
        PurchaseRequest,
        pk=pk,
        requester=request.user,
    )

    allowed_statuses = [
        PurchaseRequest.Status.DRAFT,
        PurchaseRequest.Status.REVISION_REQUIRED,
    ]

    if purchase_request.status not in allowed_statuses:
        return HttpResponseForbidden(
            "PR ini tidak dapat diedit."
        )

    if request.method == "POST":
        form = PurchaseRequestForm(
            request.POST,
            instance=purchase_request,
        )
        formset = PurchaseRequestItemFormSet(
            request.POST,
            instance=purchase_request,
        )

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()

            return redirect("requisitions:pr_list")
    else:
        form = PurchaseRequestForm(
            instance=purchase_request,
        )
        formset = PurchaseRequestItemFormSet(
            instance=purchase_request,
        )

    return render(
        request,
        "requisitions/pr_form.html",
        {
            "form": form,
            "formset": formset,
            "purchase_request": purchase_request,
            "is_edit": True,
        },
    )


@login_required
@require_POST
def pr_submit(request, pk):
    if request.user.role != "REQUESTER":
        return HttpResponseForbidden(
            "Hanya Requester yang dapat mengirim PR."
        )

    with transaction.atomic():
        purchase_request = (
            PurchaseRequest.objects
            .select_for_update()
            .filter(
                pk=pk,
                requester=request.user,
            )
            .first()
        )

        if purchase_request is None:
            return HttpResponseForbidden(
                "PR tidak ditemukan atau bukan milik Anda."
            )

        allowed_statuses = [
            PurchaseRequest.Status.DRAFT,
            PurchaseRequest.Status.REVISION_REQUIRED,
        ]

        if purchase_request.status not in allowed_statuses:
            return redirect("requisitions:pr_list")

        if not purchase_request.items.exists():
            return redirect("requisitions:pr_list")

        purchase_request.status = (
            PurchaseRequest.Status.SUBMITTED
        )
        purchase_request.save(update_fields=["status", "updated_at"])

    return redirect("requisitions:pr_list")


@login_required
def approval_list(request):
    if request.user.role != "APPROVER":
        return HttpResponseForbidden(
            "Anda tidak memiliki akses ke halaman persetujuan."
        )

    purchase_requests = PurchaseRequest.objects.filter(
        status=PurchaseRequest.Status.SUBMITTED
    ).select_related("requester").order_by("created_at")

    return render(
        request,
        "requisitions/approval_list.html",
        {"purchase_requests": purchase_requests},
    )

@login_required
def approval_detail(request, pk):
    if request.user.role != "APPROVER":
        return HttpResponseForbidden(
            "Anda tidak memiliki akses ke halaman ini."
        )

    purchase_request = get_object_or_404(
        PurchaseRequest.objects.select_related("requester"),
        pk=pk,
        status=PurchaseRequest.Status.SUBMITTED,
    )

    histories = purchase_request.approval_histories.select_related(
        "approver"
    )

    if request.method == "POST":
        form = PRApprovalForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                purchase_request = get_object_or_404(
                    PurchaseRequest.objects.select_for_update(),
                    pk=pk,
                    status=PurchaseRequest.Status.SUBMITTED,
                )

                decision = form.cleaned_data["decision"]
                comments = form.cleaned_data["comments"]

                PRApprovalHistory.objects.create(
                    purchase_request=purchase_request,
                    approver=request.user,
                    decision=decision,
                    comments=comments,
                )

                purchase_request.status = decision
                purchase_request.save(
                    update_fields=["status", "updated_at"]
                )

            return redirect("requisitions:approval_list")
    else:
        form = PRApprovalForm()

    return render(
        request,
        "requisitions/approval_detail.html",
        {
            "purchase_request": purchase_request,
            "form": form,
            "histories": histories,
        },
    )


@login_required
def vendor_list(request):
    if request.user.role != "PROCUREMENT_OFFICER":
        return HttpResponseForbidden(
            "Hanya Procurement Officer yang dapat mengakses halaman vendor."
        )

    vendors = Vendor.objects.order_by("name")

    return render(
        request,
        "requisitions/vendor_list.html",
        {"vendors": vendors},
    )

@login_required
def vendor_create(request):
    if request.user.role != "PROCUREMENT_OFFICER":
        return HttpResponseForbidden(
            "Hanya Procurement Officer yang dapat menambahkan vendor."
        )

    if request.method == "POST":
        form = VendorForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("requisitions:vendor_list")
    else:
        form = VendorForm()

    return render(
        request,
        "requisitions/vendor_form.html",
        {"form": form},
    )

@login_required
def procurement_pr_list(request):
    if request.user.role != "PROCUREMENT_OFFICER":
        return HttpResponseForbidden(
            "Hanya Procurement Officer yang dapat mengakses halaman ini."
        )

    purchase_requests = PurchaseRequest.objects.filter(
        status=PurchaseRequest.Status.APPROVED
    ).select_related("requester").order_by("-updated_at")

    return render(
        request,
        "requisitions/procurement_pr_list.html",
        {"purchase_requests": purchase_requests},
    )


@login_required
def procurement_pr_detail(request, pk):
    if request.user.role != "PROCUREMENT_OFFICER":
        return HttpResponseForbidden(
            "Hanya Procurement Officer yang dapat mengakses halaman ini."
        )

    purchase_request = get_object_or_404(
        PurchaseRequest.objects.prefetch_related("items"),
        pk=pk,
        status=PurchaseRequest.Status.APPROVED,
    )

    if request.method == "POST":
        form = VendorInvitationForm(request.POST)

        if form.is_valid():
            invitation = form.save(commit=False)
            invitation.purchase_request = purchase_request

            try:
                with transaction.atomic():
                    invitation.save()
            except IntegrityError:
                form.add_error(
                    "vendor",
                    "Vendor ini sudah diundang untuk PR tersebut.",
                )
            else:
                messages.success(
                    request,
                    f"Undangan untuk {invitation.vendor.name} berhasil dicatat.",
                )
                return redirect(
                    "requisitions:procurement_pr_detail",
                    pk=purchase_request.pk,
                )
    else:
        form = VendorInvitationForm()

    invitations = purchase_request.vendor_invitations.select_related(
        "vendor"
    ).prefetch_related("quotation").order_by("-invited_at")

    return render(
        request,
        "requisitions/procurement_pr_detail.html",
        {
            "purchase_request": purchase_request,
            "form": form,
            "invitations": invitations,
        },
    )
    
@login_required
def quotation_create(request, invitation_id):
    if request.user.role != "PROCUREMENT_OFFICER":
        return HttpResponseForbidden(
            "Hanya Procurement Officer yang dapat mencatat quotation."
        )

    invitation = get_object_or_404(
        VendorInvitation.objects.select_related(
            "purchase_request",
            "vendor",
        ),
        pk=invitation_id,
        purchase_request__status=PurchaseRequest.Status.APPROVED,
    )

    if hasattr(invitation, "quotation"):
        return redirect(
            "requisitions:procurement_pr_detail",
            pk=invitation.purchase_request_id,
        )

    if request.method == "POST":
        form = QuotationForm(request.POST)

        if form.is_valid():
            quotation = form.save(commit=False)
            quotation.invitation = invitation

            try:
                with transaction.atomic():
                    quotation.save()
                    invitation.status = VendorInvitation.Status.RESPONDED
                    invitation.save(update_fields=["status"])
            except IntegrityError:
                form.add_error(
                    None,
                    "Quotation untuk undangan ini sudah tercatat.",
                )
            else:
                messages.success(
                    request,
                    "Quotation berhasil dicatat.",
                )
                return redirect(
                    "requisitions:procurement_pr_detail",
                    pk=invitation.purchase_request_id,
                )
    else:
        form = QuotationForm()

    return render(
        request,
        "requisitions/quotation_form.html",
        {
            "form": form,
            "invitation": invitation,
        },
    )

@login_required
def quotation_comparison(request, pk):
    if request.user.role != "PROCUREMENT_OFFICER":
        return HttpResponseForbidden(
            "Hanya Procurement Officer yang dapat membandingkan quotation."
        )

    purchase_request = get_object_or_404(
        PurchaseRequest,
        pk=pk,
        status=PurchaseRequest.Status.APPROVED,
    )

    quotations = (
        Quotation.objects.filter(
            invitation__purchase_request=purchase_request,
            invitation__status=VendorInvitation.Status.RESPONDED,
        )
        .select_related("invitation__vendor")
        .order_by("total_price")
    )

    # Cari pengajuan revisi milik Procurement Officer yang login.
    revision_selection = (
        VendorSelection.objects.filter(
            purchase_request=purchase_request,
            submitted_by=request.user,
            status=VendorSelection.Status.REVISION_REQUIRED,
        )
        .order_by("-submitted_at")
        .first()
    )

    # Cek apakah masih ada pengajuan yang menunggu keputusan Manager.
    pending_selection = VendorSelection.objects.filter(
        purchase_request=purchase_request,
        status=VendorSelection.Status.PENDING,
    ).exists()

    # Cek apakah pemilihan vendor untuk PR ini sudah disetujui.
    approved_selection = VendorSelection.objects.filter(
        purchase_request=purchase_request,
        status=VendorSelection.Status.APPROVED,
    ).exists()

    initial_data = {}

    if revision_selection:
        initial_data = {
            "quotation": revision_selection.quotation_id,
            "selection_reason": revision_selection.selection_reason,
        }

    form = VendorSelectionForm(
        request.POST or None,
        purchase_request=purchase_request,
        initial=initial_data,
    )

    if request.method == "POST" and form.is_valid():
        quotation = form.cleaned_data["quotation"]

        # Pastikan quotation benar-benar milik PR ini.
        if quotation.invitation.purchase_request_id != purchase_request.pk:
            return HttpResponseForbidden(
                "Quotation tidak sesuai dengan PR."
            )

        if approved_selection:
            messages.warning(
                request,
                "Pemilihan vendor untuk PR ini sudah disetujui Manager. "
                "Pengajuan baru tidak dapat dilakukan.",
            )

        elif pending_selection:
            messages.warning(
                request,
                "Masih ada rekomendasi yang menunggu keputusan Manager.",
            )

        else:
            with transaction.atomic():
                if revision_selection:
                    # Perbarui pengajuan yang diminta revisi.
                    selection = get_object_or_404(
                        VendorSelection.objects.select_for_update(),
                        pk=revision_selection.pk,
                        submitted_by=request.user,
                        status=VendorSelection.Status.REVISION_REQUIRED,
                    )

                    selection.quotation = quotation
                    selection.selection_reason = form.cleaned_data[
                        "selection_reason"
                    ]
                    selection.status = VendorSelection.Status.PENDING
                    selection.decided_by = None
                    selection.decided_at = None
                    selection.submitted_at = timezone.now()

                    # Pertahankan komentar revisi dari Manager.
                    selection.save(
                        update_fields=[
                            "quotation",
                            "selection_reason",
                            "status",
                            "decided_by",
                            "decided_at",
                            "submitted_at",
                        ]
                    )

                    success_message = (
                        "Rekomendasi hasil revisi berhasil diajukan "
                        "kembali kepada Manager."
                    )

                else:
                    # Buat pengajuan baru jika belum ada revisi.
                    VendorSelection.objects.create(
                        purchase_request=purchase_request,
                        quotation=quotation,
                        submitted_by=request.user,
                        selection_reason=form.cleaned_data[
                            "selection_reason"
                        ],
                    )

                    success_message = (
                        "Rekomendasi vendor berhasil diajukan kepada Manager."
                    )

            messages.success(request, success_message)

            return redirect(
                "requisitions:quotation_comparison",
                pk=pk,
            )

    return render(
        request,
        "requisitions/quotation_comparison.html",
        {
            "purchase_request": purchase_request,
            "quotations": quotations,
            "form": form,
            "pending_selection": pending_selection,
            "approved_selection": approved_selection,
            "revision_selection": revision_selection,
        },
    )

@login_required
def manager_dashboard(request):
    if request.user.role != "PROCUREMENT_MANAGER":
        return HttpResponseForbidden(
            "Hanya Procurement Manager yang dapat mengakses halaman ini."
        )

    selections = VendorSelection.objects.filter(
        status=VendorSelection.Status.PENDING
    ).select_related(
        "purchase_request",
        "quotation__invitation__vendor",
        "submitted_by",
    )

    return render(
        request,
        "requisitions/manager_dashboard.html",
        {"selections": selections},
    )




@login_required
def vendor_selection_decide(request, pk):
    if request.user.role != "PROCUREMENT_MANAGER":
        return HttpResponseForbidden(
            "Hanya Procurement Manager yang dapat mengambil keputusan."
        )

    selection = get_object_or_404(
        VendorSelection.objects.select_related(
            "purchase_request",
            "quotation__invitation__vendor",
        ),
        pk=pk,
        status=VendorSelection.Status.PENDING,
    )

    # Ambil seluruh quotation yang diterima untuk PR yang sama.
    quotations = (
        Quotation.objects.filter(
            invitation__purchase_request=selection.purchase_request,
            invitation__status=VendorInvitation.Status.RESPONDED,
        )
        .select_related("invitation__vendor")
        .order_by("total_price")
    )

    if request.method == "POST":
        form = VendorSelectionDecisionForm(request.POST)

        if form.is_valid():
            decision = form.cleaned_data["decision"]
            comments = form.cleaned_data["manager_comments"].strip()

            if (
                decision in [
                    VendorSelection.Status.REVISION_REQUIRED,
                    VendorSelection.Status.REJECTED,
                ]
                and not comments
            ):
                form.add_error(
                    "manager_comments",
                    "Komentar wajib diisi jika meminta revisi atau menolak pengajuan.",
                )
            else:
                with transaction.atomic():
                    selection = get_object_or_404(
                        VendorSelection.objects.select_for_update(),
                        pk=pk,
                        status=VendorSelection.Status.PENDING,
                    )

                    selection.status = decision
                    selection.decided_by = request.user
                    selection.manager_comments = comments
                    selection.decided_at = timezone.now()

                    selection.save(
                        update_fields=[
                            "status",
                            "decided_by",
                            "manager_comments",
                            "decided_at",
                        ]
                    )

                messages.success(
                    request,
                    "Keputusan pemilihan vendor berhasil disimpan.",
                )
                return redirect("requisitions:manager_dashboard")
    else:
        form = VendorSelectionDecisionForm()

    return render(
        request,
        "requisitions/vendor_selection_decide.html",
        {
            "selection": selection,
            "form": form,
            "quotations": quotations,
        },
    )

@login_required
def my_vendor_selections(request):
    if request.user.role != "PROCUREMENT_OFFICER":
        return HttpResponseForbidden(
            "Hanya Procurement Officer yang dapat mengakses halaman ini."
        )

    selections = VendorSelection.objects.filter(
        submitted_by=request.user
    ).select_related(
        "purchase_request",
        "quotation__invitation__vendor",
        "decided_by",
    ).order_by("-submitted_at")

    return render(
        request,
        "requisitions/my_vendor_selections.html",
        {"selections": selections},
    )

@login_required
def purchase_order_list(request):
    if request.user.role != "PROCUREMENT_OFFICER":
        return HttpResponseForbidden(
            "Hanya Procurement Officer yang dapat mengakses daftar PO."
        )

    purchase_orders = (
        PurchaseOrder.objects
        .select_related(
            "vendor_selection__purchase_request",
            "vendor_selection__quotation__invitation__vendor",
            "created_by",
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "requisitions/purchase_order_list.html",
        {"purchase_orders": purchase_orders},
    )


@login_required
def purchase_order_create(request, selection_pk):
    if request.user.role != "PROCUREMENT_OFFICER":
        return HttpResponseForbidden(
            "Hanya Procurement Officer yang dapat membuat PO."
        )

    selection = get_object_or_404(
        VendorSelection.objects.select_related(
            "purchase_request",
            "quotation__invitation__vendor",
        ),
        pk=selection_pk,
        status=VendorSelection.Status.APPROVED,
    )

    # Satu pemilihan vendor hanya boleh menghasilkan satu PO.
    if PurchaseOrder.objects.filter(
        vendor_selection=selection
    ).exists():
        messages.warning(
            request,
            "Purchase Order untuk pemilihan vendor ini sudah tersedia.",
        )
        return redirect("requisitions:purchase_order_list")

    form = PurchaseOrderForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            # Cek ulang agar tidak membuat PO ganda jika ada request bersamaan.
            selection = get_object_or_404(
                VendorSelection.objects.select_for_update(),
                pk=selection_pk,
                status=VendorSelection.Status.APPROVED,
            )

            if PurchaseOrder.objects.filter(
                vendor_selection=selection
            ).exists():
                messages.warning(
                    request,
                    "Purchase Order untuk pemilihan vendor ini sudah tersedia.",
                )
                return redirect("requisitions:purchase_order_list")

            purchase_order = form.save(commit=False)
            purchase_order.vendor_selection = selection
            purchase_order.created_by = request.user
            purchase_order.save()

            # Salin item PR ke detail PO.
            pr_items = selection.purchase_request.items.all()

            PurchaseOrderItem.objects.bulk_create([
                PurchaseOrderItem(
                    purchase_order=purchase_order,
                    purchase_request_item=item,
                    item_name=item.item_name,
                    specification=item.specification,
                    quantity=item.quantity,
                    unit=item.unit,
                )
                for item in pr_items
            ])

        messages.success(
            request,
            f"Purchase Order {purchase_order.po_number} berhasil dibuat.",
        )
        return redirect("requisitions:purchase_order_list")

    return render(
        request,
        "requisitions/purchase_order_form.html",
        {
            "form": form,
            "selection": selection,
        },
    )
    
@login_required
def purchase_order_detail(request, pk):
    if request.user.role != "PROCUREMENT_OFFICER":
        return HttpResponseForbidden(
            "Hanya Procurement Officer yang dapat melihat detail PO."
        )

    purchase_order = get_object_or_404(
        PurchaseOrder.objects.select_related(
            "vendor_selection__purchase_request",
            "vendor_selection__quotation__invitation__vendor",
            "created_by",
        ).prefetch_related("items"),
        pk=pk,
    )

    return render(
        request,
        "requisitions/purchase_order_detail.html",
        {"purchase_order": purchase_order},
    )

@login_required
def purchase_order_issue(request, pk):
    if request.user.role != "PROCUREMENT_OFFICER":
        return HttpResponseForbidden(
            "Hanya Procurement Officer yang dapat menerbitkan PO."
        )

    if request.method != "POST":
        return HttpResponseForbidden(
            "Penerbitan PO harus dilakukan melalui formulir POST."
        )

    with transaction.atomic():
        purchase_order = get_object_or_404(
            PurchaseOrder.objects.select_for_update(),
            pk=pk,
        )

        if purchase_order.status != PurchaseOrder.Status.DRAFT:
            messages.warning(
                request,
                "Hanya PO berstatus Draft yang dapat diterbitkan.",
            )
            return redirect(
                "requisitions:purchase_order_detail",
                pk=purchase_order.pk,
            )

        if not purchase_order.items.exists():
            messages.error(
                request,
                "PO tidak dapat diterbitkan karena belum memiliki item.",
            )
            return redirect(
                "requisitions:purchase_order_detail",
                pk=purchase_order.pk,
            )

        purchase_order.status = PurchaseOrder.Status.ISSUED
        purchase_order.save(update_fields=["status", "updated_at"])

    messages.success(
        request,
        f"Purchase Order {purchase_order.po_number} berhasil diterbitkan.",
    )
    return redirect(
        "requisitions:purchase_order_detail",
        pk=purchase_order.pk,
    )
    
@login_required
def goods_receipt_po_list(request):
    if request.user.role != "PROCUREMENT_OFFICER":
        return HttpResponseForbidden(
            "Hanya Procurement Officer yang dapat mengakses penerimaan barang."
        )

    purchase_orders = (
        PurchaseOrder.objects.filter(
            status__in=[
                PurchaseOrder.Status.ISSUED,
                PurchaseOrder.Status.PARTIALLY_RECEIVED,
            ]
        )
        .select_related(
            "vendor_selection__purchase_request",
            "vendor_selection__quotation__invitation__vendor",
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "requisitions/goods_receipt_po_list.html",
        {"purchase_orders": purchase_orders},
    )
    
@login_required
def goods_receipt_create(request, po_pk):
    if request.user.role != "PROCUREMENT_OFFICER":
        return HttpResponseForbidden(
            "Hanya Procurement Officer yang dapat mencatat penerimaan barang."
        )

    purchase_order = get_object_or_404(
        PurchaseOrder.objects.select_related(
            "vendor_selection__purchase_request",
            "vendor_selection__quotation__invitation__vendor",
        ),
        pk=po_pk,
        status__in=[
            PurchaseOrder.Status.ISSUED,
            PurchaseOrder.Status.PARTIALLY_RECEIVED,
        ],
    )

    po_items = list(
        PurchaseOrderItem.objects.filter(
            purchase_order=purchase_order
        ).order_by("id")
    )

    if not po_items:
        messages.error(request, "PO ini belum memiliki item.")
        return redirect("requisitions:goods_receipt_po_list")

    initial_items = [
        {"purchase_order_item_id": item.pk}
        for item in po_items
    ]

    if request.method == "POST":
        form = GoodsReceiptForm(request.POST)
        formset = GoodsReceiptItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                # Kunci PO untuk mengurangi risiko penerimaan bersamaan.
                locked_po = get_object_or_404(
                    PurchaseOrder.objects.select_for_update(),
                    pk=po_pk,
                    status=PurchaseOrder.Status.ISSUED,
                )

                locked_items = {
                    item.pk: item
                    for item in PurchaseOrderItem.objects.select_for_update()
                    .filter(purchase_order=locked_po)
                }

                received_quantities = {
                    row["purchase_order_item_id"]: row["quantity"]
                    for row in GoodsReceiptItem.objects.filter(
                        purchase_order_item__purchase_order=locked_po
                    )
                    .values("purchase_order_item_id")
                    .annotate(quantity=Sum("quantity_received"))
                }

                submitted_ids = []
                receipt_lines = []
                errors = []

                for item_form in formset:
                    data = item_form.cleaned_data

                    item_id = data["purchase_order_item_id"]
                    quantity = data["quantity_received"]

                    if item_id not in locked_items:
                        errors.append(
                            "Terdapat item yang tidak sesuai dengan PO."
                        )
                        continue

                    if item_id in submitted_ids:
                        errors.append(
                            "Item PO tidak boleh dicatat lebih dari sekali "
                            "dalam satu Goods Receipt."
                        )
                        continue

                    submitted_ids.append(item_id)

                    po_item = locked_items[item_id]
                    already_received = received_quantities.get(item_id, 0)
                    remaining = po_item.quantity - already_received

                    if quantity > remaining:
                        errors.append(
                            f"{po_item.item_name}: jumlah diterima "
                            f"{quantity}, sedangkan sisa pesanan hanya "
                            f"{remaining}."
                        )
                        continue

                    receipt_lines.append(
                        GoodsReceiptItem(
                            purchase_order_item=po_item,
                            quantity_received=quantity,
                            condition=data["condition"],
                            notes=data["notes"],
                        )
                    )

                if not submitted_ids:
                    errors.append(
                        "Masukkan setidaknya satu item penerimaan."
                    )

                if errors:
                    for error in errors:
                        messages.error(request, error)
                else:
                    receipt = form.save(commit=False)
                    receipt.purchase_order = locked_po
                    receipt.received_by = request.user
                    receipt.status = GoodsReceipt.Status.PARTIAL
                    receipt.save()

                    for line in receipt_lines:
                        line.goods_receipt = receipt

                    GoodsReceiptItem.objects.bulk_create(receipt_lines)

                    # Periksa apakah semua kuantitas PO sudah diterima.
                    new_totals = dict(received_quantities)

                    for line in receipt_lines:
                        new_totals[line.purchase_order_item_id] = (
                            new_totals.get(
                                line.purchase_order_item_id, 0
                            ) + line.quantity_received
                        )

                    all_received = all(
                        new_totals.get(item.pk, 0) >= item.quantity
                        for item in locked_items.values()
                    )

                    receipt.status = (
                        GoodsReceipt.Status.COMPLETED
                        if all_received
                        else GoodsReceipt.Status.PARTIAL
                    )
                    receipt.save(update_fields=["status"])

                    locked_po.status = (
                        PurchaseOrder.Status.COMPLETED
                        if all_received
                        else PurchaseOrder.Status.PARTIALLY_RECEIVED
                    )
                    locked_po.save(update_fields=["status", "updated_at"])

                    messages.success(
                        request,
                        f"Goods Receipt {receipt.gr_number} berhasil disimpan.",
                    )
                    return redirect(
                        "requisitions:goods_receipt_detail",
                        gr_pk=receipt.pk,
                    )

    else:
        form = GoodsReceiptForm(
            initial={"receipt_date": timezone.localdate()}
        )
        formset = GoodsReceiptItemFormSet(
            initial=initial_items
        )

    # Sisa kuantitas ditampilkan kepada pengguna.
    received_quantities = {
        row["purchase_order_item_id"]: row["quantity"]
        for row in GoodsReceiptItem.objects.filter(
            purchase_order_item__purchase_order=purchase_order
        )
        .values("purchase_order_item_id")
        .annotate(quantity=Sum("quantity_received"))
    }

    item_rows = [
        {
            "item": item,
            "received": received_quantities.get(item.pk, 0),
            "remaining": item.quantity
            - received_quantities.get(item.pk, 0),
        }
        for item in po_items
    ]

    return render(
        request,
        "requisitions/goods_receipt_form.html",
        {
            "purchase_order": purchase_order,
            "form": form,
            "formset": formset,
            "item_rows": item_rows,
        },
    )
    
@login_required
def goods_receipt_detail(request, gr_pk):
    if request.user.role != "PROCUREMENT_OFFICER":
        return HttpResponseForbidden(
            "Hanya Procurement Officer yang dapat melihat detail Goods Receipt."
        )

    goods_receipt = get_object_or_404(
        GoodsReceipt.objects.select_related(
            "purchase_order",
            "received_by",
            "purchase_order__vendor_selection__purchase_request",
            "purchase_order__vendor_selection__quotation__invitation__vendor",
        ).prefetch_related(
            "items__purchase_order_item"
        ),
        pk=gr_pk,
    )

    return render(
        request,
        "requisitions/goods_receipt_detail.html",
        {"goods_receipt": goods_receipt},
    )

@login_required
def goods_receipt_list(request):
    if request.user.role != "PROCUREMENT_OFFICER":
        return HttpResponseForbidden(
            "Hanya Procurement Officer yang dapat melihat riwayat Goods Receipt."
        )

    goods_receipts = (
        GoodsReceipt.objects.select_related(
            "purchase_order",
            "received_by",
            "purchase_order__vendor_selection__purchase_request",
            "purchase_order__vendor_selection__quotation__invitation__vendor",
        )
        .order_by("-receipt_date", "-created_at")
    )

    return render(
        request,
        "requisitions/goods_receipt_list.html",
        {"goods_receipts": goods_receipts},
    )