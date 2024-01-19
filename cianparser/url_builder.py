from cianparser.constants import *


class URLBuilder:
    def __init__(self, is_newobject):
        self.url = BASE_URL
        self.add_newobject_postfix() if is_newobject else self.add_default_postfix()
        self.url += DEFAULT_PATH

    def add_default_postfix(self):
        self.url += DEFAULT_POSTFIX_PATH

    def add_newobject_postfix(self):
        self.url += NEWOBJECT_POSTFIX_PATH

    def get_url(self):
        return self.url

    def add_accommodation_type(self, accommodation_type):
        self.url += OFFER_TYPE_PATH.format(accommodation_type)
        
    def add_deal_type(self, deal_type):
        self.url += DEAL_TYPE_PATH.format(deal_type)

    def add_location(self, location_id):
        self.url += REGION_PATH.format(location_id)

    def add_room(self, rooms):
        rooms_path = ""
        if type(rooms) is tuple:
            for count_of_room in rooms:
                if type(count_of_room) is int:
                    if 0 < count_of_room < 6:
                        rooms_path += ROOM_PATH.format(count_of_room)
                elif type(count_of_room) is str:
                    if count_of_room == "studio":
                        rooms_path += STUDIO_PATH
        elif type(rooms) is int:
            if 0 < rooms < 6:
                rooms_path += ROOM_PATH.format(rooms)
        elif type(rooms) is str:
            if rooms == "studio":
                rooms_path += STUDIO_PATH
            elif rooms == "all":
                rooms_path = ""

        self.url += rooms_path

    def add_rent_period_type(self, rent_period_type):
        self.url += RENT_PERIOD_TYPE_PATH.format(rent_period_type)

    def add_object_suburban_type(self, object_type):
        self.url += OBJECT_TYPE_PATH.format(OBJECT_SUBURBAN_TYPES[object_type])

    def add_additional_settings(self, additional_settings):
        if "object_type" in additional_settings.keys():
            self.url += OBJECT_TYPE_PATH.format(OBJECT_TYPES[additional_settings["object_type"]])

        if "is_by_homeowner" in additional_settings.keys() and additional_settings["is_by_homeowner"]:
            self.url += IS_ONLY_HOMEOWNER_PATH
        if "min_balconies" in additional_settings.keys():
            self.url += MIN_BALCONIES_PATH.format(additional_settings["min_balconies"])
        if "have_loggia" in additional_settings.keys() and additional_settings["have_loggia"]:
            self.url += HAVE_LOGGIA_PATH

        if "min_house_year" in additional_settings.keys():
            self.url += MIN_HOUSE_YEAR_PATH.format(additional_settings["min_house_year"])
        if "max_house_year" in additional_settings.keys():
            self.url += MAX_HOUSE_YEAR_PATH.format(additional_settings["max_house_year"])

        if "min_price" in additional_settings.keys():
            self.url += MIN_PRICE_PATH.format(additional_settings["min_price"])
        if "max_price" in additional_settings.keys():
            self.url += MAX_PRICE_PATH.format(additional_settings["max_price"])

        if "min_floor" in additional_settings.keys():
            self.url += MIN_FLOOR_PATH.format(additional_settings["min_floor"])
        if "max_floor" in additional_settings.keys():
            self.url += MAX_FLOOR_PATH.format(additional_settings["max_floor"])

        if "min_total_floor" in additional_settings.keys():
            self.url += MIN_TOTAL_FLOOR_PATH.format(additional_settings["min_total_floor"])
        if "max_total_floor" in additional_settings.keys():
            self.url += MAX_TOTAL_FLOOR_PATH.format(additional_settings["max_total_floor"])

        if "house_material_type" in additional_settings.keys():
            self.url += HOUSE_MATERIAL_TYPE_PATH.format(additional_settings["house_material_type"])

        if "metro" in additional_settings.keys():
            if "metro_station" in additional_settings.keys():
                if additional_settings["metro"] in METRO_STATIONS.keys():
                    for metro_station, metro_id in METRO_STATIONS[additional_settings["metro"]]:
                        if additional_settings["metro_station"] == metro_station:
                            self.url += METRO_ID_PATH.format(metro_id)

        if "metro_foot_minute" in additional_settings.keys():
            self.url += METRO_FOOT_MINUTE_PATH.format(additional_settings["metro_foot_minute"])

        if "flat_share" in additional_settings.keys():
            self.url += FLAT_SHARE_PATH.format(additional_settings["flat_share"])

        if "only_flat" in additional_settings.keys():
            if additional_settings["only_flat"]:
                self.url += ONLY_FLAT_PATH.format(1)

        if "only_apartment" in additional_settings.keys():
            if additional_settings["only_apartment"]:
                self.url += APARTMENT_PATH.format(1)

        if "sort_by" in additional_settings.keys():
            if additional_settings["sort_by"] == IS_SORT_BY_PRICE_FROM_MIN_TO_MAX_PATH:
                self.url += SORT_BY_PRICE_FROM_MIN_TO_MAX_PATH
            if additional_settings["sort_by"] == IS_SORT_BY_PRICE_FROM_MAX_TO_MIN_PATH:
                self.url += SORT_BY_PRICE_FROM_MAX_TO_MIN_PATH
            if additional_settings["sort_by"] == IS_SORT_BY_TOTAL_METERS_FROM_MAX_TO_MIN_PATH:
                self.url += SORT_BY_TOTAL_METERS_FROM_MAX_TO_MIN_PATH
            if additional_settings["sort_by"] == IS_SORT_BY_CREATION_DATA_FROM_NEWER_TO_OLDER_PATH:
                self.url += SORT_BY_CREATION_DATA_FROM_NEWER_TO_OLDER_PATH
            if additional_settings["sort_by"] == IS_SORT_BY_CREATION_DATA_FROM_OLDER_TO_NEWER_PATH:
                self.url += SORT_BY_CREATION_DATA_FROM_OLDER_TO_NEWER_PATH
