import time
import requests
from bs4 import BeautifulSoup
import collections
import csv
import cloudscraper

ParseMetroNames = collections.namedtuple(
    'ParseResults',
    {
        'city',
        'metro_name',
        'metro_id',
    }
)


class Client:
    def __init__(self, start_metro_id=1, end_metro_id=20):
        self.session = cloudscraper.create_scraper()
        self.session.headers = {'Accept-Language': 'en'}

        self.metro_stations = []
        self.metro_set = set()

        self.start_metro_id = start_metro_id
        self.end_metro_id = end_metro_id

    def define_metro(self, html, metro_id: int):
        soup = BeautifulSoup(html, 'html.parser')
        offers = soup.select("div[data-name='GeneralInfoSectionRowComponent']")

        if len(offers) == 0:
            print("_" + "  " + "***")
            return self.metro_stations

        address = offers[1].text

        if ", м." not in address:
            for offer in offers:
                if ", м." in offer.text:
                    address = offer.text

        if address.find(", м.") == 0:
            print("_" + "  " + "***" + "somethins wrong")

        city = "Unknown"
        if "Москва" in address:
            city = "Москва"
        if "Казань" in address:
            city = "Казань"
        if "Санкт-Петербург" in address:
            city = "Санкт-Петербург"
        if "Самара" in address:
            city = "Самара"
        if "Екатеринбург" in address:
            city = "Екатеринбург"
        if "Новосибирск" in address:
            city = "Новосибирск"
        if "Нижний Новгород" in address:
            city = "Нижний Новгород"

        metro = address[address.find(", м.") + len(", м. "):].split(", ")[0]
        print(f"{city}, {metro}, {str(metro_id)}")

        if metro not in self.metro_set:
            self.metro_set.add(metro)
            self.metro_stations.append((city, metro, metro_id))
            self.save_results()

        return self.metro_stations

    def define_all_metro_stations(self):
        for metro_id in range(self.start_metro_id, self.end_metro_id+1):
            path = f'https://www.cian.ru/cat.php?deal_type=rent&engine_version=2&offer_type=flat&p=1&region=1&type=4&metro[0]={metro_id}'
            response = requests.get(path)
            html = response.text
            self.define_metro(html, metro_id)
            time.sleep(2)

        self.metro_stations = sorted(self.metro_stations, key=lambda x: x[0])

    def save_results(self):
        metro_stations_result = [ParseMetroNames(
            city='city',
            metro_name='metro_name',
            metro_id='metro_id',
        )]

        for metro_couple in self.metro_stations:
            metro_stations_result.append(ParseMetroNames(
                city=metro_couple[0],
                metro_name=metro_couple[1],
                metro_id=metro_couple[2],
            ))

        path = f"metro_stations_{self.start_metro_id}_{self.end_metro_id}.csv"
        with open(path, "w") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            for item in self.metro_stations:
                writer.writerow(item)


if __name__ == '__main__':
    definer = Client(start_metro_id=1, end_metro_id=10)
    definer.define_all_metro_stations()
