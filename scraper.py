from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

# Initialize the WebDriver
driver = webdriver.Chrome()

# Function to extract highest PTS for a specific year
def get_highest_pts_for_year(year):
    try:
        # Open the webpage for the given year on ESPN
        driver.get(f'https://www.espn.com/nba/player/gamelog/_/id/1966/type/nba/year/{year}')

        # Wait for the page to load and the relevant elements to be present
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'mb5')))

        # Find all div elements with the class 'mb5' (each represents a season's table)
        season_divs = driver.find_elements(By.CLASS_NAME, 'mb5')

        # Initialize a variable to track the highest PTS for the entire season
        max_pts_season = -1
        tied_rows = []  # To store all rows where the max PTS is matched

        # Loop through each div (season)
        for season_div in season_divs:
            try:
                # Find the table within the current div (season)
                table = season_div.find_element(By.TAG_NAME, 'table')

                # If table is found, proceed to extract data
                if table:
                    # Find all header rows to identify column positions
                    headers = table.find_elements(By.TAG_NAME, 'th')
                    pts_column_index = None
                    date_column_index = 0  # Assuming the first column is Date

                    # Loop through headers to find the "PTS" column
                    for i, header in enumerate(headers):
                        if "Points" in header.get_attribute("title"):
                            pts_column_index = i

                    # Ensure we found the correct column
                    if pts_column_index is None:
                        return

                    # Find all rows in the table (skip the header row)
                    rows = table.find_elements(By.TAG_NAME, 'tr')[1:]

                    # Iterate through the rows (games)
                    for row in rows:
                        try:
                            # Extract the PTS values and Date values from the row
                            cells = row.find_elements(By.CLASS_NAME, 'Table__TD')

                            # Ensure there are enough columns to extract PTS and Date
                            if len(cells) > pts_column_index and len(cells) > date_column_index:
                                pts = int(cells[pts_column_index].text)  # Extract the PTS value
                                game_date = cells[date_column_index].text.strip()  # Extract the game date

                                # If the current PTS is greater than the maximum, update max_pts_season
                                if pts > max_pts_season:
                                    max_pts_season = pts
                                    tied_rows = [(pts, game_date)]  # Reset the tied rows with the new highest PTS
                                elif pts == max_pts_season:
                                    tied_rows.append((pts, game_date))  # Add this tied PTS and Date to the list

                        except NoSuchElementException:
                            # Skip rows where data is missing
                            continue

            except NoSuchElementException:
                continue

        # After processing all tables, print the highest PTS or tied PTS with the formatted date
        if max_pts_season != -1:
            if len(tied_rows) > 1:
                # If there are multiple occurrences of the highest PTS, print the "Tied" version
                for tied_pt, game_date in tied_rows:
                    # Convert the game date format (assume it's like 'Sun 12/24')
                    date_obj = datetime.strptime(game_date, '%a %m/%d')
                    formatted_date = date_obj.replace(year=year).strftime('%m-%d')  # '%Y-%m-%d' Format as 'YYYY-MM-DD', i've removed the year
                    print(f"Tied for highest PTS in season {year}: {tied_pt} | Game Date: {formatted_date}")
            else:
                # If there's only one occurrence of the highest PTS, print it normally
                tied_pt, game_date = tied_rows[0]
                date_obj = datetime.strptime(game_date, '%a %m/%d')
                formatted_date = date_obj.replace(year=year).strftime('%m-%d') # '%Y-%m-%d' Format as 'YYYY-MM-DD'
                print(f"Highest PTS in season {year}: {tied_pt} | Game Date: {formatted_date}")

        else:
            print(f"No valid PTS values found for {year}.")

    except (NoSuchElementException, TimeoutException):
        print(f"Error: Couldn't find the game log div for {year} or page load took too long.")

# Loop over the years from 2015 to 2025 and fetch the highest PTS for each season
for year in range(2015, 2026):  # Adjust the range as necessary
    get_highest_pts_for_year(year)

# Close the browser after processing all years
driver.quit()
