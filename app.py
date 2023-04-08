from flask import Flask, render_template
from nba_api.stats.static import teams

import plotly.express as px
import pandas as pd

app = Flask(__name__)

# Data obtained from https://simplemaps.com/data/us-cities
df = pd.read_csv('uscities.csv')

@app.route('/')
def index():
    # Get a list of NBA team city names
    nba_teams = teams.get_teams()
    nba_cities = [team['city'] for team in nba_teams]
    nba_states = [team['state'] for team in nba_teams]
    nba_team_names = [team['full_name'] for team in nba_teams]

    # Filter the dataset to include only cities with NBA teams
    df_filtered = df[df['city'].isin(nba_cities) & df['state_name'].isin(nba_states)]
    # df_filtered2 = df_filtered[df_filtered['state_name'].isin(nba_states)]
    # Add a column to the filtered DataFrame with the team names
    df_filtered['team_name'] = [nba_team_names[nba_cities.index(city)] if city in nba_cities else '' for city in df_filtered['city']]


    fig = px.scatter_geo(df_filtered, lat='lat', lon='lng', size='population', color='state_name',
                         projection='albers usa', scope='north america', hover_name='team_name')

    fig.update_layout(height=800, width=1200)

    # Convert the plotly figure to HTML
    plot = fig.to_html(full_html=False)

    # Render the HTML template and pass in the plot
    return render_template('index.html', plot=plot)

if __name__ == '__main__':
    app.run(debug=True)