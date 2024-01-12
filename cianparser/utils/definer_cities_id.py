import time
import requests
from bs4 import BeautifulSoup
import pymorphy2
import collections
import csv
import cloudscraper

ParseCityNames = collections.namedtuple(
    'ParseResults',
    {
        'location_name',
        'city_id',
    }
)


class Client:
    def __init__(self, start_location_id=1, end_location_id=20):
        self.session = cloudscraper.create_scraper()
        self.session.headers = {'Accept-Language': 'en'}

        self.cities = []
        self.cities_set = set()

        self.start_location_id = start_location_id
        self.end_location_id = end_location_id

    def define_city(self, html, location_id: int):
        soup = BeautifulSoup(html, 'html.parser')
        offers = soup.select("div[data-name='HeaderDefault']")

        if len(offers) == 0:
            print("_" + "  " + "***")
            return self.cities

        title = offers[0].text
        city = title.lower()[title.lower().find("снять квартиру в ") + len("снять квартиру в "):title.lower().find(
            " на длительный срок")]

        if ("в России" in title or "АрендаСнять" not in title or
                ("области" in city or "крае" in city or "республике" in city or
                 "округе" in city or "россии" in city or
                 "кабардино" in city or "карачаево" in city or
                 "дагестан" in city or "осетии" in city or
                 "ненецком ао" in city or "ямало-ненецком ао" in city or
                 "чукотском ао" in city or "ханты-мансийском ао" in city or
                 "чувашии" in city)
        ):
            print("_" + "  " + str(location_id))
            return self.cities

        morph = pymorphy2.MorphAnalyzer()
        city = morph.parse(city)[0].normal_form.title()
        print(city + " " + str(location_id))

        if city not in self.cities_set:
            self.cities_set.add(city)
            self.cities.append((city, location_id))
            self.save_results()

        return self.cities

    def define_all_cities(self):
        for location_id in range(self.start_location_id, self.end_location_id+1):
            path = f'https://www.cian.ru/cat.php?deal_type=rent&engine_version=2&offer_type=flat&p=1&region={location_id}&type=4'
            response = requests.get(path)
            html = response.text
            self.define_city(html, location_id)
            time.sleep(2)

        self.cities = sorted(self.cities, key=lambda x: x[0])

    def save_results(self):
        cities_result = []
        cities_result.append(ParseCityNames(
            location_name='location_name',
            city_id='city_id',
        ))

        for city_couple in self.cities:
            cities_result.append(ParseCityNames(
                location_name=city_couple[0],
                city_id=city_couple[1],
            ))

        path = f"cities_{self.start_location_id}_{self.end_location_id}.csv"
        with open(path, "w") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            for item in self.cities:
                writer.writerow(item)


if __name__ == '__main__':
    definer = Client(start_location_id=6000, end_location_id=7000)
    definer.define_all_cities()
