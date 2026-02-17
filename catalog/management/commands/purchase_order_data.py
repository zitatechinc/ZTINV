from django.core.management.base import BaseCommand
from inventory.models import (
    PurchaseOrderType, PurchaseOrderStatus
)

from accounts.models import User

po_types = [
    {"code": "PO_STD", "name": "Standard PO", "description": "One-time purchase of specific goods/services with defined terms."},
    {"code": "PO_PLN", "name": "Planned PO", "description": "Long-term planning; schedule releases issued later."},
    {"code": "PO_BLK", "name": "Blanket PO", "description": "Agreement for recurring purchases over time with a total value limit."},
    {"code": "PO_CON", "name": "Contract PO", "description": "Framework/outline agreement; sets pricing/terms for future orders."},
    {"code": "PO_REC", "name": "Recurring PO", "description": "For repetitive services (e.g., cleaning, utilities, subscriptions)."},
    {"code": "PO_CNS", "name": "Consignment PO", "description": "Supplier stocks at buyer’s site; payment when goods are consumed."},
    {"code": "PO_SRV", "name": "Service PO", "description": "For services (consulting, maintenance, IT support, etc.)."},
    {"code": "PO_SUB", "name": "Subcontracting PO", "description": "Buyer provides materials, supplier performs work and returns finished goods."},
    {"code": "PO_STK", "name": "Stock Transfer PO", "description": "Transfers of goods between company plants/warehouses."},
    {"code": "PO_TPY", "name": "Third-Party PO", "description": "Supplier delivers directly to the buyer’s customer (drop shipment)."},
    {"code": "PO_INT", "name": "Intercompany PO", "description": "Between two legal entities of the same company."},
    {"code": "PO_RSH", "name": "Emergency/Rush PO", "description": "For urgent or unplanned requirements."},
    {"code": "PO_STN", "name": "Standing PO", "description": "Open-ended, ongoing purchases with multiple invoices."}
]

# -------------------------------
# Purchase Order Statuses
# -------------------------------
po_status = [
    {"code": "STAT_DRF", "name": "Draft / In Progress", "description": "PO created but not yet submitted for approval."},
    {"code": "STAT_PND", "name": "Pending Approval", "description": "PO waiting for management or system approval."},
    {"code": "STAT_APR", "name": "Approved / Released", "description": "PO approved and communicated to supplier."},
    {"code": "STAT_SNT", "name": "Sent to Vendor", "description": "PO transmitted to supplier (via email, portal, EDI, etc.)."},
    {"code": "STAT_ACK", "name": "Acknowledged", "description": "Supplier has confirmed receipt/acceptance of PO."},
    {"code": "STAT_PRC", "name": "Partially Received", "description": "Some items/services delivered; balance pending."},
    {"code": "STAT_FRC", "name": "Fully Received", "description": "All items/services received as per PO."},
    {"code": "STAT_PIN", "name": "Partially Invoiced", "description": "Supplier has invoiced some of the order."},
    {"code": "STAT_FIN", "name": "Fully Invoiced", "description": "Entire PO has been invoiced."},
    {"code": "STAT_CLS", "name": "Closed / Completed", "description": "All deliveries and invoices matched, PO finalized."},
    {"code": "STAT_CNL", "name": "Canceled / Voided", "description": "PO canceled before completion."},
    {"code": "STAT_HLD", "name": "On Hold", "description": "Temporarily paused (budget, supplier issue, etc.)."},
{
  "code": "STAT_OPN",
  "name": "Open",
  "description": "PO submitted and awaiting approval or further action."
}
]


class Command(BaseCommand):
    help = "Inventory Data Insert"

    
    def handle(self, *args, **kwargs):
        user_obj = User.objects.filter(username='staff_user').first()
        for i, name in enumerate(po_types, start=1):
            PurchaseOrderType.objects.update_or_create(
                name=name['name'],
                code=name['code'],
                status=1,
                description=name['description'],
                created_user=user_obj,
                defaults={'code': name['code']}
            )

        for i, name in enumerate(po_status, start=1):
            PurchaseOrderStatus.objects.update_or_create(
                name=name['name'],
                status=1,
                code=name['code'],
                description=name['description'],
                created_user=user_obj,
                defaults={'code': name['code']}
            )
        
        self.stdout.write(self.style.SUCCESS("Inventory Master data setup complete!"))
