from django import forms
from .models import ProjectHeader, BOMHeader, ProjectComponent, BOMItem, BOMAttachments
from core.forms import PurchaseOrderBaseModelForm, CodeReadonlyOnEditForm, CatalogBaseModelForm,ProjectidReadonlyOnEditForm
from ims.models import BudgetAllocation
from django.db.models import Sum
from location.models import Location, SubLocation
from customer.models import Customer
from catalog.models import Product
from ims.models import Project  # Assuming this is the correct Project model


class ProjectHeaderModelForm(CatalogBaseModelForm, ProjectidReadonlyOnEditForm):
    class Meta:
        model = ProjectHeader
        exclude = ('created_user', 'updated_user', 'created_at', 'slug', 'item_status')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # -----------------------------------
        # ACTIVE FILTERING
        # -----------------------------------
        self.fields['customer'].queryset = Customer.objects.filter(status=1)
        self.fields['location'].queryset = Location.objects.filter(status=1)
        self.fields['sub_location'].queryset = SubLocation.objects.filter(status=1)

        # -----------------------------------
        # EXCLUDE ALREADY USED PROJECTS
        # -----------------------------------
        # used_projects = ProjectHeader.objects.values_list("project_id", flat=True)

        # self.fields['project'].queryset = Project.objects.exclude(
        #     id__in=used_projects
        # )

        used_projects = ProjectHeader.objects.values_list("project", flat=True)

        self.fields['project'].queryset = Project.objects.exclude(
            id__in=used_projects)

        # -----------------------------------
        # WHILE EDITING → include current project
        # -----------------------------------
        if self.instance.pk:
            if self.instance.customer:
                self.fields['customer'].queryset |= Customer.objects.filter(pk=self.instance.customer.pk)

            if self.instance.location:
                self.fields['location'].queryset |= Location.objects.filter(pk=self.instance.location.pk)

            if self.instance.sub_location:
                self.fields['sub_location'].queryset |= SubLocation.objects.filter(pk=self.instance.sub_location.pk)

            if self.instance.project:
                self.fields['project'].queryset |= Project.objects.filter(pk=self.instance.project.pk)

        # -----------------------------------
        # REMOVE DUPLICATES
        # -----------------------------------
        for field_name in ['customer', 'location', 'sub_location', 'project']:
            self.fields[field_name].queryset = self.fields[field_name].queryset.distinct()

# ---------------- ProjectComponent Form ----------------
class ProjectComponentModelForm(CatalogBaseModelForm, CodeReadonlyOnEditForm):
    class Meta:
        model = ProjectComponent
        exclude = ('code','project_id','project','created_user', 'updated_user', 'created_at',  'slug')

    def __init__(self, project_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_id = project_id

        # Active filtering for foreign keys
        self.fields['bom'].queryset = BOMHeader.objects.filter(status=1)
        self.fields['product'].queryset = Product.objects.filter(status=1)
        self.fields['service'].queryset = Product.objects.filter(status=1)

        # Include current instance even if inactive
        if self.instance.pk:
            if self.instance.bom:
                self.fields['bom'].queryset |= BOMHeader.objects.filter(pk=self.instance.bom.pk)
            if self.instance.product:
                self.fields['product'].queryset |= Product.objects.filter(pk=self.instance.product.pk)
            if self.instance.service:
                self.fields['service'].queryset |= Product.objects.filter(pk=self.instance.service.pk)

        # Map component_type -> field name
        field_map = {
            "BOM": "bom",
            "Product": "product",
            "Service": "service",
            "Miscellaneous": "miscellaneous_component",
        }
        
        # Determine current component_type
        component_type = None
        if self.data.get("component_type"):
            component_type = self.data.get("component_type")
        elif self.instance.pk:
            component_type = self.instance.component_type
        
        # Make all fields optional first
        for fname in field_map.values():
            if fname in self.fields:
                self.fields[fname].required = False

        # Make the correct field required
        if component_type in field_map and field_map[component_type] in self.fields:
            self.fields[field_map[component_type]].required = True

    def clean(self):
        cleaned_data = super().clean()

        project_header = self.project_id
        component_type = cleaned_data.get("component_type")
        bom = cleaned_data.get("bom")
        product = cleaned_data.get("product")
        service = cleaned_data.get("service")
        component_qty = cleaned_data.get("component_qty")
        component_cost = cleaned_data.get("component_cost")

        # ---------------------------------
        # Quantity & Cost validation
        # ---------------------------------
        if component_qty is not None and component_qty <= 0:
            self.add_error("component_qty", "Component quantity must be greater than 0.")

        if component_cost is not None and component_cost <= 0:
            self.add_error("component_cost", "Component cost must be greater than 0.")

        # ---------------------------------
        # PRODUCT uniqueness rules
        # ---------------------------------
        if component_type == "Product" and project_header and product:
            exists = (
                ProjectComponent.objects
                .filter(project=project_header, product=product)
                .exclude(pk=self.instance.pk)
                .exists()
            )
            if exists:
                self.add_error(
                    "product",
                    "This product is already added to this project."
                )

        # ---------------------------------
        # SERVICE uniqueness rules
        # ---------------------------------
        if component_type == "Service" and project_header and service:
            exists = (
                ProjectComponent.objects
                .filter(project=project_header, service=service)
                .exclude(pk=self.instance.pk)
                .exists()
            )
            if exists:
                self.add_error(
                    "service",
                    "This service is already added to this project."
                )

        # ---------------------------------
        # BOM uniqueness rules
        # ---------------------------------
        if component_type == "BOM" and project_header and bom:
            existing = (
                ProjectComponent.objects
                .filter(bom=bom)
                .exclude(pk=self.instance.pk)
                .first()
            )

            if existing:
                if existing.project == project_header:
                    self.add_error(
                        "bom",
                        "This BOM is already added to this project."
                    )
                else:
                    self.add_error(
                        "bom",
                        f"This BOM is already assigned to Project - {existing.project}. "
                        "A BOM can be assigned to only one project."
                    )

        # ---------------------------------
        # Budget validation
        # ---------------------------------
        if not project_header or component_cost is None:
            return cleaned_data

        project = project_header.project

        budget = BudgetAllocation.objects.filter(project=project).first()

        if not budget:
            self.add_error(
                "project",
                "No budget allocation found for this project."
            )
            return cleaned_data

        used_budget = (
            ProjectComponent.objects
            .filter(project__project=project)
            .exclude(pk=self.instance.pk)
            .aggregate(total=Sum("component_cost"))
            .get("total") or 0
        )

        total_after_save = used_budget + component_cost

        if total_after_save > budget.allocated_budget:
            self.add_error(
                "component_cost",
                f"Remaining budget: {int(budget.allocated_budget - used_budget)}"
            )

        return cleaned_data


# ---------------- BOMHeader Form ----------------
class BOMHeaderModelForm(CatalogBaseModelForm, CodeReadonlyOnEditForm):
    class Meta:
        model = BOMHeader
        exclude = ('created_user', 'updated_user', 'created_at',   'slug')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = ProjectHeader.objects.filter(status=1)
        if self.instance.pk and self.instance.project:
            self.fields['project'].queryset |= ProjectHeader.objects.filter(pk=self.instance.project.pk)
            self.fields['project'].queryset = self.fields['project'].queryset.distinct()

# ---------------- BOMItem Form ----------------
class BOMItemModelForm(CatalogBaseModelForm, CodeReadonlyOnEditForm):
    class Meta:
        model = BOMItem
        exclude = ('code', 'slug', 'created_user', 'updated_user', 'created_at')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Base querysets for active objects
        self.fields['product'].queryset = Product.objects.filter(status=1)
        self.fields['bom'].queryset = BOMHeader.objects.filter(status=1)

        # Include current instance even if inactive
        if self.instance.pk:
            if self.instance.product:
                self.fields['product'].queryset |= Product.objects.filter(pk=self.instance.product.pk)
            if self.instance.bom:
                self.fields['bom'].queryset |= BOMHeader.objects.filter(pk=self.instance.bom.pk)

            # Remove duplicates
            self.fields['product'].queryset = self.fields['product'].queryset.distinct()
            self.fields['bom'].queryset = self.fields['bom'].queryset.distinct()

    def clean(self):
        cleaned_data = super().clean()

        bom = cleaned_data.get("bom")
        product = cleaned_data.get("product")
        quantity = cleaned_data.get("bom_quantity")

        # 1️⃣ Quantity validation
        if quantity is None or quantity <= 0:
            self.add_error(
                "bom_quantity",
                "Component quantity must be greater than 0."
            )

        # 2️⃣ Ensure product is unique per BOM
        if bom and product:
            exists = BOMItem.objects.filter(
                bom=bom,
                product=product
            ).exclude(pk=self.instance.pk).exists()  # ⚡ Exclude current instance for update

            if exists:
                self.add_error(
                    "product",
                    "This product is already added to this BOM."
                )

        return cleaned_data


class BOMAttachmentsModelForm(CatalogBaseModelForm, CodeReadonlyOnEditForm):
    class Meta:
        model = BOMAttachments
        exclude=('bom',)


class ProjectSearchModelForm(PurchaseOrderBaseModelForm):
    code = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    project = forms.ChoiceField(
     # choices=[(each.code, each.project_name) for each in ProjectHeader.objects.all()],
        choices=[],   # empty initially
        label="Project",
        widget=forms.Select(attrs={"class": "form-control"})
    )

    required_css_class = 'required'

    class Meta:
        model = ProjectHeader
        exclude = ('created_user', 'updated_user')

class VoucherSearchModelForm(PurchaseOrderBaseModelForm):
    code = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    project = forms.ChoiceField(
     # choices=[(each.code, each.project_name) for each in ProjectHeader.objects.all()],
        choices=[],   # empty initially
        label="Project",
        widget=forms.Select(attrs={"class": "form-control"})
    )

    required_css_class = 'required'

    class Meta:
        model = ProjectHeader
        exclude = ('created_user', 'updated_user')

class BOMSearchModelForm(PurchaseOrderBaseModelForm):

    required_css_class = 'required'

    class Meta:
        model = BOMHeader
        exclude=('created_user', 'updated_user')



