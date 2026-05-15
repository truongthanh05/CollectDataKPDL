import time
import random
import re
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

import undetected_chromedriver as uc


# ==========================================
# DELAY HUMAN
# ==========================================
def human_delay(a=2, b=5):
    time.sleep(random.uniform(a, b))


# ==========================================
# SAFE GET TEXT
# ==========================================
def safe_get_text(by, selector):
    try:
        el = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((by, selector))
        )
        return el.text.strip() if el.text else ""
    except:
        return ""


# ==========================================
# CHROME OPTIONS (STEALTH BASIC)
# ==========================================
options = uc.ChromeOptions()
options.add_argument("--start-maximized")

options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-first-run")
options.add_argument("--no-default-browser-check")
options.add_argument("--disable-infobars")

# options.add_experimental_option("excludeSwitches", ["enable-automation"])
# options.add_experimental_option("useAutomationExtension", False)


# ==========================================
# DRIVER
# ==========================================
driver = uc.Chrome(options=options, use_subprocess=True)

driver.execute_script("""
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4] });
""")

wait = WebDriverWait(driver, 30)
actions = ActionChains(driver)


# ==========================================
# LIST URL
# ==========================================
# list_url = (
#     "https://www.traveloka.com/vi-vn/hotel/vietnam/region/"
#     "ho-chi-minh-city-10009794?viewType=list"
# )


# ==========================================
# MAIN LOOP PAGE
# ==========================================
for page in range(2, 5):
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

    # scroll nhẹ
    for _ in range(3):
        driver.execute_script(
            f"window.scrollBy(0, {random.randint(300, 800)});"
        )
        human_delay(1, 3)

    hotel_cards = wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "h3[data-testid='popular-hotel-card-name']")
        )
    )

    print(f"Tìm thấy {len(hotel_cards)} khách sạn")

    page_data = []  # 👉 CHỈ DATA CỦA 1 PAGE


    # ==========================================
    # LOOP HOTEL
    # ==========================================
    for index in range(len(hotel_cards)):

        try:
            hotel_cards = wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "h3[data-testid='popular-hotel-card-name']")
                )
            )

            card = hotel_cards[index]
            hotel_name = card.text.strip()

            print(f"\nĐang lấy: {hotel_name}")

            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});",
                card
            )
            human_delay(2, 3)

            actions.move_to_element(card).perform()
            human_delay(1, 2)

            # retry click
            clicked = False
            for _ in range(3):
                try:
                    driver.execute_script("arguments[0].click();", card)
                    clicked = True
                    break
                except:
                    human_delay(1, 2)

            if not clicked:
                print("❌ Click failed")
                continue

            human_delay(5, 8)

            # ==========================================
            # HOTEL INFO
            # ==========================================
            hotel_url = driver.current_url

            address = safe_get_text(By.CSS_SELECTOR, "address div.css-901oao")

            rating_star = ""
            try:
                rating_star = driver.find_element(
                    By.CSS_SELECTOR,
                    "div[data-testid='header_star_rating']"
                ).get_attribute("data-rating")
            except:
                pass

            price = safe_get_text(
                By.CSS_SELECTOR,
                "div[data-testid='overview_cheapest_price']"
            )

            overall_rating = safe_get_text(By.CSS_SELECTOR, "div.r-s67bdx")

            # review count
            review_count = ""
            try:
                els = driver.find_elements(By.XPATH, "//*[contains(text(),'đánh giá')]")
                for el in els:
                    txt = el.text.lower()
                    if "đánh giá" in txt:
                        m = re.search(r'(\d+)', txt)
                        if m:
                            review_count = m.group(1)
                            break
            except:
                pass

            # nearby
            nearby_places = []
            try:
                items = driver.find_elements(
                    By.CSS_SELECTOR,
                    "div[data-testid='summary-location-highlight-list'] > div"
                )
                for item in items:
                    t = item.find_elements(By.CSS_SELECTOR, "div")
                    if len(t) >= 2:
                        name = t[-2].text.strip()
                        dist = t[-1].text.strip()
                        if name and dist:
                            nearby_places.append(f"{name} ({dist})")
            except:
                pass

            nearby_places_text = " | ".join(nearby_places)

            # ==========================================
            # FACILITY TAB
            # ==========================================
            try:
                tab = wait.until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "div[data-testid='link-FACILITIES']")
                    )
                )
                driver.execute_script("arguments[0].click();", tab)
                human_delay(4, 6)
            except:
                print("Không click được tab tiện ích")

            facilities_data = {}
            try:
                sections = driver.find_elements(By.CSS_SELECTOR, "div.r-b8tw3c")
                for sec in sections:
                    try:
                        title = sec.find_element(By.TAG_NAME, "h3").text.strip()
                        items = sec.find_elements(By.TAG_NAME, "li")
                        values = [i.text.strip() for i in items if i.text.strip()]
                        facilities_data[title] = " | ".join(values)
                    except:
                        pass
            except:
                pass

            # general info
            general_info = {}
            try:
                rows = driver.find_elements(By.CSS_SELECTOR, "table tr")
                for r in rows:
                    cols = r.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 2:
                        k = cols[0].text.strip()
                        v = cols[1].text.strip()
                        if k and v:
                            general_info[k] = v
            except:
                pass

            # review scores
            review_scores = {}
            try:
                blocks = driver.find_elements(By.CSS_SELECTOR, "div.r-29ag51")
                for b in blocks:
                    t = b.text.split("\n")
                    if len(t) >= 2:
                        if t[0] != t[-1]:
                            review_scores[t[0]] = t[-1]
            except:
                pass

            # ==========================================
            # SAVE ROW
            # ==========================================
            row = {
                "hotel_name": hotel_name,
                "hotel_url": hotel_url,
                "address": address,
                "star_rating": rating_star,
                "overall_rating": overall_rating,
                "review_count": review_count,
                "price": price,
                "nearby_places": nearby_places_text,
            }

            for k, v in facilities_data.items():
                row[f"facility_{k}"] = v

            for k, v in general_info.items():
                row[f"general_{k}"] = v

            for k, v in review_scores.items():
                row[f"score_{k}"] = v

            page_data.append(row)

            print("✔ Đã lấy xong")

            # ==========================================
            # BACK TO LIST (FIX)
            # ==========================================
            driver.get(url)
            human_delay(5, 8)

        except Exception as e:
            print("❌ Lỗi:", e)
            try:
                driver.get(url)
                human_delay(5, 8)
            except:
                pass


    # ==========================================
    # SAVE SAU MỖI PAGE (APPEND FILE)
    # ==========================================
    new_df = pd.DataFrame(page_data)

    output_file = "traveloka_hotels_full.xlsx"

    try:
        old_df = pd.read_excel(output_file)
        final_df = pd.concat([old_df, new_df], ignore_index=True)
    except:
        final_df = new_df

    final_df = final_df.drop_duplicates(subset=["hotel_url"])

    final_df.to_excel(output_file, index=False)

    print(f"\n✔ Đã lưu PAGE {page}")
    print(f"Tổng dữ liệu: {len(final_df)}")

    time.sleep(random.uniform(10, 20))


# ==========================================
# DONE
# ==========================================
driver.quit()