import requests
# API endpoint
top_url = 'https://ncaa-api.henrygd.me/rankings/softball/d1/espncom/usa-softball'

# Fetch the rankings data
response = requests.get(top_url)
data = response.json()

# Initialize an empty list to store the top 25 teams
TOP25 = []

# Extract the top 25 teams from the data
for team in data.get('data', [])[:25]:
    # Clean the college name by removing any trailing numbers or characters
    college_name = team['COLLEGE'].split(' (')[0]
    TOP25.append(college_name)

# Output the TOP25 list
print(TOP25)