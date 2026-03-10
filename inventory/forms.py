from django import forms
from .models import PurchaseOrderType, PurchaseOrderStatus, PurchaseOrderHeader, PurchaseOrderItem, PurchaseOrderHeader,Inventory
from catalog.models import Product
from core.forms import VendorBaseModelForm, PurchaseOrderBaseModelForm, validate_name, validate_code, CodeReadonlyOnEditForm
import re
from django.core.exceptions import ValidationError

class PurchaseOrderTypeModelForm(PurchaseOrderBaseModelForm, CodeReadonlyOnEditForm):
    required_css_class = 'required'
    name = forms.CharField(max_length=100)
    code = forms.CharField(max_length=20)

    # def clean_name(self):
    #     name = self.cleaned_data.get('name', '').strip()
    #     # Allow only alphabets and spaces
    #     if not re.match(r'^[A-Za-z\s]+$', name):
    #         raise forms.ValidationError("Name must contain only alphabets (A–Z, a–z).")
    #     return name

    # def clean_code(self):
    #     code = self.cleaned_data.get('code', '').strip()

    #     # # Must be alphanumeric (letters + numbers)
    #     # if not re.match(r'^[A-Za-z0-9]+$', code):
    #     #     raise forms.ValidationError("Code must be alphanumeric (letters and numbers only).")

    #     # Should not start with a number
    #     if re.match(r'^[0-9]', code):
    #         raise forms.ValidationError("Code should not start with a number.")

    #     return code

    class Meta:
        model = PurchaseOrderType
        exclude=('created_user', 'updated_user')

class  PurchaseOrderTypeStatusModelForm(PurchaseOrderBaseModelForm, CodeReadonlyOnEditForm):
    required_css_class = 'required'
    name = forms.CharField(max_length=100)
    code = forms.CharField(max_length=20)

    # def clean_name(self):
    #     name = self.cleaned_data.get('name', '').strip()
    #     # Allow only alphabets and spaces
    #     if not re.match(r'^[A-Za-z\s]+$', name):
    #         raise forms.ValidationError("Name must contain only alphabets (A–Z, a–z).")
    #     return name

    # def clean_code(self):
    #     code = self.cleaned_data.get('code', '').strip()

    #     # Must be alphanumeric (letters + numbers)
    #     if not re.match(r'^[A-Za-z0-9]+$', code):
    #         raise forms.ValidationError("Code must be alphanumeric (letters and numbers only).")

    #     # Should not start with a number
    #     if re.match(r'^[0-9]', code):
    #         raise forms.ValidationError("Code should not start with a number.")

    #     return code


    class Meta:
        model = PurchaseOrderStatus
        exclude=('created_user', 'updated_user')

class  PurchaseOrderHeaderModelForm(PurchaseOrderBaseModelForm):
    required_css_class = 'required'

    class Meta:
        model = PurchaseOrderHeader
        exclude=('created_user', 'updated_user')

class  PurchaseOrderItemModelForm(PurchaseOrderBaseModelForm):
    required_css_class = 'required'

    class Meta:
        model = PurchaseOrderItem
        exclude=('created_user', 'updated_user')

class PONumberForm(forms.Form):
    po_number = forms.CharField(label="PO Number", max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "PO Number"}))

class GoodsReceiverModelForm(PurchaseOrderBaseModelForm):
    code = forms.CharField(
        required=False,
        label="PO Number",
        widget=forms.HiddenInput()
    )

    PurchaseOrderHeader = forms.ChoiceField(
     # choices=[(each.code, each.project_name) for each in ProjectHeader.objects.all()],
        choices=[],   # empty initially
        label="PO Number",
        widget=forms.Select(attrs={"class": "form-control"})
    )

    required_css_class = 'required'

    class Meta:
        model = PurchaseOrderHeader
        exclude=('created_user', 'updated_user','vendor','po_date','po_requested_by','po_status','requested_delivery_date','header_notes','slug','status','description','search_keywords','po_type')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['PurchaseOrderHeader'].choices = [
            ("", "Select PO Number")
        ] + [
            (po.code, po.code)
            for po in PurchaseOrderHeader.objects.only("code")
        ]

class QualityManagementModelForm(PurchaseOrderBaseModelForm):
    code = forms.CharField(
        required=False,
        label="PO Number",
        widget=forms.HiddenInput()
    )

    PurchaseOrderHeader = forms.ChoiceField(
     # choices=[(each.code, each.project_name) for each in ProjectHeader.objects.all()],
        choices=[],   # empty initially
        label="PO Number",
        widget=forms.Select(attrs={"class": "form-control"})
    )

    required_css_class = 'required'

    class Meta:
        model = PurchaseOrderHeader
        exclude=('created_user', 'updated_user','vendor','po_date','po_requested_by','po_status','requested_delivery_date','header_notes','slug','status','description','search_keywords','po_type')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['PurchaseOrderHeader'].choices = [
            ("", "Select PO Number")
        ] + [
            (po.code, po.code)
            for po in PurchaseOrderHeader.objects.only("code")
        ]

class POReceiveLineForm(forms.Form):
    item_id = forms.IntegerField(widget=forms.HiddenInput())
    qty_being_received = forms.DecimalField(
        max_digits=12, decimal_places=2, min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"})
    )

    def __init__(self, *args, po_item=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.po_item = po_item
        if po_item:
            self.fields["item_id"].initial = po_item.id
            self.fields["qty_being_received"].widget.attrs.update({
                "max": po_item.yet_to_be_received,
                "data-already-received": po_item.already_received_qty,
                "data-ordered": po_item.quantity,
            })

    def clean_qty_being_received(self):
        qty = self.cleaned_data["qty_being_received"]
        po_item = self.po_item

        if not po_item:
            return qty

        if qty > po_item.yet_to_be_received:
            raise ValidationError("Quantity cannot exceed 'Yet to be Received'.")
        if po_item.already_received_qty + qty > po_item.quantity:
            raise ValidationError("Total received cannot exceed ordered quantity.")
        return qty

class POReceiveForm(forms.Form):
    item_id = forms.IntegerField(widget=forms.HiddenInput())
    qty_being_received = forms.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=True,
        widget=forms.NumberInput(attrs={"class": "form-control qty-being-received"})
    )

    def __init__(self, *args, po_item=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.po_item = po_item  # attach model instance

        if po_item:
            self.fields["qty_being_received"].widget.attrs.update({
                "max": po_item.yet_to_be_received,   # HTML max validation
                "step": "0.01",
                "data-po-qty": po_item.quantity,
                "data-already-received": po_item.already_received_qty,
                "data-yet-to-receive": po_item.yet_to_be_received,
            })
            self.fields["item_id"].initial = po_item.id

    def clean_qty_being_received(self):
        qty = self.cleaned_data.get("qty_being_received")
        if not self.po_item:
            return qty

        already_received = self.po_item.already_received_qty
        po_qty = self.po_item.quantity
        yet_to_receive = self.po_item.yet_to_be_received

        # ✅ Validation rules
        if qty < 0:
            raise ValidationError("Quantity must be positive.")
        if qty > yet_to_receive:
            raise ValidationError("Quantity cannot exceed 'Yet to be Received'.")
        if already_received + qty > po_qty:
            raise ValidationError("Total received cannot exceed Ordered Quantity.")

        return qty

class GoodsSearchForm(forms.Form):
    q = forms.CharField(
        label="Search Keyword",
        required=True,
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Search Keyword"
            }
        ),
        help_text="Enter keywords separated by commas (e.g., product, location, sub-location)."
    )
    GROUP_BY_CHOICES = (
        ("product", "Product"),
        ("location", "Location"),
    )
    group_by = forms.ChoiceField(
        choices=GROUP_BY_CHOICES,
        widget=forms.RadioSelect,
        initial="product",
        label="Group By"
    )


class InventorySearchModelForm(PurchaseOrderBaseModelForm):
    required_css_class = 'required'
    search_query= forms.CharField(
        label="Search Keyword",
        required=True,
        max_length=255,
        help_text="Enter keywords separated by commas (e.g., product, location, sub-location)."
    )
    GROUP_BY_CHOICES = (
        ("product", "Product"),
        ("location", "Location"),
    )
    group_by = forms.ChoiceField(
        choices=GROUP_BY_CHOICES,
        widget=forms.RadioSelect,
        initial="product",
        label="Group By"
    )

    class Meta:
        model = Inventory
        exclude=('created_user', 'updated_user','inventory_type','uom','location','sub_location','quantity','product','status')
