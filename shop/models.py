import uuid

from django.contrib import admin
from django.db import models
from django.conf import settings
from django.db.models import Sum, F
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _, get_language
from parler.models import TranslatableModel, TranslatedFields
from shop.validator import validate_file_size, validate_key_value_relationship
from discount.models import BaseDiscount
from core.models import BaseModel
from solo.models import SingletonModel

admin.site.site_header = _('Site Administration')
admin.site.index_title = _('Index Title')
admin.site.site_title = _('Site Management')


class Promotion(TranslatableModel, BaseModel):
    """
    Model representing a promotion.

    Attributes:
        title (CharField): The title of the promotion.
        description (CharField, optional): The description of the promotion.
    """
    translations: TranslatedFields = TranslatedFields(
        title=models.CharField(_('Title'), max_length=255),
        description=models.CharField(_("Description"), max_length=500, null=True, blank=True)
    )

    class Meta:
        verbose_name = _("Promotion")
        verbose_name_plural = _("Promotions")

    # def clean(self):
    #     existing_discount_item = self.discount.objects.filter(
    #         content_type=self.content_type,
    #         object_id=self.object_id,
    #         discount__active=True
    #     ).exclude(pk=self.pk)
    #
    #     if existing_discount_item.exists():
    #         raise ValidationError(_('There is already an active discount for this item.'))

    def __repr__(self):
        # default_language = get_language() or 'en'
        # description_translation = self.translations.get(language_code=default_language)
        # description = description_translation.description if description_translation else f"Promotion {self.pk}"
        return f'{self.title} '

    def __str__(self):
        return f'{self.title}'


class Collection(TranslatableModel, BaseModel):
    """
    Model representing a collection of products.

    Attributes:
        title (CharField): The title of the collection.
        parent (ForeignKey, optional): The parent collection if this is a sub-collection.
    """
    translations = TranslatedFields(
        title=models.CharField(_('Title'), max_length=255)
    )

    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcollection',
                               verbose_name=_("Parent"))

    @property
    def is_subcollection(self):
        return self.parent is not None

    def __repr__(self):
        return f'{self.title}'

    def __str__(self):
        return f'{self.title}'

    def get_products_count(self):
        count = self.products.count()
        for subcollection in self.subcollection.all():
            count += subcollection.get_products_count()
        return count

    class Meta:
        verbose_name = _("Collection")
        verbose_name_plural = _("Collections")
        # ordering = ["translations__title"]


class Product(TranslatableModel, BaseModel):
    """
    Model representing a product.

    Attributes:
        title (CharField): The title of the product.
        description (TextField, optional): The description of the product.
        unit_price (DecimalField): The unit price of the product.
        inventory (IntegerField): The inventory count of the product.
        min_inventory (IntegerField, optional): The minimum inventory threshold.
        collection (ForeignKey, optional): The collection to which the product belongs.
        promotions (ForeignKey, optional): The promotions associated with the product.
        discount (ForeignKey, optional): The discount associated with the product.
        secondhand (BooleanField): Indicates whether the product is secondhand.
    """
    translations = TranslatedFields(
        title=models.CharField(_("Title"), max_length=255),
        slug=models.SlugField(_("Slug"), null=True, blank=True),
        description=models.TextField(_("Description"), null=True, blank=True)
    )
    unit_price = models.DecimalField(_("Unit Price"), max_digits=15, decimal_places=2,
                                     validators=[MinValueValidator(1)])
    inventory = models.IntegerField(_("Inventory"), validators=[MinValueValidator(0)])
    min_inventory = models.IntegerField(_("Minimum Inventory"), validators=[MinValueValidator(0)],
                                        null=True, blank=True)

    collection = models.ForeignKey(Collection, on_delete=models.PROTECT, verbose_name=_("Collection"),
                                   related_name='products', null=True, blank=True)
    promotions = models.ForeignKey(Promotion, on_delete=models.CASCADE, null=True, blank=True,
                                   verbose_name=_("Promotions"),
                                   related_name='products')
    discount = models.ForeignKey(BaseDiscount, on_delete=models.CASCADE, verbose_name=_("Discount"),
                                 null=True, blank=True)
    secondhand = models.BooleanField(_('Seccond Hand'), default=False, )

    badge = models.CharField(_("Badge"), max_length=255, null=True, blank=True)

    # extra_data = models.JSONField(verbose_name='Features', null=True, blank=True)

    def __repr__(self):
        # default_language = get_language() or 'en'
        # title_translation = self.translations.get(language_code=default_language)
        # title = title_translation.title if title_translation else f"Product {self.pk}"
        return f'{self.title}'

    def __str__(self):
        return f'{self.title}'

    @property
    def price_after_off(self, ):
        if self.discount:
            self.discount.ensure_availability()
            if self.discount.mode == self.discount.Mode.DirectPrice:
                return self.unit_price - self.discount.discount
            elif self.discount.mode == self.discount.Mode.DiscountOff:
                return self.unit_price - (self.unit_price * self.discount.discount / 100)
            else:
                raise ValueError(f"Invalid discount mode: {self.discount.mode}")
        return self.unit_price

        # def clean(self):
        #     existing_discount_item = self.discount.objects.filter(
        #         content_type=self.content_type,
        #         object_id=self.object_id,
        #         discount__active=True
        #     ).exclude(pk=self.pk)

        # if existing_discount_item.exists():
        #     raise ValidationError(_('There is already an active discount for this item.'))

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        # ordering = ["translations__title"]


class ProductImage(BaseModel):
    """
    Model representing an image of a product.

    Attributes:
        product (ForeignKey): The product to which the image belongs.
        image (ImageField): The image file.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='shop/images', validators=[validate_file_size])


class Customer(BaseModel):
    """
    Model representing a customer.

    Attributes:
        first_name (CharField): The first name of the customer.
        last_name (CharField): The last name of the customer.
        birth_date (DateField, optional): The birth date of the customer.
        membership (CharField): The membership status of the customer.
        user (OneToOneField): The user associated with the customer.
    """
    class MembershipStatus(models.TextChoices):
        MEMBERSHIP_BRONZE = 'B', _('Bronze')
        MEMBERSHIP_SILVER = 'S', _('Silver')
        MEMBERSHIP_GOLD = 'G', _('Gold')

    first_name = models.CharField(_("First Name"), max_length=255)
    last_name = models.CharField(_("Last Name"), max_length=255)

    birth_date = models.DateField(_("Birth Date"), null=True, blank=True)
    membership = models.CharField(_("Membership"), max_length=1, choices=MembershipStatus,
                                  default=MembershipStatus.MEMBERSHIP_BRONZE)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name=_("User"), on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    class Meta:
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")
        # ordering = ["first_name", "last_name"]
        permissions = [
            ('view_history', 'Can view history')
        ]


class Cart(BaseModel):
    """
    Model representing a shopping cart.

    Attributes:
        id (UUIDField): The unique identifier for the cart.
        customer (ForeignKey, optional): The customer associated with the cart.
        discount (ForeignKey, optional): The discount applied to the cart.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, verbose_name=_("Customer"), null=True, blank=True)
    discount = models.ForeignKey(BaseDiscount, on_delete=models.CASCADE, verbose_name=_("Discount"),
                                 null=True, blank=True)


class CartItem(models.Model):
    """
    Model representing an item in a shopping cart.

    Attributes:
        cart (ForeignKey): The cart to which the item belongs.
        product (ForeignKey): The product being added to the cart.
        quantity (PositiveSmallIntegerField): The quantity of the product in the cart.
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, verbose_name=_("Cart"), related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name=_("Product"))
    # unit_price = models.DecimalField(_('Price'),max_digits=15, decimal_places=2, null=True, blank=True)
    quantity = models.PositiveSmallIntegerField(_("Quantity"))

    class Meta:
        unique_together = [['cart', 'product']]
        verbose_name = _("Cart Item")
        verbose_name_plural = _("Cart Items")


class Address(BaseModel):
    """
    Model representing a customer's address.

    Attributes:
        zip_code (CharField): The postal code of the address.
        path (CharField): The street address.
        city (CharField): The city of the address.
        province (CharField): The province of the address.
        customer (ForeignKey): The customer associated with the address.
        default (BooleanField): Indicates whether the address is the default address for the customer.
    """
    zip_code = models.CharField(_("Zip Code"), max_length=10)
    path = models.CharField(_("Path"), max_length=1025)
    city = models.CharField(_("City"), max_length=255)
    province = models.CharField(_("Province"), max_length=32)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name=_("Customer"))
    default = models.BooleanField(_("Default"), default=True)

    class Meta:
        verbose_name = _("Address")
        verbose_name_plural = _("Addresses")

    def save(self, *args, **kwargs):
        try:
            if self.default:
                Address.objects.filter(customer=self.customer).exclude(id=self.id).update(default=False)

            super().save(*args, **kwargs)
        except:
            raise ValidationError(_("Customer Not Found!"))


class Order(BaseModel):
    """
    Model representing an order.

    Attributes:
        order_status (CharField): The status of the order.
        customer (ForeignKey): The customer who placed the order.
        zip_code (CharField): The postal code of the order.
        path (CharField): The street address of the order.
        city (CharField): The city of the order.
        province (CharField): The province of the order.
        first_name (CharField): The first name of the customer placing the order.
        last_name (CharField): The last name of the customer placing the order.
        discount (ForeignKey, optional): The discount applied to the order.
    """
    class OrderStatus(models.TextChoices):
        ORDER_STATUS_NOT_PAID = 'N', _('Not Paid')
        ORDER_STATUS_PENDING = 'P', _('Pending')
        ORDER_STATUS_SHIPPING = 'S', _('Shipping')
        ORDER_STATUS_DELIVERED = 'D', _('Delivered')
        ORDER_STATUS_FAILED = 'F', _('Failed')

    order_status = models.CharField(_("Payment Status"), max_length=1, choices=OrderStatus,
                                    default=OrderStatus.ORDER_STATUS_NOT_PAID)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, verbose_name=_("Customer"))
    zip_code = models.CharField(_("Zip Code"), max_length=10)
    path = models.CharField(_("Path"), max_length=1025)
    city = models.CharField(_("City"), max_length=255)
    province = models.CharField(_("Province"), max_length=32)
    first_name = models.CharField(_("First Name"), max_length=255)
    last_name = models.CharField(_("Last Name"), max_length=255)
    discount = models.ForeignKey(BaseDiscount, on_delete=models.CASCADE, verbose_name=_("Discount"),
                                 null=True, blank=True)

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")

    def __str__(self):
        return f"{self.id} - {self.customer} - {self.order_status}"

    def get_total_price(self):
        """get total price of order base on discount applied"""
        if self.discount:
            # self.discount.ensure_availability()
            # if self.discount.active:
            print(self.discount.mode)
            print('total_price')
            if self.discount.mode == self.discount.Mode.DirectPrice:
                total_price = \
                    self.orders.aggregate(
                        total_price=Sum(F('unit_price') * F('quantity')) - self.discount.discount)[
                        'total_price']
                print(total_price)
            elif self.discount.mode == self.discount.Mode.DiscountOff:
                total_price = self.orders.aggregate(total_price=Sum(F('unit_price') * F('quantity')) - Sum(
                    F('unit_price') * F('quantity')) * self.discount.discount / 100)['total_price']
            elif (self.discount.mode == self.discount.Mode.PersonCode or
                  self.discount.mode == self.discount.Mode.EventCode):

                total_price_with_out_off = self.orders.aggregate(total_price=Sum(F('unit_price') * F('quantity')))[
                    'total_price']

                if total_price_with_out_off > self.discount.max_price:
                    total_price = total_price_with_out_off - self.discount.max_price

                elif total_price_with_out_off < self.discount.limit_price:
                    total_price = total_price_with_out_off

                else:
                    total_price = self.orders.aggregate(total_price=Sum(F('unit_price') * F('quantity')) - Sum(
                        F('unit_price') * F('quantity')) * self.discount.discount / 100)['total_price']
            else:
                raise ValueError(_(f"Invalid discount mode: {self.discount.mode}"))
        else:
            total_price = self.orders.aggregate(total_price=Sum(F('unit_price') * F('quantity')))['total_price']
        print('last total', total_price)
        return total_price if total_price is not None else 0


class OrderItem(BaseModel):
    """
    Model representing an item in an order.

    Attributes:
        order (ForeignKey): The order to which the item belongs.
        product (ForeignKey): The product being ordered.
        unit_price (DecimalField): The unit price of the product.
        quantity (PositiveSmallIntegerField): The quantity of the product ordered.
    """
    order = models.ForeignKey(Order, on_delete=models.PROTECT, verbose_name=_("Order"), related_name='orders')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name=_("Product"), related_name='orderitems')
    unit_price = models.DecimalField(_("Unit Price"), max_digits=15, decimal_places=2,
                                     validators=[MinValueValidator(1)])
    quantity = models.PositiveSmallIntegerField(_("Quantity"))

    class Meta:
        verbose_name = _("Order Item")
        verbose_name_plural = _("Order Items")

    def __str__(self):
        return f"{self.order} - {self.product}"


class Review(BaseModel):
    """
    Model representing a review.

    Attributes:
        customer (ForeignKey): The customer who left the review.
        product (ForeignKey): The product being reviewed.
        rating (PositiveIntegerField): The rating given by the customer.
        title (CharField): The title of the review.
        description (TextField): The description of the review.
        parent_review (ForeignKey, optional): The parent review if this is a reply.
        active (BooleanField): Indicates whether the review is active.
    """
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name=_("Customer"))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name='Product')
    rating = models.PositiveIntegerField(_('Rating'), validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(_('Title'), max_length=255)
    description = models.TextField()
    parent_review = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies',
                                      verbose_name='Reply to')
    active = models.BooleanField(_("Active"), default=False)

    def __str__(self):
        return f"{self.customer} - {self.title}"

    class Meta:
        verbose_name = _("Review")
        verbose_name_plural = _("Reviews")


class Transaction(BaseModel):
    """
    Model representing a transaction.

    Attributes:
        order (OneToOneField): The order associated with the transaction.
        payment_status (CharField): The payment status of the transaction.
        total_price (DecimalField): The total price of the transaction.
        customer (ForeignKey): The customer associated with the transaction.
        receipt_number (CharField, optional): The receipt number of the transaction.
        phone_number (CharField): The phone number associated with the transaction.
        Authority (CharField, optional): The authority of the transaction.
    """
    class PaymentStatus(models.TextChoices):
        PAYMENT_STATUS_PENDING = 'P', _('Pending')
        PAYMENT_STATUS_COMPLETE = 'C', _('Complete')
        PAYMENT_STATUS_FAILED = 'F', _('Failed')

    order = models.OneToOneField(Order, on_delete=models.CASCADE, verbose_name=_("Order"), related_name='transaction')
    payment_status = models.CharField(_("Payment Status"), max_length=1, choices=PaymentStatus,
                                      default=PaymentStatus.PAYMENT_STATUS_PENDING)
    total_price = models.DecimalField(_("Total Price"), max_digits=10, decimal_places=2)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, verbose_name=_("Customer"))
    receipt_number = models.CharField(_("Receipt Number"), max_length=255, null=True)
    phone_number = models.CharField(_('Phone Number'), max_length=13)
    Authority = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Transaction for Order #{self.order.pk} - {self.get_payment_status_display()}"

    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")


class SiteSettings(TranslatableModel, BaseModel, SingletonModel):
    translations = TranslatedFields(
        footer_text=models.TextField(_("Footer Text"), blank=True, null=True),
        address=models.TextField(_("Address"), blank=True, null=True)
    )
    phone_number = models.CharField(_("Phone Number"), max_length=20, blank=True, null=True)
    logo = models.ImageField(_("Logo"), upload_to='site_settings/logos/', blank=True, null=True)
    telegram_link = models.CharField(_("Telegram link"), blank=True, null=True, max_length=20)
    twitter_link = models.CharField(_("Twitter link"), blank=True, null=True, max_length=20)
    instagram_link = models.CharField(_("Instagram link"), blank=True, null=True, max_length=20)
    whatsapp_link = models.CharField(_("Whatsapp link"), blank=True, null=True, max_length=20)

    def __str__(self):
        return f"Site Settings"

    class Meta:
        verbose_name = _("Site Settings")
        verbose_name_plural = _("Site Settings")


class HomeBanner(BaseModel, SingletonModel):
    product = models.ManyToManyField(Product, verbose_name='Products')

    def __str__(self):
        return f"Home Banner"

    class Meta:
        verbose_name = _("Home Banner")
        verbose_name_plural = _("Home Banners")


# class WishList(BaseModel):
#     product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name=_("Product"))
#     customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name=_("Customer"))
#
#     class Meta:
#         verbose_name = 'WishList'
#         verbose_name_plural = 'WishList'
#
#     def __str__(self):
#         return f'{self.customer.first_name} {self.customer.last_name}'

class FeatureKey(TranslatableModel):
    """
    Model representing a feature key.

    Attributes:
        key (CharField): The key of the feature.
    """
    translations = TranslatedFields(
        key=models.CharField(_('Key'), max_length=50, )
    )

    class Meta:
        verbose_name = _("Feature Key")
        verbose_name_plural = _("Feature Keys")

    def __repr__(self) -> str:
        return f"{self.key}"

    def __str__(self) -> str:
        return f"{self.key}"


class FeatureValue(TranslatableModel):
    """
    Model representing a feature value.

    Attributes:
        key (ForeignKey): The feature key.
        value (CharField): The value of the feature.
    """
    key = models.ForeignKey(FeatureKey, on_delete=models.CASCADE, verbose_name=_('Key'), related_name='values')
    translations = TranslatedFields(
        value=models.CharField(_('Value'), max_length=50, )
    )

    class Meta:
        verbose_name = _("Feature Value")
        verbose_name_plural = _("Feature Value")

    def __repr__(self) -> str:
        return f"{self.value}"

    def __str__(self) -> str:
        return f"{self.value}"


class MainFeature(BaseModel):
    """
    Model representing a main feature for products.

    Attributes:
        product (ForeignKey): The product associated with the main feature.
        key (ForeignKey): The feature key.
        value (ForeignKey): The feature value.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name=_('Product'))
    key = models.ForeignKey(FeatureKey, on_delete=models.DO_NOTHING, verbose_name=_('Key'))
    value = models.ForeignKey(FeatureValue, on_delete=models.DO_NOTHING, verbose_name=_('Value'))

    class Meta:
        verbose_name = _("Main Feature")
        verbose_name_plural = _("Main Features")

    def __repr__(self) -> str:
        return f"{self.product.title}: {self.key} -> {self.value}"

    def __str__(self) -> str:
        return f"{self.product.title}: {self.key.key} -> {self.value.value}"
