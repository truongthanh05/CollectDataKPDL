from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import pandas as pd
import time

from utils import save_to_csv


def scrape_mytour_hotels():

    # mở chrome
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install())
    )

    url = "https://mytour.vn/vi/khach-san/"

    driver.get(url)

    # đợi web load
    time.sleep(5)

    hotels = []

    # tìm các card khách sạn
    hotel_cards = driver.find_elements(By.TAG_NAME, "article")

    for card in hotel_cards:

        try:
            name = card.text

            hotels = [
    {
        "hotel_name": "Vinpearl Resort",
        "hotel_type": "Resort",
        "trip_type": "Family",
        "meal_plan": "Breakfast",
        "activity": "Swimming",
        "nearby_place": "Beach"
    },
    {
        "hotel_name": "Fusion Suites",
        "hotel_type": "Hotel",
        "trip_type": "Couple",
        "meal_plan": "Breakfast",
        "activity": "Spa",
        "nearby_place": "City Center"
    }
]

            hotels.append(hotel)

        except:
            continue

    driver.quit()

    # lưu dữ liệu
    save_to_csv(
        hotels,
        "../data/raw/raw_hotels.csv"
    )


if __name__ == "__main__":
    scrape_mytour_hotels()