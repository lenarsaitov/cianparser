import requests
from bs4 import BeautifulSoup
import transliterate
import re
import pymorphy2

from cianparser.constants import *


class ParserRentOffers:
    def __init__(self, type_offer: str, type_accommodation: str, location_id: str, rooms, start_page: int, end_page: int):
        self.session = requests.Session()
        self.session.headers = {'Accept-Language': 'ru'}

        self.result = []
        self.type_accommodation = type_accommodation
        self.location_id = location_id
        self.rooms = rooms
        self.start_page = start_page
        self.end_page = end_page

        if type_offer == "rent_long":
            self.type_offer = 4
        elif type_offer == "rent_short":
            self.type_offer = 2

        self.url = None

    def build_url(self):
        rooms_path = ""
        if type(self.rooms) is tuple:
            for count_of_room in self.rooms:
                if type(count_of_room) is int:
                    if count_of_room > 0 and count_of_room < 6:
                        rooms_path += ROOM.format(count_of_room)
                elif type(count_of_room) is str:
                    if count_of_room == "studio":
                        rooms_path += STUDIO
        elif type(self.rooms) is int:
            if self.rooms > 0 and self.rooms < 6:
                rooms_path += ROOM.format(self.rooms)
        elif type(self.rooms) is str:
            if self.rooms == "studio":
                rooms_path += STUDIO
            elif self.rooms == "all":
                rooms_path = ""

        return BASE_LINK + ACCOMMODATION_TYPE_PARAMETER.format(self.type_accommodation) + \
            DURATION_TYPE_PARAMETER.format(self.type_offer) + rooms_path

    def load_page(self, number_page=1):
        self.url = self.build_url().format(number_page, self.location_id)
        res = self.session.get(url=self.url)
        res.raise_for_status()
        return res.text

    def parse_page(self, html: str, number_page: int):
        try:
            soup = BeautifulSoup(html, 'lxml')
        except:
            soup = BeautifulSoup(html, 'html.parser')

        offers = soup.select("div[data-name='HeaderDefault']")
        title = offers[0].text
        city = title[:title.find('Аренда')].split()[-1]
        morph = pymorphy2.MorphAnalyzer()
        city = morph.parse(city)[0].normal_form.title()

        offers = soup.select("div[data-name='Offers'] > article[data-name='CardComponent']")

        if number_page == self.start_page:
            print("Setting [", end="")
            print("=>"*len(offers), end="")
            print("] 100%")

        print(f"{number_page} page: ", end="")
        print("[", end="")
        for block in offers:
            self.parse_block(block=block)
        print("] 100%")

    def parse_page_offer(self, html_offer):
        soup_offer_page = BeautifulSoup(html_offer, 'lxml')
        try:
            text_offer = soup_offer_page.select("div[data-name='BtiContainer'] > div[data-name='BtiHouseData']")[0].text
            year = int(text_offer[text_offer.find("Год постройки")+13: text_offer.find("Год постройки") + 17])
        except:
            year = -1

        try:
            text_offer = soup_offer_page.select("div[data-name='ObjectSummaryDescription'] > div > div:nth-child(1)")[0].text
            comm = (text_offer[: text_offer.find("Общая")])
            comm_meters = int(re.findall(r'\d+', comm)[0])
        except IndexError:
            text_offer = soup_offer_page.select("div[data-name='ObjectSummaryDescription'] > div")[0].text
            comm = (text_offer[: text_offer.find("Общая")])
            comm_meters = int(re.findall(r'\d+', comm)[0])
        except:
            comm_meters = -1

        try:
            text_offer = soup_offer_page.select("div[data-name='ObjectSummaryDescription'] > div > div:nth-child(3)")[0].text
            kitchen = (text_offer[text_offer.find("Кухня")-6: text_offer.find("Кухня")])
            kitchen_meters = int(re.findall(r'\d+', kitchen)[0])
        except IndexError:
            text_offer = soup_offer_page.select("div[data-name='ObjectSummaryDescription'] > div")[0].text
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

        res = self.session.get(url=link)
        res.raise_for_status()
        html_offer_page = res.text

        year_of_construction, comm_meters, kitchen_meters = self.parse_page_offer(html_offer=html_offer_page)
        print("=>", end="")
        self.result.append({
            "accommodation": self.type_accommodation,
            "how_many_rooms": how_many_rooms,
            "price_per_month": price_per_month,
            "street": street,
            "district": district,
            "floor": floor,
            "all_floors": all_floors,
            "square_meters": meters,
            "commissions": commissions,
            "author": author,
            "year_of_construction": year_of_construction,
            "comm_meters": comm_meters,
            "kitchen_meters": kitchen_meters,
            "link": link
        })

    def get_results(self):
        return self.result

    def run(self):
        print(f"\n{' '*15}Start collecting information from pages..")

        for number_page in range(self.start_page, self.end_page+1):
            try:
                html = self.load_page(number_page=number_page)
                self.parse_page(html=html, number_page=number_page)
            except Exception as e:
                print(e)
                print(f"Dont exist this {number_page} page.. Ending parse\n")
                break
