import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import Group
from accounts.models import User

class Command(BaseCommand):
    help = "Create 8 realtime users with role-based photo and group"

    PASSWORD = "rm#123"

    USERS = [
        {
            "username": "admin_user",
            "email": "admin@mesolva.com",
            "group": "Administrator",
            "first_name": "Admin",
            "last_name": "Team",
            "mobile_number": "9123456789",
            "tz": "Asia/Kolkata",
            "role": "Administrator"
        },
        {
            "username": "staff_user",
            "email": "staff@mesolva.com",
            "group": "Staff",
            "first_name": "Staff_name1",
            "last_name": "Staff_name2",
            "mobile_number": "9123456788",
            "tz": "Asia/Kolkata",
            "role": "Staff"
        },
        {
            "username": "guest_user",
            "email": "alison@mesolva.com",
            "group": "Guest",
            "first_name": "Guest_name1",
            "last_name": "Guest_name2",
            "mobile_number": "9123456787",
            "tz": "Asia/Kolkata",
            "role": "Guest"
        },
        {
            "username": "nagesh",
            "email": "nagesh.p@meslova.com",
            "group": "Administrator",
            "first_name": "Krishnaveni",
            "last_name": "P",
            "mobile_number": "9123456100",
            "tz": "Asia/Kolkata",
            "role": "Indentor"
        },
        {
            "username": "krishnaveni",
            "email": "krishnaveni.c@meslova.com",
            "group": "Administrator",
            "first_name": "Krishnaveni",
            "last_name": "C",
            "mobile_number": "9123456101",
            "tz": "Asia/Kolkata",
            "role": "Recommending Authority"
        },
        {
            "username": "Madhusudhan",
            "email": "madhusudhan.g@meslova.com",
            "group": "Administrator",
            "first_name": "Madhusudhan",
            "last_name": "G",
            "mobile_number": "9123456102",
            "tz": "Asia/Kolkata",
            "role": "IMM"
        },
        {
            "username": "Navya",
            "email": "navya.n@meslova.com",
            "group": "Administrator",
            "first_name": "Navya",
            "last_name": "N",
            "mobile_number": "9123456103",
            "tz": "Asia/Kolkata",
            "role": "Accounts"
        },
        {
            "username": "SreedharRao",
            "email": "sreedharrao.m@meslova.com",
            "group": "Administrator",
            "first_name": "SreedharRao",
            "last_name": "M",
            "mobile_number": "9123456104",
            "tz": "Asia/Kolkata",
            "role": "Approving Authority"
        },
    ]

    def handle(self, *args, **kwargs):

        for u in self.USERS:

            user, created = User.objects.get_or_create(
                username=u["username"],
                defaults={
                    "first_name": u["first_name"],
                    "last_name": u["last_name"],
                    "email": u["email"],
                    "mobile_number": u["mobile_number"],
                    "user_timezone": u["tz"],
                    "is_active": True,
                }
            )

            if created:
                user.set_password(self.PASSWORD)

                # ---------------- Role-Based Photo ----------------
                role_name = u.get("role")

                if role_name:
                    role_image_name = role_name.replace(" ", "_") + ".png"
                    photo_path = os.path.join(settings.MEDIA_ROOT, "accounts", role_image_name)
                else:
                    photo_path = os.path.join(settings.MEDIA_ROOT, "accounts", "default.png")

                # Fallback if image not found
                if not os.path.exists(photo_path):
                    photo_path = os.path.join(settings.MEDIA_ROOT, "accounts", "default.png")
                    self.stdout.write(self.style.WARNING(
                        f"Image not found for role: {role_name}"
                    ))

                if os.path.exists(photo_path):
                    with open(photo_path, "rb") as img:
                        user.photo.save(f"{u['username']}.png", img, save=False)

                user.save()

                self.stdout.write(self.style.SUCCESS(f"Created user: {user.username}"))
            else:
                self.stdout.write(f"User already exists: {user.username}")

            # ---------------- Assign Group ----------------
            group, _ = Group.objects.get_or_create(name=u["group"])
            user.groups.add(group)

        self.stdout.write(self.style.SUCCESS(
            "\nAll Realtime Users + Photos + Groups inserted successfully\n"
        ))
