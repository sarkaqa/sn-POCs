from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
from Basketball.BasketballReference.results import ResultLogger

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

STAT_KEY = 'fg3'  # Change as needed

# Correct logger initialization
logger = ResultLogger(stat_key=STAT_KEY, stat_labels=STAT_LABELS)

driver = webdriver.Chrome()

def extract_score_and_row(row, stat_key):
    try:
        ranker = row.find_element(By.XPATH, './/th[@data-stat="ranker"]')
        if not ranker.text.strip().isdigit():
            return None
        score = int(row.find_element(By.XPATH, f'.//td[@data-stat="{stat_key}"]').text)
        return score, row
    except NoSuchElementException:
        return None


def print_result(player_id, year, max_score, tied_games, stat_label, logger):
    season_label = f"season {year - 1}-{year}"
    for score, row in tied_games:
        date = row.find_element(By.XPATH, './/td[@data-stat="date_game"]').text
        ranker = row.find_element(By.XPATH, './/th[@data-stat="ranker"]').text
        message = (
            f"{player_id.upper()} tied for highest {stat_label} in {season_label}: {score} | Date: {date} | Rk: {ranker}"
            if len(tied_games) > 1 else
            f"{player_id.upper()} highest {stat_label} in {season_label}: {score} | Date: {date} | Rk: {ranker}"
        )
        logger.log_line(message)



def process_table(table, player_id, year, stat_key, logger):
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
        print_result(player_id, year, max_score, tied_games, stat_label, logger)
    else:
        logger.log_line(f"No valid {stat_label} values found for {player_id} in {year}.")


def get_highest_score_for_year(player_id, year, stat_key, logger):
    url = f'https://www.basketball-reference.com/wnba/players/{player_id[0]}/{player_id}/gamelog/{year}'
    driver.get(url)
    time.sleep(3)

    try:
        game_log_div = driver.find_element(By.ID, 'div_wnba_pgl_basic')
        if 'table_container' not in game_log_div.get_attribute('class'):
            logger.log_line(f"Error: Game log container class mismatch for {player_id} in {year}.")
            return

        table = game_log_div.find_element(By.TAG_NAME, 'table')
        if not table:
            logger.log_line(f"Error: Table not found for {player_id} in {year}.")
            return

        process_table(table, player_id, year, stat_key, logger)

    except NoSuchElementException:
        logger.log_line(f"Error: Game log not found for {player_id} in {year}.")


#players = ['bonnede01w', 'mccouan01w', 'ogwumnn01w', 'charlti01w', 'tauradi01w']
players = ['bonnede01w']

for player in players:
    logger.log_section(f"Processing stats for {player.upper()}")
    for year in range(2023, 2026):
        get_highest_score_for_year(player, year, STAT_KEY, logger)

driver.quit()
