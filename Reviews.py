import uuid
from colorama import Fore, Back, Style


class Reviews:
    def __init__(self, title, original_rating, description, author_id, reviewee_id):
        self.id = uuid.uuid4()
        self.title = title
        self.original_rating = original_rating
        self.description = description
        self.author_id = author_id
        self.reviewee_id = reviewee_id

    def show_review(self):
        print(Fore.YELLOW + "Review ID: " + str(self.id))
        print("Review title: " + str(self.title))
        print("Original Rating: " + str(self.original_rating))
        print("Description: " + str(self.description))
        print("Author ID: " + str(self.author_id))
        print("Reviewee ID: " + str(self.reviewee_id) + Style.RESET_ALL)

    def get_review(self):
        return str(self.id), self.title, self.original_rating, self.description, self.author_id, str(self.reviewee_id)

    def update_reviewee_id(self, reviewee_id):
        self.reviewee_id = reviewee_id
