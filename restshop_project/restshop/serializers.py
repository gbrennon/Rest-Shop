from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from .models import Product, Unit, Seller

EMPTY_PHOTO_URL = 'product_images/empty.jpg'


class UnitSerializer(serializers.ModelSerializer):
    properties = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = Unit
        fields = ('sku', 'price', 'properties', 'images')

    def get_properties(self, obj):
        return [{
                    'name': property_value.property.name,
                    'value': property_value.value
                } for property_value in obj.value_set.all()]

    def get_images(self, obj):
        images = obj.unitimage_set.all()

        if images.exists():
            return [image.image.url for image in images.all()]
        else:
            return [EMPTY_PHOTO_URL]


class ProductListSerializer(serializers.ModelSerializer):
    tags = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name',
        source='tag_set'
    )

    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'title', 'tags', 'image')

    def get_image(self, obj):
        unit = obj.unit_set.filter(unitimage__isnull=False).first()

        # If there are no units for the product:
        if unit is None:
            return EMPTY_PHOTO_URL

        # Get image (preferably, main one) for the unit.
        image = unit.unitimage_set.order_by('-is_main').first()

        # If there are no images for the unit:
        if image is None:
            return EMPTY_PHOTO_URL

        return image.image.url


# Inherit from list serializer to get tags field.
class ProductSerializer(ProductListSerializer):
    units = UnitSerializer(
        many=True,
        read_only=True,
        source='unit_set'
    )

    class Meta:
        model = Product
        fields = ('id', 'title', 'tags', 'units')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'password')

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['email']
        )

        user.set_password(validated_data['password'])
        user.save()

        return user


class SellerSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.CharField(source='seller.name')
    address = serializers.CharField(source='seller.address')

    class Meta:
        model = User
        fields = ('email', 'password', 'name', 'address')

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['email'],
            is_staff=True
        )

        user.set_password(validated_data['password'])
        user.save()

        Seller.objects.create(
            user=user,
            name=validated_data['seller']['name'],
            address=validated_data['seller']['address']
        )

        return user
