import urllib.request
import urllib.error
from bs4 import BeautifulSoup


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
