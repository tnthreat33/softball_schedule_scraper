# api/schedule.py
import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Teams to track
FAV_TEAMS = ["Indiana", "Louisville", "Butler", "Northwestern"]
SEC_TEAMS = [
    "Alabama", "Arkansas", "Auburn", "Florida", "Georgia", "Kentucky",
    "LSU", "Mississippi State", "Missouri", "Ole Miss", "South Carolina",
    "Tennessee", "Texas A&M", "Vanderbilt"
]

# API URL for rankings
top_url = 'https://ncaa-api.henrygd.me/rankings/softball/d1/espncom/usa-softball'

# Fetch rankings data
response = requests.get(top_url)
data = response.json()

# Extract top 25 teams and normalize names
TOP25 = {team['COLLEGE'].split(' (')[0].strip() for team in data.get('data', [])[:25]}

# Website URL
URL = "https://www.sportsmediawatch.com/tv-schedules/college-softball-tv-schedule/"

# Gmail credentials
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_PASS = os.getenv('GMAIL_PASS')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')

def scrape_schedule():
    """Scrape today's college softball games and categorize them into Favorite, SEC, and Top 25 teams."""
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "html.parser")

    fav_games = []
    sec_games = []
    top25_games = []

    # Locate the "Today" section
    today_section = soup.find("a", {"name": "Today"})
    if not today_section:
        print("Could not find 'Today' section.")
        return fav_games, sec_games, top25_games

    # Find today's schedule table
    today_table = today_section.find_next("table", class_="schedule-table")
    
    if not today_table:
        print("No games listed for today.")
        return fav_games, sec_games, top25_games

    # Extract game details
    time_cells = today_table.find_all("td", {"data-label": "Time (ET)"})
    game_cells = today_table.find_all("td", {"data-label": "Game / TV"})

    if not time_cells or not game_cells:
        print("No valid game rows found.")
        return fav_games, sec_games, top25_games

    # Categorize games
    for time_cell, game_cell in zip(time_cells, game_cells):
        game_time = time_cell.text.strip()
        matchup = game_cell.find("div", class_="matchup-details")
        network = game_cell.find("div", class_="tv-details")

        if matchup:
            teams = matchup.text.strip()
            team_names = [t.strip() for t in teams.split(" vs ")]
            channel = network.text.strip() if network else "Unknown Channel"
            game_info = f"{teams} @ {game_time} on {channel}"

            if any(team in FAV_TEAMS for team in team_names):
                fav_games.append(game_info)
            elif any(team in SEC_TEAMS for team in team_names):
                sec_games.append(game_info)
            elif any(team in TOP25 for team in team_names):
                top25_games.append(game_info)

    return fav_games, sec_games, top25_games

def send_email(fav_games, sec_games, top25_games):
    """Send an email with the categorized game schedule."""
    if not (fav_games or sec_games or top25_games):
        print("No games found for tracked teams today.")
        return  

    subject = "College Softball Schedule - Today's Games"
    body = ""

    if fav_games:
        body += "📌 **Favorite Teams Schedule:**\n" + "\n".join(fav_games) + "\n\n"
    if sec_games:
        body += "⚾ **SEC Teams Schedule:**\n" + "\n".join(sec_games) + "\n\n"
    if top25_games:
        body += "🏆 **Top 25 Schedule:**\n" + "\n".join(top25_games) + "\n\n"

    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = RECIPIENT_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, RECIPIENT_EMAIL, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

def job():
    """Scheduled job to scrape and send an email."""
    fav_games, sec_games, top25_games = scrape_schedule()
    send_email(fav_games, sec_games, top25_games)

def handler(event, context):
    job()
    return {
        'statusCode': 200,
        'body': 'Cron job executed successfully!'
    }