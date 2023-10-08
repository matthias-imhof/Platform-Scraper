import uuid

from geopy.geocoders import Nominatim
from colorama import Fore, Back, Style



class Locations:
    def __init__(self, address, plz, city, country, latitude, longitude):
        self.id = uuid.uuid4()
        self.address = address
        self.plz = plz
        self.city = city
        self.country = country
        self.latitude = latitude
        self.longitude = longitude

    def show_location(self):
        print(Fore.GREEN + "Location ID: " + str(self.id))
        print("Location Address: " + str(self.address))
        print("Location PLZ: " + str(self.plz))
        print("Location City: " + str(self.city))
        print("Country: " + str(self.country))
        print("Latitude: " + str(self.latitude))
        print("Longitude: " + str(self.longitude) + Style.RESET_ALL)

    def get_location(self):
        return str(self.id), self.address, self.plz, self.city, self.country, self.latitude, self.longitude

    @staticmethod
    def address_from_coordinates(latitude, longitude):
        geolocator = Nominatim(user_agent="Geo Address Generator")
        return geolocator.reverse(latitude + "," + longitude)


if __name__ == '__main__':
    pass
