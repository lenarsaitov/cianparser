import cloudscraper
import time

from cianparser.constants import CITIES, METRO_STATIONS, DEAL_TYPES, OBJECT_SUBURBAN_TYPES
from cianparser.url_builder import URLBuilder
from cianparser.proxy_pool import ProxyPool
from cianparser.flat.list import FlatListPageParser
from cianparser.suburban.list import SuburbanListPageParser
from cianparser.newobject.list import NewObjectListParser


def list_locations():
    return CITIES


def list_metro_stations():
    return METRO_STATIONS


class CianParser:
    def __init__(self, location: str, proxies=None):
        """
        Initialize the Cian website parser
        Examples:
            >>> moscow_parser = cianparser.CianParser(location="Москва")
        :param str location: location. e.g. "Москва", for see all correct values use cianparser.list_locations()
        :param proxies: proxies for executing requests (https scheme), default None
        """

        location_id = __validation_init__(location)

        self.__parser__ = None
        self.__session__ = cloudscraper.create_scraper()
        self.__session__.headers = {'Accept-Language': 'en'}
        self.__proxy_pool__ = ProxyPool(proxies=proxies)
        self.__location_name__ = location
        self.__location_id__ = location_id

    def __set_proxy__(self, url_list):
        if self.__proxy_pool__.is_empty():
            return
        available_proxy = self.__proxy_pool__.get_available_proxy(url_list)
        if available_proxy is not None:
            self.__session__.proxies = {"https": available_proxy}

    def __load_list_page__(self, url_list_format, page_number, attempt_number_exception):
        url_list = url_list_format.format(page_number)
        self.__set_proxy__(url_list)

        if page_number == self.__parser__.start_page and attempt_number_exception == 0:
            print(f"The page from which the collection of information begins: \n {url_list}")

        res = self.__session__.get(url=url_list)
        if res.status_code == 429:
            time.sleep(10)
        res.raise_for_status()

        return res.text

    def __run__(self, url_list_format: str):
        print(f"\n{' ' * 30}Preparing to collect information from pages..")

        if self.__parser__.with_saving_csv:
            print(f"The absolute path to the file: \n{self.__parser__.file_path} \n")

        page_number = self.__parser__.start_page - 1
        end_all_parsing = False
        while page_number < self.__parser__.end_page and not end_all_parsing:
            page_parsed = False
            page_number += 1
            attempt_number_exception = 0

            while attempt_number_exception < 3 and not page_parsed:
                try:
                    (page_parsed, attempt_number, end_all_parsing) = self.__parser__.parse_list_offers_page(
                        html=self.__load_list_page__(url_list_format=url_list_format, page_number=page_number, attempt_number_exception=attempt_number_exception),
                        page_number=page_number,
                        count_of_pages=self.__parser__.end_page + 1 - self.__parser__.start_page,
                        attempt_number=attempt_number_exception)

                except Exception as e:
                    attempt_number_exception += 1
                    if attempt_number_exception < 3:
                        continue
                    print(f"\n\nException: {e}")
                    print(f"The collection of information from the pages with ending parse on {page_number} page...\n")
                    break

        print(f"\n\nThe collection of information from the pages with list of offers is completed")
        print(f"Total number of parsed offers: {self.__parser__.count_parsed_offers}. ", end="\n")

    def get_flats(self, deal_type: str, rooms, with_saving_csv=False, with_extra_data=False, additional_settings=None):
        """
        Parse information of flats from cian website
        Examples:
            >>> moscow_parser = cianparser.CianParser(location="Москва")
            >>> data = moscow_parser.get_flats(deal_type="rent_long", rooms=1)
            >>> data = moscow_parser.get_flats(deal_type="rent_short", rooms=(1,3,"studio"), with_saving_csv=True)
            >>> data = moscow_parser.get_flats(deal_type="sale", additional_settings={"start_page": 1, "end_page": 1, "sort_by":"price_from_min_to_max"})
        :param deal_type: type of deal, e.g. "rent_long", "rent_short", "sale"
        :param rooms: how many rooms in accommodation, default "all". Example 1, (1,3, "studio"), "studio, "all"
        :param with_saving_csv: is it necessary to save data in csv, default False
        :param with_extra_data:  is it necessary to collect additional data (but with increasing time duration), default False
        :param additional_settings:  additional settings such as min_price, sort_by and others, default None
        """

        __validation_get_flats__(deal_type, rooms)
        deal_type, rent_period_type = __define_deal_type__(deal_type)
        self.__parser__ = FlatListPageParser(
            session=self.__session__,
            accommodation_type="flat",
            deal_type=deal_type,
            rent_period_type=rent_period_type,
            location_name=self.__location_name__,
            with_saving_csv=with_saving_csv,
            with_extra_data=with_extra_data,
            additional_settings=additional_settings,
        )
        self.__run__(
            __build_url_list__(location_id=self.__location_id__, deal_type=deal_type, accommodation_type="flat",
                               rooms=rooms, rent_period_type=rent_period_type,
                               additional_settings=additional_settings))
        return self.__parser__.result

    def get_suburban(self, suburban_type: str, deal_type: str, with_saving_csv=False, with_extra_data=False, additional_settings=None):
        """
        Parse information of suburbans from cian website
        Examples:
            >>> moscow_parser = cianparser.CianParser(location="Москва")
            >>> data = moscow_parser.get_suburbans(suburban_type="house",deal_type="rent_long")
            >>> data = moscow_parser.get_suburbans(suburban_type="house",deal_type="rent_short", with_saving_csv=True)
            >>> data = moscow_parser.get_suburbans(suburban_type="townhouse",deal_type="sale", additional_settings={"start_page": 1, "end_page": 1, "sort_by":"price_from_min_to_max"})
        :param suburban_type: type of suburban building, e.g. "house", "house-part", "land-plot", "townhouse"
        :param deal_type: type of deal, e.g. "rent_long", "rent_short", "sale"
        :param with_saving_csv: is it necessary to save data in csv, default False
        :param with_extra_data:  is it necessary to collect additional data (but with increasing time duration), default False
        :param additional_settings:  additional settings such as min_price, sort_by and others, default None
        """

        __validation_get_suburban__(suburban_type=suburban_type, deal_type=deal_type)
        deal_type, rent_period_type = __define_deal_type__(deal_type)
        self.__parser__ = SuburbanListPageParser(
            session=self.__session__,
            accommodation_type="suburban",
            deal_type=deal_type,
            rent_period_type=rent_period_type,
            location_name=self.__location_name__,
            with_saving_csv=with_saving_csv,
            with_extra_data=with_extra_data,
            additional_settings=additional_settings,
            object_type=suburban_type,
        )
        self.__run__(
            __build_url_list__(location_id=self.__location_id__, deal_type=deal_type, accommodation_type="suburban",
                               rooms=None, rent_period_type=rent_period_type, suburban_type=suburban_type,
                               additional_settings=additional_settings))
        return self.__parser__.result

    def get_newobjects(self, with_saving_csv=False):
        """
        Parse information of newobjects from cian website
        Examples:
            >>> moscow_parser = cianparser.CianParser(location="Москва")
            >>> data = moscow_parser.get_newobjects(with_saving_csv=True)
        :param with_saving_csv: is it necessary to save data in csv, default False
        """

        self.__parser__ = NewObjectListParser(
            session=self.__session__,
            location_name=self.__location_name__,
            with_saving_csv=with_saving_csv,
        )
        self.__run__(
            __build_url_list__(location_id=self.__location_id__, deal_type="sale", accommodation_type="newobject"))
        return self.__parser__.result


def __validation_init__(location):
    location_id = None
    for location_info in list_locations():
        if location_info[0] == location:
            location_id = location_info[1]

    if location_id is None:
        ValueError(f'You entered {location}, which is not exists in base.'
                   f' See all available values of location in cianparser.list_locations()')

    return location_id


def __validation_get_flats__(deal_type, rooms):
    if deal_type not in DEAL_TYPES:
        raise ValueError(f'You entered deal_type={deal_type}, which is not valid value. '
                         f'Try entering one of these values: "rent_long", "sale".')

    if type(rooms) is tuple:
        for count_of_room in rooms:
            if type(count_of_room) is int:
                if count_of_room < 1 or count_of_room > 5:
                    raise ValueError(f'You entered {count_of_room} in {rooms}, which is not valid value. '
                                     f'Try entering one of these values: 1, 2, 3, 4, 5, "studio", "all".')
            elif type(count_of_room) is str:
                if count_of_room != "studio":
                    raise ValueError(f'You entered {count_of_room} in {rooms}, which is not valid value. '
                                     f'Try entering one of these values: 1, 2, 3, 4, 5, "studio", "all".')
            else:
                raise ValueError(f'In tuple "rooms" not valid type of element. '
                                 f'It is correct int and str types. Example (1,3,5, "studio").')
    elif type(rooms) is int:
        if rooms < 1 or rooms > 5:
            raise ValueError(f'You entered rooms={rooms}, which is not valid value. '
                             f'Try entering one of these values: 1, 2, 3, 4, 5, "studio", "all".')
    elif type(rooms) is str:
        if rooms != "studio" and rooms != "all":
            raise ValueError(f'You entered rooms={rooms}, which is not valid value. '
                             f'Try entering one of these values: 1, 2, 3, 4, 5, "studio", "all".')
    else:
        raise ValueError(f'In argument "rooms" not valid type of element. '
                         f'It is correct int, str and tuple types. Example 1, (1,3, "studio"), "studio, "all".')


def __validation_get_suburban__(suburban_type, deal_type):
    if suburban_type not in OBJECT_SUBURBAN_TYPES.keys():
        raise ValueError(f'You entered suburban_type={suburban_type}, which is not valid value. '
                         f'Try entering one of these values: "house", "house-part", "land-plot", "townhouse".')

    if deal_type not in DEAL_TYPES:
        raise ValueError(f'You entered deal_type={deal_type}, which is not valid value. '
                         f'Try entering one of these values: "rent_long", "sale".')


def __build_url_list__(location_id, deal_type, accommodation_type, rooms=None, rent_period_type=None,
                       suburban_type=None, additional_settings=None):
    url_builder = URLBuilder(accommodation_type == "newobject")
    url_builder.add_location(location_id)
    url_builder.add_deal_type(deal_type)
    url_builder.add_accommodation_type(accommodation_type)

    if rooms is not None:
        url_builder.add_room(rooms)

    if rent_period_type is not None:
        url_builder.add_rent_period_type(rent_period_type)

    if suburban_type is not None:
        url_builder.add_object_suburban_type(suburban_type)

    if additional_settings is not None:
        url_builder.add_additional_settings(additional_settings)

    return url_builder.get_url()


def __define_deal_type__(deal_type):
    rent_period_type = None
    if deal_type == "rent_long":
        deal_type, rent_period_type = "rent", 4
    elif deal_type == "rent_short":
        deal_type, rent_period_type = "rent", 2
    return deal_type, rent_period_type
