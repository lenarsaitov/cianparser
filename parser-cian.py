import requests
from bs4 import BeautifulSoup
import collections
import csv
import transliterate
import re
import argparse
import pymorphy2

ParseResults = collections.namedtuple(
    'ParseResults',
    {
        'how_many_rooms',
        'price_per_month',
        'street',
        'district',
        'floor',
        'all_floors',
        'square_meters',
        'commissions',
        'author',
        'year_of_construction',
        'comm_meters',
        'kitchen_meters',
        'link'
    }
)

parser = argparse.ArgumentParser()
parser.add_argument('--city_id', type=int, default=4777, help="City id")
parser.add_argument('--page_start', type=int, default=1, help="Page where parser begin")
parser.add_argument('--page_end', type=int, default=50, help="Page where parser begin")
parser.add_argument('--file_name', type=str, default="data", help="Name of file where will save parsed results")

args = parser.parse_args()
print(f"\nCity id: {args.city_id}")
print(f"Page start: {args.page_start}")
print(f"Page end: {args.page_end}")
print(f"File name: {args.file_name}.csv \n")

class Client:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
                'Accept-Language': 'ru'
        }
        self.result = []
        self.result.append(ParseResults(
            how_many_rooms='How_many_rooms',
            price_per_month='Price_per_month',
            street='Street',
            district = 'District',
            floor='Floor',
            all_floors='All_floors',
            square_meters='Square_meters',
            commissions='Commissions %',
            author='Author',
            year_of_construction='Year_of_construction',
            comm_meters='Living_area',
            kitchen_meters='kitchen_meters',
            link='Link'
        ))

    def load_page(self, i = 1):
        self.url = f"https://cian.ru/cat.php?deal_type=rent&engine_version=2&offer_type=flat&p={i}&region={args.city_id}&type=4"
        res = self.session.get(url = self.url)
        res.raise_for_status()
        return res.text

    def parse_page(self, html: str):
        try:
            soup = BeautifulSoup(html, 'lxml')
        except:
            soup = BeautifulSoup(html, 'html.parser')

        offers = soup.select("div[data-name='HeaderDefault']")
        title = offers[0].text
        city = title[:title.find('Аренда')].split()[-1]
        morph = pymorphy2.MorphAnalyzer()
        city = morph.parse(city)[0].normal_form.title()

        print(f"City name: {city}")

        offers = soup.select("div[data-name='Offers'] > article[data-name='CardComponent']")
        for block in offers:
            self.parse_block(block=block)

    def parse_page_offer(self, html_offer):
        soup_offer_page = BeautifulSoup(html_offer, 'lxml')
        try:
            text_offer = soup_offer_page.select("div[data-name='BtiContainer'] > div[data-name='BtiHouseData']")[0].text
            year = int(text_offer[text_offer.find("Год постройки")+13: text_offer.find("Год постройки") + 17])
        except:
            year = -1

        try:
            text_offer = soup_offer_page.select("div[data-name='Description'] > div > div:nth-child(2)")[0].text
            comm = (text_offer[: text_offer.find("Общая")])
            comm_meters = int(re.findall(r'\d+', comm)[0])
        except IndexError:
            text_offer = soup_offer_page.select("div[data-name='Description'] > div")[0].text
            comm = (text_offer[: text_offer.find("Общая")])
            comm_meters = int(re.findall(r'\d+', comm)[0])
        except:
            comm_meters = -1

        try:
            text_offer = soup_offer_page.select("div[data-name='Description'] > div > div:nth-child(2)")[0].text
            kitchen = (text_offer[text_offer.find("Кухня")-6: text_offer.find("Кухня")])
            kitchen_meters = int(re.findall(r'\d+', kitchen)[0])
        except IndexError:
            text_offer = soup_offer_page.select("div[data-name='Description'] > div")[0].text
            if "Кухня" in text_offer:
                kitchen = (text_offer[text_offer.find("Кухня")-6: text_offer.find("Кухня")])
                kitchen_meters = int(re.findall(r'\d+', kitchen)[0])
            else:
                kitchen_meters = -1
        except:
            kitchen_meters = -1

        return (year, comm_meters, kitchen_meters)

    def parse_block(self, block):
        title = block.select("div[data-name='LinkArea']")[0].select("div[data-name='TitleComponent']")[0].text

        try:
            author = block.select("div[data-name='Agent']")[0].select("div[data-name='ContentRow']")[0].text
        except:
            try:
                author = block.select("div[data-name='Agent']")[0].select("a[data-name='AgentTitle']")[0].text
            except:
                author = block.select("div[data-name='Agent']")[0].select("span[data-name='AgentTitle']")[0].text

        if "Опыт" in author:
            author = author[:author.find("Опыт")]

        link = block.select("div[data-name='LinkArea']")[0].select("a")[0].get('href')

        try:
            meters = int(title[title.find("м²") - 4: title.find("м²")])
        except:
            meters = int(title[title.find("м²") - 5: title.find("м²")].split(',')[0])

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

        if "1-комн" in title or "Студия" in title:
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
        district = address_long[address_long.find("р-н") + 4:].split(",")[0]
        street = address_long.split(",")[-2]
        street = street.replace("улица", "")

        price_long = block.select("div[data-name='LinkArea']")[0].select("div[data-name='ContentRow']")[1].text
        price_per_month = "".join(price_long[:price_long.find("₽/мес") - 1].split())
        price_per_month = int(price_per_month)

        if "%" in price_long:
            commissions = int(price_long[price_long.find("%") - 2:price_long.find("%")].replace(" ", ""))
        else:
            commissions = 0

        district = transliterate.translit(district, reversed=True)
        street = transliterate.translit(street, reversed=True)

        try:
            author = transliterate.translit(author, reversed=True)
        except:
            pass

        res = self.session.get(url = link)
        res.raise_for_status()
        html_offer_page = res.text

        year_of_construction, comm_meters, kitchen_meters = self.parse_page_offer(html_offer = html_offer_page)
        print(f"Year of construction, common and kitchen meters: {year_of_construction}, {comm_meters}, {kitchen_meters}")

        self.result.append(ParseResults(
            how_many_rooms=how_many_rooms,
            price_per_month=price_per_month,
            street=street,
            district = district,
            floor=floor,
            all_floors=all_floors,
            square_meters=meters,
            commissions=commissions,
            author = author,
            year_of_construction = year_of_construction,
            comm_meters = comm_meters,
            kitchen_meters = kitchen_meters,
            link = link
        ))

    def save_results(self):
        path_file_name = args.file_name.split(".")[0]
        path = f"{path_file_name}.csv"
        print(f"Save results to {path} file..")

        with open(path, "w") as f:
            writer = csv.writer(f, quoting = csv.QUOTE_MINIMAL)
            for item in self.result:
                writer.writerow(item)

    def run(self, page_start, page_end):
        print("Start parsing..")
        for i in range(page_start, page_end):
            print(f"Parsing {i} page...")
            try:
                html = self.load_page(i=i)
                self.parse_page(html=html)
            except:
                print(f"Dont exist this {i} page..")
                break

if __name__ == '__main__':
    parser = Client()
    parser.run(args.page_start, args.page_end)

    parser.save_results()