from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import date, timedelta
import requests
import os
import re
import time

def download_image(url, folder, filename):
    try:
        os.makedirs(folder, exist_ok=True)
        filepath = os.path.join(folder, filename)
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(r.content)
            return filepath
    except Exception as e:
        print(f"⚠ Error downloading image {url}: {e}")
    return None

def scrape_booking(property_type):
    type_map = {
        "hotel": "ht_id=204",
        "apartment": "ht_id=201",
        "home": "ht_id=220"
    }

    if property_type.lower() not in type_map:
        print("❌ Invalid property type. Please choose: hotel, apartment, home")
        return

    filter_code = type_map[property_type.lower()]
    max_pages = None  # No limit on pages
    stay_length = 2
    results = []
    scraped_names = set()  # To avoid duplicates based on hotel name

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        start_date = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=365)

        current_date = start_date
        while current_date <= end_date:
            checkin_date = current_date.strftime("%Y-%m-%d")
            checkout_date = (current_date + timedelta(days=stay_length)).strftime("%Y-%m-%d")

            print(f"\n🔍 Searching {property_type}s for {checkin_date} → {checkout_date}")

            page_url = (
                f"https://www.booking.com/searchresults.en-gb.html?"
                f"checkin={checkin_date}&checkout={checkout_date}&selected_currency=USD"
                f"&ss=Pakistan&group_adults=1&no_rooms=1&group_children=0&nflt={filter_code}"
            )
            page.goto(page_url, timeout=60000, wait_until='domcontentloaded')

            # New approach to get total properties count
            try:
                page.wait_for_selector('div[data-testid="results"]', timeout=15000)
                page_content = page.inner_text('body')
                match = re.search(r'([\d,]+)\s+(properties|hotels|accommodations|places)', page_content, re.I)
                if match:
                    total_properties = int(match.group(1).replace(',', ''))
                    print(f"📊 Total properties found: {total_properties}")
                else:
                    print("⚠ Total properties count text not found.")
            except Exception as e:
                print("⚠ Could not find total properties count:", e)

            page_number = 1
            while max_pages is None or page_number <= max_pages:
                print(f"📄 Scraping page {page_number} for {checkin_date}")

                try:
                    page.wait_for_selector('div[data-testid="property-card"]', timeout=15000)
                except:
                    print("⚠ No properties found for this date.")
                    break

                hotels = page.locator('div[data-testid="property-card"]')
                count = hotels.count()

                for i in range(count):
                    card = hotels.nth(i)

                    hotel_name = card.locator('div[data-testid="title"]').inner_text() if card.locator('div[data-testid="title"]').count() else None
                    if not hotel_name or hotel_name in scraped_names:
                        continue  # Skip duplicate or missing names
                    scraped_names.add(hotel_name)

                    price = card.locator('span[data-testid="price-and-discounted-price"]').inner_text() if card.locator('span[data-testid="price-and-discounted-price"]').count() else None

                    try:
                        score = card.locator('div[aria-label*="Scored"]').inner_text()
                    except:
                        score = None

                    try:
                        avg_review = card.locator('div[class*="f4d1db90c4"]').nth(0).inner_text()
                    except:
                        avg_review = None

                    try:
                        reviews_count_text = card.locator('div[class*="a91bd87e91"]').inner_text()
                        reviews_count = re.search(r'(\d+)', reviews_count_text).group(1) if reviews_count_text else None
                    except:
                        reviews_count = None

                    location = card.locator('span[data-testid="address"]').inner_text() if card.locator('span[data-testid="address"]').count() else None
                    image_url = card.locator('img').get_attribute("src") if card.locator('img').count() else None

                    image_path = None
                    if image_url and hotel_name:
                        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', hotel_name)
                        folder = f"images_{property_type}"
                        filename = f"{safe_name}_{checkin_date}.jpg"
                        image_path = download_image(image_url, folder, filename)

                    results.append({
                        "Property Type": property_type,
                        "Check-in": checkin_date,
                        "Check-out": checkout_date,
                        "Name": hotel_name,
                        "Price": price,
                        "Score": score,
                        "Average Review": avg_review,
                        "Reviews Count": reviews_count,
                        "Location": location,
                        "Image URL": image_url,
                        "Image Path": image_path
                    })

                next_button = page.locator('button[aria-label="Next page"]')
                if next_button.count() == 0 or not next_button.is_enabled():
                    break
                next_button.click()
                page.wait_for_selector('div[data-testid="property-card"]', timeout=15000)
                page_number += 1
                time.sleep(2)

            current_date += timedelta(days=7)
            time.sleep(3)

        df = pd.DataFrame(results)
        df.to_excel(f'pakistan_{property_type}_1year.xlsx', index=False)
        df.to_csv(f'pakistan_{property_type}_1year.csv', index=False)
        print(f"✅ Scraped {len(results)} unique {property_type} entries for 1 year with images downloaded.")

        browser.close()

if __name__ == "__main__":
    user_type = input("Enter property type (hotel/apartment/home): ")
    scrape_booking(user_type)
