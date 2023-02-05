import itertools
import time

from bs4 import BeautifulSoup
import transliterate
import re
import cloudscraper
import csv
import pathlib
from datetime import datetime
import math

from cianparser.constants import *
from cianparser.helpers import *


class ParserOffers:
    def __init__(self, deal_type: str, accommodation_type: str, city_name: str, location_id: str, rooms,
                 start_page: int, end_page: int, is_saving_csv=False, is_latin=False, is_express_mode=False,
                 is_by_homeowner=False):
        self.session = cloudscraper.create_scraper()
        self.session.headers = {'Accept-Language': 'en'}
        self.is_saving_csv = is_saving_csv
        self.is_latin = is_latin
        self.is_express_mode = is_express_mode
        self.is_by_homeowner = is_by_homeowner

        self.result_parsed = set()
        self.result = []
        self.accommodation_type = accommodation_type
        self.city_name = city_name.strip().replace("'", "").replace(" ", "_")
        self.location_id = location_id
        self.rooms = rooms
        self.start_page = start_page
        self.end_page = end_page

        now_time = datetime.now().strftime("%d_%b_%Y_%H_%M_%S_%f")
        file_name = f'cian_parsing_result_{deal_type}_{self.start_page}_{self.end_page}_{transliterate.translit(self.city_name.lower(), reversed=True)}_{now_time}.csv'
        current_dir_path = pathlib.Path.cwd()
        self.file_path = pathlib.Path(current_dir_path, file_name.replace("'", ""))

        self.rent_type = None
        if deal_type == "rent_long":
            self.rent_type = 4
            self.deal_type = "rent"

        elif deal_type == "rent_short":
            self.rent_type = 2
            self.deal_type = "rent"

        if deal_type == "sale":
            self.deal_type = "sale"

        self.average_price = 0
        self.parsed_announcements_count = 0

        self.url = None

    def is_sale(self):
        return self.deal_type == "sale"

    def is_rent_long(self):
        return self.deal_type == "rent" and self.rent_type == 4

    def is_rent_short(self):
        return self.deal_type == "rent" and self.rent_type == 2

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

        url = BASE_LINK + ACCOMMODATION_TYPE_PARAMETER.format(self.accommodation_type) + \
              DEAL_TYPE.format(self.deal_type) + rooms_path + WITHOUT_NEIGHBORS_OF_CITY

        if self.rent_type is not None:
            url += DURATION_TYPE_PARAMETER.format(self.rent_type)

        if self.is_by_homeowner:
            url += IS_ONLY_HOMEOWNER


        return url

    def load_page(self, number_page=1):
        self.url = self.build_url().format(number_page, self.location_id)
        res = self.session.get(url=self.url)
        res.raise_for_status()
        return res.text

    def parse_page(self, html: str, number_page: int, count_of_pages: int, attempt_number: int):
        try:
            soup = BeautifulSoup(html, 'lxml')
        except:
            soup = BeautifulSoup(html, 'html.parser')

        header = soup.select("div[data-name='HeaderDefault']")
        if len(header) == 0:
            return False, attempt_number + 1, True

        offers = soup.select("article[data-name='CardComponent']")
        page_number_html = soup.select("button[data-name='PaginationButton']")
        if len(page_number_html) == 0:
            return False, attempt_number + 1, True

        if page_number_html[0].text == "Назад" and (number_page != 1 and number_page != 0):
            return True, 0, True

        if number_page == self.start_page:
            print(f"The page from which the collection of information begins: \n {self.url} \n")
            print(f"Collecting information from pages with list of announcements", end="")

        print("")
        print(f"\r {number_page} page: {len(offers)} offers", end="\r", flush=True)

        for ind, block in enumerate(offers):
            self.parse_block(block=block)

            if not self.is_express_mode:
                time.sleep(4)

            total_planed_announcements = len(offers)*count_of_pages

            print(f"\r {number_page - self.start_page + 1} | {number_page} page with list: [" + "=>" * (
                        ind + 1) + "  " * (
                          len(offers) - ind - 1) + "]" + f" {math.ceil((ind + 1) * 100 / len(offers))}" + "%" +
                  f" | Count of all parsed: {self.parsed_announcements_count}."
                  f" Progress ratio: {math.ceil(self.parsed_announcements_count * 100 / total_planed_announcements)} %."
                  f" Average price: {'{:,}'.format(int(self.average_price)).replace(',', ' ')} rub", end="\r",
                  flush=True)

        time.sleep(2)

        return True, 0, True

    def parse_page_offer(self, html_offer):
        soup_offer_page = BeautifulSoup(html_offer, 'lxml')

        page_data = {
            "year_of_construction": -1,
            "living_meters": -1,
            "kitchen_meters": -1,
            "floor": -1,
            "floors_count": -1,
            "rooms_count": -1,
            "phone": "",
        }

        offer_page = soup_offer_page.select("div[data-name='ObjectSummaryDescription']")
        if len(offer_page) == 0:
            return page_data

        try:
            text_offer = offer_page[0].text
            if "Кухня" in text_offer:
                kitchen = (text_offer[:text_offer.find("Кухня")])
                page_data["kitchen_meters"] = float(
                    re.findall(FLOATS_NUMBERS_REG_EXPRESSION, kitchen.replace(",", "."))[-1])
            else:
                page_data["kitchen_meters"] = -1
        except:
            page_data["kitchen_meters"] = -1

        try:
            text_offer = offer_page[0].text
            if "Жилая" in text_offer:
                lining = (text_offer[:text_offer.find("Жилая")])
                page_data["living_meters"] = float(
                    re.findall(FLOATS_NUMBERS_REG_EXPRESSION, lining.replace(",", "."))[-1])
            else:
                page_data["living_meters"] = -1
        except:
            page_data["living_meters"] = -1

        try:
            contact_data = soup_offer_page.select("div[data-name='OfferContactsAside']")[0].text
            if "+7" in contact_data:
                page_data["phone"] = (contact_data[contact_data.find("+7"):contact_data.find("+7") + 16]).\
                    replace(" ", "").\
                    replace("-", "")
        except:
            pass

        try:
            text_offer = offer_page[0].text
            if "Этаж" in text_offer and "из" in text_offer:
                floor_data = (text_offer[:text_offer.find("Этаж")].split("Этаж")[-1])
                page_data["floors_count"] = int(re.findall(r'\d+', floor_data.replace(",", "."))[-1])
                page_data["floor"] = int(re.findall(r'\d+', floor_data.replace(",", "."))[-2])
            else:
                page_data["floors_count"] = -1
                page_data["floor"] = -1
        except:
            page_data["floors_count"] = -1
            page_data["floor"] = -1

        try:
            offer_page = soup_offer_page.select("div[data-name='OfferTitle']")
            page_data["rooms_count"] = define_rooms_count(offer_page[0].text)
        except:
            page_data["rooms_count"] = -1

        build_data = soup_offer_page.select("div[data-name='BtiHouseData']")
        if len(build_data) != 0:
            build_data = build_data[0].text
            year_str = build_data[build_data.find("Год постройки") + 13: build_data.find("Год постройки") + 17]
            ints = re.findall(r'\d+', year_str)
            if len(ints) != 0:
                page_data["year_of_construction"] = int(ints[0])
                return page_data

        offer_page = soup_offer_page.select("div[data-name='Parent']")
        try:
            text_offer = offer_page[0].text
            if "сдача в" in text_offer:
                ints = re.findall(r'\d+', text_offer.split("сдача в")[1])
                if len(ints) != 0:
                    for number in ints:
                        if int(number) > 1000:
                            page_data["year_of_construction"] = int(number)
                            return page_data
        except:
            pass

        try:
            text_offer = offer_page[0].text
            if "сдан в" in text_offer:
                ints = re.findall(r'\d+', text_offer.split("сдан в")[1])
                if len(ints) != 0:
                    for number in ints:
                        if int(number) > 1000:
                            page_data["year_of_construction"] = int(number)
                            return page_data
        except:
            pass

        return page_data

    def parse_page_offer_json(self, html_offer):
        soup_offer_page = BeautifulSoup(html_offer, 'lxml')

        page_data = {
            "year_of_construction": -1,
            "living_meters": -1,
            "kitchen_meters": -1,
            "floor": -1,
            "floors_count": -1,
            "phone": "",
        }

        spans = soup_offer_page.select("span")

        for index, span in enumerate(spans):
            if "Год постройки" in span:
                page_data["year_of_construction"] = spans[index + 1].text

        if page_data["year_of_construction"] == -1:
            p_tags = soup_offer_page.select("p")

            for index, p_tag in enumerate(p_tags):
                if "Год постройки" in p_tag:
                    page_data["year_of_construction"] = p_tags[index + 1].text

        if page_data["year_of_construction"] == -1:
            for index, span in enumerate(spans):
                if "Год сдачи" in span:
                    page_data["year_of_construction"] = spans[index + 1].text

        for index, span in enumerate(spans):
            if "Площадь кухни" in span:
                page_data["kitchen_meters"] = spans[index + 1].text
                floats = re.findall(FLOATS_NUMBERS_REG_EXPRESSION, page_data["kitchen_meters"])
                if len(floats) == 0:
                    page_data["kitchen_meters"] = -1
                else:
                    page_data["kitchen_meters"] = float(floats[0])

        for index, span in enumerate(spans):
            if "Жилая площадь" in span:
                page_data["living_meters"] = spans[index + 1].text
                floats = re.findall(FLOATS_NUMBERS_REG_EXPRESSION, page_data["living_meters"])
                if len(floats) == 0:
                    page_data["living_meters"] = -1
                else:
                    page_data["living_meters"] = float(floats[0])

        for index, span in enumerate(spans):
            if "Этаж" in span:
                text_value = spans[index + 1].text
                ints = re.findall(r'\d+', text_value)
                if len(ints) != 2:
                    page_data["floor"] = -1
                    page_data["floors_count"] = -1
                else:
                    page_data["floor"] = int(ints[0])
                    page_data["floors_count"] = int(ints[1])

        if "+7" in html_offer:
            page_data["phone"] = html_offer[html_offer.find("+7"): html_offer.find("+7") + 16].split('"')[0].\
                replace(" ", "").\
                replace("-", "")

        return page_data

    def define_author(self, block):
        spans = block.select("div")[0].select("span")

        author_data = {
            "author": "",
            "author_type": "",
        }

        for index, span in enumerate(spans):
            if "Агентство недвижимости" in span:
                author_data["author"] = spans[index + 1].text.replace(",", ".").strip()
                author_data["author_type"] = "real_estate_agent"
                return author_data

        for index, span in enumerate(spans):
            if "Собственник" in span:
                author_data["author"] = spans[index + 1].text
                author_data["author_type"] = "homeowner"
                return author_data

        for index, span in enumerate(spans):
            if "Риелтор" in span:
                author_data["author"] = spans[index + 1].text
                author_data["author_type"] = "realtor"
                return author_data

        for index, span in enumerate(spans):
            if "Ук・оф.Представитель" in span:
                author_data["author"] = spans[index + 1].text
                author_data["author_type"] = "official_representative"
                return author_data

        for index, span in enumerate(spans):
            if "Представитель застройщика" in span:
                author_data["author"] = spans[index + 1].text
                author_data["author_type"] = "representative_developer"
                return author_data

        for index, span in enumerate(spans):
            if "Застройщик" in span:
                author_data["author"] = spans[index + 1].text
                author_data["author_type"] = "developer"
                return author_data

        for index, span in enumerate(spans):
            if "ID" in span.text:
                author_data["author"] = span.text
                author_data["author_type"] = "unknown"
                return author_data

        return author_data

    def define_location_data(self, block):
        elements = block.select("div[data-name='LinkArea']")[0]. \
            select("div[data-name='GeneralInfoSectionRowComponent']")

        location_data = dict()
        location_data["district"] = ""
        location_data["street"] = ""
        location_data["underground"] = ""

        if self.is_sale():
            location_data["residential_complex"] = ""

        for index, element in enumerate(elements):
            if "р-н" in element.text:
                address_elements = element.text.split(",")
                if len(address_elements) < 2:
                    continue

                if "ЖК" in address_elements[0] and "«" in address_elements[0] and "»" in address_elements[0]:
                    location_data["residential_complex"] = address_elements[0].split("«")[1].split("»")[0]

                if ", м. " in element.text:
                    location_data["underground"] = element.text.split(", м. ")[1]
                    if "," in location_data["underground"]:
                        location_data["underground"] = location_data["underground"].split(",")[0]

                for ind, elem in enumerate(address_elements):
                    if "р-н" in elem:
                        district = elem.replace("р-н", "").strip()

                        location_data["district"] = district

                        if "ЖК" in address_elements[-1]:
                            location_data["residential_complex"] = address_elements[-1].strip()

                        if "ЖК" in address_elements[-2]:
                            location_data["residential_complex"] = address_elements[-2].strip()

                        if "улица" in address_elements[-1]:
                            location_data["street"] = address_elements[-1].replace("улица", "").strip()
                            return location_data

                        if "улица" in address_elements[-2]:
                            location_data["street"] = address_elements[-2].replace("улица", "").strip()
                            return location_data

                        for after_district_address_element in address_elements[ind + 1:]:
                            if len(list(set(after_district_address_element.split(" ")).intersection(
                                    NOT_STREET_ADDRESS_ELEMENTS))) != 0:
                                continue

                            if len(after_district_address_element.strip().replace(" ", "")) < 4:
                                continue

                            location_data["street"] = after_district_address_element.strip()
                            return location_data

                return location_data

        if location_data["district"] == "":
            for index, element in enumerate(elements):
                if ", м. " in element.text:
                    location_data["underground"] = element.text.split(", м. ")[1]
                    if "," in location_data["underground"]:
                        location_data["underground"] = location_data["underground"].split(",")[0]

                    if self.is_sale():
                        address_elements = element.text.split(",")
                        if "ЖК" in address_elements[-1]:
                            location_data["residential_complex"] = address_elements[-1].strip()

        return location_data

    def define_price_data(self, block):
        elements = block.select("div[data-name='LinkArea']")[0]. \
            select("div[data-name='GeneralInfoSectionRowComponent']")

        price_data = {
            "price_per_month": -1,
            "commissions": 0,
        }

        for element in elements:
            if "₽/мес" in element.text:
                price_description = element.text
                price_data["price_per_month"] = int("".join(price_description[:price_description.find("₽/мес") - 1].split()))

                if "%" in price_description:
                    price_data["commissions"] = int(price_description[price_description.find("%") - 2:price_description.find("%")].replace(" ", ""))

                return price_data

            if "₽" in element.text:
                price_description = element.text
                price_data["price"] = int("".join(price_description[:price_description.find("₽") - 1].split()))

                return price_data

        return price_data

    def define_specification_data(self, block):
        title = block.select("div[data-name='LinkArea']")[0].select("div[data-name='GeneralInfoSectionRowComponent']")[
            0].text

        common_properties = block.select("div[data-name='LinkArea']")[0]. \
            select("div[data-name='GeneralInfoSectionRowComponent']")[0].text

        total_meters = None
        if common_properties.find("м²") is not None:
            total_meters = title[: common_properties.find("м²")].replace(",", ".")
            if len(re.findall(FLOATS_NUMBERS_REG_EXPRESSION, total_meters)) != 0:
                total_meters = float(re.findall(FLOATS_NUMBERS_REG_EXPRESSION, total_meters)[-1].replace(" ", "").replace("-", ""))
            else:
                total_meters = -1

        if "этаж" in common_properties:
            floor_per = common_properties[common_properties.rfind("этаж") - 7: common_properties.rfind("этаж")]

            floor_per = floor_per.split("/")

            if len(floor_per) == 0:
                floor, floors_count = -1, -1
            else:
                floor, floors_count = floor_per[0], floor_per[1]

            ints = re.findall(r'\d+', floor)
            if len(ints) == 0:
                floor = -1
            else:
                floor = int(ints[-1])

            ints = re.findall(r'\d+', floors_count)
            if len(ints) == 0:
                floors_count = -1
            else:
                floors_count = int(ints[-1])
        else:
            floors_count = -1
            floor = -1

        return {
            "floor": floor,
            "floors_count": floors_count,
            "rooms_count": define_rooms_count(common_properties),
            "total_meters": total_meters,
        }

    def parse_block(self, block):
        common_data = dict()
        common_data["link"] = block.select("div[data-name='LinkArea']")[0].select("a")[0].get('href')
        common_data["city"] = self.city_name
        common_data["deal_type"] = self.deal_type
        common_data["accommodation_type"] = self.accommodation_type

        author_data = self.define_author(block=block)
        location_data = self.define_location_data(block=block)
        price_data = self.define_price_data(block=block)
        specification_data = self.define_specification_data(block=block)

        if self.is_by_homeowner and (author_data["author_type"] != "unknown" and author_data["author_type"] != "homeowner"):
            return

        if self.is_latin:
            try:
                location_data["district"] = transliterate.translit(location_data["district"], reversed=True)
                location_data["street"] = transliterate.translit(location_data["street"], reversed=True)
            except:
                pass

            try:
                common_data["author"] = transliterate.translit(common_data["author"], reversed=True)
            except:
                pass

            try:
                common_data["city"] = transliterate.translit(common_data["city"], reversed=True)
            except:
                pass

            try:
                location_data["underground"] = transliterate.translit(location_data["underground"], reversed=True)
            except:
                pass

            try:
                location_data["residential_complex"] = transliterate.translit(location_data["residential_complex"],
                                                                              reversed=True)
            except:
                pass

        page_data = dict()
        if not self.is_express_mode:
            res = self.session.get(url=common_data["link"])
            res.raise_for_status()
            html_offer_page = res.text

            page_data = self.parse_page_offer(html_offer=html_offer_page)
            if page_data["year_of_construction"] == -1 and page_data["kitchen_meters"] == -1 and page_data[
                "floors_count"] == -1:
                page_data = self.parse_page_offer_json(html_offer=html_offer_page)

        specification_data["price_per_m2"] = float(0)
        if "price" in price_data:
            self.average_price = (self.average_price*self.parsed_announcements_count + price_data["price"])/(self.parsed_announcements_count+1)
            price_data["price_per_m2"] = int(float(price_data["price"])/specification_data["total_meters"])
        elif "price_per_month" in price_data:
            self.average_price = (self.average_price*self.parsed_announcements_count + price_data["price_per_month"])/(self.parsed_announcements_count+1)
            price_data["price_per_m2"] = int(float(price_data["price_per_month"])/specification_data["total_meters"])

        self.parsed_announcements_count += 1

        if define_id_url(common_data["link"]) in self.result_parsed:
            return

        self.result_parsed.add(define_id_url(common_data["link"]))
        self.result.append(self.union(author_data, common_data, specification_data, price_data, page_data, location_data))

        if self.is_saving_csv:
            self.save_results()

    def union(self, *dicts):
        return dict(itertools.chain.from_iterable(dct.items() for dct in dicts))

    def get_results(self):
        return self.result

    def correlate_fields_to_deal_type(self):
        if self.is_sale():
            for not_need_field in SPECIFIC_FIELDS_FOR_RENT_LONG:
                if not_need_field in self.result[-1]:
                    del self.result[-1][not_need_field]

            for not_need_field in SPECIFIC_FIELDS_FOR_RENT_SHORT:
                if not_need_field in self.result[-1]:
                    del self.result[-1][not_need_field]

        if self.is_rent_long():
            for not_need_field in SPECIFIC_FIELDS_FOR_RENT_SHORT:
                if not_need_field in self.result[-1]:
                    del self.result[-1][not_need_field]

            for not_need_field in SPECIFIC_FIELDS_FOR_SALE:
                if not_need_field in self.result[-1]:
                    del self.result[-1][not_need_field]

        if self.is_rent_short():
            for not_need_field in SPECIFIC_FIELDS_FOR_RENT_LONG:
                if not_need_field in self.result[-1]:
                    del self.result[-1][not_need_field]

            for not_need_field in SPECIFIC_FIELDS_FOR_SALE:
                if not_need_field in self.result[-1]:
                    del self.result[-1][not_need_field]

        return self.result

    def save_results(self):
        self.correlate_fields_to_deal_type()
        keys = self.result[0].keys()

        with open(self.file_path, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys, delimiter=';')
            dict_writer.writeheader()
            dict_writer.writerows(self.result)

    def load_and_parse_page(self, number_page, count_of_pages, attempt_number):
        html = self.load_page(number_page=number_page)
        return self.parse_page(html=html, number_page=number_page, count_of_pages=count_of_pages, attempt_number=attempt_number)

    def run(self):
        print(f"\n{' ' * 30}Preparing to collect information from pages..")

        if self.is_saving_csv:
            print(f"The absolute path to the file: \n{self.file_path} \n")

        attempt_number_exception = 0
        for number_page in range(self.start_page, self.end_page + 1):
            try:
                parsed, attempt_number = False, 0
                while not parsed and attempt_number < 3:
                    parsed, attempt_number, end = self.load_and_parse_page(number_page=number_page,
                                                                      count_of_pages=self.end_page+1-self.start_page,
                                                                      attempt_number=attempt_number)
                    attempt_number_exception = 0
                    if end:
                        break

            except Exception as e:
                attempt_number_exception += 1
                if attempt_number_exception < 3:
                    continue
                print(f"\n\nException: {e}")
                print(f"The collection of information from the pages with ending parse on {number_page} page...\n")
                print(f"Average price per day: {'{:,}'.format(int(self.average_price)).replace(',', ' ')} rub")
                break

        print(f"\n\nThe collection of information from the pages with list of announcements is completed")
        print(f"Total number of parced announcements: {self.parsed_announcements_count}. ", end="")

        if self.is_sale():
            print(f"Average price: {'{:,}'.format(int(self.average_price)).replace(',', ' ')} rub")
        elif self.is_rent_long():
            print(f"Average price per month: {'{:,}'.format(int(self.average_price)).replace(',', ' ')} rub")
        elif self.is_rent_short():
            print(f"Average price per day: {'{:,}'.format(int(self.average_price)).replace(',', ' ')} rub")
