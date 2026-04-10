from rest_framework import serializers
from .models import House, HouseImage, Region, District, Wishlist, Review, Message, RecentlyViewed




class HouseImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = HouseImage
        fields = ['id', 'image']


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'name']


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ['id', 'name', 'region']


class HouseListSerializer(serializers.ModelSerializer):
    images = HouseImageSerializer(many=True, read_only=True)
    region_name = serializers.ReadOnlyField(source='region.name')
    district_name = serializers.ReadOnlyField(source='district.name')

    class Meta:
            model = House
            fields = ['id', 'region_name', 'district_name', 'price', 'images', 'created_at']


class HouseDetailSerializer(serializers.ModelSerializer):
    images = HouseImageSerializer(many=True, read_only=True)
    owner_phone = serializers.SerializerMethodField()
    similar_houses = serializers.SerializerMethodField()

    class Meta:
        model = House
        fields = [
            'id', 'owner', 'owner_phone', 'description', 'price', 'region',
            'district', 'street', 'full_address', 'latitude', 'longitude',
            'images', 'similar_houses', 'created_at'
        ]
        read_only_fields = ['owner']

    def get_owner_phone(self, obj):
        request = self.context.get('request')

        if request and request.user.is_authenticated and getattr(request.user, 'is_premium', False):
            return obj.owner.phone_number
        return "Premium tarif sotib oling"

    def get_similar_houses(self, obj):
        similar = House.objects.filter(district=obj.district).exclude(id=obj.id)[:5]
        return HouseListSerializer(similar, many=True).data


class WishlistSerializer(serializers.ModelSerializer):
    house_details = HouseListSerializer(source='house', read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'house', 'house_details']


class MessageSerializer(serializers.ModelSerializer):
    sender_email = serializers.ReadOnlyField(source='sender.email')

    class Meta:
        model = Message
        fields = ['id', 'house', 'sender', 'sender_email', 'receiver', 'text', 'created_at']
        read_only_fields = ['sender']



class RecentlyViewedSerializer(serializers.ModelSerializer):
    house_details = HouseListSerializer(source='house', read_only=True)

    class Meta:
        model = RecentlyViewed
        fields = ['id', 'house', 'house_details', 'viewed_at']