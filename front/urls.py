from django.urls import path, include
from . import views

app_name = 'front'
urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('verify-otp/', views.VerifyOtpView.as_view(), name='verify-otp'),
    path('set-password/', views.SetPasswordView.as_view(), name='set-password'),
    path('products/', views.ProductListView.as_view(), name='products'),
    path('products/<int:id>/', views.ProductDetailView.as_view(), name='products-detail'),
    path('cart/', views.CartView.as_view(), name='cart'),
    path('order-detail/<int:id>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('compare/', views.CompareView.as_view(), name='compare'),
    path('', views.HomeView.as_view(), name='home'),
    # path('', views.cached_template_home_view, name='home'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('api-v1/set_language/', views.set_language, name='set_language'),
    path('blogs/<int:id>/', views.cached_template_blog_detail_view, name='blog_detail'),
    path('blogs/', views.cached_template_blog_list_view, name='blogs'),
    path('chat/', views.ChatView.as_view(), name='chat'),
    path('chat/admin', views.ChatAdminView.as_view(), name='chat-admin'),

]
