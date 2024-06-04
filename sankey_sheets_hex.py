import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import plotly.graph_objects as go
import os
import json
from datetime import datetime, timedelta, date
import pytz

# Load environment variables
spreadsheet_id = os.getenv('SPREADSHEET_ID')
sheet_name = os.getenv('SHEET_NAME')
credentials_file = os.getenv('GOOGLE_CREDENTIALS')

# Load credentials from JSON file
with open(credentials_file) as f:
    credentials_info = json.load(f)

# Set up Google Sheets API credentials
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    credentials_info, scope)
client = gspread.authorize(creds)

# Open the Google Sheet using Spreadsheet ID
sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)

# Load data into a pandas DataFrame
data = pd.DataFrame(sheet.get_all_records())

# Drop the "Ladder" and "Platform / Role" columns
data = data.drop(columns=["Ladder", "Platform / Role"])

# Melt the dataset to have a long format with columns 'Person', 'Month', 'Team'
data_melted = data.melt(id_vars=["Person"],
                        var_name="Month",
                        value_name="Team")

# Convert "Month" to datetime
data_melted["Month"] = pd.to_datetime(
    data_melted["Month"], format="%B %Y", errors='coerce')

# Filter data based on daterange_start and daterange_end
if daterange_start and daterange_end:
    daterange_start = datetime.combine(daterange_start, datetime.min.time())
    daterange_end = datetime.combine(daterange_end, datetime.min.time())
    data_melted = data_melted[(data_melted["Month"] >= daterange_start) &
                              (data_melted["Month"] <= daterange_end)]

# Drop rows with NaN values in 'Team'
data_melted.dropna(subset=["Team"], inplace=True)

# Sort the data by Person and Month
data_melted["Month"] = data_melted["Month"].dt.strftime('%Y-%m')
data_melted["Month"] = pd.Categorical(data_melted["Month"],
                                      categories=pd.date_range(
                                          daterange_start, daterange_end, freq='MS').strftime('%Y-%m'),
                                      ordered=True)
data_melted.sort_values(by=["Person", "Month"], inplace=True)

# Create transitions from one month to the next
transitions = []
months = list(data_melted["Month"].cat.categories)
for i in range(len(months) - 1):
    month_from = months[i]
    month_to = months[i + 1]
    df_from = data_melted[data_melted["Month"] == month_from]
    df_to = data_melted[data_melted["Month"] == month_to]
    df_merged = df_from.merge(df_to, on="Person", suffixes=("_from", "_to"))
    df_merged = df_merged[df_merged["Team_from"] !=
                          df_merged["Team_to"]]  # Only include changes
    transitions.append(df_merged[["Team_from", "Team_to", "Person"]])

# Concatenate all transitions
all_transitions = pd.concat(transitions)

# Aggregate the transitions by team pair and collect the names of people
transition_agg = all_transitions.groupby(["Team_from", "Team_to"]).agg({
    "Person": lambda x: ', '.join(x),
    "Team_from": 'size'
}).rename(columns={"Team_from": "Count"}).reset_index()

# Prepare data for Sankey diagram
source = transition_agg['Team_from']
target = transition_agg['Team_to']
value = transition_agg['Count']
hovertext = transition_agg['Person']

# Create a list of unique labels (teams)
labels = list(pd.concat([source, target]).unique())

# Map labels to indices
label_to_index = {label: index for index, label in enumerate(labels)}
source_indices = source.map(label_to_index)
target_indices = target.map(label_to_index)

# Create the Sankey diagram
sankey_fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=labels
    ),
    link=dict(
        source=source_indices,
        target=target_indices,
        value=value,
        customdata=hovertext,
        hovertemplate='People: %{customdata}<extra></extra>'
    )
)])

# Replace with the user's actual timezone
user_timezone = pytz.timezone('America/New_York')
now = datetime.now(user_timezone)
previous_hour_top = now.replace(
    minute=0, second=0, microsecond=0) - timedelta(hours=1)

# Format date and time
formatted_date = previous_hour_top.strftime("%-m-%-d-%Y")
formatted_time = previous_hour_top.strftime("%-I:%M %p")
formatted_datetime = f"{formatted_date} {formatted_time}"

# Format date range for the title
daterange_start_formatted = daterange_start.strftime("%B %Y")
daterange_end_formatted = daterange_end.strftime("%B %Y")
date_range_str = f"{daterange_start_formatted} - {daterange_end_formatted}"

# Update layout with the date range and the last update time
sankey_fig.update_layout(
    title_text=f"Team Assignment Flow from {
        date_range_str}. Last updated at {formatted_datetime} ET",
    font_size=10
)
