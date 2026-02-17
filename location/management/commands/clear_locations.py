
from django.core.management.base import BaseCommand
from django.db import connection, transaction

class Command(BaseCommand):
    help = "⚠️ Truncate all Location-related tables (Country, Location, SubLocation) in SQLite"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("⚠️ Truncating all Location-related tables..."))

        try:
            with connection.cursor() as cursor:
                # Temporarily disable foreign key checks
                cursor.execute("PRAGMA foreign_keys = OFF;")

                # Delete tables
                cursor.execute("DELETE FROM location_sublocation;")
                cursor.execute("DELETE FROM location_location;")
                cursor.execute("DELETE FROM location_country;")

                # Reset AUTOINCREMENT counters
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='location_sublocation';")
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='location_location';")
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='location_country';")

                # Re-enable foreign key checks
                cursor.execute("PRAGMA foreign_keys = ON;")

            self.stdout.write(self.style.SUCCESS("🗑️ All Location-related data truncated successfully."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error truncating tables: {e}"))



