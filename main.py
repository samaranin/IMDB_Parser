import requests
from bs4 import BeautifulSoup as bs
import re


IMDB_LINK = "https://www.imdb.com"

request_url = "https://www.imdb.com/find?ref_=nv_sr_fn&s=tt&ttype=ft&q="
headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0"}


def remove_brackets(string):
    return re.sub(r"[\(\[].*?[\)\]]", "", string.strip()).strip()


def get_tags(subtext, index):
    tags_data = subtext[index].strip().split(",") if subtext[index].strip().split(",") is not None else ""
    return [tag.strip() for tag in tags_data]


def imdb_search(search_parameter, search_url, search_headers):
    session = requests.session()
    request = session.get(search_url + search_parameter, headers=search_headers)

    if request.status_code == 200:
        soup = bs(request.content, 'html.parser')
        found_tds = soup.find_all('td', attrs={'class': 'result_text'})

        search_results = []
        for td in found_tds:
            found_a = td.find('a', href=True)
            search_results.append(found_a['href'])

        parse_movie_data_from_imdb(session, search_results, search_headers)
    else:
        return {"error": request.status_code}


def parse_movie_data_from_imdb(session, links_list, request_headers):
    for link in links_list:
        request = session.get(IMDB_LINK + link, headers=request_headers)

        if request.status_code == 200:
            soup = bs(request.content, 'html.parser')

            # get title
            title_tag = soup.find('h1', attrs={'class': ''})
            title = remove_brackets(title_tag.text)

            # get year
            year_tag = title_tag.find('a', href=True)
            year = year_tag.text if year_tag is not None else ""

            # get sub info
            subtext = soup.find('div', attrs={'class': 'subtext'}).text.split("|")
            number_of_elements = len(subtext)

            if number_of_elements == 4:
                rating = subtext[0].strip()
                duration = subtext[1].strip()
                tags = get_tags(subtext, 2)
                launch_date = remove_brackets(subtext[3])

            elif number_of_elements == 3:
                tags = get_tags(subtext, 1)
                rating = ''
                duration = subtext[0].strip()
                launch_date = remove_brackets(subtext[2])

            else:
                tags = get_tags(subtext, 0)
                rating = ''
                duration = ''
                launch_date = ''

            print(rating + " " + duration + " " + str(tags) + " " + launch_date)

        else:
            return {"error": request.status_code}


print(imdb_search("Bumblebee", request_url, headers))
