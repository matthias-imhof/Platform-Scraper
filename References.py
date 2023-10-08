import uuid
from colorama import Fore, Back, Style


class References:
    def __init__(self, title, firstname, lastname, description, relationship, author_id, referencee_id):
        self.id = uuid.uuid4()
        self.title = title
        self.firstname = firstname
        self.lastname = lastname
        self.description = description
        self.relationship = relationship
        self.author_id = author_id
        self.referencee_id = referencee_id

    def show_reference(self):
        print(Fore.CYAN + "Reference ID: " + str(self.id))
        print("Reference title: " + str(self.title))
        print("Firstname: " + str(self.firstname))
        print("Lastname: " + str(self.lastname))
        print("Description: " + str(self.description))
        print("Relationship: " + str(self.relationship))
        print("Author ID: " + str(self.author_id))
        print("Referencee ID: " + str(self.referencee_id) + Style.RESET_ALL)

    def get_reference(self):
        return str(self.id), self.title, self.firstname, self.lastname, self.description, \
            self.relationship, self.author_id, str(self.referencee_id)

    def update_referencee_id(self, referencee_id):
        self.referencee_id = referencee_id
