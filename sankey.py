import pandas as pd
import plotly.graph_objects as go

# Load the dataset
file_path = './Consumer Staffing May 2024 Plan - The database.tsv'
data = pd.read_csv(file_path, sep='\t')

# Melt the dataset to have a long format with columns 'Person', 'Month', 'Team'
data_melted = data.melt(id_vars=["Person", "Ladder", "Platform / Role"],
                        var_name="Month",
                        value_name="Team")

# Drop rows with NaN values in 'Team'
data_melted.dropna(subset=["Team"], inplace=True)

# Sort the data by Person and Month
data_melted["Month"] = pd.Categorical(data_melted["Month"],
                                      categories=[
                                          "May", "June", "July", "Aug", "Sept", "Oct", "Nov", "Dec", "Jan", "Feb"],
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
    transitions.append(
        df_merged[["Team_from", "Team_to"]].value_counts().reset_index(name="Count"))

# Concatenate all transitions
all_transitions = pd.concat(transitions).groupby(
    ["Team_from", "Team_to"]).sum().reset_index()

# Prepare data for Sankey diagram
source = all_transitions['Team_from']
target = all_transitions['Team_to']
value = all_transitions['Count']

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
        value=value
    )
)])

# Update layout
sankey_fig.update_layout(
    title_text="Team Assignment Flow Over Time", font_size=10)

# Show plot
sankey_fig.show()
