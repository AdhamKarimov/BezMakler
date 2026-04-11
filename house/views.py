from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models

from .models import House, Wishlist, Message, RecentlyViewed, Region, District
from .serializers import (
    HouseListSerializer, HouseDetailSerializer,
    WishlistSerializer, MessageSerializer, RecentlyViewedSerializer, RegionSerializer, DistrictSerializer
)
from .permission import IsPremiumUser, IsOwnerOrReadOnly, CanChatPermission



class HouseListCreateView(generics.ListCreateAPIView):
    queryset = House.objects.filter(is_active=True).order_by('-created_at')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['region', 'district']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return HouseDetailSerializer
        return HouseListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsPremiumUser()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class HouseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = House.objects.all()
    serializer_class = HouseDetailSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        return [permissions.IsAuthenticated()]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Foydalanuvchi login qilgan bo'lsa, tarixga saqlaymiz
        if request.user.is_authenticated:
            RecentlyViewed.objects.update_or_create(
                user=request.user,
                house=instance
            )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class WishlistToggleView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WishlistSerializer

    def post(self, request, *args, **kwargs):
        house_id = request.data.get('house_id')
        if not house_id:
            return Response({"error": "house_id kerak"}, status=400)

        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            house_id=house_id
        )

        if not created:
            wishlist_item.delete()
            return Response({"message": "Saqlanganlardan o'chirildi"}, status=200)

        return Response({"message": "Saqlanganlarga qo'shildi"}, status=201)


class WishlistView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WishlistSerializer

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)


class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, CanChatPermission]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(
            models.Q(sender=user) | models.Q(receiver=user)
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    def create(self, request, *args, **kwargs):
        # TZ: Premium bo'lmasa xabar yubora olmaydi
        if not getattr(request.user, 'is_premium', False):
            return Response(
                {"detail": "Xabar yuborish uchun Premium tarif sotib oling!"},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)


class RecentlyViewedListView(generics.ListAPIView):
    serializer_class = RecentlyViewedSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RecentlyViewed.objects.filter(user=self.request.user)[:5]



class RegionListView(generics.ListAPIView):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [permissions.AllowAny]


class DistrictListView(generics.ListAPIView):
    serializer_class = DistrictSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        region_id = self.kwargs.get('region_id')
        return District.objects.filter(region_id=region_id)