from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import List, Union
import random
import time
import requests
from bs4 import BeautifulSoup
import uvicorn
import multiprocessing

app = FastAPI()

# Model for GTINs request
class GITNsRequest(BaseModel):
    gitns: List[int]  # List of GTINs as integers

# Function to introduce a random delay between requests
def add_random_delay():
    delay = random.uniform(1, 3)
    time.sleep(delay)

# Example function to scrape prices from Rossmann
def fetch_price_rossmann(gitn: int) -> Union[float, str]:
    url = f"https://www.rossmann.de/de/p/{gitn}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
    }

    try:
        add_random_delay()
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        euro_element = soup.find('span', class_='rm-price__integer')
        cent_element = soup.find('span', class_='rm-price__float')
        
        if euro_element and cent_element:
            euro_price = euro_element.text.strip().replace(",", "")
            cent_price = cent_element.text.strip().replace(",", "")
            full_price = f"{euro_price}.{cent_price}"
            return float(full_price)
        else:
            return "Price not found"
    except Exception as e:
        return f"Error: {str(e)}"

# Endpoint to fetch prices, returning plain text for easy copying
@app.post("/get_prices_rossmann", response_class=PlainTextResponse)
async def get_prices_rossmann(data: GITNsRequest) -> str:
    prices = [str(fetch_price_rossmann(gitn)) for gitn in data.gitns]
    return "\n".join(prices)  # Join each price with a newline for easy pasting

if __name__ == '__main__':
    multiprocessing.freeze_support()  # For Windows support
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False, workers=1)
