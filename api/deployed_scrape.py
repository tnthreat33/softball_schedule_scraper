from http.server import BaseHTTPRequestHandler
import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Teams to track
FAV_TEAMS = ["Indiana", "Louisville", "Butler", "Northwestern"]
SEC_TEAMS = [
    "Alabama", "Arkansas", "Auburn", "Florida", "Georgia", "Kentucky",
    "LSU", "Mississippi State", "Missouri", "Ole Miss", "South Carolina",
    "Tennessee", "Texas A&M", "Vanderbilt"
]

# API URL for rankings
top_url = 'https://ncaa-api.henrygd.me/rankings/softball/d1/espncom/usa-softball'

# Website URL
URL = "https://www.sportsmediawatch.com/tv-schedules/college-softball-tv-schedule/"

# Fetch rankings data
try:
    response = requests.get(top_url)
    response.raise_for_status()
    data = response.json()
    TOP25 = {team['COLLEGE'].split(' (')[0].strip() for team in data.get('data', [])[:25]}
except Exception as e:
    logger.error(f"Error fetching or parsing rankings data: {e}")
    TOP25 = set()  # Fallback to an empty set if the request fails

# Gmail credentials
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_PASS = os.getenv('GMAIL_PASS')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')

def scrape_schedule():
    """Scrape today's college softball games and categorize them into Favorite, SEC, and Top 25 teams."""
    try:
        response = requests.get(URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        fav_games = []
        sec_games = []
        top25_games = []

        # Locate the "Today" section
        today_section = soup.find("a", {"name": "Today"})
        if not today_section:
            logger.info("Could not find 'Today' section.")
            return fav_games, sec_games, top25_games

        # Find today's schedule table
        today_table = today_section.find_next("table", class_="schedule-table")
        
        if not today_table:
            logger.info("No games listed for today.")
            return fav_games, sec_games, top25_games

        # Extract game details
        time_cells = today_table.find_all("td", {"data-label": "Time (ET)"})
        game_cells = today_table.find_all("td", {"data-label": "Game / TV"})

        if not time_cells or not game_cells:
            logger.info("No valid game rows found.")
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

    except Exception as e:
        logger.error(f"Error scraping schedule: {e}")
        return [], [], []

def send_email(fav_games, sec_games, top25_games):
    """Send an email with the categorized game schedule."""
    if not (fav_games or sec_games or top25_games):
        logger.info("No games found for tracked teams today.")
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
        logger.info("Email sent successfully!")
    except Exception as e:
        logger.error(f"Error sending email: {e}")

def job():
    """Scheduled job to scrape and send an email."""
    fav_games, sec_games, top25_games = scrape_schedule()
    send_email(fav_games, sec_games, top25_games)

# Vercel expects a class-based HTTP handler
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handles incoming GET requests."""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        # Run the scraping and email job
        job()

        # Return a response
        response_data = json.dumps({"status": "Cron job executed successfully"})
        self.wfile.write(response_data.encode())
