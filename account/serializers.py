from django.core.mail import send_mail
from django.db.models import Q
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from config import settings
from .models import CodeVerify, User, VIA_EMAIL, VIA_PHONE, CODE_VERIFY, DONE, PHOTO_DONE, PremiumTransaction, NEW
from shared.utilis import check_email_or_phone,check_email_or_phone_or_username
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
import re
from datetime import date
from .models import PremiumPlan, UserCard
from django.utils import timezone
from datetime import timedelta

class SignUpSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    auth_status = serializers.CharField(read_only=True)
    auth_type = serializers.CharField(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email_or_phone'] = serializers.CharField(write_only=True,required=True)

    class Meta:
        model = User
        fields = ['id', 'auth_status', 'auth_type' ]

    def create(self, validated_data):
        user = User(
            email=validated_data.get('email'),
            phone_number=validated_data.get('phone_number'),
            auth_type=validated_data.get('auth_type'),
        )

        user.check_username()
        user.set_temp_password()
        user.check_email()
        user.save()

        if user.auth_type == VIA_EMAIL:
            code = user.generate_cod(VIA_EMAIL)
            try:
                send_mail(
                    'Tasdiqlash kodi',
                    f'Sizning kodingiz: {code}',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
            except Exception as e:
                raise ValidationError({"email": f"Xat yuborishda xatolik yuz berdi: {str(e)}"})
        elif user.auth_type == VIA_PHONE:
            code = user.generate_cod(VIA_PHONE)
            print(code, "|||||||||||||||||||||||||||")
        else:
            raise ValidationError('Email yoki telefon raqam xato')

        return user

    def validate(self, attrs):
        super().validate(attrs)
        data = self.auth_validate(attrs)
        return data

    @staticmethod
    def auth_validate(user_input):
        user_input = user_input.get('email_or_phone')
        user_input_type = check_email_or_phone(user_input)
        if user_input_type == 'phone':
            data = {
                'auth_type':VIA_PHONE,
                'phone_number':user_input
            }
        elif user_input_type == 'email':
            data = {
                'auth_type':VIA_EMAIL,
                'email':user_input
            }
        else:
            response = {
                'status': status.HTTP_400_BAD_REQUEST,
                'message': "Email yoki telefon raqamingiz xato kiritildi"
            }
            raise ValidationError(response)
        return data

    def validate_email_or_phone(self, email_or_phone):
        if User.objects.filter(Q(phone_number=email_or_phone) | Q(email=email_or_phone)).exists():
            raise ValidationError("Bu email yoki telefon raqam bilan oldin ro'yxatdan o'tilgan")
        return email_or_phone

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['message'] = 'Kodingiz yuborildi'
        tokens = instance.token()
        data['refresh'] = tokens['refresh']
        data['access'] = tokens['access']
        return data

class CodeVerifySerializer(serializers.Serializer):
    code = serializers.CharField(required=True, write_only=True)
    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user
        code = attrs.get('code')
        verify_code = user.verify_codes.filter(code=code,expiration_time__gte=timezone.now(),is_active=True).first()
        if not verify_code:
            raise ValidationError({
                "message": "Kodingiz xato yoki eskirgan",
                "status": 400
            })
        verify_code.is_active = False
        verify_code.save()
        if user.auth_status == NEW:
            user.auth_status = CODE_VERIFY
            user.save()
        attrs['user'] = user
        return attrs

class UserChangeInfoSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        password = data.get('password', None)
        confirm_password = data.get('confirm_password', None)

        if password is None or confirm_password is None or password != confirm_password:
            response = {
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Parollar mos emas yoki xato kiritildi'
            }
            raise ValidationError(response)
        if len([i for i in password if i == ' ']) > 0:
            response = {
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Parollar xato kiritildi'
            }
            raise ValidationError(response)

        return data

    def validate_username(self, username):
        if len(username) < 7:
            raise ValidationError({'message': 'Username kamida 7 ta bolishi kerak'})
        elif not username.isalnum():
            raise ValidationError({'message': 'Username da ortiqcha belgilar bolmasligi kerak'})
        elif username[0].isdigit():
            raise ValidationError({'message': 'Username raqam bilan boshlanmasin'})
        if User.objects.filter(username=username).exists():
            raise ValidationError({'message': 'Bu username band, boshqa username tanlang'})

        return username

    def validate_first_name(self,first_name):
        first_name = first_name.strip()
        if not first_name:
            raise serializers.ValidationError("Ism bo'sh bo'lishi mumkin emas.")
        if len(first_name) < 3:
            raise serializers.ValidationError("Ism kamida 3 ta belgidan iborat bo'lishi kerak.")
        if len(first_name) > 50:
            raise serializers.ValidationError("Ism 50 ta belgidan oshmasligi kerak.")
        if not first_name.isalpha():
            raise serializers.ValidationError("Ism faqat harflardan iborat bo'lishi kerak.")
        return first_name.capitalize()

    def validate_last_name(self, last_name):
        last_name = last_name.strip()
        if not last_name:
            raise serializers.ValidationError("Familiya bo'sh bo'lishi mumkin emas.")
        if len(last_name) < 2:
            raise serializers.ValidationError("Familiya kamida 2 ta belgidan iborat bo'lishi kerak.")
        if len(last_name) > 50:
            raise serializers.ValidationError("Familiya 50 ta belgidan oshmasligi kerak.")
        if not last_name.isalpha():
            raise serializers.ValidationError("Familiya faqat harflardan iborat bo'lishi kerak.")
        return last_name.capitalize()

    def update(self, instance, validated_data):
        if instance.auth_status != CODE_VERIFY:
            raise ValidationError({"message": "siz hali tasdiqlanmagansiz ",'status':status.HTTP_400_BAD_REQUEST})
        instance.first_name = validated_data.get('first_name')
        instance.last_name = validated_data.get('last_name')
        instance.username = validated_data.get('username')
        instance.set_password(validated_data.get('password'))
        instance.auth_status = DONE
        instance.save()
        return instance

class UserPhontoStatusSerializer(serializers.Serializer):
    avatar = serializers.ImageField()

    def update(self, instance, validated_data):
        avatar = validated_data.get('avatar', None)
        if avatar:
            instance.avatar = avatar
        if instance.auth_status == DONE:
            instance.auth_status = PHOTO_DONE
        instance.save()
        return instance



class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()
        return instance


class ProfileViewSerializers(serializers.ModelSerializer):
    is_premium = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name','avatar','is_premium','user_role', 'email', 'phone_number']




class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, atters):
        old_password = atters.get('old_password')
        new_password = atters.get('new_password')
        confirm_password = atters.get('confirm_password')
        if old_password == new_password:
            raise ValidationError({
                'status': status.HTTP_400_BAD_REQUEST,
                'message':"eski parol va yangi parol bir xil bo'lmasligi kerak"
            })
        if new_password is None or confirm_password is None or new_password != confirm_password:
            response = {
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Parollar mos emas yoki xato kiritildi'
            }
            raise ValidationError(response)

        if ' ' in new_password:
            raise ValidationError({
                'status': status.HTTP_400_BAD_REQUEST,
                'message': "Parolda bo'sh joy bo'lishi mumkin emas"
            })
        if len(new_password) <= 6:
            raise ValidationError({
                'status': status.HTTP_400_BAD_REQUEST,
                'message': "Parol kamida 6ta belgidan iborat bo'lishi kerak "
            })
        return atters

    def update(self, instance, validated_data):
        if not instance.check_password(validated_data.get('old_password')):
            raise ValidationError({'message': "Eski parol noto'g'ri"})
        instance.set_password(validated_data.get('new_password'))
        instance.save()
        return instance


class LoginSerializer(TokenObtainPairSerializer):
    password = serializers.CharField(required=True, write_only=True)

    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username_input'] = serializers.CharField(required=True, write_only=True)
        self.fields['username'] = serializers.CharField(read_only=True)

    def validate(self, attrs):
        user = self.chek_user_type(attrs)
        tokens=user.token()
        return {
            "status": status.HTTP_200_OK,
            'message':"siz login qildingiz",
            'access': tokens['access'],
            'refresh': tokens['refresh'],
        }



    def chek_user_type(self,data):
        password = data.get('password')
        user_input_data = data.get('username_input')
        user_type = check_email_or_phone_or_username(user_input_data)
        if user_type == "username":
            user = User.objects.filter(username = user_input_data).first()
            self.get_user(user)
            username = user_input_data
        elif user_type == "email":
            user = User.objects.filter(email__icontains=user_input_data.lower()).first()
            self.get_user(user)
            username = user.username
        elif user_type == "phone":
            user = User.objects.filter(phone_number__icontains=user_input_data).first()
            self.get_user(user)
            username = user.username
        else:
            raise ValidationError(detail="Ma'lumot topilmadi")


        authentication_kwargs = {
            "password": password,
            self.username_field: username,
        }

        if user.auth_status not in [DONE, PHOTO_DONE]:
            raise ValidationError(detail="Siz hali to'liq ro'yxatdan o'tmagansiz")

        user = authenticate(**authentication_kwargs)
        if not user:
            raise ValidationError(detail="Login yoki parol xato")

        return user


    def get_user(self,user):
        if not user:
            raise ValidationError({"message":'Xato maliumot kiritdingiz','status':status.HTTP_400_BAD_REQUEST})
        return True



def detect_card_type(card_number):
    if card_number.startswith('8600') or card_number.startswith('6262'):
        return 'uzcard'
    elif card_number.startswith('9860'):
        return 'humo'
    elif card_number.startswith('4'):
        return 'visa'
    elif card_number.startswith(('51','52','53','54','55')):
        return 'mastercard'
    return 'unknown'



def luhn_check(card_number):
    digits = [int(d) for d in card_number]
    digits.reverse()
    total = 0
    for i, digit in enumerate(digits):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


class UserCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCard
        fields = ['id', 'card_number', 'card_name', 'card_type', 'expiry_date', 'balance']
        read_only_fields = ['card_type', 'balance']

    def validate_card_number(self, card_number):
        card_number = card_number.replace(' ', '')

        if not card_number.isdigit():
            raise ValidationError("Karta raqami faqat raqamlardan iborat bo'lishi kerak.")
        if len(card_number) != 16:
            raise ValidationError("Karta raqami 16 ta raqamdan iborat bo'lishi kerak.")
        if not luhn_check(card_number):
            raise ValidationError("Karta raqami noto'g'ri.")

        return card_number

    def validate_expiry_date(self, expiry_date):
        if not re.match(r'^\d{2}/\d{2}$', expiry_date):
            raise ValidationError("Amal qilish muddati MM/YY formatida bo'lishi kerak.")

        month, year = expiry_date.split('/')
        month, year = int(month), int(year) + 2000

        if not (1 <= month <= 12):
            raise ValidationError("Oy 01 dan 12 gacha bo'lishi kerak.")

        today = date.today()
        if (year, month) < (today.year, today.month):
            raise ValidationError("Kartangizning amal qilish muddati tugagan.")

        return expiry_date

    def validate(self, attrs):
        user = self.context['request'].user

        if user.cards.exists():
            raise ValidationError("Siz faqat 1 ta karta qo'sha olasiz.")

        card_number = attrs.get('card_number')
        if UserCard.objects.filter(card_number=card_number).exists():
            raise ValidationError("Bu karta raqami allaqachon ro'yxatdan o'tgan.")

        attrs['card_type'] = detect_card_type(card_number)

        return attrs





class BuyPremiumSerializer(serializers.Serializer):
    card_id = serializers.IntegerField()
    plan_type = serializers.ChoiceField(choices=['3_days', '7_days'])

    def validate_card_id(self, card_id):
        user = self.context['request'].user
        card = UserCard.objects.filter(id=card_id, user=user).first()
        if not card:
            raise ValidationError("Karta topilmadi yoki sizga tegishli emas.")
        return card_id

    def validate(self, attrs):
        user = self.context['request'].user

        if user.is_premium:
            raise ValidationError("Sizda allaqachon aktiv premium bor.")

        plan = PremiumPlan.objects.filter(plan_type=attrs['plan_type']).first()
        if not plan:
            raise ValidationError("Bunday plan mavjud emas.")

        card = UserCard.objects.get(id=attrs['card_id'])
        if card.balance < plan.price:
            raise ValidationError(
                f"Kartangizda yetarli mablag' yo'q. Kerakli summa: {plan.price} so'm"
            )

        attrs['plan'] = plan
        attrs['card'] = card
        return attrs

    def save(self):
        user = self.context['request'].user
        plan = self.validated_data['plan']
        card = self.validated_data['card']

        card.balance -= plan.price
        card.save()

        days = 3 if plan.plan_type == '3_days' else 7
        user.premium_expires_at = timezone.now() + timedelta(days=days)
        user.save()

        PremiumTransaction.objects.create(
            user=user,
            card=card,
            plan=plan,
            amount=plan.price,
        )

        return user

class PremiumTransactionSerializer(serializers.ModelSerializer):
    plan_type = serializers.CharField(source='plan.get_plan_type_display', read_only=True)
    card_number = serializers.CharField(source='card.card_number', read_only=True)
    premium_end_date = serializers.SerializerMethodField()

    class Meta:
        model = PremiumTransaction
        fields = ['id', 'plan_type', 'card_number', 'amount', 'created_at', 'premium_end_date']

    def get_premium_end_date(self, obj):
        if not obj.plan:
            return None

        duration_map = {
            '3_days': 3,
            '7_days': 7,
        }

        days = duration_map.get(obj.plan.plan_type)
        if days:
            from datetime import timedelta
            return obj.created_at + timedelta(days=days)
        return None



class ResetPasswordRequestSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(required=True)

    def validate(self, attrs):
        user_input = attrs.get('email_or_phone').strip()
        user_input_type = check_email_or_phone(user_input)

        if user_input_type == 'phone':
            user = User.objects.filter(phone_number=user_input).first()
            auth_type = VIA_PHONE
        elif user_input_type == 'email':
            user = User.objects.filter(email=user_input.lower()).first()
            auth_type = VIA_EMAIL
        else:
            raise ValidationError("Email yoki telefon raqami formati noto'g'ri")

        if not user:
            raise ValidationError("Bunday foydalanuvchi topilmadi")

        attrs['user'] = user
        attrs['auth_type'] = auth_type
        return attrs

    def create(self, validated_data):
        user = validated_data.get('user')
        auth_type = validated_data.get('auth_type')

        if auth_type == VIA_EMAIL:
            code = user.generate_cod(VIA_EMAIL)
            try:
                send_mail(
                    'Parolni tiklash',
                    f'Sizning tasdiqlash kodingiz: {code}',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
            except Exception as e:
                raise ValidationError({"email": f"Xat yuborishda xatolik: {str(e)}"})

        elif auth_type == VIA_PHONE:
            code = user.generate_cod(VIA_PHONE)
            print(code, "|||||||||||||||||||||||||||")
        else:
            raise ValidationError('Email yoki telefon raqam xato')

        return user

    def to_representation(self, instance):
        tokens = instance.token()
        return {
            'message': 'Kodingiz yuborildi',
            'refresh': tokens['refresh'],
            'access': tokens['access'],
        }


class ResetPasswordConfirmSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate_code(self, value):
        request = self.context.get('request')
        user = request.user
        verify_code = user.verify_codes.filter(
            code=value,
            expiration_time__gte=timezone.now(),
            is_active=True
        ).first()
        if not verify_code:
            raise ValidationError("Kodingiz xato yoki eskirgan")
        return value

    def validate(self, data):
        new_password = data.get('new_password', None)
        confirm_password = data.get('confirm_password', None)

        if new_password is None or confirm_password is None or new_password != confirm_password:
            response = {
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Parollar mos emas yoki xato kiritildi'
            }
            raise ValidationError(response)
        if len([i for i in new_password if i == ' ']) > 0:
            response = {
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'Parollar xato kiritildi'
            }
            raise ValidationError(response)

        return data

    def update(self, instance, validated_data):
        new_password = validated_data.get('new_password')
        instance.set_password(new_password)
        instance.save()
        return instance