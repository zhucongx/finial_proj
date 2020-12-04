from bs4 import BeautifulSoup
import requests
import json
import re
import secrets  # file that contains your API key
import sqlite3

CACHE_FILE_NAME = 'cache.json'
CACHE_DICT = {}

api_key = secrets.API_KEY


def save_cache(cache):
    """ Saves cache to disk
    Parameters
    ----------
    cache: dict
        The dictionary to save
    Returns
    -------
    None
    """
    cache_handler = open(CACHE_FILE_NAME, 'w')
    cache_handler.write(json.dumps(cache))
    cache_handler.close()


def load_cache():
    """ Opens the cache file from disk. If the cache file
    doesn't exist, creates a empty dict
    Parameters
    ----------
    None
    Returns
    -------
    Cache: dict
    """
    try:
        cache_handler = open(CACHE_FILE_NAME, 'r')
        content = cache_handler.read()
        cache = json.loads(content)
        cache_handler.close()
    except:
        cache = {}
    return cache


def make_request_api(baseurl, params):
    """Make a request to the Web API using the baseurl and params
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dictionary
        A dictionary of param:value pairs
    Returns
    -------
    dict
        the data returned from making the request in the form of
        a dictionary
    """
    return requests.get(baseurl, params).json()


def construct_unique_key(baseurl, params):
    """ constructs a key that is guaranteed to uniquely and
    repeatably identify an API request by its baseurl and params
    AUTOGRADER NOTES: To correctly test this using the autograder, use an underscore ("_")
    to join your baseurl with the params and all the key-value pairs from params
    E.g., baseurl_key1_value1
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dict
        A dictionary of param:value pairs
    Returns
    -------
    string
        the unique key as a string
    """
    param_strings = []
    connector = '_'
    for k in params.keys():
        param_strings.append(f'{k}_{params[k]}')
    param_strings.sort()
    unique_key = baseurl + connector + connector.join(param_strings)
    return unique_key


def make_request_api_after_check_cache(baseurl, params):
    """Check the cache for a saved result for this baseurl+params:values
    combo. If the result is found, return it. Otherwise send a new
    request, save it, then return it.
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dict
        The params to search for
    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    """
    unique_key = construct_unique_key(baseurl, params)
    if unique_key in CACHE_DICT.keys():
        print("Using Cache")
    else:
        print("Fetching")
        CACHE_DICT[unique_key] = make_request_api(baseurl, params)
        save_cache(CACHE_DICT)

    return CACHE_DICT[unique_key]


def make_url_after_check_cache(url, cache):
    """Check the cache for the url. If there is cache, returns it,
    otherwise make a new request
    Parameters
    ----------
    url: string
        The URL for the html
    cache: dict
        The cache with saved data
    Returns
    -------
    str
        the results of the query as a dictionary loaded from cache
    """
    if url in (cache.keys()):
        print("Using cache")
    else:
        print("Fetching")
        response = requests.get(url)
        cache[url] = response.text
        save_cache(cache)

    return cache[url]


class City(object):
    def __init__(self, rank, name, state, description):
        self.rank = rank
        self.name = name
        self.state = state
        self.info = description

    def get_variables_tuple(self):
        return self.rank, self.name, self.state, self.info


def build_city_list():
    """ Make a dictionary that maps state name to state page url from "https://www.nps.gov"
    Parameters
    ----------
    None
    Returns
    -------
    list
        key is a state name and value is the url
    """
    city_rank_url = 'https://www.businessinsider.com/us-news-best-places-to-live-in-america-2016-3'
    response_text = make_url_after_check_cache(city_rank_url, CACHE_DICT)
    soup = BeautifulSoup(response_text, 'html.parser')
    found_list = soup.find_all(class_="slide-layout clearfix")
    city_list = []
    for city in found_list:
        title = city.find("h2", class_="slide-title-text").text
        first_split = title.split('.')
        second_split = ''.join(first_split[1:]).split(',')
        city = City(first_split[0].strip(),
                    second_split[0].strip(),
                    second_split[-1].strip(),
                    city.find('p').text)
        city_list.append(city)
    return city_list


def save_to_cities_table(city_list):
    try:
        conn = sqlite3.connect("final_project_db.sqlite")
        cur = conn.cursor()
        cur.execute('DROP TABLE IF EXISTS "Cities";')
        conn.commit()
        cur.execute('''
            CREATE TABLE "Cities" (
                "Rank"  INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
                "City"  TEXT NOT NULL,
                "State" TEXT NOT NULL,
                "Info"  TEXT NOT NULL
            );
        ''')
        add_city = "INSERT INTO Cities VALUES (?, ?, ?, ?)"
        for city in city_list:
            cur.execute(add_city, city.get_variables_tuple())
        conn.commit()
    except:
        return None


class Location(object):
    def __init__(self, name=None, city=None, address=None, categories=None, rating=None, price=None, phone=None):
        self.name = name
        self.city = city
        conn = sqlite3.connect("final_project_db.sqlite")
        cur = conn.cursor()
        query = f'SELECT Rank FROM Cities WHERE Cities.City= "{self.city}"'
        result = cur.execute(query).fetchall()
        try:
            self.city_id = result[0][0]
        except:
            print("This place is not in the city")
            self.city_id = -1
        self.address = address
        self.categories = categories
        self.rating = rating
        self.price = price
        self.phone = phone

    def get_variables_tuple(self):
        return self.name, self.city, self.city_id, self.address, self.categories, self.rating, self.price, self.phone

    def save_to_locations_table(self):
        conn = sqlite3.connect("final_project_db.sqlite")
        cur = conn.cursor()
        cur.execute('''
                    CREATE TABLE IF NOT EXISTS "Locations" (
                        "Id" INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
                        "Name"  TEXT NOT NULL,
                        "City" TEXT NOT NULL,
                        "CityId" INTEGER NOT NULL,
                        "Address" TEXT NOT NULL,
                        "Categories" TEXT NOT NULL,
                        "Rating" REAL,
                        "Price" TEXT NOT NULL,
                        "Phone" TEXT NOT NULL,
                        FOREIGN KEY (CityId) REFERENCES Cities (Id)
                    );
                ''')
        add_business = "INSERT INTO Businesses VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?)"
        cur.execute(add_business, self.get_variables_tuple())

        conn.commit()


if __name__ == "__main__":
    load_cache()
    save_to_cities_table(build_city_list())
    # print(api_key)
