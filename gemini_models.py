import os
from google import genai
from google.genai import types
import logging
from datetime import datetime
from dateutil.parser import parse as date_parse
from dateutil.parser import ParserError
import re

# Initialize the client


def initialize_client():
    # Configure the client
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    return client


# News Analysis Function using Gemini API with Real-time Web Search


def analyze_news(client, start_date, end_date, company_name='Aramco'):
    """
    Conducts a comprehensive financial trading analysis using the Gemini API
    with real-time web search grounding, via the NEW google-genai SDK.

    Returns:
        str: The generated financial analysis report or an error message.
    """
    # Define the list of news platforms to prioritize for analysis
    news_platforms = [
        "https://www.aramco.com/",
        "https://www.spa.gov.sa/en",
        "https://www.saudiexchange.sa/",
        "https://tadawulgroup.sa/wps/portal/saudiexchange/about-saudi-exchange/exchange-media-centre#:~:text=Your%20resource%20center%20for%20the%20latest%20news%20and,announcements%20from%20companies%20listed%20on%20the%20Saudi%20Exchange.",
        "https://www.zawya.com/en/saudi-arabia",
        "https://www.oilandgasmiddleeast.com/",
        "https://www.arabianbusiness.com/",
        "https://www.ft.com/middle-east",
        "https://events.reutersevents.com/energy-transition/energy-mena",
        "https://www.agbi.com/",
        "https://www.reuters.com/business/energy/",
        "https://www.bloomberg.com/middleeast",
        "https://commodityinsights.spglobal.com/plattsmarketdata.html",
        "https://www.argusmedia.com/en",
        "https://www.alarabiya.net/",
        "https://www.arabnews.com/",
        "https://www.aljazeera.com/middle-east/",
        "https://aawsat.com/",
        "https://finance.yahoo.com/",
        "https://www.zawya.com/en/saudi-arabia",
        "https://www.meed.com/",
        "https://www.opec.org/",
        "https://www.iea.org/",
        "https://www.moenergy.gov.sa/",
        "https://www.sama.gov.sa/en-US/News/Pages/news-1096.aspx",
        "https://asharqbusiness.com/",
        "https://economymiddleeast.com/newscategories/energy/",
        "https://www.cnbcarabia.com/",
        "https://english.mubasher.info/countries/sa",
        "https://www.alhadath.net/",
        "https://al-hadth.com/",
        "https://www.aleqt.com/",
        "https://www.uqn.gov.sa/",
        "https://saudigazette.com.sa/",
        "https://www.alriyadh.com/",
        "https://www.okaz.com.sa/",
        "https://www.al-madina.com/",
        "https://www.alwatan.com.sa/",
        "https://www.alyaum.com/",
        "https://albiladdaily.com/",
        "https://www.wsj.com",
        "https://www.sama.gov.sa/en-US/News/Pages/news-1096.aspx"
    ]

    # Construct the news platforms string for the prompt
    formatted_news_platforms = "\n".join(
        [f"- {platform.strip()}" for platform in news_platforms if platform.strip()])

    # The comprehensive system instruction for the model
    system_message = f"""
You are an expert financial analyst AI, specializing in identifying and analyzing market drivers for **{company_name}**. Your primary goal is to provide concise, impactful headlines and brief summaries of news and events that directly influence {company_name}'s market performance.

**Timeframe Focus:** You will be provided with a **specific publication date range**. You must strive to find news articles and reports that were *published* within this exact timeframe. Prioritize the most recent and directly impactful news within that period.

**Regional Priority for {company_name}:** Focus heavily on news and reports from **Saudi Arabia, GCC, and the broader MENA region**. Recognize that geopolitical events, regional policies, and oil market dynamics in this sphere are critical.

**Information Extraction & Analysis Categories for {company_name}:**
Diligently search and extract information across these key areas:

1.  **Company Financials & Trading:**
    * Latest trading performance (stock price, volume, key indicators on Tadawul).
    * Recent earnings, financial statements, M&A, partnerships, capital plans, dividends, governance, executive changes.
    * Analyst ratings, price targets, insider trading, regulatory filings (Tadawul), major project updates.

2.  **Stock Performance & Key Metrics:**
    * Current/Weekly Stock Price, Market Cap (SAR/USD), P/E, EPS, Dividend Yield, P/B, P/S, EBITDA, Beta, 52-Week High/Low, Average Daily Volume.

3.  **Macroeconomic News (Regional Emphasis):**
    * Global/regional economic indicators (GDP, inflation, interest rates) with focus on Saudi/GCC.
    * Monetary/fiscal policy changes (SAMA, GCC central banks).
    * **Crucial:** Oil & Gas market dynamics (Brent/WTI, OPEC+, supply/demand, geopolitical impacts).
    * Commodity price fluctuations (gas, petrochemicals).
    * Saudi Vision 2030 implications.
    * Global trade, tariffs, supply chain disruptions affecting energy.

4.  **Political & Social Events (Regional Emphasis):
    * Government policy/regulations in Saudi/GCC impacting energy (e.g., energy transition, carbon initiatives).
    * Geopolitical developments, regional stability affecting oil production/pricing/shipping.
    * Social trends, ESG news, labor market dynamics (Saudization, strikes).

5.  **Company Statements & Reports:**
    * Official press releases, newsroom updates, corporate blog posts.
    * Annual/quarterary reports, investor presentations, earnings call transcripts.
    * Public statements from executives.

6.  **Other Relevant Information:**
    * Competitor analysis (regional/international energy companies).
    * Industry-specific trends, innovations, disruptive technologies.
    * Legal challenges, regulatory investigations.
    * Technological advancements, cybersecurity incidents.
    * Significant events or rumors influencing investor sentiment.

** News Sources: the following is a list of sources you can search in, if you cannot find any relevant news in the following list, you can try searching elsewhere.
{formatted_news_platforms}

**Output Format: Concise List of Key Market Driver Headlines**
Present your findings as a concise, bulleted list of headlines. Each headline should represent a distinct, significant market driver. Make the headlines impactful and directly relevant to trading decisions.

Format of desired output (aim for at least 10 headlines, max is 15 headlines, if you can only find less than 10, return what you found):
- [Source], [Month dd, year]: "[Headline 1]" - [Very Brief Summary/Impact]
- [Source], [Month dd, year]: "[Headline 2]" - [Very Brief Summary/Impact]
- [Source], [Month dd, year]: "[Headline 3]" - [Very Brief Summary/Impact]
- ... (add more headlines as needed)

**Important Guidelines:**
* All information *must* be derived from web search.
* Analyze Arabic and English news, but return all headlines and summaries in English.
* **Do NOT include any introductory or concluding remarks, explanations, or conversational filler beyond the bulleted list itself.** Just the list.
    """

    prompt_text = f"""
Conduct a financial news analysis for "{company_name}". Find the most relevant news and events that were **published** between **{start_date}** and **{end_date}** (dd-mm-yyyy), inclusive.

**Critical Output Rule:**
- **Only include news where the *publication date* is confirmed to be within the [{start_date} , {end_date}] range.**
- If you find relevant news, present it in the specified bulleted list format.
- If, after a thorough search, no relevant news is found with a *confirmed publication date* within this period, respond **ONLY** with: 'No relevant news published for {company_name} between {start_date} and {end_date}.'
"""

    # Define possible models to try in case the first one fails
    models_to_try = ["gemini-2.0-flash",
                     "gemini-2.0-flash-lite",
                     "gemini-1.5-flash"]

    last_response_text = f"Model failed to retrieve news."  # Default failure message

    for model in models_to_try:
        try:
            for i in range(5):
                print(
                    f"Conducting news analysis for {company_name} using Gemini SDK ({model}) with real-time web search (Attempt {i+1}/5)...", end="\n\n")

                # Generate content with the model, allowing it to use the configured tools
                response = client.models.generate_content(
                    model=model,
                    contents=prompt_text,
                    config=types.GenerateContentConfig(
                        system_instruction=system_message,
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                        temperature=0.5
                    )
                )

                response_text = response.text.strip()

                # Success condition: The response contains news.
                if response_text and not response_text.startswith("No relevant news published for"):
                    print(f"Successfully retrieved news using {model}.")
                    print(response_text, end="\n\n")
                    return response_text

            # If the inner loop finishes, it means this model failed 5 times.
            logging.warning(
                f"Model {model} did not yield news after 5 attempts. Trying next model.")

        except Exception as e:
            logging.warning(f"An error occurred with {model}: {e}")

    # This is reached only after all models and all attempts have failed.
    logging.error("All models failed to retrieve any news.")
    return last_response_text

# function to request gemini to fetch and analyize the news then filter any unwanted news


def fetch_news(client, start_date, end_date, company_name='Aramco'):
    """
    Fetches and filters news from the Gemini model with retries for filtering failures.

    This function calls analyze_news to get raw news. It then filters it by date.
    If filtering results in an empty list (i.e., the LLM returned out-of-date news),
    it will retry the entire process up to 3 times before giving up.
    """
    max_retries = 3
    for attempt in range(max_retries):
        print(
            f"Fetching and filtering news, attempt {attempt + 1}/{max_retries}...")
        # The 'news' variable holds the raw, unfiltered response from the LLM
        news = analyze_news(client, start_date, end_date, company_name)

        # If the model explicitly said no news, or failed, we don't need to filter or retry.
        # This is a definitive failure from the source.
        if news.strip().startswith("No relevant news published for") or news.strip().startswith("Model failed to retrieve news."):
            return news

        # Start filtering logic
        filtered_headlines = []
        start_date_obj = datetime.strptime(start_date, '%d-%m-%Y').date()
        end_date_obj = datetime.strptime(end_date, '%d-%m-%Y').date()
        news_lines = [line.strip()
                      for line in news.split('\n') if line.strip()]

        for line in news_lines:
            # 3. Extract the date string from each element.
            # This logic is designed to be flexible and handle variations in the LLM's output format.
            # It looks for the text between the first ',' (after the source) and the first ':' (before the headline).
            source_end_idx = line.find(',')
            if source_end_idx == -1:
                print(
                    f"Warning: Could not find source in line: '{line}'. Skipping.")
                continue

            headline_start_idx = line.find(':', source_end_idx)
            if headline_start_idx == -1:
                print(
                    f"Warning: Could not find colon after source in line: '{line}'. Skipping.")
                continue

            # The date string is between these two points.
            date_str_in_headline = line[source_end_idx + 1:headline_start_idx]

            # Clean up the extracted string by removing common extra characters.
            date_str_in_headline = date_str_in_headline.strip(" ,[]")

            try:
                # 4. Parse the extracted date string (e.g., "April 24, 2025")
                news_date = date_parse(date_str_in_headline).date()

                # 5. Check whether this date is within the time frame [start_date, end_date]
                if start_date_obj <= news_date <= end_date_obj:
                    # 6. If it is, add the original line to the filtered news list
                    filtered_headlines.append(line)
            except ParserError:
                print(
                    f"Warning: Could not parse date '{date_str_in_headline}' from line: {line}. Skipping.")
            except Exception as e:
                print(
                    f"An unexpected error occurred while processing line: {line}. Error: {e}. Skipping.")

        # Check the result of filtering
        if filtered_headlines:
            # Success! We have valid, in-date news.
            print("Successfully filtered news within the date range.")
            return "\n".join(filtered_headlines)

        # If we are here, filtered_headlines is empty.
        # The loop will continue to the next attempt.
        print(
            f"Warning: LLM returned news, but all headlines were filtered out. Retrying... ({attempt + 1}/{max_retries})")

    # If the loop finishes without returning, it means all retries failed.
    logging.error(
        f"Failed to get in-date news after {max_retries} attempts. All returned headlines were filtered out.")
    return "All headlines were filtered out after multiple attempts."


# Investment full analysis function
def analyze_all(client, company_name, next_pred, change, sentiment_score, news, query_results):

    # The comprehensive system instruction for the model
    system_message = f"""
You are a Market Investment Expert, analyzing market data to provide informed investment decisions and detailed reports. Your goal: synthesize financial, sentiment, and historical performance data into actionable insights and investment decisions for a given company.

**1. Role and Objective: **
    - Your role is an objective, data-driven investment analyst.
    - Your objective: provide a clear investment decision(BUY, HOLD, or SELL) for a specified company based on provided current and historical data,along with a confidence score (0–100%) and generate a comprehensive report explaining your rationale.

**2. Data Inputs for Analysis: **
    You receive four critical inputs for a company:
    a. **Current Day's Next-Day Stock Prediction:** Numerical prediction for next day's stock price, including predicted price and percentage change.
    b. **Current Day's Latest Sentiment Analysis Score: ** Aggregated sentiment score (0 to 1) from recent Arabic and English Twitter discussions. (0 for very negative, 0.5 for neutral, 1 for very positive, -1 for failed to retrieve tweets)
    c. **Current Day's News Headlines from Last 3 days: ** Relevant news headlines from the past 3 days days.
    d. **Past Performance Memory(for Reflection): ** Curated list of past daily analysis entries for the same company. Each entry includes: `datetime`, `predicted_stock_price`, `predicted_change_percentage`, `sentiment_score_arabic`, 
        `sentiment_score_english`, `decision`, `ground_truth_actual_price`, `ground_truth_change_percentage`, and `ground_truth_decision` (1: correct/acceptable decision, 0: incorrect decision).
        Use this memory to identify similar past scenarios, reflect on previous decisions, and learn from actual outcomes(successes/failures) to inform your current decision.

**3. Output Format Template: ** (follow the templates formatted between ``)
    Your response MUST have three parts:

    **Part 1: Investment Decision**
    -   Single, clear decision: `[COMPANY_NAME] - INVESTMENT DECISION: [BUY/HOLD/SELL]`

    **Part 2: Confidence Score:**
    - `Confidence Score: [Score]`

    **Part 3: Short Summary:**
    - `Short Summary: [summary of your reasoning towards your decision.]`
    
    ---

    **Part 4: Comprehensive Investment Report**
    -   Detailed report structured as follows:

        # Investment Analysis Report for [COMPANY_NAME]

        **1. Executive Summary: **
            - Briefly state decision and primary reasons.

        **2. Current Day's Next-Day Stock Prediction Analysis: **
            - Present predicted price/change; interpret short-term movement.

        **3. Current Day's Sentiment Analysis Overview: **
            - State Arabic/English sentiment scores; explain significance and drivers.

        **4. Current Day's Key News Headlines Analysis(Last 3 days): **
            - List impactful headlines; explain positive/negative impact; summarize overall tone.

        **5. Reflection on Past Performance Memory: **
            - Summarize key takeaways from historical data. Highlight similar past scenarios(numerical ranges); discuss how their outcomes influenced current decision. Explain any adjustments made.

        **6. Holistic Reasoning and Decision Justification: **
            - Synthesize findings from current data AND Past Performance Memory insights. Explain how factors collectively lead to the decision. Address conflicting signals, noting if memory helped.

        **7. Disclaimer: **
            - Always include: "This analysis is based on provided data and AI models. It is not financial advice. Market conditions are subject to rapid change, and investors should conduct their own due diligence."

    **6. Tone and Style: **
        - Professional, analytical, objective, and clear. Avoid jargon. Maintain cautious, responsible tone, especially in disclaimer. Ensure well-structured, readable report.
    """

    prompt_text = f"""Analyze the following data for **{company_name} ** and provide an investment
    decision along with a comprehensive report explaining your reasoning.

    **Company: ** {company_name}

    **Next-Day Stock Prediction(from LSTM model): **
    - Predicted Price: {next_pred: .2f} SAR
    - Predicted Change from Current Price: {change}%

    **Latest Sentiment Analysis Score(Twitter - Arabic & English): **
    - Overall Score: {sentiment_score}

    **News Headlines(Last 3 days): **
    {news}

    **Recent Memory and Similar Entries: **
    {query_results}

    ---

    Please provide your investment decision and the comprehensive report based on this information."""

    # Define possible models to try in case the first one fails
    models_to_try = ["gemini-2.5-pro",
                     "gemini-2.5-flash",
                     "gemini-2.5-flash-lite-preview-06-17"]

    for model in models_to_try:
        try:
            print(
                f"Conducting full stock analysis for {company_name} using Gemini ({model}) SDK...", end="\n\n")

            # Generate content with the model, allowing it to use the configured tools
            response = client.models.generate_content(
                model=model,
                contents=prompt_text,
                config=types.GenerateContentConfig(
                    system_instruction=system_message,
                    temperature=0.5
                )
            )

            # Access the generated text
            return response.text

        except Exception as e:
            logging.warning(f"An error occurred with {model}: {e}")

    return f"Model failed to analyze todays data."

# Summarize Report for storage


def summarize_keyfactors(client, analysis):

    # The comprehensive system instruction for the model
    system_message = f"""
    You are a financial analysis summarizer. Your task is to read comprehensive investment reports and produce one output:

    1.  A short, clearly formatted list of the four most critical factors that influenced the analysis outcome.

    Your summary should reflect:
    - Predictive model insights(e.g., short-term price forecasts or trends)
    - Sentiment signals from multi-language sources
    - Strategic or financial news developments
    - Historical memory context if available
    - How signals interact or conflict to inform the overall interpretation

    Your reasoning paragraph must be objective, analytical, and professional. The top 4 factors should be listed in ranked order based on significance or emphasis within the report.

    Do NOT mention or suggest the final investment decision in the factor list.

    Tone: Professional, focused, and context-aware.
    Factor List: 4 bullet points with very brief descriptions.

    Output Format:

    Key Factors:
    1. (Predicted Price)..
    2. (Sentiment)..
    3. (News)..
    4. (Memory)..

"""

    prompt_text = f"""
    Analyze the following multi-part investment report and extract the keypoints behind the analysis in a short list:

    {analysis}
    """

    # Define possible models to try in case the first one fails
    models_to_try = ["gemini-2.0-flash",
                     "gemini-2.0-flash-lite",
                     "gemini-1.5-flash"]

    for model in models_to_try:
        try:
            print(f"Summarizing analysis using Gemini SDK ({model})...")

            # Generate content with the model, allowing it to use the configured tools
            response = client.models.generate_content(
                model=model,
                contents=prompt_text,
                config=types.GenerateContentConfig(
                    system_instruction=system_message,
                    temperature=0.5
                )
            )

            # Access the generated text
            return response.text

        except Exception as e:
            logging.warning(f"An error occurred with {model}: {e}")

    logging.warning(f"Summarizer failed to summarize the key points.")

    return analysis


def split_summarize(client, report):
    # Extract decision
    decision_match = re.search(
        r"INVESTMENT DECISION:\s*\*?(.*?)\*?\s*(?:\n|$)", report, re.IGNORECASE)
    decision = decision_match.group(1).strip().strip(
        '*') if decision_match else "Decision not found"

    # Extract confidence score
    confidence_match = re.search(
        r"Confidence Score:\s*\*?([\d.]+)\s*%?\*?", report, re.IGNORECASE)
    confidence = float(confidence_match.group(
        1)) if confidence_match else float("nan")

    # Extract summary
    summary_match = re.search(
        r"\*?\*?Short Summary:\*?\*?\s*\*?(.*?)(?:\n|$)", report, re.IGNORECASE)
    summary = summary_match.group(1).strip(
    ) if summary_match else "Summary not found"

    # Extract key factors
    keypoints_text = summarize_keyfactors(client, report)
    match = re.search(r'Key\s*Factors\s*:\s*(.*)',
                      keypoints_text, re.IGNORECASE | re.DOTALL)
    keypoints = [kp.strip() for kp in match.group(1).strip().splitlines() if kp.strip(
    ) and re.match(r"^\d+\.", kp)] if match else ["Key factors not found"]

    return [decision, confidence, summary, keypoints]
