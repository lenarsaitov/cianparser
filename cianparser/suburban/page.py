import time

import bs4


class SuburbanPageParser:
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
            "land_plot":-1,
            "land_plot_status": -1,
            "heating_type": -1,
            "gas_type":-1,
            "water_supply_type":-1,
            "sewage_system":-1,
            "bathroom":-1,
            "living_meters": -1,
            "floors_count": -1,
            "phone": "",
        }

        spans = self.offer_page_soup.select("span")
        for index, span in enumerate(spans):
            if "Материал дома" == span.text:
                page_data["house_material_type"] = spans[index + 1].text

            if "Участок" == span.text:
                page_data["land_plot"] = spans[index + 1].text

            if "Статус участка" == span.text:
                page_data["land_plot_status"] = spans[index + 1].text

            if "Отопление" == span.text:
                page_data["heating_type"] = spans[index + 1].text

            if "Газ" == span.text:
                page_data["gas_type"] = spans[index + 1].text

            if "Водоснабжение" == span.text:
                page_data["water_supply_type"] = spans[index + 1].text

            if "Канализация" == span.text:
                page_data["sewage_system"] = spans[index + 1].text

            if "Санузел" == span.text:
                page_data["bathroom"] = spans[index + 1].text

            if "Площадь кухни" == span.text:
                page_data["kitchen_meters"] = spans[index + 1].text

            if "Общая площадь" == span.text:
                page_data["living_meters"] = spans[index + 1].text

            if "Год постройки" in span.text:
                page_data["year_of_construction"] = spans[index + 1].text

            if "Год сдачи" in span.text:
                page_data["year_of_construction"] = spans[index + 1].text

            if "Этажей в доме" == span.text:
                page_data["floors_count"] = spans[index + 1].text

        if "+7" in self.offer_page_html:
            page_data["phone"] = self.offer_page_html[self.offer_page_html.find("+7"): self.offer_page_html.find("+7") + 16].split('"')[0]. \
                replace(" ", ""). \
                replace("-", "")

        return page_data
