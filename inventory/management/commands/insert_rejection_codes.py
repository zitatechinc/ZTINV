# Create a file: your_app/management/commands/create_rejection_codes.py

from django.core.management.base import BaseCommand
from inventory.models import RejectionCode

class Command(BaseCommand):
    help = 'Create initial rejection codes'

    def handle(self, *args, **kwargs):
        
        RejectionCode.objects.all().delete()
        rejection_codes = [
            {'code': '1', 'description': 'Damaged',"name":"Damaged"},
            {'code': '2', 'description': 'DimeDimensional Deviation','name': 'Dimensional Deviation'},
            {'code': '3', 'description': 'Isometric form error','name': 'Isometric form error'},
            {'code': '4', 'description': 'Test results not meeting chemical specification','name': 'Test results not meeting chemical specification'},
            {'code': '5', 'description': 'Test result not meeting physical specification',"name":"Test result not meeting physical specification"},
            {'code': '6', 'description': 'Practical trail not satisfactory',"name":"Practical trail not satisfactory"},
            {'code': '7', 'description': 'Wrong material supplied',"name":"Wrong material supplied"},
            {'code': '8', 'description': 'Blowholes, Porosity, Cavity, Extra materials etc.',"name":"Blowholes, Porosity, Cavity, Extra materials etc."},
            {'code': '9', 'description': 'Excess Supplied',"name":"Excess Supplied"},
            {'code': '10', 'description': 'Appearance not Good.',"name":"Appearance not Good."},
            {'code': '11', 'description': 'Short Supplied',"name":"Short Supplied"},
            
        ]

        for rc in rejection_codes:
            RejectionCode.objects.get_or_create(
                code=rc['code'],name=rc['name'],
                defaults={'description': rc['description']}
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created/Updated: {rc["code"]}')
            )