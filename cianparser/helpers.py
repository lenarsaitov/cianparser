import re
import itertools
import urllib.request
import urllib.error
from bs4 import BeautifulSoup
from cianparser.constants import *


def is_available_proxy(url, pip):
    try:
        proxy_handler = urllib.request.ProxyHandler({'http': pip})
        opener = urllib.request.build_opener(proxy_handler)
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        req = urllib.request.Request(url)
        html = urllib.request.urlopen(req)

        try:
            soup = BeautifulSoup(html, 'lxml')
        except:
            soup = BeautifulSoup(html, 'html.parser')

        if soup.text.find("Captcha") > 0:
            return False, True

        return True, False
    except urllib.error.HTTPError as e:
        print('Error code: ', e.code)
        return not e.code, False
    except Exception as detail:
        print("Error:", detail)
        return False, False


def union_dicts(*dicts):
    return dict(itertools.chain.from_iterable(dct.items() for dct in dicts))


def define_rooms_count(description):
    if "1-комн" in description or "Студия" in description:
        rooms_count = 1
    elif "2-комн" in description:
        rooms_count = 2
    elif "3-комн" in description:
        rooms_count = 3
    elif "4-комн" in description:
        rooms_count = 4
    elif "5-комн" in description:
        rooms_count = 5
    else:
        rooms_count = -1

    return rooms_count


def define_id_url(url: str):
    url_path_elements = url.split("/")
    if len(url_path_elements[-1]) > 3:
        return url_path_elements[-1]
    if len(url_path_elements[-2]) > 3:
        return url_path_elements[-2]

    return "-1"


def parse_page_offer(html_offer):
    try:
        soup_offer_page = BeautifulSoup(html_offer, 'lxml')
    except:
        soup_offer_page = BeautifulSoup(html_offer, 'html.parser')

    page_data = {
        "year_of_construction": -1,
        "living_meters": -1,
        "kitchen_meters": -1,
        "floor": -1,
        "floors_count": -1,
        "rooms_count": -1,
        "phone": "",
    }

    offer_page = soup_offer_page.select("div[data-name='ObjectSummaryDescription']")
    if len(offer_page) == 0:
        return page_data

    try:
        text_offer = offer_page[0].text
        if "Кухня" in text_offer:
            kitchen = (text_offer[:text_offer.find("Кухня")])
            page_data["kitchen_meters"] = float(
                re.findall(FLOATS_NUMBERS_REG_EXPRESSION, kitchen.replace(",", "."))[-1])
        else:
            page_data["kitchen_meters"] = -1
    except:
        page_data["kitchen_meters"] = -1

    try:
        text_offer = offer_page[0].text
        if "Жилая" in text_offer:
            lining = (text_offer[:text_offer.find("Жилая")])
            page_data["living_meters"] = float(
                re.findall(FLOATS_NUMBERS_REG_EXPRESSION, lining.replace(",", "."))[-1])
        else:
            page_data["living_meters"] = -1
    except:
        page_data["living_meters"] = -1

    try:
        contact_data = soup_offer_page.select("div[data-name='OfferContactsAside']")[0].text
        if "+7" in contact_data:
            page_data["phone"] = (contact_data[contact_data.find("+7"):contact_data.find("+7") + 16]). \
                replace(" ", ""). \
                replace("-", "")
    except:
        pass

    try:
        text_offer = offer_page[0].text
        if "Этаж" in text_offer and "из" in text_offer:
            floor_data = (text_offer[:text_offer.find("Этаж")].split("Этаж")[-1])
            page_data["floors_count"] = int(re.findall(r'\d+', floor_data.replace(",", "."))[-1])
            page_data["floor"] = int(re.findall(r'\d+', floor_data.replace(",", "."))[-2])
        else:
            page_data["floors_count"] = -1
            page_data["floor"] = -1
    except:
        page_data["floors_count"] = -1
        page_data["floor"] = -1

    try:
        offer_page = soup_offer_page.select("div[data-name='OfferTitle']")
        page_data["rooms_count"] = define_rooms_count(offer_page[0].text)
    except:
        page_data["rooms_count"] = -1

    build_data = soup_offer_page.select("div[data-name='BtiHouseData']")
    if len(build_data) != 0:
        build_data = build_data[0].text
        year_str = build_data[build_data.find("Год постройки") + 13: build_data.find("Год постройки") + 17]
        ints = re.findall(r'\d+', year_str)
        if len(ints) != 0:
            page_data["year_of_construction"] = int(ints[0])
            return page_data

    offer_page = soup_offer_page.select("div[data-name='Parent']")
    try:
        text_offer = offer_page[0].text
        if "сдача в" in text_offer:
            ints = re.findall(r'\d+', text_offer.split("сдача в")[1])
            if len(ints) != 0:
                for number in ints:
                    if int(number) > 1000:
                        page_data["year_of_construction"] = int(number)
                        return page_data
    except:
        pass

    try:
        text_offer = offer_page[0].text
        if "сдан в" in text_offer:
            ints = re.findall(r'\d+', text_offer.split("сдан в")[1])
            if len(ints) != 0:
                for number in ints:
                    if int(number) > 1000:
                        page_data["year_of_construction"] = int(number)
                        return page_data
    except:
        pass

    return page_data


def parse_page_offer_json(html_offer):
    try:
        soup_offer_page = BeautifulSoup(html_offer, 'lxml')
    except:
        soup_offer_page = BeautifulSoup(html_offer, 'html.parser')

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

    spans = soup_offer_page.select("span")

    for index, span in enumerate(spans):
        if "Год постройки" in span and len(spans[index + 1].text) < 5:
            page_data["year_of_construction"] = spans[index + 1].text

        if "Тип жилья" == span.text:
            page_data["object_type"] = spans[index + 1].text

        if "Тип дома" == span.text:
            page_data["house_material_type"] = spans[index + 1].text

        if "Отопление" == span.text:
            page_data["heating_type"] = spans[index + 1].text

        if "Отделка" == span.text:
            page_data["finish_type"] = spans[index + 1].text

    if page_data["year_of_construction"] == -1:
        p_tags = soup_offer_page.select("p")

        for index, p_tag in enumerate(p_tags):
            if "Год постройки" in p_tag:
                page_data["year_of_construction"] = p_tags[index + 1].text

    if page_data["year_of_construction"] == -1:
        for index, span in enumerate(spans):
            if "Год сдачи" in span:
                page_data["year_of_construction"] = spans[index + 1].text

    for index, span in enumerate(spans):
        if "Площадь кухни" in span:
            page_data["kitchen_meters"] = spans[index + 1].text
            floats = re.findall(FLOATS_NUMBERS_REG_EXPRESSION, page_data["kitchen_meters"])
            if len(floats) == 0:
                page_data["kitchen_meters"] = -1
            else:
                page_data["kitchen_meters"] = float(floats[0])

    for index, span in enumerate(spans):
        if "Жилая площадь" in span:
            page_data["living_meters"] = spans[index + 1].text
            floats = re.findall(FLOATS_NUMBERS_REG_EXPRESSION, page_data["living_meters"])
            if len(floats) == 0:
                page_data["living_meters"] = -1
            else:
                page_data["living_meters"] = float(floats[0])

    for index, span in enumerate(spans):
        if "Этаж" in span:
            text_value = spans[index + 1].text
            ints = re.findall(r'\d+', text_value)
            if len(ints) != 2:
                page_data["floor"] = -1
                page_data["floors_count"] = -1
            else:
                page_data["floor"] = int(ints[0])
                page_data["floors_count"] = int(ints[1])

    if "+7" in html_offer:
        page_data["phone"] = html_offer[html_offer.find("+7"): html_offer.find("+7") + 16].split('"')[0]. \
            replace(" ", ""). \
            replace("-", "")

    return page_data


def define_author(block):
    spans = block.select("div")[0].select("span")

    author_data = {
        "author": "",
        "author_type": "",
    }

    for index, span in enumerate(spans):
        if "Агентство недвижимости" in span:
            author_data["author"] = spans[index + 1].text.replace(",", ".").strip()
            author_data["author_type"] = "real_estate_agent"
            return author_data

    for index, span in enumerate(spans):
        if "Собственник" in span:
            author_data["author"] = spans[index + 1].text
            author_data["author_type"] = "homeowner"
            return author_data

    for index, span in enumerate(spans):
        if "Риелтор" in span:
            author_data["author"] = spans[index + 1].text
            author_data["author_type"] = "realtor"
            return author_data

    for index, span in enumerate(spans):
        if "Ук・оф.Представитель" in span:
            author_data["author"] = spans[index + 1].text
            author_data["author_type"] = "official_representative"
            return author_data

    for index, span in enumerate(spans):
        if "Представитель застройщика" in span:
            author_data["author"] = spans[index + 1].text
            author_data["author_type"] = "representative_developer"
            return author_data

    for index, span in enumerate(spans):
        if "Застройщик" in span:
            author_data["author"] = spans[index + 1].text
            author_data["author_type"] = "developer"
            return author_data

    for index, span in enumerate(spans):
        if "ID" in span.text:
            author_data["author"] = span.text
            author_data["author_type"] = "unknown"
            return author_data

    return author_data


def define_location_data(block, is_sale):
    elements = block.select("div[data-name='LinkArea']")[0]. \
        select("div[data-name='GeneralInfoSectionRowComponent']")

    location_data = dict()
    location_data["district"] = ""
    location_data["street"] = ""
    location_data["house_number"] = ""
    location_data["underground"] = ""

    if is_sale:
        location_data["residential_complex"] = ""

    for index, element in enumerate(elements):
        if ("ЖК" in element.text) and ("«" in element.text) and ("»" in element.text):
            location_data["residential_complex"] = element.text.split("«")[1].split("»")[0]

        if "р-н" in element.text and len(element.text) < 250:
            address_elements = element.text.split(",")
            if len(address_elements) < 2:
                continue

            if "ЖК" in address_elements[0] and "«" in address_elements[0] and "»" in address_elements[0]:
                location_data["residential_complex"] = address_elements[0].split("«")[1].split("»")[0]

            if ", м. " in element.text:
                location_data["underground"] = element.text.split(", м. ")[1]
                if "," in location_data["underground"]:
                    location_data["underground"] = location_data["underground"].split(",")[0]

            if (any(chr.isdigit() for chr in address_elements[-1]) and "жк" not in address_elements[-1].lower() and
                not any(street_type in address_elements[-1].lower() for street_type in STREET_TYPES)) and len(
                address_elements[-1]) < 10:
                location_data["house_number"] = address_elements[-1].strip()

            for ind, elem in enumerate(address_elements):
                if "р-н" in elem:
                    district = elem.replace("р-н", "").strip()

                    location_data["district"] = district

                    if "ЖК" in address_elements[-1]:
                        location_data["residential_complex"] = address_elements[-1].strip()

                    if "ЖК" in address_elements[-2]:
                        location_data["residential_complex"] = address_elements[-2].strip()

                    for street_type in STREET_TYPES:
                        if street_type in address_elements[-1]:
                            location_data["street"] = address_elements[-1].strip()
                            if street_type == "улица":
                                location_data["street"] = location_data["street"].replace("улица", "")
                            return location_data

                        if street_type in address_elements[-2]:
                            location_data["street"] = address_elements[-2].strip()
                            if street_type == "улица":
                                location_data["street"] = location_data["street"].replace("улица", "")

                            return location_data

                    for k, after_district_address_element in enumerate(address_elements[ind + 1:]):
                        if len(list(set(after_district_address_element.split(" ")).intersection(
                                NOT_STREET_ADDRESS_ELEMENTS))) != 0:
                            continue

                        if len(after_district_address_element.strip().replace(" ", "")) < 4:
                            continue

                        location_data["street"] = after_district_address_element.strip()

                        return location_data

            return location_data

    if location_data["district"] == "":
        for index, element in enumerate(elements):
            if ", м. " in element.text and len(element.text) < 250:
                location_data["underground"] = element.text.split(", м. ")[1]
                if "," in location_data["underground"]:
                    location_data["underground"] = location_data["underground"].split(",")[0]

                address_elements = element.text.split(",")

                if len(address_elements) < 2:
                    continue

                if "ЖК" in address_elements[-1]:
                    location_data["residential_complex"] = address_elements[-1].strip()

                if "ЖК" in address_elements[-2]:
                    location_data["residential_complex"] = address_elements[-2].strip()

                if (any(chr.isdigit() for chr in address_elements[-1]) and "жк" not in address_elements[
                    -1].lower() and
                    not any(
                        street_type in address_elements[-1].lower() for street_type in STREET_TYPES)) and len(
                    address_elements[-1]) < 10:
                    location_data["house_number"] = address_elements[-1].strip()

                for street_type in STREET_TYPES:
                    if street_type in address_elements[-1]:
                        location_data["street"] = address_elements[-1].strip()
                        if street_type == "улица":
                            location_data["street"] = location_data["street"].replace("улица", "")
                        return location_data

                    if street_type in address_elements[-2]:
                        location_data["street"] = address_elements[-2].strip()
                        if street_type == "улица":
                            location_data["street"] = location_data["street"].replace("улица", "")
                        return location_data

            for street_type in STREET_TYPES:
                if (", " + street_type + " " in element.text) or (" " + street_type + ", " in element.text):
                    address_elements = element.text.split(",")

                    if len(address_elements) < 3:
                        continue

                    if (any(chr.isdigit() for chr in address_elements[-1]) and "жк" not in address_elements[
                        -1].lower() and
                        not any(
                            street_type in address_elements[-1].lower() for street_type in STREET_TYPES)) and len(
                        address_elements[-1]) < 10:
                        location_data["house_number"] = address_elements[-1].strip()

                    if street_type in address_elements[-1]:
                        location_data["street"] = address_elements[-1].strip()
                        if street_type == "улица":
                            location_data["street"] = location_data["street"].replace("улица", "")

                        location_data["district"] = address_elements[-2].strip()

                        return location_data

                    if street_type in address_elements[-2]:
                        location_data["street"] = address_elements[-2].strip()
                        if street_type == "улица":
                            location_data["street"] = location_data["street"].replace("улица", "")

                        location_data["district"] = address_elements[-3].strip()

                        return location_data

    return location_data


def define_price_data(block):
    elements = block.select("div[data-name='LinkArea']")[0]. \
        select("span[data-mark='MainPrice']")

    price_data = {
        "price_per_month": -1,
        "commissions": 0,
    }

    for element in elements:
        if "₽/мес" in element.text:
            price_description = element.text
            price_data["price_per_month"] = int(
                "".join(price_description[:price_description.find("₽/мес") - 1].split()))

            if "%" in price_description:
                price_data["commissions"] = int(
                    price_description[price_description.find("%") - 2:price_description.find("%")].replace(" ", ""))

            return price_data

        if "₽" in element.text and "млн" not in element.text:
            price_description = element.text
            price_data["price"] = int("".join(price_description[:price_description.find("₽") - 1].split()))

            return price_data

    return price_data


def define_specification_data(block):
    specification_data = dict()
    specification_data["floor"] = -1
    specification_data["floors_count"] = -1
    specification_data["rooms_count"] = -1
    specification_data["total_meters"] = -1

    title = block.select("div[data-name='LinkArea']")[0].select("div[data-name='GeneralInfoSectionRowComponent']")[
        0].text

    common_properties = block.select("div[data-name='LinkArea']")[0]. \
        select("div[data-name='GeneralInfoSectionRowComponent']")[0].text

    if common_properties.find("м²") is not None:
        total_meters = title[: common_properties.find("м²")].replace(",", ".")
        if len(re.findall(FLOATS_NUMBERS_REG_EXPRESSION, total_meters)) != 0:
            specification_data["total_meters"] = float(
                re.findall(FLOATS_NUMBERS_REG_EXPRESSION, total_meters)[-1].replace(" ", "").replace("-", ""))

    if "этаж" in common_properties:
        floor_per = common_properties[common_properties.rfind("этаж") - 7: common_properties.rfind("этаж")]
        floor_properties = floor_per.split("/")

        if len(floor_properties) == 2:
            ints = re.findall(r'\d+', floor_properties[0])
            if len(ints) != 0:
                specification_data["floor"] = int(ints[-1])

            ints = re.findall(r'\d+', floor_properties[1])
            if len(ints) != 0:
                specification_data["floors_count"] = int(ints[-1])

    specification_data["rooms_count"] = define_rooms_count(common_properties)

    return specification_data
