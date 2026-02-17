import os
import pandas as pd
from django.core.management.base import BaseCommand
from project.models import ProjectHeader, BOMHeader, ProjectComponent, BOMItem
from location.models import Location,SubLocation
from django.db import IntegrityError
from datetime import datetime
from django.conf import settings
from catalog.models import Product
from customer.models import Customer

now = datetime.now()
# Format as YYYY-MM-DD HH:MM:SS
formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")

class Command(BaseCommand):
    help = 'Import data from Excel file to SQLite database'

    def handle(self, *args, **options):
        # Define the relative file path within the media directory
        file_name = "Project_BOM_Component_Data.xlsx"
        
        # Construct the full path to the file in the media directory
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)

        # Ensure the file exists
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File '{file_path}' does not exist"))
            return

        try:
            # Load all sheets into pandas DataFrames
            excel_data = pd.read_excel(file_path, sheet_name=None)

            # Each sheet is loaded as a DataFrame
            project_df = excel_data.get('ProjectHeader')
            bom_df = excel_data.get('BOMHeader')
            component_df = excel_data.get('ProjectComponent')
            bom_item_df = excel_data.get('BOMItem')

            # Import data into the respective models
            self.import_project_header(project_df)
            self.import_bom_header(bom_df)
            self.import_project_component(component_df)
            self.import_bom_item(bom_item_df)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading Excel file: {str(e)}"))

    def import_project_header(self, df):
        for _, row in df.iterrows():
            try:
                project_code = row['ProjectCode']
                project_name = row['ProjectName']
                customer_code = row['Customer']
                location_name = row['Location']
                sub_location_name = row['SubLocation']
                item_status = row['ItemStatus']
                status = row['status']
                created_at = formatted_time
                updated_at = formatted_time
                created_user_id = 1
                updated_user_id = 1

                # Set related fields if applicable
                if customer_code:
                    customer = Customer.objects.get(code=customer_code)
                    #project.customer = customer.id
                if location_name:
                    location = Location.objects.get(name=location_name)
                    #project.location = location.id
                if sub_location_name:
                    sub_location = SubLocation.objects.get(name=sub_location_name)
                    #project.sub_location = sub_location.id

                # Get or create ProjectHeader
                project, created = ProjectHeader.objects.get_or_create(
                    code=project_code,
                    project_name = project_name, 
                    slug = project_code, 
                    item_status = item_status,
                    status = status,
                    created_at = created_at,
                    updated_at = updated_at,
                    customer_id = customer.id,
                    location_id = location.id,
                    sub_location_id = sub_location.id
                )

                #project.save()

                self.stdout.write(self.style.SUCCESS(f"Successfully imported project: {project_code}"))

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Integrity error with project: {project_code}. Error: {str(e)}"))
                continue
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error importing project: {project_code}. Error: {str(e)}"))
                continue

    def import_bom_header(self, df):
        for _, row in df.iterrows():
            try:
                bom_code = row['BOMCode']
                project_code = row['ProjectCode']

                # Get the corresponding ProjectHeader instance
                project = ProjectHeader.objects.get(code=project_code)

                # Create BOMHeader
                bom_header, created = BOMHeader.objects.get_or_create(
                    code=bom_code,
                    slug=bom_code,
                    project_id=project.id,
                    status= row['status'],
                    created_at = formatted_time,
                    updated_at = formatted_time,
                    created_user_id = 1,
                    updated_user_id = 1
                )

                self.stdout.write(self.style.SUCCESS(f"Successfully imported BOM Header: {bom_code}"))

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Integrity error with BOM Header: {bom_code}. Error: {str(e)}"))
                continue
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error importing BOM Header: {bom_code}. Error: {str(e)}"))
                continue

    def import_project_component(self, df):
        for _, row in df.iterrows():
            try:
                component_code = row['ComponentCode']
                project_code = row['ProjectCode']
                component_type = row['ComponentType']
                bom_code = row['BOMCode']
                product_code = row['ProductCode']
                miscellaneous_component = row['MISC_COMPONENT']

                # Get the corresponding ProjectHeader and BOMHeader
                project = ProjectHeader.objects.get(code=project_code)
                bom_header = BOMHeader.objects.get(code=bom_code) if bom_code else None
                product = Product.objects.get(code=product_code) if product_code else None

                if component_type == 'BOM':
                    bom_id=bom_header.id
                    product_id = None,
                    service_id = None
                elif component_type == 'SERVICE':
                    bom_id=None
                    product_id = None,
                    service_id = 1
                elif component_type == 'PRODUCT':
                    bom_id= None
                    product_id = product.id,
                    service_id = None

                # Create ProjectComponent
                project_component = ProjectComponent(
                    project_id=project.id,
                    code=component_code,
                    slug=component_code,
                    component_type=component_type,
                    bom_id=bom_id,
                    product_id=product_id,
                    miscellaneous_component=miscellaneous_component,
                    component_qty=row['ComponentQty'] or 0,
                    component_cost=row['ComponentCost'] or 0,
                    status=1,
                    created_at = formatted_time,
                    updated_at = formatted_time,
                    created_user_id = 1,
                    updated_user_id = 1,
                    service_id=service_id
                )

                project_component.save()

                self.stdout.write(self.style.SUCCESS(f"Successfully imported Project Component: {component_code}"))

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Integrity error with component: {component_code}. Error: {str(e)}"))
                continue
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error importing component: {component_code}. Error: {str(e)}"))
                continue

    def import_bom_item(self, df):
        for _, row in df.iterrows():
            try:
                bom_item_code = row['BOMItemCode']
                bom_code = row['BOMCode']
                product_code = row['ProductCode']

                # Get the corresponding BOMHeader
                bom_header = BOMHeader.objects.get(code=bom_code)
                product = Product.objects.get(code=product_code) if product_code else None

                # Create BOMItem
                bom_item = BOMItem(
                    bom_id=bom_header.id,
                    code=bom_item_code,
                    slug=bom_item_code,
                    product_id=product.id,
                    bom_quantity=row['BOMQty'] or 0,
                    bom_uom=row['BOMUOM'],  # Assuming UOM is in the 'BOMUOM' column
                    scrap_percentage=row['ScrapPercentage'] or 0,
                    status=1,
                    created_at = formatted_time,
                    updated_at = formatted_time,
                    created_user_id = 1,
                    updated_user_id = 1
                )

                bom_item.save()

                self.stdout.write(self.style.SUCCESS(f"Successfully imported BOM Item: {bom_item_code}"))

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Integrity error with BOM Item: {bom_item_code}. Error: {str(e)}"))
                continue
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error importing BOM Item: {bom_item_code}. Error: {str(e)}"))
                continue
