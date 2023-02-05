from cianparser.constants import *
from cianparser.parser import ParserOffers

offer_types = {"rent_long", "rent_short", "sale"}
deal_types_not_implemented_yet = {"rent_short"}

accommodation_types = {"flat", "room", "house", "house-part", "townhouse"}
accommodation_types_not_implemented_yet = {"room", "house", "house-part", "townhouse"}


def list_cities():
    return CITIES


def parse(deal_type, accommodation_type, location, rooms="all", start_page=1, end_page=100, is_saving_csv=False, is_latin=False, is_express_mode=False, is_by_homeowner=False):
    """
    Parse information from cian website
    Examples:
        >>> data = cianparser.parse(offer="rent_long", accommodation="flat", location="Казань", rooms=1, start_page=1, end_page=1)
        >>> data = cianparser.parse(offer="rent_short", accommodation="flat", location="Москва", rooms=(1,3,"studio"))
        >>> data = cianparser.parse(offer="sale", accommodation="house", location="Санкт-Петербург", rooms="all")
    :param str deal_type: type of deal, e.g. "rent_long", "rent_short", "sale"
    :param str accommodation_type: type of accommodation, e.g. "flat", "room", "house", "house-part", "townhouse"
    :param str location: location. e.g. "Казань", for see all correct values use cianparser.list_cities()
    :param rooms: how many rooms in accommodation, default "all". Example 1, (1,3, "studio"), "studio, "all"
    :param start_page: the page from which the parser starts, default 1
    :param end_page: the page from which the parser ends, default 100
    :param is_saving_csv: is it necessary to save data in csv
    :param is_latin: is it necessary to save data in latin
    :param is_express_mode:  is it necessary to speed up data collection (but without some fields)
    :param is_by_homeowner:  is it necessary to parse only announcements created by homeowner
    """

    if deal_type not in offer_types:
        raise ValueError(f'You entered deal_type={deal_type}, which is not valid value. '
                         f'Try entering one of these values: "rent_long", "rent_short", "sale".')

    if accommodation_type not in accommodation_types:
        raise ValueError(f'You entered accommodation={accommodation_type}, which is not valid value. '
                         f'Try entering one of these values: "flat", "room", "house", "house-part", "townhouse".')

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
                raise TypeError(f'In tuple "rooms" not valid type of element. '
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
        raise TypeError(f'In argument "rooms" not valid type of element. '
                        f'It is correct int, str and tuple types. Example 1, (1,3, "studio"), "studio, "all".')

    location_id = None

    finded = False
    for city in CITIES:
        if city[0] == location:
            finded = True
            location_id = city[1]

    if not finded or location_id is None:
        raise ValueError(f'You entered {location}, which is not exists in base.'
                         f' See all correct values of location in cianparser.list_cities()')

    if deal_type in deal_types_not_implemented_yet or accommodation_type in accommodation_types_not_implemented_yet:
        print("Sorry. This functionality has not yet been implemented, but it is planned...")
        return []
    else:
        parser = ParserOffers(
            deal_type=deal_type,
            accommodation_type=accommodation_type,
            city_name=location,
            location_id=location_id,
            rooms=rooms,
            start_page=start_page,
            end_page=end_page,
            is_saving_csv=is_saving_csv,
            is_latin=is_latin,
            is_express_mode=is_express_mode,
            is_by_homeowner=is_by_homeowner,
        )

        parser.run()
        print("")

        return parser.get_results()


