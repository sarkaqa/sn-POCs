import time
from colorama import Fore, Style
from Basketball.BasketballReference.RefPlayerData.HighestScoreNBA import HighestScoreNBA as SeleniumSource
from Basketball.BasketballStatsData.PlayerData.StatsHighestScoreNBA import StatsHighestScoreNBA as APISource
from Basketball.Comparer.StatComparer import StatComparer
from Basketball.Comparer.ResultLogger import ResultLogger

# Setup
log_file_path = "logs/three_point_comparison.log"
logger = ResultLogger(log_file_path)

# Player mapping: {BasketballReference ID: (Stats.com ID, Full Name)}
player_mapping = {
    "curryst01": ("338365", "Stephen Curry"),
    # Add more players here
}

# Configuration
stat_key = "ast"
stat_label = "Assists"
start_year = 2023
end_year = 2025

# Start timing
overall_start = time.time()

# Process each player
for player_ref_id, (player_api_id, player_name) in player_mapping.items():
    logger.log_main_header(f"Processing stats for {player_name}")

    # GAME LOG CHECK SECTION
    logger.log_subsection("Game log availability checking:")
    selenium = SeleniumSource(stat_key=stat_key, year_range=(start_year, end_year))

    for year in range(start_year, end_year + 1):
        season_label = f"season {year - 1}-{year}"
        url = f'https://www.basketball-reference.com/players/{player_ref_id[0]}/{player_ref_id}/gamelog/{year}'
        selenium.driver.get(url)
        time.sleep(2)

        if "Page Not Found" in selenium.driver.title or "404" in selenium.driver.title:
            logger.log_line(f"Checking {season_label}... {Fore.RED}❌ Page not found{Style.RESET_ALL}", color=Fore.RED)
            continue

        try:
            game_log_div = selenium.driver.find_element("id", 'div_player_game_log_reg')
            if 'table_container' not in game_log_div.get_attribute('class'):
                logger.log_line(f"Checking {season_label}... {Fore.RED}❌ No table container{Style.RESET_ALL}", color=Fore.RED)
            else:
                logger.log_line(f"Checking {season_label}... {Fore.GREEN}✅{Style.RESET_ALL}", color=Fore.GREEN)
        except:
            logger.log_line(f"Checking {season_label}... {Fore.RED}❌ No game log{Style.RESET_ALL}", color=Fore.RED)

    # API GAME LOG CHECK SECTION
    logger.log_section_header(f"Stats API for {player_name}")
    api = APISource()
    api_stats = {}
    for year in range(start_year, end_year + 1):
        season_label = f"season {year} - {year + 1}"
        msg = f"Checking {season_label} via API... "
        result = api.get_highest_stat_for_season(
            player_api_id,
            year,
            stat_key=StatComparer.STAT_KEY_TRANSLATION.get(stat_key, stat_key),
            logger=None
        )
        if result:
            logger.log_line(f"{msg}{Fore.GREEN}✅{Style.RESET_ALL}", color=Fore.GREEN)
            api_stats[year - 1] = result
        else:
            logger.log_line(f"{msg}{Fore.RED}❌{Style.RESET_ALL}", color=Fore.RED)

    # RETRIEVE AND LOG SELENIUM STATS
    logger.log_section_header(f"Basketball Reference for {player_name}")
    selenium_stats = selenium.get_highest_stat_per_season(player_ref_id)
    for season in sorted(selenium_stats):
        tied_rows = selenium_stats[season].get("rows", [])
        tag = "tied for " if len(tied_rows) > 1 else ""
        for row in tied_rows:
            msg = f"{player_ref_id} {tag}highest {stat_label} in season {season}-{season + 1}: {row['value']} | Date: {row['date']} | Rk: {row['rk']}"
            logger.log_line(msg)

    # RETRIEVE AND LOG API STATS
    logger.log_section_header(f"Stats API for {player_name}")
    api_stats = api.get_highest_stat_per_season(
        player_api_id,
        stat_key=StatComparer.STAT_KEY_TRANSLATION.get(stat_key, stat_key),
        logger=logger,
        start_year=start_year,
        end_year=end_year
    )
    for season in sorted(api_stats):
        tied_rows = api_stats[season].get("rows", [])
        tag = "tied for " if len(tied_rows) > 1 else ""
        for row in tied_rows:
            msg = f"{player_api_id} {tag}highest {stat_label} Made in season {season} - {season + 1}: {row['value']} | Game Date: {row['date']} | Event ID: {row['event_id']}"
            logger.log_line(msg)

    # COMPARISON SECTION (only MATCH/MISMATCH lines)
    logger.log_section_header(f"COMPARISON OF  Basketball Reference VS STATS API for {player_name}")
    comparer = StatComparer(
        player_id_ref=player_ref_id,
        player_id_api=player_api_id,
        logger=logger,
        stat_key=stat_key,
        stat_label=stat_label,
        player_name=player_name
    )
    comparison_results = comparer.compare_stats(
        start_year=start_year,
        end_year=end_year,
        selenium_data=selenium_stats,
        api_data=api_stats
    )

    for entry in comparison_results:
        season = entry["season"]
        label = entry["label"]
        value = entry["value"]
        date = entry["date"]
        if entry["status"] == "MATCH":
            msg = f"{Fore.GREEN}[MATCH]{Style.RESET_ALL} {player_api_id} {label} in {season}: {Fore.GREEN}{value}{Style.RESET_ALL} on {Fore.GREEN}{date}{Style.RESET_ALL}"
        elif entry["status"] == "MISMATCH":
            msg = f"{Fore.RED}[MISMATCH]{Style.RESET_ALL} {player_api_id} {label} in {season}: {Fore.RED}{value}{Style.RESET_ALL} on {Fore.RED}{date}{Style.RESET_ALL}"
        else:
            msg = f"[{entry['status']}] {entry['message']}"
        logger.log_line(msg)

# End timing
elapsed = time.time() - overall_start
minutes = int(elapsed // 60)
seconds = int(elapsed % 60)
logger.log_colored_subsection(f"Total run time: {minutes} min {seconds} sec", color=Fore.CYAN)
