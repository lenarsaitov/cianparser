from cianparser.rentsparser import ParserRentOffers
from cianparser.constants import *

offer_types = {"rent_long", "rent_short", "sale"}
offer_not_implemented_yet = {"rent_short", "sale"}

accommodation_types = {"flat", "room", "house", "house-part", "townhouse"}
accommodation_not_implemented_yet = {"room", "house", "house-part", "townhouse"}


def list_cities():
    return CITIES


def parse(offer, accommodation, location, rooms="all", start_page=1, end_page=100):
    """
    Parse information from cian website
    Examples:
        >>> data = cianparser.parse(offer="rent_long", accommodation="flat", location="Казань", rooms=1, start_page=1, end_page=1)
        >>> data = cianparser.parse(offer="rent_short", accommodation="flat", location="Москва", rooms=(1,3,"studio"))
        >>> data = cianparser.parse(offer="sale", accommodation="house", location="Санкт-Петербург", rooms="all")
    :param str offer: type of offer, e.g. "rent_long", "rent_short", "sale"
    :param str accommodation: type of accommodation, e.g. "flat", "room", "house", "house-part", "townhouse"
    :param str location: location. e.g. "Казань", for see all correct values use cianparser.list_cities()
    :param rooms: how many rooms in accommodation, default "all". Example 1, (1,3, "studio"), "studio, "all"
    :param start_page: the page from which the parser starts, default 1
    :param end_page: the page from which the parser ends, default 100
    """

    if offer not in offer_types:
        raise ValueError(f'You entered offer={offer}, which is not valid value. '
                         f'Try entering one of these values: "rent_long", "rent_short", "sale".')

    if accommodation not in accommodation_types:
        raise ValueError(f'You entered accommodation={accommodation}, which is not valid value. '
                         f'Try entering one of these values: "flat", "room", "house", "house-part", "townhouse".')

    if type(rooms) is tuple:
        for count_of_room in rooms:
            print(count_of_room)
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

    finded = False
    for city in CITIES:
        if city[0] == location:
            finded = True
            location_id = city[1]

    if not finded:
        raise ValueError(f'You entered {location}, which is not exists in base.'
                         f' See all correct values of location in cianparser.list_cities()')

    if offer in offer_not_implemented_yet or accommodation in accommodation_not_implemented_yet:
        print("Sorry. This functionality has not yet been implemented, but it is planned...")
        return []
    else:
        parser = ParserRentOffers(type_offer=offer, type_accommodation=accommodation, location_id=location_id, rooms=rooms, start_page=start_page, end_page=end_page)
        parser.run()
        print('\n')

        return parser.get_results()


