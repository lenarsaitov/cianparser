import bs4
import re
import time


class FlatPageParser:
    def __init__(self, session, url):
        self.session = session
        self.url = url

    def __load_page__(self):
        res = self.session.get(self.url)
        if res.status_code == 429:
            time.sleep(10)
        res.raise_for_status()
        self.offer_page_html = res.text
        self.offer_page_soup = bs4.BeautifulSoup(self.offer_page_html, 'html.parser')

    def __parse_flat_offer_page_json__(self):
        page_data = {
            "year_of_construction": -1,
            "object_type": -1,
            "house_material_type": -1,
            "heating_type": -1,
            "finish_type": -1,
            "living_meters": -1,
            "kitchen_meters": -1,
            "floor": -1,
            "floors_count": -1,
            "phone": "",
        }

        spans = self.offer_page_soup.select("span")
        for index, span in enumerate(spans):
            if "Тип жилья" == span.text:
                page_data["object_type"] = spans[index + 1].text

            if "Тип дома" == span.text:
                page_data["house_material_type"] = spans[index + 1].text

            if "Отопление" == span.text:
                page_data["heating_type"] = spans[index + 1].text

            if "Отделка" == span.text:
                page_data["finish_type"] = spans[index + 1].text

            if "Площадь кухни" == span.text:
                page_data["kitchen_meters"] = spans[index + 1].text

            if "Жилая площадь" == span.text:
                page_data["living_meters"] = spans[index + 1].text

            if "Год постройки" in span.text:
                page_data["year_of_construction"] = spans[index + 1].text

            if "Год сдачи" in span.text:
                page_data["year_of_construction"] = spans[index + 1].text

            if "Этаж" == span.text:
                ints = re.findall(r'\d+', spans[index + 1].text)
                if len(ints) == 2:
                    page_data["floor"] = int(ints[0])
                    page_data["floors_count"] = int(ints[1])

        if "+7" in self.offer_page_html:
            page_data["phone"] = self.offer_page_html[self.offer_page_html.find("+7"): self.offer_page_html.find("+7") + 16].split('"')[0]. \
                replace(" ", ""). \
                replace("-", "")

        return page_data

    def parse_page(self):
        self.__load_page__()
        return self.__parse_flat_offer_page_json__()
