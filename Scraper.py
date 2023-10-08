import json
import logging
import platform
import sys
import time
import traceback
from datetime import datetime

import mysql.connector
from mysql.connector import Error
from selenium import webdriver
from selenium.common import NoSuchElementException, NoSuchAttributeException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.window import WindowTypes
from tqdm import tqdm

import Gigs
import Locations
import Platforms
import References
import Reviews
import Users


class Scraper:
    # Log everything related to Selenium and set LOG Level to INFO / DEBUG / VERBOSE
    logger = logging.getLogger('selenium')
    logger.setLevel(logging.INFO)
    log_path = "selenium.log"
    handler = logging.FileHandler(log_path)
    logger.addHandler(handler)
    logging.getLogger('selenium.webdriver.common').setLevel(logging.DEBUG)
    logger.debug("this is detailed debug information")

    def __init__(self, platform, host, database, user, password):
        self.platform = platform

        # save DB connections in private variables
        # establish DB connection
        self.__host = host
        self.__database = database
        self.__user = user
        self.__password = password
        # connect to DB
        self.__db_connection()

        # create browser session
        self.__setup()

        # get Platform ID from DB
        self.__platform_id = self.__get_platform_id_from_db()

    def __setup(self):
        # start a selenium Browser session for different OS Platforms
        if platform.system().lower() == 'darwin':
            self.service = Service('chromium Driver 114.0.5735.90/chromedriver_mac64/chromedriver')
        elif platform.system().lower() == 'windows':
            self.service = Service('chromium Driver 114.0.5735.90/chromedriver_win32/chromedriver.exe')
        else:
            print("OS platform currently not supported!")

        # make browser look like real browser i.e. give it correct resolution
        self.chrome_options = Options()
        self.chrome_options.add_experimental_option('detach', True)
        self.chrome_options.add_argument("--window-size=1920,1200")

        self.driver = webdriver.Chrome(service=self.service, options=self.chrome_options)

    """ close DB connection and quit browser """

    def teardown(self):
        self.__teardown_db_connection()
        self.driver.quit()

    def __db_connection(self):
        try:
            self.__connection = mysql.connector.connect(
                host=self.__host,
                database=self.__database,
                user=self.__user,
                password=self.__password)
            db_info = self.__connection.get_server_info()
            print("Connected to MySQL Server version ", db_info)
            self.__cursor = self.__connection.cursor()
        except Error as e:
            print("Error while connecting to MySQL", e)

    def __teardown_db_connection(self):
        if self.__connection.is_connected():
            self.__cursor.close()
            self.__connection.close()
            print("MySQL connection is closed")

    def __get_platform_id_from_db(self):
        self.__cursor = self.__connection.cursor()
        self.__cursor.execute(
            "select id from platforms WHERE LOWER(platform_name)=" + "'" + self.platform.__class__.__name__.lower() + "';"
        )
        return self.__cursor.fetchone()[0]

    """ Helper function to remove specific element from webdriver"""

    def remove_element_from_driver(self, element_to_remove):
        try:
            self.driver.execute_script('''
               var l = document.getElementsByClassName("''' + element_to_remove + '''")[0];
               l.parentNode.removeChild(l);
            ''')
        except:
            pass

    def login_on_platform(self):
        self.driver.get(self.platform.loginpage)
        self.driver.find_element(By.ID, self.platform.login_username_class_id).send_keys(self.platform.get_login()[0])

        # for Babysists include pause for Captcha entry by user and for additional button click
        if isinstance(self.platform, Platforms.Babysits):
            self.driver.find_element(By.XPATH, self.platform.login_button_name).click()
            time.sleep(1)
            self.driver.find_elements(By.ID, self.platform.login_password_class_id)[1].send_keys(
                self.platform.get_login()[1])
            self.driver.find_element(By.CLASS_NAME, self.platform.second_login_button_name).submit()
            # wait a minute for captcha entry
            time.sleep(60)
            print("Please fill out the captcha in the Browser")

        else:
            self.driver.find_element(By.ID, self.platform.login_password_class_id).send_keys(
                self.platform.get_login()[1])
            self.driver.find_element(By.NAME, self.platform.login_button_name).click()

    """ get cities from Database and loop through the profiles"""

    def loop_through_towns(self):
        # get all search queries ordered by PLZ ascending
        self.__cursor.execute(
            "select id,city,plz,radius,filter,scraping_4_PLZ,scraped_4_topnanny,scraped_4_babysits,scraped_4_babysitting24,scraped_4_seniorservice24 from search_query ORDER BY plz;"
        )
        search_queries = self.__cursor.fetchall()

        # to only look at PLZ which have not yet been scraped
        # position of each platform in search query returned from DB looks
        if self.platform.__class__.__name__.lower() == 'topnanny':
            pos = 6
        elif self.platform.__class__.__name__.lower() == 'babysits':
            pos = 7
        elif self.platform.__class__.__name__.lower() == 'babysitting24':
            pos = 8
        elif self.platform.__class__.__name__.lower() == 'seniorservice24':
            pos = 9
        else:
            raise Exception("Platform: " + self.platform.__class__.__name__ +
                            " no scraped_4_" + self.platform.__class__.__name__.lower() + " in Database or Platform " +
                            "not implemented")

        # loop through cities from records in search_query table on DB and present it in a nice fashion
        for search_query in tqdm(search_queries,
                                 desc='looping through the cities on Platform: ' + self.platform.__class__.__name__):
            # skip cities which have already been scraped
            if search_query[pos] == 1:
                continue
            print()
            print(search_query)
            self.search_profiles(search_query, Users.Role.AGENT)
            self.search_profiles(search_query, Users.Role.PRINCIPAL)
            # update search query DB record such that it has been scraped for this platform
            self.__cursor.execute("Update search_query set scraped_4_" + self.platform.__class__.__name__.lower() +
                                  " = 1 where id = " + "'" + search_query[0] + "';")
            self.__connection.commit()
            # wait a minute for next search query
            time.sleep(600)

    def search_profiles(self, search_query, role):
        # reset position counter on site where each profile is located i.e. which rank it has
        profile_position_on_site_with_search = 0
        profile_highlighted = False
        page_count = 1
        page = 1
        page_pos = -1

        if isinstance(self.platform, Platforms.TopNanny):
            # go to the website where the search query can be entered
            self.driver.get(self.platform.website)

            # on topnanny Principal = child_offer
            if role == Users.Role.PRINCIPAL:
                dropdown = self.driver.find_element(By.NAME, "search[search_type]")
                self.driver.execute_script("""arguments[0].setAttribute('value', 'child_offer')""", dropdown)
            # on topnanny Agent = child_service
            elif role == Users.Role.AGENT:
                dropdown = self.driver.find_element(By.NAME, "search[search_type]")
                self.driver.execute_script("""arguments[0].setAttribute('value', 'child_service')""", dropdown)

            # get PLZ from DB and enter it into the search field of the corresponding platform
            self.driver.find_element(By.ID, self.platform.searchfield_id).send_keys(search_query[2])
            self.driver.find_element(By.NAME, self.platform.search_button_id).click()

            # wait for site to properly load content
            time.sleep(5)

            # set radius for each search query -> set to default of 10km anyway. I.e. could be deleted since
            # profiles will be removed in post process/analyze
            if role == Users.Role.PRINCIPAL:
                radius_topnanny = self.driver.find_element(By.ID, "search_max_radius")
                self.driver.execute_script("""arguments[0].setAttribute('type', 'visible')""", radius_topnanny)
                self.driver.execute_script("""arguments[0].setAttribute('value', '10000')""", radius_topnanny)
                self.driver.find_element(By.ID, "search_max_radius").submit()
            elif role == Users.Role.AGENT:
                radius_topnanny = self.driver.find_element(By.ID, "search_max_radius")
                self.driver.execute_script("""arguments[0].setAttribute('type', 'visible')""", radius_topnanny)
                self.driver.execute_script("""arguments[0].setAttribute('value', '10000')""", radius_topnanny)
                self.driver.find_element(By.ID, "search_max_radius").submit()

            # wait for site to properly load content
            time.sleep(60)

            # Idea: if scraping account was blocked -> simply make a lookahead DB record
            # concretely: look in ranking_users and ranking_gigs and get latest profile hit i.e. position on site
            self.__cursor.execute(
                "select MAX(position_on_site) from ranking_users WHERE search_query_id = " + "'" + search_query[
                    0] + "' and platform_id = " + "'" + str(self.__platform_id) + "';"
            )
            last_position_user = self.__cursor.fetchone()
            self.__cursor.execute(
                "select MAX(position_on_site) from ranking_gigs WHERE search_query_id = " + "'" + search_query[
                    0] + "' and platform_id = " + "'" + str(self.__platform_id) + "';"
            )
            last_position_gig = self.__cursor.fetchone()

            if role == Users.Role.PRINCIPAL:
                last_position = last_position_gig[0]

            elif role == Users.Role.AGENT:
                last_position = last_position_user[0]

            if last_position is not None:
                # to get page on which last user was
                page = (last_position // 7) + 1
                # update profile position
                profile_position_on_site_with_search = last_position
                # position on individual page
                page_pos = (last_position % 7) - 1

            while True:
                # after every 100 profiles on each individual search query, wait 15 minutes.
                if profile_position_on_site_with_search == 100:
                    time.sleep(900)
                # then step to this page and then modulo to get individual page of next user;)
                if last_position is not None and page_count < page:
                    # to handle multiple pages, check if site has a navigation bar and open next page in the same window
                    try:
                        nav_bar = self.driver.find_element(By.ID, "search_pagination")
                        arrow_nav = nav_bar.find_elements(By.TAG_NAME, "a")
                        next_link = ""

                        for l in arrow_nav:
                            if l.get_attribute("rel") == "next":
                                next_link = l.get_attribute("href")

                        page_count += 1
                        self.driver.get(next_link)
                        continue
                    # navigation bar not present i.e. fewer or exactly 7 profiles returned / on page
                    except:
                        traceback.print_exception(*sys.exc_info())
                        pass
                # reset last position if available, such that it can continue scraping normally
                if last_position is not None:
                    last_position = None

                # on TopNanny always at most 7 results on each page
                for i in range(7):
                    if i <= page_pos:
                        continue
                    profile_id_name_on_topnanny = "result_" + str(i)
                    profile_highlighted = False
                    try:
                        links = self.driver.find_element(By.ID, profile_id_name_on_topnanny)
                        # if profile was found increment profile counter
                        profile_position_on_site_with_search += 1

                        try:
                            if links.get_attribute("class") == "boost search_result":
                                profile_highlighted = True
                        except NoSuchElementException:
                            pass
                        except NoSuchAttributeException:
                            pass
                        a = links.find_elements(By.TAG_NAME, "a")
                        # on TopNanny profile links are always returned 4 times thus can be skipped after one iteration
                        for link in a:
                            if role == Users.Role.PRINCIPAL:
                                self.explore_gig(link.get_attribute("href"), profile_position_on_site_with_search,
                                                 search_query, profile_highlighted)
                            elif role == Users.Role.AGENT:
                                self.explore_profile_agent(link.get_attribute("href"),
                                                           profile_position_on_site_with_search,
                                                           search_query, profile_highlighted)
                            break
                    # if there are less than 7 profiles on a page break out of while loop
                    except:
                        break

                # reset page position
                if page_pos > -1:
                    page_pos = -1
                # to handle multiple pages, check if site has a navigation bar and open next page in the same window
                try:
                    nav_bar = self.driver.find_element(By.ID, "search_pagination")
                    arrow_nav = nav_bar.find_elements(By.TAG_NAME, "a")
                    next_link = ""

                    for l in arrow_nav:
                        if l.get_attribute("rel") == "next":
                            next_link = l.get_attribute("href")
                    # last site reached, break out of while loop
                    if next_link == "":
                        break
                    else:
                        self.driver.get(next_link)
                # navigation bar not present i.e. fewer or exactly 7 profiles returned / on page
                except:
                    break

        elif isinstance(self.platform, Platforms.Babysits):
            # on Babysits different links for different roles
            if role == Users.Role.AGENT:
                self.driver.get(self.platform.agent_website)
            elif role == Users.Role.PRINCIPAL:
                self.driver.get(self.platform.principal_website)

            self.driver.find_element(By.XPATH, "//header[@id='header']/div/div/div[2]/button/div").click()
            time.sleep(1)
            self.driver.find_element(By.ID, 'autocomplete-header').send_keys(search_query[2] + ", " + search_query[1])
            self.driver.find_element(By.ID, 'autocomplete-header').submit()
            # wait for site to properly load
            time.sleep(60)

            while True:
                # explore all found profiles with given search
                try:
                    profiles = self.driver.find_elements(By.CLASS_NAME, 'profile-card')
                    for profile in profiles:
                        profile_position_on_site_with_search += 1
                        # after every 100 profiles on each individual search query, wait 15 minutes.
                        if profile_position_on_site_with_search == 100:
                            time.sleep(900)
                        profile_highlighted = False
                        if role == Users.Role.AGENT:
                            try:
                                if profile.find_element(By.CLASS_NAME, 'badge-supersitter'):
                                    profile_highlighted = True
                            except:
                                pass
                            self.explore_profile_agent(profile.find_element(By.TAG_NAME, 'a').get_attribute('href'),
                                                       profile_position_on_site_with_search, search_query,
                                                       profile_highlighted)
                        elif role == Users.Role.PRINCIPAL:
                            self.explore_gig(profile.find_element(By.TAG_NAME, 'a').get_attribute('href'),
                                             profile_position_on_site_with_search, search_query,
                                             profile_highlighted)
                # no profiles are found for search query
                except:
                    pass

                # loop through all pages of navigation bar
                try:
                    time.sleep(2)
                    nav_bar = self.driver.find_elements(By.XPATH,
                                                        "//div[@id='search']/div/div[2]/div/div/article/div[4]/nav/ul/li/a")
                    # no more sites, break out of the while loop
                    if nav_bar[-1].get_attribute('href') == self.driver.current_url:
                        break
                    self.driver.get(nav_bar[-1].get_attribute('href'))
                # no navigation bar found
                except:
                    break


        elif isinstance(self.platform, Platforms.Babysitting24) or isinstance(self.platform, Platforms.Seniorservice24):
            # expand dropdown for selection of principals and agents (gig worker)
            self.driver.find_element(By.XPATH, "//input[@id='']").click()

            # get webelements of both principals and agents
            principal_agent_search = self.driver.find_elements(By.XPATH,
                                                               "//form[@id='js-navigation-search_form']/div/div/div/ul/li/div/div/span")

            # save individual webelement in a variable
            for search in principal_agent_search:
                if search.text.lower() == 'jobangebote':
                    search_principals = search
                elif search.text.lower() == 'kinderbetreuer':
                    search_agents = search
                elif search.text.lower() == 'seniorenbetreuer':
                    search_agents = search

            # open web element based on search
            if role == Users.Role.PRINCIPAL:
                search_principals.click()
            elif role == Users.Role.AGENT:
                search_agents.click()

            # clear current search and enter search query
            self.driver.find_element(By.ID, "q_place").clear()
            self.driver.find_element(By.ID, "q_place").send_keys(search_query[2] + ", " + search_query[1])
            self.driver.find_element(By.ID, "q_place").submit()

            # wait for site to properly load profiles
            time.sleep(1)

            # set minimum possible radius since > 100 pages on this site cannot be scraped

            radius_babysitting24 = self.driver.find_element(By.XPATH,
                                                            "//*[@id='search_form_q_distance']")
            self.driver.execute_script("""arguments[0].setAttribute('type', 'visible')""", radius_babysitting24)
            self.driver.execute_script("""arguments[0].setAttribute('value', '1')""", radius_babysitting24)
            self.driver.find_element(By.XPATH, "//*[@id='search_form']/div[2]/input").submit()
            # wait for site to properly load profiles
            time.sleep(3)

            # to handle multiple pages, check if site has a navigation bar and open next page in the same window
            while True:
                # get all profiles on each page
                try:
                    for pos, profile in enumerate(self.driver.find_elements(By.XPATH, "//*[@id]/a")):
                        profile_highlighted = False
                        profile_position_on_site_with_search += 1
                        # after every 100 profiles on each individual search query, wait 15 minutes.
                        if profile_position_on_site_with_search == 100:
                            time.sleep(900)
                        if profile.find_element(By.XPATH, "//*[@id][" + str(
                                pos + 1) + "]/a/following-sibling::*[1]").get_attribute(
                            "class") == "new-styling card-avatar hidden-xcreated_ats mr-24 card-avatar--premium":
                            profile_highlighted = True
                        # only relevant for gig date
                        try:
                            created = profile.find_element(By.XPATH, "//*[@id][" + str(
                                pos + 1) + "]/a/following-sibling::*[4]").text
                        except:
                            created = ""
                            pass

                        if role == Users.Role.PRINCIPAL:
                            self.explore_gig(profile.get_attribute("href"), profile_position_on_site_with_search,
                                             search_query, profile_highlighted, created)
                        elif role == Users.Role.AGENT:
                            self.explore_profile_agent(profile.get_attribute("href"),
                                                       profile_position_on_site_with_search, search_query,
                                                       profile_highlighted)
                # no profiles found for search query
                except:
                    break

                # to handle multiple pages, check if site has a navigation bar and open next page in the same window
                try:
                    nav_bar = self.driver.find_element(By.XPATH,
                                                       "//*[@id='logged-in']/div[2]/div/div[2]/div[2]/div[3]/div/div")
                    pages = nav_bar.find_elements(By.TAG_NAME, "a")
                    next_page = ""

                    for l in pages:
                        if l.get_attribute("rel") == "next":
                            next_page = l.get_attribute("href")
                    # last site reached, break out of while loop
                    if next_page == "":
                        break
                    else:
                        self.driver.get(next_page)
                # navigation bar not present i.e. fewer or exact profiles returned / on page
                except:
                    break

    """ Profile will be opened in the second tab"""

    def explore_profile_agent(self, profile_url, profile_position_on_site_with_search, search_query,
                              profile_highlighted):
        # open profile in new tab such that the current position isn't lost and such that the cookies etc. can be used
        self.driver.switch_to.new_window(WindowTypes.TAB)
        self.driver.get(profile_url)
        # fix problem when account gets blocked to completely exit and save to log file
        if self.driver.current_url == self.platform.website:
            now = datetime.datetime.now()
            with open("scrapping.log", "a") as file:
                file.write("Profile couldn't be scraped, this probably means the scraping account was blocked\n")
                file.write("Time failed: " + now.strftime("%d.%m.%Y %H:%M:%S") + "\n")
                file.write("Search Query: " + str(search_query) + "\n")
                file.write("Failed to load profile on position: " + str(profile_position_on_site_with_search) + "\n\n")
            sys.exit(0)

        firstname = ""
        lastname = ""
        role = Users.Role.AGENT
        joined_on = ""
        last_online = ""
        response_time_hours = ""
        age = ""
        birthdate = ""
        gender = ""
        race = ""
        profile_description = ""
        wage = ""
        normalized_rating = ""
        original_rating = ""
        profile_id = ""
        profile_picture_url = ""
        gigs = 0
        has_documents_uploaded = 0
        has_references = 0
        verified = False
        favorised = 0
        professional_subscription = False
        experience_in_years = 0
        spoken_languages = ""
        scraped_at = ""
        # for the location object
        location = ""
        latitude = ""
        longitude = ""
        # for the review and reference objects
        reviews = []
        references = []

        # wait one second to fully load profile with all its details
        time.sleep(1)

        if isinstance(self.platform, Platforms.TopNanny):
            try:
                firstname = self.driver.find_element(By.ID, 'profile_name').text
            except:
                pass
            try:
                age = False
            except:
                pass
            try:
                last_online = self.driver.find_element(By.ID, 'last_connexion').text
            except:
                pass
            try:
                profile_description = self.driver.find_element(By.ID, 'presentation').text
            except:
                pass
            # reviews and rating
            try:
                # temporary lists to store individual reviews
                review_authors = []
                review_description = []
                review_ratings = []
                review_rating = 0
                count = 0
                original_rating = 0

                # only when more objects than two reviews exist
                if len(self.driver.find_elements(By.XPATH, "//*[@id='recommendations']/div")) > 2:
                    review_elements = self.driver.find_elements(By.XPATH, "//*[@id='recommendations']/div")
                    for pos, review in enumerate(review_elements):
                        # first and last element not relevant
                        if (pos == 0) or (pos == len(review_elements) - 1):
                            continue
                        # add description of review to list
                        review_description.append(self.driver.find_element(By.XPATH,
                                                                           "//*[@id='recommendations']/div[" + str(
                                                                               pos + 1) + "]/p").text)
                        # add author of review to list
                        review_authors.append(self.driver.find_element(By.XPATH,
                                                                       "//*[@id='recommendations']/div[" + str(
                                                                           pos + 1) + "]/div").text)
                        # get all stars in each individual review and count it up
                        stars = self.driver.find_elements(By.XPATH, "//*[@id='recommendations']/div[" + str(
                            pos + 1) + "]/div/div/i")
                        for star in stars:
                            count += 1
                            if star.get_attribute("class") == "icon active":
                                review_rating += 1
                                original_rating += 1
                            if count == 5:
                                review_ratings.append(review_rating)
                                count = 0
                                review_rating = 0

                    # instantiate review object and add it to the review list
                    # reviewee_id is currently empty and will be added once user is instantiated later
                    for pos in range(len(review_ratings)):
                        reviews.append(Reviews.Reviews(
                            "",
                            review_ratings[pos],
                            review_description[pos],
                            review_authors[pos],
                            ""
                        ))

                    # calculate original rating from individual reviews
                    if len(review_ratings) > 0:
                        original_rating = (original_rating / len(review_ratings))

            except:
                traceback.print_exception(*sys.exc_info())
                pass
            try:
                # instantiate empty location object if location couldn't be converted
                location_obj = Locations.Locations("-1", "-1", "-1", "-1", "-1", "-1")
            except:
                pass
            try:
                wage_unmod = self.driver.find_element(By.CLASS_NAME, 'price_amount').text
                newline_pos = wage_unmod.find("\n")
                wage = wage_unmod[:newline_pos] + " " + wage_unmod[newline_pos + 1:]
            except:
                pass
            try:
                picture_url_class = self.driver.find_element(By.CLASS_NAME, 'galleria-images')
                profile_picture_url = picture_url_class.find_element(By.TAG_NAME, 'img').get_attribute('src')
            except:
                pass
            try:
                # stupid way but only way I could come up for TopNanny
                verified_class = self.driver.find_elements(By.ID, 'verifications_box')
                pos = verified_class[0].text.find('Identität\nüberprüft')
                if pos > 0:
                    verified = True
            except:
                pass
            try:
                # to get languages always in table under "Gesprochene Sprachen" which ends before
                # the next entry "Zusätzliche Dienste"
                start = 0
                end = 0
                # save position in table element to find start of language and end
                table = self.driver.find_elements(By.TAG_NAME, 'td')
                spoken_languages_lst = []
                for pos, i in enumerate(table):
                    if i.text == "Gesprochene Sprachen":
                        start = pos
                    if i.text == "Zusätzliche Dienste":
                        end = pos
                # go through it again to get data
                for pos, i in enumerate(table):
                    if (start > 0) & (pos > start) & (pos < end):
                        spoken_languages_lst.append(i.text)

                for language in spoken_languages_lst:
                    spoken_languages += language.strip()
            except:
                pass

        # Get the profile from Babysits. Not possible to scrape:
        # professional subscription
        elif isinstance(self.platform, Platforms.Babysits):
            professional_subscription = "n/A"
            has_documents_uploaded = "n/A"
            # get firstname, age and check if profile is verified
            try:
                firstname = self.driver.find_element(By.XPATH,
                                                     "//div[@class='name d-flex align-items-center']/h1/span[@class='name']").text
                age = False
                if (self.driver.find_element(By.XPATH,
                                             "//div[@class='name d-flex align-items-center']/h1/span[@class='badge-government-id']")):
                    verified = True
            except:
                pass
            # get user id, on babysits user can be accessed directly via https://babysits.ch/user/profileid
            try:
                for detail in self.driver.find_elements(By.TAG_NAME, "dialog"):
                    try:
                        if detail.find_element(By.TAG_NAME, "input").get_attribute("name") == "user_id":
                            profile_id = detail.find_element(By.TAG_NAME, "input").get_attribute("value")
                    except:
                        pass
            except:
                pass
            # get profile picture and wage
            try:
                json_ob = self.driver.find_element(By.CSS_SELECTOR, "script[type='application/ld+json']")
                # setting strict to False since JSON object is not properly formated
                json_text = json.loads(json_ob.get_attribute("innerHTML"), strict=False)
                profile_picture_url = json_text["image"]
                wage = json_text["priceRange"]
                original_rating = json_text["aggregateRating"]["ratingValue"]

            except:
                pass

            # handling reviews of the user
            try:
                # create separate list for all author names and links to their profile of the reviews
                review_authors_links = []
                try:
                    authors = self.driver.find_elements(By.XPATH,
                                                        "//*[@id='reviews-block-ref']/div/div[1]/div[2]/div[1]/div/div/div/div/div[1]/div/div[2]/div/div/h3/a")
                    for author in authors:
                        review_authors_links.append(author.get_attribute('href'))
                except:
                    pass

                # create review objects and add all review objects to a separate list
                # Reviews not yet saved to DB since the user ID (reviewee ID) does not yet exist
                for pos, review_in_json in enumerate(json_text["review"]):
                    if len(review_authors_links) == 0:
                        review_author_link = ""
                    else:
                        review_author_link = review_authors_links[pos]
                    # empty title since it doesn't exist on Babysits reviews
                    # empty reviewee ID since the user object has not yet been created
                    reviews.append(Reviews.Reviews(
                        "",
                        review_in_json["reviewRating"]["ratingValue"],
                        review_in_json["reviewBody"],
                        review_in_json["author"]["name"] + " " + review_author_link,
                        ""
                    ))
            except:
                pass

            try:
                references_lst = self.driver.find_elements(By.XPATH,
                                                           "//*[@id='references-wrapper']/div/div[1]/div[2]/div[1]/div/div")
                for reference in references_lst:
                    try:
                        has_references += 1
                        references.append(
                            References.References(
                                "",
                                reference.find_element(By.CLASS_NAME, "title").find_element(By.TAG_NAME, "a").text,
                                "",
                                reference.find_element(By.XPATH, "//div/div/div[2]/p").get_attribute("data-content"),
                                reference.find_element(By.CLASS_NAME, "title").find_elements(By.TAG_NAME, "span")[
                                    1].text,
                                reference.find_element(By.CLASS_NAME, "title").find_element(By.TAG_NAME,
                                                                                            "a").text + " " +
                                reference.find_element(By.CLASS_NAME, "title").find_element(By.TAG_NAME,
                                                                                            "a").get_attribute("href"),
                                ""
                            )
                        )
                    except:
                        pass

            except:
                pass

            # get location of user
            try:
                # instantiate empty location object if location couldn't be converted
                location_obj = Locations.Locations("-1", "-1", "-1", "-1", "-1", "-1")
            except:
                pass

            # get if a person was favorised and check all spoken languages
            try:
                for detail in self.driver.find_elements(By.CLASS_NAME, "col-sm-6"):
                    try:
                        if detail.find_element(By.CLASS_NAME, "title").text.lower() == "favorisiert":
                            favorised_unmod = detail.find_element(By.CLASS_NAME, "status").text
                            favorised = favorised_unmod.replace(" mal", "")
                    except:
                        pass
                    try:
                        if detail.find_element(By.CLASS_NAME, "title").text.lower() == "sprachen, die ich spreche":
                            spoken_languages_unmod = detail.find_element(By.CLASS_NAME, "status").text
                            spoken_languages = spoken_languages_unmod.replace("\n", ", ")
                    except:
                        pass
            except:
                pass

            # activity
            try:
                for detail in self.driver.find_elements(By.CLASS_NAME, "activity"):
                    try:
                        if detail.find_element(By.CLASS_NAME, "title").text.lower() == "mitglied seit":
                            joined_on = detail.find_element(By.CLASS_NAME, "status").text
                    except:
                        pass
                    try:
                        if detail.find_element(By.CLASS_NAME, "title").text.lower() == "letzte aktivität":
                            last_online = detail.find_element(By.TAG_NAME, "time").get_attribute("datetime")
                    except:
                        pass
                    try:
                        if detail.find_element(By.CLASS_NAME, "title").text.lower() == "durchschnittliche antwortzeit":
                            response_time_hours = detail.find_element(By.CLASS_NAME, "status").text
                    except:
                        pass
                    try:
                        if detail.find_element(By.CLASS_NAME, "title").text.lower() == "buchungen":
                            gigs = detail.find_element(By.CLASS_NAME, "status").text
                    except:
                        pass
            except:
                pass

            # experience
            try:
                experience_in_years = self.driver.find_element(By.XPATH,
                                                               "//*[@id='profile']/div[2]/div/div[1]/div/div[2]/div[1]/div[2]/div[2]").text
            except:
                pass

            # expand description of user iff not fully visible open (read more...)
            try:
                self.driver.find_element(By.XPATH,
                                         "//*[@id='profile']/div/div/div/div/div/div/div/div/div/button").click()
            except:
                pass
            # get description of profile
            try:
                profile_description = self.driver.find_element(By.CLASS_NAME, 'description-content').text
            except:
                pass

        # Get the profile from Babysitting24. Not possible to scrape:
        # gigs
        # favorised
        elif isinstance(self.platform, Platforms.Babysitting24) or isinstance(self.platform, Platforms.Seniorservice24):
            # on Babysitting24 some results are still shown, although not valid anymore
            try:
                self.driver.find_element(By.XPATH, "//*[@id='logged-in']/div[4]/div/div[4]/div[2]/div[3]/button")
                # close current tab and switch back to the main tab
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                return
            except:
                pass

            # on all profile links the pagination is always added by the search query -> get rid of that
            profile_url = profile_url[:profile_url.find("?")]

            # on Babysitting24 highlighted only when professional subscription
            professional_subscription = profile_highlighted

            try:
                firstname = self.driver.find_element(By.XPATH,
                                                     "//*[@id='profile_main_column']/div[1]/div[1]/div[2]/div/div/div[1]/div/div/h1").text
            except:
                pass

            # get joined date and last login date
            try:
                for pos, detail in enumerate(self.driver.find_elements(By.XPATH,
                                                                       "//*[@id='logged-in']/div/div/div/div[1]/div/div/div/div[2]/div[2]/div/div/span[1]")):
                    try:
                        if detail.text.lower() == "zuletzt eingeloggt:":
                            last_online = self.driver.find_element(By.XPATH,
                                                                   "//*[@id='logged-in']/div/div/div/div[1]/div/div/div/div[2]/div[2]/div[" + str(
                                                                       pos + 1) + "]/div/span/following-sibling::*[1]").text
                    except:
                        pass
                    try:
                        if detail.text.lower() == "mitglied seit:":
                            joined_on = self.driver.find_element(By.XPATH,
                                                                 "//*[@id='logged-in']/div/div/div/div[1]/div/div/div/div[2]/div[2]/div[" + str(
                                                                     pos + 1) + "]/div/span/following-sibling::*[1]").text
                    except:
                        pass
            except:
                pass

            # age, wage and experience
            try:
                if isinstance(self.platform, Platforms.Seniorservice24):
                    age = False
                    wage = self.driver.find_element(By.XPATH,
                                                    "//*[@id='profile_main_column']/div[1]/div[1]/div[2]/div/div/div/div/div/div[2]/div/div[2]").text
                    experience_in_years = self.driver.find_element(By.XPATH,
                                                                   "//*[@id='profile_main_column']/div[1]/div[1]/div[2]/div/div/div/div/div/div[3]/div/div[2]").text.split(
                        " ")[0]
                else:
                    age = False
                    wage = self.driver.find_element(By.XPATH,
                                                    "//*[@id='profile_main_column']/div[1]/div[1]/div[2]/div/div/div[3]/div/div/div[2]/div/div[2]").text
                    experience_in_years = self.driver.find_element(By.XPATH,
                                                                   "//*[@id='profile_main_column']/div[1]/div[1]/div[2]/div/div/div[3]/div/div/div[3]/div/div[2]").text.split(
                        " ")[0]
            except:
                pass

            try:
                profile_description = self.driver.find_element(By.XPATH,
                                                               "//*[@id='profile_main_column']/div[1]/div[3]/div/div/div[1]/div/div/div").text
            except:
                pass

            # profile ID from profile URL
            try:
                profile_id = profile_url.split("/")[-1]
            except:
                pass

            # profile picture URL
            try:
                profile_picture_url = self.driver.find_element(By.XPATH,
                                                               "//*[@id='logged-in']/div/div/div/div/div/div/div/div/div/div/div/div/a/img").get_attribute(
                    "src")
            except:
                pass

            # save how many documents a user has uploaded
            # references are stored as documents on sites
            try:
                if isinstance(self.platform, Platforms.Seniorservice24):
                    if self.driver.find_element(By.XPATH, "//*[@id='documents']"):
                        has_documents_uploaded = len(
                            self.driver.find_elements(By.XPATH, "//*[@id='documents']/div/div/div/span"))

                    for detail in self.driver.find_elements(By.XPATH, "//*[@id='documents']/div/div/div/span"):
                        if detail.text.lower() == "referenz":
                            has_references += 1
                else:
                    if self.driver.find_element(By.XPATH, "//*[@id='documents']"):
                        has_documents_uploaded = len(
                            self.driver.find_elements(By.XPATH, "//*[@id='documents']/div/div/a/span"))

                    for detail in self.driver.find_elements(By.XPATH, "//*[@id='documents']/div/div/a/span"):
                        if detail.text.lower() == "referenz":
                            has_references += 1
            except:
                pass

            # check if profile is verified
            try:
                if self.driver.find_element(By.XPATH,
                                            "//*[@id='profile_main_column']/div[1]/div[1]/div[2]/div/div/div[1]/div/div/div/div/div/div"):
                    verified = True
            except:
                pass

            # spoken languages
            try:
                for pos, detail in enumerate(self.driver.find_elements(By.XPATH,
                                                                       "//*[@id='profile_main_column']/div[1]/div[4]/div/div/div/div/div/div[1]")):
                    if detail.text.lower() == 'sprachen':
                        spoken_languages = self.driver.find_element(By.XPATH,
                                                                    "//*[@id='profile_main_column']/div[1]/div[4]/div/div/div[" + str(
                                                                        pos + 1) + "]/div/div/div[2]").text
            except:
                pass

            # location of user
            try:
                plz = self.driver.find_element(By.XPATH,
                                               "//*[@id='profile_main_column']/div[1]/div[1]/div[2]/div/div/div[2]/div/span[1]").text.split(
                    " ")[0]
                city = self.driver.find_element(By.XPATH,
                                                "//*[@id='profile_main_column']/div[1]/div[1]/div[2]/div/div/div[2]/div/span[1]").text.split(
                    " ")[1]
                location_obj = Locations.Locations("-1", plz, city, "-1", "-1", "-1")
            except:
                location_obj = Locations.Locations("-1", "-1", "-1", "-1", "-1", "-1")
                pass

            # open and expand all reviews if there are more than 3
            try:
                self.driver.find_element(By.XPATH, "//*[@id='profile_main_column']/div/div/div/div/button[1]").click()
                time.sleep(1)
            except:
                pass

            try:
                # temporary lists to store individual reviews
                review_authors = []
                review_description = []
                review_ratings = []
                review_rating = 0
                count = 0
                original_rating = 0

                # get description of each review
                for description in self.driver.find_elements(By.XPATH,
                                                             "//*[@id='profile_main_column']/div/div/div/div[2]/div/div/div[2]"):
                    review_description.append(description.text)

                # get author names of each review
                for authors in self.driver.find_elements(By.XPATH,
                                                         "//*[@id='profile_main_column']/div/div/div/div[2]/div/div/div[last()]/div"):
                    review_authors.append(authors.text)

                # step through each star and check if it's filled out which corresponds to the rating
                # (max. on platform is 5 stars) -> after reaching 5 stars, reset counter to get next rating of review
                for star in self.driver.find_elements(By.XPATH,
                                                      "//*[@id='profile_main_column']/div/div/div/div[2]/div/div/div[1]/*/div[1]"):
                    count += 1
                    if star.get_attribute("class") == "new-styling absolute full-width full-height star-border filling":
                        review_rating += 1
                        original_rating += 1
                    if count == 5:
                        review_ratings.append(review_rating)
                        count = 0
                        review_rating = 0

                # instantiate review object and add it to the review list
                for pos in range(len(review_ratings)):
                    reviews.append(Reviews.Reviews(
                        "",
                        review_ratings[pos],
                        review_description[pos],
                        review_authors[pos],
                        ""
                    ))

                # calculate original rating from individual reviews
                if len(review_ratings) > 0:
                    original_rating = (original_rating / len(review_ratings))

            except:
                pass

        # to get current date and time
        now = datetime.now()
        scraped_at = now.strftime("%d.%m.%Y %H:%M:%S")

        # instantiate user and it's ranking
        try:
            user = Users.Users(firstname, lastname, role, joined_on, last_online, response_time_hours, age, gender,
                               race, profile_description, wage, normalized_rating, original_rating, profile_id,
                               profile_picture_url,
                               profile_url, gigs, has_documents_uploaded, has_references, verified, favorised,
                               professional_subscription,
                               experience_in_years, spoken_languages, scraped_at,
                               self.__platform_id, location_obj)

            ranking_obj = Users.Ranking(
                profile_position_on_site_with_search, profile_highlighted, search_query[0], self.__platform_id,
                str(user.id)
            )

            # get user from DB which already exists
            self.__cursor.execute("select id, firstname, profile_id, profile_url, platform_id from users WHERE " +
                                  "LOWER(firstname)='" + user.firstname.lower() + "' " +
                                  "and LOWER(profile_id)='" + user.profile_id.lower() + "' " +
                                  "and LOWER(profile_url)='" + user.profile_url.lower() + "' " +
                                  "and platform_id='" + user.platform_id + "';")
            db_user = self.__cursor.fetchone()

            # user does not yet exist in DB
            if db_user is None:
                sql_base_query = """INSERT INTO locations (id, address, plz, city, country, latitude, longitude)
                                                VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                self.__cursor.execute(sql_base_query, location_obj.get_location())
                self.__connection.commit()

                sql_base_query = """INSERT INTO users (id, firstname, lastname, role, joined_on, last_online,
                response_time_hours, age, gender, race, profile_description, wage, normalized_rating, original_rating,
                profile_id, picture_url, profile_url, gigs, has_documents_uploaded, has_references, verified,
                favorised, professional_subscription, experience_in_years, spoken_languages, scraped_at,
                platform_id, location_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                self.__cursor.execute(sql_base_query, user.get_user())
                self.__connection.commit()

                sql_base_query = """INSERT INTO ranking_users (id, position_on_site, profile_highlighted, search_query_id,
                                scraped_at, platform_id, user_id)
                                                            VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                self.__cursor.execute(sql_base_query, ranking_obj.get_ranking())
                self.__connection.commit()

                # go through all reviews and update the reviewee ID with above user and save it to the DB
                try:
                    for review in reviews:
                        review.update_reviewee_id(user.id)
                        sql_base_query = """INSERT INTO reviews (id, title, original_rating, description, author_id, reviewee_id)
                                                VALUES (%s, %s, %s, %s, %s, %s)"""
                        self.__cursor.execute(sql_base_query, review.get_review())
                        self.__connection.commit()

                except:
                    traceback.print_exception(*sys.exc_info())
                    pass

                # go through all references and update the referencee ID with above user
                try:
                    for reference in references:
                        reference.update_referencee_id(user.id)
                        sql_base_query = """INSERT INTO platforms.references (id, title, firstname, lastname,
                                                description, relationship, author_id, referencee_id)
                                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                        self.__cursor.execute(sql_base_query, reference.get_reference())
                        self.__connection.commit()
                except:
                    traceback.print_exception(*sys.exc_info())
                    pass

            # user already exists in DB -> only ranking needs to be added
            else:
                # in the ranking update the id of the already existing DB user
                ranking_obj.update_user_id(db_user[0])
                sql_base_query = """INSERT INTO ranking_users (id, position_on_site, profile_highlighted, search_query_id,
                                                scraped_at, platform_id, user_id)
                                                                            VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                self.__cursor.execute(sql_base_query, ranking_obj.get_ranking())
                self.__connection.commit()
                print("user already exists")

        except:
            traceback.print_exception(*sys.exc_info())
            pass

        # close current tab and switch back to the main tab
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

    """ Open Gig and scrape details from it """

    def explore_gig(self, gig_url, gig_position_on_site_with_search, search_query,
                    gig_highlighted, created="n/A"):
        # open profile in new tab such that the current position isn't lost and such that the cookies etc. can be used
        self.driver.switch_to.new_window(WindowTypes.TAB)
        self.driver.get(gig_url)
        # fix problem when account gets blocked to completely exit
        if self.driver.current_url == self.platform.website:
            now = datetime.datetime.now()
            with open("scrapping.log", "a") as file:
                file.write("Profile couldn't be scraped, this probably means the scraping account was blocked\n")
                file.write("Time failed: " + now.strftime("%d.%m.%Y %H:%M:%S") + "\n")
                file.write("Search Query: " + str(search_query) + "\n")
                file.write("Failed to load profile on position: " + str(profile_position_on_site_with_search) + "\n\n")
            sys.exit(0)

        title = ""
        if isinstance(self.platform, Platforms.Seniorservice24):
            type_of_job = Gigs.TypeOfJob.SENIORSERVICE
        else:
            type_of_job = Gigs.TypeOfJob.CHILDSERVICE
        created_at = ""
        gig_date = ""
        wage = ""
        gig_description = ""
        author_id = ""
        agent_id = ""
        gig_id = ""
        scraped_at = ""
        # TODO: not yet in DB
        last_online = ""

        # for the location object
        location = ""
        latitude = ""
        longitude = ""

        # for the review and reference objects
        reviews = []
        references = []

        # wait one second to fully load profile with all its details
        time.sleep(1)

        if isinstance(self.platform, Platforms.TopNanny):
            try:
                title = self.driver.find_element(By.TAG_NAME, 'h1').text
            except:
                pass
            try:
                last_online = self.driver.find_element(By.ID, 'last_connexion').text
            except:
                pass
            try:
                gig_description = self.driver.find_element(By.ID, 'offer_content').text
            except:
                pass
            try:
                for i in self.driver.find_elements(By.TAG_NAME, 'meta'):
                    if i.get_attribute('itemprop') == 'datePosted':
                        created_at = i.get_attribute('content')
            except:
                pass
            try:
                # instantiate empty location object if location couldn't be converted
                location_obj = Locations.Locations("-1", "-1", "-1", "-1", "-1", "-1")
            except:
                pass

        # Get the gig from Babysits. Not possible to scrape:
        # gig date
        elif isinstance(self.platform, Platforms.Babysits):
            try:
                json_ob = self.driver.find_element(By.CSS_SELECTOR, "script[type='application/ld+json']")
                # setting strict to False since JSON object is not properly formated
                json_text = json.loads(json_ob.get_attribute("innerHTML"), strict=False)
                created_at = json_text["datePosted"]
                title = json_text["title"]
                wage = str(json_text["baseSalary"]["value"]["value"]) + " " + json_text["baseSalary"]["value"][
                    "unitText"]
            except:
                pass
            # get author id, on babysits user can be accessed directly via https://babysits.ch/user/profileid
            # on Babysits gig_id = author_id since it is directly the principals profile
            try:
                for detail in self.driver.find_elements(By.TAG_NAME, "dialog"):
                    try:
                        if detail.find_element(By.TAG_NAME, "input").get_attribute("name") == "user_id":
                            gig_id = detail.find_element(By.TAG_NAME, "input").get_attribute("value")
                    except:
                        pass
            except:
                pass

            # expand description of user iff not fully visible open (read more...)
            try:
                self.driver.find_element(By.XPATH,
                                         "//*[@id='profile']/div/div/div/div/div/div/div/div/div/button").click()
            except:
                pass
            # get description of gig
            try:
                gig_description = self.driver.find_element(By.CLASS_NAME, 'description-content').text
            except:
                pass

            # get location of gig
            try:
                # instantiate empty location object if location couldn't be converted
                location_obj = Locations.Locations("-1", "-1", "-1", "-1", "-1", "-1")
            except:
                pass

            # handling reviews of the user
            try:
                # create separate list for all author names and links to their profile of the reviews
                review_authors_links = []
                try:
                    authors = self.driver.find_elements(By.XPATH,
                                                        "//*[@id='reviews-block-ref']/div/div[1]/div[2]/div[1]/div/div/div/div/div[1]/div/div[2]/div/div/h3/a")
                    for author in authors:
                        review_authors_links.append(author.get_attribute('href'))
                except:
                    pass
            except:
                pass

        # Get the profile from Babysitting24. Not possible to scrape:
        # wage
        # review
        # references
        # author_id
        # agent_id
        elif isinstance(self.platform, Platforms.Babysitting24) or isinstance(self.platform, Platforms.Seniorservice24):
            # on Babysitting24 some results are still shown, although not valid anymore
            try:
                self.driver.find_element(By.XPATH, "//*[@id='logged-in']/div[4]/div/div[4]/div[2]/div[3]/button")
                # close current tab and switch back to the main tab
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                return
            except:
                pass

            # on all profile links the pagination is always added by the search query -> get rid of that
            gig_url = gig_url[:gig_url.find("?")]
            wage = "n/A"

            try:
                title = self.driver.find_element(By.XPATH,
                                                 "//*[@id='profile_main_column']/div[1]/div[1]/div[2]/div/div/div[1]/div/div/h1").text
            except:
                pass

            # created_at from passing of function
            created_at = created

            # get last login date
            try:
                for pos, detail in enumerate(self.driver.find_elements(By.XPATH,
                                                                       "//*[@id='logged-in']/div/div/div/div[1]/div/div/div/div[2]/div[2]/div/div/span[1]")):
                    try:
                        if detail.text.lower() == "zuletzt eingeloggt:":
                            last_online = self.driver.find_element(By.XPATH,
                                                                   "//*[@id='logged-in']/div/div/div/div[1]/div/div/div/div[2]/div[2]/div[" + str(
                                                                       pos + 1) + "]/div/span/following-sibling::*[1]").text
                    except:
                        pass
            except:
                pass

            # gig_date
            try:
                if isinstance(self.platform, Platforms.Seniorservice24):
                    gig_date = self.driver.find_element(By.XPATH,
                                                        "//*[@id='profile_main_column']/div[1]/div/div/div/div/div[1]/div/div/div[2]").text
                else:
                    gig_date = self.driver.find_element(By.XPATH,
                                                        "//*[@id='profile_main_column']/div[1]/div/div/div/div[1]/div[1]/div[1]/div[1]/div[2]").text
            except:
                pass

            # gig_description
            try:
                if isinstance(self.platform, Platforms.Seniorservice24):
                    for pos, detail in enumerate(self.driver.find_elements(By.XPATH,
                                                                           "//*[@id='profile_main_column']/div[1]/div/div/div/div[1]/div[1]/div[1]/div[1]")):
                        if detail.text.lower() == "ein paar worte zu den aufgaben und zur wunschperson":
                            gig_description = self.driver.find_element(By.XPATH,
                                                                       "//*[@id='profile_main_column']/div[1]/div[" + str(
                                                                           pos + 1) + "]/div/div/div[1]/div[1]/div[1]/div[1]/following-sibling::*").text
                else:
                    for pos, detail in enumerate(self.driver.find_elements(By.XPATH,
                                                                           "//*[@id='profile_main_column']/div[1]/div/div/div/div[1]/div[1]/div[1]/div[1]")):
                        if detail.text.lower() == "zusätzliche angaben":
                            gig_description = self.driver.find_element(By.XPATH,
                                                                       "//*[@id='profile_main_column']/div[1]/div[" + str(
                                                                           pos + 1) + "]/div/div/div[1]/div[1]/div[1]/div[1]/following-sibling::*").text
            except:
                pass

            # gig_id
            try:
                gig_id = gig_url.split("/")[-1]
            except:
                pass

            # location of user
            try:
                plz = self.driver.find_element(By.XPATH,
                                               "//*[@id='profile_main_column']/div[1]/div[1]/div[2]/div/div/div[2]/div/div/div/span[1]").text.split(
                    " ")[0]
                city = self.driver.find_element(By.XPATH,
                                                "//*[@id='profile_main_column']/div[1]/div[1]/div[2]/div/div/div[2]/div/div/div/span[1]").text.split(
                    " ")[1]
                location_obj = Locations.Locations("-1", plz, city, "-1", "-1", "-1")
            except:
                location_obj = Locations.Locations("-1", "-1", "-1", "-1", "-1", "-1")
                pass

        # to get current date and time
        now = datetime.now()
        scraped_at = now.strftime("%d.%m.%Y %H:%M:%S")

        # instantiate GIG
        try:
            gig = Gigs.Gigs(title, type_of_job, created_at, gig_date, gig_url, wage, gig_id, gig_description, author_id,
                            agent_id,
                            self.__platform_id, scraped_at, location_obj)

            ranking_obj = Gigs.Ranking(
                gig_position_on_site_with_search, gig_highlighted, search_query[0], self.__platform_id,
                str(gig.id)
            )

            # get gig from DB which already exists
            self.__cursor.execute(
                "select id, title, type_of_job, created_at, gig_date, gig_url, wage, gig_id, description, "
                "author_id, agent_id, platform_id, scraped_at, location_id "
                "from gigs WHERE " +
                "LOWER(title)='" + gig.title.lower() + "' " +
                "and LOWER(author_id)='" + gig.author_id.lower() + "' " +
                "and LOWER(gig_url)='" + gig.gig_url.lower() + "' " +
                "and platform_id='" + gig.platform_id + "';")
            db_gig = self.__cursor.fetchone()

            # gig does not yet exist in DB
            if db_gig is None:
                sql_base_query = """INSERT INTO locations (id, address, plz, city, country, latitude, longitude)
                                                                VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                self.__cursor.execute(sql_base_query, location_obj.get_location())
                self.__connection.commit()

                # whats author_id? -> since foreign_key same for agent_id

                sql_base_query = """INSERT INTO gigs (id, title, type_of_job, created_at, gig_date, gig_url, wage,
                                gig_id, description, author_id, agent_id, platform_id, scraped_at, location_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                self.__cursor.execute(sql_base_query, gig.get_gig())
                self.__connection.commit()

                sql_base_query = """INSERT INTO ranking_gigs (id, position_on_site, gig_highlighted, search_query_id,
                                                                scraped_at, platform_id, gig_id)
                                                                VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                self.__cursor.execute(sql_base_query, ranking_obj.get_ranking())
                self.__connection.commit()

            # gig already exists in DB -> only ranking needs to be added
            else:
                # in the ranking update the id of the already existing DB user
                ranking_obj.update_gig_id(db_gig[0])
                sql_base_query = """INSERT INTO ranking_gigs (id, position_on_site, gig_highlighted, search_query_id,
                                                                scraped_at, platform_id, gig_id)
                                                                VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                self.__cursor.execute(sql_base_query, ranking_obj.get_ranking())
                self.__connection.commit()
                print("gig already exists")
        except:
            traceback.print_exception(*sys.exc_info())
            pass

        # close current tab and switch back to the main tab
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])


if __name__ == '__main__':
    # instantiate Platforms including its login
    topnanny = Platforms.TopNanny("username@example.com", "myFancyPassword123")

    s_topnanny = Scraper(topnanny, 'Database Host', 'DB Name', 'username', 'password')
    s_topnanny.login_on_platform()
    s_topnanny.loop_through_towns()
    s_topnanny.teardown()

    babysits = Platforms.Babysits("username@example.com", "myFancyPassword123")

    s_babysits = Scraper(babysits, 'Database Host', 'DB Name', 'username', 'password')
    s_babysits.login_on_platform()
    s_babysits.loop_through_towns()
    s_babysits.teardown()

    babysitting24 = Platforms.Babysitting24("username@example.com", "myFancyPassword123")

    s_babysitting24 = Scraper(babysitting24, 'Database Host', 'DB Name', 'username', 'password')
    s_babysitting24.login_on_platform()
    s_babysitting24.loop_through_towns()
    s_babysitting24.teardown()

    seniorservice24 = Platforms.Seniorservice24("username@example.com", "myFancyPassword123")

    s_seniorservice24 = Scraper(seniorservice24, 'Database Host', 'DB Name', 'username', 'password')
    s_seniorservice24.login_on_platform()
    s_seniorservice24.loop_through_towns()
    s_seniorservice24.teardown()
