import uuid
import logging
from decimal import Decimal
from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers
from discount.models import BaseDiscount
from core.models import AuditLog, User
from shop.models import Product, Collection, Review, Customer, Order, OrderItem, ProductImage, CartItem, Cart, Address, \
    Transaction, MainFeature, Promotion, SiteSettings, HomeBanner, FeatureKey, FeatureValue
from parler_rest.serializers import TranslatableModelSerializer, TranslatedFieldsField
from django.utils.translation import gettext_lazy as _

views_logger = logging.getLogger('views_logger')


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']

    def create(self, validated_data):
        product_id = self.context['product_id']
        return ProductImage.objects.create(product_id=product_id, **validated_data)


class FeatureValueFullSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=FeatureValue)
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = FeatureValue
        fields = ['id', 'translations', 'product_count', 'value']

    def get_product_count(self, obj):
        return MainFeature.objects.filter(value=obj).count()


class FeatureKeyFullSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=FeatureKey)
    values = serializers.SerializerMethodField()
    key_product_count = serializers.SerializerMethodField()

    class Meta:
        model = FeatureKey
        fields = ['id', 'translations', 'key_product_count', 'values', 'key']

    def get_values(self, obj):
        children_serializer = FeatureValueFullSerializer(obj.values.all(), many=True)
        return children_serializer.data if obj.values.exists() else None

    def get_key_product_count(self, obj):
        return MainFeature.objects.filter(key=obj).values('product').count()


class FeatureKeySerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=FeatureKey)

    class Meta:
        model = FeatureKey
        fields = ['id', 'translations', 'key']


class FeatureValueSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=FeatureValue)

    class Meta:
        model = FeatureValue
        fields = ['id', 'key', 'translations', 'value']


class MainFeatureSerializer(TranslatableModelSerializer):
    id = serializers.IntegerField(read_only=True)
    key = FeatureKeySerializer()
    value = FeatureValueSerializer()

    class Meta:
        model = MainFeature
        fields = ['id', 'key', 'value']
        allow_null = True


class ProductSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Product)
    value_feature = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'translations', 'inventory', 'org_price',
                  'price', 'price_with_tax', 'collection_id', 'promotions', 'value_feature', 'images', 'secondhand',
                  'title', 'description', 'slug', 'badge']

    images = ProductImageSerializer(many=True, read_only=True)
    collection_id = serializers.IntegerField(required=False)
    price = serializers.DecimalField(max_digits=15, decimal_places=2, source='price_after_off', required=False)
    org_price = serializers.DecimalField(max_digits=15, decimal_places=2, source='unit_price')
    price_with_tax = serializers.SerializerMethodField(method_name='calculate_tax')

    """4 ways to serialize relations : 1.pk 2.object 3.string 4.hyperlink"""

    def calculate_tax(self, product: Product):
        return product.unit_price * Decimal(1.1)

    def create(self, validated_data):
        if 'title' in validated_data:
            validated_data['slug'] = slugify(validated_data['title'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'title' in validated_data:
            validated_data['slug'] = slugify(validated_data['title'])
        return super().update(instance, validated_data)

    def get_value_feature(self, product):
        main_features = MainFeature.objects.filter(product_id=product.id)
        serializer = MainFeatureSerializer(main_features, many=True)
        return serializer.data


class SimpleProductSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Product)
    images = ProductImageSerializer(many=True, read_only=True)
    org_price = serializers.DecimalField(max_digits=15, decimal_places=2, source='unit_price')
    price = serializers.DecimalField(max_digits=15, decimal_places=2, source='price_after_off')

    class Meta:
        model = Product
        fields = ['id','images' ,'translations', 'org_price', 'price', 'title', 'description', 'badge']

    """validation example"""
    # def validate(self,data):
    #     if True:
    #         return data
    #     else: return serializers.ValidationError('msg')

    """create method overwrite"""
    # def create(self, validated_data):
    #     product = Product(**validated_data)
    #     product.other = 1
    #     product.save()
    #     return product

    """update method overwrite"""
    # def update(self, instance, validated_data):
    #     instance.unit_price = validated_data.get('unit_price')
    #     instance.save()
    #     return instance


class CollectionSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Collection)
    children = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = ['id', 'translations', 'parent', 'products_count', 'children', 'title']

    products_count = serializers.IntegerField(read_only=True)

    def get_children(self, obj):
        children_serializer = self.__class__(obj.subcollection.all(), many=True)
        return children_serializer.data if obj.subcollection.exists() else None


class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, cart_item: CartItem):
        return cart_item.quantity * cart_item.product.price_after_off

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'total_price']


class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    org_price = serializers.SerializerMethodField()

    # def get_total_price(self, cart):
    #     if cart.items:
    #         return sum([item.quantity * item.product.price_after_off for item in cart.items.all()])
    #     else:
    #         return 0

    def get_total_price(self, cart):
        if cart.discount:
            cart.discount.ensure_availability()
            if cart.discount.active:
                print(cart.discount.mode)
                print('total_price')
                if cart.discount.mode == cart.discount.Mode.DirectPrice:
                    total_price = sum([item.quantity * item.product.price_after_off for item in
                                       cart.items.all()]) - cart.discount.discount
                    print(total_price)
                elif cart.discount.mode == cart.discount.Mode.DiscountOff:
                    total_price = sum(
                        [item.quantity * item.product.price_after_off for item in cart.items.all()]) - sum(
                        [item.quantity * item.product.price_after_off for item in
                         cart.items.all()]) * cart.discount.discount / 100
                elif (cart.discount.mode == cart.discount.Mode.PersonCode or
                      cart.discount.mode == cart.discount.Mode.EventCode):
                    total_price_with_out_off = sum(
                        [item.quantity * item.product.price_after_off for item in cart.items.all()])
                    if total_price_with_out_off > cart.discount.max_price:
                        total_price = total_price_with_out_off - cart.discount.max_price

                    elif total_price_with_out_off < cart.discount.limit_price:
                        total_price = total_price_with_out_off

                    else:
                        total_price = total_price_with_out_off - total_price_with_out_off * cart.discount.discount / 100

                else:
                    raise ValueError(_(f"Invalid discount mode: {cart.discount.mode}"))
            else:
                cart.discount = None
                cart.save()
                raise ValueError(_(f"Discount is not active!"))

        else:
            total_price = sum([item.quantity * item.product.price_after_off for item in
                               cart.items.all()])

        print(total_price)
        return total_price if total_price is not None else 0

    def get_org_price(self, cart):
        org_price = sum([item.quantity * item.product.price_after_off for item in
                         cart.items.all()])
        return org_price if org_price is not None else 0

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price', 'org_price']


class ApplyDiscountSerializer(serializers.Serializer):
    discount_code = serializers.CharField(help_text='discount_code', label='discount_code')


class AddItemsSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()

    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'quantity']

    def save(self, **kwargs):
        cart_id = self.context['cart_id']
        product_id = self.validated_data['product_id']
        quantity = self.validated_data['quantity']
        product_inventory = Product.objects.get(id=product_id).inventory
        try:
            cart_item = CartItem.objects.get(cart_id=cart_id, product_id=product_id)
            cart_item.quantity += quantity
            if cart_item.quantity > product_inventory:
                raise serializers.ValidationError(_(f'You can not add more then inventory {product_inventory} !'))
            cart_item.save()
            self.instance = cart_item
        except CartItem.DoesNotExist:
            if quantity > product_inventory:
                raise serializers.ValidationError(_(f'You can not add more then inventory {product_inventory} !'))
            self.instance = CartItem.objects.create(cart_id=cart_id, **self.validated_data)
        return self.instance

    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError(_('No Prodcuts found!'))
        else:
            return value

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError(_('Most be at least 1 !'))
        else:
            return value


class UpdateItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']

    def save(self, **kwargs):
        instance = super().save(**kwargs)
        cart_id = self.context.get('cart_id')
        quantity = self.validated_data['quantity']

        product_id = instance.product_id
        product_inventory = Product.objects.get(id=product_id).inventory
        if quantity > product_inventory:
            instance.quantity = product_inventory
            instance.save()
            raise serializers.ValidationError(_(f'You cannot add more than inventory {product_inventory}!'))

        return instance

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError(_('Most be at least 1 !'))
        else:
            return value


class CustomerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    membership = serializers.CharField(read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'first_name', 'last_name', 'user_id', 'birth_date', 'membership']


class ReviewSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'created_at', 'parent_review', 'title', 'description', 'rating', 'customer', 'replies']

    def get_replies(self, obj):
        children_serializer = self.__class__(obj.replies.all(), many=True)
        return children_serializer.data if obj.replies.exists() else None

    # def to_representation(self, instance):
    #     if instance.active:
    #         return super().to_representation(instance)
    #     return None

    def create(self, validated_data):
        product_id = self.context['product_id']
        try:
            customer = Customer.objects.get(user_id=self.context['user_id'])
        except Customer.DoesNotExist:
            raise serializers.ValidationError(_('User not found'))
        return Review.objects.create(product_id=product_id, customer=customer, **validated_data)


class OrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    price = serializers.DecimalField(max_digits=15, decimal_places=2, source='unit_price')

    class Meta:
        model = OrderItem
        fields = ('product', 'price', 'quantity')


class OrderSerializer(serializers.ModelSerializer):
    orders = OrderItemSerializer(many=True)
    total_price = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            'id', 'order_status', 'customer', 'phone_number', 'email', 'zip_code', 'path', 'city', 'province',
            'first_name', 'last_name',
            'orders', 'updated_at',
            'total_price')

    def get_total_price(self, order):
        return order.get_total_price()

    def get_email(self, order):
        user = User.objects.get(id=order.customer.user_id)
        return user.email

    def get_phone_number(self, order):
        user = User.objects.get(id=order.customer.user_id)
        return user.phone_number


class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()

    def validate_cart_id(self, value):
        if not Cart.objects.filter(pk=value).exists():
            raise serializers.ValidationError(_('No cart found!'))
        if CartItem.objects.filter(cart_id=value).count() == 0:
            raise serializers.ValidationError(_('Cart is empty!'))
        return value

    def save(self, **kwargs):
        with transaction.atomic():
            cart_id = self.validated_data['cart_id']
            customer = Customer.objects.get(user_id=self.context['user_id'])
            first_name = customer.first_name
            last_name = customer.last_name
            address: Address = customer.address_set.filter(default=True).first()
            if not address:
                raise serializers.ValidationError(_('You dont have address set please set your default address!'))
            zip_code = address.zip_code
            province = address.province
            path = address.path
            city = address.city
            discount: BaseDiscount = Cart.objects.get(id=cart_id).discount

            order = Order.objects.create(customer=customer, first_name=first_name, last_name=last_name,
                                         zip_code=zip_code, province=province, path=path, city=city, discount=discount)
            cart_items = CartItem.objects.filter(cart_id=cart_id)
            new_inventories = []
            order_items = []
            for item in cart_items:
                if item.quantity <= item.product.inventory:
                    order_item = OrderItem(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        unit_price=item.product.price_after_off
                    )
                    order_items.append(order_item)
                    product = item.product
                    product.inventory -= item.quantity
                    new_inventories.append(product)
                else:
                    raise serializers.ValidationError(
                        _(f'product {item.product.title} has limited inventory: {item.product.inventory}'))
            OrderItem.objects.bulk_create(order_items)
            Product.objects.bulk_update(new_inventories, ['inventory'])
            "https://stackoverflow.com/questions/30632743/how-can-i-use-signals-in-django-bulk-create"
            print('done saving')
            # Cart.objects.filter(pk=cart_id).delete()

            transactions = Transaction.objects.get(order=order)
            print(order.discount)
            print(order.get_total_price())
            total_price = order.get_total_price()
            transactions.total_price = total_price
            transactions.save()
            if discount:
                print('discount here:', discount.mode)
                views_logger.info(f'discount here: {discount.mode}')
                views_logger.info(f'discount here: {dir(discount.mode)}')
                views_logger.info(f'discount here too: {discount.mode == BaseDiscount.Mode.PersonCode}')
                if discount.mode == BaseDiscount.Mode.PersonCode:
                    views_logger.info(f'discount here: {discount.mode}')
                    views_logger.info(f'discount here: {discount}')

                    discount.active = False
                    views_logger.info(f'discount here: {discount}')
                    discount.save()
            return order


class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['order_status']


class AddressSerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Address
        fields = ('id', 'zip_code', 'path', 'city', 'province', 'default', 'customer_id')

    def create(self, validated_data):
        customer_id = self.context['customer_id']
        return Address.objects.create(customer_id=customer_id, **validated_data)


class TransactionSerializer(serializers.ModelSerializer):
    order = serializers.HyperlinkedRelatedField(
        queryset=Order.objects.all(),
        view_name='orders-detail'
    )

    class Meta:
        model = Transaction
        fields = ['id', 'payment_status', 'order', 'total_price', 'customer', 'receipt_number']


class UpdateTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['payment_status', 'receipt_number']


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['user', 'action', 'timestamp', 'table_name', 'row_id', 'changes']


class PromotionSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Promotion)

    class Meta:
        model = Promotion
        fields = ['id', 'translations', 'title', 'description']


class ReportingSerializer(serializers.Serializer):
    days = serializers.IntegerField(required=False)
    start_at = serializers.DateTimeField(required=False)
    end_at = serializers.DateTimeField(required=False)


class SiteSettingsSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=SiteSettings)

    class Meta:
        model = SiteSettings
        fields = ['id', 'phone_number', 'logo', 'telegram_link', 'twitter_link', 'instagram_link', 'whatsapp_link',
                  'translations', 'footer_text', 'address']


class HomeBannerSerializer(serializers.ModelSerializer):
    product = ProductSerializer(many=True)

    class Meta:
        model = HomeBanner
        fields = ['id', 'product']

        read_only_fields = ['id']


class SendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['phone_number', 'total_price']


class VerifySerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['order', 'total_price', 'Authority']
