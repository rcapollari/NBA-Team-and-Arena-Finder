from flask import Flask, render_template
from nba_api.stats.static import teams
from nba_api.stats.endpoints import teamdetails
import plotly.express as px
import pandas as pd

app = Flask(__name__)

# Data obtained from https://simplemaps.com/data/us-cities
df = pd.read_csv('uscities.csv')
nba_teams = teams.get_teams()
nba_cities = [team['city'] for team in nba_teams]
nba_states = [team['state'] for team in nba_teams]
nba_team_names = [team['full_name'] for team in nba_teams]
team_id_map = {team['full_name']: team['id'] for team in nba_teams}

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

@app.route('/')
def index():
    fig = px.scatter_geo(df_combined, lat='lat', lon='lng', size='population', color='state_name',
                         projection='albers usa', scope='north america', hover_name='team_name')
    fig.update_layout(height=800, width=800)
    fig.update_traces(hovertemplate='%{hovertext}<extra></extra>')
    fig.update_layout(showlegend=False, margin={"r":0,"t":0,"l":0,"b":0})

    plot = fig.to_html(full_html=False)

    return render_template('index.html', plot=plot, nba_team_names=nba_team_names)


@app.route('/info/<team>')
def gps(team):
    # Find the team with the specified full name
    nba_teams = teams.get_teams()
    team_info = None
    for t in nba_teams:
        if t['full_name'] == team:
            team_info = t
            break

    # If the team is not found, return an error
    if team_info is None:
        return render_template('error.html', message=f'Team "{team}" not found')

    team_id = team_info['id']
    team_details = teamdetails.TeamDetails(team_id)
    team_info = team_details.team_background.get_dict()['data'][0]
    arena_index = team_details.team_background.get_dict()['headers'].index('ARENA')
    coach_index = team_details.team_background.get_dict()['headers'].index('HEADCOACH')
    year_founded_index = team_details.team_background.get_dict()['headers'].index('YEARFOUNDED')
    team_arena = team_info[arena_index]
    team_coach = team_info[coach_index]
    year = team_info[year_founded_index]
    return render_template('info.html', team=team, team_arena=team_arena, team_coach=team_coach, year=year)


if __name__ == '__main__':
    print('starting Flask app', app.name)
    app.run(debug=True)