from django.contrib import admin
from django.urls import path
from exchange_rates import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('get_currencies/', views.GetCurrencies.as_view(), name='get_currencies'),
    path('get_currency_codes/', views.GetCurrenciesCodes.as_view(), name='get_currency_codes'),
]
