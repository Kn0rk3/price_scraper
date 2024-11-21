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

import asyncio
from playwright.async_api import async_playwright

import os
import sys

app = FastAPI()

# Model for GTINs request
class GITNsRequest(BaseModel):
    gitns: List[int]  # List of GTINs as integers

# Function to introduce a random delay between requests
def add_random_delay():
    delay = random.uniform(1, 3)
    time.sleep(delay)

def get_chromium_path():
    # The path to the Chromium binary bundled with PyInstaller
    if getattr(sys, 'frozen', False):
        # If we're running as a bundled executable (frozen by PyInstaller)
        bundle_dir = sys._MEIPASS  # This is the temporary folder where PyInstaller stores the extracted files
        return os.path.join(bundle_dir, 'playwright', 'chromium', 'chrome-win','chrome.exe')
    else:
        # When running from source, use Playwright's normal install path
        return "standard"

# fetch prices from rossmann online store
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
        return "Price not found"

# fetch prices from dm online store
async def fetch_price_dm(gitn: int) -> str:
    
    url = f"https://www.dm.de/p{gitn}.html"
    try:
        async with async_playwright() as p:

            browser = None

            # Get the path to the bundled Chromium
            chromium_path = get_chromium_path()

            if chromium_path == "standard":
                browser = await p.chromium.launch(headless=True)
            else:
                # Launch Chromium from the correct path
                browser = await p.chromium.launch(executable_path=chromium_path, headless=True)

            page = await browser.new_page()

            await page.goto(url)
            await page.wait_for_timeout(3000)  # Wait to allow content to load fully
            
            # Scrape the price based on the `data-dmid` attribute
            try:
                # Find all price elements, then pick the first one
                price_elements = await page.locator('span[data-dmid="price-localized"]').all_text_contents()
                
                if price_elements:
                    # Get the first price, clean it up and return it
                    price = price_elements[0].strip().replace('€', '').replace(',', '.').strip()
                    return price
                else:
                    return "Price not found"
            except Exception as e:
                return "Price not found"
            finally:
                await browser.close()

    except Exception as e:
        return f"Error: {str(e)}"
    
# Endpoint to fetch prices, returning plain text for easy copying
@app.post("/get_prices_rossmann", response_class=PlainTextResponse)
async def get_prices_rossmann(data: GITNsRequest) -> str:
    prices = [str(fetch_price_rossmann(gitn)) for gitn in data.gitns]
    return "\n".join(prices)  # Join each price with a newline for easy pasting

# Endpoint to fetch prices, returning plain text for easy copying
@app.post("/get_prices_dm", response_class=PlainTextResponse)
async def get_prices_dm(data: GITNsRequest) -> str:
    """Fetch prices for a list of GTINs and return them as plain text."""
    prices = await asyncio.gather(*(fetch_price_dm(gitn) for gitn in data.gitns))
    return "\n".join(prices)  # Join each price with a newline for easy pasting

if __name__ == '__main__':
    multiprocessing.freeze_support()  # For Windows support
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False, workers=1)
