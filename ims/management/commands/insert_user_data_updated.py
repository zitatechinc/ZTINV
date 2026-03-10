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
             "mobile_number": "9123456789",
             "tz":"Asia/Kolkata"
        },
         {
             "username": "staff_user",
             "email": "alex@mesolva.com",
             "group": "Staff",
             "first_name": "Alex",
             "last_name": "Freberg",
             "mobile_number": "9123456788",
             "tz":"Asia/Kolkata"
         },
         {
             "username": "guest_user",
             "email": "alison@mesolva.com",
             "group": "Guest",
             "first_name": "Alison",
             "last_name": "Candy",
             "mobile_number": "9123456787",
             "tz":"Asia/Kolkata"
         },
          {
             "username": "100101",
             "email": "nagesh.p@meslova.com",
             "group": "Administrator",
             "first_name": "Krishnaveni",
             "last_name": "P",
             "mobile_number": "9123456100",
             "tz":"Asia/Kolkata"
         },
          {
             "username": "100102",
             "email": "krishnaveni.c@meslova.com",
             "group": "Administrator",
             "first_name": "Krishnaveni",
             "last_name": "C",
             "mobile_number": "9123456101",
             "tz":"Asia/Kolkata"
         },
         {
            "username": "100103",
            "email": "madhusudhan.g@meslova.com",
            "group": "Administrator",
            "first_name": "Madhusudhan",
            "last_name": "G",
            "mobile_number": "9123456102",
            "tz":"Asia/Kolkata"
        },
          {
            "username": "100104",
             "email": "navya.n@meslova.com",
             "group": "Administrator",
             "first_name": "Navya",
             "last_name": "N",
             "mobile_number": "9123456103",
             "tz":"Asia/Kolkata"
         },
          {
             "username": "100105",
             "email": "sreedharrao.m@meslova.com",
             "group": "Administrator",
             "first_name": "SreedharRao",
             "last_name": "M",
             "mobile_number": "9123456104",
             "tz":"Asia/Kolkata"
         },
    ]

    PASSWORD = "meslova@123"

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
