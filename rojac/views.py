
from django.http import HttpResponseServerError, JsonResponse
from django.shortcuts import render
from django.contrib.auth.tokens import default_token_generator
from django.core import serializers as sez
from django.core.serializers import serialize
from djoser.serializers import ActivationSerializer
import pytz
from djoser import signals
from .serializers import *
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import *
from rest_framework import filters
from django.core.mail import send_mail
from smtplib import SMTPException
from .permissions import *
# from .mpesa import lipa_na_mpesa
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from .utils.accounts import has_pending_signup, get_session_data
from random import seed
from random import randint


class Index():
    pass


class CreateUserAccountApiView(CreateAPIView):
    """An api end point for creating new user accounts"""
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def post(self, request):

        serializer = UserSerializer(data=request.data)
        """first verify that the submitted data does not match any of an existsing user with
        a pending registration status"""
        if not has_pending_signup(request.data['email']):
            if serializer.is_valid(raise_exception=True):
                user = serializer.save()
                # override the default return value upon success
                return Response({"user": [user.id],
                                "detail": [("your user account has been successfully created. Please check your"
                                            " email inbox for activation link.")], "status_code": 201})

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateClientApiView(CreateAPIView):
    """creat new client accounts"""

    serializer_class = ClientSerializer
    queryset = Client.objects.all()

    def post(self, request):

        serializer = ClientSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        client = serializer.save()

        # override the default return value upon success
        return Response({
            'email': client.profile.email,
            'user_id': client.profile.id,
            'account_id': client.pk,
            "detail": ("your account has been successfully created.Please check your"
                       " email inbox for activation link."
                        " Thank you for choosing rojac"),
            "status_code": 201})


class ListClientsApiView(ListAPIView):
    """Lists all instances of clients"""

    # user must be authenticated and with the staff status
    # permission_classes = [permissions.IsAuthenticated, IsManager]
    serializer_class = ClientSecureSerializer
    queryset = Client.objects.all()


class SpecificClientApiView(ListAPIView):
    """Gets a specific instance of a client"""

    serializer_class = ClientSecureSerializer

    def get_queryset(self):
        return Client.objects.all().filter(pk=self.kwargs['pk'])


class UpdateClientApiView(RetrieveUpdateDestroyAPIView):
    """Allows clients to update their accounts"""
    # user must be logged in as a the owner of the target object
    # permission_classes = [permissions.IsAuthenticated, HasAccountPermission]

    serializer_class = ClientUpdateSerializer
    queryset = Client.objects.all()


class AddProductApiView(CreateAPIView):
    """api for adding new sale items"""
    # user must be authenticated and with the staff status
    # permission_classes = [permissions.IsAuthenticated, IsManager]

    serializer_class = ProductSerializer
    queryset = Product.objects.all()


class HomePagedataApiView(ListAPIView):
    """api for getting home data"""

    serializer_class = HomePageDataSerializer

    def get_queryset(self):
        product_categories = ProductCategory.objects.all()
        products = Product.objects.filter(is_featured=True).order_by('-id')
        data = [{
            'product_categories': product_categories,
            'products': products,
        }]
        return data


class ListProductsApiView(ListAPIView):
    """api for listing all sale items"""

    serializer_class = ProductSerializer
    queryset = Product.objects.all().filter(is_featured=True).order_by('-id')
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, ]
    search_fields = [
        'product_title', 'product_description', 'price', 'product_category__category_title', ]

    filterset_fields = ['product_category', ]


class SpecificProductApiView(ListAPIView):
    """gets a specific sale item"""

    serializer_class = ProductDataSerializer

    def get_queryset(self):
        product = Product.objects.get(id=self.kwargs['pk'])
        related_products = Product.objects.all().filter(
            product_category=product.product_category).exclude(id=self.kwargs['pk']).filter(is_featured=True)
        product_images = ProductImage.objects.all().filter(
            product=product)
        product_variations = ProductVariation.objects.all()
        product_variation_images = ProductVariationImage.objects.all().filter(
            product_variation__product=product).filter(is_featured=True)
        product_data = [
            {'product': product,
             'related_products': related_products,
             'product_images': product_images,
             'product_variations': product_variations,
             'product_variation_images': product_variation_images},
        ]
        # results = ProductDataSerializer(product_data, many=True).data
        # results = JSONRenderer().render(results)
        # return Response(results)
        return product_data


class UpdateProductApiView(RetrieveUpdateDestroyAPIView):
    """api that allows shop owner to update their sale commodities"""
    # user must be authenticated and with the staff status
    # permission_classes = [permissions.IsAuthenticated, IsManager]

    serializer_class = ProductSerializer
    queryset = Product.objects.all()


class AddProductCategoryApiView(CreateAPIView):
    """api for adding new product categories"""
    # user must be authenticated and with the staff status
    # permission_classes = [permissions.IsAuthenticated, IsManager]

    serializer_class = ProductCategorySerializer
    queryset = ProductCategory.objects.all()


class ListProductCategoriesApiView(ListAPIView):
    """api for listing all product categories"""

    serializer_class = ProductCategorySerializer
    queryset = ProductCategory.objects.all()
    # filter_backends = [filters.SearchFilter, DjangoFilterBackend, ]
    # search_fields = [
    #     'product_name', 'description', 'price', 'category', ]

    # filterset_fields = ['category', ]


class SpecificProductCategoryApiView(ListAPIView):
    """gets a specific product category"""

    serializer_class = ProductCategorySerializer

    def get_queryset(self):
        return ProductCategory.objects.all().filter(pk=self.kwargs['pk'])


class UpdateProductCategoryApiView(RetrieveUpdateDestroyAPIView):
    """api that allows shop owner to update their product categories"""
    # user must be authenticated and with the staff status
    # permission_classes = [permissions.IsAuthenticated, IsManager]

    serializer_class = ProductCategorySerializer
    queryset = ProductCategory.objects.all()


class AddProductVariationApiView(CreateAPIView):
    """api for adding a new product variation"""
    # user must be authenticated and with the staff status
    # permission_classes = [permissions.IsAuthenticated, IsManager]

    serializer_class = ProductVariationSerializer
    queryset = ProductVariation.objects.all()


class ListProductVariationsApiView(ListAPIView):
    """api for listing all product variations"""

    serializer_class = ProductVariationSerializer
    queryset = ProductVariation.objects.all()
    # filter_backends = [filters.SearchFilter, DjangoFilterBackend, ]
    # search_fields = [
    #     'product_name', 'description', 'price', 'category', ]

    # filterset_fields = ['category', ]


class SpecificProductVariationApiView(ListAPIView):
    """gets a specific product variation"""

    serializer_class = ProductVariationSerializer

    def get_queryset(self):
        return ProductVariation.objects.all().filter(pk=self.kwargs['pk'])


class UpdateProductVariationApiView(RetrieveUpdateDestroyAPIView):
    """api that allows shop owner to update their product variations"""
    # user must be authenticated and with the staff status
    # permission_classes = [permissions.IsAuthenticated, IsManager]

    serializer_class = ProductVariationSerializer
    queryset = ProductVariation.objects.all()


class AddProductImageApiView(CreateAPIView):
    """api for adding new product images"""
    # user must be authenticated and with the staff status
    # permission_classes = [permissions.IsAuthenticated, IsManager]

    serializer_class = ProductImageSerializer
    queryset = ProductImage.objects.all()


class ListProductImagesApiView(ListAPIView):
    """api for listing all product images"""

    serializer_class = ProductImageSerializer
    queryset = ProductImage.objects.all()
    # filter_backends = [filters.SearchFilter, DjangoFilterBackend, ]
    # search_fields = [
    #     'product_name', 'description', 'price', 'category', ]

    # filterset_fields = ['category', ]


class SpecificProductImageApiView(ListAPIView):
    """gets a specific product image"""

    serializer_class = ProductImageSerializer

    def get_queryset(self):
        return ProductImage.objects.all().filter(pk=self.kwargs['pk'])


class UpdateProductImageApiView(RetrieveUpdateDestroyAPIView):
    """api that allows shop owner to update their product images"""
    # user must be authenticated and with the staff status
    # permission_classes = [permissions.IsAuthenticated, IsManager]

    serializer_class = ProductImageSerializer
    queryset = ProductImage.objects.all()


class AddProductVariationImageApiView(CreateAPIView):
    """api for adding new product images"""
    # user must be authenticated and with the staff status
    # permission_classes = [permissions.IsAuthenticated, IsManager]

    serializer_class = ProductVariationImageSerializer
    queryset = ProductVariationImage.objects.all()


class ListProductVariationImagesApiView(ListAPIView):
    """api for listing all product variation images"""

    serializer_class = ProductVariationImageSerializer
    queryset = ProductVariationImage.objects.all()


class SpecificProductVariationImageApiView(ListAPIView):
    """gets a specific product variation image"""

    serializer_class = ProductVariationImageSerializer

    def get_queryset(self):
        return ProductVariationImage.objects.all().filter(pk=self.kwargs['pk'])


class UpdateProductVariationImageApiView(RetrieveUpdateDestroyAPIView):
    """api that allows shop owner to update their product variation images"""
    # user must be authenticated and with the staff status
    # permission_classes = [permissions.IsAuthenticated, IsManager]

    serializer_class = ProductImageSerializer
    queryset = ProductVariationImage.objects.all()


# class LNMOrderAPIView(CreateAPIView):
#     """api for placing an lnm order"""
#     # user must be an authenticated client
#     permission_classes = [permissions.IsAuthenticated, IsClient]

#     query_set = LNMOrder.objects.all()
#     serializer_class = LNMOrderSerializer


# class ListLNMOrdersApiView(ListAPIView):
#     """lists all LNM orders"""
#     # user must be an authenticated client or staff
#     permission_classes = [permissions.IsAuthenticated, IsManager | IsEmployee]

#     serializer_class = LNMOrderSerializer
#     queryset = LNMOrder.objects.all()


# class SpecificLNMOrderApiView(ListAPIView):
#     """api used to get a specific LNM order"""
#     # user must be an authenticated staff or client who owns the target object
#     permission_classes = [permissions.IsAuthenticated,
#                           IsManager | HasClientOrderPermission]

#     serializer_class = LNMOrderSerializer

#     def get_queryset(self):
#         return LNMOrder.objects.all().filter(id=self.kwargs['pk'])


# class SpecificClientOrdersApiView(ListAPIView):
#     """api for listing all orders made by a specific client"""
#     # user must be an authenticated staff or client who owns the target objects
#     permission_classes = [permissions.IsAuthenticated, IsManager | IsClient]
#     serializer_class = LNMOrderSerializer

#     def get_queryset(self):
#         return LNMOrder.objects.all().filter(placer=self.kwargs['pk'])


# class UpdateLNMOrderApiView(RetrieveUpdateDestroyAPIView):
#     """api that enable an LNM order update"""
#     # allows only authenticated users with the staff status ot change the target object
#     permission_classes = [permissions.IsAuthenticated,
#                           IsManager]

#     serializer_class = LNMOrderSerializer
#     queryset = LNMOrder.objects.all()


class ClientEmailView(CreateAPIView):
    """api for contacting admin via email"""
    serializer_class = ClientEmailSerializer

    def post(self, request):
        """gets user request data and sends it to the admin email address"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid:
            name = request.data["first_name"] + " " + request.data["last_name"]
            phone_number = request.data["phone"]
            email_address = request.data["email"]
            message = request.data["message"]

            subject = "Important!! Client Incoming"
            message = f"""
            Name: {name}
            Phone No.: {phone_number}
            Sender email: {email_address}

            {message}"""

            try:
                send_mail(subject, message, email_address, [
                          'njeveh2020@gmail.com'], fail_silently=False)
                data = {'status': 'success', 'status_code': 200}
                return JsonResponse(data)

            except SMTPException:
                data = {'status': 'failed',
                        'status_code': HttpResponseServerError.status_code}
                return JsonResponse(data)

        else:
            data = {'status': 'failed',
                    'status_code': 400}


# def user_account_activation(request, uid, token):
#     """gets the activation request, captures the activation id and token from the request link
#     and posts them to the djoser account activation url"""

#     # if conf.PRODUCTION:
#     #     protocal = 'https://'
#     # else:
#     protocal = 'https://'
#     web_url = protocal + "njeveh.pythonanywhere.com"
#     post_url = web_url + "/accounts/users/activation/"
#     post_data = {'uid': uid, 'token': token}
#     # return render(request=request, template_name="email/pages/account_activation_complete.html", context={"message": "success", "post_data": post_data})
#     try:
#         result = requests.post(post_url, json=post_data)
#         if result.status_code == 204:
#             return render(request=request, template_name="email/pages/account_activation_complete.html", context={"message": "success", "post_data": post_data})
#         else:
#             return render(request=request, template_name="email/pages/account_activation_complete.html", context={"message": "fail", "post_data": post_data})
#     except Exception as e:
#         message = e
#         return render(request=request, template_name="email/pages/account_activation_complete.html", context={"message": message, "post_data": post_data})
class ActivateUser(APIView):
    """gets the activation request, captures the activation id and token from the request link
    and posts them to the djoser account activation url"""
    token_generator = default_token_generator

    def get(self, request, **kwargs):
        try:
            serializer = self.get_serializer(
                data={'uid': self.kwargs['uid'], 'token': self.kwargs['token']})
            try:
                serializer.is_valid(raise_exception=True)
            except PermissionDenied:
                error = "stale_link"
                return render(request=request, template_name="/pages/account_activation_error.html", context={"error": error, })
            except ValidationError:
                error = "invalid_link"
                return render(request=request, template_name="/pages/account_activation_error.html", context={"error": error, })
            user = serializer.user
            with transaction.atomic():
                user.is_active = True
                user.save()
                signals.user_activated.send(
                    sender=self.__class__, user=user, request=self.request
                )

                if settings.SEND_CONFIRMATION_EMAIL:
                    context = {"user": user}
                    to = [get_user_email(user)]
                    settings.EMAIL.confirmation(self.request, context).send(to)
                return render(request=request, template_name="/pages/account_activation_complete.html")
        except Exception as e:
            return render(request=request, template_name="/pages/internal_error_500.html")

    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = ActivationSerializer
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

        # return Response(status=status.HTTP_204_NO_CONTENT)

# def user_account_activated(request):
#     """displays user account activation response message"""

#     if request.is_secure():
#         protocol = 'https://'
#         web_url = protocol + 'njeveh.pythonanywhere.com'
#     else:
#         protocol = 'http://'
#         web_url = protocol + 'localhost:8000'
#     post_url = web_url + "/accounts/users/activation/"
#     post_data = {'uid': uid, 'token': token}
#     result = requests.post(post_url, json=post_data)
#     content = result.json()
#     return Response(content)


class CustomAuthToken(ObtainAuthToken):
    """A Custom authentication class that creates an expiring authentication token
    for a user who logs in"""
    serializer_class = CustomTokenCreateSerializer

    def post(self, request, *args, **kwargs):
        """An override of the post method that takes a login request, verifies
        the login credentials and creates an expiring token once the user is verified"""

        try:
            serializer = self.serializer_class(data=request.data,
                                               context={'request': request})

            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            if not created:
                # update the created time of the token to keep it valid
                token.created = datetime.utcnow().replace(tzinfo=pytz.utc)
                token.save()

            session_data = get_session_data(user)

            return Response({
                'token': token.key,
                'email': user.email,
                'session_status': session_data['session_status'],
                'account_id': session_data['account_id'],
                'profile_picture': session_data['profile_picture'],
                'status': 'success',
                'status_code': 200
            })
        except Exception as e:
            raise e


# class LNMCallbackUrlAPIView(CreateAPIView):
#     queryset = LNMOnline.objects.all()
#     serializer_class = LNMOnlineSerializer

#     def create(self, request):

#         merchant_request_id = request.data["Body"]["stkCallback"]["MerchantRequestID"]
#         checkout_request_id = request.data["Body"]["stkCallback"]["CheckoutRequestID"]
#         result_code = request.data["Body"]["stkCallback"]["ResultCode"]
#         result_description = request.data["Body"]["stkCallback"]["ResultDesc"]
#         amount = request.data["Body"]["stkCallback"]["CallbackMetadata"]["Item"][0][
#             "Value"
#         ]
#         mpesa_receipt_number = request.data["Body"]["stkCallback"]["CallbackMetadata"][
#             "Item"
#         ][1]["Value"]

#         balance = ""
#         transaction_date = request.data["Body"]["stkCallback"]["CallbackMetadata"][
#             "Item"
#         ][2]["Value"]

#         phone_number = request.data["Body"]["stkCallback"]["CallbackMetadata"]["Item"][
#             3
#         ]["Value"]

#         str_transaction_date = str(transaction_date)
#         transaction_datetime = datetime.strptime(
#             str_transaction_date, "%Y%m%d%H%M%S")

#         aware_transaction_datetime = pytz.utc.localize(transaction_datetime)

#         our_model = LNMOnline.objects.create(
#             CheckoutRequestID=checkout_request_id,
#             MerchantRequestID=merchant_request_id,
#             Amount=amount,
#             ResultCode=result_code,
#             ResultDesc=result_description,
#             MpesaReceiptNumber=mpesa_receipt_number,
#             Balance=balance,
#             TransactionDate=aware_transaction_datetime,
#             PhoneNumber=phone_number,
#         )

#         our_model.save()

#         return Response({"OurResultDesc": "YEEY!!! It worked!"})


# class MakeLNMPayment(CreateAPIView):
#     """Api for making lnm express requests"""
#     queryset = LNMOnline.objects.all()
#     serializer_class = LNMOnlineRequestSerializer
#     permission_classes = [permissions.IsAuthenticated, IsClient]

#     def post(self, request):
#         phonenumber = str(request.data['PhoneNumber'])
#         # create the required phone number format regardless of the format submitted by the user
#         phonenumber = '254' + phonenumber[-9:]
#         amount = request.data['Amount']

#         payment = lipa_na_mpesa.lipa_na_mpesa(phonenumber, amount)
#         return Response(payment)

class C2BInitiateAPIView(CreateAPIView):
    queryset = C2bBillRefNumber.objects.all()
    serializer_class = C2bBillRefSerializer

    def create(self, request):
        seed(1)
        random_number = randint(10000, 99999)
        amount = request.data['amount']
        bill_ref_data = C2bBillRefNumber.objects.create(
            bill_ref_number=random_number,
            amount=amount,
        )
        return Response({
            'bill_ref': bill_ref_data.bill_ref_number,
            'amount': amount,
        })


class C2BValidationAPIView(CreateAPIView):
    """Validates mpesa C2B transactions"""
    queryset = C2BPayment.objects.all()
    serializer_class = C2BPaymentSerializer

    def create(self, request):
        print(request.data, "this is request.data in Validation")
        # my_headers = self.get_success_headers(request.data)

        return Response({
            "ResultCode": 0,
            "ResultDesc": "Accepted"
        })


# {
#     "ResultCode": "C2B00011"
#     "ResultDesc": "Rejected"
# }
# Other Result Error Codes

# C2B00011

# Invalid MSISDN

# C2B00012

# Invalid Account Number

# C2B00013

# Invalid Amount

# C2B00014

# Invalid KYC Details

# C2B00015

# Invalid Shortcode

# C2B00016

# Other Error


class C2BConfirmationAPIView(CreateAPIView):
    """gets mpesa c2b transactions confirmation data"""
    # the data is stored in the database
    queryset = C2BPayment.objects.all()
    serializer_class = C2BPaymentSerializer

    def create(self, request):
        print(request.data, "this is request.data in Validation")

        transaction_time = request.data['TransTime']
        str_transaction_date = str(transaction_time)
        transaction_date = datetime.strptime(
            str_transaction_date, '%Y%m%d%H%M%S')

        # Sync Safaricoms response time with server time
        aware_transaction_date = pytz.utc.localize(transaction_date)
        print(aware_transaction_date)

        transaction_type = request.data['TransactionType']
        transaction_id = request.data['TransID']
        transaction_time = aware_transaction_date
        transaction_amount = request.data['TransAmount']
        business_short_code = request.data['BusinessShortCode']
        bill_ref_number = request.data['BillRefNumber']
        invoice_number = request.data['InvoiceNumber']
        org_account_balance = request.data['OrgAccountBalance']
        third_party_transaction_id = request.data['ThirdPartyTransID']
        phone_number = request.data['MSISDN']
        first_name = request.data['FirstName']
        middle_name = request.data['MiddleName']
        last_name = request.data['LastName']

        c2bmodel_data = C2BPayment.objects.create(
            TransactionType=transaction_type,
            TransID=transaction_id,
            TransTime=transaction_time,
            TransAmount=transaction_amount,
            BusinessShortCode=business_short_code,
            BillRefNumber=bill_ref_number,
            InvoiceNumber=invoice_number,
            OrgAccountBalance=org_account_balance,
            ThirdPartyTransID=third_party_transaction_id,
            MSISDN=phone_number,
            FirstName=first_name,
            MiddleName=middle_name,
            LastName=last_name,
        )

        c2bmodel_data.save()
        c2b_context = {
            "Result Code": 0,
            "Data": "success"
        }

        return Response(c2b_context)
