import requests
import json
import os
import pandas as pd
import io

from time import sleep
from datetime import datetime, timedelta
import pytz

def refresh_token_ads_vk(refresh_token, client_secret, client_id):
    """
    Refreshes access token
    """
    url = "https://ads.vk.com/api/v2/oauth2/token.json"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_secret": client_secret,
        "client_id": client_id
    }

    response = requests.post(url, headers=headers, data=data)
    token = response.json()['access_token']
    return token


def get_balance_vk_accs(access_token, client_ids):
    """
    Returns balance VK accounts
    client_ids - string with client ids with comma separated
    """
    url = "https://ads.vk.com/api/v2/agency/clients.json"
    headers = {
         "Authorization": f"Bearer {access_token}"
    }

    params = {
        "_user__id__in": client_ids
    }

    response = requests.get(url, headers=headers, params=params)
    json_data = response.json()

    balance_list = []
    for item in json_data['items']:
        client_info_dict = {
            'client_name': item['user']['additional_info']['client_name'],
            'balance': item['user']['account']['balance'],
            'id': item['user']['id']
        }
        balance_list.append(client_info_dict)

    return balance_list



def get_spent_vk_client(accaunt_ids, access_token, date_from, date_to):
    """
    Returns stat VK campaigns
    accaunt_ids - string with campaigns ids with comma separated
    """

    url = "https://ads.vk.com/api/v2/statistics/users/day.json"
    headers = {
         "Authorization": f"Bearer {access_token}"
    }
    params = {
        "id": accaunt_ids,
        "date_from": date_from,
        "date_to": date_to,
        "metrics": "base"
    }

    response = requests.get(url, headers=headers, params=params)
    return response.json()


def old_vk_get_stat_campaigns(access_token, 
                        account_id, 
                        campaign_ids, 
                        date_from, 
                        date_to):
    """
    Returns stat of campaigns from old VK account
    campaign_ids - string with campaigns ids with comma separated
    """
    url_ads = 'https://api.vk.com/method/ads.getStatistics'
    params = {
    'account_id': account_id,
    'ids_type': 'campaign',
    'ids': campaign_ids,
    'period': 'day',
    'date_from': date_from,
    'date_to': date_to,
    'v': '5.199'
}
    headers = {
    "Authorization": f"Bearer {access_token}"
}
    response = requests.get(url_ads, headers=headers, params=params)
    return response.json()



# Telegram bot
class TelegramBot:
    def __init__(self, token, chat_id):
        """
        Initializes a new instance of the telegram bot with the provided 
        token and chat ID.

        Parameters:
            token (str): The token for the Telegram bot.
            chat_id (int): The ID of the chat.
        """
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}/"
        self.chat_id = chat_id

    def send_message(self, text):
        url = self.base_url + "sendMessage"
        params = {"chat_id": self.chat_id, "text": text}
        response = requests.post(url, params=params)
        return response.json()
    

# Yandex Messenger bot 
class YandexMessengerBot:
    def __init__(self, token, chat_id):
        """
        Initializes a new instance of the Yandex bot with the provided 
        token and chat ID.

        Parameters:
            token (str): The token for the Yandex bot.
            chat_id (int): The ID of the chat.
        """
        self.token = token
        self.base_url = "https://botapi.messenger.yandex.net/bot/v1/messages/"
        self.chat_id = chat_id

    def send_text(self, text):
        self.headers = {"Authorization": f"OAuth {self.token}",
                        'Content-Type': 'application/json'}
        url = self.base_url + "sendText/"
        if '/' in self.chat_id:
            data = {"chat_id": self.chat_id,
                    "text": text}
        else:
            data = {"login": self.chat_id,
                    "text": text}
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()
    
    def send_file(self, file_data, filename="data.csv"):
        """
        Sends a file to the Yandex Messenger chat.
        file_data: байтовый объект (или открытый файл)
        filename: имя файла, которое увидит пользователь
        """
        headers = {"Authorization": f"OAuth {self.token}"}
        url = self.base_url + "sendFile/"

        data = {}
        if '/' in str(self.chat_id):
            data["chat_id"] = self.chat_id
        else:
            data["login"] = self.chat_id
        
        # Подготовка файла для отправки
        # Формат: 'ключ_формы': ('имя_файла', байтовый_объект, 'mime/type')
        files = {
            "document": (filename, file_data, "text/csv")
        }

        response = requests.post(url, headers=headers, data=data, files=files)
        return response.json()
    
    def getupdate(self, offset=0):
        self.headers = {"Authorization": f"OAuth {self.token}"}
        url = self.base_url + "getUpdates/"
        params = {"offset": offset}
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
    


## Yandex Direct
class YandexDirect:
    def __init__(self, token):
        """
         Initializes a new instance of the yandex direct exporter 
         with the provided token.

        Parameters: token (str) - The token for Yandex Direct API.
        """
        self.token = token
        self.url_accounts = 'https://api.direct.yandex.ru/live/v4/json/'
        self.url_reports = 'https://api.direct.yandex.com/json/v5/reports'
        self.url_campaigns = 'https://api.direct.yandex.com/json/v5/campaigns'
        self.url_clients = 'https://api.direct.yandex.com/json/v5/clients'

    def get_single_account_balance(self, token, login):
        """
        Returns balance for a single account using individual token
        
        Parameters:
            token (str): Individual account token
            login (str): Account login
            
        Returns:
            dict: {'login': str, 'amount': float, 'currency': str} or None if error
        """
        body = {
            "method": "AccountManagement",
            "token": token,
            "locale": "ru",
            "param": {
                "Action": "Get",
                "SelectionCriteria": {
                }
            }
        }
        
        try:
            response = requests.post(self.url_accounts, json=body)
            response.encoding = 'utf-8'
            
            # Отладочный вывод
            print(f"Статус ответа для {login}: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Отладка: смотрим структуру ответа
                print(f"Структура ответа для {login}:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # Проверяем разные варианты структуры ответа
                if 'data' in data and 'Accounts' in data['data']:
                    account = data['data']['Accounts'][0]
                    return {
                        'login': account['Login'],
                        'amount': round(float(account['Amount']), 2),
                        'currency': account.get('Currency', 'RUB')
                    }
                elif 'Accounts' in data:
                    account = data['Accounts'][0]
                    return {
                        'login': account['Login'],
                        'amount': round(float(account['Amount']), 2),
                        'currency': account.get('Currency', 'RUB')
                    }
                else:
                    print(f"Неожиданная структура ответа для {login}")
                    print(f"Ключи в ответе: {data.keys()}")
                    return None
            elif response.status_code == 400:
                print(f"Параметры запроса для {login} указаны неверно")
                print(response.text)
                return None
            else:
                print(f"Ошибка для {login}: статус {response.status_code}")
                print(response.text)
                return None
                
        except ConnectionError:
            print(f"Ошибка соединения при запросе баланса для {login}")
            return None
        except Exception as e:
            print(f"Непредвиденная ошибка для {login}: {e}")
            print(f"Полный ответ сервера:")
            try:
                print(response.text)
            except:
                pass
            return None
        
    def get_multiple_accounts_balances(self, accounts_dict):
        """
        Returns balances for multiple accounts with individual tokens
        
        Parameters:
            accounts_dict (dict): Dictionary with {login: token} pairs
            
        Returns:
            list: List of dicts with balance info
        """
        balances = []
        
        for login, token in accounts_dict.items():
            print(f"Запрашиваю баланс для {login}...")
            balance = self.get_single_account_balance(token, login)
            
            if balance:
                balances.append(balance)
            
            # Небольшая пауза между запросами
            sleep(0.5)
        
        return balances
    
    def accounts_budget(self, logins):
        """
        Returns accounts budget (original agency method)
        """
        token = self.token
        AgencyClientsBody = {
            "method": "AccountManagement",
            "token": token,
            "param": {
                "Action": "Get",
                "SelectionCriteria": {
                "Logins": logins  
                }
            }
        }
        response = requests.post(self.url_accounts, json=AgencyClientsBody)
    
        if response.status_code == 200:
            print("Request was successful")
            json_data = response.json()
            accounts_budget = [{'Login': account['Login'], 
              'Amount': round(float(account['Amount']), 2)} for account in json_data['data']['Accounts']]
            return accounts_budget
        else:
            print("Request failed with status code:", response.status_code)
            print(response.text)

    def get_single_account_spent(self, token, login, date_range="LAST_3_DAYS"):
        """
        Returns spent amount for a single account using individual token
        
        Parameters:
            token (str): Individual account token
            login (str): Account login
            date_range (str): Date range for the report (default: "LAST_3_DAYS")
            
        Returns:
            dict: {'login': str, 'cost': float} or None if error
        """
        main_url = self.url_reports
        headers = {
            "Authorization": "Bearer " + token,
            "Accept-Language": "ru",
            'skipReportHeader': "true",
            'skipColumnHeader': "true",
            'skipReportSummary': "true",
            'returnMoneyInMicros': "false",
            'Client-Login': login
        }
        body = {
            "params": {
                "SelectionCriteria": {},
                "FieldNames": ["Cost"],
                "ReportName": "ACCOUNT_PERFORMANCE",
                "ReportType": "ACCOUNT_PERFORMANCE_REPORT",
                "DateRangeType": date_range,
                "Format": "TSV",
                "IncludeVAT": "YES",
                "IncludeDiscount": "NO"
            }
        }
        
        requestBody = json.dumps(body, indent=4)
        
        # Цикл для выполнения запросов с обработкой статусов 201/202
        while True:
            try:
                req = requests.post(main_url, requestBody, headers=headers)
                req.encoding = 'utf-8'
                
                if req.status_code == 400:
                    print(f"Параметры запроса для {login} указаны неверно или достигнут лимит отчетов в очереди")
                    print(f"RequestId: {req.headers.get('RequestId', False)}")
                    print(f"JSON-код запроса: {body}")
                    print(f"JSON-код ответа сервера: \n{req.json()}")
                    return None
                    
                elif req.status_code == 200:
                    print(f"Отчет для аккаунта {login} создан успешно")
                    print(f"RequestId: {req.headers.get('RequestId', False)}")
                    
                    if req.text != "":
                        tempresult = req.text.split('\t')
                        return {
                            'login': login,
                            'cost': float(tempresult[0])
                        }
                    else:
                        return {
                            'login': login,
                            'cost': 0.0
                        }
                        
                elif req.status_code == 201:
                    print(f"Отчет для аккаунта {login} успешно поставлен в очередь в режиме offline")
                    retryIn = int(req.headers.get("retryIn", 60))
                    print(f"Повторная отправка запроса через {retryIn} секунд")
                    print(f"RequestId: {req.headers.get('RequestId', False)}")
                    sleep(retryIn)
                    
                elif req.status_code == 202:
                    print(f"Отчет для аккаунта {login} формируется в режиме офлайн")
                    retryIn = int(req.headers.get("retryIn", 60))
                    print(f"Повторная отправка запроса через {retryIn} секунд")
                    print(f"RequestId: {req.headers.get('RequestId', False)}")
                    sleep(retryIn)
                    
                elif req.status_code == 500:
                    print(f"При формировании отчета для {login} произошла ошибка. Попробуйте повторить запрос позднее.")
                    print(f"RequestId: {req.headers.get('RequestId', False)}")
                    print(f"JSON-код ответа сервера: \n{req.json()}")
                    return None
                    
                elif req.status_code == 502:
                    print(f"Время формирования отчета для {login} превысило серверное ограничение.")
                    print("Попробуйте изменить параметры запроса - уменьшить период и количество запрашиваемых данных.")
                    print(f"JSON-код запроса: {body}")
                    print(f"RequestId: {req.headers.get('RequestId', False)}")
                    print(f"JSON-код ответа сервера: \n{req.json()}")
                    return None
                    
                else:
                    print(f"Произошла непредвиденная ошибка для {login}")
                    print(f"RequestId: {req.headers.get('RequestId', False)}")
                    print(f"JSON-код запроса: {body}")
                    print(f"JSON-код ответа сервера: \n{req.json()}")
                    return None

            except ConnectionError:
                print(f"Произошла ошибка соединения с сервером API для {login}")
                return None
                
            except Exception as e:
                print(f"Произошла непредвиденная ошибка для {login}: {e}")
                return None


    def get_multiple_accounts_spent(self, accounts_dict, date_range="LAST_3_DAYS"):
        """
        Returns spent amounts for multiple accounts with individual tokens
        
        Parameters:
            accounts_dict (dict): Dictionary with {login: token} pairs
            date_range (str): Date range for the report (default: "LAST_3_DAYS")
            
        Returns:
            list: List of dicts with spent info or CSV string
        """
        results = []
        
        for login, token in accounts_dict.items():
            print(f"Запрашиваю траты для {login}...")
            spent = self.get_single_account_spent(token, login, date_range)
            
            if spent:
                results.append(spent)
            
            # Небольшая пауза между запросами
            sleep(0.5)
        
        return results
        
        # Если нужен CSV формат:
        # resultcsv = "Login,Costs\n"
        # for result in results:
        #     resultcsv += f"{result['login']},{result['cost']}\n"
        # return resultcsv

    def _request_report_tsv(self, token, login, body):
        """
        Executes a Yandex Direct report request and returns TSV text (or empty string).
        """
        main_url = self.url_reports
        headers = {
            "Authorization": "Bearer " + token,
            "Accept-Language": "ru",
            'skipReportHeader': "true",
            'skipColumnHeader': "true",
            'skipReportSummary': "true",
            'returnMoneyInMicros': "false",
            'Client-Login': login
        }

        requestBody = json.dumps(body, indent=4)

        while True:
            try:
                req = requests.post(main_url, requestBody, headers=headers)
                req.encoding = 'utf-8'

                if req.status_code == 400:
                    print(f"Параметры запроса для {login} указаны неверно или достигнут лимит отчетов в очереди")
                    print(f"RequestId: {req.headers.get('RequestId', False)}")
                    print(f"JSON-код запроса: {body}")
                    print(f"JSON-код ответа сервера: \n{req.json()}")
                    return ""

                elif req.status_code == 200:
                    print(f"Отчет для аккаунта {login} создан успешно")
                    print(f"RequestId: {req.headers.get('RequestId', False)}")
                    return req.text or ""

                elif req.status_code == 201:
                    print(f"Отчет для аккаунта {login} успешно поставлен в очередь в режиме offline")
                    retryIn = int(req.headers.get("retryIn", 60))
                    print(f"Повторная отправка запроса через {retryIn} секунд")
                    print(f"RequestId: {req.headers.get('RequestId', False)}")
                    sleep(retryIn)

                elif req.status_code == 202:
                    print(f"Отчет для аккаунта {login} формируется в режиме офлайн")
                    retryIn = int(req.headers.get("retryIn", 60))
                    print(f"Повторная отправка запроса через {retryIn} секунд")
                    print(f"RequestId: {req.headers.get('RequestId', False)}")
                    sleep(retryIn)

                elif req.status_code == 500:
                    print(f"При формировании отчета для {login} произошла ошибка. Попробуйте повторить запрос позднее.")
                    print(f"RequestId: {req.headers.get('RequestId', False)}")
                    print(f"JSON-код ответа сервера: \n{req.json()}")
                    return ""

                elif req.status_code == 502:
                    print(f"Время формирования отчета для {login} превысило серверное ограничение.")
                    print("Попробуйте изменить параметры запроса - уменьшить период и количество запрашиваемых данных.")
                    print(f"JSON-код запроса: {body}")
                    print(f"RequestId: {req.headers.get('RequestId', False)}")
                    print(f"JSON-код ответа сервера: \n{req.json()}")
                    return ""

                else:
                    print(f"Произошла непредвиденная ошибка для {login}")
                    print(f"RequestId: {req.headers.get('RequestId', False)}")
                    print(f"JSON-код запроса: {body}")
                    print(f"JSON-код ответа сервера: \n{req.json()}")
                    return ""

            except ConnectionError:
                print(f"Произошла ошибка соединения с сервером API для {login}")
                return ""

            except Exception as e:
                print(f"Произошла непредвиденная ошибка для {login}: {e}")
                return ""

    def _sum_cost_from_tsv(self, tsv_text):
        """
        Sums the Cost column from a TSV report body.
        """
        if not tsv_text:
            return 0.0

        total = 0.0
        for line in tsv_text.strip().splitlines():
            if not line:
                continue
            parts = line.split('\t')
            if not parts:
                continue
            value = parts[0].strip()
            if value in ("", "-"):
                continue
            try:
                total += float(value)
            except ValueError:
                continue
        return total

    def get_single_account_spent_filtered(self, token, login, date_range="LAST_3_DAYS",
                                          ad_network_type=None, location_ids=None):
        """
        Returns spent amount for a single account with optional filters:
        - ad_network_type: "SEARCH" or "AD_NETWORK"
        - location_ids: list of LocationOfPresenceId
        """
        filters = []
        if ad_network_type:
            filters.append({
                "Field": "AdNetworkType",
                "Operator": "EQUALS",
                "Values": [ad_network_type]
            })
        if location_ids:
            filters.append({
                "Field": "LocationOfPresenceId",
                "Operator": "EQUALS",
                "Values": [str(x) for x in location_ids]
            })

        body = {
            "params": {
                "SelectionCriteria": {},
                "FieldNames": ["Cost"],
                "ReportName": "FILTERED_SPEND",
                "ReportType": "CUSTOM_REPORT",
                "DateRangeType": date_range,
                "Format": "TSV",
                "IncludeVAT": "YES",
                "IncludeDiscount": "NO"
            }
        }
        if filters:
            body["params"]["Filter"] = filters

        tsv_text = self._request_report_tsv(token, login, body)
        return {
            'login': login,
            'cost': self._sum_cost_from_tsv(tsv_text)
        }

    def get_multiple_accounts_spent_filtered(self, accounts_dict, date_range="LAST_3_DAYS",
                                             ad_network_type=None, location_ids=None):
        """
        Returns spent amounts for multiple accounts with optional filters.
        """
        results = []

        for login, token in accounts_dict.items():
            print(f"Запрашиваю траты (filtered) для {login}...")
            spent = self.get_single_account_spent_filtered(
                token=token,
                login=login,
                date_range=date_range,
                ad_network_type=ad_network_type,
                location_ids=location_ids
            )

            if spent:
                results.append(spent)

            sleep(0.5)

        return results

    def get_accounts_reconcile_with_commission(self, accounts_dict, date_range="LAST_MONTH",
                                               outside_rf_location_ids=None,
                                               commission_rate=0.03, commission_base=0.97):
        """
        Returns reconciliation data per account:
        - total_spend: all spend with VAT
        - search_spend: spend in search (AdNetworkType=SEARCH)
        - rsy_outside_rf_spend: spend in RSYA outside РФ (AdNetworkType=AD_NETWORK + location filter)
        - excluded_sum: search_spend + rsy_outside_rf_spend
        - commission_base_sum: total_spend - excluded_sum
        - commission_sum: commission_base_sum * (1 + commission_rate/commission_base)
        """
        if outside_rf_location_ids is None:
            outside_rf_location_ids = [166, 111, 183, 241, 10002, 10003, 138]

        results = []
        multiplier = 1 + (commission_rate / commission_base)

        for login, token in accounts_dict.items():
            print(f"Сверка с комиссией для {login}...")

            total_spend = self.get_single_account_spent(
                token=token,
                login=login,
                date_range=date_range
            )
            total_cost = total_spend['cost'] if total_spend else 0.0

            search_spend = self.get_single_account_spent_filtered(
                token=token,
                login=login,
                date_range=date_range,
                ad_network_type="SEARCH"
            )
            search_cost = search_spend['cost'] if search_spend else 0.0

            rsy_outside_spend = self.get_single_account_spent_filtered(
                token=token,
                login=login,
                date_range=date_range,
                ad_network_type="AD_NETWORK",
                location_ids=outside_rf_location_ids
            )
            rsy_outside_cost = rsy_outside_spend['cost'] if rsy_outside_spend else 0.0

            excluded_sum = search_cost + rsy_outside_cost
            commission_base_sum = total_cost - excluded_sum
            commission_sum = commission_base_sum * multiplier

            results.append({
                "login": login,
                "total_spend": total_cost,
                "search_spend": search_cost,
                "rsy_outside_rf_spend": rsy_outside_cost,
                "excluded_sum": excluded_sum,
                "commission_base_sum": commission_base_sum,
                "commission_sum": commission_sum
            })

            sleep(0.5)

        return results



    def get_account_spent(self, logins, date_range="LAST_3_DAYS"):
        """
        Returns accounts spent
        """
        main_url = self.url_reports
        token = self.token
        headers = {
            "Authorization": "Bearer " + token,
            "Accept-Language": "ru",
            'skipReportHeader': "true",
            'skipColumnHeader': "true",
            'skipReportSummary': "true",
            'returnMoneyInMicros': "false"
        }
        body = {
            "params": {
                "SelectionCriteria": {},
                "FieldNames": ["Cost"],
                "ReportName": "ACCOUNT_PERFORMANCE",
                "ReportType": "ACCOUNT_PERFORMANCE_REPORT",
                "DateRangeType": date_range,
                "Format": "TSV",
                "IncludeVAT": "YES",
                "IncludeDiscount": "NO"
            }
        }
        resultcsv = "Login,Costs\n"
        for Client in logins:
            # Добавление HTTP-заголовка "Client-Login"
            headers['Client-Login'] = Client
            # Кодирование тела запроса в JSON
            requestBody = json.dumps(body, indent=4)
            # Запуск цикла для выполнения запросов
            # Если получен HTTP-код 200, то содержание отчета добавляется к результирующим данным
            # Если получен HTTP-код 201 или 202, выполняются повторные запросы
            while True:
                try:
                    req = requests.post(main_url, requestBody, headers=headers)
                    req.encoding = 'utf-8'  # Принудительная обработка ответа в кодировке UTF-8
                    if req.status_code == 400:
                        print("Параметры запроса указаны неверно или достугнут лимит отчетов в очереди")
                        print(f"RequestId: {req.headers.get('RequestId', False)}")
                        print(f"JSON-код запроса: {body}")
                        print(f"JSON-код ответа сервера: \n{req.json()}")
                        break
                    elif req.status_code == 200:
                        print(f"Отчет для аккаунта {str(Client)} создан успешно")
                        print(f"RequestId: {req.headers.get('RequestId', False)}")
                        if req.text != "":
                            tempresult = req.text.split('\t')
                            resultcsv += "{},{}\n".format(Client, tempresult[0])
                        else:
                            resultcsv += "{},0\n".format(Client)
                        break
                    elif req.status_code == 201:
                        print(f"Отчет для аккаунта {str(Client)} успешно поставлен в очередь в режиме offline")
                        retryIn = int(req.headers.get("retryIn", 60))
                        print(f"Повторная отправка запроса через {retryIn} секунд")
                        print(f"RequestId: {req.headers.get('RequestId', False)}")
                        sleep(retryIn)
                    elif req.status_code == 202:
                        print("Отчет формируется в режиме офлайн")
                        retryIn = int(req.headers.get("retryIn", 60))
                        print(f"Повторная отправка запроса через {retryIn} секунд")
                        print(f"RequestId: {req.headers.get('RequestId', False)}")
                        sleep(retryIn)
                    elif req.status_code == 500:
                        print("При формировании отчета произошла ошибка. Пожалуйста, попробуйте повторить запрос позднее.")
                        print(f"RequestId: {req.headers.get('RequestId', False)}")
                        print(f"JSON-код ответа сервера: \n{req.json()}")
                        break
                    elif req.status_code == 502:
                        print("Время формирования отчета превысило серверное ограничение.")
                        print(
                            "Пожалуйста, попробуйте изменить параметры запроса - уменьшить период и количество запрашиваемых данных.")
                        print(f"JSON-код запроса: {body}")
                        print(f"RequestId: {req.headers.get('RequestId', False)}")
                        print(f"JSON-код ответа сервера: \n{req.json()}")
                        break
                    else:
                        print("Произошла непредвиденная ошибка")
                        print(f"RequestId: {req.headers.get('RequestId', False)}")
                        print(f"JSON-код запроса: {body}")
                        print(f"JSON-код ответа сервера: \n{req.json()}")
                        break

                # Обработка ошибки, если не удалось соединиться с сервером API Директа
                except ConnectionError:
                    # В данном случае мы рекомендуем повторить запрос позднее
                    print("Произошла ошибка соединения с сервером API")
                    # Принудительный выход из цикла
                    break

                # Если возникла какая-либо другая ошибка
                except:
                    # В данном случае мы рекомендуем проанилизировать действия приложения
                    print("Произошла непредвиденная ошибка")
                    # Принудительный выход из цикла
                    break
        return resultcsv
    
    def get_working_campaigns(self, login):
        """
        Returns list of names and ids of working campaigns
        """
        token = self.token
        headers = {
            "Authorization": "Bearer " + token,
            "Client-Login": login
        }
        json_data = {
            "method": "get",
            "params": {
                "SelectionCriteria": {
                    "States": ["ON"]
                },
                "FieldNames": ["Id", "Name"]
            }
        }
        response = requests.post(self.url_campaigns, headers=headers, json=json_data)

        if response.status_code == 200:
            print("Request was successful")
            json_data = response.json()
            return json_data
        else:
            print("Request failed with status code:", response.status_code)

    def suspend_campaigns(self, login, campaign_ids):
        """
        Suspend campaigns in Yandex Direct
        """
        token = self.token
        headers = {
            "Authorization": "Bearer " + token,
            "Client-Login": login
        }
        json_data = {
            "method": "suspend",
            "params": {
                "SelectionCriteria": {
                    "Ids": campaign_ids
                }
            }
        }
        response = requests.post(self.url_campaigns, headers=headers, json=json_data)

        if response.status_code == 200:
            print("Request was successful")
            json_data = response.json()
            timezone = pytz.timezone('Europe/Moscow')
            current_time = datetime.now(timezone)
            filepath = f"{login}.json"
            json_to_save = {
                "date" : current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "campaign_ids": campaign_ids                 
            }
            if os.path.exists(filepath):
                print(f"Файл {filepath} уже существует. Данные будут заменены.")
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(json_to_save, f, indent=4, ensure_ascii=False)
            else:
                print(f"Файл {filepath} не существует. Создание нового.")
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(json_to_save, f, indent=4, ensure_ascii=False)
            return json_data
    def get_campaign_names(self, login, ids):
        """
        Get names of campaigns
        """
        token = self.token
        headers = {
            "Authorization": "Bearer " + token,
            "Client-Login": login
        }
        json_data = {
            "method": "get",
            "params": {
                "SelectionCriteria": {
                    "Ids": ids
                },
                "FieldNames": ["Id", "Name"]
            }
        }
        response = requests.post(self.url_campaigns, headers=headers, json=json_data)

        if response.status_code == 200:
            print("Request was successful")
            json_data = response.json()
            campaign_names = [campaign['Name'] for campaign in json_data['result']['Campaigns']]
            return campaign_names

    def recover_campaigns(self, login):
        """
        Turn suspended campaigns back
        """
        token = self.token
        headers = {
            "Authorization": "Bearer " + token,
            "Client-Login": login
        }
        with open(f"{login}.json", 'r', encoding='utf-8') as f:
            json_data_tmp = json.load(f)
            campaign_ids = json_data_tmp['campaign_ids']
        json_data = {
            "method": "resume",
            "params": {
                "SelectionCriteria": {
                    "Ids": campaign_ids
                }
            }
        }
        response = requests.post(self.url_campaigns, headers=headers, json=json_data)

        if response.status_code == 200:
            print("Request was successful")
            json_data = response.json()
            return json_data
