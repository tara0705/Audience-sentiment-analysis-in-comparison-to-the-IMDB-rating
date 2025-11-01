'''import requests, re, time
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def slugify(title):
    """Turn a title into a Rotten-Tomatoes style slug."""
    title = re.sub(r"[^a-zA-Z0-9 ]", "", title).strip().lower()
    return title.replace(" ", "_")

def fetch_audience_reviews(slug, max_reviews=20):
    """Return a list of audience reviews for that slug."""
    url = f"https://www.rottentomatoes.com/m/{slug}/reviews?type=user"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code != 200:
        return None, None     # page not found

    soup = BeautifulSoup(r.text, "html.parser")

    # try to grab the audience score from the score-board tag
    board = soup.select_one("score-board")
    aud_score = board.get("audiencescore") if board else None

    reviews = [r.text.strip() for r in soup.select("p.audience-reviews__review.js-review-text")]
    return aud_score, reviews[:max_reviews]

def analyze_sentiment(reviews):
    """Return average VADER compound score."""
    analyzer = SentimentIntensityAnalyzer()
    scores = [analyzer.polarity_scores(r)["compound"] for r in reviews]
    return round(sum(scores)/len(scores), 3) if scores else None

def main():
    title_input = input("Enter a movie name: ").strip()
    slug = slugify(title_input)
    print(f"\nSearching Rotten Tomatoes for: {slug}")
    aud_score, reviews = fetch_audience_reviews(slug)
    if reviews is None:
        print("Movie not found on Rotten Tomatoes.")
        return
    if not reviews:
        print("Found page but no audience reviews visible.")
        return
    avg_sent = analyze_sentiment(reviews)
    print(f"\nFound {len(reviews)} reviews.")
    print(f"Average VADER sentiment: {avg_sent}")
    print(f"Official Audience Score: {aud_score}")
    if aud_score and avg_sent is not None:
        diff = avg_sent*100 - float(aud_score)
        print(f"Difference (sentiment − audience score): {diff:.1f}")
    print("\nSample review:")
    print("–", reviews[0][:400], "…")

if __name__ == "__main__":
    main()'''


import requests, re, time, pandas as pd
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os

def slugify(title):
    """Turn a title into Rotten-Tomatoes slug."""
    title = re.sub(r"[^a-zA-Z0-9 ]", "", title).strip().lower()
    return title.replace(" ", "_")

def search_fallback(title):
    """Search Rotten Tomatoes if direct slug fails."""
    query = title.replace(" ", "%20")
    url = f"https://www.rottentomatoes.com/search?search={query}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code != 200:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    link = soup.select_one("search-page-media-row a")
    if link:
        return "https://www.rottentomatoes.com" + link["href"]
    return None

def fetch_reviews_and_score(url, max_reviews=15):
    """Extract audience score and reviews from given RT movie URL."""
    url = url.replace("httpshttps", "https")
    if not url.startswith("https://www.rottentomatoes.com"):
        if url.startswith("https://"):
            url = "https://www.rottentomatoes.com" + url.split("rottentomatoes.com")[-1]
    url = re.sub(r"(https://www\.rottentomatoes\.com)+", "https://www.rottentomatoes.com", url)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    # ensure only one /reviews?type=user suffix
    full_url = url.rstrip("/") + "/reviews?type=user"
    r = requests.get(full_url, headers=headers, timeout=15)
    if r.status_code != 200:
        return None, []
    soup = BeautifulSoup(r.text, "html.parser")
    board = soup.select_one("score-board")
    aud_score = board.get("audiencescore") if board else None
    reviews = [r.text.strip() for r in soup.select("p.audience-reviews__review.js-review-text")]
    return aud_score, reviews[:max_reviews]

def analyze_sentiment(reviews):
    analyzer = SentimentIntensityAnalyzer()
    scores = [analyzer.polarity_scores(r)["compound"] for r in reviews]
    return round(sum(scores) / len(scores), 3) if scores else None

def main():
    print("Starting Rotten Tomatoes Audience Sentiment Scraper")
    os.makedirs("data", exist_ok=True)

    imdb_df = pd.read_csv("data/imdb_movies.csv")
    titles = imdb_df["Title"].tolist()
    results = []

    for title in titles:
        title_clean = re.sub(r"^\d+\.\s*", "", title).strip()
        slug = slugify(title_clean)
        url = f"https://www.rottentomatoes.com/m/{slug}"

        print(f"\n{title_clean}")
        aud_score, reviews = fetch_reviews_and_score(url)

        if not reviews:
            #print("No reviews found — trying search fallback...")
            search_url = search_fallback(title_clean)
            if search_url:
                aud_score, reviews = fetch_reviews_and_score(search_url)
            else:
                print("Movie not found on Rotten Tomatoes search.")
                results.append([title_clean, None, None, 0])
                continue

        if not reviews:
            print("No audience reviews found even after fallback.")
            results.append([title_clean, aud_score, None, 0])
            continue

        avg_sentiment = analyze_sentiment(reviews)
        print(f"Reviews found: {len(reviews)} | Avg Sentiment: {avg_sentiment} | Audience Score: {aud_score}")
        results.append([title_clean, aud_score, avg_sentiment, len(reviews)])

        time.sleep(2)
    df = pd.DataFrame(results, columns=["Title", "RT Audience Score", "RT Audience Sentiment", "Review Count"])
    df.to_csv("data/rt_audience_sentiment.csv", index=False)
    print("\nSaved Rotten Tomatoes sentiment data to data/rt_audience_sentiment.csv")
    print(df.head())

if __name__ == "__main__":
    main()
