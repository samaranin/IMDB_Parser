import re
import requests

from bs4 import BeautifulSoup as Bs

# define same headers for all requests
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0"}


class StringProcessing:
    """
    Helper class for string processing while data parsing
    """

    @staticmethod
    def remove_text_in_brackets(string):
        """
        Remove round brackets and redundant spaces and data between it with regex
        :param string: text with brackets
        :return: text without brackets
        """
        return re.sub(r"[\(\[].*?[\)\]]", "", string.strip()).strip()

    @staticmethod
    def split_words(text):
        """
        Split words separated with comas into list of word and removes redundant spaces
        :param text: string with comas
        :return: list of words
        """
        tags_data = text.strip().split(",") if text.strip().split(",") is not None else ""
        return [tag.strip() for tag in tags_data]


class Response:
    """
    Helper class for saving and representing responses from server
    """

    def __init__(self, response_status, request_url, request_results):
        """
        :param response_status: HTML response code (200, 400, etc.)
        :param request_url: request destination
        :param request_results: parsed and processed response from server (None for empty object or any error)
        """
        self.response_status = response_status
        self.request_url = request_url
        self.request_results = request_results


class Movie:
    """
    Base class for Movie information
    """

    def __init__(self, **kwargs):
        """
        Gets sequence of constructions param=param_value to create movie object
        :param kwargs:name, duration, rating, launch_date, image_link, imdb_rating, director, writers, actors, storyline
        """
        defaults = {
            'name': '',
            'duration': '',
            'rating': '',
            'launch_date': '',
            'image_link': '',
            'genre': '',
            'imdb_rating': '',
            'director': '',
            'writers': '',
            'actors': '',
            'storyline': ''
        }

        for (prop, value) in defaults.items():
            setattr(self, prop, kwargs.get(prop, value))


class IMDBSearch:
    """
    Class for IMDB movies data search and parse
    """

    IMDB_SEARCH_URL = "https://www.imdb.com/find?ref_=nv_sr_fn&s=tt&ttype=ft&q="
    IMDB_LINK = "https://www.imdb.com"

    def __init__(self, search_headers):
        """
        :param search_headers: headers for search session
        """
        self.session = requests.session()  # create new session on search start
        self.search_headers = search_headers  # save same headers for all search session

    def imdb_movie_search(self, search_parameter):
        """
        Base method for movie search on IMDB
        :param search_parameter: search request parameter
        :return: Response object with list of link to movies pages
        """
        request_link = self.IMDB_SEARCH_URL + search_parameter  # generate search link
        request = self.session.get(request_link, headers=self.search_headers)  # make request to server

        # if request is successful
        if request.status_code == 200:
            soup = Bs(request.content, 'html.parser')  # parse page data
            found_tds = soup.find_all('td', attrs={'class': 'result_text'})  # parse data for all search results

            # save all links for movies pages to separate list
            search_results = []
            for td in found_tds:
                found_a = td.find('a', href=True)
                search_results.append(self.IMDB_LINK + found_a['href'])

            # and return response with links list
            return Response(request.status_code, request_link, search_results)
        else:
            # otherwise - return Response with empty data field
            return Response(request.status_code, request_link, None)

    def parse_movie_data_from_imdb(self, movie_link):
        """
        Base method for parsing data from movie page
        :param movie_link: link to movie page
        :return: Response object where stored Movie object and base data about object
        """
        request = self.session.get(movie_link, headers=self.search_headers)  # make request to server for a movie page

        # if request is successful
        if request.status_code == 200:
            soup = Bs(request.content, 'html.parser')  # get page data

            # get movie title
            title_tag = soup.find('h1', attrs={'class': ''})
            title = StringProcessing.remove_text_in_brackets(title_tag.text)

            # get movie release year
            year_tag = title_tag.find('a', href=True)
            year = year_tag.text if year_tag is not None else ""

            # get sub info: rating, duration, genre, release_date
            sub_info = soup.find('div', attrs={'class': 'subtext'}).text.split("|")

            # dict of lambda-functions for parsing movie sub info
            # return order: rating, duration, genre, launch_date
            sub_info_parsers = {
                2: lambda sub_info_data: (
                    '',
                    '',
                    StringProcessing.split_words(sub_info_data[0]),
                    ''
                ),
                3: lambda sub_info_data: (
                    '',
                    sub_info_data[0].strip(),
                    StringProcessing.split_words(sub_info_data[1]),
                    StringProcessing.remove_text_in_brackets(sub_info[2])
                ),
                4: lambda sub_info_data: (
                    sub_info_data[0].strip(),                               # rating
                    sub_info_data[1].strip(),                               # duration
                    StringProcessing.split_words(sub_info_data[2]),         # genre
                    StringProcessing.remove_text_in_brackets(sub_info[3])   # launch_date
                )
            }

            rating, duration, genre, launch_date = sub_info_parsers[len(sub_info)](sub_info)

            # get poster image link
            image_container = soup.find('div', attrs={'class': 'poster'})
            image_link = image_container.find('img')['src'] if image_container is not None else ''

            print(title + " " + year)
            print(rating + " " + duration + " " + str(genre) + " " + launch_date)
            print(image_link)
            print()

            # return a Response object with Movie data in
            return Response(request.status_code, movie_link, Movie())
        else:
            # or return an empty response
            return Response(request.status_code, movie_link, None)


if __name__ == "__main__":

    search_text = "Bumblebee"

    imdb_search = IMDBSearch(HEADERS)  # create parser object

    search_result = imdb_search.imdb_movie_search(search_text)  # make search request to IMDB
    search_links = search_result.request_results  # get list of links from response

    if search_links is not None:
        # parsing movie page for every link
        for link in search_links:
            imdb_search.parse_movie_data_from_imdb(link)
    else:
        # or show an error
        print("No results found on request \"" + search_result.request_url
              + "\" with status " + search_result.response_status)
