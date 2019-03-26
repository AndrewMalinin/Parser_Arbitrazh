# coding=utf-8
import requests
from bs4 import BeautifulSoup
import time
import smtplib
import zlib
import os

# Добавляем необходимые подклассы - MIME-типы
from email.mime.multipart import MIMEMultipart      # Многокомпонентный объект
from email.mime.text import MIMEText                # Текст/HTML
from email.mime.image import MIMEImage              # Изображения


# Имя файла куда записываем полученные от сервера дела
name_data = 'test'
name_data_file = name_data + '.html'


def send_to_email():
    addr_from = "python.assistantX@gmail.com"  # Адресат
    password = '1495#Android'
    addr_to = "artemsedov@sedovstudio.com"  # Получатель

    msg = MIMEMultipart()  # Создаем сообщение
    msg['From'] = addr_from  # Адресат
    msg['To'] = addr_to  # Получатель
    msg['Subject'] = 'Добрый вечер!'  # Тема сообщения

    prefix = 'Здравствуйте\n!'
    postfix = '\nДосвидания!'
    body = ''

    msg.attach(MIMEText((prefix + body + postfix), 'plain'))

    MailServer = smtplib.SMTP('smtp.gmail.com', 587)  # Подключаемся к почте
    MailServer.starttls()  # Включаем шифрование
    MailServer.login(addr_from, password)  # Передаём логин и пароль
    MailServer.send_message(msg)  # Отправка сообщения
    MailServer.quit()  # Выходим

    return

class Arbitrage:
    
    def __init__(self, inn):
        self.number_of_case = 0
        self.plaintiff = []
        self.respondent = []
        self.judge = []
        self.court = []
        self.url = 'http://kad.arbitr.ru/Kad/SearchInstances'
        self.inn = inn

    # Функция загрузки данных по заданному ИНН, отправляет POST запрос на url
    # Входные параметры: inn - нужный ИНН,
    # path - альтернативный путь сохранения html
    # Выходные параметры: время затраченное на выполнение функции в милисекундах
    def get_data_from_server(self, path=''):
        
        # headers -  Задаём имя браузера и системы с которой сидим
        headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; \
        Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)\
        Chrome/71.0.3578.80 Safari/537.36'}
        
        print("--Отправка POST запроса на %s " % self.url)
        tic = time.perf_counter()

        # Скачиваем первую страницу по нужному инн
        try:
            r = self.send_POST(headers, 1)
        except requests.exceptions.ConnectionError:
            toc = time.perf_counter()
            self.error_handler('Connection error')
            return round((toc - tic) * 1000, 1)

        # Полученные данные пишем в HTML-файл, если ответ 200
        if r.status_code == 200:
            with open(path + name_data_file, 'w') as output_file:
                output_file.write(r.text)
        else:
            toc = time.perf_counter()
            self.error_handler('Error write file')
            self.error_handler('Http '+str(r.status_code))
            return round((toc - tic) * 1000, 1)

        # Узнаем сколько страниц вообще есть и записываем в rest_of_pages количество оставшихся
        total_pages = self.get_count_of_page()
        rest_of_the_pages = total_pages - 1
        page = 2
        data_file = open(path + name_data_file, 'a')
# ----------------------------ОТПРАВКА POST ЗАПРОСОВ-----------------------------
        while rest_of_the_pages > 0:
            r = self.send_POST(headers, page)
            data_file.write(r.text)
            rest_of_the_pages -= 1
            page += 1
            time.sleep(0.1)
# ------------------------------------------------------------------------------
        data_file.close()
        toc = time.perf_counter()
        # Функция возвращает HTTP ответ от сервера
        self.error_handler('Http '+str(r.status_code))
        return round((toc-tic)*1000, 1)

    # Функция вычисления контрольной crc32 суммы
    # Входные параметры: string - строка для который вычисляем crc32

    @staticmethod
    def generate_check_summ(string):
        return zlib.crc32(bytearray(string.encode('utf-8')))
    # Функция в которой содержится формат отправляемого запроса
    # Входные параметры:
    #
    #
    def send_POST(self, headers, page):
        return requests.post(self.url, json={
            "Page": page, "Count": 25, "Courts": [], "DateFrom": 'null', "DateTo": 'null',
            "Sides": [{'Name': self.inn, 'Type': -1, 'ExactMatch': 'false'}],
            "Judges": [], "CaseNumbers": [], "WithVKSInstances": 'true'},
            headers=headers)
    # Функция парсит файл и находит в нём информацию о количестве страниц по данному запросу
    def get_count_of_page(self):
        try:
            with open(name_data_file, 'r') as pars_file:
                raw_data = pars_file.read()
        except FileNotFoundError:
            self.error_handler('File not found')
            return -1
        raw_data = BeautifulSoup(raw_data, features="html.parser")
        return int(raw_data.find('input', attrs={'type': "hidden", 'id': 'documentsPagesCount'}).get('value'))

    def parsing(self):
        tic = time.perf_counter()
        # Открываем полученный с сервера файл
        try:
            with open(name_data_file, 'r') as pars_file:
                raw_data = pars_file.read()
        except:
            toc = time.perf_counter()
            self.error_handler('Error open file')
            return round((toc-tic)*1000, 1)
    
        # Преобразуем файл в объект BeautifulSoup
        data = BeautifulSoup(raw_data, features="html.parser")

        # Вытаскиваем список судей и итеративно пишем в массив self.judge
        data_list = data.find_all('div', attrs={'class': 'judge'})
        for i in range(len(data_list)):
            self.judge.append(data_list[i].get('title')) 

        # Вытаскиваем список истцов и итеративно пишем в массив self.plaintiff
        data_list = data.find_all('td', attrs={'class': 'plaintiff'})
        for i in range(len(data_list)):
            self.plaintiff.append(data_list[i].find('strong').contents) 
            
        # Вытаскиваем список ответчиков и итеративно пишем в массив self.respondent
        respondent_list = data.find_all('td', attrs={'class': 'respondent'})
        respondent_list = str(respondent_list)
        self.number_of_case = respondent_list.count(str(self.inn))
        respondent_list = BeautifulSoup(str(respondent_list), features="html.parser")
        respondent_list = respondent_list.find_all('span', attrs={'class': 'js-rollover b-newRollover'})
        for i in range(len(respondent_list)):
            self.respondent.append(respondent_list[i].find('strong').contents)

        toc = time.perf_counter()
        self.error_handler('Parsing ok')
        return round((toc-tic)*1000, 1)

    def error_handler(self, status):
        # Ошибки вызванные обращением к серверу
        if status == 'Http 200':
            print('--POST Запрос выполнен. Ответ сервера: %s' % (status[5:]))
        elif status == 'Parsing ok':
            print("--Анализ файла успешно выполнен.")
        else:
            print('----ОШИБКА!!----')
            if status == 'Http 429':
                print('--Данные не загружены.\n--На сайте сработала защита.\nОтвет сервера: 429\n')
            elif status == 'Connection error':
                print('--Данные не загружены.\n--Отсутствует подключение к интернету.')
            elif status == 'Error write file':
                print('--Данные загружены, но не записаны.\n--Ошибка записи в файл.')
            elif status[0:4] == 'Http':
                print('--Данные не загружены.\n--Возникла неизвестная ошибка. Ответ сервера: %s' % (status[5:]))

        # Ошибки вызванные парсером загруженных данных
            elif status == 'File not found':
                print('--Не удалость открыть файл для подсчёта страниц.Причина - отсутствует файл %s\n' % name_data_file)
            elif status == 'Error open file':
                print('--Не удалость выполнить анализ файла. Причина - отсутствует файл %s\n' % name_data_file)
            else:
                print('--Возникла неизвестная ошибка\n')

# ------------------------------ОСНОВНОЙ ЦИКЛ-----------------------------------


print('\n-----Старт программы-----')
tic = time.perf_counter()
inn = '`'  # "7841026793"

Pars = Arbitrage(inn)

Pars.get_data_from_server()
# status = [200, 10]

print('--Старт анализа загруженных данных.')
if Pars.get_count_of_page() != 0:
    status = Pars.parsing()
    
    print("Список судей:"+str(Pars.judge))
    print("Список истцов:"+str(Pars.plaintiff))
    print("Список ответчиков:"+str(Pars.respondent))

    print('Страниц в файле: '+str(Pars.get_count_of_page()))
    print('Количество дел ведущихся в отношении данного ИНН: ' + str(Pars.number_of_case))
else:
    print('--Дел в отношении данного ИНН не ведётся')

toc = time.perf_counter()
print('\n--Время выполнения программы : %s ' % round((toc-tic)*1000, 1) + "мc.")
print('-----Работа программы завершена-----')
