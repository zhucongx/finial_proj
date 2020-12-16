from bs4 import BeautifulSoup
import requests
import json
import re
import secrets  # file that contains your API key
import sqlite3
import textwrap
import plotly.figure_factory as ff
import plotly.graph_objects as go

CACHE_FILE_NAME = 'cache.json'
CACHE_DICT = {}
DATA_BASE_NAME = 'database.sqlite'
HEADERS = {'Authorization': 'Bearer ' + secrets.API_KEY}


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
    return requests.get(baseurl, params, headers=HEADERS).json()


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
        """
        Parameters
        ----------
        rank: string
            The rank of the city on the website
        name: string
            City name
        state:
            The states of the city
        description: string
            A short introduction
        """
        self.rank = int(rank)
        self.name = name
        self.state = state
        self.description = description

    def get_variables_tuple(self):
        """Gets a tuple with info for database

        Returns
        -------
        tuple
            A tuple with info for database
        """
        return self.rank, self.name, self.state, self.description

    def get_print_str(self):
        """Gets a base info str of the city

        Returns
        -------
        str
            Base info str of the city
        """
        return_str = f'{self.rank}. {self.name}, {self.state}'
        return return_str

    def get_city_info_str(self):
        """Gets the introduction str of the city

        Returns
        -------
        str
            Introduction str of the city
        """
        info_list = textwrap.wrap(self.description)
        return '   ' + '\n   '.join(info_list)


def build_city_list():
    """Builds a list of city class

    Returns
    -------
    list
        The city list
    """
    city_rank_url = 'https://www.businessinsider.com/us-news-best-places-to-live-in-america-2016-3'
    response_text = make_url_after_check_cache(city_rank_url, CACHE_DICT)
    soup = BeautifulSoup(response_text, 'html.parser')
    found_list = soup.find_all(class_="slide-layout clearfix")
    city_list = []
    for city_result in found_list:
        title = city_result.find("h2", class_="slide-title-text").text
        first_split = title.split('.')
        second_split = ''.join(first_split[1:]).split(',')
        city = City(first_split[0].strip(),
                    second_split[0].strip(),
                    second_split[-1].strip(),
                    city_result.find('p').text)
        city_list.append(city)
    return city_list


def save_to_cities_table(in_city_list):
    """Saves the city list to the local database

    Parameters
    ----------
    in_city_list

    Returns
    -------

    """
    try:
        conn = sqlite3.connect(DATA_BASE_NAME)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS "Cities" (
                "Rank"  INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
                "City"  TEXT NOT NULL,
                "State" TEXT NOT NULL,
                "Info"  TEXT NOT NULL
            );
        ''')
        add_city = "INSERT INTO Cities VALUES (?, ?, ?, ?)"
        for city in in_city_list:
            cur.execute(add_city, city.get_variables_tuple())
        conn.commit()
    except:
        return None


def display_city_list(in_city_list):
    """Displays the cities information
    Parameters
    ----------
    in_city_list

    Returns
    -------

    """
    for city in in_city_list:
        print(city.get_print_str())
    print('-' * 80)


class Location(object):
    def __init__(self, name=None, city=None, address=None, categories=None,
                 rating=None, price=None, phone=None):
        """A class to describe a location
        Parameters
        ----------
        name
        city
        address
        categories
        rating
        price
        phone
        """
        self.name = name
        self.city = city
        self.address = address
        self.categories = categories
        self.rating = rating
        self.price = price
        self.phone = phone

    def get_variables_tuple(self, city_id):
        """Gets a tuple for saving to database
        Parameters
        ----------
        city_id

        Returns
        -------
        tuple
        """
        return self.name, self.city, city_id, self.address, self.categories, self.rating, self.price, self.phone

    def get_print_str(self):
        """Gets a string for information showing
        Returns
        -------
        str
        """
        return f'{self.name} | Rating: {self.rating} | Price: {self.price} | Address: {self.address}'


def save_to_locations_table(location_list):
    """Saves the location list to the local database

    Parameters
    ----------
    location_list

    Returns
    -------

    """
    for loc in location_list:
        try:
            conn = sqlite3.connect(DATA_BASE_NAME)
            cur = conn.cursor()
            query = f'SELECT Rank FROM Cities WHERE Cities.City= "{loc.city}"'
            result = cur.execute(query).fetchall()
            conn.close()
            city_id = result[0][0]
            conn.close()

            conn = sqlite3.connect(DATA_BASE_NAME)
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
            add_business = "INSERT INTO Locations VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?)"
            cur.execute(add_business, loc.get_variables_tuple(city_id))
            conn.commit()
        except:
            return None


def get_location_dict_list_from_api(city_name, term='food'):
    """Generates a location list from api with cache checking
    Parameters
    ----------
    city_name
    term

    Returns
    -------
    dict:
        API raw dict
    """
    yelp_url = 'https://api.yelp.com/v3/businesses/search'
    yelp_dict = make_request_api_after_check_cache(yelp_url, {
        'location': city_name,
        'term': term,
        'limit': 50
    })
    return yelp_dict


def try_to_get_str_from_dict(dic, key):
    """ if dic has key, return dic[key], else return "".

    Parameters
    ----------
    dic: dict
    key: Any

    Returns
    -------
    Any
        value of key in the dict
    """
    try:
        return dic[key]
    except:
        return ''


def build_location_list_from_api_result(yelp_dict, city, cat):
    """Builds a list of location class

    Parameters
    ----------
    yelp_dict: dict
    city: string
    cat: string

    Returns
    -------
    list

    """
    location_list = []
    for loc in yelp_dict["businesses"]:
        name = loc['name']
        rating = float(try_to_get_str_from_dict(loc, 'rating'))
        price = try_to_get_str_from_dict(loc, 'price')
        phone = try_to_get_str_from_dict(loc, 'phone')
        address = ''
        if try_to_get_str_from_dict(loc, 'location') != '':
            address = try_to_get_str_from_dict(loc['location'], 'address1')
        if price == '':
            price = 'no price info'
        if rating == '':
            rating = 'no rating info'
        location_list.append(Location(name, city, address, cat, rating, price, phone))
    return location_list


def get_info_from_dataset(props, params=None):
    """Return information from the dataset

    Parameters
    ----------
    props:list Information asking for
    params:dict Information constrained

    Returns
    -------
    list
        A list of asked props
    """
    conn = sqlite3.connect(DATA_BASE_NAME)
    cur = conn.cursor()
    real_props = ""
    for i in range(len(props)):
        real_props += f"b.{props[i]}, "
    real_props = real_props[:-2]
    command = f'SELECT {real_props} FROM Locations as b'
    if params != None:
        keys = list(params.keys())
        for key in keys:
            if keys.index(key) == 0:
                command += f' WHERE {key}="{params[key]}"'
            else:
                command += f' AND {key}="{params[key]}"'
    command += ";"
    result = cur.execute(command).fetchall()
    conn.close()
    return result


def get_unique_database_type_set():
    """Checks the database for existing recording
    Returns
    -------
    set
    """
    try:
        res = set()
        info = get_info_from_dataset(['city', 'categories'])
        for item in info:
            res.add(item[0] + item[1])
        return res
    except:
        return set()


def display_loc_list(in_loc_list):
    """Displays the locations
    Parameters
    ----------
    in_loc_list

    Returns
    -------

    """
    for i, loc in enumerate(in_loc_list):
        print(f'{i + 1}.', loc.get_print_str())
    print('-' * 80)


def input_user_cities_choice_index(upper_range):
    """Asks user for city choice

    Parameters
    ----------
    upper_range

    Returns
    -------
    int
    """
    possible_choice = [str(i) for i in range(1, upper_range + 1)]
    while True:
        cities_choice = input(f'Please enter a city number from 1 to {upper_range} or "exit": ').lower()
        print('-' * 80)
        if cities_choice == "exit":
            exit()
        if cities_choice in possible_choice:
            return int(cities_choice) - 1
        else:
            print('[Error] Wrong command. Try again')


def input_user_categories_choice():
    """Asks user for category choice

    Parameters
    ----------
    upper_range

    Returns
    -------
    str
    """
    categories_list = ['American', 'British', 'Chinese', 'Indian']
    while True:
        categories_choice = input(f'Please choose from the following categories {", ".join(categories_list)} '
                                  'or "back" to choose another city: ').lower()
        print('-' * 80)
        if categories_choice == 'back':
            return categories_choice
        if categories_choice in [cate.lower() for cate in categories_list]:
            return categories_choice
        else:
            print('[Error] Wrong command. Try again')


def input_user_display_choice():
    """Asks user for display method choice

    Parameters
    ----------
    upper_range

    Returns
    -------
    int
    """
    possible_choice = [str(i) for i in range(1, 5)]
    while True:
        print('Data visualization')
        print('1. The highest 3 rating restaurant')
        print('2. Average rating of these restaurants')
        print('3. Rating distribution plot')
        print('4. Price pie chart')
        display_choice = input(f'Please enter a choice number from 1 to 4 or "back" to chose a new category: ').lower()
        print('-' * 80)
        if display_choice == "back":
            return display_choice
        if display_choice in possible_choice:
            return display_choice
        else:
            print('[Error] Wrong command. Try again')


def print_highest_three_rating_restaurants(params):
    """Display method one showing the first three highest rating restaurants
    Parameters
    ----------
    params

    Returns
    -------

    """
    info_list = get_info_from_dataset(['name', 'rating', 'price', 'address'], params)

    info_list.sort(key=lambda sort_loc: float(sort_loc[1]), reverse=True)

    print("The highest 3 rating restaurant in this category:")
    for rest in info_list[:3]:
        print(f'{rest[0]} | Rating: {rest[1]} | Price: {rest[2]} | Address: {rest[3]}')
    print('-' * 80)


def print_average_rating(params):
    """Display method two showing the average rating
    Parameters
    ----------
    params

    Returns
    -------

    """
    info_list = get_info_from_dataset(['rating'], params)
    average = sum(float(loc[0]) for loc in info_list) / len(info_list)
    print(f'The average rating is {average}')
    print('-' * 80)


def plot_rating_distribution(params):
    """Display method three plotting the rating distribution
    Parameters
    ----------
    params

    Returns
    -------

    """
    info_list = get_info_from_dataset(['rating'], params)
    rating_list = [float(loc[0]) for loc in info_list]
    fig = ff.create_distplot([rating_list], ['Rating'], bin_size=0.5)
    print("Plotting")
    print('-' * 80)
    fig.show()


def plot_price_pie_chart(params):
    """Display method three plotting the price pie chart
    Parameters
    ----------
    params

    Returns
    -------

    """
    info_list = get_info_from_dataset(['price'], params)
    price_dict = {}
    for loc in info_list:
        price_dict[loc[0]] = price_dict.get(loc[0], 0) + 1
    labels = []
    values = []
    for key, value in price_dict.items():
        if key[0] == '$':
            key = 'pricing level ' + str(len(key))
        labels.append(key)
        values.append(value)
    print("Plotting")
    print('-' * 80)
    fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
    fig.show()


if __name__ == "__main__":
    CACHE_DICT = load_cache()
    city_list = build_city_list()
    # sort by rank
    city_list.sort(key=lambda city: city.rank)

    save_to_cities_table(city_list)
    city_category_set = get_unique_database_type_set()

    while True:
        display_city_list(city_list)
        city_index = input_user_cities_choice_index(len(city_list))
        query_city = city_list[city_index]
        print(query_city.get_print_str())
        print(query_city.get_city_info_str())
        while True:
            category = input_user_categories_choice()
            if category == 'back':
                break

            loc_list = build_location_list_from_api_result(get_location_dict_list_from_api(query_city.name,
                                                                                           category),
                                                           query_city.name, category)
            if (query_city.name + category) in city_category_set:
                print("Using data from dataset")
            else:
                print("Saving new data")
                save_to_locations_table(loc_list)
                city_category_set.add(query_city.name + category)

            display_loc_list(loc_list)
            parms = {'city': query_city.name, 'categories': category}
            while True:
                display = input_user_display_choice()
                if display == 'back':
                    break
                if display == '1':
                    print_highest_three_rating_restaurants(parms)
                elif display == '2':
                    print_average_rating(parms)
                elif display == '3':
                    plot_rating_distribution(parms)
                elif display == '4':
                    plot_price_pie_chart(parms)

