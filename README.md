# SI-507-Final-Project

## Introduction
This is an application that displays data on each team in the National Basketball Association (NBA). You will find roster information, as well as the upcoming game schedule for every team. In addition, you will find information on the arenas where each team plays and driving directions to those locations.

## Data Sources
The following are the data sources I used for this project:
* NBA team data from the NBA API at https://github.com/swar/nba_api
* uscities.csv from https://simplemaps.com/data/us-cities

## To run this app:
To run the project locally, clone the repository and type 
    python app.py 
in the terminal and go to http://localhost:5000/.

You will also need to create an account at https://openrouteservice.org/ and obtain an API key which will be used for the URL to create the map with directions to each NBA arena. When this API key is obtained, create a file called map_secrets.py, create a variable called API_KEY, and assign it to your key.

## Overview
Upon running the app, it will take you to the home page below. There is a Plotly map that the user can hover over to see the locations of each NBA team. The user will need to select a team on the right side menu to move forward.
![Home Page](/images/Home%20Page.png)

Once a team has been selected, the user will go through a short series of questions to determine which page they want to land on. 
![Question 1](/images/root_question.png)
![Tickets Question](/images/tickets.png)
![Roster Question](/images/roster_question.png)

Then, depending on the answers to the questions, the user will land on one of these types of pages:
![Directions Page](/images/directions.png)
![Roster Page](/images/roster_ex.png)
![Schedule Page](/images/schedule.png)