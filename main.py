"""
This file is part of Price_Scraper.
Licensed under the MIT License. See LICENSE file for details.
"""

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import List, Union
from decimal import Decimal
from bs4 import BeautifulSoup
import uvicorn
import multiprocessing
import asyncio
from playwright.async_api import async_playwright
import os
import sys
import httpx
import logging

CONST_EXC_NOT_LISTED = "Not listed anymore"

LICENSE_TEXT = """
MIT License

Copyright (c) 2024 Georg Leuschel

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
...

"""

app = FastAPI()

# Model for GTINs request
class GITNsRequest(BaseModel):
    gitns: List[int]  # List of GTINs as integers

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_chromium_path():
    if getattr(sys, 'frozen', False):
        bundle_dir = sys._MEIPASS  # PyInstaller temp folder
        return os.path.join(bundle_dir, 'playwright', 'chromium', 'chrome-win', 'chrome.exe')
    return "standard"

# Enhanced Rossmann scraper
async def fetch_price_rossmann(gitn: int) -> Union[float, str]:
    url = f"https://www.rossmann.de/de/p/{gitn}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
    }
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # Check the final redirected URL
            final_url = str(response.url)

            if not final_url.startswith("https://www.rossmann.de"):
                raise Exception(f"Unexpected redirection to {final_url}")

            # When not the product page is loaded the article was listed before but isn't anymore
            if not final_url.endswith(f"/p/{gitn}"):
                raise Exception(CONST_EXC_NOT_LISTED)

            # Parse the HTML of the final page
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract the price from the DOM
            euro_element = soup.find('span', class_='rm-price__integer')
            cent_element = soup.find('span', class_='rm-price__float')

            if euro_element and cent_element:
                euro_price = euro_element.text.strip().replace(",", "")
                cent_price = cent_element.text.strip().replace(",", "")
                return Decimal(f"{euro_price}.{cent_price}")

            return "Price not found"

    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error occurred: {str(e)}")
        return "Price not found"
    except Exception as e:
        logging.error( f"Error fetching Rossmann price for GTIN {gitn}: {str(e)}")
        if e.args[0] == CONST_EXC_NOT_LISTED:
            return CONST_EXC_NOT_LISTED
        return "Price not found"

# Enhanced DM scraper
async def fetch_price_dm(gitn: int) -> Union[float, str]:
    url = f"https://www.dm.de/p{gitn}.html"
    try:
        async with async_playwright() as p:
            chromium_path = get_chromium_path()
            browser = (
                await p.chromium.launch(headless=True)
                if chromium_path == "standard"
                else await p.chromium.launch(executable_path=chromium_path, headless=True)
            )
            page = await browser.new_page()
            await page.goto(url)
            await page.wait_for_selector('span[data-dmid="price-localized"]', timeout=5000)

            price_elements = await page.locator('span[data-dmid="price-localized"]').all_text_contents()
            await browser.close()

            if price_elements:
                return Decimal(price_elements[0].strip().replace('€', '').replace(',', '.').strip())
            return "Price not found"
    except Exception as e:
        logging.error(f"Error fetching DM price for GTIN {gitn}: {e}")
        return "Price not found"

# Endpoints
@app.post("/get_prices_rossmann", response_class=PlainTextResponse)
async def get_prices_rossmann(data: GITNsRequest) -> str:
    prices = await asyncio.gather(*(fetch_price_rossmann(gitn) for gitn in data.gitns))
    return "\n".join(str(price) for price in prices)

@app.post("/get_prices_dm", response_class=PlainTextResponse)
async def get_prices_dm(data: GITNsRequest) -> str:
    prices = await asyncio.gather(*(fetch_price_dm(gitn) for gitn in data.gitns))
    return "\n".join(str(price) for price in prices)

if __name__ == '__main__':
    logging.info("Starting Uvicorn server with the following license:")
    logging.info(LICENSE_TEXT)
    multiprocessing.freeze_support()  # For Windows support
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False, workers=1)