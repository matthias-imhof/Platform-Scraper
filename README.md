# Scrapper for Swiss Freelancing Platforms

Made in Zürich with love! 
Made by a Student of the departments of Informatics @ UZH for his Bachelor Thesis.

## Introduction

This project aims to collect data to measure the supply and demand of work and workers on Swiss freelancing websites in the care sector, such as [TopNanny / TopHelp](https://topnanny.ch/de), [Babysits](https://babysits.ch), [Babysitting24](https://babysitting24.ch/de) and [Seniorservice24](https://seniorservice24.ch/de). It stores the scraped data in a structured way in a relational MySQL database for later analysis. 

## Technologies & Blueprint

* Python 3.11

* Selenium with Chromium drivers (`version: 114.0.5735.90`) 

* MySQL `version: 5.7` as the database

* Runs on macOS and Windows (tested on macOS 13.4 and on Windows 11 Pro 22H2)

* [Genderize.io](https://genderize.io/) to classify the gender based on the first name of the user

### Additional Libraries

* uuid (uuid4) are used as identifiers for the objects and to save in the database

* tqdm to display the status bar in the console nicely

* colorama to change the colour in the console

* Nominatim to convert the latitude and the longitude of users into addresses 

## Requirements

* MySQL database with the appropriate schema and tables. For ease of use, look at the [Database4Platforms.sql](Database4Platforms.sql) to set up the database with the Schema used for this project.
* The above libraries must be installed either in the project virtual environment or in the interpreter system-wide. 

## Setup and run

1. Load the cities into the database. For ease of use, the [LoadCitiesIntoDB.py](LoadCitiesIntoDB.py) provides you with a script to automatically load the cities into your DB. Of course, you can also manually insert the cities with their corresponding PLZ into the DB. If you use the referenced file, remember to provide the correct database, username and password.

2. Initialize the database and the scraping account. This must be done for each Platform in the [Scraper.py](Scraper.py) class (see above for all supported platforms).

```python
if __name__ == '__main__':
    # instantiate each Platform with the account for the scrapper to work with (must be manualy created)
    topnanny = Platforms.TopNanny("username@example.com", "myFancyPassword123")

    # instantiate the scraper for each platform
    # pass the initialized platform and the Database to use (remember MySQL)
    s_topnanny = Scraper(topnanny, 'Database Host', 'DB Name', 'username', 'password')
    s_topnanny.login_on_platform()
    s_topnanny.loop_through_towns()
    s_topnanny.teardown()
```

## Statistics

Here are some statistics about how long it takes to run on the platforms and how much data it collects. 

Each individual platform was scraped one after another on a Windows 11 Pro machine with the following specification:

- Intel Core i7-11700K

- 64 GB @ 3200 MHz

| Platform        | Time to  Scrape            | # Rankings for Gigworkers | # Gigworkers | # Rankings  for Gigs | # Gigs |
|:---------------:|:--------------------------:|:-------------------------:|:------------:|:--------------------:|:------:|
| TopNanny        | 2 days 18 hours 3 minutes  | 22,719                    | 1,137        | 3,658                | 185    |
| Babysits        | 8 hours 17 minutes         | 5,537                     | 757          | 1,565                | 225    |
| Babysitting24   | 2 days 1 hour 45 minutes   | 23,471                    | 8,656        | 6,715                | 3,988  |
| Seniorservice24 | 8 hours  43 minutes        | 4,835                     | 1,815        | 158                  | 76     |
| Total           | 5 days 12 hours 48 minutes | 56,562                    | 12,365       | 12,096               | 4,474  |

## Additional Work

- [ ] More platforms such as [yoopies](https://yoopies.ch), [rockmybaby](https://rockmybaby.ch), [MisGrosi](https://www.misgrosi.ch) etc.

- [ ] Multi-language support for scrapping accounts (currently, only DE is supported). This is only important if one is observing the scraper; everything is shown in German. Changing this to other Languages requires some smaller refactorings in [Scraper.py](Scraper.py)

- [ ] Make Linux compatible

## Authors and acknowledgements

[Matthias Imhof](https://github.com/matthias-imhof)

## License

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
