import time
import requests
from collections import defaultdict
from Basketball.BasketballStatsData.statsResults import ResultLogger


class StatsHighestScoreNBA:
    STAT_LABELS = {
        "pointsByPeriod": "Highest Points in a Single Period",
    }

    def __init__(self, logger=None):
        self.logger = logger or ResultLogger(stat_key="pointsByPeriod", stat_labels=self.STAT_LABELS)

    def get_all_events_for_season(self, player_id, season):
        url = f'https://prod.origin.api.stats.com/v1/stats/basketball/nba/stats/players/{player_id}/events/?eventTypeId=1&season={season}'
        response = requests.get(url)
        event_ids = []

        if response.status_code == 200:
            try:
                data = response.json()
                for result in data.get('apiResults', []):
                    for player in result['league']['players']:
                        for season_data in player['seasons']:
                            if season_data['season'] != season:
                                continue
                            for event_type in season_data['eventType']:
                                for event in event_type['splits']:
                                    for game in event['events']:
                                        event_id = game.get('eventId')
                                        if event_id:
                                            event_ids.append(event_id)
            except Exception as e:
                self.logger.log_line(f"❌ Error processing data for player {player_id} in season {season}: {e}")
        else:
            self.logger.log_line(f"❌ Failed to retrieve data for player {player_id} in season {season} (status code: {response.status_code})")

        return event_ids

    def get_points_by_period_for_event(self, event_id, player_id, season):
        url = f"https://prod.origin.api.stats.com/v1/stats/basketball/NBA/events/{event_id}?pbp=true&accept=json"
        response = requests.get(url)

        if response.status_code != 200:
            self.logger.log_line(f"❌ Failed to fetch event {event_id} (status code: {response.status_code})")
            return

        try:
            data = response.json()
            pbp = (
                data.get("apiResults", [{}])[0]
                .get("league", {})
                .get("season", {})
                .get("eventType", [])[0]
                .get("events", [])[0]
                .get("pbp", [])
            )

            period_points = defaultdict(int)

            for play in pbp:
                if play.get("pointsScored", 0) > 0 and play.get("players"):
                    players = play["players"]
                    first_player = players[0] if players else None

                    if first_player and first_player.get("playerId") == player_id:
                        period = play.get("period")
                        if period in [1, 2, 3, 4]:
                            period_points[period] += play["pointsScored"]

            self.logger.log_line(f"\nPoints scored by player {player_id} in event {event_id} in season {season}:")
            for period in range(1, 5):
                points = period_points.get(period, 0)
                self.logger.log_line(f"  Period {period}: {points} pts")

        except Exception as e:
            self.logger.log_line(f"❌ Error parsing play-by-play data for event {event_id}: {e}")

    def process_season(self, player_id, season):
        event_ids = self.get_all_events_for_season(player_id, season)

        if event_ids:
            self.logger.log_line(f"\n✅ Found {len(event_ids)} eventId(s) for player {player_id} in season {season}:")
            for i in range(0, len(event_ids), 10):
                self.logger.log_line(", ".join(str(eid) for eid in event_ids[i:i + 10]))

            for event_id in event_ids:
                self.get_points_by_period_for_event(event_id, player_id, season)
        else:
            self.logger.log_line(f"\n⚠️ No eventIds found for player {player_id} in season {season}.")


if __name__ == '__main__':
    player_id = 1175367
    start_year = 2019
    end_year = 2021

    logger = ResultLogger(stat_key="pointsByPeriod", stat_labels=StatsHighestScoreNBA.STAT_LABELS)

    instance = StatsHighestScoreNBA(logger=logger)
    start = time.time()

    for season in range(start_year, end_year + 1):
        instance.process_season(player_id, season)

    elapsed = time.time() - start
    logger.log_line(f"\nFinished in {int(elapsed // 60)} min {int(elapsed % 60)} sec.")
