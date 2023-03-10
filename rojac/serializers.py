# from pyexpat import model
# from socket import gaierror
from pyexpat import model
from rest_framework import serializers
from .models import *

from rest_framework.authtoken.serializers import AuthTokenSerializer
from django.contrib.auth import authenticate
from djoser.conf import settings
from rojac_backend import settings as conf
from djoser.signals import user_registered
from djoser.compat import get_user_email
from djoser.serializers import UserCreateSerializer
from django.db import IntegrityError, transaction
from rest_framework import status
from .utils.exceptions import CustomException


class CustomTokenCreateSerializer(AuthTokenSerializer):
    """A customized Authentication token serializer that allows to obtain
    the auth_token for user without an activated account."""

    def validate(self, attrs):
        password = attrs.get("password")
        params = {settings.LOGIN_FIELD: attrs.get(settings.LOGIN_FIELD)}

        if password and params[settings.LOGIN_FIELD]:
            user = authenticate(request=self.context.get(
                "request"), **params, password=password)
            if not user:
                user = User.objects.filter(**params).first()
                if user and not user.check_password(password):
                    msg = ('Unable to log in with provided credentials.')
                    raise serializers.ValidationError(
                        msg, code='authorization')
        else:
            msg = ('Must include "username" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        if user:  # and self.user.is_active:
            attrs['user'] = user
            return attrs

        msg = ('Unable to log in with provided credentials.')
        raise serializers.ValidationError(msg, code='authorization')


class UserSerializer(UserCreateSerializer):
    """A serializer class for django user"""
    confirm_password = serializers.CharField(
        required=True, write_only=True,
        style={'input_type': 'password'}
    )

    class Meta(UserCreateSerializer.Meta):
        fields = UserCreateSerializer.Meta.fields+('confirm_password',)

    def validate(self, data):
        """
        Check that the confirm_password is equal to password.
        """
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Password mismatch")
        return data

    def create(self, validated_data):
        """an override of djoser UserCreateSerializer create_user Method. It creates a user and
        sends account activation link to their email address"""

        request = self.context.get("request")

        try:
            validated_data.pop("confirm_password")
            user = self.perform_create_user(validated_data)
            user_registered.send(sender=self.__class__,
                                 user=user, request=request)

            context = {
                "user": user,
                "domain": conf.SITE_DOMAIN,
                "protocal": "https"
            }
            to = [get_user_email(user)]
            if settings.SEND_ACTIVATION_EMAIL:
                try:
                    settings.EMAIL.activation(
                        request, context).send(to)
                except Exception as e:
                    raise CustomException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        code=500,
                        detail={"error": [("Sorry, something went wrong. we are unable to complete your request."
                                " Please contact support for more information")]},
                    )
        except Exception as e:
            raise e
        return user

    def perform_create_user(self, validated_data):
        """an override of djoser UserCreateSerializer perform_create_user Method."""
        user = User.objects.create_user(**validated_data)
        if settings.SEND_ACTIVATION_EMAIL:
            user.is_active = False
            user.save(update_fields=["is_active"])
        return user


class UserSecureSerializer(serializers.ModelSerializer):
    """a serializer class for the django user excluding sensitive information"""
    class Meta:
        model = User
        fields = ['username', 'email']


class ClientSerializer(serializers.ModelSerializer):
    """A serializer class for the client model"""
    profile = UserSerializer()

    class Meta:
        model = Client
        fields = '__all__'

    def create(self, validated_data):
        """creates new instances of User if it doesn't exist
        and proceeds to create an instance of a Buyer"""

        with transaction.atomic():

            user_data = validated_data.pop("profile")
            nested_serializer = self.fields['profile']

            try:
                user = User.objects.get(username=user_data["username"])
            except:
                # User.objects.create_user(**user_data)
                user = nested_serializer.create(user_data)
            validated_data.update({"profile": user})

            client = Client.objects.create(**validated_data)
            return client


class ClientSecureSerializer(serializers.ModelSerializer):
    """a serializer class for the Client model excluding sensitive information"""
    profile = UserSecureSerializer(many=False)

    class Meta:
        model = Client
        fields = ['pk', 'profile', 'phone_number']


class ClientUpdateSerializer(serializers.ModelSerializer):
    """a serializer class for updating Client accounts"""

    class Meta:
        model = Client
        exclude = ["profile"]

    def update(self, instance, validated_data):
        """update method to enable updates on the Client accounts"""

        instance.phone_number = validated_data.get(
            "phone_number", instance.phone_number)

        instance.save()

        return instance


class ProductCategorySerializer(serializers.ModelSerializer):
    """a serializer class for the product category model"""

    class Meta:
        model = ProductCategory
        fields = "__all__"

    def update(self, instance, validated_data):
        """update method to enable updates on the Product Category"""

        instance.category_title = validated_data.get(
            "category_title", instance.category_title)
        instance.image = validated_data.get(
            "image", instance.image)
        instance.save()

        return instance


class ProductImageSerializer(serializers.ModelSerializer):
    """a serializer class for the product image model"""

    class Meta:
        model = ProductImage
        fields = "__all__"


class ProductVariationSerializer(serializers.ModelSerializer):
    """a serializer class for the product variation model"""

    class Meta:
        model = ProductVariation
        fields = "__all__"

    def update(self, instance, validated_data):
        """update method to enable updates on the Product Variation instances"""

        instance.value = validated_data.get(
            "value", instance.value)
        instance.category = validated_data.get(
            "category", instance.category)
        instance.image = validated_data.get(
            "image", instance.image)
        instance.price = validated_data.get(
            "price", instance.price)
        instance.number_in_stock = validated_data.get(
            "number_in_stock", instance.number_in_stock)
        instance.is_featured = validated_data.get(
            "is_featured", instance.is_featured)
        instance.save()

        return instance


class ProductSerializer(serializers.ModelSerializer):
    """a serializer class for the product model"""

    class Meta:
        model = Product
        fields = "__all__"

    def update(self, instance, validated_data):
        """update method to enable updates on the Product"""

        instance.product_name = validated_data.get(
            "product_name", instance.product_name)
        instance.category = validated_data.get(
            "category", instance.category)
        instance.description = validated_data.get(
            "description", instance.description)
        instance.price = validated_data.get(
            "price", instance.price)
        instance.pricing_unit = validated_data.get(
            "pricing_unit", instance.pricing_unit)
        instance.number_in_stock = validated_data.get(
            "number_in_stock", instance.number_in_stock)
        instance.product_main_image = validated_data.get(
            "product_main_image", instance.product_main_image)
        instance.product_extra_image1 = validated_data.get(
            "product_extra_image1", instance.product_extra_image1)
        instance.product_extra_image2 = validated_data.get(
            "product_extra_image2", instance.product_extra_image2)
        instance.save()

        return instance


class HomePageDataSerializer(serializers.Serializer):
    """a serializer class for home page data"""
    product_categories = ProductCategorySerializer(many=True)
    products = ProductSerializer(many=True)


class ProductDataSerializer(serializers.Serializer):
    """a serializer class for the product detail data"""
    product = ProductSerializer(many=False)
    related_products = ProductSerializer(many=True)
    product_images = ProductImageSerializer(many=True)
    product_variations = ProductVariationSerializer(many=True)
    product_variation_images = ProductImageSerializer(many=True)

    # class Meta:
    #     fields = ['product', 'related_products', 'product_images',
    #               'product_variations', 'product_variation_images']


class ProductVariationImageSerializer(serializers.ModelSerializer):
    """a serializer class for the product variation image model"""

    class Meta:
        model = ProductImage
        fields = "__all__"
# class LNMOrderSerializer(serializers.ModelSerializer):
#     payment_transaction = serializers.PrimaryKeyRelatedField(read_only=True)
#     placer = serializers.PrimaryKeyRelatedField(read_only=True)

#     class Meta:
#         model = LNMOrder
#         fields = "__all__"

#     def create(self, validated_data):
#         """creates an instance of an LNMOrder"""

#         order_items = validated_data.pop("order_items")
#         payment_transaction = validated_data.pop(
#             "payment_transaction", None)
#         transaction_id = validated_data.pop("transaction_id")
#         validated_data.pop("placer", None)
#         try:
#             placer = Client.objects.get(user=self.context['request'].user)
#             validated_data.update({"placer": placer})
#         except:
#             msg = ({'error': 'you must be logged in as a client to be able to make this order',
#                     'status_code': status.HTTP_403_FORBIDDEN})
#             raise serializers.ValidationError(
#                 msg, code='permission_denied')
#         try:
#             payment_transaction = LNMOnline.objects.get(
#                 MpesaReceiptNumber=transaction_id)
#             validated_data.update(
#                 {"payment_transaction": payment_transaction})
#         except:
#             msg = ({'error': 'Unable to place the order, No transaction matches the id submitted',
#                     'status_code': status.HTTP_400_BAD_REQUEST})
#             raise serializers.ValidationError(
#                 msg, code='validationation')
#         order = LNMOrder.objects.create(**validated_data)
#         order.order_items.set(order_items)
#         order.save()
#         return order


class ClientEmailSerializer(serializers.Serializer):
    phone = serializers.CharField()
    email = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    message = serializers.CharField(style={'base_template': 'textarea.html'})

    class Meta:
        fields = "__all__"


# class LNMOnlineSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = LNMOnline
#         fields = "__all__"


# class LNMOnlineRequestSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = LNMOnline
#         fields = ['Amount', 'PhoneNumber']


class C2BPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = C2BPayment
        fields = ("id",
                  "TransactionType",
                  "TransID",
                  "TransTime",
                  "TransAmount",
                  "BusinessShortCode",
                  "BillRefNumber",
                  "InvoiceNumber",
                  "OrgAccountBalance",
                  "ThirdPartyTransID",
                  "MSISDN",
                  "FirstName",
                  "MiddleName",
                  "LastName",
                  )


class C2bBillRefSerializer(serializers.ModelSerializer):
    class Meta:
        model = C2bBillRefNumber
        fields = ['amount']
