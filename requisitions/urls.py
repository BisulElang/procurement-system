from django.urls import path
from . import views

app_name = "requisitions"

urlpatterns = [
    path("", views.pr_list, name="pr_list"),
    path("create/", views.pr_create, name="pr_create"),
    path("<int:pk>/submit/", views.pr_submit, name="pr_submit"),
    path(
    "pr/<int:pk>/edit/",
    views.pr_edit,
    name="pr_edit",
    ),
    path(
        "approvals/",
        views.approval_list,
        name="approval_list",
    ),
    path(
        "approvals/<int:pk>/",
        views.approval_detail,
        name="approval_detail",
    ),
    path("vendors/", views.vendor_list, name="vendor_list"),
    path("vendors/create/", views.vendor_create, name="vendor_create"),
    path(
    "procurement/purchase-requests/",
    views.procurement_pr_list,
    name="procurement_pr_list",
    ),
    path(
    "procurement/purchase-requests/<int:pk>/",
    views.procurement_pr_detail,
    name="procurement_pr_detail",
    ),
    path(
    "procurement/quotations/create/<int:invitation_id>/",
    views.quotation_create,
    name="quotation_create",
    ),
    path(
        "procurement/purchase-requests/<int:pk>/quotations/",
        views.quotation_comparison,
        name="quotation_comparison",
    ),
    path(
        "manager/",
        views.manager_dashboard,
        name="manager_dashboard",
    ),
    path(
        "manager/vendor-selections/<int:pk>/",
        views.vendor_selection_decide,
        name="vendor_selection_decide",
    ),
    path(
        "procurement/vendor-selections/",
        views.my_vendor_selections,
        name="my_vendor_selections",
    ),
    path(
        "procurement/purchase-orders/",
        views.purchase_order_list,
        name="purchase_order_list",
    ),
    path(
        "procurement/vendor-selections/<int:selection_pk>/create-po/",
        views.purchase_order_create,
        name="purchase_order_create",
    ),
    path(
    "procurement/purchase-orders/<int:pk>/",
    views.purchase_order_detail,
    name="purchase_order_detail",
    ),
    path(
        "procurement/purchase-orders/<int:pk>/issue/",
        views.purchase_order_issue,
        name="purchase_order_issue",
    ),
    path(
    "procurement/goods-receipts/",
    views.goods_receipt_po_list,
    name="goods_receipt_po_list",
    ),
    path(
        "procurement/purchase-orders/<int:po_pk>/goods-receipts/create/",
        views.goods_receipt_create,
        name="goods_receipt_create",
    ),
    path(
    "procurement/goods-receipts/<int:gr_pk>/",
    views.goods_receipt_detail,
    name="goods_receipt_detail",
    ),
    path(
    "procurement/goods-receipts/history/",
    views.goods_receipt_list,
    name="goods_receipt_list",
    ),
]
