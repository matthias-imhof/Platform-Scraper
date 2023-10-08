import mysql
from mysql.connector import Error
import uuid
from datetime import date


if __name__ == "__main__":
    try:
        connection = mysql.connector.connect(
            host='Database Host',
            database='DB Name',
            user='username',
            password='password')
        db_Info = connection.get_server_info()
        print("Connected to MySQL Server version ", db_Info)
        cursor = connection.cursor()

        cities = {
            "Zürich": [
                8000, 8001, 8002, 8003, 8004, 8005, 8006, 8008, 8010, 8011, 8012, 8032, 8037, 8038, 8041, 8044, 8045,
                8046, 8047, 8048, 8049, 8050, 8051, 8052, 8053, 8055, 8057, 8063, 8064, 8099
            ],
            "Adliswil": [
                8134
            ],
            "Bassersdorf": [
                8303
            ],
            "Bergdietikon ": [
                8962
            ],
            "Dietikon": [
                8953
            ],
            "Dietlikon": [
                8305
            ],
            "Dübendorf": [
                8600
            ],
            "Erlenbach ZH": [
                8703
            ],
            "Geroldswil": [
                8954
            ],
            "Greifensee": [
                8606
            ],
            "Herrliberg": [
                8704
            ],
            "Horgen": [
                8810
            ],
            "Kilchberg ZH": [
                8802
            ],
            "Kloten": [
                8302
            ],
            "Küsnacht ZH": [
                8700
            ],
            "Langnau am Albis": [
                8135
            ],
            "Oberengstringen": [
                8102
            ],
            "Oberrieden": [
                8942
            ],
            "Oetwil an der Limmat": [
                8955
            ],
            "Opfikon": [
                8152
            ],
            "Rüschlikon ": [
                8803
            ],
            "Schlieren": [
                8952
            ],
            "Schwerzenbach": [
                8603
            ],
            "Thalwil": [
                8800
            ],
            "Unterengstringen": [
                8103
            ],
            "Urdorf": [
                8901, 8902
            ],
            "Volketswil": [
                8604
            ],
            "Wallisellen": [
                8304
            ],
            "Wangen-Brüttisellen": [
                8602, 8306
            ],
            "Weiningen ZH": [
                8104
            ],
            "Zollikon": [
                8702
            ],
            "Zollikerberg": [
                8125
            ],
            "Zumikon": [
                8126
            ],
            "Basel": [
                4000, 4001, 4002, 4005, 4009, 4010, 4018, 4019, 4020, 4030, 4031, 4039, 4040, 4041, 4042, 4051, 4052,
                4053, 4054, 4055, 4056, 4057, 4058, 4059, 4070, 4075, 4089, 4091
            ],
            "Bern": [
                3000, 3001, 3003, 3004, 3005, 3006, 3007, 3008, 3010, 3011, 3012, 3013, 3014, 3015, 3018, 3019, 3020,
                3024, 3027, 3029, 3030
            ],
            "St. Gallen": [
                9000, 9001, 9004, 9006, 9007, 9008, 9010, 9011, 9012, 9014, 9015, 9016, 9020, 9023, 9024, 9026, 9027,
                9028, 9029
            ],
            "Zug": [
                6300, 6301, 6302, 6303
            ],
            "Aarau": [
                5000, 5001, 5004
            ],
            "Schwyz (10km Radius)": [
                6315, 6410, 6414, 6416, 6417, 6418, 6422, 6423, 6424, 6430, 6431, 6432, 6433, 6434, 6436, 6438, 6440,
                6441, 6443, 8840, 8841, 8843, 8849
            ],
            "Altstätten (10km Radius)": [
                9034, 9035, 9036, 9037, 9038, 9042, 9043, 9044, 9050, 9055, 9056, 9405, 9410, 9411, 9413, 9424, 9426,
                9427, 9428, 9430, 9434, 9435, 9436, 9437, 9442, 9443, 9444, 9445, 9450, 9451, 9452, 9453, 9462, 9463,
                9464
            ]

        }

        sql_baseQuery = """INSERT INTO search_query (id, city, plz, radius, filter, scraping_4_PLZ) VALUES (%s, %s, %s, %s, %s, %s)"""

        today = date.today()
        formated_today = today.strftime("%d.%m.%Y")

        for city in cities:
            print("**********")
            for plz in cities[city]:
                random_uuid = uuid.uuid4()
                data = [
                    str(random_uuid),
                    city,
                    plz,
                    0,
                    "Automatically added by LoadCitiesIntoDB Helper Program on: " + str(formated_today),
                    True
                ]
                print([data,])
                cursor.executemany(sql_baseQuery, [data, ])

            print("**********")
        connection.commit()



    except Error as e:
        print("Error while connecting to MySQL", e)


    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")