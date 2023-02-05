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
