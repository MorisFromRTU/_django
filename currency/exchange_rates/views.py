from django.views.generic import View
from django.http import  JsonResponse
from .models import *
from bs4 import BeautifulSoup
import json
import requests
from datetime import datetime
from django.db import connection
from django.shortcuts import get_object_or_404
from decimal import Decimal
from django.shortcuts import render


class GetCurrencies(View):

    def save_to_database(self, data):
        for code, name in data.items():
            currency, created = Currency.objects.get_or_create(code=code)
            if created:
                currency.name = name
                currency.save()

    def get(self, request):
        url = 'https://www.finmarket.ru/currency/rates/?id=10148&pv=1&cur=52170&bd=1&bm=2&by=2022&ed=1&'
        response = requests.get(url)
        
        currencies = Currency.objects.all()
        options_dict = {currency.code: currency.name for currency in currencies}

        if response.status_code == 200:
            text = response.content.decode('windows-1251')
            soup = BeautifulSoup(text, 'html.parser')
            rows = soup.find('table', class_='fs11').find('tr').find('td').find('select', class_='fs11')
            options = rows.find_all('option')

            for option in options:
                value = option['value']
                if value and value not in options_dict:
                    text = option.text.strip()
                    options_dict[value] = text
            self.save_to_database(options_dict)

        context = {'currencies': currencies}
        return render(request, 'exchange_rates/index.html', context)

class GetCurrenciesData(View):

    def post(self, request):
        start_date = request.POST.get('startDate')
        end_date = request.POST.get('endDate')
        selected_currency = request.POST.get('selectedCurrency')

        start_object = datetime.strptime(start_date, "%Y-%m-%d")
        end_object = datetime.strptime(end_date, "%Y-%m-%d")

        start_year = start_object.year
        start_month = start_object.month
        start_day = start_object.day 

        end_year = end_object.year
        end_month = end_object.month
        end_day = end_object.day 

        url = f'https://www.finmarket.ru/currency/rates/?id=10148&pv=1&cur={selected_currency}&bd={start_day}&bm={start_month}&by={start_year}&ed={end_day}&em={end_month}&ey={end_year}&x=15&y=11#archive'
        response = requests.get(url)

        result = []
        if response.status_code == 200:
            text = response.content.decode('windows-1251')
            soup = BeautifulSoup(text, 'html.parser')
            rows = soup.find('table', class_='karramba').find_all('tr')
            for row in rows:
                elements = row.find_all('td')
                temp = []
                for element in elements:
                    temp.append(element.text)
                if temp:
                    date_str = temp[0]
                    date = datetime.strptime(date_str, "%d.%m.%Y")
                    
                    exists = ExchangeRate.objects.filter(currency=Currency.objects.get(code=selected_currency),
                                                        date=date).exists()
                    if not exists:
                        ExchangeRate.objects.create(
                            currency=Currency.objects.get(code=selected_currency),
                            date=datetime.strptime(temp[0], "%d.%m.%Y"),
                            amount=temp[1],
                            rate=Decimal(temp[2].replace(',', '')),
                        )
                    else:
                        existing_rate = get_object_or_404(ExchangeRate, currency=Currency.objects.get(code=selected_currency), date=date)
                        if temp[2] != existing_rate.rate:
                            existing_rate.rate = Decimal(temp[2].replace(',', ''))
                            existing_rate.save()
                    result.append(temp)

        context = {
            'resuls' : result
        }
        return render(request, 'exchange_rates/results.html', context)    
        
class SuccessView(View):
        def get(self, request):
            return render(request, 'success.html')