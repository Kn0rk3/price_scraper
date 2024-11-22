# Price_scraper

## Setup
- main.py is plain and simple a FastAPI application which runs a uvicorn webserver in background
- use pip install requirements in your python venv

## Debugging and Running
- run the main.py and open 127.0.0.1/docs to test the endpoints

## Build main.exe for local distribution
- execute `pyinstaller --onefile --add-data "C:\Users\<username>\AppData\Local\ms-playwright\chromium-1140:playwright/chromium" --version-file version_info.rc --name price_scraper -F main.py --clean` to build the main.exe for local distribution on windows machines
    - replace the username in the path with your local user where playwright was installed

### Note about playwright
- when the api responds for the dm endpoint that the executable does not exist check the path for temp folder and this exe might be packed again with the new path
- the current path to chromium when packed inside the exe during runtime is C:\Users\<username>\AppData\Local\Temp\_MEI198562\playwright\chromium\chrome-win

## Running application on Windows
- run the main.exe
- when the terminal opens and show successfull messages open browser and navigate to http://127.0.0.1:8000/docs
- open the wanted scraper endpoint and click on Try it out
- use the excel to transfer list of GITNs into the needed format - be careful with the brackets  only one pair of [] needs to be pasted
- close the terminal when done

### License note
- license is added to the ditribution files, added to the exe and also shown at start of the server