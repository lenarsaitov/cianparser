import time

from bs4 import BeautifulSoup
import transliterate
import re
import pymorphy2
import cloudscraper
import sys
import csv
import os
from datetime import datetime

from cianparser.constants import *


class ParserRentOffers:
    def __init__(self, type_offer: str, type_accommodation: str, location_id: str, rooms, start_page: int,
                 end_page: int, save_csv=False):
        self.session = cloudscraper.create_scraper()
        self.session.headers = {'Accept-Language': 'en'}
        self.save_csv = save_csv

        self.result = []
        self.type_accommodation = type_accommodation
        self.location_id = location_id
        self.rooms = rooms
        self.start_page = start_page
        self.end_page = end_page

        file_name = f'parsing_result_{self.start_page}_{self.end_page}_{self.location_id}_{datetime.now()}.csv'
        current_path = os.path.abspath(".")
        self.file_path = os.path.join(current_path, file_name)

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

    def parse_page(self, html: str, number_page: int, attempt_number: int):
        try:
            soup = BeautifulSoup(html, 'lxml')
        except:
            soup = BeautifulSoup(html, 'html.parser')

        header = soup.select("div[data-name='HeaderDefault']")
        if len(header) == 0:
            return False, attempt_number+1

        title = header[0].text
        city = title[:title.find('Аренда')].split()[-1]
        morph = pymorphy2.MorphAnalyzer()
        city = morph.parse(city)[0].normal_form.title()

        offers = soup.select("article[data-name='CardComponent']")

        if number_page == self.start_page:
            print("Setting [", end="")
            print("=>" * len(offers), end="")
            print("] 100%")

        print(f"{number_page} page: {len(offers)} offers")

        for ind, block in enumerate(offers):
            self.parse_block(block=block)
            time.sleep(4)
            sys.stdout.write("\033[F")
            print(f"{number_page} page: [" + "=>" * (ind+1) + "  " * (len(offers) - ind - 1) + "]" + f" {round((ind + 1) * 100/len(offers))}" + "%")
            time.sleep(1)

        return True, 0

    def parse_page_offer(self, html_offer):
        soup_offer_page = BeautifulSoup(html_offer, 'lxml')

        build_data = soup_offer_page.select("div[data-name='BtiHouseData']")
        if len(build_data) == 0:
            year = -1
        else:
            build_data = build_data[0].text
            year_str = build_data[build_data.find("Год постройки") + 13: build_data.find("Год постройки") + 17]
            ints = re.findall(r'\d+', year_str)
            if len(ints) == 0:
                year = -1
            else:
                year = int(ints[0])

        offer_page = soup_offer_page.select("div[data-name='ObjectSummaryDescription']")
        if len(offer_page) == 0:
            return year, -1, -1

        text_offer = offer_page[0].text

        try:
            if "Общая" in text_offer:
                comm = (text_offer[: text_offer.find("Общая")])
                comm_meters = int(re.findall(r'\d+', comm)[0])
            else:
                comm_meters = -1
        except:
            comm_meters = -1

        try:
            if "Кухня" in text_offer:
                kitchen = (text_offer[text_offer.find("Кухня") - 5: text_offer.find("Кухня")])
                kitchen_meters = int(re.findall(r'\d+', kitchen)[0])
            else:
                kitchen_meters = -1
        except:
            kitchen_meters = -1

        return year, comm_meters, kitchen_meters

    def define_author(self, block):
        author = ""
        spans = block.select("div")[0].select("span")

        for index, span in enumerate(spans):
            if "Агентство недвижимости" in span:
                author = spans[index + 1].text
                return author

        for index, span in enumerate(spans):
            if "Собственник" in span:
                author = spans[index + 1].text
                return author

        for index, span in enumerate(spans):
            if "Риелтор" in span:
                author = spans[index + 1].text
                return author

        return author

    def define_location_data(self, block):
        elements = block.select("div[data-name='LinkArea']")[0]. \
            select("div[data-name='GeneralInfoSectionRowComponent']")

        for index, element in enumerate(elements):
            if "р-н" in element.text:
                location = element.text
                district = location[location.find("р-н") + 4:].split(",")[0]
                street = location.split(",")[-2]
                street = street.replace("улица", "")

                return district, street

        return "", ""

    def define_price_data(self, block):
        elements = block.select("div[data-name='LinkArea']")[0]. \
            select("div[data-name='GeneralInfoSectionRowComponent']")

        for element in elements:
            if "₽/мес" in element.text:
                price_description = element.text
                price_per_month = int("".join(price_description[:price_description.find("₽/мес") - 1].split()))

                if "%" in price_description:
                    commissions = int(
                        price_description[price_description.find("%") - 2:price_description.find("%")].replace(" ", ""))
                else:
                    commissions = 0

                return price_per_month, commissions

        return None, None

    def parse_block(self, block):
        author = self.define_author(block=block)
        link = block.select("div[data-name='LinkArea']")[0].select("a")[0].get('href')

        common_properties = block.select("div[data-name='LinkArea']")[0]. \
            select("div[data-name='GeneralInfoSectionRowComponent']")[0].text

        meters = None
        if common_properties.find("м²") is not None:
            meters = common_properties[common_properties.find("м²") - 5: common_properties.find("м²")]

            if "," in meters:
                meters = meters.split(',')
                if meters[0].isdigit():
                    meters = int(meters[0])
                elif meters[1].isdigit():
                    meters = int(meters[1])
                else:
                    meters = 0

        if "этаж" in common_properties:
            floor_per = common_properties[common_properties.find("м²") + 3: common_properties.find("м²") + 9]
            floor_per = floor_per.replace(' ', '')
            floor_per = floor_per.replace('э', '')
            floor_per = floor_per.split("/")
            all_floors = int(floor_per[1])
            floor = int(floor_per[0])
        else:
            all_floors = -1
            floor = -1

        if "1-комн" in common_properties or "Студия" in common_properties:
            how_many_rooms = 1
        elif "2-комн" in common_properties:
            how_many_rooms = 2
        elif "3-комн" in common_properties:
            how_many_rooms = 3
        elif "4-комн" in common_properties:
            how_many_rooms = 4
        elif "5-комн" in common_properties:
            how_many_rooms = 5
        else:
            how_many_rooms = -1

        district, street = self.define_location_data(block)
        price_per_month, commissions = self.define_price_data(block)

        try:
            district = transliterate.translit(district, reversed=True)
            street = transliterate.translit(street, reversed=True)
        except:
            pass

        try:
            author = transliterate.translit(author, reversed=True)
        except:
            pass

        res = self.session.get(url=link)
        res.raise_for_status()
        html_offer_page = res.text

        year_of_construction, comm_meters, kitchen_meters = self.parse_page_offer(html_offer=html_offer_page)
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

        if self.save_csv:
            self.save_results()

    def get_results(self):
        return self.result

    def save_results(self):
        keys = self.result[0].keys()

        with open(self.file_path, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(self.result)

    def load_and_parse_page(self, number_page, attempt_number):
        html = self.load_page(number_page=number_page)
        return self.parse_page(html=html, number_page=number_page, attempt_number=attempt_number)

    def run(self):
        print(f"\n{' ' * 18}Collecting information from pages..")
        print(f"The absolute path to the file: \n", self.file_path)

        for number_page in range(self.start_page, self.end_page + 1):
            try:
                parsed, attempt_number = False, 0
                while not parsed and attempt_number < 3:
                    parsed, attempt_number = self.load_and_parse_page(number_page=number_page, attempt_number=attempt_number)
            except Exception as e:
                print("Failed exception: ", e)
                print(f"Ending parse on {number_page} page...\n")
                break
