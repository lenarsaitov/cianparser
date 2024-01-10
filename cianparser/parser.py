import time

from bs4 import BeautifulSoup
import transliterate
import cloudscraper
import csv
import pathlib
from datetime import datetime
import math
import random
import socket

from cianparser.constants import *
from cianparser.helpers import *
from cianparser.url import *


class ParserOffers:
    def __init__(self, deal_type: str, accommodation_type: str, city_name: str, location_id: str, rooms,
                 start_page: int, end_page: int, is_saving_csv=False, is_express_mode=False,
                 additional_settings=None, proxies=None):
        self.session = cloudscraper.create_scraper()
        self.session.headers = {'Accept-Language': 'en'}

        if proxies is not None:
            if len(proxies) == 0:
                proxies = None

        self.proxy_pool = proxies
        self.is_saving_csv = is_saving_csv
        self.is_express_mode = is_express_mode
        self.additional_settings = additional_settings

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
        self.file_path = pathlib.Path(pathlib.Path.cwd(), file_name.replace("'", ""))

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

        self.list_url = None

    def is_sale(self):
        return self.deal_type == "sale"

    def is_rent_long(self):
        return self.deal_type == "rent" and self.rent_type == 4

    def is_rent_short(self):
        return self.deal_type == "rent" and self.rent_type == 2

    def build_list_url(self, page_number, location_id):        
        url_builder = URLBuilder(page_number, location_id)
        url_builder.add_room(self.rooms)
        url_builder.add_deal_type(self.deal_type)
        url_builder.add_accommodation_type(self.accommodation_type)

        if self.rent_type is not None:
            url_builder.add_rent_type(self.rent_type)

        if self.additional_settings is not None:
            url_builder.add_additional_settings(self.additional_settings)

        return url_builder.get_url()

    def load_page(self, page_number=1):
        socket.setdefaulttimeout(10)
        was_proxy = self.proxy_pool is not None
        set_proxy = False
        self.list_url = self.build_list_url(page_number, self.location_id)

        if was_proxy:
            print("The process of checking the proxies... Search an available one among them...")

        ind = 0
        while self.proxy_pool is not None and set_proxy is False:
            ind += 1
            proxy = random.choice(self.proxy_pool)

            available, is_captcha = is_available_proxy(self.list_url, proxy)
            if not available or is_captcha:
                if is_captcha:
                    print(f" {ind} | proxy {proxy}: there is captcha.. trying another")
                else:
                    print(f" {ind} | proxy {proxy}: unavailable.. trying another..")

                self.proxy_pool.remove(proxy)
                if len(self.proxy_pool) == 0:
                    self.proxy_pool = None
            else:
                print(f" {ind} | proxy {proxy}: available.. stop searching")
                self.session.proxies = {"http": proxy, "https": proxy}
                set_proxy = True

        if was_proxy and set_proxy is False:
            return None

        res = self.session.get(url=self.list_url)
        res.raise_for_status()

        return res.text

    def parse_list(self, html: str, page_number: int, count_of_pages: int, attempt_number: int):
        try:
            soup = BeautifulSoup(html, 'lxml')
        except:
            soup = BeautifulSoup(html, 'html.parser')

        if page_number == self.start_page and attempt_number == 0:
            print(f"The page from which the collection of information begins: \n {self.list_url}")

        if soup.text.find("Captcha") > 0:
            print(f"\r{page_number} page: there is CAPTCHA... failed to parse page...")

            if self.proxy_pool is not None:
                proxy = random.choice(self.proxy_pool)
                print(f"\r{page_number} page: new attempt with proxy {proxy}...")
                self.session.proxies = {"http": proxy}
                return False, attempt_number + 1, False

            return False, attempt_number + 1, True

        header = soup.select("div[data-name='HeaderDefault']")
        if len(header) == 0:
            return False, attempt_number + 1, False

        if page_number == self.start_page and attempt_number == 0:
            print(f"Collecting information from pages with list of announcements", end="")

        offers = soup.select("article[data-name='CardComponent']")
        print("")
        print(f"\r {page_number} page: {len(offers)} offers", end="\r", flush=True)

        for ind, block in enumerate(offers):
            self.parse_offer(block=block)

            if not self.is_express_mode:
                time.sleep(4)

            print(f"\r {page_number - self.start_page + 1} | {page_number} page with list: [" + "=>" * (
                    ind + 1) + "  " * (
                          len(offers) - ind - 1) + "]" + f" {math.ceil((ind + 1) * 100 / len(offers))}" + "%" +
                  f" | Count of all parsed: {self.parsed_announcements_count}."
                  f" Progress ratio: {math.ceil(self.parsed_announcements_count * 100 / len(offers) * count_of_pages)} %."
                  f" Average price: {'{:,}'.format(int(self.average_price)).replace(',', ' ')} rub", end="\r",
                  flush=True)

        time.sleep(2)

        return True, 0, False

    def parse_offer(self, block):
        common_data = dict()
        common_data["link"] = block.select("div[data-name='LinkArea']")[0].select("a")[0].get('href')
        common_data["city"] = self.city_name
        common_data["deal_type"] = self.deal_type
        common_data["accommodation_type"] = self.accommodation_type

        author_data = define_author(block=block)
        location_data = define_location_data(block=block, is_sale=self.is_sale())
        price_data = define_price_data(block=block)
        specification_data = define_specification_data(block=block)

        if (self.additional_settings is not None and "is_by_homeowner" in self.additional_settings.keys() and
            self.additional_settings["is_by_homeowner"]) and (
                author_data["author_type"] != "unknown" and author_data["author_type"] != "homeowner"):
            return

        page_data = dict()
        if not self.is_express_mode:
            res = self.session.get(url=common_data["link"])
            res.raise_for_status()
            html_offer_page = res.text

            page_data = parse_page_offer(html_offer=html_offer_page)
            if page_data["year_of_construction"] == -1 and page_data["kitchen_meters"] == -1 and page_data[
                "floors_count"] == -1:
                page_data = parse_page_offer_json(html_offer=html_offer_page)

        specification_data["price_per_m2"] = float(0)
        if "price" in price_data:
            self.average_price = (self.average_price * self.parsed_announcements_count + price_data["price"]) / (
                    self.parsed_announcements_count + 1)
            price_data["price_per_m2"] = int(float(price_data["price"]) / specification_data["total_meters"])
        elif "price_per_month" in price_data:
            self.average_price = (self.average_price * self.parsed_announcements_count + price_data[
                "price_per_month"]) / (self.parsed_announcements_count + 1)
            price_data["price_per_m2"] = int(float(price_data["price_per_month"]) / specification_data["total_meters"])

        self.parsed_announcements_count += 1

        if define_id_url(common_data["link"]) in self.result_parsed:
            return

        self.result_parsed.add(define_id_url(common_data["link"]))
        self.result.append(
            union_dicts(author_data, common_data, specification_data, price_data, page_data, location_data))

        if self.is_saving_csv:
            self.save_results()

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

        with open(self.file_path, 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, keys, delimiter=';')
            dict_writer.writeheader()
            dict_writer.writerows(self.result)

    def load_and_parse_page(self, page_number, count_of_pages, attempt_number):
        html = self.load_page(page_number=page_number)

        if html is None:
            return False, attempt_number + 1, True

        return self.parse_list(html=html, page_number=page_number, count_of_pages=count_of_pages, attempt_number=attempt_number)

    def run(self):
        print(f"\n{' ' * 30}Preparing to collect information from pages..")

        if self.is_saving_csv:
            print(f"The absolute path to the file: \n{self.file_path} \n")

        page_number = self.start_page - 1
        while page_number < self.end_page:
            page_parsed = False
            page_number += 1
            attempt_number_exception = 0

            while attempt_number_exception < 3 and not page_parsed:
                try:
                    (page_parsed, attempt_number, end_all_parsing) = self.load_and_parse_page(
                        page_number=page_number,
                        count_of_pages=self.end_page + 1 - self.start_page,
                        attempt_number=attempt_number_exception)

                    if end_all_parsing:
                        attempt_number_exception = 3
                        page_number = self.end_page

                except Exception as e:
                    attempt_number_exception += 1
                    if attempt_number_exception < 3:
                        continue
                    print(f"\n\nException: {e}")
                    print(f"The collection of information from the pages with ending parse on {page_number} page...\n")
                    print(f"Average price per day: {'{:,}'.format(int(self.average_price)).replace(',', ' ')} rub")
                    break

        print(f"\n\nThe collection of information from the pages with list of announcements is completed")
        print(f"Total number of parsed announcements: {self.parsed_announcements_count}. ", end="")

        if self.is_sale():
            print(f"Average price: {'{:,}'.format(int(self.average_price)).replace(',', ' ')} rub")
        elif self.is_rent_long():
            print(f"Average price per month: {'{:,}'.format(int(self.average_price)).replace(',', ' ')} rub")
        elif self.is_rent_short():
            print(f"Average price per day: {'{:,}'.format(int(self.average_price)).replace(',', ' ')} rub")
