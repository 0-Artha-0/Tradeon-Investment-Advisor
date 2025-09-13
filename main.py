# main.py (FastAPI application)
import pandas as pd
from datetime import datetime, timedelta, date
import time
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from tasi_api import fetch_data
from lstm_model import load_LSTM, predict_price
from sentiment_analysis import load_sentiment, analyze_sentiment
import gemini_models as gem
import memory_functions as mem
import re
import os
import json

# Run full framework


def load_models():
    model, scaler = load_LSTM()
    print("Loaded LSTM model.")

    arabert, finbert = load_sentiment()
    print("Loaded the Sentiment Analysis models.")

    client = gem.initialize_client()
    print("Configured Gemini Client.")

    return [model, scaler, arabert, finbert, client]


async def apply_framework(models, end_date, company_name='Aramco'):

    print(f"\nTodays date: {end_date}", end="\n\n")

    # Unpack the models
    model, scaler, arabert, finbert, client = models

    reference_date = datetime.strptime(end_date, "%d-%m-%Y")

    # Subtract 30 days
    start_date = reference_date - timedelta(days=30)
    # Convert back to string
    start_date = start_date.strftime("%d-%m-%Y")

    # Fetch data
    data = fetch_data(start_date, end_date)

    # for testing
    actual_price = data[:1].copy()
    data = data.drop(data[:1].index)

    # Run LSTM model
    today_price, pred_price, change, lower, upper = predict_price(
        model, scaler, data)

    # Compute ground truth
    actual_price = actual_price['Close'].iloc[0]
    ground_percentage = round(
        ((actual_price - today_price)/today_price) * 100, 2)

    # Reformat dates to cover last 3 days only for twitter query
    start_date = (reference_date - timedelta(days=3)).strftime("%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%d-%m-%Y").strftime("%Y-%m-%d")

    # Analyze sentiment
    sentiment_score = await analyze_sentiment(arabert, finbert, start_date, end_date)

    # Reformat dates to cover last 3 days only for news query
    start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d-%m-%Y")
    end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d-%m-%Y")

    # Use Gemini models for decision making
    latest_news = gem.fetch_news(client, start_date, end_date, company_name)

    with open(f"{company_name}_news_analysis_headlines.txt", "w", encoding="utf-8") as file:
        file.write(latest_news)

    print(
        f"Saved the news headlines in {company_name}_news_analysis_headlines.txt file successfully.")

    # Memory bank analysis
    memory_results, scenarios_found, success_rate = mem.query_memory(
        pred_price, change, sentiment_score)

    # Analyze using all data collectively
    report = gem.analyze_all(client, company_name, pred_price,
                             change, sentiment_score, latest_news, memory_results)

    print(report, end="\n\n")
    with open(f"investment reports/Investment_analysis_{end_date}.txt", "w", encoding="utf-8") as file:
        file.write(report)

    decision, confidence, analysis, key_points = gem.split_summarize(
        client, report)

    mem.insert_memory(end_date, pred_price, change, sentiment_score,
                      latest_news, decision, analysis, company_name)

    return {
        "today_price": today_price,
        "lstm_pred": pred_price,
        "change": change,
        "lower": lower,
        "upper": upper,
        "sentiment_score": sentiment_score,
        "news": latest_news,
        "memory_results": memory_results,
        "decision": decision,
        "analysis": analysis,
        "confidence": confidence,
        "key_points": key_points,
        "actual_price": actual_price,
        "ground_percentage": ground_percentage,
        # Top 4 events
        "events_list": [re.search(r'["“](.*?)["”]', line).group(1) for line in latest_news.split('\n') if re.search(r'["“](.*?)["”]', line)][:4],
        "scenarios_found": scenarios_found,
        "success_rate": round(success_rate, 2)
    }

# Helper function during testing retrieve last computed date and restart after it


def remove_done(batch):
    memory = pd.read_excel('investment_memory.xlsx', engine='openpyxl')

    if memory.empty:
        return batch

    last = memory.iloc[-1]["Datetime"]

    if last in batch:
        i = batch.index(last)
        batch = batch[i+1:]
        print(f"\nRestarting after date {last}", end="\n\n")

    return batch


def decision_computed(today_date):
    memory = pd.read_excel('investment_memory.xlsx', engine='openpyxl')

    if memory.empty or today_date != memory.iloc[-1]["Datetime"]:
        return False
    else:
        return True


app = FastAPI()

# Configure CORS to allow your HTML file to fetch data
origins = [
    # Or whatever port your HTML is served from (e.g., Live Server in VS Code)
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    # Allows requests from files opened directly in the browser (file://)
    "null",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DashboardData(BaseModel):
    main_decision: Dict[str, Any]
    lstm_prediction: Dict[str, Any]
    social_sentiment: Dict[str, Any]
    event_impact: Dict[str, Any]
    memory_bank: Dict[str, Any]
    market_overview: Dict[str, Any]


# To Run the FastAPI server: uvicorn main:app --reload
@app.get("/dashboard_data")
async def dashboard_data():
    # In a real application, this would fetch data from a database,
    # run your LLM models, etc.

    # Create a backtesting date range
    # Backtesting Settings
    """backtest_dates = pd.date_range(
        start="2025-04-23", end="2025-09-09", freq='D')

    # Convert the date range to a list of strings in 'DD-MM-YYYY' format
    backtest_dates = backtest_dates.strftime("%d-%m-%Y").to_list()

    # Remove already computed days from the list if there are (In case app failure in the middle of running)
    backtest_dates = remove_done(backtest_dates)

    # Load all models once
    models_list = load_models()

    lstm_list = []
    sentiment_list = []

    counter1 = 0
    counter2 = 0

    for end_date in backtest_dates:
        # To mimic human behavior
        if counter1 >= 30:
            counter1 = 0
            print("\nTaking a break for a few minutes (5 min)..")
            time.sleep(300)
            print("Resuming execution now.", end="\n\n")

        # To mimic human behavior
        if counter2 >= 60:
            counter2 = 0
            print("\nTaking a break for a few minutes (10 min)..")
            time.sleep(600)
            print("Resuming execution now.", end="\n\n")

        # Run the framework and fetch all needed data for the dashboard
        results = await apply_framework(models_list, end_date)

        lstm_list.append(results['lstm_pred'])
        sentiment_list.append(results['sentiment_score'])

        if end_date != "09-09-2025":
            mem.update_memory_daily(
                results['actual_price'], results['ground_percentage'])

        counter1 = counter1 + 1
        counter2 = counter2 + 1 """

   # Daily Inference Settings
    # ------------------------------------------------------------------
    # 1. Check first if the inference had been done for today
    today_date = "12-09-2025"

    # 1.1 If yes, just fetch the data from memory and return it
    if decision_computed(today_date):
        print(
            f"\nInference already done for today {today_date}. Fetching data from memory..", end="\n\n")

        # Load the daily temporary memory
        with open('today_dashboard_data.json', 'r') as f:
            results = json.load(f)

    # 1.2 If not, run the inference and add it to memory
    else:
        # ------------------------------------------------------------------
        # 2. First update ground truth results for the last predicted day

        # fetch last actual closing price (yesterday) and its change percentage
        today_data = fetch_data(today_date, today_date, max_records=1)
        today_price = today_data['Close'].iloc[0]
        ground_percentage = today_data['changePercent'].iloc[0]

        mem.update_memory_daily(today_price, ground_percentage)

        # ------------------------------------------------------------------
        # 3. Predict today's decision
        print(f"\nRunning inference for today {today_date}..", end="\n\n")

        # Load all models once
        models_list = load_models()

        # Run the framework and fetch all needed data for the dashboard
        results = await apply_framework(models_list, today_date)

        # Retrieve the last week LSTM and Sentiment results for display
        lstm_list, sentiment_list = mem.fetch_lists()

        results['lstm_list'] = lstm_list
        results['sentiment_list'] = sentiment_list

        # Save the daily temporary memory
        with open('today_dashboard_data.json', 'w') as f:
            json.dump(results, f)

    # ------------------------------------------------------------------
    # Simulate dynamic data changes for demonstration
    confidence = results['confidence']
    last_price = results['today_price']

    # LSTM predictions
    lstm_prediction_score = results['lstm_pred']
    lower = results['lower']
    upper = results['upper']
    lstm_chart_data = results['lstm_list']
    lstm_chart_labels = ["Day -6", "Day -5", "Day -4",
                         "Day -3", "Day -2", "Day -1", "Today"]

    # BERT sentiment scores
    sentiment_score = results['sentiment_score']
    sentiment_chart_data = results['sentiment_list']
    sentiment_chart_labels = ["Week -6", "Week -5",
                              "Week -4", "Week -3", "Week -2", "Week -1", "Current"]

    # Example for sentiment summary based on score
    sentiment_summary = "Neutral sentiment"
    if sentiment_score > 0.8:
        sentiment_summary = "Strong positive sentiment surge"
    elif sentiment_score > 0.5:
        sentiment_summary = "Positive sentiment"
    elif sentiment_score < 0.2:
        sentiment_summary = "Strong negative sentiment"
    elif sentiment_score < 0.5:
        sentiment_summary = "Negative sentiment"

    # Event impact
    events = results['events_list']

    #
    memory_success_rate = results['success_rate']
    memory_scenarios_found = results['scenarios_found']
    # Check if the model was able to draw several key insights
    last_keypoint = results['key_points'][-1] if results['key_points'] else ""
    idx = last_keypoint.find(')')
    memory_insight = last_keypoint[idx+1:].strip() if idx != - \
        1 else last_keypoint or "No significant insights found."

    decision = results['decision']
    analysis = results['analysis']
    key_factors = results['key_points']

    decision_color = "#22c55e" if decision == "BUY" else (
        "#ef4444" if decision == "SELL" else "#f59e0b")
    confidence_color = "#4f46e5" if confidence > 80 else (
        "#f59e0b" if confidence > 70 else "#ef4444")

    data = {
        "main_info": {
            "date": today_date,
            "last_price": last_price,
        },
        "main_decision": {
            "decision": decision,
            "decision_color": decision_color,
            "confidence": confidence,
            "confidence_color": confidence_color,
            "ai_reasoning": analysis,
            "key_factors": key_factors
        },
        "lstm_prediction": {
            "prediction_score": lstm_prediction_score,
            # confidence here is totally irrelavent
            "prediction_interval": f"{lower} - {upper}",
            "chart_data": lstm_chart_data,
            "chart_labels": lstm_chart_labels
        },
        "social_sentiment": {
            "sentiment_score": sentiment_score,
            "chart_data": sentiment_chart_data,
            "chart_labels": sentiment_chart_labels,
            "summary": sentiment_summary
        },
        "event_impact": {
            # Convert Pydantic models to dicts
            "events": events
        },
        "memory_bank": {
            "scenarios_found": memory_scenarios_found,
            "success_rate": memory_success_rate,
            "insight": memory_insight
        }
    }
    return data


@app.get("/download_report")
def get_report_file(end_date):
    with open(f"investment reports/Investment_analysis_{end_date}.txt", "r", encoding="utf-8") as file:
        report = file.read()
    return Response(report, media_type="text/plain")

# Run the app to update the investment memory and dashboard json data during scheduled runs
data = dashboard_data()
