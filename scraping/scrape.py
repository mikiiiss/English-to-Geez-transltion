# import pandas as pd

# # Read Parquet file
# df = pd.read_parquet('/home/miki/Desktop/NLP/Eng_Geez/0000.parquet')

# # Save as CSV
# df.to_csv('output.csv', index=False)
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
import os
import json
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException

logging.basicConfig(filename='scrape_ethiopic_bible.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_driver():
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(30)
        logging.info("WebDriver initialized successfully.")
        return driver
    except Exception as e:
        logging.error(f"Error setting up WebDriver: {e}")
        raise

def clean_verse_text(text):
    if not text:
        return ""
    return ' '.join(text.strip().split())

def save_chapter_to_json(chapter_data, output_file):
    try:
        if os.path.exists(output_file):
            base, ext = os.path.splitext(output_file)
            output_file = f"{base}_{time.strftime('%Y%m%d_%H%M%S')}{ext}"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chapter_data, f, ensure_ascii=False, indent=2)
        logging.info(f"Successfully saved chapter {chapter_data.get('chapter', 'unknown')} to {output_file}")
    except Exception as e:
        logging.error(f"Error saving chapter to JSON: {e}")

def scrape_chapter(driver, url, output_file):
    try:
        logging.info(f"Navigating to {url}")
        driver.get(url)
        if "captcha" in driver.page_source.lower():
            logging.error(f"CAPTCHA detected at {url}")
            return None

        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".kjvBibleChapterContainer tbody tr"))
        )

        chapter_data = {
            "url": url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "verses": []
        }

        try:
            title_element = driver.find_element(By.CSS_SELECTOR, ".kjvBibleChapterContainer .bookTitle")
            book_text = title_element.text
            chapter_element = title_element.find_element(By.CLASS_NAME, "chapterTitle")
            chapter_text = chapter_element.text
            chapter_data["book"] = book_text.split('Chapter')[0].strip() if 'Chapter' in book_text else book_text.strip()
            chapter_data["chapter"] = chapter_text.replace('Chapter', '').strip()
        except NoSuchElementException:
            logging.warning("Could not extract chapter title")
            chapter_data["book"] = "Unknown"
            chapter_data["chapter"] = "Unknown"

        try:
            geez_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.language.geez"))
            )
            geez_button.click()
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".geezBibleChapterContainer tbody tr"))
            )
            logging.info("Switched to Ge'ez version")
        except Exception as e:
            logging.error(f"Could not switch to Ge'ez version: {e}")
            return None

        english_rows = driver.find_elements(By.CSS_SELECTOR, ".kjvBibleChapterContainer tbody tr")
        geez_rows = driver.find_elements(By.CSS_SELECTOR, ".geezBibleChapterContainer tbody tr")
        
        if len(english_rows) != len(geez_rows):
            logging.error(f"Verse count mismatch: English={len(english_rows)}, Ge'ez={len(geez_rows)}")
            return None

        for eng_row, geez_row in zip(english_rows, geez_rows):
            try:
                verse_num = eng_row.find_element(By.CLASS_NAME, "verseNumCell").text.strip()
                english_text = clean_verse_text(eng_row.find_element(By.CLASS_NAME, "verseContentCell").text)
                geez_text = clean_verse_text(geez_row.find_element(By.CLASS_NAME, "verseContentCell").text)
                chapter_data["verses"].append({
                    "verse": verse_num,
                    "english": english_text,
                    "geez": geez_text
                })
            except Exception as e:
                logging.warning(f"Error processing verse: {e}")
                continue

        logging.info(f"Successfully scraped {len(chapter_data['verses'])} verses")
        return chapter_data

    except TimeoutException:
        logging.error(f"Timeout loading URL or content: {url}")
        return None
    except Exception as e:
        logging.error(f"Error scraping chapter: {e}")
        return None
    finally:
        try:
            english_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.colorizer[value='0']"))
            )
            english_button.click()
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".kjvBibleChapterContainer"))
            )
            logging.info("Switched back to English version")
        except Exception as e:
            logging.warning(f"Could not switch back to English: {e}")

def main():
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    url = "https://www.ethiopicbible.com/books/%E1%8A%A6%E1%88%AA%E1%89%B5-%E1%8B%98%E1%8B%B3%E1%8C%8D%E1%88%9D-10"
    output_file = os.path.join(output_dir, "deuteronomy_chapter_10.json")

    driver = setup_driver()
    try:
        chapter_data = scrape_chapter(driver, url, output_file)
        if chapter_data:
            save_chapter_to_json(chapter_data, output_file)
            logging.info(f"Successfully saved chapter data to {output_file}")
        else:
            logging.error("Failed to scrape chapter data")
    except Exception as e:
        logging.error(f"Error during scraping process: {e}")
    finally:
        driver.quit()
        logging.info("WebDriver closed.")