from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from accounts.models import User


class Command(BaseCommand):
    help = "Create default users for each group with password rm#123"

    USERS = [
         {
             "username": "admin_user",
             "email": "admin@mesolva.com",
             "group": "Administrator",
             "first_name": "Admin",
             "last_name": "Team",
             "mobile_number": "9123456789"
        },
         {
             "username": "staff_user",
             "email": "alex@mesolva.com",
             "group": "Staff",
             "first_name": "Alex",
             "last_name": "Freberg",
             "mobile_number": "9123456788"
         },
         {
             "username": "guest_user",
             "email": "alison@mesolva.com",
             "group": "Guest",
             "first_name": "Alison",
             "last_name": "Candy",
             "mobile_number": "9123456787"
         },
          {
             "username": "sathya.k",
             "email": "sathya.k@mesolva.com",
             "group": "Administrator",
             "first_name": "Sathya",
             "last_name": "K",
             "mobile_number": "9123456100"
         },
          {
             "username": "Sai.k",
             "email": "sai.k@mesolva.com",
             "group": "Administrator",
             "first_name": "Sai",
             "last_name": "K",
             "mobile_number": "9123456101"
         },
         {
            "username": "venkatesh.n",
            "email": "venkatesh.n@mesolva.com",
            "group": "Administrator",
            "first_name": "Venkatesh",
            "last_name": "N",
            "mobile_number": "9123456102"
        },
          {
            "username": "Kumar.I",
             "email": "Kumar.I@mesolva.com",
             "group": "Administrator",
             "first_name": "Kumar",
             "last_name": "I",
             "mobile_number": "9123456103"
         },
          {
             "username": "Manasa.K",
             "email": "manasa.k@mesolva.com",
             "group": "Administrator",
             "first_name": "Manasa",
             "last_name": "K",
             "mobile_number": "9123456104"
         },
    ]

    PASSWORD = "rm#123"

    def handle(self, *args, **kwargs):
        for user_data in self.USERS:
            user, created = User.objects.update_or_create(
                username=user_data["username"],
                defaults={
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                    "email": user_data["email"],
                    "mobile_number": user_data["mobile_number"],
                    "is_active": True,
                }
            )

            if created:
                user.set_password(self.PASSWORD)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created user: {user.username}"))
            else:
                self.stdout.write(f"User already exists: {user.username}")

            # Add user to group
            group, group_created = Group.objects.get_or_create(name=user_data["group"])
            user.groups.add(group)
            self.stdout.write(self.style.SUCCESS(f"Added {user.username} to group {group.name}"))
