import bs4
import time
import math
import csv
import pathlib
from datetime import datetime
import transliterate

from cianparser.helpers import *


class DealNewObjectParser:
    def __init__(self, session, city_name: str, start_page: int, end_page: int, is_saving_csv=False, additional_settings=None):

        self.accommodation_type = "newobject"
        self.session = session
        self.city_name = city_name
        self.start_page = start_page
        self.end_page = end_page
        self.is_saving_csv = is_saving_csv
        self.additional_settings = additional_settings

        self.result = []
        self.result_set = set()
        self.file_path = self.build_file_path()
        self.average_price = 0
        self.count_parsed_offers = 0

    def build_file_path(self):
        now_time = datetime.now().strftime("%d_%b_%Y_%H_%M_%S_%f")
        file_name = FILE_NAME_BASE.format(self.accommodation_type, "sale", self.start_page, self.end_page, transliterate.translit(self.city_name.lower(), reversed=True), now_time)
        return pathlib.Path(pathlib.Path.cwd(), file_name.replace("'", ""))

    def print_parse_progress(self, page_number, count_of_pages, offers, ind):
        print(f"\r {page_number - self.start_page + 1}"
              f" | {page_number} page with list: [" + "=>" * (ind + 1) + "  " * (len(offers) - ind - 1) + "]" + f" {math.ceil((ind + 1) * 100 / len(offers))}" + "%" +
              f" | Count of all parsed: {self.count_parsed_offers}."
              f" Progress ratio: {math.ceil(self.count_parsed_offers * 100 / len(offers) * count_of_pages)} %.",
              end="\r", flush=True)

    def parse_list_offers_page(self, html, page_number: int, count_of_pages: int, attempt_number: int):
        list_soup = bs4.BeautifulSoup(html, 'lxml')

        if list_soup.text.find("Captcha") > 0:
            print(f"\r{page_number} page: there is CAPTCHA... failed to parse page...")
            return False, attempt_number + 1, True

        offers = list_soup.select("div[data-mark='GKCard']")
        print("")
        print(f"\r {page_number} page: {len(offers)} offers", end="\r", flush=True)

        if page_number == self.start_page and attempt_number == 0:
            print(f"Collecting information from pages with list of offers", end="")

        # print("\n\n\n", offers[0].select("a[data-mark='Link']"))
        print("\n\n\n", offers[0].select("a[data-mark='Link']")[0].get('href'))
        print("\n\n\n", offers[0].select("span[data-mark='Text']")[0].text)

        # common_data["link"] = offer.select("div[data-name='LinkArea']")[0].select("a")[0].get('href')

        # for ind, offer in enumerate(offers):
        #     self.parse_offer_page(offer=offer)
        #     self.print_parse_progress(page_number=page_number, count_of_pages=count_of_pages, offers=offers, ind=ind)

        time.sleep(2)

        return True, 0, False

    def parse_offer_page(self, offer):
        common_data = dict()
        common_data["link"] = offer.select("div[data-name='LinkArea']")[0].select("a")[0].get('href')
        common_data["city"] = self.city_name
        common_data["accommodation_type"] = self.accommodation_type

        author_data = define_author(block=offer)
        location_data = define_location_data(block=offer, is_sale=self.is_sale())
        price_data = define_price_data(block=offer)
        specification_data = define_specification_data(block=offer)

        if (self.additional_settings is not None and "is_by_homeowner" in self.additional_settings.keys() and
            self.additional_settings["is_by_homeowner"]) and (author_data["author_type"] != "unknown" and author_data["author_type"] != "homeowner"):
            return

        res = self.session.get(url=common_data["link"])
        res.raise_for_status()
        html_offer_page = res.text

        page_data = parse_flat_offer_page(html_offer=html_offer_page)
        if page_data["year_of_construction"] == -1 and page_data["kitchen_meters"] == -1 and page_data[
            "floors_count"] == -1:
            page_data = parse_flat_offer_page_json(html_offer=html_offer_page)

        specification_data["price_per_m2"] = float(0)
        if "price" in price_data:
            self.average_price = (self.average_price * self.count_parsed_offers + price_data["price"]) / (self.count_parsed_offers + 1)
            price_data["price_per_m2"] = int(float(price_data["price"]) / specification_data["total_meters"])
        elif "price_per_month" in price_data:
            self.average_price = (self.average_price * self.count_parsed_offers + price_data["price_per_month"]) / (self.count_parsed_offers + 1)
            price_data["price_per_m2"] = int(float(price_data["price_per_month"]) / specification_data["total_meters"])

        self.count_parsed_offers += 1

        if define_id_url(common_data["link"]) in self.result_set:
            return

        self.result_set.add(define_id_url(common_data["link"]))
        self.result.append(union_dicts(author_data, common_data, specification_data, price_data, page_data, location_data))

        if self.is_saving_csv:
            self.save_results()

        time.sleep(4)

    def save_results(self):
        keys = self.result[0].keys()

        with open(self.file_path, 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, keys, delimiter=';')
            dict_writer.writeheader()
            dict_writer.writerows(self.result)

