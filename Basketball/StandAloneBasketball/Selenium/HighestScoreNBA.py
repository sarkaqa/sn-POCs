import time
import warnings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from Basketball.BasketballReference.results import ResultLog

warnings.filterwarnings("ignore", category=UserWarning, message=".*NotOpenSSLWarning.*")

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


class HighestScoreNBA:
    DEFAULT_YEAR_RANGE = (2022, 2025)

    def __init__(self, stat_key='fg3', year_range=None):
        self.driver = webdriver.Chrome()
        self.stat_key = stat_key
        self.year_range = year_range if year_range else self.DEFAULT_YEAR_RANGE
        self.logger = ResultLog(stat_key=stat_key, stat_labels=STAT_LABELS)

    def extract_score_and_row(self, row):
        try:
            ranker = row.find_element(By.XPATH, './/th[@data-stat="ranker"]')
            if not ranker.text.strip().isdigit():
                return None
            score_text = row.find_element(By.XPATH, f'.//td[@data-stat="{self.stat_key}"]').text
            score = int(score_text) if score_text.strip().isdigit() else 0
            return score, row
        except NoSuchElementException:
            return None

    def print_result(self, player_id, year, max_score, tied_games):
        stat_label = STAT_LABELS.get(self.stat_key.lower(), self.stat_key)
        season_label = f"season {year - 1}-{year}"
        for score, row in tied_games:
            date = row.find_element(By.XPATH, './/td[@data-stat="date"]').text
            ranker = row.find_element(By.XPATH, './/th[@data-stat="ranker"]').text
            message = (
                f"{player_id} tied for highest {stat_label} in {season_label}: {score} | Date: {date} | Rk: {ranker}"
                if len(tied_games) > 1 else
                f"{player_id} highest {stat_label} in {season_label}: {score} | Date: {date} | Rk: {ranker}"
            )
            self.logger.log_line(message)

    def process_table(self, table, player_id, year):
        rows = table.find_elements(By.TAG_NAME, 'tr')[1:]
        max_score = -1
        tied_games = []

        for row in rows:
            result = self.extract_score_and_row(row)
            if not result:
                continue

            score, row = result
            if score > max_score:
                max_score = score
                tied_games = [(score, row)]
            elif score == max_score:
                tied_games.append((score, row))

        if tied_games:
            self.print_result(player_id, year, max_score, tied_games)
            tied_dates = [
                row.find_element(By.XPATH, './/td[@data-stat="date"]').text for _, row in tied_games
            ]
            return {'value': max_score, 'dates': tied_dates}
        else:
            stat_label = STAT_LABELS.get(self.stat_key.lower(), self.stat_key)
            self.logger.log_line(f"No valid {stat_label} values found for {player_id} in {year}.")
            return None

    def get_highest_score_for_year(self, player_id, year):
        url = f'https://www.basketball-reference.com/players/{player_id[0]}/{player_id}/gamelog/{year}'
        self.driver.get(url)
        time.sleep(3)

        if "Page Not Found" in self.driver.title or "404" in self.driver.title:
            self.logger.log_line(f"Skipping {player_id} in {year} — page not found.")
            return None

        try:
            game_log_div = self.driver.find_element(By.ID, 'div_player_game_log_reg')
            if 'table_container' not in game_log_div.get_attribute('class'):
                self.logger.log_line(f"Error: Game log container missing for {player_id} in {year}.")
                return None

            table = game_log_div.find_element(By.TAG_NAME, 'table')
            return self.process_table(table, player_id, year)

        except NoSuchElementException:
            self.logger.log_line(f"No game log table found for {player_id} in {year}.")
            return None

    def get_available_seasons(self, player_id):
        available_seasons = []
        for year in range(*self.year_range):
            url = f'https://www.basketball-reference.com/players/{player_id[0]}/{player_id}/gamelog/{year}'
            self.driver.get(url)
            time.sleep(3)

            if "Page Not Found" in self.driver.title or "404" in self.driver.title:
                self.logger.log_line(f"Skipping {player_id} in {year} — page not found.")
                continue

            try:
                game_log_div = self.driver.find_element(By.ID, 'div_player_game_log_reg')
                if 'table_container' not in game_log_div.get_attribute('class'):
                    self.logger.log_line(f"Error: Game log container missing for {player_id} in {year}.")
                    continue
                available_seasons.append(year - 1)
            except NoSuchElementException:
                self.logger.log_line(f"No game log table found for {player_id} in {year}.")
                continue

        return available_seasons

    def get_highest_stat_per_season(self, player_id, stat_key=None):
        if stat_key:
            self.stat_key = stat_key

        highest_stats = {}
        available_seasons = self.get_available_seasons(player_id)
        for start_year in available_seasons:
            end_year = start_year + 1
            result = self.get_highest_score_for_year(player_id, end_year)
            if result:
                highest_stats[start_year] = result
        return highest_stats

    def run(self, players, year_range=None):
        # Allow overriding year_range at runtime
        if year_range:
            self.year_range = year_range

        for player_id in players:
            self.logger.log_section(f"Processing {player_id}")
            available_seasons = self.get_available_seasons(player_id)
            if available_seasons:
                self.logger.log_line(f"Available seasons for {player_id}: {', '.join(map(str, available_seasons))}")
                for start_year in available_seasons:
                    end_year = start_year + 1
                    self.get_highest_score_for_year(player_id, end_year)

    def quit(self):
        self.driver.quit()


if __name__ == "__main__":
    scraper = HighestScoreNBA()
    scraper.run(['jamesle01'])  # Default range (2006–2025)
    scraper.quit()
