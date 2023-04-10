"""simbank_pro URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path

from core.views import (
    AuthorizeAPIView,
    RegistrationAPIView,
    ResetPasswordAPIView,
    VerifyRegistrationAPIView,
    BankRequestAPIView,
    PaymentSuccess,
    PaymentFail,
)
from .routers import router

urlpatterns = [
    path('chat/', include("chat.urls")),
    path('admin/', admin.site.urls),
    path('api/', include((router.urls, 'core'))),
    re_path(r'^api/authorize/$', AuthorizeAPIView.as_view(), name='authorize'),
    re_path(r'^api/registration/$', RegistrationAPIView.as_view(), name='registration'),
    re_path(r'^api/top-up-balance/$', BankRequestAPIView.as_view(), name='top-up-balance'),
    re_path(r'^api/payment-failure/$', PaymentFail.as_view(), name='payment-failure'),
    re_path(r'^api/payment-success/$', PaymentSuccess.as_view(), name='payment-success'),
    re_path(r'^email-verify/$', VerifyRegistrationAPIView.as_view(), name='verify-email'),
    re_path(r'^reset-password/$', ResetPasswordAPIView.as_view(), name='reset-password')
]
