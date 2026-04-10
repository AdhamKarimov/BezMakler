from django.contrib.auth import authenticate
from django.core.mail import send_mail
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.generics import UpdateAPIView, GenericAPIView, ListCreateAPIView, CreateAPIView, \
    RetrieveDestroyAPIView, ListAPIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from .models import User, NEW, CODE_VERIFY, VIA_PHONE, VIA_EMAIL, PremiumTransaction
from .serializers import SignUpSerializer, UserChangeInfoSerializer, ChangePasswordSerializer, ProfileViewSerializers, \
    UpdateProfileSerializer, UserPhontoStatusSerializer, LoginSerializer, BuyPremiumSerializer, \
    PremiumTransactionSerializer, ResetPasswordConfirmSerializer, ResetPasswordRequestSerializer, CodeVerifySerializer
from rest_framework.exceptions import ValidationError
from config import settings
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated,AllowAny
from .models import UserCard
from .serializers import UserCardSerializer
# Create your views here.


class SignUpView(CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = SignUpSerializer
    queryset = User


class CodeVerifyView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CodeVerifySerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            user = serializer.validated_data['user']

            response_data = {
                'message': 'Kod tasdiqlandi',
                'status': status.HTTP_200_OK,
                'access': user.token()['access'],
                'refresh': user.token()['refresh']
            }
            return Response(response_data, status=status.HTTP_200_OK)


class GetNewCodeView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        user = request.user
        codes = user.verify_codes.filter(expiration_time__gte = timezone.now(),is_active=True)
        if codes.exists():
            raise ValidationError({"message": "Sizda hali activ kod bor", "status": status.HTTP_400_BAD_REQUEST})
        else:
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
        response_data = {
            'message': 'Kod yuborildi',
            'status': status.HTTP_201_CREATED,
        }
        return Response(response_data)


class UserChangeInfoView(APIView):
    permission_classes = (IsAuthenticated,)

    def patch(self, request):
        serializer = UserChangeInfoSerializer(instance=request.user,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': status.HTTP_200_OK,
                'message': "Siz muvofaqqiyatli ro'yxatdan o'tdingiz",
            })
        return Response({
            'status': status.HTTP_400_BAD_REQUEST,
            'message': 'Xato',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)





class UserPhotoChangeView(APIView):
    permission_classes = (IsAuthenticated,)

    def patch(self,request):
        user=request.user
        serializer = UserPhontoStatusSerializer(data = request.data, partial = True)
        serializer.is_valid(raise_exception=True)
        serializer.update(instance=user,validated_data= serializer.validated_data)
        return Response({
            'message':"rasm qo'shildi",
            'status': status.HTTP_200_OK,
            'access': user.token()['access'],
            'refresh': user.token()['refresh'],
        })



class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer



class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        refresh = self.request.data.get('refresh',None)
        try:
            refresh_token = RefreshToken(refresh)
            refresh_token.blacklist()
        except Exception as e:
            raise ValidationError( detail=f"xatolik:{e}" )

        else:
            return Response({
                'status': status.HTTP_200_OK,
                'message':"Tizimdan chiqdingiz"
            })



class UpdatePofileView(UpdateAPIView):
    permission_classes = (IsAuthenticated, )
    queryset = User.objects.all()
    serializer_class = UpdateProfileSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return Response({
            'status': status.HTTP_200_OK,
            'message': "Ma'lumotingiz o'zgartirildi",
        })

    def partial_update(self, request, *args, **kwargs):
        super().partial_update(request, *args, **kwargs)
        return Response({
            'status': status.HTTP_200_OK,
            'message': "Ma'lumotingiz qisman o'zgartirildi",
        })


class ProfileView(GenericAPIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = ProfileViewSerializers
    queryset = User

    def get(self, request):
        user = self.request.user
        serializer =ProfileViewSerializers(user)

        response = {
            'status': status.HTTP_200_OK,
            'user': serializer.data,
        }
        return Response(response)


class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated, )

    def patch(self, request):
        serializer = ChangePasswordSerializer(instance=request.user, data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response = {
            'status': status.HTTP_200_OK,
            'message': "Passwordingiz o'zgartilrildi",
        }
        return Response(response)


class LoginRefreshView(APIView):
    permission_classes = (AllowAny, )
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({
                'status': status.HTTP_400_BAD_REQUEST,
                'message':"refresh token yuborilmadi"
            })

        try:
            token = RefreshToken(refresh_token)

            return Response({
                'status': status.HTTP_200_OK,
                'access_token': str(token.access_token)
            })

        except Exception:
            return Response({
                'status': status.HTTP_400_BAD_REQUEST,
                'message': "Refresh token noto‘g‘ri yoki eskirgan",
            })



class CardListCreateView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserCardSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return UserCard.objects.none()
        return UserCard.objects.filter(user=self.request.user).order_by('-id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CardDetailView(RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserCardSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return UserCard.objects.none()
        return UserCard.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'status': status.HTTP_200_OK,
            'message': "Karta o'chirildi"
        }, status=status.HTTP_200_OK)


class BuyPremiumView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = BuyPremiumSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            'status': status.HTTP_200_OK,
            'message': "Premium muvaffaqiyatli faollashtirildi!",
            'premium_expires_at': user.premium_expires_at,
        })


class PremiumTransactionListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PremiumTransactionSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return PremiumTransaction.objects.none()
        return PremiumTransaction.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


class ResetPasswordRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordRequestSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                serializer.to_representation(user),
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ResetPasswordConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ResetPasswordConfirmSerializer(
            instance=request.user,
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Parol muvaffaqiyatli yangilandi"},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)