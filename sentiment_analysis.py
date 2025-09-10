import nest_asyncio
import pandas as pd
import re
from twscrape import API, gather
from twscrape.logger import set_log_level
from transformers import pipeline
import warnings

warnings.filterwarnings("ignore")

# Load the models once only


def load_sentiment():

    # Load AraBERT Twitter sentiment model
    arabert_sentiment = pipeline(
        "sentiment-analysis",
        model="Abdo36/Arabert-Sentiment-Analysis-ArSAS",
        tokenizer="Abdo36/Arabert-Sentiment-Analysis-ArSAS",
        truncation=True,
        max_length=512
    )

    # Load FinBERT sentiment model
    finbert_sentiment = pipeline(
        "sentiment-analysis",
        model="nickmuchi/finbert-tone-finetuned-fintwitter-classification",
        tokenizer="nickmuchi/finbert-tone-finetuned-fintwitter-classification",
        truncation=True,
        max_length=512
    )

    return [arabert_sentiment, finbert_sentiment]

# Send query to scrape Arabic tweets about Aramco stock


async def scrape_twitter(query, max_tweets=500):
    """
    Function to send a query to the twscrape API.
    """
    # Patch asyncio to allow nested event loops

    # This is necessary for environments like Jupyter notebooks
    nest_asyncio.apply()
    # Optional: increase verbosity
    set_log_level("INFO")

    api = API()  # uses stored logged-in sessions

    tweets = []

    try:
        retrieved = await gather(api.search(query, limit=max_tweets, kv={"product": "Top"}))
        print(f"\n✅ Scraped {len(retrieved)} tweets about Aramco stock")

    except Exception as e:
        print(f"Error during tweet scraping: {e}")

    if len(retrieved) > 0:
        # Iterate through tweets found by the API search
        for tweet in retrieved:
            tweets.append({
                "Date": tweet.date,
                "Username": tweet.user.username,
                "Display Name": tweet.user.displayname,
                "Followers": tweet.user.followersCount,
                "Content": tweet.rawContent,
                "Tweet URL": f"https://twitter.com/{tweet.user.username}/status/{tweet.id}"
            })
    else:
        print("0 tweets retrieved..", end="\n\n")

    return pd.DataFrame(tweets)

# filter tweets to exclude unwanted content


def filter_tweets(twts, pattern):
    # Keep only tweets containing the pattern in the Content
    twts_filtered = twts[twts["Content"].str.contains(
        pattern, case=False, na=False)]

    return twts_filtered

# Compute sentiment scores for Arabic and English tweets


def compute_score(label_map, sentiment_results):
    labels = [label_map[res['label'].lower()] for res in sentiment_results]
    scores = [res['score'] for res in sentiment_results]

    # Weighted sum of positive (1) and negative (0) labels
    weighted_sum = sum(label * score for label, score in zip(labels, scores))
    total_weight = sum(scores)

    score = weighted_sum / total_weight if total_weight > 0 else 0
    print(f"Overall sentiment score: {score:.3f}")

    return score

# perform Arabic Sentiment Analysis on the tweets


async def analyze_arabic_sentiment(arabert_sentiment, start_date, end_date):
    """
    Function to perform sentiment analysis on Arabic tweets.
    """
    # Initialize the arabic query
    query = (
        '"سهم أرامكو" OR "أسهم أرامكو" OR "تاسي أرامكو" OR "أرامكو تداول" OR "أرامكو سعر السهم" '
        '-تيليجرام -سناب -توصية -توصيات -توصيتين -توصيتك -اشترك -أرسل -ارسل -دعاية -اعلان -تم -يراسلني -يرسل -يرسلوا -قروب -تواصل -بالخاص -راسلنا -واتساب -تفضل -الاستفسار -للاستفسار -بالاستفسار -المبتعثين -للتواصل -معه -معنا -يتواصل -يتواصلوا -راسلني -الخاص -الواتساب -انضم -يراسلي -توصياتنا -ارسلوا -شاركنا -القناة -قناة -تابع -يبي -الجلسة -مبارك -الجروب -الاستشارات'
        'lang:ar '
        # Start date for scraping (for the current test example)
        f'since:{start_date} '  # Star
        f'until:{end_date} '  # End date for scraping
        '-filter:replies '
        '-filter:retweets '
    )

    # Fetch Arabic tweets using the send_query function
    arabic_twts = await scrape_twitter(query)

    if len(arabic_twts) > 0:
        # Set the pattern to filter tweets
        pattern = r"(سهم\s*[أا]رامكو|سهم\s*#?[أا]رامكو)"

        # Filter the tweets to keep only those containing the pattern
        arabic_twts = filter_tweets(arabic_twts, pattern)

        # Analyze sentiments
        sentiment_results = arabert_sentiment(
            arabic_twts["Content"].tolist(), truncation=True)
        print(f"✅ Arabic sentiment analysis complete.")

        # Compute sentiment score
        label_map = {"positive": 1, "negative": 0,
                     "neutral": 0.5, "mixed": 0.5}
        sentiment_score = compute_score(label_map, sentiment_results)

    else:
        sentiment_score = -1

    return sentiment_score


# Perform English Sentiment Analysis on the tweets


async def analyze_english_sentiment(finbert_sentiment, start_date, end_date):
    """    
    Function to perform sentiment analysis on English tweets.
    """
    # Initialize the english query
    query = (
        '"Aramco stock" OR "Aramco shares" OR "Aramco price" OR "Aramco earnings" OR "Aramco results" OR "Aramco dividend" OR "2222.TAD" OR "Aramco IPO" OR "Aramco TASI" OR "Aramco Tadawul" OR "Saudi Oil prices" OR "Saudi Oil exports"'
        'lang:en '
        # Start date for scraping (for the current test example)
        f'since:{start_date} '  # Start date for scraping
        f'until:{end_date} '  # End date for scraping
        '-filter:retweets '
    )

    # Fetch English tweets using the send_query function
    english_twts = await scrape_twitter(query)

    # Check if retrieved tweets dataframe is not empty
    if len(english_twts) > 0:
        # Define keywords/phrases to match (case-insensitive)
        keywords = [
            "ARAMCO", "Aramco", "aramco", "Stock", "stock", "Shares", "shares", "Price", "price", "Earnings",
            "earnings", "Aramco price", "Aramco earnings", "Aramco results", "Dividend", "dividend", "2222.TAD",
            "Saudi oil exports", "saudi oil exports", "IPO", "TASI", "Tadawul", "tadawul"
        ]

        # Build regex pattern to match any of the keywords/phrases
        pattern = r"|".join([re.escape(k) for k in keywords])

        # Filter the tweets to keep only those containing the pattern
        english_twts = filter_tweets(english_twts, pattern)

        # Analyze sentiments on filtered English tweets
        sentiment_results = finbert_sentiment(
            english_twts["Content"].tolist(), truncation=True)
        print(f"✅ English sentiment analysis complete.")

        # Analyze sentiment results
        # Map string labels to numeric values
        label_map = {"bearish": 0, "neutral": 0.5, "bullish": 1}

        sentiment_score = compute_score(label_map, sentiment_results)

    else:
        sentiment_score = -1

    return sentiment_score

# Combine Arabic and English sentiment scores


async def analyze_sentiment(arabert, finbert, start_date, end_date):

    # analyze arabic sentiment
    arabic_score = await analyze_arabic_sentiment(arabert, start_date, end_date)

    # analyze english sentiment
    english_score = await analyze_english_sentiment(finbert, start_date, end_date)

    # Combine scores
    if arabic_score > -1 and english_score > -1:
        combined_score = (arabic_score + english_score) / 2
        print(f"Combined sentiment score: {combined_score:.3f}")
        return round(combined_score, 3)

    elif arabic_score > -1:
        print("Only Arabic Score is available.")
        return arabic_score

    elif english_score > -1:
        print("Only English score is available.")
        return english_score
    else:
        print("Failed to retrieve tweets.")
        return -1
