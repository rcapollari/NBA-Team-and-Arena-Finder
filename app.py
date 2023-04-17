from flask import Flask, render_template, redirect, url_for, request
from nba_api.stats.static import teams
from nba_api.stats.endpoints import teamdetails, CommonTeamRoster, scoreboardv2
import plotly.express as px
import pandas as pd
from flask_caching import Cache
import os
from geopy.geocoders import Nominatim
import folium
from map_secrets import API_KEY
import requests
import geocoder
from datetime import datetime, timedelta

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# CSV data obtained from https://simplemaps.com/data/us-cities
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
@cache.cached(timeout=2)
def index():
    fig = px.scatter_geo(df_combined, lat='lat', lon='lng', size='population', color='state_name',
                         projection='albers usa', scope='north america', hover_name='team_name')
    fig.update_layout(height=800, width=800)
    fig.update_traces(hovertemplate='%{hovertext}<extra></extra>')
    fig.update_layout(showlegend=False, margin={"r":0,"t":0,"l":0,"b":0})

    plot = fig.to_html(full_html=False)

    return render_template('index.html', plot=plot, nba_team_names=nba_team_names)

@app.route('/info/<team>', methods=['POST', 'GET'])
@cache.cached(timeout=2)
def info(team):
    team_info = None
    for t in nba_teams:
        if t['full_name'] == team:
            team_info = t
            break

    team_id = team_info['id']
    print(team_id)
    team_details = teamdetails.TeamDetails(team_id)
    team_info = team_details.team_background.get_dict()['data'][0]
    arena_index = team_details.team_background.get_dict()['headers'].index('ARENA')
    coach_index = team_details.team_background.get_dict()['headers'].index('HEADCOACH')
    year_founded_index = team_details.team_background.get_dict()['headers'].index('YEARFOUNDED')
    team_arena = team_info[arena_index]
    team_coach = team_info[coach_index]
    year = team_info[year_founded_index]

    today = datetime.today()
    start_date = datetime.today()
    games = []
    # Today's Score Board
    scoreboard = scoreboardv2.ScoreboardV2(game_date=today.strftime('%m/%d/%Y'))
    games += scoreboard.game_header.get_dict()['data']

    for i in range(1, 7):
        game_date = start_date + timedelta(days=i)
        scoreboard = scoreboardv2.ScoreboardV2(game_date=game_date.strftime('%m/%d/%Y'))
        games += scoreboard.game_header.get_dict()['data']
        print(scoreboard.game_header.get_dict())

    team_games = []
    for game in games:
        if game[7] == team_id or game[6] == team_id:
            team_games.append(game)
    
    return render_template('info.html', team=team, team_arena=team_arena, team_coach=team_coach, year=year, games=games, team_id=team_id, nba_teams=nba_teams, team_games=team_games)

@app.route('/question/<team>', methods=['GET', 'POST'])
@cache.cached(timeout=2)
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
@cache.cached(timeout=2)
def directions(team):
    if request.method == 'GET':
        return redirect(url_for('directions_page', team=team))
    else:
        return redirect(url_for('info', team=team))
    
@app.route('/directions/<team>/page', methods=['GET','POST'])
@cache.cached(timeout=2)
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

    nom = Nominatim(user_agent="SI 507 Final Project")
    n = nom.geocode(team_arena)
    lat = n.latitude
    lon = n.longitude

    g = geocoder.ip('me')
    
    user_lat, user_lon = None, None
    if request.method == 'POST':
        user_address = request.form.get('user-address')
        user_location = nom.geocode(user_address)
        if user_location is not None:
            user_lat, user_lon = user_location.latitude, user_location.longitude
        else:
            user_lat, user_lon = g.latlng
    else:
        user_lat, user_lon = g.latlng

    url = f'https://api.openrouteservice.org/v2/directions/driving-car?api_key={API_KEY}&start={user_lon},{user_lat}&end={lon},{lat}'
    response = requests.get(url)

    # Parse the JSON response and extract the route geometry and instructions
    data = response.json()
    route_geometry = data['features'][0]['geometry']['coordinates']
    route_coords = [[coord[1], coord[0]] for coord in route_geometry]
    route_instructions = [(step['instruction'], step['distance'], step['duration']) for step in data['features'][0]['properties']['segments'][0]['steps']]

    total_distance = 0.0
    total_time = 0.0

    for instruction in route_instructions:
        total_distance += instruction[1]
        total_time += instruction[2]

    map = folium.Map(location=[lat, lon], zoom_start=7, tiles='OpenStreetMap') # Height and Width of map can be listed here
    folium.Marker(location=[lat, lon], tooltip=team_arena, icon=folium.Icon(color='red')).add_to(map)
    folium.Marker(location=[user_lat, user_lon], tooltip='Starting Location', icon=folium.Icon(color='green')).add_to(map)
    folium.PolyLine(locations=route_coords, color='blue').add_to(map)

    map_html = map._repr_html_()

    return render_template('directions.html', team=team, team_arena=team_arena, lat=lat, lon=lon, map_html=map_html, route_instructions=route_instructions, total_distance=total_distance, total_time=total_time)

@app.route('/<team>/currentstats', methods=['GET', 'POST'])
@cache.cached(timeout=2)
def currentstats(team):
    team_info = None
    for t in nba_teams:
        if t['full_name'] == team:
            team_info = t
            break
    team_id = team_info['id']
    team_details = teamdetails.TeamDetails(team_id)
    team_info = team_details.team_background.get_dict()['data'][0]
    
    roster = CommonTeamRoster(team_id=team_id).get_data_frames()[0]
    roster = roster[['PLAYER', 'POSITION', 'HEIGHT', 'WEIGHT', 'SCHOOL']]
    return render_template('currentstats.html', team=team, roster=roster)

@app.route('/<team>/tickets', methods=['GET', 'POST'])
@cache.cached(timeout=2)
def tickets(team):
    return render_template('tickets.html', team=team)

if __name__ == '__main__':
    print('starting Flask app', app.name)
    app.run(debug=True)

app.config['CACHE_DIR'] = os.getcwd() + '/cache.json'
cache.init_app(app)