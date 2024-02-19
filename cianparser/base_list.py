import math
import csv

from cianparser.constants import SPECIFIC_FIELDS_FOR_RENT_LONG, SPECIFIC_FIELDS_FOR_RENT_SHORT, SPECIFIC_FIELDS_FOR_SALE


class BaseListPageParser:
    def __init__(self,
                 session,
                 accommodation_type: str, deal_type: str, rent_period_type, location_name: str,
                 with_saving_csv=False, with_extra_data=False,
                 object_type=None, additional_settings=None):
        self.accommodation_type = accommodation_type
        self.session = session
        self.deal_type = deal_type
        self.rent_period_type = rent_period_type
        self.location_name = location_name
        self.with_saving_csv = with_saving_csv
        self.with_extra_data = with_extra_data
        self.additional_settings = additional_settings
        self.object_type = object_type

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
        pass

    def define_average_price(self, price_data):
        if "price" in price_data:
            self.average_price = (self.average_price * self.count_parsed_offers + price_data["price"]) / self.count_parsed_offers
        elif "price_per_month" in price_data:
            self.average_price = (self.average_price * self.count_parsed_offers + price_data["price_per_month"]) / self.count_parsed_offers

    def print_parse_progress(self, page_number, count_of_pages, offers, ind):
        total_planed_offers = len(offers) * count_of_pages
        print(f"\r {page_number - self.start_page + 1}"
              f" | {page_number} page with list: [" + "=>" * (ind + 1) + "  " * (len(offers) - ind - 1) + "]" + f" {math.ceil((ind + 1) * 100 / len(offers))}" + "%" +
              f" | Count of all parsed: {self.count_parsed_offers}."
              f" Progress ratio: {math.ceil(self.count_parsed_offers * 100 / total_planed_offers)} %."
              f" Average price: {'{:,}'.format(int(self.average_price)).replace(',', ' ')} rub",
              end="\r", flush=True)

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

    def save_results(self):
        self.remove_unnecessary_fields()
        keys = self.result[0].keys()

        with open(self.file_path, 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, keys, delimiter=';')
            dict_writer.writeheader()
            dict_writer.writerows(self.result)