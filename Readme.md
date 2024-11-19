# Price_scraper

## Setup
- main.py is plain and simple a FastAPI application which runs a uvicorn webserver in background
- use pip install requirements in your python venv

## Debugging and Running
- run the main.py and open 127.0.0.1/docs to test the endpoints

## Build main.exe for local distribution
- execute pyinstaller -F main.py --clean to build the main.exe for local distribution on windows machines

## Running application on Windows
- run the main.exe
- when the terminal opens and show successfull messages open browser and navigate to http://127.0.0.1:8000/docs
- open the wanted scraper endpoint and click on Try it out
- use the excel to transfer list of GITNs into the needed format - be careful with the brackets  only one pair of [] needs to be pasted
- close the terminal when done