import os
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from courses.models import Assignment, Attendance, Course, Enrollment, Lesson, Progress, Submission
from plans.models import Plan
from payments.models import Payment
from subscriptions.models import Subscription


class Command(BaseCommand):
    help = "Create idempotent, realistic LMS demonstration data."

    @transaction.atomic
    def handle(self, *args, **options):
        password = os.environ.get("SEED_DEMO_PASSWORD", "DemoPass123!")
        user_specs = [
            ("admin@akrlms.local", "khaja.admin@gmail.com", "Khaja Moinuddin", "admin", True, True),
            ("instructor@akrlms.local", "ravi.instructor@gmail.com", "Dr. Ravi Kumar", "instructor", False, False),
            ("student1@akrlms.local", "khaja1@gmail.com", "Khaja Ahmed", "student", False, False),
            ("student2@akrlms.local", "meera.sharma1@gmail.com", "Meera Sharma", "student", False, False),
            ("student3@akrlms.local", "arjun.reddy1@gmail.com", "Arjun Reddy", "student", False, False),
        ]
        created_users = {}
        for old_email, email, name, role, staff, superuser in user_specs:
            user = User.objects.filter(email=email).first()
            if user is None:
                user = User.objects.filter(email=old_email).first()
                if user is not None:
                    user.email = email
            if user is None:
                user = User(email=email)
            user.name = name
            user.role = role
            user.is_active = True
            user.is_staff = staff
            user.is_superuser = superuser
            user.set_password(password)
            user.save()
            created_users[email] = user

        instructor = created_users["ravi.instructor@gmail.com"]
        course_specs = [
            ("Django & FastAPI Production Backend", "Build a shared-database LMS backend with secure APIs.", "Intermediate", True, Decimal("1499.00")),
            ("Python Foundations", "Practical Python fundamentals, testing, and clean code.", "Beginner", False, Decimal("0.00")),
            ("Real-Time Web Applications", "WebSockets, Redis pub/sub, presence, and notifications.", "Advanced", True, Decimal("1999.00")),
        ]
        video_urls = [
            "https://www.youtube.com/watch?v=F5mRW0jo-U4",
            "https://youtu.be/rfscVS0vtbw",
            "https://www.youtube.com/watch?v=7eh4d6sabA0",
        ]
        courses = []
        for title, description, level, premium, price in course_specs:
            course, _ = Course.objects.update_or_create(
                title=title,
                defaults={
                    "description": description,
                    "level": level,
                    "duration": "12 Hours",
                    "instructor": instructor,
                    "status": "published",
                    "is_premium": premium,
                    "price": price,
                    "instructor_commission": Decimal("20.00"),
                },
            )
            courses.append(course)
            for order, lesson_title in enumerate(("Introduction and setup", "Core concepts", "Production project"), 1):
                Lesson.objects.update_or_create(
                    course=course,
                    order=order,
                    defaults={
                        "title": lesson_title,
                        "content": f"Hands-on lesson for {title}.",
                        "video_url": video_urls[order - 1],
                    },
                )

        students = [
            created_users["khaja1@gmail.com"],
            created_users["meera.sharma1@gmail.com"],
            created_users["arjun.reddy1@gmail.com"],
        ]
        for course in courses:
            for student in students:
                enrollment, _ = Enrollment.objects.get_or_create(user=student, course=course)
                Progress.objects.get_or_create(
                    enrollment=enrollment,
                    defaults={"completed_lessons": 1, "progress_percent": Decimal("33.33")},
                )

        plans = []
        for name, price, days in (("Basic", "499.00", 30), ("Pro", "999.00", 90), ("Enterprise", "2499.00", 365)):
            plan, _ = Plan.objects.update_or_create(
                name=name,
                defaults={
                    "description": f"{name} learning access",
                    "price": Decimal(price),
                    "duration_days": days,
                    "is_active": True,
                },
            )
            plans.append(plan)
        now = timezone.now()
        for index, student in enumerate(students):
            selected_plan = plans[min(index, 1)]
            subscription, _ = Subscription.objects.update_or_create(
                user=student,
                plan=selected_plan,
                defaults={
                    "status": "active",
                    "start_date": now,
                    "end_date": now + timedelta(days=selected_plan.duration_days),
                    "auto_renew": index == 0,
                },
            )
            Payment.objects.update_or_create(
                transaction_id=f"DEMO-TXN-{student.id}-{selected_plan.id}",
                defaults={
                    "subscription": subscription,
                    "amount": (selected_plan.price * Decimal("1.18")).quantize(Decimal("0.01")),
                    "payment_method": "upi",
                    "payment_status": "success",
                    "invoice_number": f"DEMO-INV-{student.id}-{selected_plan.id}",
                    "paid_at": now,
                },
            )

        assignment, _ = Assignment.objects.update_or_create(
            course=courses[0],
            title="Build a secure LMS endpoint",
            defaults={
                "description": "Implement validation, authorization, and automated tests.",
                "deadline": now + timedelta(days=7),
                "created_by": instructor,
            },
        )
        for offset in range(3):
            day = timezone.localdate() - timedelta(days=offset)
            for index, student in enumerate(students):
                Attendance.objects.get_or_create(
                    student=student,
                    course=courses[0],
                    date=day,
                    defaults={"status": "Absent" if index == 2 and offset == 1 else "Present", "marked_by": instructor},
                )
        Submission.objects.get_or_create(
            assignment=assignment,
            student=students[0],
            defaults={
                "file_url": "/uploads/assignments/demo-submission.pdf",
                "original_filename": "khaja-lms-endpoint.pdf",
                "grade": Decimal("92.00"),
                "remarks": "Excellent validation and clean structure.",
                "graded_at": now,
                "graded_by": instructor,
            },
        )

        self.stdout.write(self.style.SUCCESS(
            "Demo data ready: 5 users, 3 courses, 9 lessons, 3 plans, subscriptions, payments, enrollments, attendance, and assignment data."
        ))
        self.stdout.write("Demo password: SEED_DEMO_PASSWORD (local default: DemoPass123!).")
