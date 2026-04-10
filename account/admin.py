from django.contrib import admin
from .models import PremiumPlan,UserCard,User,PremiumTransaction,CodeVerify

admin.site.register([PremiumPlan,UserCard,User,PremiumTransaction,CodeVerify])