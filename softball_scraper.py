import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import time

# Teams to track update
# TEAMS = ["Tennessee", "Indiana", "Louisville", "Oklahoma", "Alabama", "Florida State"]

# Gmail credentials
GMAIL_USER = "rhamby95@gmail.com"
GMAIL_PASS = "hjmdygespqhybmet"
RECIPIENT_EMAIL = "arcoleman18@gmail.com"

# Website URL
URL = "https://www.sportsmediawatch.com/tv-schedules/college-softball-tv-schedule/"

def scrape_schedule():
    """Scrape the Sports Media Watch website for today's college softball games."""
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
            # if any(team in teams for team in TEAMS): 
            channel = network.text.strip() if network else "Unknown Channel"
            games.append(f"{teams} @ {game_time} on {channel}")

    return games
# today_games = scrape_schedule()
# print("\nToday's Games for Selected Teams:")
# print("\n".join(today_games) if today_games else "No games found for today.")
def send_email(games):
    """Send an email with the filtered game schedule."""
    if not games:
        print("No games found for tracked teams today.")
        return  

    subject = "College Softball Schedule - Today's Games"
    body = "\n".join(games)

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
    games = scrape_schedule()
    send_email(games)

# Run job immediately when the script is executed
job()

