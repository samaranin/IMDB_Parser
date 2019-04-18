import re
import requests

from bs4 import BeautifulSoup as Bs

# define same headers for all requests
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0",
           "Accept-Language": "en-US,en;q=0"}


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

    @staticmethod
    def concatenate_strings(string_list, separator=", "):
        """
        Concatenates list of words into one string wits words separated with comas
        :param string_list: list of strings
        :param separator: separates words in string
        :return: single string with word separated with comas
        """
        concatenation = ''
        for list_item in string_list:
            concatenation += list_item + separator

        # remove redundant coma in the end
        concatenation = concatenation.strip(', ')
        return concatenation


class Response:
    """
    Helper class for saving and representing responses from server
    """

    def __init__(self, response_status, request_url, request_result):
        """
        :param response_status: HTML response code (200, 400, etc.)
        :param request_url: request destination
        :param request_result: parsed and processed response from server (None for empty object or any error)
        """
        self.response_status = response_status
        self.request_url = request_url
        self.request_result = request_result

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)


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

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)


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

            title_tag = soup.find('h1', attrs={'class': ''})

            if title_tag is not None:
                pass
            else:
                title_tag = soup.find('div', attrs={'class': 'title_wrapper'}).find('h1', attrs={'class': 'long'})

            # get movie title
            title = StringProcessing.remove_text_in_brackets(title_tag.text) if title_tag is not None else ''

            # get movie release year
            year_tag = title_tag.find('a', href=True)
            year = year_tag.text if year_tag is not None else ""

            # get sub info: rating, duration, genre, release_date
            sub_info = soup.find('div', attrs={'class': 'subtext'}).text.split("|")

            # dict of lambda-functions for parsing movie sub info
            # return order: rating, duration, genre, launch_date
            sub_info_parsers = {
                1: lambda sub_info_data: (
                    '',
                    '',
                    StringProcessing.split_words(sub_info_data[0]),
                    ''
                ),
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

            # get imdb rating
            imdb_rating = soup.find('span', attrs={'itemprop': 'ratingValue'})
            imdb_rating = imdb_rating.text.strip() if imdb_rating is not None else ''

            # get summary info
            summary = soup.find('div', attrs={'class': 'plot_summary'})

            # if we do not have summary - make fields empty
            if summary is None:
                director, writers, actors, storyline = '', '', '', ''
            else:
                # get storyline from summary
                storyline = summary.find('div', attrs={'class': 'summary_text'})
                storyline = storyline.text.strip().replace("...\n                    See full summary\xa0", "") \
                    if storyline is not None else ''

                # find all stuff
                stuff = summary.find_all('div', attrs={'class': 'credit_summary_item'})

                def persons_parsers(stuff_object):
                    """
                    Parses staff and creates single line
                    :param stuff_object: parsed stuff data
                    :return: string with stuff name separated with comas
                    """
                    stuff_list = stuff_object.find_all('a', href=True)
                    # create list of persons names
                    # link to person's name contains 'name' part - so we need only it
                    # same thing will be for
                    persons = [
                        stuff_item.text if 'name' in stuff_item['href'] else ''
                        for stuff_item in stuff_list
                        if stuff_list is not None
                    ]
                    stuff_string = StringProcessing.concatenate_strings(persons)
                    stuff_string = stuff_string if stuff_string != 'IMDbPro' else ''
                    return stuff_string

                # get directors from stuff
                director = persons_parsers(stuff[0]) if len(stuff) > 0 else ''

                # get writers from stuff
                writers = persons_parsers(stuff[1]) if len(stuff) > 1 else ''

                # get actors from stuff
                actors = persons_parsers(stuff[2]) if len(stuff) > 2 else ''

            # creating new movie object to return
            movie = Movie(
                name=title,
                year=year,
                rating=rating,
                duration=duration,
                genre=genre,
                launch_date=launch_date,
                image_link=image_link,
                imdb_rating=imdb_rating,
                director=director,
                writers=writers,
                actors=actors,
                storyline=storyline
            )

            # return a Response object with Movie data in
            return Response(request.status_code, movie_link, movie)
        else:
            # or return an empty response
            return Response(request.status_code, movie_link, None)


if __name__ == "__main__":

    search_text = "Avengers"

    imdb_search = IMDBSearch(HEADERS)  # create parser object

    search_result = imdb_search.imdb_movie_search(search_text)  # make search request to IMDB
    search_links = search_result.request_result  # get list of links from response

    if search_links is not None:
        # parsing movie page for every link
        for link in search_links:
            response = imdb_search.parse_movie_data_from_imdb(link)
            print(response.request_result.__dict__)
    else:
        # or show an error
        print("No results found on request \"" + search_result.request_url
              + "\" with status " + search_result.response_status)
