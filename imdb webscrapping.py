from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time, os
def get_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver
def scrape_imdb_top_movies():
    print("Starting IMDb Scraper")
    driver = get_driver(headless=False)
    driver.get("https://www.imdb.com/chart/top/")
    time.sleep(5)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    page_source = driver.page_source
    driver.quit()
    soup = BeautifulSoup(page_source, "html.parser")
    movies = soup.select("li.ipc-metadata-list-summary-item")[:250]

    titles, years, ratings, urls = [], [], [], []

    for m in movies:
        try:
            title_tag = m.select_one("h3.ipc-title__text")
            title = title_tag.text.strip() if title_tag else "N/A"
            year_tag = m.select_one("span.cli-title-metadata-item")
            year = year_tag.text.strip() if year_tag else "N/A"
            rating_tag = m.select_one("span.ipc-rating-star--rating")
            rating = rating_tag.text.strip() if rating_tag else "N/A"
            link_tag = m.select_one("a.ipc-title-link-wrapper")
            link = "https://www.imdb.com" + link_tag["href"].split("?")[0] if link_tag else "N/A"
            titles.append(title)
            years.append(year)
            ratings.append(rating)
            urls.append(link)
        except Exception as e:
            print("Skipped one movie due to:", e)
            continue
    df = pd.DataFrame({
        "Title": titles,
        "Year": years,
        "IMDb Rating": ratings,
        "IMDb URL": urls
    })

    os.makedirs("data", exist_ok=True)
    df.to_csv("data/imdb_movies.csv", index=False)
    print("\nIMDb data saved to data/imdb_movies.csv")
    print(df.head(10))
    print(f"\nTotal movies scraped: {len(df)}")

if __name__ == "__main__":
    scrape_imdb_top_movies()
#BASE CODE
'''from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import os
def get_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver
def scrape_imdb_top_movies():
    print("Starting IMDb Scraper...")
    driver = get_driver(headless=True)
    driver.get("https://www.imdb.com/chart/top/")  # IMDb Top 250 Page
    time.sleep(3)
    movies = driver.find_elements(By.XPATH, '//li[@class="ipc-metadata-list-summary-item"]')[:100]  # top 100
    titles, years, ratings, urls = [], [], [], []
    for movie in movies:
        try:
            title = movie.find_element(By.XPATH, './/h3').text
            year = movie.find_element(By.XPATH, './/span[contains(@class,"title")]').text.strip("()")
            rating = movie.find_element(By.XPATH, './/span[contains(@class,"ratingGroup--imdb-rating")]').text
            link = movie.find_element(By.XPATH, './/a').get_attribute("href")
            titles.append(title)
            years.append(year)
            ratings.append(rating)
            urls.append(link)
        except Exception as e:
            print("Error:", e)
            continue
    driver.quit()
    df = pd.DataFrame({
        "Title": titles,
        "Year": years,
        "IMDb Rating": ratings,
        "IMDb URL": urls
    })

    os.makedirs("data", exist_ok=True)
    df.to_csv("data/imdb_movies.csv", index=False)
    print("IMDb data saved to data/imdb_movies.csv")
    print(df.head())
    print(f"\nTotal movies scraped: {len(df)}")
    return df
if __name__ == "__main__":
    scrape_imdb_top_movies()'''