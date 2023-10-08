import uuid
from datetime import datetime
from enum import Enum
from colorama import Fore, Back, Style


class Gigs:
    def __init__(self, title, type_of_job, created_at, gig_date, gig_url, wage, gig_id, description, author_id, agent_id, platform_id,
                 scraped_at, location_obj):
        self.id = uuid.uuid4()
        self.title = title
        self.type_of_job = type_of_job
        self.created_at = created_at
        self.gig_date = gig_date
        self.gig_url = gig_url
        self.wage = wage
        self.gig_id = gig_id
        self.description = description
        self.author_id = author_id
        self.agent_id = agent_id
        self.platform_id = platform_id
        self.scraped_at = scraped_at
        self.location = location_obj
        self.location_id = location_obj.id

    def show_gig(self):
        print("Gig ID: " + str(self.id))
        print("Title: " + str(self.title))
        print("Type of Job: " + str(self.type_of_job))
        print("Created at: " + str(self.created_at))
        print("Gig Date: " + str(self.gig_date))
        print("Gig URL: " + str(self.gig_url))
        print("wage: " + str(self.wage))
        print("Gig ID on Platform: " + str(self.gig_id))
        print("Gig Description: " + str(self.description))
        print("Author ID: " + str(self.author_id))
        print("Agent ID: " + str(self.agent_id))
        print("Platform ID: " + str(self.platform_id))
        print("Scraped at: " + str(self.scraped_at))
        print("Platform ID: " + str(self.platform_id))
        self.location.show_location()

    def get_gig(self):
        return str(self.id), self.title, str(self.type_of_job), self.created_at, self.gig_date,\
            self.gig_url, self.wage, self.gig_id, self.description, self.author_id, self. agent_id, self.platform_id, \
            self.scraped_at, str(self.location_id)

class Ranking:
    def __init__(self, position_on_site, gig_highlighted, search_query_id, platform_id, gig_id):
        now = datetime.now()
        self.id = uuid.uuid4()
        self.position_on_site = position_on_site
        self.gig_highlighted = gig_highlighted
        self.search_query_id = search_query_id
        self.scraped_at = now.strftime("%d.%m.%Y %H:%M:%S")
        self.platform_id = platform_id
        self.gig_id = gig_id

    def show_ranking(self):
        print(Fore.RED + "Ranking ID: " + str(self.id))
        print("Position on Site: " + str(self.position_on_site))
        print("Gig highlighted: " + str(self.gig_highlighted))
        print("Search Query ID: " + str(self.search_query_id))
        print("Scraped at: " + str(self.scraped_at))
        print("Platform ID: " + str(self.platform_id))
        print("Gig ID: " + str(self.gig_id) + Style.RESET_ALL)

    def update_gig_id(self, gig_id):
        self.gig_id = gig_id

    def get_ranking(self):
        return str(self.id), self.position_on_site, self.gig_highlighted, str(self.search_query_id), self.scraped_at, str(self.platform_id), str(self.gig_id)



class TypeOfJob(Enum):
    CHILDSERVICE = 1
    SENIORSERVICE = 2


if __name__ == '__main__':
    pass
