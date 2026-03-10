from datetime import timezone
import os
import uuid
from django.db import models
# from django.contrib.auth.models import User
from accounts.models import User
from vendor.models import Vendor
from catalog.models import Product
from project.models import ProjectComponent,ProjectHeader
from location.models import Location,SubLocation
from django.utils.timezone import now

 
# Budget allocation can be tied to either a project or a department
budgetType =  (('Project','Project'),('Department','Department'))
# Predefined types of remarks that can be used for logging stage progress
RemarkType = (
    ('PR_Raised', 'PR_Raised'),
    ('Approval', 'Approval'),
    ('Reject', 'Reject'),
    ('Modified', 'Modified'),
    ('Enquiry Generated', 'Enquiry Generated'),
    ('CST', 'CST'),
    ('Negotiation', 'Negotiation'),
    ('DPO', 'DPO'),
    ('PO', 'PO'),
    ('PO_Approval','PO_Approval'),
    ('Enquiry_Modified', 'Enquiry_Modified'),
    ('CST_Modified', 'CST_Modified'),
    ('Negotiation_Modified', 'Negotiation_Modified'),
    ('DPO_Modified', 'DPO_Modified'),
    ('enquiry_approval', 'enquiry_approval'),
    ('Negotiation_approval', 'Negotiation_approval'),
    ('enquiry_return', 'enquiry_return'),
    ('Negotiation_return', 'Negotiation_return'),
    ('CST_approval', 'CST_approval'),
    ('CST_return', 'CST_return'),
    ('DPO_approval', 'DPO_approval'),
    ('DPO_return', 'DPO_return'),
    ('Payment_Generated','Payment_Generated'),
    ('Payment_Modified','Payment_Modified'),
    ('Invoice','Invoice')
)
 
 
class Roles(models.Model):
    role =  models.CharField(max_length = 225, null = True) # Role name, e.g., "IMM", "AA"
    def __str__(self):
        return self.role
   
class Designation(models.Model):
    designation =  models.CharField(max_length = 225, null = True)
    def __str__(self):
        return self.designation
 
 
class Manager(models.Model):
    manager = models.OneToOneField('UserReg', on_delete=models.PROTECT, related_name='managed_by')  
    employees = models.ManyToManyField('UserReg', related_name='managers', blank=True)  
   
    def __str__(self):
        return f"Manager: {self.manager.emp_id}"
 
class Director(models.Model):
    director = models.OneToOneField('UserReg', on_delete=models.PROTECT, related_name='directed_by')  
    managers = models.ManyToManyField(Manager, related_name='directors', blank=True)
    def __str__(self):
        return f"Director: {self.director.emp_id}"
 
class Department(models.Model):
    dept_name = models.CharField(max_length=100, unique=True)# Name of the department (e.g., "Finance", "HR")
    dept_code = models.CharField(max_length=10, unique=True,blank=True,null=True)  # Unique code for the department (e.g., "01", "02")
    def __str__(self):
        return f"{self.dept_name} ({self.dept_code})"
   
    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
 
class UserReg(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)# Link to Django auth user
    emp_id = models.CharField(max_length=6, blank=True,null=True) # Employee ID (used as primary key)
    # password=models.CharField(max_length=8, null=False, blank=False)
     # Optional user info
    username=models.CharField(max_length=30,null=True)# Username for login
    email_id = models.EmailField(max_length=30, null=True, unique=True)# Email address (mandatory)
    alternate_email = models.EmailField(max_length=30, null=True)# Alternate email address (optional)
    gender = models.CharField(max_length=10, null=True, default=None, choices=(('Male', 'Male'), ('Female', 'Female')))# Gender of the user
    phone_number = models.CharField(max_length=14, null=True, default='')# Phone number (optional)
    role = models.ManyToManyField("Roles",null=True, blank=True)# Roles assigned to the user
    designation = models.ForeignKey("Designation", on_delete=models.PROTECT, null=True, default='', blank=True)# Designation of the user
    user_dept = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)# Department of the user
    manager = models.ForeignKey(Manager, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')# Manager of the user
    director = models.ForeignKey(Director, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')# Director of the user
    is_active = models.BooleanField(default=True)# Active status for system use
    sign = models.FileField(upload_to='sign_doc/', blank=True, null=True)
    profile_img = models.FileField(upload_to='profile_doc/', blank=True, null=True)
    def __str__(self):
        return f"{self.emp_id} - {self.user.first_name} {self.user.last_name}"
    # Utility function to get role names for a user
    def get_all_roles_for_user(user):
        if not user.is_authenticated:
            return []
        try:
            userreg = user.userreg  # Access related UserReg object
            roles = userreg.role.all().values_list('role', flat=True)  # Get role names from Roles model
            return list(roles)
        except UserReg.DoesNotExist:
            return []

 
class Project(models.Model):
    project_id = models.CharField(max_length=255,blank=True,null=True)# Unique project code
    name = models.CharField(max_length=255)# Project name

    def __str__(self):
        return f"{self.project_id} - {self.name}"

    def getItems(self):
        proj_obj = ProjectHeader.objects.filter(project_id = self.pk)        
        return ProjectComponent.objects.filter(project_id=proj_obj[0].id)
    def get_allocated_budget(self, financial_year=None):
        if not financial_year:
            financial_year = f"{now().year}-{now().year + 1}"

        budget = self.budgetallocation_set.all().first()

        return int(budget.allocated_budget) if budget else 0
 
class BudgetAllocation(models.Model):
    project =  models.ForeignKey('Project',on_delete=models.SET_NULL, blank=True, null=True)# Project associated with budget
    financial_year = models.CharField(max_length=20) # e.g., "2024-2025"
    allocated_budget=models.DecimalField(max_digits=20,decimal_places=2,) # Total allocated amount
    remaining_budget=models.DecimalField(max_digits=20, decimal_places=2)# Amount left after spend
    department = models.ForeignKey('Department',on_delete=models.SET_NULL, blank=True, null=True)# Optional department association
    budgettype = models.CharField(max_length=20, choices =  budgetType)# "Project" or "Department"
    class Meta:
         # Prevent duplicate entries for same project & financial year
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'financial_year'],
                name='unique_project_financial_year'
            )
        ]
 
class BudgetAllocationLog(models.Model):
    budget_allocation = models.ForeignKey('BudgetAllocation', on_delete=models.CASCADE, null=True, blank=True)# Related budget allocation
    previous_allocated = models.DecimalField(max_digits=20, decimal_places=2) # Snapshot before update
    updated_allocated = models.DecimalField(max_digits=20, decimal_places=2)
    previous_remaining = models.DecimalField(max_digits=20, decimal_places=2) 
    updated_remaining_budget = models.DecimalField(max_digits=20, decimal_places=2)  # snapshot
    remarks = models.TextField() # Reason for update or remarks
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.budget_allocation.project.project_id} - {self.budget_allocation.financial_year} log"


# class Vendor(models.Model):
#     vendor_id = models.CharField(max_length=20,null=True,blank=True)# Internal/vendor code
#     vendor_name = models.CharField(max_length=255,null=True,blank=True) # Contact name
#     email = models.EmailField(null=True,blank=True)
#     phone_number = models.CharField(max_length=14, null=True)
#     gst_number = models.CharField(max_length=20,null=True,blank=True)
#     address = models.TextField(null=True,blank=True)
#     tin_number = models.CharField(max_length=15,null=True,blank=True)# Optional
#     state = models.CharField(max_length=100,null=True,blank=True)
#     city = models.CharField(max_length=100,null=True,blank=True)
#     pincode = models.CharField(max_length=6,null=True,blank=True)
#     company_name = models.TextField(null=True,blank=True)
#     country = models.CharField(max_length=100,null=True,blank=True)
    
 
#     def __str__(self):
#         return f"{self.vendor_id } - {self.company_name}"
 
class TenderType(models.Model):
    tender_code = models.CharField(max_length=255,blank=True,null=True)# Unique tender identifier
    tender_type = models.CharField(max_length=15,blank=True,null=True) # Type name
 
    def __str__(self):
        return f'({self.tender_code}-{self.tender_type})'
 
class ProcurementType(models.Model):
    Procurement_code = models.CharField(max_length=255,blank=True,null=True)# Unique procurement identifier
    Procurement_name = models.CharField(max_length=255, null=True, blank=True)# Type of procurement (e.g., "Import", "Indigeneous")
 
    def __str__(self):
        return f"{self.Procurement_code} - {self.Procurement_name}"
   
 
class SourceOfMake(models.Model):
    source_code = models.CharField(max_length=255,blank=True,null=True)# Unique source identifier
    source_type = models.CharField(max_length=15,blank=True,null=True)# Type of source (e.g., "Indigenous", "Imported")
 
    def __str__(self):
        return f"{self.source_code} - {self.source_type}"

class Delivery(models.Model):
    delivery_name = models.CharField(max_length=255)# Name of the delivery location or method
    def __str__(self):
        return f"{self.delivery_name}"
   
 
class OfficeBranch(models.Model):
    location = models.CharField(max_length=255, null=True, blank=True)# Location of the office branch
    def __str__(self):
        return f"{self.location}"
 
class Quantity(models.Model):
    quantity=models.CharField(max_length=255,blank=True, null=True)# Quantity description (e.g., "10")
    expected_date=models.DateField(null=True, blank=True)# Expected date for this quantity
    def __str__(self):
        return f"{self.quantity}"
    
# class Units(models.Model):
#     unit=models.CharField(max_length=255,blank=True, null=True)# Unit of measurement (e.g., "kg", "pcs", "liters")
#     def __str__(self):
#         return f"{self.unit}"

class Units(models.Model):
    unit = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.unit

 
class Particular(models.Model):
    product  = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True) 
    particular_id = models.CharField(max_length=255, blank=True, null=True)
    item_name=models.TextField(blank=True, null=True)# Name of the item or service being procured
    item_specification=models.TextField(blank=True, null=True)# Specification details for the item
    spec_document = models.FileField(upload_to='spec_doc/', blank=False, null=False)# Specification document (mandatory)
    make=models.TextField(blank=True, null=True)# Manufacturer or brand of the item
    materialcode=models.TextField(blank=True,null=True)# Material code or identifier
    estimatedvalue=models.DecimalField(max_digits=200,decimal_places=2,blank=True,null=True)# Estimated value of the item
    datequantity=models.ManyToManyField(Quantity)# Quantity details with expected dates
    total_qty_required=models.IntegerField(blank=True,null=True)# Total quantity required for this item
    reasons_for_procurement = models.TextField(blank=True, null=True)# Reasons for procurement (optional)
    reasons_document = models.FileField(upload_to='reasons_doc/',blank=True,null=True)# Document for reasons (optional)
    partno=models.TextField(max_length=255,blank=True, null=True)# Part number or identifier for the item
    unitname=models.ForeignKey(Units,on_delete=models.SET_NULL, null=True, blank=True)# Unit of measurement for the item
    delivery = models.ForeignKey(Delivery, on_delete=models.SET_NULL, null=True, blank=True)# Delivery method or location
    Quotation_upload = models.FileField(upload_to='quotation_doc/',blank=True,null=True)
    def __str__(self):
        return f"{self.item_name}"
    
 
class Procurement(models.Model):
     # Unique identifier for this procurement entry
    procurement_id = models.CharField(max_length=255,blank=True, null=True)
     # If this procurement is a modification of a previous PR (purchase request)
    modifiedpr_id=models.CharField(max_length=255,blank=True, null=True)
    # Details from earlier/previous procurements (if any)
    earlier_procurement_details = models.TextField(blank=True, null=True)
    # Whether the material is import or indigenous (linked to SourceOfMake)
    import_indigenous = models.ForeignKey(SourceOfMake, on_delete=models.SET_NULL, null=True, blank=True)
    # Type of tender used (e.g., Open, Limited)
    tender_type = models.ForeignKey(TenderType, on_delete=models.SET_NULL, null=True, blank=True)
    # Type of procurement (e.g., Import, Indigenous)
    procurement_type = models.ForeignKey(ProcurementType, on_delete=models.SET_NULL, null=True, blank=True)
    # Branch where procurement is raised
    branch=models.ForeignKey(SubLocation,on_delete=models.SET_NULL, null=True, blank=True)
    # Department associated with this procurement
    department = models.ForeignKey(Department,on_delete=models.SET_NULL, null=True, blank=True)
    # Linked project (if applicable)
    project =  models.ForeignKey(Project,on_delete=models.SET_NULL, null=True, blank=True)
    # Budget allocation used for this procurement
    budget=models.ForeignKey(BudgetAllocation,on_delete=models.SET_NULL,null=True,blank=True)
    # Vendors/suppliers involved (can be multiple)
    supplier=models.ManyToManyField(Vendor)
    # Any quality certifications required from suppliers
    quality_certificates_required = models.TextField(blank=True, null=True)
    # Material standard requirements
    material_to_confirm_to_standard = models.TextField(blank=True, null=True)
    # Quality document upload (mandatory)
    quality_document = models.FileField(upload_to='quan_doc', blank=False, null=False)
    # Whether this procurement has been canceled
    cancellation=models.BooleanField(default=False)
    # Whether this is a modified PR (purchase request)
    modificationpr=models.BooleanField(default=False)
    # Particulars involved in the procurement (can be multiple items/services)
    particular=models.ManyToManyField(Particular)
    # Date and time when the procurement entry was created
    datetime=models.DateTimeField(auto_now_add=True)
    # Indicates if the procurement is saved as draft (not final)
    is_draft=models.BooleanField(default=False)
    # Indentor or creator of this procurement entry
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    # Approval/review users for different roles
    ra_user =  models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,related_name="ra_user")
    imm_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,related_name="imm_user")
    account_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,related_name="account_user")
    aa_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,related_name="aa_user")
    ri_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,related_name="ri_user")
    # Indicates if this procurement includes negotiation from the indentor's side
    is_negotiation = models.BooleanField(default=False)#indentor negotiation
    # Indicates if this procurement includes negotiation from the RA's side
    RA_negotiation = models.BooleanField(default=False)
    # Number of installments (if applicable for payment or delivery)
    installments=models.IntegerField(null=True,blank=True)# is_back = models.BooleanField(default=False)
    procurement_title=models.CharField(max_length=50,blank=True, null=True)
    is_delivered=models.BooleanField(default=False)
    pr_choices = [
        ('Online_order', 'Online_order'),
        ('Purchase_order', 'Purchase_order'),
        
    ]

    pr_events = models.CharField(
        max_length=255,
        choices=pr_choices,
        default='Purchase_order'
    )
    category_choices = [
        ('Sub_Contract', 'Sub_Contract'),
        ('Service_Contract', 'Service_Contract'),
        ('Meslova_Material','Meslova_Material'),
        ('None','None')
        
    ]

    category_events = models.CharField(
        max_length=255,
        choices=category_choices,
        default='None'
    )
    
    def __str__(self):
        # Return procurement ID or modified ID or fallback
        return f"{self.procurement_id or self.modifiedpr_id or 'No ID'}"
    

# class Product(models.Model):
#     productname=models.CharField(max_length=255, blank=True, null=True)
#     productid=models.CharField(max_length=255, blank=True, null=True)
#     vendor=models.ManyToManyField(Vendor)
#     make=models.TextField(blank=True, null=True)

class ModifiedPr(models.Model):
    # Original procurement reference
    procurement= models.ForeignKey(Procurement,on_delete=models.CASCADE,related_name="procurement", null=True, blank=True)
     # Modified version of the same procurement
    modifiedpr=models.ForeignKey(Procurement,on_delete=models.CASCADE,related_name="modifiedpr", null=True, blank=True)
    # Timestamp of when the modification link was created
    datetime=models.DateTimeField(auto_now_add=True)
 
class PrDocs(models.Model):
    # Document linked to the original procurement
    procurementdoc = models.ForeignKey(Procurement,on_delete=models.CASCADE,related_name="procurementdoc", null=True, blank=True)
    # Document linked to a modified procurement
    modifiedprdoc = models.ForeignKey(Procurement,on_delete=models.CASCADE,related_name="modifiedprdoc", null=True, blank=True)
    # Actual uploaded file (mandatory)
    file=models.FileField(upload_to='media/prDocs', blank=False, null=False)
    # Timestamp for last update
    datetime=models.DateTimeField(auto_now=True)

class QuotationQuantity(models.Model):
    quantity = models.IntegerField(blank=True, null=True)# Quantity of the item quoted (can be used for full quantity or staggered deliveries)
    deliverytimeline = models.CharField(max_length=255, blank=True, null=True)
    delivery_unittypes= models.CharField(max_length=255, blank=True, null=True)#this is for dropdown (days,weeks,months,years)
    
class QuotationParticular(models.Model):
    csparticular=models.ForeignKey(Particular,on_delete=models.SET_NULL, null=True, blank=True)    # The particular item this value is associated with
    totalqty = models.IntegerField(blank=True, null=True)# The total quantity required or quoted for this particular item (can be null/optional)
    deliverytype = models.ForeignKey(Delivery,on_delete=models.CASCADE, null=True, blank=True)#type of delivery(full quantity,staggered)
    quantity = models.ManyToManyField(QuotationQuantity) # Many-to-many relationship to represent different quantity breakdowns 
    
    value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)    # total Quoted value for  unit value for eachor evaluated price
    dollar_value = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True) #total Dollar value for  unit value- Particular Quoted value 

    ra_choosen_vendor = models.BooleanField(default=False)#ra choosen vendor final if ra_wants another vendor based on the price quality
    indentor_choosen_vendor = models.BooleanField(default=False)# Whether the indentor (the one who raised the PR) selected this vendor
    system_choosen_vendor = models.BooleanField(default=False)# Whether the system automatically selected this vendor (e.g., based on best price)
    indentor_negotiation = models.BooleanField(default=False)#indentor wants negotiation if indentor
    ra_negotiation = models.BooleanField(default=False)#ra_negotiation if ra wants negotiation ra_negotiation is final


# class VendorNegoChoosen(models.Model):
#     quotparticular=models.ForeignKey(QuotationParticular,on_delete=models.SET_NULL, null=True, blank=True)    
#     person_choices = [
#         ('system', 'system'),
#         ('indentor', 'indentor'),
#         ('ra', 'ra'),
#     ]#Choice fields for payment modes
#     person_events = models.CharField(
#         max_length=255,
#         choices=person_choices,
#     )#It mapps with the payment_events_choices,where it saves the selected choice
#     choosen_vendor = models.BooleanField(default=False)# Whether the system automatically selected this vendor (e.g., based on best price)
#     is_negotiation = models.BooleanField(default=False)#ra_negotiation if ra wants negotiation ra_negotiation is final
#     ind_ra_stage = models.ForeignKey("StageProgress", on_delete=models.CASCADE, null=True, blank=True)


class Negotiation(models.Model):
    quoted_vendors = models.ForeignKey(QuotationParticular, on_delete=models.SET_NULL, null=True, blank=True) #each particular has separate lowest1 vendor that vendor savd here
    place = models.TextField(blank=True, null=True) #optional field (Not yet used) If Place(Address) should edit then save here 
    vendors = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)#optional field (Not yet used) if vendor edit happens then this applies
   
    quoted_product = models.TextField(blank=True, null=True) # Quoted product description
    quoted_quantity = models.TextField(blank=True, null=True) # Quantity quoted
    quoted_price = models.TextField(blank=True, null=True) # Price quoted 
    quoted_taxes = models.TextField(blank=True, null=True) # Taxes mentioned if indigenous
    quoted_warranty = models.TextField(blank=True, null=True) # Warranty details
    quoted_paymentterms = models.TextField(blank=True, null=True)# Payment terms
    quoteddeliveryschedule = models.TextField(blank=True, null=True)# Delivery schedule
    quoteddeliveryterms = models.TextField(blank=True, null=True) # Delivery terms
    quoted_aftersalessupport = models.TextField(blank=True, null=True)#  Quoted After-sales support details
    quoted_documentation = models.FileField(upload_to="finalprice", blank=False, null=False) # Uploaded quotation document if any file or quoatation file
    quoted_memberspresent = models.TextField(blank=True, null=True) # Quoted members details text area (as it is single field we are saving the details here)
    quoted_anyotherpointnotcovered = models.TextField(blank=True, null=True)# Additional info details after negotiation (as it is single field we are saving the details here)
    
    negotiated_product = models.TextField(blank=True, null=True) # negotiated product description
    negotiated_quantity = models.TextField(blank=True, null=True) #Negotiated Quantity
    negotiated_price = models.TextField(blank=True, null=True) # Negiotiated price
    negotiated_taxes = models.TextField(blank=True, null=True) #Negotiated Tax (if indigenous) 
    negotiated_warranty = models.TextField(blank=True, null=True) #Negotiated warranty details
    negotiated_paymentterms = models.TextField(blank=True, null=True) #Negtoiated Payment terms
    negotiateddeliveryschedule = models.TextField(blank=True, null=True) #Negotiated delivery schedule details
    negotiateddeliveryterms = models.TextField(blank=True, null=True) #Negotiated Delivery terms details
    negotiated_aftersalessupport = models.TextField(blank=True, null=True)  # Negotiated After-sales support details
    negotiated_documentation = models.FileField(upload_to="finalprice", blank=False, null=False) # if any docs available regarding Negotiation  or any info
    negotiated_memberspresent = models.TextField(blank=True, null=True) #as we are storing details of Quoted members present (this is not yet used)
    negotiated_anyotherpointnotcovered = models.TextField(blank=True, null=True)  #as we are storing details of Quoted  Additional info (this is not yet used)
	
    rep_from_finance = models.TextField(blank=True, null=True) #this field is for mentioning name of the Accounts person
    head_imm = models.TextField(blank=True, null=True) #this field is for mentioning name of the imm person
    director_project_delivery = models.TextField(blank=True, null=True) #this field is for mentioning name of the Director of the project 
    chairman_pnc = models.TextField(blank=True, null=True) #this field is for mentioning name of the chairman 
    quotation_ref_date = models.TextField(blank=True, null=True)  # this is to display the Quotation reference number
	 #stage progress updation
    # stage = models.ForeignKey(StageProgress, on_delete=models.CASCADE, null=True, blank=True) #stage name (stage8 Negotiation)
    datetime = models.DateTimeField(auto_now_add=True)# Timestamp when final price record was created
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True) # User who submitted the quote
    def __str__(self):
        return f"FinalPrice {self.id}"

   
class Stages(models.Model):
    # Name of the workflow stage (e.g., "stage1", "stage2", "stage3")
    stage=models.CharField(max_length=255,blank=True,null=True)
 
class StageProgress(models.Model):
    # Associated procurement (original or modified)
    procurement_id = models.ForeignKey(Procurement,on_delete=models.CASCADE, null=False, blank=False,related_name='prid')
     # Name of the stage this progress belongs to
    stagename=models.ForeignKey(Stages,on_delete=models.CASCADE, null=False, blank=False,related_name='stagename')
    # Timestamp of when this stage progress was recorded
    datetime=models.DateTimeField(auto_now_add=True)
    # Type of remark (e.g., "Approved", "Rejected", "Forwarded")
    remarktype = models.CharField(max_length=20, choices = RemarkType)
    # Detailed remark or comment by the user
    remarks=models.TextField(blank=True,null=True)
    # User who gave the remark
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,related_name='remarks_given_user')
    # If rejected, who rejected the PR
    rejectuser = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,related_name='rejectuser')
    # If rejected, which stage it was rejected from
    rejectstage = models.ForeignKey(Stages,on_delete=models.CASCADE, null=True, blank=True,related_name='rejectstage')
    # If this is for a modified PR, link it here
    modified_id = models.ForeignKey(Procurement,on_delete=models.CASCADE,null=True, blank=False,related_name='modprid')
    # Attachment relevant to the stage remark
    attachment = models.FileField(upload_to='stage_attachments/', null=True, blank=True)
     # User to whom this stage is forwarded next (if applicable)
    forwarded_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='forwarded_stage_progress')
    # highlight = models.BooleanField(default=False)
    vendors = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)#optional field  if vendor edit happens then this applies

    nego_quota_particular = models.ForeignKey(Negotiation, on_delete=models.SET_NULL, null=True, blank=True)#which particular is modified

class Tracking(models.Model):
    # The procurement to which this tracking belongs
    procurement_id = models.ForeignKey(Procurement,on_delete=models.CASCADE)
    # Particulars (items/services) being tracked
    particular=models.ManyToManyField(Particular)
    # StageProgress records linked to this tracking
    tracker=models.ManyToManyField(StageProgress)
    # Workflow stages associated with the tracking
    progress=models.ManyToManyField(Stages)

    
class Invoice_File(models.Model):
    file_location = models.FileField(upload_to='invoices/', blank=False, null=False) # Uploaded invoice file will be saved here.(multiple)
 
    def __str__(self):
        return f"Invoice File {self.id}"

class Invoice_Upload(models.Model):
    payment = models.ForeignKey('PaymentData', on_delete=models.CASCADE)#It is mapped to PaymentData table,where it can select from dropdown and save related to the payment mode.
    payment_file = models.ManyToManyField(Invoice_File)#Saves multiple invoice files which are mapped to Invoice_Upload table.
    invoice_stage=models.ForeignKey(StageProgress,on_delete=models.CASCADE, null=True, blank=True)
 
class PaymentFile(models.Model):
    file_location = models.FileField(upload_to='invoices/', blank=False, null=False)# Uploaded payment file
 
    def __str__(self):
        return f"Invoice File {self.id}"
 
class PaymentData(models.Model):
    procurement = models.ForeignKey(
        'Procurement',
        on_delete=models.CASCADE,
    )# Link to Procurement record
    installmentname=models.TextField(null=True, blank=True)#It saves the installment related name.
    po_id = models.ForeignKey("Purchase_Order",on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
       
        return f"{self.procurement.procurement_id} - {self.installmentname}"
 
class PaymentTracking(models.Model):
    payment = models.ForeignKey('PaymentData', on_delete=models.CASCADE)# Link to a specific payment mode ,it is mapped to PaymentData
    installment_date = models.DateField(null=True, blank=True)  # Stores each installment date
    payment_file = models.ManyToManyField(PaymentFile)# One or more invoice files related to this payment,it is mapped to PaymentFile table
   
    payment_events_choices = [
        ('Along with PO as an advance', 'Along with PO as an advance'),
        ('On supply of full material ', 'On supply of full material '),
        ('On supply of partial material', 'On supply of partial material'),
        ('On supply and acceptance of material','On supply and acceptance of material'),
        ('None','None')
    ]#Choice fields for payment modes
    payment_events = models.CharField(
        max_length=255,
        choices=payment_events_choices,
    )#It mapps with the payment_events_choices,where it saves the selected choice
    uploaded_date = models.DateTimeField(auto_now_add=True) # Timestamp of when payment record was uploaded
    submitted_by = models.ForeignKey(
        'UserReg',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )# Who submitted this payment info usually a logged in user.
    payment_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    ) # Actual payable amount for particulars
    payment_mode_choices = [
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('online', 'Online'),
    ] # Mode of payment

    payment_mode = models.CharField(
        max_length=10,
        choices=payment_mode_choices,
    )#It mapps with the payment_events_choices,where it saves the selected choice
    cheque_date = models.DateField(null=True, blank=True)#Cheque generated date will be saved.
    cheque_validity = models.DateField(null=True, blank=True)#It saves the date,till when the cheque will be valid for.
    cheque_no = models.CharField(max_length=50, null=True, blank=True)#It saves the cheque no
    transaction_id = models.CharField(max_length=100, null=True, blank=True) # Online payment transaction ID (if applicable)
    payment_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )# % payment will be saved in the percentages 
    payment_remarks = models.TextField(null=True, blank=True)# Any remarks will be saved about the payment
    payment_stage=models.ForeignKey(StageProgress,on_delete=models.CASCADE, null=True, blank=True)

 
    def __str__(self):
        return f"Payment for {self.payment.procurement.procurement_id} - {self.payment_mode}"
 

#new models

class EnquiryQuantity(models.Model):
    quantity = models.IntegerField(blank=True,null=True)#Here we can add multiple quantities for each particular,it is mapped to En_delivery_dates
    en_expected_date=models.DateField(null=True, blank=True)#Here we can add multiple dates for each particular
 
class En_delivery_dates(models.Model):
    en_particular= models.ForeignKey(Particular,on_delete=models.CASCADE, null=False, blank=False)#Particular table is mapped as many to many field,where we can add multiple dates to each particular
    en_quantity= models.ManyToManyField(EnquiryQuantity)#Saving of multiple quantities based on delivery type,It is mapped as many to many field to the EnquiryQuantity table.
    total_quantity = models.IntegerField(blank=True,null=True)#Total quantity will be saved ,which is related to the quantity for each particular
    delivery_type=models.ForeignKey(Delivery,on_delete=models.CASCADE, null=True, blank=True)#Delivery Type will be saved ,mapped to the Delivery table.

class EnquirySupplierPR(models.Model):
    procure=models.ForeignKey(Procurement,on_delete=models.CASCADE, null=False, blank=False)# It is mapped to the Procurement table where added suppliers can be linked to the each procurement
    suppliers=models.ManyToManyField(Vendor)# New Multiple Vendors can be added in this,where it is mapped to the Vendor table which is many to many field
 
class EnquiryFormPR(models.Model):
    enquiryno=models.CharField(max_length=255,blank=True, null=True)# Auto-generated enquiry number (e.g., EN-PR123) 
    procure=models.ForeignKey(Procurement,on_delete=models.CASCADE, null=False, blank=False)# Related procurement for which enquiry form is being generated
    createddate=models.DateTimeField(auto_now_add=True)#On which date the enquiry form is generated
    duedate=models.CharField(max_length=255,blank=True, null=True)# Due date is used in enquiry form ,till when the enquiry form can be used.
    users=models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True) # Logged in user who generated the enquiry form
    subject=models.CharField(max_length=255,blank=True, null=True)# Subject of the enquiry which handles reason why the enquiry is being generated
    enquirysuppliers=models.ForeignKey(EnquirySupplierPR, on_delete=models.SET_NULL, null=True, blank=True)# New multiple vendors can added ,where it is mapped to EnquirySupplierPR
    stageprogress=models.ForeignKey(StageProgress,on_delete=models.CASCADE, null=True, blank=True)#saves the stage6 as stagename after enquiry is generated,where it is mapped to Stageprogress
    expecteddate=models.CharField(max_length=255,blank=True,null=True)# Expected delivery saves the delivery date ,when the particulars have to be delivered.
    dateddue=models.DateTimeField(null=True,blank=True)# Due date is used in enquiry form till when till enquiry form is valid
    delivery_date=models.ManyToManyField(En_delivery_dates)# Expected delivery saves the delivery date,where it mapps to every particular.
    en_term_cond = models.TextField(null=True,blank=True)# Terms and Conditions related to the Enquiry form will be saved here.
    def save(self, *args, **kwargs):
        if not self.enquiryno and self.procure:
            self.enquiryno = f"EN-{self.procure.procurement_id}"
        super().save(*args, **kwargs)


class VendorQuotations(models.Model):
    eqno=models.ForeignKey(EnquiryFormPR,on_delete=models.CASCADE, null=True, blank=True)#EnquiryFormPR is mapped here ,so the uploaded file is being linked to each enquiry number
    vendors=models.ForeignKey(Vendor,on_delete=models.CASCADE) #Saves the vendors,who uploaded the quotation.
    quoted_user=models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)#Saves the Logged in User who uploaded the quotation
    uploadeddate=models.DateTimeField(auto_now_add=True)# Auto-filled date when the quotation was uploaded
    files=models.FileField(upload_to="quotations",blank=True, null=True)# The uploaded quotation document (PDF, etc.)
    state=models.ForeignKey(StageProgress,on_delete=models.CASCADE, null=True, blank=True)# The stage progress context in which this quotation was uploaded
    
class CompartiveStatementPR(models.Model):
    pro_id = models.ForeignKey(Procurement, on_delete=models.CASCADE, null=False, blank=False)       # Procurement ID related to this CST   
    csuser = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)# User who created or submitted this CST entry
    csdate = models.DateTimeField(auto_now_add=True)  # Date the CST entry was created
    cststate = models.ForeignKey(StageProgress, on_delete=models.CASCADE, null=False, blank=False)    # The stage progress when this CST entry was recorded
    send_choices = [
        ('DPO', 'DPO'),
        ('Indentor', 'Indentor'),
    ]
    send_to = models.CharField(max_length=255,choices=send_choices,default='Indentor') #if single vendor for this procument, imm user will have choice to send directly to dpo or indentor and  Set 'Indentor' as the default value
    additional_info = models.TextField(blank=True, null=True)#any additional information provided by the IMM he can write like for remarks
    payment_invest = models.ManyToManyField(PaymentData)



class VendorQuotationDetails(models.Model):
    cst = models.ForeignKey(CompartiveStatementPR, on_delete=models.CASCADE, null=False, blank=False)# Foreign key linking to the Comparative Statement of Purchase Requisition (CST)
    sources = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=False, blank=False) # Foreign key linking to the Vendor submitting the quotation
    vendor_quotation = models.ForeignKey(VendorQuotations, on_delete=models.CASCADE, null=True, blank=True)      # Related enquiry related quotation
    quotation_reference = models.CharField(max_length=255, blank=True, null=True)      # Reference ID from vendor quotation
    particular = models.ManyToManyField(QuotationParticular)
    coc = models.BooleanField(default=False)  # Confirmation of CST being part of Committee of Comparison (COC)
    validityoffer = models.DateField(blank=True, null=True)     # Offer validity (if applicable)
    discount = models.CharField(max_length=50, blank=True, null=True)      # Commercial details
    # deliverytimeline = models.CharField(max_length=255, blank=True, null=True)
    gst = models.CharField(max_length=255, blank=True, null=True)# GST (Goods and Services Tax) details provided by the vendor
    deliveryterms = models.CharField(max_length=255, blank=True, null=True)
    # delivery_unittypes= models.CharField(max_length=255, blank=True, null=True)#this is for dropdown (days,weeks,months,years)
    paymentterms = models.CharField(max_length=255, blank=True, null=True)# Payment terms agreed upon or proposed by the vendor (e.g., 50% advance, 50% on delivery)
   
    packaging_charges = models.CharField(max_length=255, blank=True, null=True)# Optional packaging charges quoted by the vendor
    insurance_charges = models.CharField(max_length=255, blank=True, null=True) # Optional insurance charges mentioned by the vendor
    customs_duty = models.CharField(max_length=255, blank=True, null=True)# Optional customs duty, if applicable (usually for imported items)
    material_test_report = models.BooleanField(default=False)# Boolean indicating whether a Material Test Report (MTR) is required or provided

    

class DPOParticular(models.Model):
    quotation_particular =  models.ForeignKey(QuotationParticular, on_delete=models.CASCADE,null=True,blank=True)#Associated vendor quotation paticular details
    negotiation =  models.ForeignKey(Negotiation, on_delete=models.CASCADE,null=True,blank=True) # if negotiation happens get the details of the particular from negotiation
    # In DPO if imm wants to edit the details and save, even after negotiation and cst
    description = models.TextField(blank=True, null=True)  
    quantity_dpo=models.IntegerField(blank=True,null=True) #quantity display unit for this particular item in the DPO
    partno_dpo=models.CharField(max_length=255, blank=True, null=True)
    modelno_dpo=models.CharField(max_length=255, blank=True, null=True)
    units_dpo=models.ForeignKey(Units,on_delete=models.SET_NULL, null=True, blank=True)
    unit_display=models.CharField(max_length=255, blank=True, null=True) #if another unit is given by imm,PA then it will be saved here
    unit_price_dpo=models.DecimalField(max_digits=12, decimal_places=2, default=0.00) # Unit price for this particular item in the DPO
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00) # total price Financial breakdown

    

#For a procurement, check how many particular items have been finalized by the RA for the particular vendor — the finalized items will then be carried forward to this model with dpo id
class DPO(models.Model):
    procurement = models.ForeignKey(Procurement, on_delete=models.CASCADE,null=True,blank=True, related_name='draft_pos') #Associated procurement
    particular = models.ManyToManyField(DPOParticular) # the details of particualrs 
    sources = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=False, blank=False)# The vendor/source submitting the quotation
    dpoid = models.CharField(max_length=255, blank=True, null=True) #Optional draft PO ID 
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00) # discount field can edit and submit
    packingcharges = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    quotation_refrence=models.TextField(null=True, blank=True)
    gst_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00,blank=True, null=True) # percentage field for indigenous forms
    gst_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00,blank=True, null=True) #gst field for indigenous form
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00) # final value after gst,discount
    termcond = models.TextField(null=True,blank=True)   # Terms and conditions
    gentermcond = models.TextField(null=True,blank=True) #General terms and conditions after edits
    payment_terms = models.TextField(blank=True, null=True)     # Delivery & payment info
    vendor_address = models.TextField(blank=True, null=True)
    delivery_weeks = models.TextField(blank=True, null=True)  # delivery weeks value
    warranty_period = models.TextField(blank=True, null=True) #warranty details
    billing_address_1 = models.TextField(null=True, blank=True)     # Address details 1(Billing Address)
    delivery_address_2 = models.TextField(null=True, blank=True)     # Address details 2(Delivery Address)
    poid = models.CharField(max_length=255, blank=True, null=True)      # Final PO ID linked after approval
    user_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True) # DPO Submitted person details through user registration
    date = models.DateTimeField(auto_now_add=True) #Timestamp of DPO creation
    dpostage = models.ForeignKey(StageProgress, on_delete=models.CASCADE, null=True, blank=True) # Workflow stage of this draft PO
    def __str__(self):
        return f"DPO-{self.dpoid or self.id}"

class Purchase_Order(models.Model):
    procurement = models.ForeignKey(Procurement, on_delete=models.CASCADE,null=True,blank=True)  # Associated procurement record
    draft_po = models.ForeignKey(DPO, on_delete=models.CASCADE,null=True,blank=True, related_name='final_po')# Associated draft PO that was approved
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE,null=True,blank=True)
    po_number = models.CharField(max_length=255,null=True,blank=True)      # Official PO number
    quote = models.CharField(max_length=255,null=True,blank=True)         # Reference quote number if applicable (from CST)
    date_created = models.DateTimeField(auto_now_add=True) # Creation timestamp of final PO
    gst_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00,blank=True, null=True) 
    basic_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00,null=True, blank=True)
    po_grandtotal=models.DecimalField(max_digits=12, decimal_places=2, default=0.00,null=True, blank=True)
    po_files=models.FileField(upload_to="po",blank=True, null=True)
    postage = models.ForeignKey(StageProgress, on_delete=models.CASCADE, null=True, blank=True) 
    po_sign = models.BooleanField(default=False,null=True, blank=True)

    def __str__(self):
        return f"PO-{self.po_number}"

 
class POApproval(models.Model):
    po = models.ForeignKey(Purchase_Order, on_delete=models.CASCADE) # associated PO 
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True) #choosen person details after sending for signature 
    remarks = models.TextField() #remarks given by user while giving signature
    done_sign = models.BooleanField(default=False) # checking if the approval is done or not  for getting signature
    po_approval = models.ForeignKey(StageProgress, on_delete=models.CASCADE, null=True, blank=True) 


class PurchaseVendor(models.Model):
    po = models.ForeignKey(Purchase_Order, on_delete=models.CASCADE) # associated PO 
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE) # associated Vendor

 

#end new models

class Budget_PO(models.Model):
    from_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00,blank=True, null=True) 
    to_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00,blank=True, null=True) 
    po_approval_user = models.ManyToManyField(User, related_name='po_user', blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

class UserFeedback(models.Model):
    # The user who submitted the feedback
    user = models.ForeignKey(UserReg, on_delete=models.CASCADE, null=True)
    # Short title or subject of the feedback
    title = models.CharField(max_length=200)
    # Detailed feedback message
    description = models.TextField()
    # Timestamp when feedback was created
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} by {self.user.username if self.user else 'Anonymous'}"
    
 
 
 
class GateEntry(models.Model):
    gateentry_id=models.CharField(max_length=255, null=True, blank=True)#Gate entry id will be saved for each procurement,it can be saved serial number wise along with the procuremen id.
    ponumber=models.ForeignKey(Purchase_Order,on_delete=models.CASCADE,null=True)#PO number will be saved ,which is mapped to the PO table.
    invoice_number=models.CharField(max_length=255, null=True, blank=True)#Here saves the invoice number which is related to PO.
    challan_number=models.CharField(max_length=255, null=True, blank=True)#saves the challan_number for the PO related material.
    delivered_by=models.ForeignKey(Vendor,on_delete=models.CASCADE,null=True)#Saves the vendor details,who delivered the particulars.
    noofpackages=models.CharField(max_length=255, null=True, blank=True)#It saves the no.of packages delivered.
    vehicle_info=models.TextField()#It saves the vehicle information which is related to delivery.
    remarks=models.TextField()#Any remarks can be saved which is related to particulars or info related to vendor also.
    checked_by=models.ForeignKey(User,on_delete=models.CASCADE,null=True)#Logged in user will be saved.
    received_at = models.DateTimeField(auto_now_add=True)#It saves the date ,when the items recieved.
    
    def __str__(self):
        return f"{self.gateentry_id}"


class QuantityCheckFiles(models.Model):
    quantitycheck_file = models.FileField(upload_to='quantity_copies/')#saves multiple files related to the quantity check.
    uploaded_at = models.DateTimeField(auto_now_add=True)#Saves the date,when the files have been saved.

    def __str__(self):
        return f"Quantity_Check_Files {self.id}"
    
class QuantityCheck(models.Model):
    ponumber=models.ForeignKey(Purchase_Order,on_delete=models.CASCADE,null=True)#PO number will be saved ,which is mapped to the PO table.
    remarks=models.TextField()#Any remarks can be saved which is related to particulars etc.
    quantity_received=models.CharField(max_length=255, null=True, blank=True)#It saves how much quantity is recieved.
    quantity_required=models.CharField(max_length=255, null=True, blank=True)#It saves how much quantity is required.
    gate_entry_id=models.ForeignKey(GateEntry,on_delete=models.CASCADE,null=True)#It gets the gate entry ids and saves the related gate entry id.
    challen_attachments=models.ManyToManyField(QuantityCheckFiles, related_name='quantitycheck_files', blank=True)#uploads the attachemnts which is related to challan info.
    checked_by=models.ForeignKey(User,on_delete=models.CASCADE,null=True)#Logged in user will be saved.
    timestamp=models.DateTimeField(auto_now_add=True)#Date will be saved ,when the quantity check is saved.
    

    def __str__(self):
        return f"{self.ponumber}"
  
class QualityCheckFiles(models.Model):
    quality_check_file = models.FileField(upload_to='quality_copies/')#saves multiple files related to the quality check.
    uploaded_at = models.DateTimeField(auto_now_add=True)#Saves the date,when the files have been saved.

    def __str__(self):
        return f"Quality_Check_Files {self.id}"
    
class QualityCheck(models.Model):
    serial_number=models.CharField(max_length=255, null=True, blank=True)#It saves the serial number which is related to each item.
    quantity_check=models.ForeignKey(QuantityCheck,on_delete=models.CASCADE,null=True)#
    items=models.ForeignKey(Particular,on_delete=models.CASCADE,null=True)#It maps to particular table,so that it saves the data for each particular.
    spec_match=[
        ('yes', 'Yes'),
        ('no', 'No'),
        ('partial', 'Partial'),
    ]#It is choice field for quality check.
    quality_spec=models.CharField(
        max_length=10,
        choices=spec_match,
    )#Here saves the selected choice from the spec match
    damage=models.BooleanField(default=False)#It is boolen field ,where saves the item is damaged or not.
    test_choices=[
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('custom', 'Custom'),
    ]#It is choice field for test choices.
    test_results=models.CharField(
        max_length=10,
        choices=test_choices,
    )#Here saves the selected choice from the test results
    status_choices=[
         ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('rework', 'Rework'),
    ]#It is choice field for status choices.
    quality_status=models.CharField(
        max_length=10,
        choices=status_choices,
    )#Here saves the selected choice from the quality status
    remarks=models.TextField()#Any remarks can be saved related to the item or the quality check etc.
    timestamp=models.DateTimeField(auto_now_add=True)#Saves the date,when the quality check is held.
    checked_by=models.ForeignKey(User,on_delete=models.CASCADE,null=True)#Saves the logged in user 
    attachments=models.ManyToManyField(QualityCheckFiles, related_name='qualitycheck_files', blank=True)#It saves the multiple files related to quality check,which is mapped to QualityCheckFiles table.

    def __str__(self):
        return f"Quality Check for Quantity Check ID: {self.quantity_check.id if self.quantity_check else 'N/A'}"


   
 