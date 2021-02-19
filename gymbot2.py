import pyrebase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from datetime import date
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")


config = {
    "apiKey": "*****",
    "authDomain": "*****",
    "databaseURL": "*****",
    "projectId": "*****",
    "storageBucket": "*****",
    "messagingSenderId": "*****",
    "appId": "*****",
    "measurementId": "*****",
    "serviceAccount": "*****"
}
firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
user = auth.sign_in_with_email_and_password("*****", "*****")
db = firebase.database()


class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password


east_room = "https://fitnessonline.asu.edu/booking/3a910bb2-d3a2-4bf6-9cb6-fd56d09df21c"
west_room = "https://fitnessonline.asu.edu/booking/18cabec8-0fda-445b-bd3d-b3f03256736f"
two_bay = "https://fitnessonline.asu.edu/booking/3b06e0d8-62ad-4714-a964-972edd4c86ce"

user_list = []

def book_slot(username, password, default_gym, default_time):
    try:
        options = Options()
        # options.add_argument('--headless')
        # options.add_argument('--disable-gpu')

        driver = webdriver.Chrome(options=options)
        driver.get("https://fitnessonline.asu.edu/booking")
        driver.implicitly_wait(10)

        weightbutton = driver.find_element_by_class_name(
            'container-image-link-item')
        weightbutton.click()

        loginbutton = driver.find_element_by_class_name('loginOption')
        loginbutton.click()

        usernameinput = driver.find_element_by_id('username')
        usernameinput.clear()
        usernameinput.send_keys(username)

        passwordinput = driver.find_element_by_id('password')
        passwordinput.clear()
        passwordinput.send_keys(password)

        submitbutton = driver.find_element_by_class_name('btn-submit')
        submitbutton.click()

        error = driver.find_elements_by_class_name('error')
        if len(error) > 0:
            print("Invalid username/password")
            db.child('callback').child(username).set(999)
            driver.close()
            return

        driver.get(default_gym)

        second_day = driver.find_elements_by_class_name(
            'single-date-select-one-click')
        second_day[1].click()

        timeslots = driver.find_elements_by_class_name('booking-slot-item')
        try:
            time = slot.find_element_by_tag_name(
                'strong').get_attribute('innerHTML')
        except:
            timeslots = driver.find_elements_by_class_name('booking-slot-item')

        print("\nSearching for time slots...\n")
        for slot in timeslots:
            time = slot.find_element_by_tag_name(
                'strong').get_attribute('innerHTML')
            if (time == default_time):
                print("FOUND TIME SLOT: " + default_time)
                try:
                    bookbutton = slot.find_element_by_class_name('btn-primary')
                    text = bookbutton.get_attribute('innerHTML')
                    print(text)
                    if (text == "Book Now"):
                        print("Time slot is available! Booking...")
                        bookbutton.click()
                        print("Booked!")
                        db.child('callback').child(username).set(1)
                        break
                    else:
                        print("Time slot is not available...")
                        db.child('callback').child(username).set(2)
                except NoSuchElementException:
                    print("You booked this slot already!")
                    db.child('callback').child(username).set(3)

        driver.close()
    except:
        print('something went wrong...')

        db.child('callback').child(username).set(0)

def load_users():
    snapshots = db.child('users').get()
    for snapshot in snapshots.each():
        username = snapshot.key()
        password = snapshot.val()
        user = User(username, password)
        user_list.append(user)


load_users()


def iterate_through_users():
    today = date.today()
    month = str(today.month - 1)
    day = str(today.day + 1)
    date_string = month + '-' + day
    for user in user_list:
        gymsnap = db.child('slots').child(date_string).child(user.username).child('gym').get()
        timesnap = db.child('slots').child(date_string).child(user.username).child('time').get()

        gym = gymsnap.val()
        time = timesnap.val()
        print(gym)
        if gym is None:
            print('no slots for user: ' + user.username)
        else:
            default_gym = ""
            if (gym == 'east'):
                default_gym = east_room
            elif (gym == 'west'):
                default_gym = west_room
            else:
                default_gym = two_bay

            book_slot(user.username, user.password, default_gym, time)

iterate_through_users()
