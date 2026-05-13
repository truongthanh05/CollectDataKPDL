from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import time

from utils import save_to_csv


def scrape_klook_activities():

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install())
    )

    url = "https://www.klook.com/vi/"

    driver.get(url)

    time.sleep(5)

    activities = []

    cards = driver.find_elements(By.TAG_NAME, "a")

    for card in cards[:50]:

        try:

            activity = {
                "activity_name": card.text,
                "activity_type": "Tour",
                "price_range": "Medium",
                "location": "Da Nang"
            }

            activities.append(activity)

        except:
            continue

    driver.quit()

    save_to_csv(
        activities,
        "../data/raw/raw_activities.csv"
    )


if __name__ == "__main__":
    scrape_klook_activities()