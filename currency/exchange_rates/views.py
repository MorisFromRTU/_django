from django.views.generic import View
from django.http import HttpResponse, JsonResponse
from .models import *
from bs4 import BeautifulSoup
import json
import requests
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from django.db import connection
from django.shortcuts import get_object_or_404
from decimal import Decimal
from django.shortcuts import render

def index(request):
    return render(request, 'exchange_rates/index.html')


class GetCurrencies(View):
    def get(self, request):
        url = 'https://www.finmarket.ru/currency/rates/'
        response = requests.get(url)

        if response.status_code == 200:
            currencies = dict(Currency.objects.values_list('code', 'name'))
            text = response.content.decode('windows-1251')
            soup = BeautifulSoup(text, 'html.parser')
            rows = soup.find('tbody').find_all('tr')
            for row in rows:
                name = row.find_all('td')[1].text
                code = row.find_all('td')[0].text
                if code and code not in currencies:
                    currencies[code] = name
                    Currency.objects.create(code=code, name=name)
        context = {
            'currencies': currencies,
        }


        return render(request, 'exchange_rates/index.html', context)

@method_decorator(csrf_exempt, name='dispatch')
class GetCurrenciesCodes(View):
    def post(self, request):
        body = request.body.decode('utf-8')
        data = json.loads(body)

        start_date = data.get('startDate')
        end_date = data.get('endDate')
        selected_currency = data.get('selectedCurrency')

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
                    
                    exists = ExchangeRate.objects.filter(currency=CurrencyRate.objects.get(code=selected_currency),
                                                        date=date).exists()
                    if not exists:
                        ExchangeRate.objects.create(
                            currency=CurrencyRate.objects.get(code=selected_currency),
                            date=datetime.strptime(temp[0], "%d.%m.%Y"),
                            amount=temp[1],
                            rate=Decimal(temp[2].replace(',', '')),
                        )
                    else:
                        existing_rate = get_object_or_404(ExchangeRate, currency=CurrencyRate.objects.get(code=selected_currency), date=date)
                        if temp[2] != existing_rate.rate:
                            existing_rate.rate = Decimal(temp[2].replace(',', ''))
                            existing_rate.save()
                    result.append(temp)
            
        return JsonResponse(result, safe=False)

    def get(self, request):
        currencies = CurrencyRate.objects.all()
        options_dict = {currency.code: currency.name for currency in currencies}

        url = 'https://www.finmarket.ru/currency/rates/?id=10148&pv=1&cur=52170&bd=1&bm=2&by=2022&ed=1&'
        response = requests.get(url)
        
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
            return JsonResponse({"data": options_dict})
        else:
            print("Failed to fetch currency rates")
            return JsonResponse({"error": "Failed to fetch currency rates"}, status=500)

    def save_to_database(self, data):
        for code, name in data.items():
            currency, created = CurrencyRate.objects.get_or_create(code=code)
            if created:
                currency.name = name
                currency.save()

    def clear_table(self, table_name):
        with connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM {table_name}")
