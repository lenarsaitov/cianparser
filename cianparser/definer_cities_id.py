import requests
from bs4 import BeautifulSoup
import pymorphy2
import collections
import csv
import cloudscraper

ParseCityNames = collections.namedtuple(
    'ParseResults',
    {
        'city_name',
        'city_id',
    }
)


class Client:
    def __init__(self):
        self.session = cloudscraper.create_scraper()
        self.session.headers = {'Accept-Language': 'en'}

        self.cities = []
        self.cities_set = set()

    def define_city(self, html, location):
        soup = BeautifulSoup(html, 'html.parser')
        offers = soup.select("div[data-name='HeaderDefault']")

        title = offers[0].text
        city = title[:title.find('Аренда')].split()[-1]
        if city == "России":
            print(location)
            return self.cities

        morph = pymorphy2.MorphAnalyzer()
        city = morph.parse(city)[0].normal_form.title()
        print(city + " " + str(location))

        if city not in self.cities_set:
            self.cities_set.add(city)
            self.cities.append((city, location))

        return self.cities

    def define_all_cities(self):
        for location in range(4550, 6000):
            path = f'https://www.cian.ru/cat.php?deal_type=rent&engine_version=2&offer_type=flat&p=1&region={location}&type=4'
            response = requests.get(path)
            html = response.text
            self.define_city(html, location)

        self.cities = sorted(self.cities, key=lambda x: x[0])

    def save_results(self):
        cities_result = []
        cities_result.append(ParseCityNames(
            city_name='city_name',
            city_id='city_id',
        ))

        for city_couple in self.cities:
            cities_result.append(ParseCityNames(
                city_name=city_couple[0],
                city_id=city_couple[1],
            ))

        path = "cities_eng.csv"
        with open(path, "w") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            for item in self.cities:
                writer.writerow(item)


if __name__ == '__main__':
    definer = Client()
    definer.define_all_cities()
    definer.save_results()