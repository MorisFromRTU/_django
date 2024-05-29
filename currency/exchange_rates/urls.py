from django.contrib import admin
from django.urls import path
from exchange_rates import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.GetCurrencies.as_view(), name='get_currencies'),
    path('get_curreny_data', views.GetCurrenciesData.as_view(), name='get_currency_data')
]
