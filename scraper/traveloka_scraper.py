import time
import random
import re
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.action_chains import ActionChains


# ==========================================
# HÀM RANDOM DELAY
# ==========================================

def human_delay(a=2, b=5):
    time.sleep(random.uniform(a, b))


# ==========================================
# HÀM LẤY TEXT AN TOÀN
# ==========================================

def safe_get_text(by, selector):

    try:
        element = driver.find_element(by, selector)

        text = element.text.strip()

        if text:
            return text

        return ""

    except:
        return ""


# ==========================================
# CHROME OPTIONS
# ==========================================

options = webdriver.ChromeOptions()

options.add_argument("--start-maximized")

# né detect bot
options.add_argument("--disable-blink-features=AutomationControlled")

options.add_experimental_option(
    "excludeSwitches",
    ["enable-automation"]
)

options.add_experimental_option(
    "useAutomationExtension",
    False
)

options.add_argument(
    "user-agent=Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/137.0.0.0 Safari/537.36"
)

# ==========================================
# DRIVER
# ==========================================

driver = webdriver.Chrome(
    service=Service(
        ChromeDriverManager().install()
    ),
    options=options
)

driver.execute_script("""
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
})
""")

wait = WebDriverWait(driver, 20)

actions = ActionChains(driver)

# ==========================================
# DATA
# ==========================================

all_data = []

# ==========================================
# PAGE LOOP
# ==========================================

for page in range(1, 2):

    # ==========================================
    # URL
    # ==========================================

    if page == 1:

        url = (
            "https://www.traveloka.com/vi-vn/hotel/"
            "vietnam/region/ho-chi-minh-city-10009794"
            "?viewType=list"
        )

    else:

        url = (
            f"https://www.traveloka.com/vi-vn/hotel/"
            f"vietnam/region/ho-chi-minh-city-10009794/"
            f"{page}?viewType=list"
        )

    print(f"\n===== PAGE {page} =====")

    driver.get(url)

    human_delay(5, 8)

    # ==========================================
    # SCROLL RANDOM
    # ==========================================

    for _ in range(3):

        driver.execute_script(
            f"window.scrollBy(0, {random.randint(300, 800)});"
        )

        human_delay(1, 3)

    # ==========================================
    # LẤY HOTEL CARDS
    # ==========================================

    hotel_cards = wait.until(
        EC.presence_of_all_elements_located(
            (
                By.CSS_SELECTOR,
                "h3[data-testid='popular-hotel-card-name']"
            )
        )
    )

    print(f"Tìm thấy {len(hotel_cards)} khách sạn")

    # ==========================================
    # LOOP HOTEL
    # ==========================================

    for index in range(len(hotel_cards)):

        try:

            # reload card sau khi back
            hotel_cards = wait.until(
                EC.presence_of_all_elements_located(
                    (
                        By.CSS_SELECTOR,
                        "h3[data-testid='popular-hotel-card-name']"
                    )
                )
            )

            card = hotel_cards[index]

            # scroll
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});",
                card
            )

            human_delay(2, 4)

            # hover giống người thật
            actions.move_to_element(card).perform()

            human_delay(1, 2)

            # hotel name
            hotel_name = card.text.strip()

            print(f"\nĐang lấy: {hotel_name}")

            # click
            driver.execute_script(
                "arguments[0].click();",
                card
            )

            human_delay(5, 8)

            # ==========================================
            # URL
            # ==========================================

            hotel_url = driver.current_url

            # ==========================================
            # ADDRESS (FIX)
            # ==========================================

            address = ""

            try:

                address_element = driver.find_element(
                    By.CSS_SELECTOR,
                    "address div.css-901oao"
                )

                address = address_element.text.strip()

            except:
                pass

            # ==========================================
            # STAR
            # ==========================================

            rating_star = ""

            try:

                star_div = driver.find_element(
                    By.CSS_SELECTOR,
                    "div[data-testid='header_star_rating']"
                )

                rating_star = star_div.get_attribute(
                    "data-rating"
                )

            except:
                pass

            # ==========================================
            # PRICE
            # ==========================================

            price = safe_get_text(
                By.CSS_SELECTOR,
                "div[data-testid='overview_cheapest_price']"
            )

            # ==========================================
            # OVERALL SCORE
            # ==========================================

            overall_rating = ""

            try:

                overall_rating = driver.find_element(
                    By.CSS_SELECTOR,
                    "div.r-s67bdx"
                ).text.strip()

            except:
                pass

            # ==========================================
            # REVIEW COUNT (FIX)
            # ==========================================

            review_count = ""

            try:

                review_elements = driver.find_elements(
                    By.XPATH,
                    "//*[contains(text(),'đánh giá')]"
                )

                for el in review_elements:

                    text = el.text.strip()

                    if "đánh giá" in text.lower():

                        match = re.search(
                            r'(\d+)',
                            text
                        )

                        if match:

                            review_count = match.group(1)
                            break

            except:
                pass

            # ==========================================
            # ĐỊA ĐIỂM NỔI BẬT
            # ==========================================

            nearby_places = []

            try:

                location_items = driver.find_elements(
                    By.CSS_SELECTOR,
                    "div[data-testid='summary-location-highlight-list'] > div"
                )

                for item in location_items:

                    texts = item.find_elements(
                        By.CSS_SELECTOR,
                        "div"
                    )

                    if len(texts) >= 2:

                        place_name = texts[-2].text.strip()
                        distance = texts[-1].text.strip()

                        if place_name and distance:

                            nearby_places.append(
                                f"{place_name} ({distance})"
                            )

            except:
                pass

            nearby_places_text = " | ".join(nearby_places)

            # ==========================================
            # CLICK TAB TIỆN ÍCH
            # ==========================================

            try:

                facility_tab = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.CSS_SELECTOR,
                            "div[data-testid='link-FACILITIES']"
                        )
                    )
                )

                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});",
                    facility_tab
                )

                human_delay(2, 4)

                driver.execute_script(
                    "arguments[0].click();",
                    facility_tab
                )

                human_delay(4, 6)

            except:
                print("Không click được tab tiện ích")

            # ==========================================
            # LẤY TOÀN BỘ TIỆN ÍCH
            # ==========================================

            facilities_data = {}

            try:

                facility_sections = driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.r-b8tw3c"
                )

                for section in facility_sections:

                    try:

                        title = section.find_element(
                            By.TAG_NAME,
                            "h3"
                        ).text.strip()

                        items = section.find_elements(
                            By.TAG_NAME,
                            "li"
                        )

                        values = []

                        for item in items:

                            txt = item.text.strip()

                            if txt:
                                values.append(txt)

                        facilities_data[title] = " | ".join(values)

                    except:
                        pass

            except:
                pass

            # ==========================================
            # THÔNG TIN CHUNG
            # ==========================================

            general_info = {}

            try:

                rows = driver.find_elements(
                    By.CSS_SELECTOR,
                    "table tr"
                )

                for row in rows:

                    try:

                        cols = row.find_elements(
                            By.TAG_NAME,
                            "td"
                        )

                        if len(cols) >= 2:

                            key = cols[0].text.strip()
                            value = cols[1].text.strip()

                            if key and value:

                                general_info[key] = value

                    except:
                        pass

            except:
                pass

            # ==========================================
            # CHỈ SỐ ĐÁNH GIÁ CHI TIẾT
            # ==========================================

            review_scores = {}

            try:

                review_blocks = driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.r-29ag51"
                )

                for block in review_blocks:

                    try:

                        texts = block.text.strip().split("\n")

                        if len(texts) >= 2:

                            category = texts[0]
                            score = texts[-1]

                            # bỏ block overall review
                            if category != score:

                                review_scores[category] = score

                    except:
                        pass

            except:
                pass

            # ==========================================
            # DATA ROW
            # ==========================================

            row_data = {

                "hotel_name": hotel_name,
                "hotel_url": hotel_url,

                "address": address,

                "star_rating": rating_star,

                "overall_rating": overall_rating,

                "review_count": review_count,

                "price": price,

                "nearby_places": nearby_places_text
            }

            # add facilities
            for k, v in facilities_data.items():

                row_data[f"facility_{k}"] = v

            # add general info
            for k, v in general_info.items():

                row_data[f"general_{k}"] = v

            # add review scores
            for k, v in review_scores.items():

                row_data[f"score_{k}"] = v

            all_data.append(row_data)

            print("Đã lấy xong")

            # ==========================================
            # BACK
            # ==========================================

            driver.back()

            human_delay(5, 8)

        except Exception as e:

            print("Lỗi:", e)

            try:

                driver.back()

                human_delay(5, 8)

            except:
                pass

# ==========================================
# DATAFRAME
# ==========================================

df = pd.DataFrame(all_data)

# ==========================================
# XÓA TRÙNG
# ==========================================

df = df.drop_duplicates()

# ==========================================
# SAVE EXCEL
# ==========================================

output_file = "traveloka_hotels_full.xlsx"

df.to_excel(
    output_file,
    index=False
)

# ==========================================
# RESULT
# ==========================================

print("\n===== KẾT QUẢ =====")

print(df.head())

print(f"\nTổng số khách sạn: {len(df)}")

print(f"\nĐã lưu file: {output_file}")

# ==========================================
# CLOSE
# ==========================================

driver.quit()