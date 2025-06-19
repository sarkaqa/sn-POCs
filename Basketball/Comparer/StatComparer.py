from Basketball.BasketballReference.RefPlayerData.HighestScoreNBA import HighestScoreNBA as SeleniumStatSource
from Basketball.BasketballStatsData.PlayerData.StatsHighestScoreNBA import StatsHighestScoreNBA as APIStatSource


class StatComparer:
    STAT_KEY_TRANSLATION = {
        'fg3': 'threePointFieldGoals',
        'fg': 'fieldGoals',
        'ft': 'freeThrows',
        'trb': 'rebounds',
        'ast': 'assists',
        'stl': 'steals',
        'blk': 'blockedShots',
        'tov': 'turnovers',
        'pf': 'personalFouls',
        'pts': 'points',
    }

    def __init__(self, player_id_ref, player_id_api, logger, stat_key, stat_label, player_name):
        self.player_id_ref = player_id_ref
        self.player_id_api = player_id_api
        self.logger = logger
        self.stat_key = stat_key
        self.stat_label = stat_label
        self.player_name = player_name

    def compare_stats(self, selenium_data, api_data, start_year=None, end_year=None):
        if not selenium_data or not api_data:
            return [{
                "status": "ERROR",
                "message": f"No data for {self.player_name}"
            }]

        seasons = sorted(set(selenium_data.keys()) & set(api_data.keys()))
        if start_year is not None:
            seasons = [s for s in seasons if s >= start_year]
        if end_year is not None:
            seasons = [s for s in seasons if s <= end_year]

        results = []

        for season in seasons:
            selenium_stat = selenium_data.get(season)
            api_stat = api_data.get(season)

            if not selenium_stat or not api_stat:
                continue

            match_dates = set(selenium_stat["dates"]) & set(api_stat["dates"])
            mismatch_dates = (set(selenium_stat["dates"]) | set(api_stat["dates"])) - match_dates

            for date in match_dates:
                tag = "Tied" if len(selenium_stat["dates"]) > 1 or len(api_stat["dates"]) > 1 else ""
                label = f"{self.stat_label} {tag}".strip()
                results.append({
                    "status": "MATCH",
                    "season": season,
                    "label": label,
                    "value": api_stat['value'],
                    "date": date
                })

            for date in mismatch_dates:
                tag = "Tied" if len(selenium_stat["dates"]) > 1 or len(api_stat["dates"]) > 1 else ""
                label = f"{self.stat_label} {tag}".strip()
                results.append({
                    "status": "MISMATCH",
                    "season": season,
                    "label": label,
                    "value": api_stat['value'],
                    "date": date
                })

        return results
