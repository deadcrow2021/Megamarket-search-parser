from selenium import webdriver
from selenium.webdriver.chrome.service import Service 
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import datetime
import time
import csv
from bs4 import BeautifulSoup

from pathlib import Path
import sys
import os


def parse_number_str(text: str) -> int:
    list_of_digits = [x for x in text if x.isdigit()]
    number = ''.join(list_of_digits)
    
    return number


def parse_str(text: str):
    text = text.encode("ascii", "ignore").decode()
    text = text.strip().replace('  ', ' ')
    return text


if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)

path = Path(application_path)
WORK_DIR = path.absolute()

path_to_results = WORK_DIR / 'results'

if not os.path.isdir(path_to_results):
    os.makedirs(path_to_results, exist_ok=True)

# текст в панели поиска
SEARCH_TEXT = str(input('Запрос: '))

use_price_filte = str(input('Использовать фильтр по ценам: 0 - нет | 1 - да. >>> '))

if use_price_filte == '1':
    from_price = str(input('От: '))
    to_price = str(input('До: '))

# сколько раз нажать кнопку "показать еще"
SHOW_MORE_PRESS_NUMBER = 10

options = Options()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
options.add_argument('--disable-notifications')
options.add_argument('--ignore-certificate-errors')
options.add_argument("--disable-proxy-certificate-handler")
options.add_argument("--disable-content-security-policy")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.set_window_size(1600, 900)

URL = 'https://megamarket.ru'

# переход на сайт
driver.get(URL)
time.sleep(2)
# ищем панель поиска и кнопку поиска
search_field = driver.find_element(By.CLASS_NAME, 'search-field')
search_field_input = driver.find_element(By.XPATH, './/*[@id="page-header"]/div/div[1]/div/div/div/div/div[3]/form/div/input')
search_field_button = driver.find_element(By.XPATH, './/*[@id="page-header"]/div/div[1]/div/div/div/div/div[3]/form/div/button')

# ввожу нужный текст в панель поиска и нажимаю на кнопку
search_field_input.send_keys(SEARCH_TEXT)
time.sleep(0.1)
search_field_button.click()
time.sleep(3)

if use_price_filte == '1':
    price_filter = driver.find_elements(By.CLASS_NAME, 'field-range-slider')[0]
    range_inputs_block = price_filter.find_element(By.CLASS_NAME, 'range-inputs')
    labels_blocks = range_inputs_block.find_elements(By.TAG_NAME, 'label')

    for i, label_block in enumerate(labels_blocks):
        input_block = label_block.find_element(By.TAG_NAME, 'input')
        input_block.click()
        time.sleep(0.2)
        input_block.send_keys(Keys.CONTROL + "a")
        time.sleep(0.1)
        input_block.send_keys(Keys.DELETE)
        time.sleep(0.1)

        if i == 0:
            input_block.send_keys(from_price)
        else:
            input_block.send_keys(to_price)
            
        input_block.send_keys(Keys.ENTER)
        time.sleep(3)

i = 1
# несколько раз нажимаю кнопку "показать еще"
while True:
    try:
        show_more = driver.find_element(By.CLASS_NAME, 'catalog-items-list__show-more')
    except:
        break

    try:
        driver.execute_script("arguments[0].click();", show_more)
        print('Кнопка еще нажата', i, 'раз')
    except:
        break

    i += 1
    time.sleep(2)

# нахожу блок со всеми карточками
cards_panel = driver.find_element(By.CLASS_NAME, 'catalog-items-list')
cards = cards_panel.find_elements(By.CLASS_NAME, 'ddl_product_link')
print('Количество карточек', len(cards))

# доп парсер html кода
soup = BeautifulSoup(cards_panel.get_attribute('innerHTML'), 'lxml')

time_name = datetime.datetime.now().strftime('%a %d %b %Y__%H-%M-%S')
name = f'stat__{time_name}_q_{parse_str(SEARCH_TEXT)}.csv'

# открываю csv файл шоб записывать данные
with open(path_to_results / name, 'w', newline='', encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile, delimiter=';')
    writer.writerow([
                    'Title',
                    'Price',
                    'Bonus',
                    'Merchant',
                    'Delivery Time',
                    'Link'
                    ])

    items = soup.find_all("div", {"class": "catalog-item-desktop"})

    # прохожусь по всем карточкам и собираю из них инфу
    for item in items:
        try:
            title = item.find("div", {"class": "catalog-item-regular-desktop__main-info"}).find("a").get_text()
        except:
            title = ''

        try:
            price = item.find("div", {"class": "catalog-item-regular-desktop__price"}).get_text() # .replace('₽', '').replace(' ', '')
        except:
            price = ''

        try:
            bonus = item.find("span", {"class": "bonus-amount"}).get_text()
        except:
            bonus = ''

        try:
            merchant = item.find("span", {"class": "merchant-info__name"}).get_text()
        except:
            merchant = ''

        try:
            delivery_time = item.find("div", {"class": "catalog-item-delivery"}).find("span", {"catalog-item-delivery__text"}).get_text()
        except:
            delivery_time = ''

        try:
            link = item.find("div", {"class": "catalog-item-regular-desktop__main-info"}).find_all("a", href=True)[0]['href']
        except:
            link = ''

        result = [parse_str(title),
                parse_number_str(price),
                parse_number_str(bonus),
                merchant,
                delivery_time.replace('\n', ' '),
                URL + link
            ]

        # убираю ненужные символы из полученных данных
        result = [x.strip() for x in result]
        # записываю строку с данными одной карточки в csv файл
        writer.writerow(result)

driver.quit()
