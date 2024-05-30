from django.contrib import admin
from django.urls import path,include
from exchange_rates.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('exchange_rates.urls')),
]
