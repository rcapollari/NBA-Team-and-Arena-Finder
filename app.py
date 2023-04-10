from flask import Flask, render_template, redirect, url_for, request
from nba_api.stats.static import teams
from nba_api.stats.endpoints import teamdetails
import plotly.express as px
import pandas as pd
from flask_caching import Cache
import os

app = Flask(__name__)
app.config['CACHE_TYPE'] = 'filesystem'
app.config['CACHE_DIR'] = '/cache.json'
cache = Cache(app)

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

# tree = ("Do you want directions to this team's arena?",
#         ("Do you want to look for tickets?",
#             ("Go to TicketMaster or another ticket site", None, None),
#             ("Directions", None, None)),
#         ("Do you want to see this team's current roster and stats?",
#             ("Do you want to see the current stats?", None, None),
#             ("Do you want to see all time team info?", None, None)))

tree = \
    ("Do you want directions to this team's arena?",
     ("Do you want to look for tickets first?", None, None),
     ("Do you want to see their roster and stats?", None, None))

def traverse(tree):
    question, left, right = tree
    if left is None and right is None: # If leaf
        return question
    else:
        answer = request.form.get('answer')
        if answer == 'yes':
            return traverse(left)
        elif answer == 'no':
            return traverse(right)
        else:
            return question
        
@app.route('/')
def index():
    fig = px.scatter_geo(df_combined, lat='lat', lon='lng', size='population', color='state_name',
                         projection='albers usa', scope='north america', hover_name='team_name')
    fig.update_layout(height=800, width=800)
    fig.update_traces(hovertemplate='%{hovertext}<extra></extra>')
    fig.update_layout(showlegend=False, margin={"r":0,"t":0,"l":0,"b":0})

    plot = fig.to_html(full_html=False)

    return render_template('index.html', plot=plot, nba_team_names=nba_team_names)


@app.route('/info/<team>', methods=['POST', 'GET'])
@cache.cached(timeout=10)
def info(team):
    team_info = None
    for t in nba_teams:
        if t['full_name'] == team:
            team_info = t
            break

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

@app.route('/question/<team>', methods=['GET', 'POST'])
@cache.cached(timeout=10)
def question(team):
    team_info = None
    for t in nba_teams:
        if t['full_name'] == team:
            team_info = t
            break

    team_id = team_info['id']
    team_details = teamdetails.TeamDetails(team_id)
    team_info = team_details.team_background.get_dict()['data'][0]
    arena_index = team_details.team_background.get_dict()['headers'].index('ARENA')
    team_arena = team_info[arena_index]
    city = nba_cities[nba_team_names.index(team)]

    if request.method == 'POST':
        result = traverse(tree)
        return render_template('result.html', result=result, team=team, city=city)
    else:
        question = traverse(tree)
    return render_template('question.html', question=question, team=team, team_arena=team_arena, city=city)    
    
@app.route('/directions/<team>', methods=['GET','POST'])
@cache.cached(timeout=10)
def directions(team):
    if request.method == 'GET':
        return redirect(url_for('directions_page', team=team))
    else:
        return redirect(url_for('info', team=team))
    
@app.route('/directions/<team>/page')
def directions_page(team):
    team_info = None
    for t in nba_teams:
        if t['full_name'] == team:
            team_info = t
            break

    team_id = team_info['id']
    team_details = teamdetails.TeamDetails(team_id)
    team_info = team_details.team_background.get_dict()['data'][0]
    arena_index = team_details.team_background.get_dict()['headers'].index('ARENA')
    team_arena = team_info[arena_index]
    return render_template('directions.html', team=team, team_arena=team_arena)

@app.route('/demo', methods=['GET', 'POST'])
def demo():
    if request.method == 'POST':
        result = traverse(tree)
        return render_template('result.html', result=result)
    else:
        question = traverse(tree)
        return render_template('demo_index.html', question=question)

if __name__ == '__main__':
    print('starting Flask app', app.name)
    app.run(debug=True)

app.config['CACHE_DIR'] = os.getcwd() + '/cache.json'
cache.init_app(app)