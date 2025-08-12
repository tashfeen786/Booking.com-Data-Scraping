from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import pandas as pd
import time
import re
import os
import requests

HEADLESS = False
DOWNLOAD_IMAGES = True
SCROLL_PAUSE = 3
MAX_SCROLLS = 60
OUTPUT_PREFIX = "pakistan"
PROPERTY_TYPE_MAP = {
    "hotel": "ht_id=204",
    "apartment": "ht_id=201",
    "home": "ht_id=220"
}

CITIES = [
    "Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad", "Multan",
    "Peshawar", "Quetta", "Sialkot", "Gujranwala", "Bahawalpur", "Sukkur",
    "Hyderabad", "Muzaffarabad", "Sargodha", "Sahiwal", "Dera Ghazi Khan",
    "Mardan", "Kasur", "Sheikhupura", "Okara", "Jhelum",
    "Hunza", "Skardu", "Khaplu"
]

def safe_filename(s, maxlen=120):
    if not s:
        return "no_name"
    s = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', s)
    return s[:maxlen]

def download_image(url, folder, filename):
    if not DOWNLOAD_IMAGES or not url:
        return None
    try:
        os.makedirs(folder, exist_ok=True)
        filepath = os.path.join(folder, filename)
        if os.path.exists(filepath):
            return filepath
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(r.content)
            return filepath
    except Exception as e:
        print(f"⚠ Image download error: {e}")
    return None

def scrape_city(page, property_type, city):
    filter_code = PROPERTY_TYPE_MAP[property_type.lower()]
    results = []

    base_url = (
        f"https://www.booking.com/searchresults.en-gb.html?"
        f"ss={city}&group_adults=1&no_rooms=1&group_children=0&nflt={filter_code}"
    )
    print(f"\n🔗 Opening city: {city}")
    page.goto(base_url, timeout=60000)

    previous_height = None
    scrolls = 0
    while scrolls < MAX_SCROLLS:
        scrolls += 1
        print(f"⏳ Scrolling attempt {scrolls} for {city}")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE)

        current_height = page.evaluate("document.body.scrollHeight")
        if previous_height == current_height:
            print(f"⚠ No new content loaded for {city}, scrolling complete.")
            break
        previous_height = current_height

    try:
        page.wait_for_selector('div[data-testid="property-card"]', timeout=15000)
    except PlaywrightTimeoutError:
        print(f"⚠ No properties found for {city}")
        return results

    cards = page.locator('div[data-testid="property-card"]')
    count = cards.count()
    print(f"✅ Total loaded properties for {city}: {count}")

    for i in range(count):
        try:
            card = cards.nth(i)
            name = card.locator('div[data-testid="title"]').inner_text().strip() if card.locator('div[data-testid="title"]').count() else None
            price = card.locator('span[data-testid="price-and-discounted-price"]').inner_text().strip() if card.locator('span[data-testid="price-and-discounted-price"]').count() else None
            rating = None
            if card.locator('div[data-testid="review-score"]').count():
                try:
                    rating = card.locator('div[data-testid="review-score"]').inner_text().strip().split("\n")[0]
                except:
                    rating = None
            reviews_count = None
            if card.locator('div[data-testid="review-score"]').count():
                try:
                    rtxt = card.locator('div[data-testid="review-score"]').inner_text()
                    m = re.search(r'\d+', rtxt.replace(',', ''))
                    if m:
                        reviews_count = m.group()
                except:
                    reviews_count = None
            location = card.locator('span[data-testid="address"]').inner_text().strip() if card.locator('span[data-testid="address"]').count() else None
            image_url = None
            try:
                img = card.locator('img')
                if img.count():
                    image_url = img.get_attribute("src") or img.get_attribute("data-src") or img.get_attribute("data-lazy")
            except:
                image_url = None

            image_path = None
            if image_url and name and DOWNLOAD_IMAGES:
                folder = f"images_{property_type}"
                filename = safe_filename(name) + ".jpg"
                image_path = download_image(image_url, folder, filename)

            results.append({
                "City": city,
                "Property Type": property_type,
                "Name": name,
                "Price": price,
                "Rating": rating,
                "Reviews Count": reviews_count,
                "Location": location,
                "Image URL": image_url,
                "Image Path": image_path
            })
        except Exception as e:
            print(f"⚠ Error scraping card {i} in {city}: {e}")
            continue

    return results

def scrape_all_cities(property_type):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        page = browser.new_page()
        page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/115.0.0.0 Safari/537.36")
        })

        all_results = []
        for city in CITIES:
            city_results = scrape_city(page, property_type, city)
            all_results.extend(city_results)
            time.sleep(5)

        browser.close()

    df = pd.DataFrame(all_results)
    if not df.empty:
        # Remove duplicates based on Name + Location
        df.drop_duplicates(subset=['Name', 'Location'], inplace=True)

    out_xlsx = f"{OUTPUT_PREFIX}_{property_type}_all_cities.xlsx"
    out_csv = f"{OUTPUT_PREFIX}_{property_type}_all_cities.csv"
    df.to_excel(out_xlsx, index=False)
    df.to_csv(out_csv, index=False)

    print(f"\n✅ Total unique {property_type}s scraped across {len(CITIES)} cities: {len(df)}")
    print("Files saved:", out_xlsx, "|", out_csv)


if __name__ == "__main__":
    user_type = input("Enter property type (hotel/apartment/home): ").strip().lower()
    if user_type not in PROPERTY_TYPE_MAP:
        print("❌ Invalid property type. Choose from hotel, apartment, home.")
    else:
        scrape_all_cities(user_type)
