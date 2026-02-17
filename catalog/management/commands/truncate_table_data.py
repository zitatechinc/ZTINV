from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Delete all data from customer table and reset auto-increment counter'


    # Customer 
    
    # def handle(self, *args, **kwargs):
    #     with connection.cursor() as cursor:
    #         # Step 1: Delete all rows from the customer table
    #         cursor.execute('DELETE FROM customer_customer;')
            
    #         # Step 2: Reset the auto-increment counter for the customer table
    #         cursor.execute('DELETE FROM sqlite_sequence WHERE name="customer_customer";')

    #     self.stdout.write(self.style.SUCCESS('Successfully deleted all data from the customer table and reset the auto-increment counter.'))
    
    # Vendor Data

    # def handle(self, *args, **kwargs):
    #     with connection.cursor() as cursor:
    #         # Step 1: Delete all rows from the customer table
    #         cursor.execute('DELETE FROM vendor_vendor;')
            
    #         # Step 2: Reset the auto-increment counter for the customer table
    #         cursor.execute('DELETE FROM sqlite_sequence WHERE name="vendor_vendor";')

    #     self.stdout.write(self.style.SUCCESS('Successfully deleted all data from the Vendor table and reset the auto-increment counter.'))

    def handle(self, *args, **kwargs):
        with connection.cursor() as cursor:
            # Step 1: Delete all rows from the customer table
            cursor.execute('DELETE FROM accounts_user;')
            
            # Step 2: Reset the auto-increment counter for the customer table
            cursor.execute('DELETE FROM sqlite_sequence WHERE name="accounts_user";')

        self.stdout.write(self.style.SUCCESS('Successfully deleted all data from the accounts_user table and reset the auto-increment counter.'))