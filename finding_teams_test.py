import requests
from bs4 import BeautifulSoup

# API URL
top_url = 'https://ncaa-api.henrygd.me/rankings/softball/d1/espncom/usa-softball'

# Fetch rankings data
response = requests.get(top_url)
data = response.json()

# Extract top 25 teams and normalize names
TOP25 = {team['COLLEGE'].split(' (')[0].strip() for team in data.get('data', [])[:25]}

# Website URL
URL = "https://www.sportsmediawatch.com/tv-schedules/college-softball-tv-schedule/"

def scrape_schedule():
    """Scrape today's college softball games and filter only Top 25 matchups."""
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "html.parser")

    games = []

    # Locate the "Today" section using <a name="Today">
    today_section = soup.find("a", {"name": "Today"})
    if not today_section:
        print("Could not find 'Today' section.")
        return games

    # Find the next table containing games for today
    today_table = today_section.find_next("table", class_="schedule-table")
    
    if not today_table:
        print("No games listed for today.")
        return games

    # Extract game details by looking for <td> with "Time (ET)"
    time_cells = today_table.find_all("td", {"data-label": "Time (ET)"})
    game_cells = today_table.find_all("td", {"data-label": "Game / TV"})

    if not time_cells or not game_cells:
        print("No valid game rows found.")
        return games

    # Iterate over extracted time and game cells
    for time_cell, game_cell in zip(time_cells, game_cells):
        game_time = time_cell.text.strip()
        matchup = game_cell.find("div", class_="matchup-details")
        network = game_cell.find("div", class_="tv-details")

        if matchup:
            teams = matchup.text.strip()
            team_names = [t.strip() for t in teams.split(" vs ")]

            # Exact match check
            if any(team in TOP25 for team in team_names):
                channel = network.text.strip() if network else "Unknown Channel"
                games.append(f"{teams} @ {game_time} on {channel}")

    return games

today_games = scrape_schedule()
print("\nToday's Games for Selected Teams:")
print("\n".join(today_games) if today_games else "No games found for today.")
