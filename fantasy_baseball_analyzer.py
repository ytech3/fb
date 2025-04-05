#!/usr/bin/env python3
# Fantasy Baseball League Analyzer
# This script analyzes fantasy baseball teams and provides recommendations based on
# projections from various credible sources (PECOTA, FanGraphs, MLB.com, etc.)

import os
import csv
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate
import warnings
warnings.filterwarnings('ignore')

class FantasyBaseballAnalyzer:
    def __init__(self, league_id="2874", your_team_name="Kenny Kawaguchis"):
        self.league_id = league_id
        self.your_team_name = your_team_name
        self.teams = {}
        self.batter_projections = {}
        self.pitcher_projections = {}
        self.team_rankings = {}
        self.team_points = {}
        self.category_rankings = {}
        
        # Create directories for data storage
        os.makedirs("data", exist_ok=True)
        os.makedirs("reports", exist_ok=True)
        os.makedirs("visuals", exist_ok=True)
        
        print(f"Fantasy Baseball Analyzer initialized for league ID: {league_id}")
        print(f"Your team: {your_team_name}")
    
    def load_teams(self, teams_file=None):
        """
        Load team rosters from CSV file or use default data
        CSV format should be: team_name,player_name,position
        """
        if teams_file and os.path.exists(teams_file):
            try:
                df = pd.read_csv(teams_file)
                for _, row in df.iterrows():
                    team_name = row['team_name']
                    player_name = row['player_name']
                    position = row['position']
                    
                    if team_name not in self.teams:
                        self.teams[team_name] = {"batters": [], "pitchers": []}
                    
                    if position in ['SP', 'RP', 'P']:
                        self.teams[team_name]["pitchers"].append(player_name)
                    else:
                        self.teams[team_name]["batters"].append(player_name)
                
                print(f"Loaded {len(self.teams)} teams from {teams_file}")
            except Exception as e:
                print(f"Error loading teams file: {e}")
                self._load_default_teams()
        else:
            print("Teams file not provided or doesn't exist. Loading default data.")
            self._load_default_teams()
    
    def _load_default_teams(self):
        """Load default team data based on our previous analysis"""
        # Default team structure based on league analysis
        self.teams = {
            "Kenny Kawaguchis": {
                "batters": [
                    "Logan O'Hoppe", "Bryce Harper", "Mookie Betts", "Austin Riley", "CJ Abrams", 
                    "Lawrence Butler", "Riley Greene", "Adolis García", "Taylor Ward", "Tommy Edman", 
                    "Roman Anthony", "Jonathan India", "Trevor Story", "Iván Herrera"
                ],
                "pitchers": [
                    "Cole Ragans", "Hunter Greene", "Jack Flaherty", "Ryan Helsley", "Tanner Scott", 
                    "Pete Fairbanks", "Ryan Pepiot", "MacKenzie Gore", "Camilo Doval"
                ]
            },
            "Mickey 18": {
                "batters": [
                    "Adley Rutschman", "Pete Alonso", "Matt McLain", "Jordan Westburg", "Jeremy Peña", 
                    "Jasson Domínguez", "Tyler O'Neill", "Vladimir Guerrero Jr.", "Eugenio Suárez", 
                    "Ronald Acuña Jr."
                ],
                "pitchers": [
                    "Tarik Skubal", "Spencer Schwellenbach", "Hunter Brown", "Jhoan Duran", "Jeff Hoffman", 
                    "Ryan Pressly", "Justin Verlander", "Max Scherzer"
                ]
            },
            "Burnt Ends": {
                "batters": [
                    "Yainer Diaz", "Triston Casas", "Luis García Jr.", "Manny Machado", "Ezequiel Tovar", 
                    "Kyle Tucker", "Corbin Carroll", "Lane Thomas", "Anthony Volpe", "Jurickson Profar"
                ],
                "pitchers": [
                    "Corbin Burnes", "Jacob deGrom", "Yoshinobu Yamamoto", "Carlos Estévez", "Jordan Romano", 
                    "Logan Webb", "Blake Treinen", "Zac Gallen", "Aaron Nola"
                ]
            },
            "Skenes Machines": {
                "batters": [
                    "Austin Wells", "Cody Bellinger", "Brice Turang", "Max Muncy", "Gunnar Henderson", 
                    "Kyle Schwarber", "Marcell Ozuna", "Randy Arozarena", "Bo Bichette", "Christian Yelich"
                ],
                "pitchers": [
                    "Paul Skenes", "Kodai Senga", "Emmanuel Clase", "Josh Hader", "Félix Bautista", 
                    "Drew Rasmussen", "Zach Eflin", "Shane Baz"
                ]
            },
            "Gingerbeard Men": {
                "batters": [
                    "Salvador Perez", "Yandy Díaz", "Ketel Marte", "Alec Bohm", "Elly De La Cruz", 
                    "Brent Rooker", "Teoscar Hernández", "Bryan Reynolds", "Josh Lowe", "Bryson Stott"
                ],
                "pitchers": [
                    "Zack Wheeler", "Framber Valdez", "Robert Suarez", "Alexis Díaz", "David Bednar", 
                    "Taj Bradley", "Lucas Erceg"
                ]
            },
            "Pitch Perfect": {
                "batters": [
                    "William Contreras", "Freddie Freeman", "Luis Arraez", "Junior Caminero", "Trea Turner", 
                    "Mike Trout", "Steven Kwan", "Dylan Crews", "Shohei Ohtani", "Nick Castellanos"
                ],
                "pitchers": [
                    "Shota Imanaga", "Justin Steele", "Freddy Peralta", "Kenley Jansen", "Chris Martin", 
                    "Ben Joyce", "Tyler Holton", "Jason Adam"
                ]
            },
            "Poopers": {
                "batters": [
                    "Tyler Stephenson", "Alec Burleson", "Andrés Giménez", "José Ramírez", "Willy Adames", 
                    "Fernando Tatis Jr.", "Michael Harris II", "Brandon Nimmo", "Pete Crow-Armstrong", 
                    "Ryan Mountcastle"
                ],
                "pitchers": [
                    "Michael King", "Pablo López", "Luis Castillo", "Devin Williams", "Kyle Finnegan", 
                    "Sonny Gray", "George Kirby", "Carlos Rodón", "Yusei Kikuchi"
                ]
            },
            "Rally Roosters": {
                "batters": [
                    "Will Smith", "Paul Goldschmidt", "Brandon Lowe", "Alex Bregman", "Corey Seager", 
                    "Juan Soto", "Julio Rodríguez", "Anthony Santander", "Dansby Swanson", "Michael Toglia"
                ],
                "pitchers": [
                    "Blake Snell", "Bryce Miller", "Ryan Walker", "Jason Foley", "Grant Holmes", 
                    "Nick Lodolo", "Sandy Alcantara", "Robbie Ray", "Seth Lugo", "Spencer Strider"
                ]
            },
            "Rayful Rejects": {
                "batters": [
                    "Cal Raleigh", "Jake Burger", "Marcus Semien", "Isaac Paredes", "Bobby Witt Jr.", 
                    "Jarren Duran", "Wyatt Langford", "Luis Robert Jr.", "Colton Cowser", "Carlos Correa"
                ],
                "pitchers": [
                    "Logan Gilbert", "Dylan Cease", "Joe Ryan", "Raisel Iglesias", "Cade Smith", 
                    "Trevor Megill", "Liam Hendriks", "Clay Holmes", "Walker Buehler"
                ]
            },
            "Sho Time Jazz": {
                "batters": [
                    "J.T. Realmuto", "Josh Naylor", "Ozzie Albies", "Rafael Devers", "Xavier Edwards", 
                    "Jackson Chourio", "Seiya Suzuki", "Jazz Chisholm Jr.", "Christian Yelich", "George Springer"
                ],
                "pitchers": [
                    "Cristian Javier", "Lucas Giolito", "Max Fried", "Andrés Muñoz", "A.J. Minter", 
                    "Reynaldo López", "Michael Kopech", "Brandon Woodruff"
                ]
            },
            "Teddy Perkins": {
                "batters": [
                    "Willson Contreras", "Matt Olson", "Jackson Holliday", "Matt Chapman", "Francisco Lindor", 
                    "Yordan Alvarez", "Ian Happ", "Victor Robles", "Jorge Soler", "Josh Jung"
                ],
                "pitchers": [
                    "Garrett Crochet", "Tyler Glasnow", "A.J. Puk", "Mason Miller", "Edwin Díaz", 
                    "Andrés Muñoz", "Orion Kerkering", "Porter Hodge", "Taylor Rogers", "Bryan Woo"
                ]
            },
            "The Barners": {
                "batters": [
                    "Shea Langeliers", "Vinnie Pasquantino", "Jose Altuve", "Mark Vientos", "Oneil Cruz", 
                    "Aaron Judge", "Jackson Merrill", "James Wood", "Brenton Doyle", "Masyn Winn"
                ],
                "pitchers": [
                    "Tanner Bibee", "Bailey Ober", "Cristopher Sánchez", "Calvin Faucher", "Nick Martinez", 
                    "Beau Brieske", "Shane Bieber", "Mitch Keller", "Chris Sale", "Nathan Eovaldi"
                ]
            }
        }
        print(f"Loaded {len(self.teams)} teams with default data")
    
    def load_projections(self, batter_file=None, pitcher_file=None):
        """
        Load player projections from CSV files or use default data
        CSV format for batters: player_name,AB,R,HR,RBI,SB,AVG,OPS
        CSV format for pitchers: player_name,IP,ERA,WHIP,K9,QS,SV
        """
        if batter_file and os.path.exists(batter_file) and pitcher_file and os.path.exists(pitcher_file):
            # Load from files if they exist
            try:
                batter_df = pd.read_csv(batter_file)
                for _, row in batter_df.iterrows():
                    self.batter_projections[row['player_name']] = {
                        'AB': row['AB'], 'R': row['R'], 'HR': row['HR'], 
                        'RBI': row['RBI'], 'SB': row['SB'], 'AVG': row['AVG'], 'OPS': row['OPS']
                    }
                
                pitcher_df = pd.read_csv(pitcher_file)
                for _, row in pitcher_df.iterrows():
                    self.pitcher_projections[row['player_name']] = {
                        'IP': row['IP'], 'ERA': row['ERA'], 'WHIP': row['WHIP'], 
                        'K9': row['K9'], 'QS': row['QS'], 'SV': row['SV']
                    }
                
                print(f"Loaded {len(self.batter_projections)} batter and {len(self.pitcher_projections)} pitcher projections from files")
            except Exception as e:
                print(f"Error loading projection files: {e}")
                self._load_default_projections()
        else:
            print("Projection files not provided or don't exist. Loading default projections.")
            self._load_default_projections()
    
    def _load_default_projections(self):
        """Load default projections based on our previous analysis"""
        # Default batter projections based on industry averages
        self.batter_projections = {
            # Catchers
            "Logan O'Hoppe": {'AB': 450, 'R': 68, 'HR': 22, 'RBI': 71, 'SB': 3, 'AVG': 0.262, 'OPS': 0.782},
            "Adley Rutschman": {'AB': 570, 'R': 85, 'HR': 26, 'RBI': 85, 'SB': 2, 'AVG': 0.275, 'OPS': 0.835},
            "Yainer Diaz": {'AB': 480, 'R': 65, 'HR': 21, 'RBI': 75, 'SB': 1, 'AVG': 0.284, 'OPS': 0.790},
            "Austin Wells": {'AB': 420, 'R': 60, 'HR': 18, 'RBI': 65, 'SB': 4, 'AVG': 0.252, 'OPS': 0.750},
            "Salvador Perez": {'AB': 520, 'R': 70, 'HR': 28, 'RBI': 92, 'SB': 1, 'AVG': 0.270, 'OPS': 0.795},
            "William Contreras": {'AB': 540, 'R': 75, 'HR': 22, 'RBI': 78, 'SB': 5, 'AVG': 0.282, 'OPS': 0.820},
            "Tyler Stephenson": {'AB': 450, 'R': 58, 'HR': 16, 'RBI': 65, 'SB': 2, 'AVG': 0.260, 'OPS': 0.750},
            "Will Smith": {'AB': 530, 'R': 80, 'HR': 24, 'RBI': 90, 'SB': 3, 'AVG': 0.272, 'OPS': 0.815},
            "Cal Raleigh": {'AB': 480, 'R': 70, 'HR': 30, 'RBI': 85, 'SB': 0, 'AVG': 0.232, 'OPS': 0.780},
            "J.T. Realmuto": {'AB': 510, 'R': 72, 'HR': 20, 'RBI': 75, 'SB': 10, 'AVG': 0.265, 'OPS': 0.775},
            "Willson Contreras": {'AB': 490, 'R': 70, 'HR': 23, 'RBI': 75, 'SB': 2, 'AVG': 0.268, 'OPS': 0.795},
            "Shea Langeliers": {'AB': 460, 'R': 65, 'HR': 25, 'RBI': 70, 'SB': 1, 'AVG': 0.235, 'OPS': 0.740},
            "Iván Herrera": {'AB': 380, 'R': 45, 'HR': 12, 'RBI': 48, 'SB': 2, 'AVG': 0.258, 'OPS': 0.735},
            
            # First Basemen
            "Bryce Harper": {'AB': 540, 'R': 98, 'HR': 33, 'RBI': 103, 'SB': 12, 'AVG': 0.289, 'OPS': 0.920},
            "Pete Alonso": {'AB': 560, 'R': 88, 'HR': 37, 'RBI': 105, 'SB': 3, 'AVG': 0.252, 'OPS': 0.835},
            "Triston Casas": {'AB': 520, 'R': 80, 'HR': 30, 'RBI': 90, 'SB': 2, 'AVG': 0.268, 'OPS': 0.860},
            "Vladimir Guerrero Jr.": {'AB': 590, 'R': 95, 'HR': 35, 'RBI': 100, 'SB': 5, 'AVG': 0.295, 'OPS': 0.890},
            "Freddie Freeman": {'AB': 570, 'R': 97, 'HR': 25, 'RBI': 92, 'SB': 12, 'AVG': 0.302, 'OPS': 0.890},
            "Cody Bellinger": {'AB': 550, 'R': 85, 'HR': 26, 'RBI': 95, 'SB': 14, 'AVG': 0.272, 'OPS': 0.820},
            "Yandy Díaz": {'AB': 530, 'R': 82, 'HR': 18, 'RBI': 75, 'SB': 2, 'AVG': 0.290, 'OPS': 0.825},
            "Matt Olson": {'AB': 560, 'R': 95, 'HR': 38, 'RBI': 110, 'SB': 2, 'AVG': 0.265, 'OPS': 0.880},
            "Paul Goldschmidt": {'AB': 540, 'R': 80, 'HR': 24, 'RBI': 85, 'SB': 5, 'AVG': 0.275, 'OPS': 0.830},
            "Alec Burleson": {'AB': 480, 'R': 65, 'HR': 22, 'RBI': 78, 'SB': 3, 'AVG': 0.270, 'OPS': 0.780},
            "Vinnie Pasquantino": {'AB': 570, 'R': 83, 'HR': 24, 'RBI': 90, 'SB': 2, 'AVG': 0.285, 'OPS': 0.815},
            "Josh Naylor": {'AB': 540, 'R': 78, 'HR': 30, 'RBI': 95, 'SB': 4, 'AVG': 0.270, 'OPS': 0.820},
            "Roman Anthony": {'AB': 350, 'R': 48, 'HR': 12, 'RBI': 45, 'SB': 8, 'AVG': 0.251, 'OPS': 0.740},
            
            # Middle Infielders
            "Mookie Betts": {'AB': 580, 'R': 115, 'HR': 30, 'RBI': 85, 'SB': 18, 'AVG': 0.293, 'OPS': 0.915},
            "CJ Abrams": {'AB': 610, 'R': 97, 'HR': 18, 'RBI': 65, 'SB': 43, 'AVG': 0.275, 'OPS': 0.780},
            "Matt McLain": {'AB': 520, 'R': 78, 'HR': 20, 'RBI': 68, 'SB': 18, 'AVG': 0.268, 'OPS': 0.790},
            "Luis García Jr.": {'AB': 540, 'R': 75, 'HR': 16, 'RBI': 65, 'SB': 5, 'AVG': 0.270, 'OPS': 0.750},
            "Brice Turang": {'AB': 500, 'R': 70, 'HR': 10, 'RBI': 50, 'SB': 30, 'AVG': 0.258, 'OPS': 0.710},
            "Ketel Marte": {'AB': 560, 'R': 92, 'HR': 28, 'RBI': 85, 'SB': 8, 'AVG': 0.282, 'OPS': 0.850},
            "Ozzie Albies": {'AB': 600, 'R': 95, 'HR': 26, 'RBI': 90, 'SB': 15, 'AVG': 0.285, 'OPS': 0.830},
            "Gunnar Henderson": {'AB': 570, 'R': 95, 'HR': 32, 'RBI': 95, 'SB': 15, 'AVG': 0.270, 'OPS': 0.860},
            "Jeremy Peña": {'AB': 580, 'R': 80, 'HR': 20, 'RBI': 72, 'SB': 15, 'AVG': 0.265, 'OPS': 0.750},
            "Ezequiel Tovar": {'AB': 590, 'R': 85, 'HR': 22, 'RBI': 78, 'SB': 18, 'AVG': 0.278, 'OPS': 0.785},
            "Elly De La Cruz": {'AB': 540, 'R': 90, 'HR': 25, 'RBI': 75, 'SB': 45, 'AVG': 0.245, 'OPS': 0.780},
            "Trea Turner": {'AB': 600, 'R': 100, 'HR': 25, 'RBI': 80, 'SB': 30, 'AVG': 0.290, 'OPS': 0.850},
            "Corey Seager": {'AB': 580, 'R': 98, 'HR': 35, 'RBI': 100, 'SB': 3, 'AVG': 0.295, 'OPS': 0.910},
            "Willy Adames": {'AB': 560, 'R': 85, 'HR': 30, 'RBI': 95, 'SB': 8, 'AVG': 0.255, 'OPS': 0.820},
            "Bo Bichette": {'AB': 590, 'R': 90, 'HR': 22, 'RBI': 85, 'SB': 12, 'AVG': 0.290, 'OPS': 0.830},
            "Francisco Lindor": {'AB': 620, 'R': 95, 'HR': 28, 'RBI': 85, 'SB': 18, 'AVG': 0.270, 'OPS': 0.830},
            "Tommy Edman": {'AB': 450, 'R': 72, 'HR': 11, 'RBI': 50, 'SB': 28, 'AVG': 0.272, 'OPS': 0.730},
            "Jonathan India": {'AB': 520, 'R': 80, 'HR': 17, 'RBI': 58, 'SB': 15, 'AVG': 0.265, 'OPS': 0.765},
            "Trevor Story": {'AB': 440, 'R': 65, 'HR': 19, 'RBI': 70, 'SB': 12, 'AVG': 0.255, 'OPS': 0.750},
            "Anthony Volpe": {'AB': 550, 'R': 85, 'HR': 20, 'RBI': 70, 'SB': 25, 'AVG': 0.252, 'OPS': 0.760},
            "Masyn Winn": {'AB': 550, 'R': 75, 'HR': 12, 'RBI': 60, 'SB': 25, 'AVG': 0.272, 'OPS': 0.745},
            "Jackson Holliday": {'AB': 520, 'R': 78, 'HR': 18, 'RBI': 70, 'SB': 12, 'AVG': 0.265, 'OPS': 0.785},
            "Jose Altuve": {'AB': 560, 'R': 95, 'HR': 22, 'RBI': 75, 'SB': 15, 'AVG': 0.290, 'OPS': 0.840},
            
            # Third Basemen
            "Austin Riley": {'AB': 570, 'R': 92, 'HR': 34, 'RBI': 105, 'SB': 4, 'AVG': 0.278, 'OPS': 0.855},
            "Jordan Westburg": {'AB': 540, 'R': 75, 'HR': 22, 'RBI': 80, 'SB': 8, 'AVG': 0.265, 'OPS': 0.780},
            "Manny Machado": {'AB': 560, 'R': 85, 'HR': 28, 'RBI': 90, 'SB': 5, 'AVG': 0.275, 'OPS': 0.835},
            "Max Muncy": {'AB': 490, 'R': 80, 'HR': 30, 'RBI': 85, 'SB': 1, 'AVG': 0.240, 'OPS': 0.820},
            "Alec Bohm": {'AB': 580, 'R': 82, 'HR': 22, 'RBI': 95, 'SB': 4, 'AVG': 0.282, 'OPS': 0.815},
            "Junior Caminero": {'AB': 520, 'R': 72, 'HR': 25, 'RBI': 80, 'SB': 5, 'AVG': 0.260, 'OPS': 0.780},
            "José Ramírez": {'AB': 590, 'R': 100, 'HR': 35, 'RBI': 110, 'SB': 25, 'AVG': 0.280, 'OPS': 0.900},
            "Alex Bregman": {'AB': 560, 'R': 90, 'HR': 25, 'RBI': 92, 'SB': 2, 'AVG': 0.275, 'OPS': 0.850},
            "Isaac Paredes": {'AB': 530, 'R': 75, 'HR': 28, 'RBI': 85, 'SB': 2, 'AVG': 0.258, 'OPS': 0.810},
            "Rafael Devers": {'AB': 580, 'R': 95, 'HR': 35, 'RBI': 105, 'SB': 3, 'AVG': 0.290, 'OPS': 0.880},
            "Matt Chapman": {'AB': 540, 'R': 85, 'HR': 28, 'RBI': 90, 'SB': 2, 'AVG': 0.252, 'OPS': 0.825},
            "Eugenio Suárez": {'AB': 520, 'R': 75, 'HR': 28, 'RBI': 85, 'SB': 2, 'AVG': 0.235, 'OPS': 0.760},
            "Mark Vientos": {'AB': 490, 'R': 65, 'HR': 25, 'RBI': 75, 'SB': 2, 'AVG': 0.245, 'OPS': 0.780},
            "Josh Jung": {'AB': 520, 'R': 75, 'HR': 28, 'RBI': 88, 'SB': 3, 'AVG': 0.260, 'OPS': 0.810},
            
            # Outfielders
            "Lawrence Butler": {'AB': 520, 'R': 82, 'HR': 24, 'RBI': 75, 'SB': 24, 'AVG': 0.256, 'OPS': 0.780},
            "Riley Greene": {'AB': 570, 'R': 88, 'HR': 27, 'RBI': 84, 'SB': 12, 'AVG': 0.270, 'OPS': 0.815},
            "Adolis García": {'AB': 550, 'R': 85, 'HR': 32, 'RBI': 96, 'SB': 16, 'AVG': 0.248, 'OPS': 0.790},
            "Taylor Ward": {'AB': 510, 'R': 75, 'HR': 22, 'RBI': 78, 'SB': 5, 'AVG': 0.261, 'OPS': 0.768},
            "Kyle Tucker": {'AB': 560, 'R': 95, 'HR': 35, 'RBI': 100, 'SB': 20, 'AVG': 0.280, 'OPS': 0.885},
            "Corbin Carroll": {'AB': 580, 'R': 95, 'HR': 20, 'RBI': 75, 'SB': 40, 'AVG': 0.275, 'OPS': 0.830},
            "Lane Thomas": {'AB': 590, 'R': 85, 'HR': 25, 'RBI': 80, 'SB': 20, 'AVG': 0.265, 'OPS': 0.790},
            "Jasson Domínguez": {'AB': 520, 'R': 75, 'HR': 25, 'RBI': 80, 'SB': 20, 'AVG': 0.255, 'OPS': 0.780},
            "Tyler O'Neill": {'AB': 490, 'R': 75, 'HR': 28, 'RBI': 80, 'SB': 8, 'AVG': 0.258, 'OPS': 0.810},
            "Kyle Schwarber": {'AB': 520, 'R': 95, 'HR': 38, 'RBI': 95, 'SB': 2, 'AVG': 0.235, 'OPS': 0.850},
            "Marcell Ozuna": {'AB': 550, 'R': 85, 'HR': 35, 'RBI': 100, 'SB': 3, 'AVG': 0.272, 'OPS': 0.870},
            "Randy Arozarena": {'AB': 540, 'R': 90, 'HR': 25, 'RBI': 85, 'SB': 20, 'AVG': 0.250, 'OPS': 0.800},
            "Brent Rooker": {'AB': 520, 'R': 75, 'HR': 30, 'RBI': 90, 'SB': 5, 'AVG': 0.248, 'OPS': 0.810},
            "Teoscar Hernández": {'AB': 540, 'R': 85, 'HR': 32, 'RBI': 95, 'SB': 6, 'AVG': 0.260, 'OPS': 0.820},
            "Bryan Reynolds": {'AB': 570, 'R': 85, 'HR': 22, 'RBI': 82, 'SB': 8, 'AVG': 0.280, 'OPS': 0.820},
            "Josh Lowe": {'AB': 530, 'R': 80, 'HR': 20, 'RBI': 75, 'SB': 22, 'AVG': 0.275, 'OPS': 0.800},
            "Mike Trout": {'AB': 500, 'R': 95, 'HR': 35, 'RBI': 90, 'SB': 10, 'AVG': 0.285, 'OPS': 0.950},
            "Steven Kwan": {'AB': 580, 'R': 90, 'HR': 8, 'RBI': 50, 'SB': 23, 'AVG': 0.305, 'OPS': 0.780},
            "Dylan Crews": {'AB': 480, 'R': 70, 'HR': 20, 'RBI': 75, 'SB': 8, 'AVG': 0.265, 'OPS': 0.780},
            "Shohei Ohtani": {'AB': 580, 'R': 105, 'HR': 40, 'RBI': 110, 'SB': 25, 'AVG': 0.285, 'OPS': 0.970},
            "Nick Castellanos": {'AB': 570, 'R': 80, 'HR': 26, 'RBI': 90, 'SB': 6, 'AVG': 0.265, 'OPS': 0.800},
            "Fernando Tatis Jr.": {'AB': 570, 'R': 100, 'HR': 32, 'RBI': 85, 'SB': 25, 'AVG': 0.275, 'OPS': 0.870},
            "Michael Harris II": {'AB': 560, 'R': 85, 'HR': 23, 'RBI': 80, 'SB': 20, 'AVG': 0.282, 'OPS': 0.820},
            "Brandon Nimmo": {'AB': 550, 'R': 90, 'HR': 20, 'RBI': 65, 'SB': 5, 'AVG': 0.270, 'OPS': 0.830},
            "Pete Crow-Armstrong": {'AB': 520, 'R': 75, 'HR': 15, 'RBI': 60, 'SB': 30, 'AVG': 0.255, 'OPS': 0.750},
            "Ryan Mountcastle": {'AB': 530, 'R': 75, 'HR': 26, 'RBI': 85, 'SB': 2, 'AVG': 0.262, 'OPS': 0.790},
            "Juan Soto": {'AB': 550, 'R': 110, 'HR': 35, 'RBI': 95, 'SB': 8, 'AVG': 0.300, 'OPS': 0.995},
            "Julio Rodríguez": {'AB': 600, 'R': 95, 'HR': 30, 'RBI': 90, 'SB': 30, 'AVG': 0.280, 'OPS': 0.850},
            "Anthony Santander": {'AB': 550, 'R': 85, 'HR': 35, 'RBI': 100, 'SB': 2, 'AVG': 0.255, 'OPS': 0.825},
            "Jarren Duran": {'AB': 590, 'R': 95, 'HR': 18, 'RBI': 70, 'SB': 35, 'AVG': 0.280, 'OPS': 0.820},
            "Wyatt Langford": {'AB': 540, 'R': 85, 'HR': 25, 'RBI': 80, 'SB': 15, 'AVG': 0.270, 'OPS': 0.830},
            "Luis Robert Jr.": {'AB': 540, 'R': 90, 'HR': 35, 'RBI': 95, 'SB': 20, 'AVG': 0.265, 'OPS': 0.855},
            "Colton Cowser": {'AB': 500, 'R': 75, 'HR': 22, 'RBI': 75, 'SB': 10, 'AVG': 0.255, 'OPS': 0.790},
            "Jackson Chourio": {'AB': 550, 'R': 80, 'HR': 20, 'RBI': 75, 'SB': 25, 'AVG': 0.265, 'OPS': 0.780},
            "Seiya Suzuki": {'AB': 520, 'R': 80, 'HR': 25, 'RBI': 85, 'SB': 12, 'AVG': 0.275, 'OPS': 0.835},
            "Jazz Chisholm Jr.": {'AB': 540, 'R': 85, 'HR': 24, 'RBI': 75, 'SB': 22, 'AVG': 0.255, 'OPS': 0.790},
            "Christian Yelich": {'AB': 570, 'R': 95, 'HR': 22, 'RBI': 80, 'SB': 18, 'AVG': 0.285, 'OPS': 0.860},
            "George Springer": {'AB': 550, 'R': 90, 'HR': 25, 'RBI': 75, 'SB': 10, 'AVG': 0.260, 'OPS': 0.810},
            "Yordan Alvarez": {'AB': 560, 'R': 95, 'HR': 38, 'RBI': 110, 'SB': 1, 'AVG': 0.295, 'OPS': 0.945},
            "Ian Happ": {'AB': 540, 'R': 85, 'HR': 25, 'RBI': 75, 'SB': 10, 'AVG': 0.255, 'OPS': 0.800},
            "Victor Robles": {'AB': 480, 'R': 65, 'HR': 8, 'RBI': 45, 'SB': 30, 'AVG': 0.250, 'OPS': 0.685},
            "Jorge Soler": {'AB': 520, 'R': 80, 'HR': 32, 'RBI': 85, 'SB': 2, 'AVG': 0.245, 'OPS': 0.815},
            "Aaron Judge": {'AB': 550, 'R': 115, 'HR': 45, 'RBI': 115, 'SB': 10, 'AVG': 0.295, 'OPS': 1.050},
            "Jackson Merrill": {'AB': 550, 'R': 75, 'HR': 18, 'RBI': 70, 'SB': 15, 'AVG': 0.265, 'OPS': 0.775},
            "James Wood": {'AB': 520, 'R': 80, 'HR': 25, 'RBI': 80, 'SB': 15, 'AVG': 0.258, 'OPS': 0.800},
            "Brenton Doyle": {'AB': 530, 'R': 70, 'HR': 20, 'RBI': 65, 'SB': 20, 'AVG': 0.240, 'OPS': 0.730},
            "Ronald Acuña Jr.": {'AB': 600, 'R': 110, 'HR': 32, 'RBI': 85, 'SB': 40, 'AVG': 0.320, 'OPS': 0.950},
            "Jurickson Profar": {'AB': 550, 'R': 80, 'HR': 18, 'RBI': 70, 'SB': 8, 'AVG': 0.255, 'OPS': 0.770},
            "Dansby Swanson": {'AB': 580, 'R': 85, 'HR': 22, 'RBI': 75, 'SB': 12, 'AVG': 0.255, 'OPS': 0.775},
            "Michael Toglia": {'AB': 450, 'R': 60, 'HR': 20, 'RBI': 65, 'SB': 5, 'AVG': 0.235, 'OPS': 0.730},
            "Carlos Correa": {'AB': 540, 'R': 80, 'HR': 24, 'RBI': 85, 'SB': 2, 'AVG': 0.270, 'OPS': 0.820},
            "Bobby Witt Jr.": {'AB': 620, 'R': 100, 'HR': 30, 'RBI': 95, 'SB': 35, 'AVG': 0.285, 'OPS': 0.850},
            "Oneil Cruz": {'AB': 560, 'R': 85, 'HR': 28, 'RBI': 85, 'SB': 18, 'AVG': 0.250, 'OPS': 0.815},
            "Marcus Semien": {'AB': 650, 'R': 105, 'HR': 28, 'RBI': 90, 'SB': 15, 'AVG': 0.270, 'OPS': 0.830},
            "Bryson Stott": {'AB': 590, 'R': 85, 'HR': 15, 'RBI': 70, 'SB': 25, 'AVG': 0.275, 'OPS': 0.760},
            "Jake Burger": {'AB': 500, 'R': 70, 'HR': 32, 'RBI': 90, 'SB': 1, 'AVG': 0.245, 'OPS': 0.815},
            "Luis Arraez": {'AB': 600, 'R': 85, 'HR': 5, 'RBI': 55, 'SB': 3, 'AVG': 0.325, 'OPS': 0.800},
            "Xavier Edwards": {'AB': 520, 'R': 75, 'HR': 5, 'RBI': 45, 'SB': 28, 'AVG': 0.290, 'OPS': 0.740},
            "Andrés Giménez": {'AB': 560, 'R': 75, 'HR': 15, 'RBI': 65, 'SB': 20, 'AVG': 0.265, 'OPS': 0.745}
        }
        
        # Default pitcher projections based on industry averages
        self.pitcher_projections = {
            # Starting Pitchers
            "Cole Ragans": {'IP': 185, 'ERA': 3.15, 'WHIP': 1.12, 'K9': 10.8, 'QS': 18, 'SV': 0},
            "Hunter Greene": {'IP': 170, 'ERA': 3.45, 'WHIP': 1.18, 'K9': 11.5, 'QS': 16, 'SV': 0},
            "Jack Flaherty": {'IP': 180, 'ERA': 3.60, 'WHIP': 1.20, 'K9': 9.8, 'QS': 15, 'SV': 0},
            "Tarik Skubal": {'IP': 190, 'ERA': 3.10, 'WHIP': 1.05, 'K9': 10.5, 'QS': 20, 'SV': 0},
            "Spencer Schwellenbach": {'IP': 165, 'ERA': 3.50, 'WHIP': 1.18, 'K9': 9.2, 'QS': 14, 'SV': 0},
            "Hunter Brown": {'IP': 175, 'ERA': 3.80, 'WHIP': 1.25, 'K9': 9.5, 'QS': 15, 'SV': 0},
            "Justin Verlander": {'IP': 160, 'ERA': 3.65, 'WHIP': 1.15, 'K9': 8.5, 'QS': 15, 'SV': 0},
            "Max Scherzer": {'IP': 140, 'ERA': 3.55, 'WHIP': 1.12, 'K9': 10.0, 'QS': 13, 'SV': 0},
            "Corbin Burnes": {'IP': 200, 'ERA': 3.05, 'WHIP': 1.08, 'K9': 9.8, 'QS': 22, 'SV': 0},
            "Jacob deGrom": {'IP': 130, 'ERA': 2.80, 'WHIP': 0.95, 'K9': 11.8, 'QS': 15, 'SV': 0},
            "Yoshinobu Yamamoto": {'IP': 175, 'ERA': 3.25, 'WHIP': 1.12, 'K9': 9.2, 'QS': 18, 'SV': 0},
            "Logan Webb": {'IP': 195, 'ERA': 3.15, 'WHIP': 1.10, 'K9': 8.2, 'QS': 21, 'SV': 0},
            "Zac Gallen": {'IP': 185, 'ERA': 3.30, 'WHIP': 1.10, 'K9': 9.5, 'QS': 20, 'SV': 0},
            "Aaron Nola": {'IP': 200, 'ERA': 3.40, 'WHIP': 1.12, 'K9': 9.2, 'QS': 20, 'SV': 0},
            "Paul Skenes": {'IP': 170, 'ERA': 3.15, 'WHIP': 1.10, 'K9': 10.5, 'QS': 18, 'SV': 0},
            "Kodai Senga": {'IP': 165, 'ERA': 3.25, 'WHIP': 1.15, 'K9': 10.2, 'QS': 16, 'SV': 0},
            "Drew Rasmussen": {'IP': 140, 'ERA': 3.60, 'WHIP': 1.20, 'K9': 8.8, 'QS': 12, 'SV': 0},
            "Zach Eflin": {'IP': 180, 'ERA': 3.45, 'WHIP': 1.12, 'K9': 8.5, 'QS': 18, 'SV': 0},
            "Shane Baz": {'IP': 150, 'ERA': 3.50, 'WHIP': 1.18, 'K9': 10.2, 'QS': 14, 'SV': 0},
            "Zack Wheeler": {'IP': 195, 'ERA': 3.10, 'WHIP': 1.08, 'K9': 9.8, 'QS': 21, 'SV': 0},
            "Framber Valdez": {'IP': 190, 'ERA': 3.25, 'WHIP': 1.15, 'K9': 8.5, 'QS': 20, 'SV': 0},
            "Taj Bradley": {'IP': 160, 'ERA': 3.70, 'WHIP': 1.22, 'K9': 10.5, 'QS': 14, 'SV': 0},
            "Shota Imanaga": {'IP': 170, 'ERA': 3.40, 'WHIP': 1.15, 'K9': 9.5, 'QS': 16, 'SV': 0},
            "Justin Steele": {'IP': 175, 'ERA': 3.30, 'WHIP': 1.15, 'K9': 8.8, 'QS': 17, 'SV': 0},
            "Freddy Peralta": {'IP': 165, 'ERA': 3.35, 'WHIP': 1.10, 'K9': 11.2, 'QS': 15, 'SV': 0},
            "Michael King": {'IP': 170, 'ERA': 3.60, 'WHIP': 1.20, 'K9': 9.5, 'QS': 16, 'SV': 0},
            "Pablo López": {'IP': 185, 'ERA': 3.45, 'WHIP': 1.15, 'K9': 10.0, 'QS': 19, 'SV': 0},
            "Luis Castillo": {'IP': 190, 'ERA': 3.30, 'WHIP': 1.12, 'K9': 9.8, 'QS': 20, 'SV': 0},
            "Sonny Gray": {'IP': 175, 'ERA': 3.35, 'WHIP': 1.13, 'K9': 9.5, 'QS': 18, 'SV': 0},
            "George Kirby": {'IP': 185, 'ERA': 3.25, 'WHIP': 1.05, 'K9': 8.8, 'QS': 19, 'SV': 0},
            "Carlos Rodón": {'IP': 170, 'ERA': 3.55, 'WHIP': 1.20, 'K9': 10.2, 'QS': 16, 'SV': 0},
            "Yusei Kikuchi": {'IP': 160, 'ERA': 3.80, 'WHIP': 1.25, 'K9': 9.5, 'QS': 14, 'SV': 0},
            "Blake Snell": {'IP': 165, 'ERA': 3.20, 'WHIP': 1.15, 'K9': 12.0, 'QS': 15, 'SV': 0},
            "Bryce Miller": {'IP': 175, 'ERA': 3.65, 'WHIP': 1.18, 'K9': 8.8, 'QS': 16, 'SV': 0},
            "Nick Lodolo": {'IP': 160, 'ERA': 3.70, 'WHIP': 1.20, 'K9': 10.5, 'QS': 14, 'SV': 0},
            "Sandy Alcantara": {'IP': 200, 'ERA': 3.10, 'WHIP': 1.08, 'K9': 8.5, 'QS': 22, 'SV': 0},
            "Robbie Ray": {'IP': 170, 'ERA': 3.65, 'WHIP': 1.22, 'K9': 10.8, 'QS': 15, 'SV': 0},
            "Seth Lugo": {'IP': 180, 'ERA': 3.45, 'WHIP': 1.15, 'K9': 8.5, 'QS': 18, 'SV': 0},
            "Spencer Strider": {'IP': 180, 'ERA': 2.90, 'WHIP': 1.02, 'K9': 13.5, 'QS': 18, 'SV': 0},
            "Logan Gilbert": {'IP': 185, 'ERA': 3.35, 'WHIP': 1.10, 'K9': 9.8, 'QS': 19, 'SV': 0},
            "Dylan Cease": {'IP': 180, 'ERA': 3.45, 'WHIP': 1.18, 'K9': 11.0, 'QS': 17, 'SV': 0},
            "Joe Ryan": {'IP': 175, 'ERA': 3.55, 'WHIP': 1.15, 'K9': 10.2, 'QS': 16, 'SV': 0},
            "Walker Buehler": {'IP': 160, 'ERA': 3.40, 'WHIP': 1.12, 'K9': 9.0, 'QS': 15, 'SV': 0},
            "Cristian Javier": {'IP': 170, 'ERA': 3.65, 'WHIP': 1.20, 'K9': 9.8, 'QS': 16, 'SV': 0},
            "Lucas Giolito": {'IP': 185, 'ERA': 3.75, 'WHIP': 1.22, 'K9': 9.5, 'QS': 17, 'SV': 0},
            "Max Fried": {'IP': 180, 'ERA': 3.25, 'WHIP': 1.12, 'K9': 8.8, 'QS': 19, 'SV': 0},
            "Brandon Woodruff": {'IP': 150, 'ERA': 3.15, 'WHIP': 1.05, 'K9': 10.0, 'QS': 16, 'SV': 0},
            "Garrett Crochet": {'IP': 155, 'ERA': 3.25, 'WHIP': 1.10, 'K9': 11.5, 'QS': 14, 'SV': 0},
            "Tyler Glasnow": {'IP': 160, 'ERA': 3.10, 'WHIP': 1.05, 'K9': 12.0, 'QS': 16, 'SV': 0},
            "Bryan Woo": {'IP': 160, 'ERA': 3.70, 'WHIP': 1.20, 'K9': 9.0, 'QS': 14, 'SV': 0},
            "Tanner Bibee": {'IP': 175, 'ERA': 3.45, 'WHIP': 1.15, 'K9': 9.5, 'QS': 17, 'SV': 0},
            "Bailey Ober": {'IP': 170, 'ERA': 3.50, 'WHIP': 1.12, 'K9': 9.2, 'QS': 16, 'SV': 0},
            "Cristopher Sánchez": {'IP': 175, 'ERA': 3.60, 'WHIP': 1.20, 'K9': 8.5, 'QS': 16, 'SV': 0},
            "Shane Bieber": {'IP': 180, 'ERA': 3.30, 'WHIP': 1.10, 'K9': 9.0, 'QS': 19, 'SV': 0},
            "Mitch Keller": {'IP': 185, 'ERA': 3.55, 'WHIP': 1.18, 'K9': 9.0, 'QS': 18, 'SV': 0},
            "Chris Sale": {'IP': 165, 'ERA': 3.20, 'WHIP': 1.08, 'K9': 11.0, 'QS': 16, 'SV': 0},
            "Nathan Eovaldi": {'IP': 170, 'ERA': 3.40, 'WHIP': 1.15, 'K9': 8.5, 'QS': 17, 'SV': 0},
            "Ryan Pepiot": {'IP': 145, 'ERA': 3.85, 'WHIP': 1.25, 'K9': 9.2, 'QS': 12, 'SV': 0},
            "MacKenzie Gore": {'IP': 160, 'ERA': 3.95, 'WHIP': 1.28, 'K9': 10.1, 'QS': 13, 'SV': 0},
            
            # Relief Pitchers
            "Ryan Helsley": {'IP': 65, 'ERA': 2.35, 'WHIP': 0.98, 'K9': 11.2, 'QS': 0, 'SV': 38},
            "Tanner Scott": {'IP': 68, 'ERA': 2.75, 'WHIP': 1.12, 'K9': 12.1, 'QS': 0, 'SV': 34},
            "Pete Fairbanks": {'IP': 55, 'ERA': 2.90, 'WHIP': 1.05, 'K9': 11.8, 'QS': 0, 'SV': 28},
            "Camilo Doval": {'IP': 58, 'ERA': 3.65, 'WHIP': 1.22, 'K9': 10.8, 'QS': 0, 'SV': 24},
            "Jhoan Duran": {'IP': 60, 'ERA': 2.60, 'WHIP': 1.02, 'K9': 12.5, 'QS': 0, 'SV': 36},
            "Jeff Hoffman": {'IP': 70, 'ERA': 3.10, 'WHIP': 1.15, 'K9': 11.2, 'QS': 0, 'SV': 5},
            "Ryan Pressly": {'IP': 60, 'ERA': 2.85, 'WHIP': 1.08, 'K9': 10.8, 'QS': 0, 'SV': 32},
            "Carlos Estévez": {'IP': 62, 'ERA': 3.20, 'WHIP': 1.18, 'K9': 10.0, 'QS': 0, 'SV': 30},
            "Jordan Romano": {'IP': 60, 'ERA': 2.75, 'WHIP': 1.10, 'K9': 10.5, 'QS': 0, 'SV': 32},
            "Blake Treinen": {'IP': 65, 'ERA': 3.05, 'WHIP': 1.12, 'K9': 9.8, 'QS': 0, 'SV': 8},
            "Emmanuel Clase": {'IP': 70, 'ERA': 2.40, 'WHIP': 0.95, 'K9': 9.5, 'QS': 0, 'SV': 42},
            "Josh Hader": {'IP': 65, 'ERA': 2.65, 'WHIP': 1.05, 'K9': 13.5, 'QS': 0, 'SV': 38},
            "Félix Bautista": {'IP': 65, 'ERA': 2.55, 'WHIP': 1.00, 'K9': 14.0, 'QS': 0, 'SV': 40},
            "Robert Suarez": {'IP': 65, 'ERA': 2.80, 'WHIP': 1.10, 'K9': 10.5, 'QS': 0, 'SV': 35},
            "Alexis Díaz": {'IP': 62, 'ERA': 2.90, 'WHIP': 1.12, 'K9': 11.8, 'QS': 0, 'SV': 36},
            "David Bednar": {'IP': 68, 'ERA': 2.75, 'WHIP': 1.08, 'K9': 11.2, 'QS': 0, 'SV': 32},
            "Lucas Erceg": {'IP': 70, 'ERA': 3.15, 'WHIP': 1.15, 'K9': 10.2, 'QS': 0, 'SV': 6},
            "Kenley Jansen": {'IP': 55, 'ERA': 3.25, 'WHIP': 1.12, 'K9': 10.5, 'QS': 0, 'SV': 30},
            "Chris Martin": {'IP': 60, 'ERA': 3.10, 'WHIP': 1.08, 'K9': 9.5, 'QS': 0, 'SV': 5},
            "Ben Joyce": {'IP': 65, 'ERA': 2.95, 'WHIP': 1.15, 'K9': 13.2, 'QS': 0, 'SV': 15},
            "Tyler Holton": {'IP': 70, 'ERA': 3.20, 'WHIP': 1.15, 'K9': 9.0, 'QS': 0, 'SV': 2},
            "Jason Adam": {'IP': 65, 'ERA': 2.85, 'WHIP': 1.10, 'K9': 10.8, 'QS': 0, 'SV': 18},
            "Devin Williams": {'IP': 60, 'ERA': 2.65, 'WHIP': 1.08, 'K9': 14.0, 'QS': 0, 'SV': 35},
            "Kyle Finnegan": {'IP': 65, 'ERA': 3.15, 'WHIP': 1.20, 'K9': 9.5, 'QS': 0, 'SV': 28},
            "Ryan Walker": {'IP': 68, 'ERA': 3.25, 'WHIP': 1.18, 'K9': 10.2, 'QS': 0, 'SV': 10},
            "Jason Foley": {'IP': 65, 'ERA': 3.35, 'WHIP': 1.22, 'K9': 8.5, 'QS': 0, 'SV': 25},
            "Grant Holmes": {'IP': 60, 'ERA': 3.45, 'WHIP': 1.25, 'K9': 9.8, 'QS': 0, 'SV': 5},
            "Raisel Iglesias": {'IP': 65, 'ERA': 2.80, 'WHIP': 1.05, 'K9': 11.0, 'QS': 0, 'SV': 35},
            "Cade Smith": {'IP': 60, 'ERA': 3.10, 'WHIP': 1.15, 'K9': 10.5, 'QS': 0, 'SV': 5},
            "Trevor Megill": {'IP': 65, 'ERA': 3.25, 'WHIP': 1.18, 'K9': 11.2, 'QS': 0, 'SV': 8},
            "Liam Hendriks": {'IP': 45, 'ERA': 3.10, 'WHIP': 1.12, 'K9': 11.5, 'QS': 0, 'SV': 20},
            "Clay Holmes": {'IP': 65, 'ERA': 3.05, 'WHIP': 1.15, 'K9': 9.8, 'QS': 0, 'SV': 32},
            "Andrés Muñoz": {'IP': 65, 'ERA': 2.70, 'WHIP': 1.05, 'K9': 12.5, 'QS': 0, 'SV': 30},
            "A.J. Minter": {'IP': 70, 'ERA': 3.00, 'WHIP': 1.10, 'K9': 11.0, 'QS': 0, 'SV': 8},
            "Reynaldo López": {'IP': 130, 'ERA': 3.45, 'WHIP': 1.18, 'K9': 9.8, 'QS': 10, 'SV': 0},
            "Michael Kopech": {'IP': 145, 'ERA': 3.75, 'WHIP': 1.25, 'K9': 10.5, 'QS': 12, 'SV': 0},
            "A.J. Puk": {'IP': 140, 'ERA': 3.50, 'WHIP': 1.20, 'K9': 10.8, 'QS': 10, 'SV': 0},
            "Mason Miller": {'IP': 60, 'ERA': 2.45, 'WHIP': 0.95, 'K9': 14.2, 'QS': 0, 'SV': 35},
            "Edwin Díaz": {'IP': 65, 'ERA': 2.35, 'WHIP': 0.98, 'K9': 13.8, 'QS': 0, 'SV': 38},
            "Orion Kerkering": {'IP': 60, 'ERA': 3.00, 'WHIP': 1.12, 'K9': 11.2, 'QS': 0, 'SV': 8},
            "Porter Hodge": {'IP': 50, 'ERA': 3.55, 'WHIP': 1.25, 'K9': 10.5, 'QS': 0, 'SV': 0},
            "Taylor Rogers": {'IP': 65, 'ERA': 3.15, 'WHIP': 1.15, 'K9': 10.2, 'QS': 0, 'SV': 18},
            "Calvin Faucher": {'IP': 60, 'ERA': 3.85, 'WHIP': 1.30, 'K9': 9.5, 'QS': 0, 'SV': 5},
            "Nick Martinez": {'IP': 130, 'ERA': 3.75, 'WHIP': 1.25, 'K9': 8.5, 'QS': 8, 'SV': 10},
            "Beau Brieske": {'IP': 120, 'ERA': 4.00, 'WHIP': 1.30, 'K9': 8.8, 'QS': 6, 'SV': 2}
        }
        
        print(f"Loaded default projections for {len(self.batter_projections)} batters and {len(self.pitcher_projections)} pitchers")
    
    def calculate_team_stats(self):
        """Calculate team statistics based on player projections"""
        team_batting_stats = {}
        team_pitching_stats = {}
        
        # Calculate batting stats for each team
        for team_name, roster in self.teams.items():
            team_batting_stats[team_name] = {
                'R': 0, 'HR': 0, 'RBI': 0, 'SB': 0, 'AB': 0, 'H': 0, 'TB': 0, 'OBP': 0, 'SLG': 0
            }
            
            # Sum up batting stats for each player
            for batter in roster['batters']:
                if batter in self.batter_projections:
                    proj = self.batter_projections[batter]
                    team_batting_stats[team_name]['R'] += proj['R']
                    team_batting_stats[team_name]['HR'] += proj['HR']
                    team_batting_stats[team_name]['RBI'] += proj['RBI']
                    team_batting_stats[team_name]['SB'] += proj['SB']
                    team_batting_stats[team_name]['AB'] += proj['AB']
                    # Calculate hits based on batting average
                    hits = round(proj['AB'] * proj['AVG'])
                    team_batting_stats[team_name]['H'] += hits
                    
                    # Estimate OBP and SLG from OPS and AVG
                    # Rough estimate: OBP = AVG + 0.07, SLG = OPS - OBP
                    obp = proj['AVG'] + 0.07
                    slg = proj['OPS'] - obp
                    # Estimate total bases for slugging
                    tb = round(proj['AB'] * slg)
                    team_batting_stats[team_name]['TB'] += tb
                else:
                    print(f"Warning: No projections found for batter {batter} on {team_name}")
            
            # Calculate AVG and OPS
            if team_batting_stats[team_name]['AB'] > 0:
                team_batting_stats[team_name]['AVG'] = round(team_batting_stats[team_name]['H'] / team_batting_stats[team_name]['AB'], 3)
                team_batting_stats[team_name]['SLG'] = round(team_batting_stats[team_name]['TB'] / team_batting_stats[team_name]['AB'], 3)
                team_batting_stats[team_name]['OBP'] = round(team_batting_stats[team_name]['AVG'] + 0.07, 3)  # Rough estimate
                team_batting_stats[team_name]['OPS'] = round(team_batting_stats[team_name]['OBP'] + team_batting_stats[team_name]['SLG'], 3)
            else:
                team_batting_stats[team_name]['AVG'] = 0
                team_batting_stats[team_name]['OPS'] = 0
        
        # Calculate pitching stats for each team
        for team_name, roster in self.teams.items():
            team_pitching_stats[team_name] = {
                'IP': 0, 'ER': 0, 'H': 0, 'BB': 0, 'K': 0, 'QS': 0, 'SV': 0
            }
            
            # Sum up pitching stats for each player
            for pitcher in roster['pitchers']:
                if pitcher in self.pitcher_projections:
                    proj = self.pitcher_projections[pitcher]
                    team_pitching_stats[team_name]['IP'] += proj['IP']
                    team_pitching_stats[team_name]['ER'] += round(proj['IP'] * proj['ERA'] / 9)
                    team_pitching_stats[team_name]['K'] += round(proj['IP'] * proj['K9'] / 9)
                    team_pitching_stats[team_name]['QS'] += proj['QS']
                    team_pitching_stats[team_name]['SV'] += proj['SV']
                    
                    # Estimate H and BB from WHIP
                    # Rough estimate: BB = IP * 0.35, H = WHIP * IP - BB
                    bb = round(proj['IP'] * 0.35)
                    h = round(proj['IP'] * proj['WHIP'] - bb)
                    team_pitching_stats[team_name]['H'] += h
                    team_pitching_stats[team_name]['BB'] += bb
                else:
                    print(f"Warning: No projections found for pitcher {pitcher} on {team_name}")
            
            # Calculate ERA and WHIP
            if team_pitching_stats[team_name]['IP'] > 0:
                team_pitching_stats[team_name]['ERA'] = round(team_pitching_stats[team_name]['ER'] * 9 / team_pitching_stats[team_name]['IP'], 2)
                team_pitching_stats[team_name]['WHIP'] = round((team_pitching_stats[team_name]['H'] + team_pitching_stats[team_name]['BB']) / team_pitching_stats[team_name]['IP'], 2)
                team_pitching_stats[team_name]['K9'] = round(team_pitching_stats[team_name]['K'] * 9 / team_pitching_stats[team_name]['IP'], 1)
            else:
                team_pitching_stats[team_name]['ERA'] = 0
                team_pitching_stats[team_name]['WHIP'] = 0
                team_pitching_stats[team_name]['K9'] = 0
        
        # Store the team stats
        self.team_batting_stats = team_batting_stats
        self.team_pitching_stats = team_pitching_stats
        
        print("Team statistics calculated successfully")
        return team_batting_stats, team_pitching_stats
    
    def rank_teams(self):
        """Rank teams based on each category and calculate points"""
        
        if not hasattr(self, 'team_batting_stats') or not hasattr(self, 'team_pitching_stats'):
            self.calculate_team_stats()
        
        # Categories to rank (higher is better except ERA and WHIP)
        batting_categories = ['R', 'HR', 'RBI', 'SB', 'AVG', 'OPS']
        pitching_categories = ['ERA', 'WHIP', 'K9', 'QS', 'SV']
        
        # Initialize rankings dictionary
        rankings = {cat: {} for cat in batting_categories + pitching_categories}
        team_points = {team: {'batting': 0, 'pitching': 0, 'total': 0} for team in self.teams.keys()}
        category_rankings = {team: {} for team in self.teams.keys()}
        
        # Rank batting categories
        for cat in batting_categories:
            # Sort teams by category value (descending)
            sorted_teams = sorted(self.team_batting_stats.keys(), 
                                 key=lambda x: self.team_batting_stats[x][cat], 
                                 reverse=True)
            
            # Assign points (12 for 1st, 11 for 2nd, etc.)
            for i, team in enumerate(sorted_teams):
                points = len(sorted_teams) - i
                rankings[cat][team] = points
                team_points[team]['batting'] += points
                category_rankings[team][cat] = i + 1  # Store rank (1st, 2nd, etc.)
        
        # Rank pitching categories
        for cat in pitching_categories:
            # For ERA and WHIP, lower is better
            reverse_sort = False if cat in ['ERA', 'WHIP'] else True
            
            sorted_teams = sorted(self.team_pitching_stats.keys(), 
                                 key=lambda x: self.team_pitching_stats[x][cat], 
                                 reverse=reverse_sort)
            
            for i, team in enumerate(sorted_teams):
                points = len(sorted_teams) - i
                rankings[cat][team] = points
                team_points[team]['pitching'] += points
                category_rankings[team][cat] = i + 1  # Store rank
        
        # Calculate total points
        for team in team_points:
            team_points[team]['total'] = team_points[team]['batting'] + team_points[team]['pitching']
        
        # Sort teams by total points
        sorted_teams = sorted(team_points.keys(), key=lambda x: team_points[x]['total'], reverse=True)
        
        # Create final rankings
        final_rankings = []
        for i, team in enumerate(sorted_teams):
            final_rankings.append({
                'rank': i + 1,
                'team': team,
                'batting_points': team_points[team]['batting'],
                'pitching_points': team_points[team]['pitching'],
                'total_points': team_points[team]['total']
            })
        
        # Store the rankings
        self.rankings = rankings
        self.team_points = team_points
        self.final_rankings = final_rankings
        self.category_rankings = category_rankings
        
        print("Team rankings calculated successfully")
        return final_rankings
    
    def analyze_your_team(self):
        """Analyze your team's strengths and weaknesses"""
        if not hasattr(self, 'category_rankings'):
            self.rank_teams()
        
        if self.your_team_name not in self.teams:
            print(f"Error: Your team '{self.your_team_name}' not found in the league")
            return None
        
        # Get your team's category rankings
        your_rankings = self.category_rankings[self.your_team_name]
        
        # Find strengths (top 4 categories)
        strengths = sorted(your_rankings.items(), key=lambda x: x[1])[:4]
        
        # Find weaknesses (bottom 4 categories)
        weaknesses = sorted(your_rankings.items(), key=lambda x: x[1], reverse=True)[:4]
        
        # Get your team's projected stats
        batting_stats = self.team_batting_stats[self.your_team_name]
        pitching_stats = self.team_pitching_stats[self.your_team_name]
        
        # Identify potential trade partners
        trade_partners = []
        
        # Look for teams with complementary needs
        for team in self.teams:
            if team == self.your_team_name:
                continue
            
            team_rankings = self.category_rankings[team]
            
            # Check if team is strong where you're weak and weak where you're strong
            strong_match = False
            weak_match = False
            
            for cat, rank in strengths:
                if team_rankings.get(cat, 0) > 8:  # They're weak where you're strong
                    strong_match = True
                    break
            
            for cat, rank in weaknesses:
                if team_rankings.get(cat, 0) < 5:  # They're strong where you're weak
                    weak_match = True
                    break
            
            if strong_match and weak_match:
                # They have complementary needs - good trade partner
                their_strengths = []
                their_weaknesses = []
                
                for cat, rank in sorted(team_rankings.items(), key=lambda x: x[1])[:3]:
                    their_strengths.append(cat)
                
                for cat, rank in sorted(team_rankings.items(), key=lambda x: x[1], reverse=True)[:3]:
                    their_weaknesses.append(cat)
                
                # Find notable players on their team
                notable_players = []
                
                # Add notable batters
                if any(cat in ['R', 'HR', 'RBI', 'SB', 'AVG', 'OPS'] for cat in their_strengths):
                    # Find top batters in the categories you need help with
                    for batter in self.teams[team]['batters']:
                        if batter in self.batter_projections:
                            proj = self.batter_projections[batter]
                            
                            # Check if player is strong in categories you need
                            is_notable = False
                            for cat, _ in weaknesses:
                                if cat == 'R' and proj['R'] > 90:
                                    is_notable = True
                                elif cat == 'HR' and proj['HR'] > 30:
                                    is_notable = True
                                elif cat == 'RBI' and proj['RBI'] > 90:
                                    is_notable = True
                                elif cat == 'SB' and proj['SB'] > 20:
                                    is_notable = True
                                elif cat == 'AVG' and proj['AVG'] > 0.280:
                                    is_notable = True
                                elif cat == 'OPS' and proj['OPS'] > 0.850:
                                    is_notable = True
                            
                            if is_notable and batter not in notable_players:
                                notable_players.append(batter)
                
                # Add notable pitchers
                if any(cat in ['ERA', 'WHIP', 'K9', 'QS', 'SV'] for cat in their_strengths):
                    # Find top pitchers in the categories you need help with
                    for pitcher in self.teams[team]['pitchers']:
                        if pitcher in self.pitcher_projections:
                            proj = self.pitcher_projections[pitcher]
                            
                            # Check if player is strong in categories you need
                            is_notable = False
                            for cat, _ in weaknesses:
                                if cat == 'ERA' and proj['ERA'] < 3.20:
                                    is_notable = True
                                elif cat == 'WHIP' and proj['WHIP'] < 1.10:
                                    is_notable = True
                                elif cat == 'K9' and proj['K9'] > 10.5:
                                    is_notable = True
                                elif cat == 'QS' and proj['QS'] > 18:
                                    is_notable = True
                                elif cat == 'SV' and proj['SV'] > 30:
                                    is_notable = True
                            
                            if is_notable and pitcher not in notable_players:
                                notable_players.append(pitcher)
                
                if notable_players:
                    trade_partners.append({
                        'team': team,
                        'their_strengths': their_strengths,
                        'their_weaknesses': their_weaknesses,
                        'notable_players': notable_players[:3]  # Limit to top 3 players
                    })
        
        # Get player projections for your team
        your_batters = []
        for batter in self.teams[self.your_team_name]['batters']:
            if batter in self.batter_projections:
                your_batters.append({
                    'name': batter,
                    'projections': self.batter_projections[batter]
                })
        
        your_pitchers = []
        for pitcher in self.teams[self.your_team_name]['pitchers']:
            if pitcher in self.pitcher_projections:
                your_pitchers.append({
                    'name': pitcher,
                    'projections': self.pitcher_projections[pitcher]
                })
        
        # Create the team analysis
        team_analysis = {
            'team_name': self.your_team_name,
            'overall_rank': next((r['rank'] for r in self.final_rankings if r['team'] == self.your_team_name), None),
            'total_points': next((r['total_points'] for r in self.final_rankings if r['team'] == self.your_team_name), None),
            'batting_stats': batting_stats,
            'pitching_stats': pitching_stats,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'trade_partners': trade_partners[:3],  # Limit to top 3 partners
            'batters': your_batters,
            'pitchers': your_pitchers
        }
        
        print(f"Team analysis completed for {self.your_team_name}")
        return team_analysis
    
    def generate_strategy_recommendations(self, team_analysis=None):
        """Generate strategy recommendations based on team analysis"""
        if team_analysis is None:
            team_analysis = self.analyze_your_team()
            
        if team_analysis is None:
            return None
        
        # Extract key areas from analysis
        strengths = [cat for cat, _ in team_analysis['strengths']]
        weaknesses = [cat for cat, _ in team_analysis['weaknesses']]
        
        recommendations = []
        
        # Recommendation 1: Address weaknesses
        weak_categories = []
        for cat, rank in team_analysis['weaknesses']:
            if cat in ['ERA', 'WHIP', 'K9', 'QS']:
                weak_categories.append('starting pitching')
            elif cat == 'SV':
                weak_categories.append('relief pitching')
            elif cat in ['HR', 'RBI']:
                weak_categories.append('power hitting')
            elif cat in ['R', 'SB']:
                weak_categories.append('speed')
            elif cat in ['AVG', 'OPS']:
                weak_categories.append('batting average/OPS')
        
        # Remove duplicates
        weak_categories = list(set(weak_categories))
        
        if weak_categories:
            recommendations.append(f"Target {', '.join(weak_categories)}: Your team is weakest in {', '.join(weaknesses)}. Consider trading for players who excel in these categories.")
        
        # Recommendation 2: Trade from strength
        if 'SB' in strengths or 'R' in strengths:
            # Find players with high SB/R who could be traded
            speed_players = []
            for batter in team_analysis['batters']:
                if batter['projections']['SB'] > 20 or batter['projections']['R'] > 90:
                    speed_players.append(batter['name'])
            
            if speed_players:
                recommendations.append(f"Trade from Strength: You have excellent {', '.join([s for s, _ in team_analysis['strengths'][:2]])} numbers. Consider trading a player like {', '.join(speed_players[:2])}, who provide significant value in these categories but may be expendable.")
        
        # Recommendation 3: Category-specific advice
        if 'OPS' in weaknesses:
            recommendations.append("Improve OPS: Your team is ranked low in OPS despite having good hitters. Consider adding a high-OPS bat like Juan Soto, Aaron Judge, or Yordan Alvarez if possible.")
        
        if 'ERA' in weaknesses or 'WHIP' in weaknesses:
            recommendations.append("Focus on Pitching Ratios: Target pitchers with elite ratios who may not be as highly valued for counting stats like QS or K.")
        
        # Recommendation 4: Relief pitching strategy
        relievers = [p for p in team_analysis['pitchers'] if p['projections']['SV'] > 0]
        if len(relievers) > 2 and 'SV' not in weaknesses:
            recommendations.append(f"Consider Trading a Closer: You have {len(relievers)} strong relievers. Consider trading one (perhaps {relievers[-1]['name']}) for help in other categories.")
        
        # Recommendation 5: Monitor bench players
        bench_batters = team_analysis['batters'][9:]  # Assuming standard 9 starting batters
        if bench_batters:
            recommendations.append(f"Monitor Bench: {', '.join([b['name'] for b in bench_batters])} are currently on your bench. Monitor their performance and be ready to use them if they outperform your starters.")
        
        # Recommendation 6: Potential trade package
        if team_analysis['trade_partners']:
            partner = team_analysis['trade_partners'][0]
            your_trade_chip = None
            for s in strengths:
                if s == 'SB' and any(b['projections']['SB'] > 20 for b in team_analysis['batters']):
                    your_trade_chip = next(b['name'] for b in team_analysis['batters'] if b['projections']['SB'] > 20)
                elif s == 'SV' and any(p['projections']['SV'] > 20 for p in team_analysis['pitchers']):
                    your_trade_chip = next(p['name'] for p in team_analysis['pitchers'] if p['projections']['SV'] > 20)
            
            if your_trade_chip and partner['notable_players']:
                recommendations.append(f"Potential Trade Package Example: Give: {your_trade_chip} ({s}) + Get: A high-quality player like {partner['notable_players'][0]} from {partner['team']}")
        
        # Recommendation 7: Waiver wire focus
        if 'ERA' in weaknesses or 'WHIP' in weaknesses:
            recommendations.append("Waiver Wire Focus: Keep an eye on the waiver wire for starting pitchers with good ratios, even if they don't accumulate many counting stats.")
        elif 'OPS' in weaknesses or 'AVG' in weaknesses:
            recommendations.append("Waiver Wire Focus: Monitor for high-OBP/SLG hitters who may be undervalued, especially players who get hot and could provide short-term value.")
        
        return recommendations
    
    def generate_report(self, output_file=None):
        """Generate a comprehensive league report"""
        if not hasattr(self, 'final_rankings'):
            self.rank_teams()
        
        team_analysis = self.analyze_your_team()
        recommendations = self.generate_strategy_recommendations(team_analysis)
        
        if output_file is None:
            output_file = f"reports/fantasy_baseball_report_{datetime.now().strftime('%Y%m%d')}.md"
        
        with open(output_file, 'w') as f:
            # Title
            f.write("# Fantasy Baseball League Analysis - 2025 Projections\n\n")
            
            # Team Batting Stats
            f.write("## Projected Team Statistics\n\n")
            f.write("### Batting Statistics\n")
            
            # Create batting table
            batting_table = []
            headers = ["Team", "R", "HR", "RBI", "SB", "AVG", "OPS"]
            
            for team, stats in self.team_batting_stats.items():
                batting_table.append([
                    team,
                    stats['R'],
                    stats['HR'],
                    stats['RBI'],
                    stats['SB'],
                    f"{stats['AVG']:.3f}",
                    f"{stats['OPS']:.3f}"
                ])
            
            f.write(tabulate(batting_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Team Pitching Stats
            f.write("### Pitching Statistics\n")
            
            # Create pitching table
            pitching_table = []
            headers = ["Team", "IP", "ERA", "WHIP", "K/9", "QS", "SV"]
            
            for team, stats in self.team_pitching_stats.items():
                pitching_table.append([
                    team,
                    stats['IP'],
                    stats['ERA'],
                    stats['WHIP'],
                    stats['K9'],
                    stats['QS'],
                    stats['SV']
                ])
            
            f.write(tabulate(pitching_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Overall Rankings
            f.write("## Overall Team Rankings\n")
            
            # Create rankings table
            rankings_table = []
            headers = ["Rank", "Team", "Batting Points", "Pitching Points", "Total Points"]
            
            for team in self.final_rankings:
                rankings_table.append([
                    team['rank'],
                    team['team'],
                    team['batting_points'],
                    team['pitching_points'],
                    team['total_points']
                ])
            
            f.write(tabulate(rankings_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Detailed Category Rankings
            f.write("## Detailed Category Rankings\n")
            
            # Create detailed rankings table
            detailed_table = []
            categories = ['R', 'HR', 'RBI', 'SB', 'AVG', 'OPS', 'ERA', 'WHIP', 'K9', 'QS', 'SV', 'Total']
            headers = ["Team"] + categories
            
            for team_data in self.final_rankings:
                team = team_data['team']
                row = [team]
                
                for cat in categories[:-1]:  # All except Total
                    row.append(self.category_rankings[team].get(cat, '-'))
                
                row.append(team_data['total_points'])  # Add Total points
                detailed_table.append(row)
            
            f.write(tabulate(detailed_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Your Team Analysis
            f.write(f"## Your Team Analysis ({self.your_team_name})\n\n")
            
            # Team Strengths
            f.write("### Team Strengths (Top 4 Categories):\n")
            for i, (cat, rank) in enumerate(team_analysis['strengths']):
                cat_value = None
                if cat in ['R', 'HR', 'RBI', 'SB']:
                    cat_value = team_analysis['batting_stats'][cat]
                elif cat in ['AVG', 'OPS']:
                    cat_value = f"{team_analysis['batting_stats'][cat]:.3f}"
                elif cat in ['ERA', 'WHIP', 'K9']:
                    cat_value = team_analysis['pitching_stats'][cat]
                elif cat in ['QS', 'SV']:
                    cat_value = team_analysis['pitching_stats'][cat]
                
                strength_desc = ""
                if cat == 'SB' and rank == 1:
                    strength_desc = "- League-leading stolen base total"
                elif cat == 'R' and rank <= 3:
                    strength_desc = "- Elite run production"
                elif cat == 'HR' and rank <= 3:
                    strength_desc = "- Top power production"
                elif cat == 'RBI' and rank <= 3:
                    strength_desc = "- Excellent RBI production"
                elif cat == 'SV' and rank <= 3:
                    closers = [p['name'] for p in team_analysis['pitchers'] if p['projections']['SV'] > 20]
                    if closers:
                        strength_desc = f"- Strong in saves with {', '.join(closers)}"
                
                f.write(f"{i+1}. **{cat}**: Rank {rank} ({cat_value}) {strength_desc}\n")
            
            f.write("\n")
            
            # Team Weaknesses
            f.write("### Team Weaknesses (Bottom 4 Categories):\n")
            for i, (cat, rank) in enumerate(team_analysis['weaknesses']):
                cat_value = None
                if cat in ['R', 'HR', 'RBI', 'SB']:
                    cat_value = team_analysis['batting_stats'][cat]
                elif cat in ['AVG', 'OPS']:
                    cat_value = f"{team_analysis['batting_stats'][cat]:.3f}"
                elif cat in ['ERA', 'WHIP', 'K9']:
                    cat_value = team_analysis['pitching_stats'][cat]
                elif cat in ['QS', 'SV']:
                    cat_value = team_analysis['pitching_stats'][cat]
                
                weakness_desc = ""
                if rank == len(self.teams):
                    weakness_desc = "- Worst in the league"
                elif rank >= len(self.teams) - 2:
                    weakness_desc = "- Near bottom of the league"
                elif cat == 'QS' and rank > len(self.teams) / 2:
                    weakness_desc = "- Below average in quality starts"
                
                f.write(f"{i+1}. **{cat}**: Rank {rank} ({cat_value}) {weakness_desc}\n")
            
            f.write("\n")
            
            # Potential Trade Targets
            f.write("### Potential Trade Targets:\n\n")
            
            for i, partner in enumerate(team_analysis['trade_partners']):
                f.write(f"{i+1}. **{partner['team']}**\n")
                f.write(f"   - Strong in: {', '.join(partner['their_strengths'])}\n")
                f.write(f"   - They are weak in: {', '.join(partner['their_weaknesses'])}\n")
                
                # Determine potential deal based on complementary needs
                your_strength = set([s for s, _ in team_analysis['strengths'][:2]])
                your_weakness = set([w for w, _ in team_analysis['weaknesses'][:2]])
                their_strength = set(partner['their_strengths'][:2])
                their_weakness = set(partner['their_weaknesses'][:2])
                
                common_interests = (your_strength.intersection(their_weakness)) and (your_weakness.intersection(their_strength))
                
                if common_interests:
                    deal_desc = f"Trade from your {', '.join(your_strength.intersection(their_weakness))} "
                    deal_desc += f"surplus for {', '.join(your_weakness.intersection(their_strength))} help"
                    f.write(f"   - Potential deal: {deal_desc}\n")
                
                if partner['notable_players']:
                    f.write(f"   - Players to target: {', '.join(partner['notable_players'])}\n")
                
                f.write("\n")
            
            # Player Projections
            f.write("## Player Projections for Your Team\n\n")
            
            # Batters
            f.write("### Batters\n")
            batter_table = []
            headers = ["Player", "AB", "R", "HR", "RBI", "SB", "AVG", "OPS"]
            
            for batter in team_analysis['batters']:
                batter_table.append([
                    batter['name'],
                    batter['projections']['AB'],
                    batter['projections']['R'],
                    batter['projections']['HR'],
                    batter['projections']['RBI'],
                    batter['projections']['SB'],
                    f"{batter['projections']['AVG']:.3f}",
                    f"{batter['projections']['OPS']:.3f}"
                ])
            
            f.write(tabulate(batter_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Pitchers
            f.write("### Pitchers\n")
            pitcher_table = []
            headers = ["Player", "IP", "ERA", "WHIP", "K/9", "QS", "SV"]
            
            for pitcher in team_analysis['pitchers']:
                pitcher_table.append([
                    pitcher['name'],
                    pitcher['projections']['IP'],
                    pitcher['projections']['ERA'],
                    pitcher['projections']['WHIP'],
                    pitcher['projections']['K9'],
                    pitcher['projections']['QS'],
                    pitcher['projections']['SV']
                ])
            
            f.write(tabulate(pitcher_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Strategy Recommendations
            f.write("## Strategy Recommendations\n\n")
            
            for i, rec in enumerate(recommendations):
                f.write(f"{i+1}. **{rec.split(':')[0]}**: {rec.split(':', 1)[1] if ':' in rec else rec}\n\n")
        
        print(f"Report generated successfully: {output_file}")
        return output_file
    
    def visualize_team_ranks(self, output_file=None):
        """Create a heatmap visualization of team ranks across categories"""
        if not hasattr(self, 'category_rankings'):
            self.rank_teams()
        
        if output_file is None:
            output_file = f"visuals/team_ranks_heatmap_{datetime.now().strftime('%Y%m%d')}.png"
        
        # Create a DataFrame from category rankings
        categories = ['R', 'HR', 'RBI', 'SB', 'AVG', 'OPS', 'ERA', 'WHIP', 'K9', 'QS', 'SV']
        rank_data = []
        
        for team in sorted(self.category_rankings.keys()):
            team_ranks = self.category_rankings[team]
            rank_data.append([team_ranks.get(cat, 0) for cat in categories])
        
        df = pd.DataFrame(rank_data, 
                         index=sorted(self.category_rankings.keys()),
                         columns=categories)
        
        # Set up the matplotlib figure
        plt.figure(figsize=(12, 10))
        
        # Generate a heatmap
        sns.heatmap(df, annot=True, cmap="YlGnBu_r", linewidths=0.5, fmt="d")
        
        plt.title("Team Category Rankings Heatmap (1 = Best)", fontsize=16)
        plt.ylabel("Teams", fontsize=12)
        plt.xlabel("Categories", fontsize=12)
        
        # Save the figure
        plt.tight_layout()
        plt.savefig(output_file)
        plt.close()
        
        print(f"Heatmap visualization saved to {output_file}")
        return output_file
    
    def visualize_team_strengths(self, output_file=None):
        """Create a radar chart of your team's strengths relative to league average"""
        if not hasattr(self, 'team_batting_stats') or not hasattr(self, 'team_pitching_stats'):
            self.calculate_team_stats()
        
        if output_file is None:
            output_file = f"visuals/team_strengths_radar_{datetime.now().strftime('%Y%m%d')}.png"
        
        # Categories to compare
        categories = ['R', 'HR', 'RBI', 'SB', 'AVG', 'OPS', 'ERA', 'WHIP', 'K9', 'QS', 'SV']
        
        # Calculate league averages
        league_avgs = {}
        for cat in categories[:6]:  # Batting cats
            values = [stats[cat] for team, stats in self.team_batting_stats.items()]
            league_avgs[cat] = sum(values) / len(values)
        
        for cat in categories[6:]:  # Pitching cats
            values = [stats[cat] for team, stats in self.team_pitching_stats.items()]
            league_avgs[cat] = sum(values) / len(values)
        
        # Get your team's stats
        your_stats = {}
        for cat in categories[:6]:
            your_stats[cat] = self.team_batting_stats[self.your_team_name][cat]
        
        for cat in categories[6:]:
            your_stats[cat] = self.team_pitching_stats[self.your_team_name][cat]
        
        # For radar chart, we need to normalize the values
        # For ERA and WHIP, lower is better so we'll invert the values
        normalized = {}
        for cat in categories:
            if cat in ['ERA', 'WHIP']:
                normalized[cat] = [league_avgs[cat] / your_stats[cat] if your_stats[cat] > 0 else 1]
            else:
                normalized[cat] = [your_stats[cat] / league_avgs[cat] if league_avgs[cat] > 0 else 1]
        
        # Set up the matplotlib figure
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, polar=True)
        
        # Number of categories
        N = len(categories)
        
        # Angle of each axis
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]  # Close the loop
        
        # Plot your team data
        values = [normalized[cat][0] for cat in categories]
        values += values[:1]  # Close the loop
        
        ax.plot(angles, values, linewidth=2, linestyle='solid', label=self.your_team_name)
        ax.fill(angles, values, alpha=0.25)
        
        # Plot league average as reference (value of 1.0)
        league_values = [1] * N
        league_values += league_values[:1]  # Close the loop
        
        ax.plot(angles, league_values, linewidth=1, linestyle='--', label='League Average')
        
        # Set category labels
        plt.xticks(angles[:-1], categories)
        
        # Add legend
        plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
        
        plt.title(f"{self.your_team_name} Strengths vs. League Average", fontsize=16)
        
        # Save the figure
        plt.tight_layout()
        plt.savefig(output_file)
        plt.close()
        
        print(f"Radar chart visualization saved to {output_file}")
        return output_file
    
    def run_full_analysis(self, teams_file=None, batter_file=None, pitcher_file=None):
        """Run complete analysis pipeline and generate report"""
        print("Starting full fantasy baseball analysis...")
        
        # Load data
        self.load_teams(teams_file)
        self.load_projections(batter_file, pitcher_file)
        
        # Calculate team stats
        self.calculate_team_stats()
        
        # Rank teams
        self.rank_teams()
        
        # Analyze your team
        self.analyze_your_team()
        
        # Generate report
        report_file = self.generate_report()
        
        # Create visualizations
        vis_file1 = self.visualize_team_ranks()
        vis_file2 = self.visualize_team_strengths()
        
        print("Analysis complete!")
        print(f"Report saved to: {report_file}")
        print(f"Visualizations saved to: {vis_file1} and {vis_file2}")
        
        return report_file

# If run directly
if __name__ == "__main__":
    print("Fantasy Baseball League Analyzer v1.0")
    print("-------------------------------------")
    
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description='Fantasy Baseball League Analyzer')
    parser.add_argument('--league_id', type=str, default="2874", help='League ID')
    parser.add_argument('--your_team', type=str, default="Kenny Kawaguchis", help='Your team name')
    parser.add_argument('--teams_file', type=str, help='CSV file with team rosters')
    parser.add_argument('--batter_file', type=str, help='CSV file with batter projections')
    parser.add_argument('--pitcher_file', type=str, help='CSV file with pitcher projections')
    
    args = parser.parse_args()
    
    # Create analyzer and run full analysis
    analyzer = FantasyBaseballAnalyzer(args.league_id, args.your_team)
    analyzer.run_full_analysis(args.teams_file, args.batter_file, args.pitcher_file)
