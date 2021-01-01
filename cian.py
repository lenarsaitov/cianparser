import requests
from bs4 import BeautifulSoup
import re
import math
import logging
import collections

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('wb')

ParseResults = collections.namedtuple(
    'ParseResults',
    {
        'how_many_rooms',
        'price_per_month',
        'address',
        'floor',
        'all_floors',
        'square_meters',
        'commissions',
        'author',
        'link'
    }
)

class Client:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.60 YaBrowser/20.12.0.963 Yowser/2.5 Safari/537.36',
            'Accept-Language': 'ru'
        }
        self.result = []

    def load_page(self):
        url = "https://kazan.cian.ru/cat.php?deal_type=rent&engine_version=2&offer_type=flat&p=2&region=4777&type=4"
        res = self.session.get(url = url)
        res.raise_for_status()
        return res.text

    def parse_page(self, html: str):
        soup = BeautifulSoup(html, 'lxml')
        offers = soup.select("div[data-name='Offers'] > article[data-name='CardComponent']")

        for block in offers:
            self.parse_block(block=block)

    def parse_block(self, block):
        title = block.select("div[data-name='LinkArea']")[0].select("div[data-name='TitleComponent']")[0].text
        if not title:
            logger.error("no title")
            return

        author = block.select("div[data-name='Agent'] div.title-text")[0].text
        if not author:
            logger.error("no author")
            return

        link = block.select("div[data-name='LinkArea']")[0].select("a")[0].get('href')
        if not link:
            logger.error("no link")
            return

        logger.info("%s", link)

        meters = int(title[title.find("м²") - 4: title.find("м²")])
        if "этаж" in title:
            floor_per = title[title.find("м²") + 3: title.find("м²") + 9]
            floor_per = floor_per.replace(' ', '')
            floor_per = floor_per.replace('э', '')
            floor_per = floor_per.split("/")
            all_floors = int(floor_per[1])
            floor = int(floor_per[0])
        else:
            all_floors = -1
            floor = -1

        if "1-комн" in title:
            how_many_rooms = 1
        elif "2-комн" in title:
            how_many_rooms = 2
        elif "3-комн" in title:
            how_many_rooms = 3
        elif "4-комн" in title:
            how_many_rooms = 4
        else:
            how_many_rooms = -1

        address_long = block.select("div[data-name='LinkArea']")[0].select("div[data-name='ContentRow']")[0].text
        address = address_long[address_long.find("Казань") + 8:]

        price_long = block.select("div[data-name='LinkArea']")[0].select("div[data-name='ContentRow']")[1].text
        price_per_month = "".join(price_long[:price_long.find("₽/мес") - 1].split())

        if "%" in price_long:
            commissions = int(price_long[price_long.find("%") - 3:price_long.find("%")].replace(" ", ""))
        else:
            commissions = 0


        self.result.append(ParseResults(
            author = author,
            link = link,
            address = address,
            price_per_month = price_per_month,
            commissions = commissions,
            square_meters = meters,
            how_many_rooms = how_many_rooms,
            floor = floor,
            all_floors = all_floors
        ))



    def run(self):
        html = self.load_page()
        self.parse_page(html=html)

if __name__ == '__main__':
    parser = Client()
    parser.run()

#
# def get_html(url):
#     r = requests.get(url)
#     return r.text
#
# def get_total_pages(html):
#     soup = BeautifulSoup(html, 'lxml')
#     pages = soup.select("div[data-name='SummarySection'] > div > div > h5")[0].text
#     pages = re.findall(r'\d+', pages)
#     total_pages = math.ceil((int(''.join(pages))/28))
#     return total_pages
#
# def get_pages(html):
#     soup = BeautifulSoup(html, 'lxml')
#     pages = soup.select("div[data-name='Pagination'] > div > ul > li")
#
# def get_page_data(html):
#     soup = BeautifulSoup(html, 'lxml')
#     offers = soup.select("div[data-name='Offers'] > article[data-name='CardComponent']")
#     flat = offers.select(" > div > div:nth-child(2) > div:nth-child(1) > div[data-name='LinkArea']")
#     person = offers.select("div[data-name='Agent'] a[data-name='AgentTitle']")
#
#
# def main():
#     print("start..")
#     url = 'https://kazan.cian.ru/cat.php?deal_type=rent&engine_version=2&offer_type=flat&p=4&region=4777&type=4'
#     base_url = 'https://kazan.cian.ru/cat.php?deal_type=rent&engine_version=2&offer_type=flat&region=4777&type=4'
#     page_part = '&p='
#
#     total_pages = get_total_pages(get_html(url))
#
#     for i in range(1,2):
#         url_gen = base_url + page_part + str(i)
#         print(url_gen)
#         html = get_html(url_gen)
#         get_page_data(html)
#
# if __name__ == '__main__':
#     main()