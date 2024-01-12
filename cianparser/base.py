import cloudscraper

from cianparser.url_builder import *
from cianparser.deal_flat import DealFlatParser
from cianparser.deal_newobject import DealNewObjectParser


class Base:
    def __init__(self,
                 deal_type: str, accommodation_type: str, city_name: str, location_id: str, rooms,
                 start_page: int, end_page: int, is_saving_csv=False, is_express_mode=False,
                 additional_settings=None,
                 ):
        self.session = cloudscraper.create_scraper()
        self.session.headers = {'Accept-Language': 'en'}

        self.accommodation_type = accommodation_type
        self.is_saving_csv = is_saving_csv
        self.start_page = start_page
        self.end_page = end_page

        self.define_deal_type(deal_type)
        self.url_list_format = self.build_url_list(location_id, rooms, deal_type, accommodation_type,
                                                   self.rent_period_type, additional_settings)

        if self.accommodation_type == "flat":
            self.flat_parser = DealFlatParser(
                session=self.session,
                deal_type=self.deal_type,
                rent_period_type=self.rent_period_type,
                city_name=city_name,
                start_page=start_page,
                end_page=end_page,
                is_saving_csv=is_saving_csv,
                is_express_mode=is_express_mode,
                additional_settings=additional_settings,
            )
        elif self.accommodation_type == "newobject":
            self.newobject_parser = DealNewObjectParser(
                session=self.session,
                city_name=city_name,
                start_page=start_page,
                end_page=end_page,
                is_saving_csv=is_saving_csv,
                additional_settings=additional_settings,
            )

    def define_deal_type(self, deal_type):
        self.rent_period_type = None
        if deal_type == "sale":
            self.deal_type = "sale"
        elif deal_type == "rent_long":
            self.rent_period_type, self.deal_type = 4, "rent"
        elif deal_type == "rent_short":
            self.rent_period_type, self.deal_type = 2, "rent"

    def build_url_list(self, location_id, rooms, deal_type, accommodation_type, rent_period_type, additional_settings):
        url_builder = URLBuilder(self.accommodation_type == "newobject")
        url_builder.add_location(location_id)
        url_builder.add_room(rooms)
        url_builder.add_deal_type(deal_type)
        url_builder.add_accommodation_type(accommodation_type)

        if rent_period_type is not None:
            url_builder.add_rent_period_type(rent_period_type)

        if additional_settings is not None:
            url_builder.add_additional_settings(additional_settings)

        return url_builder.get_url()

    def get_results(self):
        if self.accommodation_type == "flat":
            return self.flat_parser.result
        elif self.accommodation_type == "newobject":
            return self.newobject_parser.result
        else:
            return ""

    def get_file_path(self):
        if self.accommodation_type == "flat":
            return self.flat_parser.file_path
        elif self.accommodation_type == "newobject":
            return self.newobject_parser.file_path
        else:
            return ""

    def get_average_price(self):
        if self.accommodation_type == "flat":
            return self.flat_parser.average_price
        elif self.accommodation_type == "newobject":
            return self.newobject_parser.average_price
        else:
            return ""

    def get_count_parsed_offers(self):
        if self.accommodation_type == "flat":
            return self.flat_parser.count_parsed_offers
        elif self.accommodation_type == "newobject":
            return self.newobject_parser.count_parsed_offers
        else:
            return ""

    def load_list_page(self, page_number):
        url_list = self.url_list_format.format(page_number)

        if page_number == self.start_page:
            print(f"The page from which the collection of information begins: \n {url_list}")

        res = self.session.get(url=url_list)
        res.raise_for_status()

        return res.text

    def parse_list_offers_page(self, html, page_number, count_of_pages, attempt_number):
        if self.accommodation_type == "flat":
            return self.flat_parser.parse_list_offers_page(html, page_number, count_of_pages, attempt_number)
        elif self.accommodation_type == "newobject":
            return self.newobject_parser.parse_list_offers_page(html, page_number, count_of_pages, attempt_number)
        else:
            return ""

    def run(self):
        print(f"\n{' ' * 30}Preparing to collect information from pages..")

        if self.is_saving_csv:
            print(f"The absolute path to the file: \n{self.get_file_path()} \n")

        page_number = self.start_page - 1
        while page_number < self.end_page:
            page_parsed = False
            page_number += 1
            attempt_number_exception = 0

            while attempt_number_exception < 3 and not page_parsed:
                # try:
                    (page_parsed, attempt_number, end_all_parsing) = self.parse_list_offers_page(
                        html=self.load_list_page(page_number=page_number),
                        page_number=page_number,
                        count_of_pages=self.end_page + 1 - self.start_page,
                        attempt_number=attempt_number_exception)

                    if end_all_parsing:
                        attempt_number_exception, page_number = 3, self.end_page

                # except Exception as e:
                #     attempt_number_exception += 1
                #     if attempt_number_exception < 3:
                #         continue
                #     print(f"\n\nException: {e}")
                #     print(f"The collection of information from the pages with ending parse on {page_number} page...\n")
                #     print(
                #         f"Average price per day: {'{:,}'.format(int(self.get_average_price())).replace(',', ' ')} rub")
                #     break

        print(f"\n\nThe collection of information from the pages with list of offers is completed")
        print(f"Total number of parsed offers: {self.get_count_parsed_offers()}. ", end="")

        print(f"Average price: {'{:,}'.format(int(self.get_average_price())).replace(',', ' ')} rub")
