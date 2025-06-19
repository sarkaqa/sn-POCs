from Basketball.Reporting.ESPNPlayerReportStats import Espn_highestPTS
from Basketball.Reporting.REFPlayerReportStats import HighestPTS

# ANSI color codes for terminal output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

class Report:
    def __init__(self):
        self.espn_scraper = Espn_highestPTS()
        self.basketball_reference_scraper = HighestPTS()

    def generate_report(self, start_year, end_year):
        print("---------------------- BASKETBALL PTS COMPARISON REPORT ----------------------")
        report_lines = ["---------------------- BASKETBALL PTS COMPARISON REPORT ----------------------\n"]

        for year in range(start_year, end_year + 1):
            print(f"Processing year {year}...")

            br_result = self.basketball_reference_scraper.get_highest_pts_for_year(year)
            espn_result = self.espn_scraper.get_highest_pts_for_year(year)

            br_pts = self._extract_pts(br_result)
            espn_pts = self._extract_pts(espn_result)

            report_lines.append(f"Year: {year}")

            if br_pts is not None:
                print(f"{RESET}Basketball Reference PTS: {br_pts}{RESET}")
                report_lines.append(f"Basketball Reference PTS: {br_pts}")
            else:
                print(f"{YELLOW}Basketball Reference data not available for {year}.{RESET}")
                report_lines.append(f"Basketball Reference data not available.")

            if espn_pts is not None:
                print(f"{RESET}ESPN PTS: {espn_pts}{RESET}")
                report_lines.append(f"ESPN PTS: {espn_pts}")
            else:
                print(f"{YELLOW}ESPN data not available for {year}.{RESET}")
                report_lines.append(f"ESPN data not available.")

            if br_pts is not None and espn_pts is not None:
                if br_pts != espn_pts:
                    diff_line = f"Difference: {abs(br_pts - espn_pts)}"
                    print(f"{RED}{diff_line}{RESET}")
                    report_lines.append(f"!!! {diff_line} !!!")
                else:
                    same_line = f"No difference found: {br_pts}"
                    print(f"{RESET}{same_line}{RESET}")
                    report_lines.append(same_line)
                    #else:
                #print(f"{YELLOW}Comparison skipped due to missing data.{RESET}")
                #report_lines.append("Comparison skipped due to missing data.")

            print("--------------------------------------------")
            report_lines.append("-" * 60)

        # Save to file
        with open("comparison_report.txt", "w") as file:
            file.write("\n".join(report_lines))

        print("Report generated successfully!")

    def _extract_pts(self, result):
        """
        Try to extract the integer PTS value from the scraper's result.
        Assumes the result is a list with a string containing the points as the first item.
        """
        if isinstance(result, list) and result:
            text = result[0]
            for word in text.split():
                if word.isdigit():
                    return int(word)
        elif isinstance(result, int):
            return result
        return None

    def close(self):
        self.basketball_reference_scraper.close()
        self.espn_scraper.close()


# Example usage
if __name__ == "__main__":
    report = Report()
    report.generate_report(2020, 2025)
    report.close()
