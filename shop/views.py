import logging

from django.conf import settings
from django.core.exceptions import FieldError
from django.db.models import Count, F, Sum, DecimalField
from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, GenericViewSet, ReadOnlyModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, ListModelMixin
from zeep import Client

from core.models import User, AuditLog
from discount.models import BaseDiscount
from .pagination import DefaultPagination
from .reports import Reporting
from .serializers import (ProductSerializer, CollectionSerializer, ReviewSerializer,
                          CartSerializer, CartItemSerializer, AddItemsSerializer, UpdateItemsSerializer,
                          CustomerSerializer, OrderSerializer, CreateOrderSerializer, UpdateOrderSerializer,
                          ProductImageSerializer, AddressSerializer, TransactionSerializer, UpdateTransactionSerializer,
                          AuditLogSerializer, PromotionSerializer, SimpleProductSerializer, ReportingSerializer,
                          SiteSettingsSerializer, HomeBannerSerializer, ApplyDiscountSerializer,
                          FeatureKeyFullSerializer, SendRequestSerializer, VerifySerializer)
from .models import Product, Collection, OrderItem, Review, Customer, Order, ProductImage, CartItem, Cart, Address, \
    Transaction, Promotion, SiteSettings, HomeBanner, MainFeature, FeatureKey
from .filters import ProductFilter, RecursiveDjangoFilterBackend, CustomerFilterBackend
from .permissions import IsAdminOrReadOnly, ViewCustomerHistoryPermission

views_logger = logging.getLogger('views_logger')

# Create your views here.
"""class api view example"""
# class ProductList(APIView):
#     def get(self, request):
#         queryset = Product.objects.all()
#         serializer = ProductSerializer(queryset, many=True, context={'request': request})
#         return Response(serializer.data)
#
#     def post(self, request):
#         serializer = ProductSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
#
#
# class ProductDetail(APIView):
#     def get(self, request, pk):
#         product = get_object_or_404(Product, pk=pk)
#         serializer = ProductSerializer(product)
#         return Response(serializer.data)
#     def patch(self, request, pk):
#         product = get_object_or_404(Product, pk=pk)
#         serializer = ProductSerializer(product, data=request)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)
#
#     def delete(self, request, pk):
#         product = get_object_or_404(Product, pk=pk)
#         if product.orderitems.count() > 0:
#             return Response({'error' : 'can not be deleted!'})
#
"""function api view example"""
# @api_view(['GET', 'POST'])
# def collection_list(request):
#     if request.method == 'GET':
#         queryset = Collection.objects.annotate(products_count=Count('products')).all()
#         serializer = CollectionSerializer(queryset, many=True)
#         return Response(serializer.data)
#     elif request.method == 'POST':
#         serializer = CollectionSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
#
#
# @api_view(['GET', 'PUT', 'DELETE'])
# def collection_detail(request, pk):
#     collection = get_object_or_404(Collection.objects.annotate(products_count=Count('products')), pk=pk)
#     if request.method == 'GET':
#         serializer = CollectionSerializer(collection)
#         return Response(serializer.data)
#     elif request.method == 'PUT':
#         serializer = CollectionSerializer(collection, data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)
#     elif request.method == 'DELETE':
#         if collection.products_count > 0:
#             return Response({'error': 'Collection cannot be deleted'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
#         collection.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)
"""now we use GENERIC VIEW"""
"""https://www.django-rest-framework.org/api-guide/generic-views/"""

"""exasmple for overwriting these methods"""

# class ProductList(ListCreateAPIView):
#     def get_queryset(self):
#         return Product.objects.all().select_related('collection')
#
#     def get_serializer_class(self):
#         return ProductSerializer
#
#     def get_serializer_context(self):
#         return {'request': self.request}
"""Generic view example"""
# class ProductList(ListCreateAPIView):
#     queryset = Product.objects.all()
#     serializer_class = ProductSerializer
#
#     def get_serializer_context(self):
#         return {'request': self.request}
#
#
# class ProductDetail(RetrieveUpdateDestroyAPIView):
#     queryset = Product.objects.all()
#     serializer_class = ProductSerializer
#
#     def delete(self, request, pk):
#         product = get_object_or_404(Product, pk=pk)
#         if product.orderitems.count() > 0:
#             return Response({'error': 'can not be deleted!'})
#         product.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)
# class CollectionList(ListCreateAPIView):
#     queryset = Collection.objects.annotate(products_count=Count('products')).all()
#     serializer_class = CollectionSerializer
#
#
# class CollectionDetail(RetrieveUpdateDestroyAPIView):
#     queryset = Collection.objects.annotate(products_count=Count('products')).all()
#     serializer_class = CollectionSerializer
#
#     def delete(self, request, pk):
#         collection = get_object_or_404(Collection, pk=pk)
#         if collection.products.count() > 0:
#             return Response({'error': 'can not be deleted!'})
#         collection.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)
"""now we use View Set"""


class ProductViewSet(ModelViewSet):
    # queryset = Product.objects.all().prefetch_related('images')
    serializer_class = ProductSerializer
    pagination_class = DefaultPagination
    filter_backends = [RecursiveDjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['translations__title', 'translations__description']
    ordering_fields = ['unit_price', 'updated_at']
    permission_classes = [IsAdminOrReadOnly]

    """we can manually filter by overwrite get_queryset function"""

    # def get_queryset(self):
    #     queryset = Product.objects.all()
    #     collection_id = self.request.query_params.get('collection_id')
    #     if collection_id is not None:
    #         queryset = queryset.filter(collection_id=collection_id)
    #     return queryset

    def get_queryset(self):
        queryset = Product.objects.select_related('collection').prefetch_related('images', 'mainfeature_set')

        collection_id = self.request.query_params.get('collection_id')
        if collection_id:
            q_object = RecursiveDjangoFilterBackend().get_recursive_q(collection_id)
            queryset = queryset.filter(q_object)

        lt = self.request.query_params.get('unit_price__lt')
        gt = self.request.query_params.get('unit_price__gt')
        if lt and gt:
            unit_price_filters = RecursiveDjangoFilterBackend().get_unit_price_filters(self.request)
            queryset = queryset.filter(unit_price_filters)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(translations__title__contains=search)

        feature_key = self.request.query_params.get('feature_key')
        feature_value = self.request.query_params.get('feature_value')
        if feature_key:
            queryset = queryset.filter(mainfeature__key__id=feature_key)
        if feature_value:
            queryset = queryset.filter(mainfeature__value__id=feature_value)

        secondhand = self.request.query_params.get('secondhand')
        if secondhand in ('true', 'false'):
            secondhand_bool = secondhand == 'true'
            queryset = queryset.filter(secondhand=secondhand_bool)

        ordering = self.request.query_params.get('ordering', 'updated_at')
        try:
            queryset = queryset.order_by(ordering)
        except FieldError:
            """https://stackoverflow.com/questions/40950251/django-rest-ordering-custom"""
            """:-/"""
            if ordering == 'best_sales':
                queryset = self.order_by_best_sales(queryset)

        views_logger.info("Filtering queryset for products.")

        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        views_logger.info(f"Listing product page {page} for products.")

        return Response(serializer.data)

    def get_serializer_context(self):
        return {'request': self.request}

    def destroy(self, request, *args, **kwargs):
        if OrderItem.objects.filter(product_id=kwargs['pk']).count() > 0:
            return Response({'error': 'can not be deleted!'})
        return super.destroy(request, *args, **kwargs)

    def order_by_best_sales(self, queryset):
        return (
            queryset.annotate(
                used_products=Sum('orderitems__quantity', distinct=True),
                total_sales=Sum(
                    (F('orderitems__unit_price') * 1.0000000001 * F('orderitems__quantity')),
                    output_field=DecimalField()
                )
            )
            .order_by('-used_products')
        )


class CollectionViewSet(ModelViewSet):
    queryset = Collection.objects.annotate(products_count=Count('products')).filter(parent__isnull=True)
    serializer_class = CollectionSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_products_count(self, collection):
        products_count = Product.objects.filter(collection=collection).count()
        subcollections = collection.subcollection.all()
        for subcollection in subcollections:
            products_count += self.get_products_count(subcollection)
        return products_count

    def update_products_count(self, data):
        for collection_data in data:
            collection = Collection.objects.get(id=collection_data['id'])
            collection_data['products_count'] = self.get_products_count(collection)
            if collection_data.get('children'):
                self.update_products_count(collection_data['children'])

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        data = serializer.data
        self.update_products_count(data)

        return Response(data)

    def destroy(self, request, *args, **kwargs):
        if Product.objects.filter(collection=kwargs['pk']).count() > 0:
            return Response({'error': 'can not be deleted!'})
        return super().destroy(request, *args, **kwargs)

    def filter_products_by_collection(self, collection):
        products = Product.objects.filter(collection=collection)
        subcollections = collection.subcollection.all()
        for subcollection in subcollections:
            products |= self.filter_products_by_collection(subcollection)
        return products

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        products = self.filter_products_by_collection(instance)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class ReviewViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'head', 'options']
    serializer_class = ReviewSerializer
    filter_backends = [SearchFilter]
    search_fields = ['title', 'description']
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs['product_pk'], active=True, parent_review=None)

    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk'], 'user_id': self.request.user.id}

    @swagger_auto_schema(
        methods=['get'],
        responses={
            200: 'Successful response',
            404: 'Not found',
        }
    )
    @action(detail=True, methods=['GET'])
    def replies(self, request, *args, **kwargs):
        review = self.get_object()
        replies = Review.objects.filter(parent_review=review)
        serializer = self.get_serializer(replies, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        review_id = kwargs.get('pk')

        try:
            review = Review.objects.get(id=review_id, active=True)
        except Review.DoesNotExist:
            return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(review)
        data = serializer.data

        replies = Review.objects.filter(parent_review=review)
        reply_serializer = self.get_serializer(replies, many=True)
        data['replies'] = reply_serializer.data

        return Response(data)


class PromotionViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer

    def get_permissions(self):
        if self.request.method in ['PATCH', 'DELETE', 'PUT', 'POST']:
            return [IsAdminUser()]
        else:
            return []

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        products = Product.objects.filter(promotions=instance)
        products_serializer = SimpleProductSerializer(products, many=True)
        data['products'] = products_serializer.data

        return Response(data)


class CartViewSet(CreateModelMixin,
                  RetrieveModelMixin,
                  DestroyModelMixin,
                  GenericViewSet):

    def get_queryset(self):
        return Cart.objects.all().prefetch_related('items__product')

    serializer_class = CartSerializer

    def get_serializer_context(self):
        return {'user_id': self.request.user.id}

    def create(self, request, *args, **kwargs):
        user_id = request.user.id
        try:
            customer = Customer.objects.get(user_id=user_id)
            existing_cart = Cart.objects.filter(customer_id=customer.id).order_by('-updated_at').first()
            if existing_cart:
                serializer = self.get_serializer(existing_cart, data=request.data)
            else:
                print('create cart new', request.data)
                serializer = self.get_serializer(data=request.data)
        except Customer.DoesNotExist:
            serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @swagger_auto_schema(
        methods=['get', 'post'],
        responses={
            200: 'Successful response (Apply Discount)',
            400: 'Bad request',
        },

    )
    @action(detail=True, methods=['get', 'post'])
    def apply_discount(self, request, pk=None):
        cart = self.get_object()

        if request.method == 'GET':
            serializer = ApplyDiscountSerializer()
            return Response(serializer.data)

        serializer = ApplyDiscountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        discount_code = serializer.validated_data['discount_code']
        try:
            discount = BaseDiscount.objects.get(code=discount_code)
            if not discount.active:
                raise ValidationError(_("Discount is not active."))
            if not discount.ensure_availability():
                raise ValidationError(_("Discount is not available at the moment."))
            total_price = CartSerializer(data=cart)
            total_price = total_price.get_total_price(cart)
            print('total_price', total_price)

            if total_price < discount.limit_price:
                raise ValidationError(_("Total price is below the discount limit."))
            cart.discount = discount
            cart.save()

            return Response({'message': 'Discount applied successfully.'}, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({'error': e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except BaseDiscount.DoesNotExist:
            return Response({'error': _('Discount Code Not Found')}, status=status.HTTP_400_BAD_REQUEST)


class CartItemViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        return CartItem.objects.filter(cart_id=self.kwargs['cart_pk']).select_related('product')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddItemsSerializer
        elif self.request.method == 'PATCH':
            return UpdateItemsSerializer
        return CartItemSerializer

    def get_serializer_context(self):
        return {'cart_id': self.kwargs['cart_pk']}


class CustomerViewSet(ModelViewSet):
    http_method_names = ['get', 'put']

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email']
    ordering_fields = ['membership', 'user_id']
    permission_classes = [IsAdminUser]

    """we can overwrite like this!"""

    # def get_permissions(self):
    #     if self.request.method == 'GET':
    #         return [IsAuthenticated()]
    #     else:
    #         return [IsAdminUser()]

    @action(detail=False, methods=['GET', 'PUT'], permission_classes=[IsAuthenticated])
    def me(self, request):
        user_id = request.user.id
        customer = Customer.objects.get(user_id=user_id)
        if request.method == 'GET':
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @swagger_auto_schema(
        methods=['get'],
        responses={
            200: 'Successful response',
            403: 'Permission Denied',
        }
    )
    @action(detail=True, permission_classes=[ViewCustomerHistoryPermission], methods=['get'])
    def history(self, request, pk):
        user = User.objects.get(pk=pk)
        data = AuditLog.objects.all().filter(user=user)
        serializer = AuditLogSerializer(data, many=True)

        return Response(serializer.data)


class OrderViewSet(ModelViewSet):
    http_method_names = ['get', 'patch', 'post', 'delete', 'head', 'options']
    filter_backends = [CustomerFilterBackend]

    def get_permissions(self):
        if self.request.method in ['PATCH', 'DELETE']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        try:
            serializer = CreateOrderSerializer(data=request.data, context={'user_id': self.request.user.id})
        except serializer.ValidationError:
            return Response(_('Item deleted from your cart because limit inventory'),
                            status=status.HTTP_400_BAD_REQUEST)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        customer_id = Customer.objects.only('id').get(user_id=user.id)
        return Order.objects.filter(customer_id=customer_id)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateOrderSerializer
        elif self.request.method == 'PATCH':
            return UpdateOrderSerializer
        return OrderSerializer

    @swagger_auto_schema(
        methods=['post'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'order_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            required=['order_id'],
        ),
        responses={
            200: 'Successful response',
            400: 'Bad Request',
            503: 'Service Unavailable',
        }
    )
    @action(detail=True, methods=['post'], url_path='payment-request')
    def payment_request(self, request, pk=None):
        order = self.get_object()
        domain = request.get_host()
        Mobile = order.customer.user.phone_number
        Email = order.customer.user.email
        Amount = order.get_total_price()
        Description = f'user {Mobile} wants to pay {Amount}'
        MerchantID = settings.MERCHANT
        CallbackURL = domain + '/api-v1/zar-request/'
        print('CallbackURL', CallbackURL)
        print('CallbackURL', type(CallbackURL))
        print(MerchantID, Amount, Description, Email, Mobile, CallbackURL)
        if True :
            print('success merchangt result sandbax')
            return Response(
                {'redirect': settings.ZP_API_STARTPAY,
                    'Authority': str('sdfasd')},
                status=status.HTTP_200_OK)
    


class ProductImageViewSet(ModelViewSet):
    serializer_class = ProductImageSerializer

    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk']}

    def get_queryset(self):
        return ProductImage.objects.filter(prodcut_id=self.kwargs['product_pk'])


class AddressViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer

    def get_serializer_context(self):
        customer = Customer.objects.get(user_id=self.request.user.id)
        return {'customer_id': customer.id}

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Address.objects.all()
        else:
            return Address.objects.filter(customer__user_id=user.id)


class TransactionViewSet(ModelViewSet):
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']
    permission_classes = [IsAdminUser]
    queryset = Transaction.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TransactionSerializer
        elif self.request.method == 'PATCH':
            return UpdateTransactionSerializer


class ReportingAPIView(APIView):
    """
    {
        "days": "1"
    }
    """

    def post(self, request, *args, **kwargs):
        serializer = ReportingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reporting_data = Reporting(serializer.validated_data)

        total_sales = reporting_data.total_sales()
        favorite_products = list(reporting_data.favorite_products())
        best_cutomer = reporting_data.best_cutomer()
        favorite_collection = list(reporting_data.favorite_collection())
        order_status_counts = list(reporting_data.order_status_counts())

        response_data = {
            'total_sales': total_sales,
            'favorite_products': favorite_products,
            'best_cutomer': best_cutomer,
            'favorite_collection': favorite_collection,
            'order_status_counts': order_status_counts,
        }

        return Response(response_data, status=status.HTTP_200_OK)


class SiteSettingsViewSet(ModelViewSet):
    queryset = SiteSettings.objects.all()
    serializer_class = SiteSettingsSerializer


class HomeBannerViewSet(ReadOnlyModelViewSet):
    queryset = HomeBanner.objects.all()
    serializer_class = HomeBannerSerializer


@swagger_auto_schema(
    method='GET',
    manual_parameters=[
        openapi.Parameter(
            name='product_ids',
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_ARRAY,
            items=openapi.Items(type=openapi.TYPE_INTEGER),
            description='List of product IDs to compare',
            required=True,
        ),
    ],
    responses={
        200: 'Successful response',
        400: 'Bad Request',
    }
)
@api_view(['GET'])
def compare_products(request):
    product_ids = request.GET.getlist('product_ids')
    products = Product.objects.filter(id__in=product_ids)
    data = {}

    productattr = ['Title', 'Price_after_off', 'Collection', 'Images']
    for attr in productattr:
        product_attrs = {}
        for product in products:
            if attr == 'Collection':
                try:
                    product_attrs[str(product.title)] = str(eval(f'product.{attr.lower()}.title'))
                except AttributeError:
                    product_attrs[str(product.title)] = None
            elif attr == 'Images':
                product_attrs[str(product.title)] = str(eval(f'product.{attr.lower()}.first().image'))
            else:
                product_attrs[str(product.title)] = str(eval(f'product.{attr.lower()}'))

        if attr == 'Price_after_off':
            attr = _('Price')
        if attr == 'Collection':
            attr = _('Collection')
        if attr == 'Title':
            attr = _('Title')
        if attr == 'Images':
            attr = _('Images')

        attr = str(attr)
        data[attr] = product_attrs

    feature_keys = []
    for product in products:
        main_features = MainFeature.objects.filter(product=product)
        for main_feature in main_features:
            feature_keys.append(main_feature.key)

    for key in feature_keys:
        feature_data = {}
        for product in products:
            main_features = MainFeature.objects.filter(product=product, key=key)
            if main_features:
                values = []
                for main_feature in main_features:
                    values.append(str(main_feature.value.value))
                feature_data[
                    str(product.title)] = str(', '.join(values))
            else:
                feature_data[str(product.title)] = None
        data[str(key.key)] = feature_data
    return Response(data)


class FeatureViewSet(ModelViewSet):
    queryset = FeatureKey.objects.all()
    serializer_class = FeatureKeyFullSerializer


class VerifyAPIView(APIView):
    """
    {
"order_id": "1",
"total_price": "1000",
"Authority": "000000000000000000000000000001349929"
}
    """
    serializer_class = VerifySerializer

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'order_id': openapi.Schema(type=openapi.TYPE_STRING),
                'total_price': openapi.Schema(type=openapi.TYPE_STRING),
                'Authority': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={
            200: 'Transaction success',
            400: 'Bad Request',
        }
    )
    def post(self, request, *args, **kwargs):  # pragma: no cover
        client = Client(settings.ZP_API)

        MERCHANT = settings.MERCHANT
        order_id = request.data.get('order_id', '')
        amount = int(request.data.get('total_price', ''))
        Authority = request.data.get('Authority', '')
        transaction = Transaction.objects.get(order_id=order_id)
        order = transaction.order
        print(amount)
        print(type(amount))
        # result = client.service.PaymentVerification(MERCHANT, Authority, amount)
        # print(result)
        if True:
            # transaction.receipt_number = str(result.RefID)
            transaction.receipt_number = str("111")
            transaction.Authority = Authority
            transaction.payment_status = 'C'
            customer = transaction.customer
            order.order_status = 'P'
            order.save()
            cart = Cart.objects.filter(customer=customer.id)
            cart.delete()
            transaction.save()
            print(request.user)
            print('PAYMENT FINISHED!!!')
            return Response({'details': 'Transaction success. RefID: ' + str("111")},
                            status=200)
        elif result.Status == 100:
            transaction.receipt_number = str(result.RefID)
            transaction.Authority = Authority
            transaction.payment_status = 'C'
            customer = transaction.customer
            order.order_status = 'P'
            order.save()
            cart = Cart.objects.filter(customer=customer.id)
            cart.delete()
            transaction.save()
            return Response({'details': 'Transaction success. RefID: ' + str(result.RefID)},
                            status=200)
        elif result.Status == 101:
            return Response({'details': 'Transaction submitted'}, status=200)
        else:
            transaction.payment_status = 'F'
            order.order_status = 'F'
            order.save()
            transaction.save()
            new_inventories = []
            order_items = OrderItem.objects.filter(order_id=order.id)
            for items in order_items:
                product = items.product
                quantity = items.quantity
                product.inventory += quantity
                new_inventories.append(product)
            Product.objects.bulk_update(new_inventories, ['inventory'])
            return Response({'details': 'Transaction failed . error code : ' + str(result.Status)},
                            status=200)
