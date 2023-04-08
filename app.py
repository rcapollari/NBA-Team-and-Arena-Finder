from flask import Flask, render_template
from nba_api.stats.static import teams

import plotly.express as px
import pandas as pd

app = Flask(__name__)

# Data obtained from https://simplemaps.com/data/us-cities
df = pd.read_csv('uscities.csv')

@app.route('/')
def index():
    nba_teams = teams.get_teams()
    nba_cities = [team['city'] for team in nba_teams]
    nba_states = [team['state'] for team in nba_teams]
    nba_team_names = [team['full_name'] for team in nba_teams]

    df_filtered = df[df['city'].isin(nba_cities) & df['state_name'].isin(nba_states)]
    df_filtered['team_name'] = [nba_team_names[nba_cities.index(city)] if city in nba_cities else '' for city in df_filtered['city']]
    
    lakers_df = pd.DataFrame({
        'city': 'Los Angeles',
        'lat': 34.0522,
        'lng': -118.2437,
        'state_id': ['CA'],
        'state_name': ['California'],
        'team_name': ['Los Angeles Lakers'],
        'population': 12121244
    })
    df_combined = pd.concat([df_filtered, lakers_df], ignore_index=True)

    fig = px.scatter_geo(df_combined, lat='lat', lon='lng', size='population', color='city',
                         projection='albers usa', scope='north america', hover_name='team_name')

    fig.update_layout(height=800, width=1200)
    fig.update_traces(hovertemplate='%{hovertext}<extra></extra>')

    plot = fig.to_html(full_html=False)

    return render_template('index.html', plot=plot)

if __name__ == '__main__':
    app.run(debug=True)