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
from bs4 import BeautifulSoup
import time
import logging
import os
import json
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    filename='scrape_ethiopic_bible.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def setup_driver():
    """Set up Selenium WebDriver with Chrome."""
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        logging.info("WebDriver initialized successfully.")
        return driver
    except Exception as e:
        logging.error(f"Error setting up WebDriver: {e}")
        raise

def clean_verse_text(text):
    """Clean verse text by removing extra whitespace and normalizing."""
    if not text:
        return ""
    return ' '.join(text.strip().split())

def save_chapter_to_json(chapter_data, output_file):
    """Save chapter data to JSON file."""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Write data to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chapter_data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Successfully saved chapter {chapter_data.get('chapter', 'unknown')} to JSON file.")
    except Exception as e:
        logging.error(f"Error saving chapter to JSON: {e}")

def scrape_chapter(driver, url, output_file):
    """Scrape English and Ge'ez versions of a Bible chapter."""
    try:
        logging.info(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for the main content to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "mainChapterContainer"))
        )
        
        # Initialize chapter data structure
        chapter_data = {
            "url": url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "verses": []
        }

        # Extract chapter title (English)
        try:
            title_element = driver.find_element(By.CSS_SELECTOR, ".kjvBibleChapterContainer .bookTitle")
            chapter_data["book"] = title_element.text.split('Chapter')[0].strip()
            chapter_data["chapter"] = title_element.find_element(By.CLASS_NAME, "chapterTitle").text.replace('Chapter', '').strip()
        except Exception as e:
            logging.warning(f"Could not extract chapter title: {e}")

        # Click Ge'ez button to show Ge'ez version
        try:
            geez_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.language.geez"))
            )
            geez_button.click()
            time.sleep(2)  # Wait for content to load
            logging.info("Switched to Ge'ez version")
        except Exception as e:
            logging.error(f"Could not switch to Ge'ez version: {e}")
            return None

        # Extract verses from both versions
        try:
            # Get English verses
            english_rows = driver.find_elements(By.CSS_SELECTOR, ".kjvBibleChapterContainer tbody tr")
            
            # Get Ge'ez verses
            geez_rows = driver.find_elements(By.CSS_SELECTOR, ".geezBibleChapterContainer tbody tr")
            
            if len(english_rows) != len(geez_rows):
                logging.warning(f"Mismatch in verse counts: English={len(english_rows)}, Ge'ez={len(geez_rows)}")

            for eng_row, geez_row in zip(english_rows, geez_rows):
                try:
                    verse_num = eng_row.find_element(By.CLASS_NAME, "verseNumCell").text.strip()
                    english_text = clean_verse_text(eng_row.find_element(By.CLASS_NAME, "verseConentCell").text)
                    geez_text = clean_verse_text(geez_row.find_element(By.CLASS_NAME, "verseConentCell").text)
                    
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

        except Exception as e:
            logging.error(f"Error extracting verses: {e}")
            return None

    except Exception as e:
        logging.error(f"Error scraping chapter: {e}")
        return None
    finally:
        # Switch back to English version for consistency
        try:
            english_button = driver.find_element(By.CSS_SELECTOR, "button.colorizer[value='0']")
            english_button.click()
            time.sleep(1)
        except:
            pass

def main():
    # Configuration
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Example URL (Deuteronomy Chapter 10)
    url = "https://www.ethiopicbible.com/books/%E1%8A%A6%E1%88%AA%E1%89%B5-%E1%8B%98%E1%8B%B3%E1%8C%8D%E1%88%9D-10"
    output_file = os.path.join(output_dir, "deuteronomy_chapter_10.json")

    driver = setup_driver()
    try:
        # Scrape the chapter
        chapter_data = scrape_chapter(driver, url, output_file)
        
        if chapter_data:
            # Save the results
            save_chapter_to_json(chapter_data, output_file)
            logging.info(f"Successfully saved chapter data to {output_file}")
        else:
            logging.error("Failed to scrape chapter data")

    except Exception as e:
        logging.error(f"Error during scraping process: {e}")
    finally:
        driver.quit()
        logging.info("WebDriver closed.")

if __name__ == "__main__":
    main()