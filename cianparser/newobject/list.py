import bs4
import time
import math
import csv
import pathlib
from datetime import datetime
from transliterate import translit
import urllib.parse

from cianparser.constants import FILE_NAME_NEWOBJECT_FORMAT
from cianparser.helpers import union_dicts
from cianparser.newobject.page import NewObjectPageParser


class NewObjectListParser:
    def __init__(self, session, location_name: str, with_saving_csv=False):
        self.accommodation_type = "newobject"
        self.deal_type = "sale"
        self.session = session
        self.location_name = location_name
        self.with_saving_csv = with_saving_csv

        self.result = []
        self.result_set = set()
        self.average_price = 0
        self.count_parsed_offers = 0
        self.start_page = 1
        self.end_page = 50
        self.file_path = self.build_file_path()

    def build_file_path(self):
        now_time = datetime.now().strftime("%d_%b_%Y_%H_%M_%S_%f")
        file_name = FILE_NAME_NEWOBJECT_FORMAT.format(self.accommodation_type, translit(self.location_name.lower(), reversed=True), now_time)
        return pathlib.Path(pathlib.Path.cwd(), file_name.replace("'", ""))

    def print_parse_progress(self, page_number, count_of_pages, offers, ind):
        total_planed_offers = len(offers) * count_of_pages
        print(f"\r {page_number - self.start_page + 1}"
              f" | {page_number} page with list: [" + "=>" * (ind + 1) + "  " * (len(offers) - ind - 1) + "]" + f" {math.ceil((ind + 1) * 100 / len(offers))}" + "%" +
              f" | Count of all parsed: {self.count_parsed_offers}."
              f" Progress ratio: {math.ceil(self.count_parsed_offers * 100 / total_planed_offers)} %.",
              end="\r", flush=True)

    def parse_list_offers_page(self, html, page_number: int, count_of_pages: int, attempt_number: int):
        list_soup = bs4.BeautifulSoup(html, 'html.parser')

        if list_soup.text.find("Captcha") > 0:
            print(f"\r{page_number} page: there is CAPTCHA... failed to parse page...")
            return False, attempt_number + 1, True

        offers = list_soup.select("div[data-mark='GKCard']")
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
        common_data["name"] = offer.select_one("span[data-mark='Text']").text
        common_data["location"] = self.location_name
        common_data["accommodation_type"] = self.accommodation_type
        common_data["url"] = "https://" + urllib.parse.urlparse(offer.select_one("a[data-mark='Link']").get('href')).netloc
        common_data["full_full_location_address"] = offer.select_one("div[data-mark='CellAddressBlock']").text

        if common_data["url"] in self.result_set:
            return

        flat_parser = NewObjectPageParser(session=self.session, url=common_data["url"])
        page_data = flat_parser.parse_page()
        time.sleep(4)

        self.count_parsed_offers += 1
        self.result_set.add(common_data["url"])
        self.result.append(union_dicts(common_data, page_data))

        if self.with_saving_csv:
            self.save_results()

    def save_results(self):
        keys = self.result[0].keys()

        with open(self.file_path, 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, keys, delimiter=';')
            dict_writer.writeheader()
            dict_writer.writerows(self.result)
