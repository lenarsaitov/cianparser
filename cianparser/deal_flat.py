import bs4
import time
import math
import csv
import pathlib
from datetime import datetime
import transliterate

from cianparser.helpers import *


class DealFlatParser:
    def __init__(self,
                 session,
                 deal_type: str, rent_period_type, location_name: str,
                 with_saving_csv=False, with_extra_data=False,
                 additional_settings=None):
        self.accommodation_type = "flat"
        self.session = session
        self.deal_type = deal_type
        self.rent_period_type = rent_period_type
        self.location_name = location_name
        self.with_saving_csv = with_saving_csv
        self.with_extra_data = with_extra_data
        self.additional_settings = additional_settings

        self.result = []
        self.result_set = set()
        self.average_price = 0
        self.count_parsed_offers = 0
        self.start_page = 1 if (additional_settings is None or "start_page" not in additional_settings.keys()) else additional_settings["start_page"]
        self.end_page = 100 if (additional_settings is None or "end_page" not in additional_settings.keys()) else additional_settings["end_page"]
        self.file_path = self.build_file_path()

    def is_sale(self):
        return self.deal_type == "sale"

    def is_rent_long(self):
        return self.deal_type == "rent" and self.rent_period_type == 4

    def is_rent_short(self):
        return self.deal_type == "rent" and self.rent_period_type == 2

    def build_file_path(self):
        now_time = datetime.now().strftime("%d_%b_%Y_%H_%M_%S_%f")
        file_name = FILE_NAME_BASE.format(self.accommodation_type, self.deal_type, self.start_page, self.end_page, transliterate.translit(self.location_name.lower(), reversed=True), now_time)
        return pathlib.Path(pathlib.Path.cwd(), file_name.replace("'", ""))

    def print_parse_progress(self, page_number, count_of_pages, offers, ind):
        total_planed_offers = len(offers) * count_of_pages
        print(f"\r {page_number - self.start_page + 1}"
              f" | {page_number} page with list: [" + "=>" * (ind + 1) + "  " * (len(offers) - ind - 1) + "]" + f" {math.ceil((ind + 1) * 100 / len(offers))}" + "%" +
              f" | Count of all parsed: {self.count_parsed_offers}."
              f" Progress ratio: {math.ceil(self.count_parsed_offers * 100 / total_planed_offers)} %."
              f" Average price: {'{:,}'.format(int(self.average_price)).replace(',', ' ')} rub",
              end="\r", flush=True)

    def parse_list_offers_page(self, html, page_number: int, count_of_pages: int, attempt_number: int):
        list_soup = bs4.BeautifulSoup(html, 'lxml')

        if list_soup.text.find("Captcha") > 0:
            print(f"\r{page_number} page: there is CAPTCHA... failed to parse page...")
            return False, attempt_number + 1, True

        header = list_soup.select("div[data-name='HeaderDefault']")
        if len(header) == 0:
            return False, attempt_number + 1, False

        offers = list_soup.select("article[data-name='CardComponent']")
        print("")
        print(f"\r {page_number} page: {len(offers)} offers", end="\r", flush=True)

        if page_number == self.start_page and attempt_number == 0:
            print(f"Collecting information from pages with list of offers", end="\n")

        for ind, offer in enumerate(offers):
            self.parse_offer(offer=offer)
            self.print_parse_progress(page_number=page_number, count_of_pages=count_of_pages, offers=offers, ind=ind)

        time.sleep(2)

        return True, 0, False

    def parse_offer(self, offer):
        common_data = dict()
        common_data["link"] = offer.select("div[data-name='LinkArea']")[0].select("a")[0].get('href')
        common_data["location"] = self.location_name
        common_data["deal_type"] = self.deal_type
        common_data["accommodation_type"] = self.accommodation_type

        author_data = define_author(block=offer)
        location_data = define_location_data(block=offer, is_sale=self.is_sale())
        price_data = define_price_data(block=offer)
        specification_data = define_specification_data(block=offer)

        if (self.additional_settings is not None and "is_by_homeowner" in self.additional_settings.keys() and
            self.additional_settings["is_by_homeowner"]) and (author_data["author_type"] != "unknown" and author_data["author_type"] != "homeowner"):
            return

        page_data = dict()
        if self.with_extra_data:
            res = self.session.get(url=common_data["link"])
            res.raise_for_status()
            html_offer_page = res.text

            page_data = parse_flat_offer_page(html_offer=html_offer_page)
            if page_data["year_of_construction"] == -1 and page_data["kitchen_meters"] == -1 and page_data["floors_count"] == -1:
                page_data = parse_flat_offer_page_json(html_offer=html_offer_page)

        specification_data["price_per_m2"] = float(0)
        if "price" in price_data:
            self.average_price = (self.average_price * self.count_parsed_offers + price_data["price"]) / (self.count_parsed_offers + 1)
            price_data["price_per_m2"] = int(float(price_data["price"]) / specification_data["total_meters"])
        elif "price_per_month" in price_data:
            self.average_price = (self.average_price * self.count_parsed_offers + price_data["price_per_month"]) / (self.count_parsed_offers + 1)
            price_data["price_per_m2"] = int(float(price_data["price_per_month"]) / specification_data["total_meters"])

        self.count_parsed_offers += 1

        if define_url_id(common_data["link"]) in self.result_set:
            return

        self.result_set.add(define_url_id(common_data["link"]))
        self.result.append(union_dicts(author_data, common_data, specification_data, price_data, page_data, location_data))

        if self.with_saving_csv:
            self.save_results()

        if self.with_extra_data:
            time.sleep(4)

    def save_results(self):
        self.remove_unnecessary_fields()
        keys = self.result[0].keys()

        with open(self.file_path, 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, keys, delimiter=';')
            dict_writer.writeheader()
            dict_writer.writerows(self.result)

    def remove_unnecessary_fields(self):
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
