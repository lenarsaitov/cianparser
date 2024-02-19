import bs4
import time
import pathlib
from datetime import datetime
from transliterate import translit

from cianparser.constants import FILE_NAME_SUBURBAN_FORMAT
from cianparser.helpers import union_dicts, define_author, parse_location_data, define_price_data, define_deal_url_id
from cianparser.suburban.page import SuburbanPageParser
from cianparser.base_list import BaseListPageParser


class SuburbanListPageParser(BaseListPageParser):
    def build_file_path(self):
        now_time = datetime.now().strftime("%d_%b_%Y_%H_%M_%S_%f")
        file_name = FILE_NAME_SUBURBAN_FORMAT.format(self.accommodation_type, self.object_type, self.deal_type, self.start_page, self.end_page, translit(self.location_name.lower(), reversed=True), now_time)
        return pathlib.Path(pathlib.Path.cwd(), file_name.replace("'", ""))

    def parse_list_offers_page(self, html, page_number: int, count_of_pages: int, attempt_number: int):
        list_soup = bs4.BeautifulSoup(html, 'html.parser')

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
        common_data["url"] = offer.select("div[data-name='LinkArea']")[0].select("a")[0].get('href')
        common_data["location"] = self.location_name
        common_data["deal_type"] = self.deal_type
        common_data["accommodation_type"] = self.accommodation_type
        common_data["suburban_type"] = self.object_type

        author_data = define_author(block=offer)
        location_data = parse_location_data(block=offer)
        price_data = define_price_data(block=offer)

        if define_deal_url_id(common_data["url"]) in self.result_set:
            return

        page_data = dict()
        if self.with_extra_data:
            suburban_parser = SuburbanPageParser(session=self.session, url=common_data["url"])
            page_data = suburban_parser.parse_page()
            time.sleep(4)

        self.count_parsed_offers += 1
        self.define_average_price(price_data=price_data)
        self.result_set.add(define_deal_url_id(common_data["url"]))
        self.result.append(union_dicts(author_data, common_data, price_data, page_data, location_data))

        if self.with_saving_csv:
            self.save_results()


