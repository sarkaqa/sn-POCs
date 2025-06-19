from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time

# === CONFIGURATION ===

STAT_LABELS = {
    'fg': 'Field Goals',
    'fg3': 'Three Point Field Goals',
    'fg2': 'Two Point Field Goals',
    'ft': 'Free Throws',
    'trb': 'Total Rebounds',
    'ast': 'Assists',
    'stl': 'Steals',
    'blk': 'Blocks',
    'tov': 'Turnovers',
    'pf': 'Personal Fouls',
    'pts': 'Points'
}

STAT_KEY = 'fg3'  # Change stat key if needed
PLAYERS = ['jamesle01']  # Example: LeBron James
SEASON_YEARS = [2023, 2024]  # Regular season years like 2022–23 => 2023

# === LOGGING ===

class SimpleLogger:
    def __init__(self):
        pass

    def log_line(self, msg):
        print(msg)

    def log_section(self, title):
        print("=" * 50)
        print(title)
        print("=" * 50)


logger = SimpleLogger()

# === FUNCTIONAL HELPERS ===

def extract_score_and_row(row, stat_key):
    try:
        ranker = row.find_element(By.XPATH, './/th[@data-stat="ranker"]')
        if not ranker.text.strip().isdigit():
            return None
        cell = row.find_element(By.XPATH, f'.//td[@data-stat="{stat_key}"]')
        score = int(cell.text.strip()) if cell.text.strip().isdigit() else 0
        return score, row
    except NoSuchElementException:
        return None


def print_result(player_id, year, max_score, tied_games, stat_label):
    season_label = f"season {year - 1}-{year}"
    for score, row in tied_games:
        date = row.find_element(By.XPATH, './/td[@data-stat="date"]').text
        ranker = row.find_element(By.XPATH, './/th[@data-stat="ranker"]').text
        message = (
            f"{player_id.upper()} tied for highest {stat_label} in {season_label}: {score} | Date: {date} | Rk: {ranker}"
            if len(tied_games) > 1 else
            f"{player_id.upper()} highest {stat_label} in {season_label}: {score} | Date: {date} | Rk: {ranker}"
        )
        logger.log_line(message)


def process_table(table, player_id, year, stat_key):
    rows = table.find_elements(By.TAG_NAME, 'tr')[1:]
    max_score = -1
    tied_games = []
    stat_label = STAT_LABELS.get(stat_key.lower(), stat_key)

    for row in rows:
        result = extract_score_and_row(row, stat_key)
        if not result:
            continue

        score, row = result
        if score > max_score:
            max_score = score
            tied_games = [(score, row)]
        elif score == max_score:
            tied_games.append((score, row))

    if tied_games:
        print_result(player_id, year, max_score, tied_games, stat_label)
    else:
        logger.log_line(f"No valid {stat_label} values found for {player_id} in {year}.")


def get_highest_score_for_year(driver, player_id, year, stat_key):
    url = f'https://www.basketball-reference.com/players/{player_id[0]}/{player_id}/gamelog/{year}'
    driver.get(url)
    time.sleep(3)

    try:
        game_log_div = driver.find_element(By.ID, 'div_player_game_log_reg')
        if 'table_container' not in game_log_div.get_attribute('class'):
            logger.log_line(f"[ERROR] Unexpected table structure for {player_id} in {year}")
            return

        table = game_log_div.find_element(By.TAG_NAME, 'table')
        process_table(table, player_id, year, stat_key)

    except NoSuchElementException:
        logger.log_line(f"[ERROR] Could not find data for {player_id} in {year}")


# === MAIN SCRIPT EXECUTION ===

def main():
    logger.log_section("NBA STAT COMPARISON (Selenium)")

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Remove if you want to see browser
    with webdriver.Chrome(options=options) as driver:
        for player_id in PLAYERS:
            logger.log_section(f"Processing stats for {player_id.upper()}")
            for season in SEASON_YEARS:
                get_highest_score_for_year(driver, player_id, season, STAT_KEY)


if __name__ == '__main__':
    main()
