from abc import ABC, abstractmethod

class Platforms(ABC):
    def __init__(self, username, password, website, loginpage, login_username_class_id, login_password_class_id,
                 login_button_name, logout_button_name, searchfield_id, search_button_id):
        self.__username = username
        self.__password = password
        self.website = website
        self.loginpage = loginpage
        self.login_username_class_id = login_username_class_id
        self.login_password_class_id = login_password_class_id
        self.login_button_name = login_button_name
        self.logout_button_name = logout_button_name
        self.searchfield_id = searchfield_id
        self.search_button_id = search_button_id

        self.min_rating_reviews = 0
        self.max_rating_reviews = 0

        self.min_rating_references = 0
        self.max_rating_references = 0

        self.min_rating_users = 0
        self.max_rating_users = 0

        self.metadata = ""

    def get_login(self):
        return self.__username, self.__password

    @abstractmethod
    def run(self):
        pass


class Babysits(Platforms):
    def __init__(self, username, password):
        super().__init__(username, password, "https://www.babysits.ch", "https://www.babysits.ch/einloggen/",
                         "continueEmail", 'loginPassword', "//div[@id='auth']", "",
                         "", "")

        self.second_login_button_name = 'mb-4'
        self.agent_website = 'https://www.babysits.ch/babysitter/'
        self.principal_website = 'https://www.babysits.ch/babysitting/'
        self.search_button_name = "search-expandable"
    def run(self):
        pass


class Babysitting24(Platforms):
    def __init__(self, username, password):
        super().__init__(username, password, "https://babysitting24.ch/de", "https://babysitting24.ch/de/sign_in",
                         "user_login", "user_password", "commit", "", "", "")

    def run(self):
        pass


class Seniorservice24(Platforms):
    def __init__(self, username, password):
        super().__init__(username, password, "https://seniorservice24.ch/de", "https://seniorservice24.ch/de/sign_in",
                         "user_login", "user_password", "commit", "", "", "")

    def run(self):
        pass


class TopNanny(Platforms):
    def __init__(self, username, password):
        super().__init__(username, password, "https://topnanny.ch/de", "https://topnanny.ch/de/sessions/new",
                         "email", "password", "commit", "", "geofield_search", "commit")

    def run(self):
        pass


if __name__ == '__main__':
    pass
