import requests
import xml.etree.ElementTree as ET
from Basketball.BasketballStatsData.statsResults import ResultLogger


class StatsHighestScoreNBA:
    STAT_LABELS = {
        'points': 'Points',
        'assists': 'Assists',
        'steals': 'Steals',
        'blockedShots': 'Blocks',
        'turnovers': 'Turnovers',
        'personalFouls': 'Personal Fouls',
        'rebounds': 'Total Rebounds',
        'offensiveRebounds': 'Offensive Rebounds',
        'defensiveRebounds': 'Defensive Rebounds',
        'fieldGoals': 'Field Goals Made',
        'fieldGoalsAttempted': 'Field Goals Attempted',
        'threePointFieldGoals': 'Three Point Field Goals Made',
        'threePointFieldGoalsAttempted': 'Three Point Field Goals Attempted',
        'freeThrows': 'Free Throws Made',
        'freeThrowsAttempted': 'Free Throws Attempted',
    }

    STAT_EXTRACTORS = {
        'points': lambda stats: stats.get('points', 0),
        'assists': lambda stats: stats.get('assists', 0),
        'steals': lambda stats: stats.get('steals', 0),
        'blockedShots': lambda stats: stats.get('blockedShots', 0),
        'turnovers': lambda stats: stats.get('turnovers', 0),
        'personalFouls': lambda stats: stats.get('personalFouls', 0),
        'rebounds': lambda stats: stats.get('rebounds', {}).get('total', 0),
        'offensiveRebounds': lambda stats: stats.get('rebounds', {}).get('offensive', 0),
        'defensiveRebounds': lambda stats: stats.get('rebounds', {}).get('defensive', 0),
        'fieldGoals': lambda stats: stats.get('fieldGoals', {}).get('made', 0),
        'fieldGoalsAttempted': lambda stats: stats.get('fieldGoals', {}).get('attempted', 0),
        'threePointFieldGoals': lambda stats: stats.get('threePointFieldGoals', {}).get('made', 0),
        'threePointFieldGoalsAttempted': lambda stats: stats.get('threePointFieldGoals', {}).get('attempted', 0),
        'freeThrows': lambda stats: stats.get('freeThrows', {}).get('made', 0),
        'freeThrowsAttempted': lambda stats: stats.get('freeThrows', {}).get('attempted', 0),
    }

    def extract_game_stats(self, game, stat_key):
        try:
            player_stats = game.get('playerStats', {})
            extractor = self.STAT_EXTRACTORS.get(stat_key)
            if extractor is None:
                return None, None, None

            value = extractor(player_stats)
            start_date_list = game.get('startDate', [])
            eastern_date = next((d.get('full') for d in start_date_list if d.get('dateType') == 'Eastern'), None)
            date_only = eastern_date.split('T')[0] if eastern_date else None
            event_id = game.get('eventId')

            return value, date_only, event_id
        except Exception:
            return None, None, None

    def get_available_seasons(self, player_id):
        url = f'https://prod.origin.api.stats.com/v1/stats/basketball/nba/stats/players/{player_id}?eventTypeId=1&enc=true&careerOnly=false'
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/xml',
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            try:
                content = response.content.decode('utf-8-sig').strip()
                root = ET.fromstring(content)
                seasons = root.find('.//players/player/seasons')
                if seasons is None:
                    print(f"No seasons found for player {player_id}")
                    return []

                year_list = []
                for season_node in seasons.findall('season'):
                    year_elem = season_node.find('season')
                    if year_elem is not None and year_elem.text and year_elem.text.isdigit():
                        year_list.append(int(year_elem.text))

                return year_list
            except ET.ParseError as e:
                print(f"Error parsing XML for player {player_id}: {e}")
        else:
            print(f"Failed to fetch data for player {player_id}, status code: {response.status_code}")
        return []

    def get_highest_stat_for_season(self, player_id, season, stat_key, logger=None):
        url = f'https://prod.origin.api.stats.com/v1/stats/basketball/nba/stats/players/{player_id}/events/?eventTypeId=1&season={season}'
        response = requests.get(url)

        if response.status_code == 200:
            try:
                data = response.json()
                if 'apiResults' not in data:
                    if logger:
                        logger.log_line(f"No 'apiResults' found for player {player_id} in season {season}.")
                    return None

                stat_values = []
                game_dates = []
                event_ids = []

                for result in data['apiResults']:
                    for player in result['league']['players']:
                        for season_data in player['seasons']:
                            if season_data['season'] != season:
                                continue
                            for event_type in season_data['eventType']:
                                for event in event_type['splits']:
                                    for game in event['events']:
                                        value, game_date, event_id = self.extract_game_stats(game, stat_key)
                                        if value is not None:
                                            stat_values.append(value)
                                            game_dates.append(game_date)
                                            event_ids.append(event_id)

                if not stat_values:
                    if logger:
                        logger.log_line(
                            f"No {self.STAT_LABELS.get(stat_key, stat_key)} data found for player {player_id} in season {season}.")
                    return None

                max_value = max(stat_values)
                tied_indices = [i for i, val in enumerate(stat_values) if val == max_value]
                stat_label = self.STAT_LABELS.get(stat_key, stat_key)
                season_label = f"season {season} - {season + 1}"

                tied_dates = []
                for i in tied_indices:
                    date = game_dates[i]
                    event_id = event_ids[i]
                    tied_dates.append(date)
                    message = (
                        f"{player_id} tied for highest {stat_label} in {season_label}: {max_value} | Game Date: {date} | Event ID: {event_id}"
                        if len(tied_indices) > 1 else
                        f"{player_id} highest {stat_label} in {season_label}: {max_value} | Game Date: {date} | Event ID: {event_id}"
                    )
                    if logger:
                        logger.log_line(message)

                return {'value': max_value, 'dates': tied_dates}

            except Exception as e:
                if logger:
                    logger.log_line(f"Error processing data for player {player_id} in season {season}: {e}")
        else:
            if logger:
                logger.log_line(
                    f"Failed to retrieve data for player {player_id} in season {season} (status code: {response.status_code})")
        return None

    def get_highest_stat_per_season(self, player_id, stat_key, logger=None, start_year=None, end_year=None):
        all_seasons = self.get_available_seasons(player_id)

        if start_year is not None or end_year is not None:
            seasons = [s for s in all_seasons if
                       (start_year is None or s >= start_year) and
                       (end_year is None or s <= end_year)]
        else:
            seasons = all_seasons

        results = {}
        for season in seasons:
            result = self.get_highest_stat_for_season(player_id, season, stat_key, logger=logger)
            if result:
                results[season] = result
        return results


if __name__ == '__main__':
    STAT_KEY = 'threePointFieldGoals'
    players = [214152]
    logger = ResultLogger(stat_key=STAT_KEY, stat_labels=StatsHighestScoreNBA.STAT_LABELS)

    for player_id in players:
        logger.log_section(f"Processing stats for player {player_id} (limited range: 2003–2012)")
        data_range = StatsHighestScoreNBA().get_highest_stat_per_season(
            player_id, STAT_KEY, logger=logger, start_year=2005, end_year=2025
        )
