# Booking.com-Data-Scraping

# 🏨 Booking.com Accommodation Scraper (1-Year Data)

This project is a **Python + Playwright** based web scraper for **Booking.com** that collects accommodation details for **up to 1 year** in advance for different property types (Hotel, Apartment, Resort, Hostel, Villa, Guesthouse).  
It saves results in **CSV** and **Excel** formats and downloads property images locally, with the option to embed them directly into Excel.

---

## 📌 Features

- 🔍 Search properties on **Booking.com** for an entire year, checking weekly availability.
- 🏠 Supports multiple property types:
  - Hotel  
  - Apartment  
  - Resort  
  - Hostel  
  - Villa  
  - Guesthouse
- 📅 Automatically loops through weekly date ranges.
- 💰 Extracts:
  - Property name
  - Price
  - Review score
  - Average review text
  - Number of reviews
  - Location
  - Image URL
- 🖼 Saves images locally & stores the local path in CSV.
- 📊 Saves results as:
  - **CSV** (with local image paths)
  - **Excel** (with embedded images)

---

## 📂 Project Structure
Booking-Scraper/
│
├── images_hotel/ # Downloaded hotel images
├── images_apartment/ # Downloaded apartment images
│
├── pakistan_hotel_1year.csv # Output CSV
├── pakistan_hotel_1year.xlsx # Output Excel with embedded images
│
├── main.py # Main scraper script
├── requirements.txt # Python dependencies
└── README.md # Project documentation
---

## 🛠 Installation

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/booking-scraper.git
cd booking-scraper

📌 Notes
The script runs in non-headless mode so you can watch the scraping process.

Image embedding in Excel may slightly increase file size.

The project is for educational purposes only. Please respect the website's terms of service.

🏗 Future Improvements
Add proxy rotation for large-scale scraping.

Support multiple countries instead of fixed "Pakistan".

Add multi-threading for faster scraping.

📜 License
This project is licensed under the MIT License — feel free to use and modify it.

