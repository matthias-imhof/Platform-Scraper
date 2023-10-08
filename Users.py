import uuid
from enum import Enum
from colorama import Fore, Back, Style

from datetime import datetime


class Users:

    def __init__(self, firstname, lastname, role, joined_on, last_online, response_time_hours, age, gender,
                 race, profile_description, wage, normalized_rating, original_rating, profile_id, picture_url,
                 profile_url, gigs, has_documents_uploaded, has_references, verified, favorised,
                 professional_subscription,
                 experience_in_years, spoken_languages, scraped_at,
                 platform_id, location_obj):
        self.id = uuid.uuid4()
        self.firstname = firstname
        self.lastname = lastname
        self.role = role
        self.joined_on = joined_on
        self.last_online = last_online
        self.response_time_hours = response_time_hours
        self.age = age
        self.gender = gender
        self.race = race
        self.profile_description = profile_description
        self.wage = wage
        self.normalized_rating = normalized_rating
        self.original_rating = original_rating
        self.profile_id = profile_id
        self.picture_url = picture_url
        self.profile_url = profile_url
        self.gigs = gigs
        self.has_documents_uploaded = has_documents_uploaded
        self.has_references = has_references
        self.verified = verified
        self.favorised = favorised
        self.professional_subscription = professional_subscription
        self.experience_in_years = experience_in_years
        self.spoken_languages = spoken_languages
        self.scraped_at = scraped_at
        self.platform_id = platform_id
        self.location = location_obj
        self.location_id = location_obj.id

    def __eq__(self, other):
        return (self.firstname.lower() == other.firstname.lower()) & (
                self.profile_url.lower() == other.profile_url.lower())

    def show_user(self):
        print("User ID: " + str(self.id))
        print("Firstname: " + str(self.firstname))
        print("Lastname: " + str(self.lastname))
        print("Role: " + str(self.role))
        print("Joined on: " + str(self.joined_on))
        print("Last online: " + str(self.last_online))
        print("Response time: " + str(self.response_time_hours))
        print("Age: " + str(self.age))
        print("Gender: " + str(self.gender))
        print("Race: " + str(self.race))
        print("Profile Description: " + str(self.profile_description))
        print("Wage: " + str(self.wage))
        print("Normalized Rating: " + str(self.normalized_rating))
        print("Original Rating: " + str(self.original_rating))
        print("Profile ID: " + str(self.profile_id))
        print("Profile URL: " + str(self.profile_url))
        print("Picture URL: " + str(self.picture_url))
        print("# Gigs: " + str(self.gigs))
        print("Has Documents Uploaded: " + str(self.has_documents_uploaded))
        print("Has References: " + str(self.has_references))
        print("Profile verified: " + str(self.verified))
        print("# Favorised: " + str(self.favorised))
        print("Professional Subscription: " + str(self.professional_subscription))
        print("Experience in years: " + str(self.experience_in_years))
        print("Spoken languages: " + str(self.spoken_languages))
        print("scrapped at: " + str(self.scraped_at))
        print("Platform ID: " + str(self.platform_id))
        self.location.show_location()

    def get_user(self):
        return str(self.id), self.firstname, self.lastname, str(self.role), self.joined_on, self.last_online, \
            self.response_time_hours, self.age, self.gender, self.race, self.profile_description, self.wage, self.normalized_rating, self.original_rating, \
            self.profile_id, self.picture_url, self.profile_url, self.gigs, self.has_documents_uploaded, self.has_references, self.verified, \
            self.favorised, self.professional_subscription, self.experience_in_years, self.spoken_languages, self.scraped_at, \
            self.platform_id, str(self.location_id)

    @staticmethod
    def calculate_birthdate(birthdate):
        pass


class Ranking:
    def __init__(self, position_on_site, profile_highlighted, search_query_id, platform_id, user_id):
        now = datetime.now()
        self.id = uuid.uuid4()
        self.position_on_site = position_on_site
        self.profile_highlighted = profile_highlighted
        self.search_query_id = search_query_id
        self.scraped_at = now.strftime("%d.%m.%Y %H:%M:%S")
        self.platform_id = platform_id
        self.user_id = user_id

    def show_ranking(self):
        print(Fore.RED + "Ranking ID: " + str(self.id))
        print("Position on Site: " + str(self.position_on_site))
        print("Profile highlighted: " + str(self.profile_highlighted))
        print("Search Query ID: " + str(self.search_query_id))
        print("Scraped at: " + str(self.scraped_at))
        print("Platform ID: " + str(self.platform_id))
        print("User ID: " + str(self.user_id) + Style.RESET_ALL)

    def update_user_id(self, user_id):
        self.user_id = user_id

    def get_ranking(self):
        return str(self.id), self.position_on_site, self.profile_highlighted, str(
            self.search_query_id), self.scraped_at, str(self.platform_id), str(self.user_id)


class Role(Enum):
    AGENT = 1
    PRINCIPAL = 2
    REVIEWER = 3
    REFERENCER = 4


if __name__ == '__main__':
    pass
