import time
import requests
from Basketball.BasketballStatsData.statsResults import ResultLogger

EVENT_LABELS = {
    1: "Free Throws Made",
    2: "Free Throws Missed",
    3: "Field Goals Made",
    4: "Field Goals Missed",
    5: "Three Pointers Made",
    6: "Three Pointers Missed"
}


class StreakTracker:
    def __init__(self, player_id, play_event_id=1, break_event_id=2, threshold=10, logger=None):
        self.player_id = player_id
        self.play_event_id = play_event_id
        self.break_event_id = break_event_id
        self.threshold = threshold
        self.logger = logger or ResultLogger(stat_key=str(play_event_id), stat_labels=EVENT_LABELS)

    def fetch_event_ids_for_season(self, season):
        url = f'https://prod.origin.api.stats.com/v1/stats/basketball/nba/stats/players/{self.player_id}/events/?eventTypeId=1&season={season}'
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
                                        eid = game.get('eventId')
                                        if eid:
                                            event_ids.append(eid)
            except Exception as e:
                self.logger.log_line(f"Error fetching event IDs for season {season}: {e}")
        return event_ids

    def fetch_pbp_for_event(self, event_id):
        url = f"https://prod.origin.api.stats.com/v1/stats/basketball/NBA/events/{event_id}?pbp=true&accept=json"
        response = requests.get(url)
        if response.status_code != 200:
            self.logger.log_line(f"❌ Failed to fetch pbp for event {event_id}")
            return []

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
            for play in pbp:
                play["eventId"] = event_id
            return pbp
        except Exception as e:
            self.logger.log_line(f"❌ Error parsing pbp for event {event_id}: {e}")
            return []

    def compute_all_streaks(self, pbp, initial_streak=0, initial_start=None):
        streaks = []
        current_streak = initial_streak
        current_start = initial_start

        for play in pbp:
            if not play.get("players") or not play.get("playEvent"):
                continue

            first_player = play["players"][0]
            event_id = play["eventId"]
            play_id = play["playId"]
            if first_player.get("playerId") != self.player_id:
                continue

            ev = play["playEvent"].get("playEventId")
            if ev == self.play_event_id:
                if current_streak == 0:
                    current_start = (event_id, play_id)
                current_streak += 1
            elif ev == self.break_event_id:
                if current_streak >= self.threshold:
                    streaks.append((current_streak, current_start, (event_id, play_id)))
                current_streak = 0
                current_start = None

        return streaks, current_streak, current_start

    def get_longest_streak_per_season(self, start_season, end_season):
        for season in range(start_season, end_season + 1):
            event_ids = self.fetch_event_ids_for_season(season)
            self.logger.log_section(f"Analyzing {EVENT_LABELS.get(self.play_event_id, 'Plays')} for player {self.player_id} in season {season}...")

            all_streaks = []
            carry_streak = 0
            carry_start = None
            last_play = None
            last_event = None

            for idx, eid in enumerate(event_ids, 1):
                print(f"{eid}", end=", " if idx < len(event_ids) else "\n", flush=True)
                pbp = self.fetch_pbp_for_event(eid)
                streaks, carry_streak, carry_start = self.compute_all_streaks(pbp, carry_streak, carry_start)
                all_streaks.extend(streaks)

                # Keep last event/play if continuing
                if carry_streak > 0:
                    last_event = eid
                    last_play = pbp[-1]["playId"] if pbp else None

            # Final carryover check at season end
            if carry_streak >= self.threshold:
                all_streaks.append((carry_streak, carry_start, (last_event, last_play)))

            if not all_streaks:
                self.logger.log_line(f"⚠️ Season {season}: No streak ≥ {self.threshold}")
                continue

            longest = max(all_streaks, key=lambda s: s[0])
            self.logger.log_line(
                f"✅ Season {season}: Longest streak = {longest[0]} made "
                f"(Start: Event {longest[1][0]}, Play {longest[1][1]} → "
                f"End: Event {longest[2][0]}, Play {longest[2][1]})"
            )

            for streak in all_streaks:
                if streak != longest:
                    self.logger.log_line(
                        f"✅ - {streak[0]} made "
                        f"(Start: Event {streak[1][0]}, Play {streak[1][1]} → "
                        f"End: Event {streak[2][0]}, Play {streak[2][1]})"
                    )


if __name__ == '__main__':
    player_id = 551768
    play_event_id = 1
    break_event_id = 2
    threshold = 10
    start_year = 2020
    end_year = 2021

    logger = ResultLogger(stat_key=str(play_event_id), stat_labels=EVENT_LABELS)
    tracker = StreakTracker(player_id, play_event_id, break_event_id, threshold, logger)

    start = time.time()
    tracker.get_longest_streak_per_season(start_year, end_year)
    elapsed = time.time() - start
    print(f"\nFinished in {int(elapsed // 60)} min {int(elapsed % 60)} sec.")
