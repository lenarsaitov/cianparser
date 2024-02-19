import bs4
import re
import time


class NewObjectPageParser:
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

    def parse_page(self):
        self.__load_page__()

        page_data = {
            "year_of_construction": -1,
            "house_material_type": -1,
            "finish_type": -1,
            "ceiling_height":-1,
            "class": -1,
            "parking_type": -1,
            "floors_from": -1,
            "floors_to": -1,
        }

        spans = self.offer_page_soup.select("span")
        for index, span in enumerate(spans):
            if "Срок сдачи" in span.text:
                page_data["year_of_construction"] = spans[index + 1].text

            if "Тип дома" == span.text:
                page_data["house_material_type"] = spans[index + 1].text

            if "Отделка" == span.text:
                page_data["finish_type"] = spans[index + 1].text

            if "Высота потолков" == span.text:
                page_data["ceiling_height"] = spans[index + 1].text

            if "Класс" == span.text:
                page_data["class"] = spans[index + 1].text

            if "Застройщик" in span.text and "Проектная декларация" in span.text:
                page_data["builder"] = span.text.split(".")[0]

            if "Парковка" == span.text:
                page_data["parking_type"] = spans[index + 1].text

            if "Этажность" == span.text:
                ints = re.findall(r'\d+', spans[index + 1].text)
                if len(ints) == 2:
                    page_data["floors_from"] = int(ints[0])
                    page_data["floors_to"] = int(ints[1])
                if len(ints) == 1:
                    page_data["floors_from"] = int(ints[0])
                    page_data["floors_to"] = int(ints[0])

        return page_data


