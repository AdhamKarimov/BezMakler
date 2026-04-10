from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from config.settings import EMAIL_EXPIRATION_TIME,PHONE_EXPIRATION_TIME
from django.core.validators import FileExtensionValidator
from rest_framework_simplejwt.tokens import RefreshToken
from shared.models import BaseModels
from datetime import timedelta

import random
import string
import uuid


ORDINARY_USER,ADMIN = ('ordinary_user','admin')
NEW,CODE_VERIFY,DONE,PHOTO_DONE = ('new','code_verify','done','photo_done')
VIA_EMAIL,VIA_PHONE, = ('via_email','via_phone',)

class User(BaseModels,AbstractUser):
    USER_ROLE = (
        (ORDINARY_USER,ORDINARY_USER),
        (ADMIN,ADMIN),
    )
    USER_STATUS = (
        (NEW,NEW),
        (CODE_VERIFY,CODE_VERIFY),
        (DONE,DONE),
        (PHOTO_DONE,PHOTO_DONE)
    )
    USER_AUTH_STATUS = (
        (VIA_EMAIL,VIA_EMAIL),
        (VIA_PHONE,VIA_PHONE)
    )
    premium_expires_at = models.DateTimeField(null=True, blank=True)
    report_count = models.PositiveIntegerField(default=0)
    user_role = models.CharField(max_length=20, choices=USER_ROLE, default=ORDINARY_USER)
    auth_status = models.CharField(max_length=20, choices=USER_STATUS, default=NEW)
    auth_type = models.CharField(max_length=20, choices=USER_AUTH_STATUS, null=True, blank=True)
    email = models.EmailField(max_length=100, blank=True, null=True, unique=True)
    phone_number = models.CharField(max_length=13, blank=True, null=True, unique=True)
    avatar = models.ImageField(upload_to='user_photo/',validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'heic'])], null=True,blank=True)

    @property
    def is_premium(self):
        return self.premium_expires_at and self.premium_expires_at > timezone.now()

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def check_username(self):
        if not self.username:
            temp_username = f"username{uuid.uuid4().__str__().split('-')[-1]}"
            while User.objects.filter(username=temp_username).exists():
                temp_username += str(random.randint(0, 9))
            self.username = temp_username

    def set_temp_password(self):
        if not self.password:
            temp_password = f"pass{(uuid.uuid4().__str__().split('-')[-1])}"
            self.set_password(temp_password)

    def check_email(self):
        if self.email:
            email_normalize = self.email.lower()
            self.email = email_normalize

    def token(self):
        refresh_token = RefreshToken.for_user(self)

        data = {
            'refresh': str(refresh_token),
            'access': str(refresh_token.access_token)
        }
        return data

    def generate_cod(self, verify_type):
        code = ''.join(random.choices(string.digits, k=6))
        CodeVerify.objects.create(
            code=code,
            user=self,
            verify_type=verify_type
        )
        return code

class UserCard(models.Model):
    CARD_TYPES = (
        ('uzcard', 'Uzcard'),
        ('humo', 'Humo'),
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('unknown', 'Noma\'lum'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cards')
    card_number = models.CharField(max_length=16, unique=True)
    card_name = models.CharField(max_length=100)
    card_type = models.CharField(max_length=20, choices=CARD_TYPES, default='unknown')
    expiry_date = models.CharField(max_length=5)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=100000.00)

    def __str__(self):
        return f"{self.card_type.upper()} | {self.card_number[-4:]}"

THREE_DAYS, SEVEN_DAYS = ('3_days', '7_days')

class PremiumPlan(models.Model):
    PLAN_TYPES = (
        (THREE_DAYS, '3 kun'),
        (SEVEN_DAYS, '7 kun'),
    )
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.get_plan_type_display()} - {self.price} so'm"


class CodeVerify(BaseModels):
    VERIFY_TYPE = (
        (VIA_EMAIL, VIA_EMAIL),
        (VIA_PHONE, VIA_PHONE)
    )

    user = models.ForeignKey(User,on_delete=models.CASCADE, related_name='verify_codes')
    code = models.CharField(max_length=6)
    verify_type = models.CharField(max_length=30,choices=VERIFY_TYPE)
    expiration_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def save(self,*args,**kwargs):
        if self.verify_type == VIA_EMAIL:
            self.expiration_time = timezone.now()+timedelta(minutes=EMAIL_EXPIRATION_TIME)
        else:
            self.expiration_time = timezone.now()+timedelta(minutes=PHONE_EXPIRATION_TIME)

        super().save(*args,**kwargs)

    def __str__(self):
        return f"{self.user.username} | {self.code}"


class PremiumTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    card = models.ForeignKey(UserCard, on_delete=models.SET_NULL, null=True)
    plan = models.ForeignKey(PremiumPlan, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} | {self.amount} so'm | {self.created_at}"