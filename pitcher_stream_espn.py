# this is the pitcher streaming script
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np


url = "https://www.espn.com/fantasy/baseball/story/_/id/39831901"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Send a GET request to the URL with headers
response = requests.get(url, headers=headers)

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Parse the HTML content
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all elements with class "inline-with-table"
    inline_with_table_elements = soup.find_all(class_="inline-with-table")

    # Extract and print the text content of each element
    for element in inline_with_table_elements:
        cleaned_text = element.get_text(separator="\n", strip=True)

else:
    print("Failed to retrieve content. Status code:", response.status_code)


# now that cleaned_text is a str, i need to remove everything before "FPTS" case sensitive

# Find the index of the SECOND occurrence of "FPTS" in the text
index = cleaned_text.find("FPTS", cleaned_text.find("FPTS") + 1)

# Extract the text starting from the index
cleaned_text = cleaned_text[index:]

# convert cleaned_text to a list of strings
# Split the text into a list of strings using the newline character "\n"
cleaned_text_list = cleaned_text.split("\n")


# remove "Team" from cleaned_text_list
cleaned_text_list.remove("Team")

# save the first 11 elements to new list for column names
column_names = cleaned_text_list[:11]


# save the rest of the elements to a new list for data
data = cleaned_text_list[11:]


# split data into chunks of 11
data_chunks = [data[i : i + 11] for i in range(0, len(data), 11)]

# Create a DataFrame from the data chunks
espn_projections = pd.DataFrame(data_chunks, columns=column_names)

# remove the % from the W% column
espn_projections["W%"] = espn_projections["W%"].str.rstrip("%")

# convert W% to a float
espn_projections["W%"] = espn_projections["W%"].astype(float)

# convert FPTS to a float
espn_projections["FPTS"] = espn_projections["FPTS"].astype(float)


# remove T, ML, O/U, IP, ER, K columns
espn_projections = espn_projections.drop(columns=["T", "ML", "O/U", "IP", "ER", "K"])


# making the adjustment for 5pt w/l instead of 2pt
espn_projections["win_percent_adjustment"] = (
    (espn_projections["W%"] * 3) - ((100 - espn_projections["W%"]) * 3)
) / 100

# create adj_fpts column
espn_projections["adj_fpts"] = (
    espn_projections["FPTS"] + espn_projections["win_percent_adjustment"]
)

# grab todays date
from datetime import date

today = date.today()
print(today)

# add date column
espn_projections["date"] = today

# convert - to underscore
today = str(today).replace("-", "_")

# write to csv formatted with date
espn_projections.to_csv(f"espn_projections_{today}.csv", index=False)

# drop date column
espn_projections = espn_projections.drop(columns=["date"])

#################ESPN FANTASY LEAGUE LOAD AREA####################
from espn_api.baseball import League

# Create a league object
league = League(
    league_id=1893307610,
    year=2024,
    swid="{2775F236-BFEF-4D4C-B5F2-36BFEF3D4C8E}",
    espn_s2="AECtTBz1STuXPdo4TMFTarhWjlgExxE7Vt7UFvOTscpbT6Ajd8qhO3EWuCuJ3xZrgGovAlw2Whkl1VPzDCGN7lpuRzzq7GtVhXtD2IvAELW%2FES61ZF3gMrGIzwjZ28dtDtATNFf%2B1UK5Sj%2FZWnq7e6aZY6nTfVb59UWRwkzXv6rq2l9bm8AT8xzYvdp0KN%2FbRjo4jqc2Sh%2FmSFVvj3lzMYMl1BeEqu5eE5aHZbCkPWzq1%2Fmf%2F%2BSQIXMbmZLzHq5zOuMUa2IWWxKNymv1o29nVcQA",
)

# grab my team
my_team = league.teams[8]

my_roster = my_team.roster

my_roster_strings = [str(player).split("(")[1][:-1] for player in my_roster]


# grab all free agents
free_agents = league.free_agents(size=100000)


free_agent_strings = [str(player).split("(")[1][:-1] for player in free_agents]

# filter down espn_projections for only my team
my_team_espn_projections = espn_projections[
    espn_projections["Pitcher"].isin(my_roster_strings)
]

# filter down espn_projections for only free agents
free_agent_espn_projections = espn_projections[
    espn_projections["Pitcher"].isin(free_agent_strings)
]

print(my_team_espn_projections)

print(free_agent_espn_projections)
