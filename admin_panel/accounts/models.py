"""
accounts/models.py

This is the single 'users' table shared between Django (Admin Panel)
and FastAPI (User Panel). Both services read/write the SAME database
table, so the column names here matter -- FastAPI's SQLAlchemy model
(user_api/app/models.py) is written to match this table exactly.

Table columns (per the task spec):
    id, name, email, role, password_hash
"""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserRole(models.TextChoices):
    """Allowed roles. FastAPI uses the exact same string values."""
    ADMIN = "admin", "Admin"
    INSTRUCTOR = "instructor", "Instructor"
    STUDENT = "student", "Student"


class UserManager(BaseUserManager):
    """Custom manager because we use `email` instead of `username` to log in."""

    def create_user(self, email, name, password=None, role=UserRole.STUDENT, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        if not email.lower().endswith("@gmail.com"):
            raise ValueError("Users must have a Gmail address ending with @gmail.com")
        user = self.model(email=email, name=name, role=role, **extra_fields)
        user.set_password(password)  # hashed with PASSWORD_HASHERS (bcrypt_sha256)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.ADMIN)
        return self.create_user(email, name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model. AbstractBaseUser gives us the `password` field
    (this IS the password_hash column the task spec asks for) and login
    handling, without Django's default 'username' field getting in the way.
    """

    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.STUDENT)
    profile_picture = models.TextField(blank=True, default="")

    # AbstractBaseUser already defines `password`, we just rename the DB
    # column to `password_hash` so it matches the task spec's schema and
    # the FastAPI SQLAlchemy model column-for-column.
    password = models.CharField(max_length=128, db_column="password_hash")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # required for Django admin login
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        db_table = "users"  # explicit table name so FastAPI's SQLAlchemy model matches it
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.name} ({self.email}) - {self.role}"

    @property
    def is_instructor(self):
        return self.role == UserRole.INSTRUCTOR

    @property
    def is_student(self):
        return self.role == UserRole.STUDENT
