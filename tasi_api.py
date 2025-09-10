# tadawul_scraper.py
import requests
import time
import pandas as pd
from bs4 import BeautifulSoup

# Retrieve fresh cookies for every new session


def get_fresh_cookies():
    session = requests.Session()
    bootstrap_url = "https://www.saudiexchange.sa/wps/portal/saudiexchange/home/"
    session.get(bootstrap_url)

    return session.cookies.get_dict()

# Build session payload


def build_payload(start, start_date, end_date):
    # Your payload logic stays here
    return {
        'draw': '1',
        'start': str(start),
        'length': '100',
        'search[value]': '',
        'search[regex]': 'false',
        'selectedMarket': 'MAIN',
        'selectedSector': 'TENI:31',
        'selectedEntity': '2222',
        'startDate': start_date,
        'endDate': end_date,
        'tableTabId': '0',
        'startIndex': str(start),
        'endIndex': str(start + 99),
        # The rest of the column definitions here...
        'columns[0][data]': 'transactionDateStr',
        'columns[0][name]': '',
        'columns[0][searchable]': 'true',
        'columns[0][orderable]': 'false',
        'columns[0][search][value]': '',
        'columns[0][search][regex]': 'false',
        'columns[1][data]': 'todaysOpen',
        'columns[1][name]': '',
        'columns[1][searchable]': 'true',
        'columns[1][orderable]': 'false',
        'columns[1][search][value]': '',
        'columns[1][search][regex]': 'false',
        'columns[2][data]': 'highPrice',
        'columns[2][name]': '',
        'columns[2][searchable]': 'true',
        'columns[2][orderable]': 'false',
        'columns[2][search][value]': '',
        'columns[2][search][regex]': 'false',
        'columns[3][data]': 'lowPrice',
        'columns[3][name]': '',
        'columns[3][searchable]': 'true',
        'columns[3][orderable]': 'false',
        'columns[3][search][value]': '',
        'columns[3][search][regex]': 'false',
        'columns[4][data]': 'previousClosePrice',
        'columns[4][name]': '',
        'columns[4][searchable]': 'true',
        'columns[4][orderable]': 'false',
        'columns[4][search][value]': '',
        'columns[4][search][regex]': 'false',
        'columns[5][data]': 'change',
        'columns[5][name]': '',
        'columns[5][searchable]': 'true',
        'columns[5][orderable]': 'false',
        'columns[5][search][value]': '',
        'columns[5][search][regex]': 'false',
        'columns[6][data]': 'changePercent',
        'columns[6][name]': '',
        'columns[6][searchable]': 'true',
        'columns[6][orderable]': 'false',
        'columns[6][search][value]': '',
        'columns[6][search][regex]': 'false',
        'columns[7][data]': 'volumeTraded',
        'columns[7][name]': '',
        'columns[7][searchable]': 'true',
        'columns[7][orderable]': 'false',
        'columns[7][search][value]': '',
        'columns[7][search][regex]': 'false',
        'columns[8][data]': 'turnOver',
        'columns[8][name]': '',
        'columns[8][searchable]': 'true',
        'columns[8][orderable]': 'false',
        'columns[8][search][value]': '',
        'columns[8][search][regex]': 'false',
        'columns[9][data]': 'noOfTrades',
        'columns[9][name]': '',
        'columns[9][searchable]': 'true',
        'columns[9][orderable]': 'false',
        'columns[9][search][value]': '',
        'columns[9][search][regex]': 'false',
    }

# Extract change and changePercent from HTML strings


def extract_change(html_str):
    soup = BeautifulSoup(html_str, "html.parser")
    div = soup.find("div", class_="priceDown") or soup.find(
        "div", class_="priceUp")
    return float(div.text) if div else 0.0

# Preprocess the data to be compatible with the LSTM


def preprocess_data(days, window_size=11):  # NEEDD a load of editing
    # Rename the columns for clarity
    days.rename(columns={
        "todaysOpen": "Open",
        "highPrice": "High",
        "lowPrice": "Low",
        "previousClosePrice": "Close",
        "volumeTraded": "Volume",
        "turnOver": "Turnover",
        "noOfTrades": "NoOfTrades",
        "transactionDateStr": "Date"
    }, inplace=True)

    # Drop the 'transactionDate' & 'lastTradePrice' column (redundant with 'Date' & 'Close')
    days.drop(['transactionDate', 'lastTradePrice'], axis=1, inplace=True)

    # Ensure 'Date' is in datetime format
    days["Date"] = pd.to_datetime(
        days["Date"], format="%Y-%m-%d", errors='coerce')

    # Move 'Date' to the first column
    cols = days.columns.tolist()
    cols.insert(0, cols.pop(cols.index('Date')))
    days = days[cols]

    # Apply the extraction function to the 'change' and 'changePercent' columns
    days["change"] = days["change"].apply(extract_change)
    days["changePercent"] = days["changePercent"].apply(
        lambda s: extract_change(s.strip('%')))

    # Ensure all numeric columns are in float format
    for col in ["Open", "High", "Low", "Close", "change", "changePercent"]:
        days[col] = pd.to_numeric(days[col], errors="coerce")

    for col in ["Volume", "Turnover", "NoOfTrades"]:
        days[col] = (
            days[col]
            .astype(str)
            .str.replace(",", "", regex=False)  # Remove commas
            .str.replace("-", "", regex=False)  # Remove dashes
            # Remove non-breaking spaces
            .str.replace("\u00a0", "", regex=False)
            .str.strip()  # Remove leading/trailing whitespace
        )
        days[col] = pd.to_numeric(days[col], errors="coerce")

    # Set 'Date' as the index
    days.set_index('Date', inplace=True)

    # Take the latest 10 results only + the actual day (FOR TESTING)
    days = days.head(window_size)

    return days


def fetch_data(start_date, end_date, entity_id="2222", max_records=1500):
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.saudiexchange.sa',
        'referer': 'https://www.saudiexchange.sa/wps/portal/saudiexchange/newsandreports/reports-publications/historical-reports/!ut/p/z1/04_Sj9CPykssy0xPLMnMz0vMAfIjo8ziTR3NDIw8LAz8DTxCnA3MDILdzUJDLAyNXE30I4EKzHEqMDTTDyekoCA7zRMAIkY09Q!!/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'x-requested-with': 'XMLHttpRequest',
    }

    cookies = get_fresh_cookies()

    url = 'https://www.saudiexchange.sa/wps/portal/saudiexchange/newsandreports/reports-publications/historical-reports/!ut/p/z1/lY9NDsIgFITP0gMYRhRki8ZSE2uLFK1sDAtjSBRdGM9v4078SZ3dS755M0McaYmL_h6O_hYu0Z-6e-f4nkkOWghUKJoZOIzithFDOh-T7SsgSsWhV1JXdMKgNiDuLz9MzaDzuhwtsYYC7-fHF8ke-S5BtBVdA5NPmQCFQQp8mJh8eN_wBH6UNIdIrmdrW4TFQGbZA6as4Ag!/p0/IZ7_5A602H80O0HTC060SG6UT81216=CZ6_5A602H80O0HTC060SG6UT812E4=NJpopulateCompanyDetails=/'

    all_rows = []
    for start in range(0, max_records, 100):
        payload = build_payload(start, start_date, end_date)
        payload['selectedEntity'] = entity_id  # Dynamic injection
        res = requests.post(url, headers=headers,
                            cookies=cookies, data=payload)
        res.raise_for_status()
        rows = res.json().get("data", [])
        if not rows:
            break
        all_rows.extend(rows)
        time.sleep(1)  # polite delay

    # past '30' days
    past_days = pd.DataFrame(all_rows)

    # preprocess the data and return '10' days only (window size)
    past_days = preprocess_data(past_days)

    return past_days
