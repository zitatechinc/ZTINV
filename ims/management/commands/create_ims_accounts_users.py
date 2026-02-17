import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import Group
from accounts.models import User
from ims.models import UserReg, Roles, Designation, Department


class Command(BaseCommand):
    help = "Create Users + Conditional UserReg + Role Images + Profile + Sign"

    PASSWORD = "rm#123"

    USERS = [
        # -------- ONLY accounts.User --------
        {
            "username": "admin_user",
            "email": "admin@mesolva.com",
            "group": "Administrator",
            "first_name": "Admin",
            "last_name": "Team",
            "mobile": "9123456789",
            "tz": "Asia/Kolkata",
            "roles": ["Administrator"]
        },
        {
            "username": "staff_user",
            "email": "staff@mesolva.com",
            "group": "Staff",
            "first_name": "Staff_name1",
            "last_name": "Staff_name2",
            "mobile": "9123456788",
            "tz": "Asia/Kolkata",
            "roles": ["Staff"]
        },
        {
            "username": "guest_user",
            "email": "alison@mesolva.com",
            "group": "Guest",
            "first_name": "Guest_name1",
            "last_name": "Guest_name2",
            "mobile": "9123456787",
            "tz": "Asia/Kolkata",
            "roles": ["Guest"]
        },
        # -------- accounts.User + UserReg --------
        {
            "username": "nagesh",
            "first_name": "Nagesh",
            "last_name": "P",
            "email": "nagesh@test.com",
            "mobile": "900000001",
            "roles": ["Indentor"],
            "tz": "Asia/Kolkata",
            "group": "Administrator",
            "emp_id": "100101",
            "username1": "nagesh",
            "email1": "nagesh@test.com",
            "alternate_email": "nagesh@test.com",
            "gender": "Male",
            "mobile1": "900000001",
            "designation": "Purchase Officer",
            "department": "Engineering",
        },
        {
            "username": "krishnaveni",
            "first_name": "Krishnaveni",
            "last_name": "C",
            "email": "krishnaveni.c@meslova.com",
            "mobile": "9123456101",
            "roles": ["Recommending Authority"],
            "tz": "Asia/Kolkata",
            "group": "Administrator",
            "emp_id": "100102",
            "username1": "krishnaveni",
            "email1": "krishnaveni.c@meslova.com",
            "alternate_email": "krishnaveni.c@meslova.com",
            "gender": "Female",
            "mobile1": "9123456101",
            "designation": "Procurement Manager",
            "department": "Engineering",
        },
        {
            "username": "madhusudhan",
            "first_name": "Madhusudhan",
            "last_name": "G",
            "email": "madhusudhan.g@meslova.com",
            "mobile": "9123456102",
            "roles": ["IMM"],
            "tz": "Asia/Kolkata",
            "group": "Administrator",
            "emp_id": "100103",
            "username1": "madhusudhan",
            "email1": "madhusudhan.g@meslova.com",
            "alternate_email": "madhusudhan.g@meslova.com",
            "gender": "Male",
            "mobile1": "9123456102",
            "designation": "Warehouse Supervisor",
            "department": "Engineering",
        },
        {   "username": "navya", 
            "first_name": "Navya", 
            "last_name": "N", 
            "email": "navya.n@meslova.com", 
            "mobile": "9123456103", 
            "roles": ["Accounts"], 
            "tz": "Asia/Kolkata", 
            "group": "Administrator", 
            "emp_id": "100104", 
            "username1": "navya", 
            "email1": "navya.n@meslova.com", 
            "alternate_email": "navya.n@meslova.com", 
            "gender": "Female", 
            "mobile1": "9123456103", 
            "designation": "Finance Manager", 
            "department": "Engineering", 
        }, 
        { 
            "username": "sreedharrao", 
            "first_name": "Sreedhar", 
            "last_name": "M", 
            "email": "sreedharrao.m@meslova.com", 
            "mobile": "9123456104", 
            "roles": ["Approving Authority"], 
            "tz": "Asia/Kolkata", 
            "group": "Administrator", 
            "emp_id": "100105", 
            "username1": "sreedharrao", 
            "email1": "sreedharrao.m@meslova.com", 
            "alternate_email": "sreedharrao.m@meslova.com", 
            "gender": "Male", 
            "mobile1": "9123456104", 
            "designation": "Chief Executive Officer", 
            "department": "Engineering", },
    ]

    def handle(self, *args, **kwargs):

        for u in self.USERS:
            print(u)
            # ================= SAFE USER CREATION =================

            # 1️⃣ Try find by username
            user = User.objects.filter(username=u["username"]).first()

            # 2️⃣ If not found, try find by mobile
            if not user:
                user = User.objects.filter(mobile_number=u["mobile"]).first()

            # 3️⃣ If still not found, create new instance (DO NOT SAVE YET)
            if not user:
                user = User()

            # 4️⃣ Always update values
            try:
                user.username = u["emp_id"]
                user.first_name = u["first_name"]
                user.last_name = u["last_name"]
                user.email = u["email"]
                user.mobile_number = u["mobile"]
                user.user_timezone = u["tz"]
                user.is_active = True
                user.set_password(self.PASSWORD)
            except:
                user.username = u["username"]
                user.first_name = u["first_name"]
                user.last_name = u["last_name"]
                user.email = u["email"]
                user.mobile_number = u["mobile"]
                user.user_timezone = u["tz"]
                user.is_active = True
                user.set_password(self.PASSWORD)

            # 5️⃣ Save once
            user.save()


            # -------- ROLE BASED IMAGE FOR USER --------
            role_name = u["roles"][0]
            image_name = role_name.replace(" ", "_") + ".png"

            photo_path = os.path.join(settings.MEDIA_ROOT, "accounts", image_name)
            if not os.path.exists(photo_path):
                photo_path = os.path.join(settings.MEDIA_ROOT, "accounts", "default.png")

            if os.path.exists(photo_path):
                with open(photo_path, "rb") as img:
                    user.photo.save(f"{u['username']}.png", img, save=False)

            user.save()

            # -------- GROUP --------
            group, _ = Group.objects.get_or_create(name=u["group"])
            user.groups.add(group)

            # ================= CONDITIONAL USERREG =================
            if role_name not in ["Administrator", "Staff", "Guest"]:

                userreg, _ = UserReg.objects.get_or_create(user=user)

                # Update fields safely
                userreg.emp_id = u["emp_id"]
                userreg.username = u["username1"]
                userreg.email_id = u["email1"]
                userreg.alternate_email = u["alternate_email"]
                userreg.gender = u["gender"]
                userreg.phone_number = u["mobile1"]

                # Safe designation
                designation, _ = Designation.objects.get_or_create(
                    designation=u["designation"]
                )
                userreg.designation = designation

                # Safe department
                department, _ = Department.objects.get_or_create(
                    dept_name=u["department"]
                )
                userreg.user_dept = department

                userreg.save()

                # Assign roles safely
                userreg.role.clear()
                for r in u["roles"]:
                    role_obj, _ = Roles.objects.get_or_create(role=r)
                    userreg.role.add(role_obj)

                # -------- PROFILE IMAGE --------
                profile_path = os.path.join(settings.MEDIA_ROOT, "profile_doc", image_name)
                if not os.path.exists(profile_path):
                    profile_path = os.path.join(settings.MEDIA_ROOT, "profile_doc", "default.png")

                if os.path.exists(profile_path):
                    with open(profile_path, "rb") as img:
                        userreg.profile_img.save(f"{u['username']}.png", img, save=False)

                # -------- SIGN IMAGE --------
                sign_path = os.path.join(settings.MEDIA_ROOT, "sign_doc", image_name)
                if not os.path.exists(sign_path):
                    sign_path = os.path.join(settings.MEDIA_ROOT, "sign_doc", "default.png")

                if os.path.exists(sign_path):
                    with open(sign_path, "rb") as img:
                        userreg.sign.save(f"{u['username']}.png", img, save=False)

                userreg.save()

                self.stdout.write(self.style.SUCCESS(
                    f"Created User + UserReg: {user.username}"
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f"Created ONLY User: {user.username}"
                ))

        self.stdout.write(self.style.SUCCESS(
            "\nALL USERS CREATED SUCCESSFULLY\n"
        ))
