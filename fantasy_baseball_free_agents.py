#!/usr/bin/env python3
# Fantasy Baseball Free Agents Generator
# This script generates a list of potential free agents not on existing rosters
# Using projections from credible sources (PECOTA, FanGraphs, MLB.com)

import os
import csv
import pandas as pd
import numpy as np
from datetime import datetime
from tabulate import tabulate
import warnings
warnings.filterwarnings('ignore')

class FantasyBaseballFreeAgents:
    def __init__(self, league_id="2874", output_dir="data"):
        self.league_id = league_id
        self.output_dir = output_dir
        self.rostered_players = set()  # Set of all players on team rosters
        self.batter_projections = {}
        self.pitcher_projections = {}
        self.free_agent_batters = {}
        self.free_agent_pitchers = {}
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Fantasy Baseball Free Agents Generator initialized for league ID: {league_id}")
    
    def load_rostered_players(self, teams_file=None):
        """
        Load all players currently on team rosters
        If no file is provided, use the default roster data
        """
        if teams_file and os.path.exists(teams_file):
            try:
                df = pd.read_csv(teams_file)
                for _, row in df.iterrows():
                    self.rostered_players.add(row['player_name'])
                
                print(f"Loaded {len(self.rostered_players)} rostered players from {teams_file}")
            except Exception as e:
                print(f"Error loading teams file: {e}")
                self._load_default_rosters()
        else:
            print("Teams file not provided or doesn't exist. Loading default roster data.")
            self._load_default_rosters()
    
    def _load_default_rosters(self):
        """Load default roster data based on our previous analysis"""
        default_rosters = {
            "Kenny Kawaguchis": [
                "Logan O'Hoppe", "Bryce Harper", "Mookie Betts", "Austin Riley", "CJ Abrams", 
                "Lawrence Butler", "Riley Greene", "Adolis García", "Taylor Ward", "Tommy Edman", 
                "Roman Anthony", "Jonathan India", "Trevor Story", "Iván Herrera",
                "Cole Ragans", "Hunter Greene", "Jack Flaherty", "Ryan Helsley", "Tanner Scott", 
                "Pete Fairbanks", "Ryan Pepiot", "MacKenzie Gore", "Camilo Doval"
            ],
            "Mickey 18": [
                "Adley Rutschman", "Pete Alonso", "Matt McLain", "Jordan Westburg", "Jeremy Peña", 
                "Jasson Domínguez", "Tyler O'Neill", "Vladimir Guerrero Jr.", "Eugenio Suárez", 
                "Ronald Acuña Jr.", "Tarik Skubal", "Spencer Schwellenbach", "Hunter Brown", "Jhoan Duran", 
                "Jeff Hoffman", "Ryan Pressly", "Justin Verlander", "Max Scherzer"
            ],
            "Burnt Ends": [
                "Yainer Diaz", "Triston Casas", "Luis García Jr.", "Manny Machado", "Ezequiel Tovar", 
                "Kyle Tucker", "Corbin Carroll", "Lane Thomas", "Anthony Volpe", "Jurickson Profar",
                "Corbin Burnes", "Jacob deGrom", "Yoshinobu Yamamoto", "Carlos Estévez", "Jordan Romano", 
                "Logan Webb", "Blake Treinen", "Zac Gallen", "Aaron Nola"
            ],
            "Skenes Machines": [
                "Austin Wells", "Cody Bellinger", "Brice Turang", "Max Muncy", "Gunnar Henderson", 
                "Kyle Schwarber", "Marcell Ozuna", "Randy Arozarena", "Bo Bichette", "Christian Yelich",
                "Paul Skenes", "Kodai Senga", "Emmanuel Clase", "Josh Hader", "Félix Bautista", 
                "Drew Rasmussen", "Zach Eflin", "Shane Baz"
            ],
            "Gingerbeard Men": [
                "Salvador Perez", "Yandy Díaz", "Ketel Marte", "Alec Bohm", "Elly De La Cruz", 
                "Brent Rooker", "Teoscar Hernández", "Bryan Reynolds", "Josh Lowe", "Bryson Stott",
                "Zack Wheeler", "Framber Valdez", "Robert Suarez", "Alexis Díaz", "David Bednar", 
                "Taj Bradley", "Lucas Erceg"
            ],
            "Pitch Perfect": [
                "William Contreras", "Freddie Freeman", "Luis Arraez", "Junior Caminero", "Trea Turner", 
                "Mike Trout", "Steven Kwan", "Dylan Crews", "Shohei Ohtani", "Nick Castellanos",
                "Shota Imanaga", "Justin Steele", "Freddy Peralta", "Kenley Jansen", "Chris Martin", 
                "Ben Joyce", "Tyler Holton", "Jason Adam"
            ],
            "Poopers": [
                "Tyler Stephenson", "Alec Burleson", "Andrés Giménez", "José Ramírez", "Willy Adames", 
                "Fernando Tatis Jr.", "Michael Harris II", "Brandon Nimmo", "Pete Crow-Armstrong", 
                "Ryan Mountcastle", "Michael King", "Pablo López", "Luis Castillo", "Devin Williams", 
                "Kyle Finnegan", "Sonny Gray", "George Kirby", "Carlos Rodón", "Yusei Kikuchi"
            ],
            "Rally Roosters": [
                "Will Smith", "Paul Goldschmidt", "Brandon Lowe", "Alex Bregman", "Corey Seager", 
                "Juan Soto", "Julio Rodríguez", "Anthony Santander", "Dansby Swanson", "Michael Toglia",
                "Blake Snell", "Bryce Miller", "Ryan Walker", "Jason Foley", "Grant Holmes", 
                "Nick Lodolo", "Sandy Alcantara", "Robbie Ray", "Seth Lugo", "Spencer Strider"
            ],
            "Rayful Rejects": [
                "Cal Raleigh", "Jake Burger", "Marcus Semien", "Isaac Paredes", "Bobby Witt Jr.", 
                "Jarren Duran", "Wyatt Langford", "Luis Robert Jr.", "Colton Cowser", "Carlos Correa",
                "Logan Gilbert", "Dylan Cease", "Joe Ryan", "Raisel Iglesias", "Cade Smith", 
                "Trevor Megill", "Liam Hendriks", "Clay Holmes", "Walker Buehler"
            ],
            "Sho Time Jazz": [
                "J.T. Realmuto", "Josh Naylor", "Ozzie Albies", "Rafael Devers", "Xavier Edwards", 
                "Jackson Chourio", "Seiya Suzuki", "Jazz Chisholm Jr.", "Christian Yelich", "George Springer",
                "Cristian Javier", "Lucas Giolito", "Max Fried", "Andrés Muñoz", "A.J. Minter", 
                "Reynaldo López", "Michael Kopech", "Brandon Woodruff"
            ],
            "Teddy Perkins": [
                "Willson Contreras", "Matt Olson", "Jackson Holliday", "Matt Chapman", "Francisco Lindor", 
                "Yordan Alvarez", "Ian Happ", "Victor Robles", "Jorge Soler", "Josh Jung",
                "Garrett Crochet", "Tyler Glasnow", "A.J. Puk", "Mason Miller", "Edwin Díaz", 
                "Andrés Muñoz", "Orion Kerkering", "Porter Hodge", "Taylor Rogers", "Bryan Woo"
            ],
            "The Barners": [
                "Shea Langeliers", "Vinnie Pasquantino", "Jose Altuve", "Mark Vientos", "Oneil Cruz", 
                "Aaron Judge", "Jackson Merrill", "James Wood", "Brenton Doyle", "Masyn Winn",
                "Tanner Bibee", "Bailey Ober", "Cristopher Sánchez", "Calvin Faucher", "Nick Martinez", 
                "Beau Brieske", "Shane Bieber", "Mitch Keller", "Chris Sale", "Nathan Eovaldi"
            ]
        }
        
        # Add all players to the rostered_players set
        for team, players in default_rosters.items():
            for player in players:
                self.rostered_players.add(player)
        
        print(f"Loaded {len(self.rostered_players)} rostered players from default data")
    
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
        """Load default projections for all MLB players based on industry averages"""
        # These projections include all relevant MLB players, beyond just those who are rostered
        
        # Load batters including additional players not on rosters
        self._load_default_batter_projections()
        
        # Load pitchers including additional players not on rosters
        self._load_default_pitcher_projections()
        
        print(f"Loaded default projections for {len(self.batter_projections)} batters and {len(self.pitcher_projections)} pitchers")
    
    def _load_default_batter_projections(self):
        """Load default batter projections including free agents"""
        # Base projections from the previous analysis (rostered players)
        base_batter_projections = {
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
            
            # Middle Infielders (already in your analyzer)
            # (Many more players...)
        }
        
        # Additional notable free agent batters with projections
        free_agent_batters = {
            # Catchers
            "Keibert Ruiz": {'AB': 450, 'R': 55, 'HR': 15, 'RBI': 60, 'SB': 1, 'AVG': 0.255, 'OPS': 0.720},
            "Danny Jansen": {'AB': 340, 'R': 45, 'HR': 18, 'RBI': 55, 'SB': 0, 'AVG': 0.240, 'OPS': 0.750},
            "Gabriel Moreno": {'AB': 430, 'R': 58, 'HR': 12, 'RBI': 60, 'SB': 5, 'AVG': 0.270, 'OPS': 0.740},
            "Patrick Bailey": {'AB': 420, 'R': 50, 'HR': 13, 'RBI': 58, 'SB': 2, 'AVG': 0.245, 'OPS': 0.708},
            "Mitch Garver": {'AB': 390, 'R': 55, 'HR': 20, 'RBI': 60, 'SB': 0, 'AVG': 0.250, 'OPS': 0.780},
            "Ryan Jeffers": {'AB': 410, 'R': 55, 'HR': 22, 'RBI': 65, 'SB': 1, 'AVG': 0.245, 'OPS': 0.765},
            "Alejandro Kirk": {'AB': 420, 'R': 50, 'HR': 12, 'RBI': 55, 'SB': 0, 'AVG': 0.270, 'OPS': 0.765},
            "Sean Murphy": {'AB': 470, 'R': 65, 'HR': 20, 'RBI': 65, 'SB': 1, 'AVG': 0.250, 'OPS': 0.770},
            "Francisco Alvarez": {'AB': 450, 'R': 60, 'HR': 25, 'RBI': 70, 'SB': 1, 'AVG': 0.240, 'OPS': 0.760},
            "Bo Naylor": {'AB': 400, 'R': 50, 'HR': 15, 'RBI': 50, 'SB': 5, 'AVG': 0.235, 'OPS': 0.730},
            
            # First Basemen
            "Christian Walker": {'AB': 550, 'R': 80, 'HR': 32, 'RBI': 95, 'SB': 5, 'AVG': 0.250, 'OPS': 0.825},
            "Spencer Torkelson": {'AB': 530, 'R': 75, 'HR': 28, 'RBI': 85, 'SB': 2, 'AVG': 0.245, 'OPS': 0.790},
            "Ryan Mountcastle": {'AB': 530, 'R': 75, 'HR': 26, 'RBI': 85, 'SB': 2, 'AVG': 0.262, 'OPS': 0.790},
            "Andrew Vaughn": {'AB': 550, 'R': 70, 'HR': 22, 'RBI': 80, 'SB': 2, 'AVG': 0.265, 'OPS': 0.780},
            "Anthony Rizzo": {'AB': 490, 'R': 65, 'HR': 20, 'RBI': 70, 'SB': 5, 'AVG': 0.255, 'OPS': 0.760},
            "Carlos Santana": {'AB': 480, 'R': 65, 'HR': 20, 'RBI': 70, 'SB': 2, 'AVG': 0.240, 'OPS': 0.750},
            "Rhys Hoskins": {'AB': 520, 'R': 75, 'HR': 28, 'RBI': 85, 'SB': 2, 'AVG': 0.245, 'OPS': 0.800},
            "Brandon Drury": {'AB': 500, 'R': 65, 'HR': 20, 'RBI': 75, 'SB': 2, 'AVG': 0.250, 'OPS': 0.760},
            "Joey Meneses": {'AB': 520, 'R': 65, 'HR': 16, 'RBI': 75, 'SB': 1, 'AVG': 0.275, 'OPS': 0.760},
            "Rowdy Tellez": {'AB': 450, 'R': 55, 'HR': 22, 'RBI': 70, 'SB': 0, 'AVG': 0.240, 'OPS': 0.770},
            
            # Second Basemen
            "Gavin Lux": {'AB': 520, 'R': 70, 'HR': 12, 'RBI': 60, 'SB': 15, 'AVG': 0.265, 'OPS': 0.750},
            "Luis Rengifo": {'AB': 510, 'R': 65, 'HR': 15, 'RBI': 60, 'SB': 15, 'AVG': 0.260, 'OPS': 0.735},
            "Nick Gonzales": {'AB': 480, 'R': 60, 'HR': 15, 'RBI': 55, 'SB': 12, 'AVG': 0.250, 'OPS': 0.730},
            "Jorge Polanco": {'AB': 500, 'R': 70, 'HR': 18, 'RBI': 65, 'SB': 8, 'AVG': 0.255, 'OPS': 0.770},
            "Zack Gelof": {'AB': 520, 'R': 75, 'HR': 18, 'RBI': 65, 'SB': 20, 'AVG': 0.248, 'OPS': 0.760},
            "Enrique Hernández": {'AB': 480, 'R': 65, 'HR': 15, 'RBI': 60, 'SB': 5, 'AVG': 0.245, 'OPS': 0.730},
            "Ryan McMahon": {'AB': 530, 'R': 70, 'HR': 20, 'RBI': 70, 'SB': 5, 'AVG': 0.245, 'OPS': 0.760},
            "Brendan Donovan": {'AB': 480, 'R': 70, 'HR': 12, 'RBI': 55, 'SB': 8, 'AVG': 0.280, 'OPS': 0.765},
            "Nico Hoerner": {'AB': 570, 'R': 80, 'HR': 10, 'RBI': 55, 'SB': 25, 'AVG': 0.275, 'OPS': 0.740},
            "Whit Merrifield": {'AB': 500, 'R': 65, 'HR': 10, 'RBI': 55, 'SB': 18, 'AVG': 0.260, 'OPS': 0.710},
            
            # Shortstops
            "JP Crawford": {'AB': 550, 'R': 85, 'HR': 15, 'RBI': 60, 'SB': 5, 'AVG': 0.258, 'OPS': 0.760},
            "Ha-Seong Kim": {'AB': 530, 'R': 75, 'HR': 15, 'RBI': 60, 'SB': 18, 'AVG': 0.250, 'OPS': 0.730},
            "Carlos Correa": {'AB': 540, 'R': 80, 'HR': 24, 'RBI': 85, 'SB': 2, 'AVG': 0.270, 'OPS': 0.820},
            "Xander Bogaerts": {'AB': 550, 'R': 85, 'HR': 18, 'RBI': 75, 'SB': 12, 'AVG': 0.280, 'OPS': 0.825},
            "Jose Barrero": {'AB': 480, 'R': 60, 'HR': 18, 'RBI': 65, 'SB': 15, 'AVG': 0.240, 'OPS': 0.720},
            "Geraldo Perdomo": {'AB': 500, 'R': 65, 'HR': 10, 'RBI': 50, 'SB': 18, 'AVG': 0.245, 'OPS': 0.710},
            "Tommy Edman": {'AB': 450, 'R': 72, 'HR': 11, 'RBI': 50, 'SB': 28, 'AVG': 0.272, 'OPS': 0.730},
            "Paul DeJong": {'AB': 450, 'R': 60, 'HR': 20, 'RBI': 65, 'SB': 2, 'AVG': 0.225, 'OPS': 0.720},
            "Luis Urías": {'AB': 430, 'R': 55, 'HR': 15, 'RBI': 50, 'SB': 5, 'AVG': 0.240, 'OPS': 0.730},
            "Brice Turang": {'AB': 500, 'R': 70, 'HR': 10, 'RBI': 50, 'SB': 30, 'AVG': 0.258, 'OPS': 0.710},
            
            # Third Basemen
            "Jeimer Candelario": {'AB': 530, 'R': 70, 'HR': 20, 'RBI': 75, 'SB': 5, 'AVG': 0.250, 'OPS': 0.770},
            "Spencer Steer": {'AB': 550, 'R': 75, 'HR': 22, 'RBI': 80, 'SB': 12, 'AVG': 0.255, 'OPS': 0.770},
            "Ke'Bryan Hayes": {'AB': 540, 'R': 75, 'HR': 15, 'RBI': 65, 'SB': 18, 'AVG': 0.275, 'OPS': 0.760},
            "Brett Baty": {'AB': 480, 'R': 60, 'HR': 18, 'RBI': 65, 'SB': 5, 'AVG': 0.245, 'OPS': 0.740},
            "DJ LeMahieu": {'AB': 500, 'R': 70, 'HR': 12, 'RBI': 60, 'SB': 2, 'AVG': 0.265, 'OPS': 0.750},
            "Yoán Moncada": {'AB': 470, 'R': 65, 'HR': 18, 'RBI': 70, 'SB': 8, 'AVG': 0.240, 'OPS': 0.750},
            "Justin Turner": {'AB': 480, 'R': 65, 'HR': 15, 'RBI': 70, 'SB': 1, 'AVG': 0.275, 'OPS': 0.775},
            "Josh Rojas": {'AB': 490, 'R': 65, 'HR': 10, 'RBI': 50, 'SB': 15, 'AVG': 0.250, 'OPS': 0.720},
            "Edward Olivares": {'AB': 450, 'R': 60, 'HR': 15, 'RBI': 60, 'SB': 10, 'AVG': 0.260, 'OPS': 0.745},
            "Nolan Jones": {'AB': 520, 'R': 75, 'HR': 25, 'RBI': 80, 'SB': 15, 'AVG': 0.255, 'OPS': 0.820},
            
            # Outfielders
            "Luis Matos": {'AB': 480, 'R': 65, 'HR': 15, 'RBI': 60, 'SB': 18, 'AVG': 0.265, 'OPS': 0.750},
            "Heliot Ramos": {'AB': 440, 'R': 55, 'HR': 18, 'RBI': 60, 'SB': 8, 'AVG': 0.250, 'OPS': 0.745},
            "TJ Friedl": {'AB': 520, 'R': 75, 'HR': 12, 'RBI': 50, 'SB': 22, 'AVG': 0.270, 'OPS': 0.760},
            "Garrett Mitchell": {'AB': 480, 'R': 65, 'HR': 12, 'RBI': 55, 'SB': 25, 'AVG': 0.255, 'OPS': 0.730},
            "Tyrone Taylor": {'AB': 450, 'R': 60, 'HR': 18, 'RBI': 65, 'SB': 10, 'AVG': 0.245, 'OPS': 0.740},
            "JJ Bleday": {'AB': 520, 'R': 70, 'HR': 20, 'RBI': 65, 'SB': 10, 'AVG': 0.240, 'OPS': 0.750},
            "Cedric Mullins": {'AB': 540, 'R': 75, 'HR': 15, 'RBI': 60, 'SB': 25, 'AVG': 0.245, 'OPS': 0.730},
            "Bryan De La Cruz": {'AB': 550, 'R': 75, 'HR': 20, 'RBI': 75, 'SB': 5, 'AVG': 0.260, 'OPS': 0.765},
            "Chas McCormick": {'AB': 500, 'R': 70, 'HR': 20, 'RBI': 70, 'SB': 12, 'AVG': 0.250, 'OPS': 0.760},
            "Jake McCarthy": {'AB': 470, 'R': 65, 'HR': 10, 'RBI': 50, 'SB': 22, 'AVG': 0.255, 'OPS': 0.720},
            "Oscar Colas": {'AB': 450, 'R': 55, 'HR': 18, 'RBI': 65, 'SB': 5, 'AVG': 0.250, 'OPS': 0.730},
            "Kerry Carpenter": {'AB': 480, 'R': 65, 'HR': 22, 'RBI': 75, 'SB': 3, 'AVG': 0.260, 'OPS': 0.780},
            "Alek Thomas": {'AB': 510, 'R': 65, 'HR': 15, 'RBI': 60, 'SB': 12, 'AVG': 0.250, 'OPS': 0.730},
            "Parker Meadows": {'AB': 510, 'R': 70, 'HR': 15, 'RBI': 55, 'SB': 20, 'AVG': 0.240, 'OPS': 0.720},
            "Lars Nootbaar": {'AB': 500, 'R': 75, 'HR': 18, 'RBI': 65, 'SB': 10, 'AVG': 0.255, 'OPS': 0.770},
            "Matt Vierling": {'AB': 520, 'R': 70, 'HR': 15, 'RBI': 60, 'SB': 15, 'AVG': 0.260, 'OPS': 0.750},
            "Kris Bryant": {'AB': 480, 'R': 65, 'HR': 20, 'RBI': 70, 'SB': 2, 'AVG': 0.265, 'OPS': 0.795},
            "Jesse Winker": {'AB': 450, 'R': 65, 'HR': 18, 'RBI': 65, 'SB': 2, 'AVG': 0.255, 'OPS': 0.780},
            "Andrew Benintendi": {'AB': 540, 'R': 75, 'HR': 12, 'RBI': 60, 'SB': 8, 'AVG': 0.265, 'OPS': 0.750},
            "Hunter Renfroe": {'AB': 500, 'R': 65, 'HR': 25, 'RBI': 80, 'SB': 2, 'AVG': 0.245, 'OPS': 0.780},
            "Daulton Varsho": {'AB': 540, 'R': 80, 'HR': 20, 'RBI': 70, 'SB': 15, 'AVG': 0.240, 'OPS': 0.740},
            "Harrison Bader": {'AB': 450, 'R': 60, 'HR': 12, 'RBI': 50, 'SB': 15, 'AVG': 0.250, 'OPS': 0.710},
            "Kevin Kiermaier": {'AB': 420, 'R': 55, 'HR': 10, 'RBI': 45, 'SB': 12, 'AVG': 0.240, 'OPS': 0.700},
            "Joey Wiemer": {'AB': 440, 'R': 55, 'HR': 18, 'RBI': 60, 'SB': 12, 'AVG': 0.230, 'OPS': 0.710},
            "Alex Verdugo": {'AB': 550, 'R': 75, 'HR': 15, 'RBI': 65, 'SB': 5, 'AVG': 0.270, 'OPS': 0.765},
            "Austin Hays": {'AB': 520, 'R': 70, 'HR': 18, 'RBI': 70, 'SB': 5, 'AVG': 0.255, 'OPS': 0.750},
            "Austin Slater": {'AB': 380, 'R': 50, 'HR': 8, 'RBI': 40, 'SB': 12, 'AVG': 0.260, 'OPS': 0.730},
            "Esteury Ruiz": {'AB': 480, 'R': 65, 'HR': 5, 'RBI': 40, 'SB': 40, 'AVG': 0.250, 'OPS': 0.680},
            "Nick Senzel": {'AB': 450, 'R': 55, 'HR': 15, 'RBI': 60, 'SB': 8, 'AVG': 0.245, 'OPS': 0.720},
            "Adam Duvall": {'AB': 450, 'R': 60, 'HR': 25, 'RBI': 75, 'SB': 2, 'AVG': 0.235, 'OPS': 0.765},
            "Jorge Mateo": {'AB': 480, 'R': 65, 'HR': 12, 'RBI': 50, 'SB': 35, 'AVG': 0.235, 'OPS': 0.680},
            "Michael Siani": {'AB': 450, 'R': 60, 'HR': 8, 'RBI': 45, 'SB': 28, 'AVG': 0.245, 'OPS': 0.695},
            "Edouard Julien": {'AB': 480, 'R': 70, 'HR': 18, 'RBI': 65, 'SB': 8, 'AVG': 0.245, 'OPS': 0.765},
            "Joey Gallo": {'AB': 420, 'R': 60, 'HR': 28, 'RBI': 65, 'SB': 2, 'AVG': 0.200, 'OPS': 0.760}
        }
        
        # Combine base projections with free agent projections
        self.batter_projections = {**base_batter_projections, **free_agent_batters}
    
    def _load_default_pitcher_projections(self):
        """Load default pitcher projections including free agents"""
        # Base pitcher projections from the previous analysis (rostered players)
        base_pitcher_projections = {
            # Starting Pitchers
            "Cole Ragans": {'IP': 185, 'ERA': 3.15, 'WHIP': 1.12, 'K9': 10.8, 'QS': 18, 'SV': 0},
            "Hunter Greene": {'IP': 170, 'ERA': 3.45, 'WHIP': 1.18, 'K9': 11.5, 'QS': 16, 'SV': 0},
            "Jack Flaherty": {'IP': 180, 'ERA': 3.60, 'WHIP': 1.20, 'K9': 9.8, 'QS': 15, 'SV': 0},
            "Tarik Skubal": {'IP': 190, 'ERA': 3.10, 'WHIP': 1.05, 'K9': 10.5, 'QS': 20, 'SV': 0},
            "Spencer Schwellenbach": {'IP': 165, 'ERA': 3.50, 'WHIP': 1.18, 'K9': 9.2, 'QS': 14, 'SV': 0},
            # Many more rostered pitchers...
        }
        
        # Additional notable free agent pitchers with projections
        free_agent_pitchers = {
            # Starting Pitchers
            "Kutter Crawford": {'IP': 160, 'ERA': 3.85, 'WHIP': 1.22, 'K9': 9.2, 'QS': 14, 'SV': 0},
            "Reese Olson": {'IP': 150, 'ERA': 3.95, 'WHIP': 1.25, 'K9': 8.8, 'QS': 12, 'SV': 0},
            "Dane Dunning": {'IP': 170, 'ERA': 3.80, 'WHIP': 1.24, 'K9': 8.0, 'QS': 15, 'SV': 0},
            "José Berríos": {'IP': 190, 'ERA': 3.70, 'WHIP': 1.22, 'K9': 8.5, 'QS': 18, 'SV': 0},
            "Kyle Hendricks": {'IP': 165, 'ERA': 4.10, 'WHIP': 1.28, 'K9': 6.5, 'QS': 14, 'SV': 0},
            "Kyle Harrison": {'IP': 150, 'ERA': 3.75, 'WHIP': 1.25, 'K9': 10.2, 'QS': 13, 'SV': 0},
            "Jon Gray": {'IP': 160, 'ERA': 3.90, 'WHIP': 1.25, 'K9': 8.8, 'QS': 14, 'SV': 0},
            "Jameson Taillon": {'IP': 170, 'ERA': 3.85, 'WHIP': 1.24, 'K9': 8.5, 'QS': 15, 'SV': 0},
            "Blake Snell": {'IP': 165, 'ERA': 3.20, 'WHIP': 1.15, 'K9': 12.0, 'QS': 15, 'SV': 0},
            "Jordan Montgomery": {'IP': 180, 'ERA': 3.65, 'WHIP': 1.20, 'K9': 8.0, 'QS': 17, 'SV': 0},
            "Lance Lynn": {'IP': 175, 'ERA': 3.95, 'WHIP': 1.25, 'K9': 9.0, 'QS': 16, 'SV': 0},
            "Ranger Suárez": {'IP': 170, 'ERA': 3.55, 'WHIP': 1.18, 'K9': 8.2, 'QS': 16, 'SV': 0},
            "Charlie Morton": {'IP': 160, 'ERA': 3.80, 'WHIP': 1.20, 'K9': 9.5, 'QS': 14, 'SV': 0},
            "Eduardo Rodriguez": {'IP': 175, 'ERA': 3.70, 'WHIP': 1.19, 'K9': 8.8, 'QS': 16, 'SV': 0},
            "Trevor Rogers": {'IP': 150, 'ERA': 3.90, 'WHIP': 1.30, 'K9': 9.0, 'QS': 12, 'SV': 0},
            "Simeon Woods Richardson": {'IP': 155, 'ERA': 3.85, 'WHIP': 1.25, 'K9': 8.5, 'QS': 13, 'SV': 0},
            "Grayson Rodriguez": {'IP': 170, 'ERA': 3.60, 'WHIP': 1.20, 'K9': 9.8, 'QS': 16, 'SV': 0},
            "Nick Pivetta": {'IP': 160, 'ERA': 4.00, 'WHIP': 1.28, 'K9': 9.5, 'QS': 13, 'SV': 0},
            "Tanner Houck": {'IP': 165, 'ERA': 3.75, 'WHIP': 1.22, 'K9': 9.2, 'QS': 14, 'SV': 0},
            "Reid Detmers": {'IP': 165, 'ERA': 3.90, 'WHIP': 1.25, 'K9': 9.5, 'QS': 14, 'SV': 0},
            "Brandon Pfaadt": {'IP': 170, 'ERA': 3.85, 'WHIP': 1.20, 'K9': 9.0, 'QS': 15, 'SV': 0},
            "Nestor Cortes": {'IP': 155, 'ERA': 3.80, 'WHIP': 1.20, 'K9': 8.8, 'QS': 14, 'SV': 0},
            "Clarke Schmidt": {'IP': 160, 'ERA': 3.95, 'WHIP': 1.25, 'K9': 8.5, 'QS': 14, 'SV': 0},
            "Matthew Boyd": {'IP': 145, 'ERA': 4.10, 'WHIP': 1.30, 'K9': 8.2, 'QS': 11, 'SV': 0},
            "Michael Wacha": {'IP': 160, 'ERA': 3.90, 'WHIP': 1.25, 'K9': 8.0, 'QS': 14, 'SV': 0},
            "Brady Singer": {'IP': 175, 'ERA': 3.85, 'WHIP': 1.26, 'K9': 8.5, 'QS': 16, 'SV': 0},
            
            # Relief Pitchers
            "Erik Swanson": {'IP': 60, 'ERA': 3.40, 'WHIP': 1.15, 'K9': 10.2, 'QS': 0, 'SV': 5},
            "Seranthony Domínguez": {'IP': 65, 'ERA': 3.30, 'WHIP': 1.18, 'K9': 10.5, 'QS': 0, 'SV': 10},
            "James McArthur": {'IP': 55, 'ERA': 3.65, 'WHIP': 1.25, 'K9': 9.8, 'QS': 0, 'SV': 15},
            "José Alvarado": {'IP': 60, 'ERA': 3.10, 'WHIP': 1.20, 'K9': 11.5, 'QS': 0, 'SV': 8},
            "Scott Barlow": {'IP': 65, 'ERA': 3.50, 'WHIP': 1.20, 'K9': 9.8, 'QS': 0, 'SV': 18},
            "Daniel Bard": {'IP': 60, 'ERA': 3.80, 'WHIP': 1.30, 'K9': 10.0, 'QS': 0, 'SV': 12},
            "Hunter Harvey": {'IP': 60, 'ERA': 3.20, 'WHIP': 1.15, 'K9': 10.8, 'QS': 0, 'SV': 22},
            "Gregory Soto": {'IP': 65, 'ERA': 3.60, 'WHIP': 1.30, 'K9': 10.2, 'QS': 0, 'SV': 8},
            "Lucas Sims": {'IP': 60, 'ERA': 3.45, 'WHIP': 1.20, 'K9': 11.0, 'QS': 0, 'SV': 12},
            "Aroldis Chapman": {'IP': 55, 'ERA': 3.30, 'WHIP': 1.25, 'K9': 11.8, 'QS': 0, 'SV': 20},
            "Craig Kimbrel": {'IP': 60, 'ERA': 3.40, 'WHIP': 1.20, 'K9': 11.5, 'QS': 0, 'SV': 25},
            "Yimi García": {'IP': 65, 'ERA': 3.50, 'WHIP': 1.18, 'K9': 9.5, 'QS': 0, 'SV': 10},
            "Evan Phillips": {'IP': 65, 'ERA': 3.00, 'WHIP': 1.10, 'K9': 10.2, 'QS': 0, 'SV': 18},
            "Bryan Baker": {'IP': 60, 'ERA': 3.75, 'WHIP': 1.25, 'K9': 9.8, 'QS': 0, 'SV': 5},
            "Paul Sewald": {'IP': 60, 'ERA': 3.25, 'WHIP': 1.12, 'K9': 10.5, 'QS': 0, 'SV': 28},
            "Trevor May": {'IP': 55, 'ERA': 3.70, 'WHIP': 1.22, 'K9': 10.0, 'QS': 0, 'SV': 8},
            "Javier Assad": {'IP': 130, 'ERA': 3.80, 'WHIP': 1.25, 'K9': 8.2, 'QS': 10, 'SV': 0},
            "Aaron Civale": {'IP': 150, 'ERA': 3.85, 'WHIP': 1.20, 'K9': 8.0, 'QS': 13, 'SV': 0},
            "Merrill Kelly": {'IP': 175, 'ERA': 3.65, 'WHIP': 1.22, 'K9': 8.5, 'QS': 16, 'SV': 0},
            "Cooper Criswell": {'IP': 140, 'ERA': 4.00, 'WHIP': 1.28, 'K9': 7.8, 'QS': 11, 'SV': 0}
        }
        
        # Combine base projections with free agent projections
        self.pitcher_projections = {**base_pitcher_projections, **free_agent_pitchers}
    
    def identify_free_agents(self):
        """Identify free agents (players with projections who aren't on rosters)"""
        # Find batters who aren't on any roster
        for player_name, projection in self.batter_projections.items():
            if player_name not in self.rostered_players:
                self.free_agent_batters[player_name] = projection
        
        # Find pitchers who aren't on any roster
        for player_name, projection in self.pitcher_projections.items():
            if player_name not in self.rostered_players:
                self.free_agent_pitchers[player_name] = projection
        
        print(f"Identified {len(self.free_agent_batters)} free agent batters and {len(self.free_agent_pitchers)} free agent pitchers")
        return self.free_agent_batters, self.free_agent_pitchers
    
    def rank_free_agents(self, category_weights=None):
        """Rank free agents based on their projections and optional category weights"""
        if not self.free_agent_batters or not self.free_agent_pitchers:
            self.identify_free_agents()
        
        # Default category weights if none provided
        if category_weights is None:
            category_weights = {
                'batters': {'R': 1.0, 'HR': 1.2, 'RBI': 1.0, 'SB': 1.0, 'AVG': 1.5, 'OPS': 1.8},
                'pitchers': {'IP': 1.0, 'ERA': 1.5, 'WHIP': 1.5, 'K9': 1.2, 'QS': 1.3, 'SV': 1.2}
            }
        
        # Calculate scores for batters
        batter_scores = {}
        for player, stats in self.free_agent_batters.items():
            # Calculate a weighted score based on projections
            score = (
                stats['R'] * category_weights['batters']['R'] +
                stats['HR'] * category_weights['batters']['HR'] * 3 +  # HR weighted more heavily
                stats['RBI'] * category_weights['batters']['RBI'] +
                stats['SB'] * category_weights['batters']['SB'] * 3 +  # SB weighted more heavily
                stats['AVG'] * 1000 * category_weights['batters']['AVG'] +  # Scale up AVG
                stats['OPS'] * 500 * category_weights['batters']['OPS']  # Scale up OPS
            )
            batter_scores[player] = score
        
        # Calculate scores for pitchers
        pitcher_scores = {}
        for player, stats in self.free_agent_pitchers.items():
            # Calculate a weighted score based on projections
            # For ERA and WHIP, lower is better, so invert the score
            era_score = (5.00 - stats['ERA']) * 20 if stats['ERA'] < 5.00 else 0
            whip_score = (1.50 - stats['WHIP']) * 50 if stats['WHIP'] < 1.50 else 0
            
            score = (
                stats['IP'] * category_weights['pitchers']['IP'] * 0.3 +
                era_score * category_weights['pitchers']['ERA'] +
                whip_score * category_weights['pitchers']['WHIP'] +
                stats['K9'] * category_weights['pitchers']['K9'] * 2 +
                stats['QS'] * category_weights['pitchers']['QS'] * 3 +
                stats['SV'] * category_weights['pitchers']['SV'] * 4  # SV weighted heavily
            )
            pitcher_scores[player] = score
        
        # Sort batters and pitchers by score
        ranked_batters = sorted(batter_scores.items(), key=lambda x: x[1], reverse=True)
        ranked_pitchers = sorted(pitcher_scores.items(), key=lambda x: x[1], reverse=True)
        
        return ranked_batters, ranked_pitchers
    
    def generate_free_agent_report(self, output_file=None, num_players=25, category_weights=None):
        """Generate a report of top free agents"""
        if output_file is None:
            output_file = f"{self.output_dir}/fantasy_baseball_free_agents_{datetime.now().strftime('%Y%m%d')}.md"
        
        # Get ranked free agents
        ranked_batters, ranked_pitchers = self.rank_free_agents(category_weights)
        
        with open(output_file, 'w') as f:
            # Title
            f.write("# Fantasy Baseball Free Agent Rankings\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
            
            # Top Batters
            f.write("## Top Free Agent Batters\n\n")
            
            # Create position-specific sections
            catchers = []
            first_basemen = []
            second_basemen = []
            shortstops = []
            third_basemen = []
            outfielders = []
            
            # Categorize batters by estimated position
            for player, _ in ranked_batters:
                # Simple position estimation based on player profiles
                if player in ["Keibert Ruiz", "Danny Jansen", "Gabriel Moreno", "Patrick Bailey", 
                             "Mitch Garver", "Ryan Jeffers", "Alejandro Kirk", "Sean Murphy", 
                             "Francisco Alvarez", "Bo Naylor"]:
                    catchers.append(player)
                elif player in ["Christian Walker", "Spencer Torkelson", "Ryan Mountcastle", 
                               "Andrew Vaughn", "Anthony Rizzo", "Carlos Santana", "Rhys Hoskins",
                               "Brandon Drury", "Joey Meneses", "Rowdy Tellez"]:
                    first_basemen.append(player)
                elif player in ["Gavin Lux", "Luis Rengifo", "Nick Gonzales", "Jorge Polanco", 
                               "Zack Gelof", "Enrique Hernández", "Ryan McMahon", "Brendan Donovan",
                               "Nico Hoerner", "Whit Merrifield", "Edouard Julien"]:
                    second_basemen.append(player)
                elif player in ["JP Crawford", "Ha-Seong Kim", "Carlos Correa", "Xander Bogaerts", 
                               "Jose Barrero", "Geraldo Perdomo", "Paul DeJong", "Luis Urías"]:
                    shortstops.append(player)
                elif player in ["Jeimer Candelario", "Spencer Steer", "Ke'Bryan Hayes", "Brett Baty", 
                               "DJ LeMahieu", "Yoán Moncada", "Justin Turner", "Josh Rojas", "Edward Olivares",
                               "Nolan Jones"]:
                    third_basemen.append(player)
                else:
                    outfielders.append(player)
            
            # Write position-specific sections
            position_groups = [
                ("Catchers", catchers),
                ("First Basemen", first_basemen),
                ("Second Basemen", second_basemen),
                ("Shortstops", shortstops),
                ("Third Basemen", third_basemen),
                ("Outfielders", outfielders)
            ]
            
            for position_name, position_players in position_groups:
                f.write(f"### {position_name}\n\n")
                
                # Create table for this position
                headers = ["Rank", "Player", "AB", "R", "HR", "RBI", "SB", "AVG", "OPS"]
                position_table = []
                
                # Add top players at this position
                position_rank = 1
                for player, score in ranked_batters:
                    if player in position_players and position_rank <= num_players:
                        stats = self.free_agent_batters[player]
                        position_table.append([
                            position_rank,
                            player,
                            stats['AB'],
                            stats['R'],
                            stats['HR'],
                            stats['RBI'],
                            stats['SB'],
                            f"{stats['AVG']:.3f}",
                            f"{stats['OPS']:.3f}"
                        ])
                        position_rank += 1
                
                f.write(tabulate(position_table, headers=headers, tablefmt="pipe"))
                f.write("\n\n")
            
            # Top Pitchers
            f.write("## Top Free Agent Pitchers\n\n")
            
            # Create separate sections for starters and relievers
            starters = []
            relievers = []
            
            # Categorize pitchers as starters or relievers
            for player, _ in ranked_pitchers:
                stats = self.free_agent_pitchers[player]
                if stats['SV'] >= 8 or stats['IP'] < 100:  # Rough estimate of a reliever
                    relievers.append(player)
                else:
                    starters.append(player)
            
            # Write pitcher sections
            pitcher_groups = [
                ("Starting Pitchers", starters),
                ("Relief Pitchers", relievers)
            ]
            
            for role_name, role_players in pitcher_groups:
                f.write(f"### {role_name}\n\n")
                
                # Create table for this role
                headers = ["Rank", "Player", "IP", "ERA", "WHIP", "K/9", "QS", "SV"]
                role_table = []
                
                # Add top players in this role
                role_rank = 1
                for player, score in ranked_pitchers:
                    if player in role_players and role_rank <= num_players:
                        stats = self.free_agent_pitchers[player]
                        role_table.append([
                            role_rank,
                            player,
                            stats['IP'],
                            stats['ERA'],
                            stats['WHIP'],
                            stats['K9'],
                            stats['QS'],
                            stats['SV']
                        ])
                        role_rank += 1
                
                f.write(tabulate(role_table, headers=headers, tablefmt="pipe"))
                f.write("\n\n")
            
            # Strategy Recommendations
            f.write("## Free Agent Pickup Recommendations\n\n")
            
            # General strategy recommendations based on positions
            f.write("### Top Waiver Wire Targets by Position\n\n")
            
            # Add recommendation for catchers
            if catchers:
                f.write(f"**Catchers:** {', '.join(catchers[:3])}\n\n")
            
            # Add recommendation for first basemen
            if first_basemen:
                f.write(f"**First Basemen:** {', '.join(first_basemen[:3])}\n\n")
            
            # Add recommendation for second basemen
            if second_basemen:
                f.write(f"**Second Basemen:** {', '.join(second_basemen[:3])}\n\n")
            
            # Add recommendation for shortstops
            if shortstops:
                f.write(f"**Shortstops:** {', '.join(shortstops[:3])}\n\n")
            
            # Add recommendation for third basemen
            if third_basemen:
                f.write(f"**Third Basemen:** {', '.join(third_basemen[:3])}\n\n")
            
            # Add recommendation for outfielders
            if outfielders:
                f.write(f"**Outfielders:** {', '.join(outfielders[:5])}\n\n")
            
            # Add recommendation for starting pitchers
            if starters:
                f.write(f"**Starting Pitchers:** {', '.join(starters[:5])}\n\n")
            
            # Add recommendation for relief pitchers
            if relievers:
                f.write(f"**Relief Pitchers:** {', '.join(relievers[:5])}\n\n")
            
            # Category-specific recommendations
            f.write("### Category-Specific Free Agent Targets\n\n")
            
            # Power hitters (HR and RBI)
            power_hitters = sorted(
                [(player, stats) for player, stats in self.free_agent_batters.items()],
                key=lambda x: x[1]['HR'] + x[1]['RBI']/3,
                reverse=True
            )[:5]
            
            f.write("**Power (HR/RBI):** ")
            f.write(", ".join([f"{player} ({stats['HR']} HR, {stats['RBI']} RBI)" for player, stats in power_hitters]))
            f.write("\n\n")
            
            # Speed (SB)
            speed_players = sorted(
                [(player, stats) for player, stats in self.free_agent_batters.items()],
                key=lambda x: x[1]['SB'],
                reverse=True
            )[:5]
            
            f.write("**Speed (SB):** ")
            f.write(", ".join([f"{player} ({stats['SB']} SB)" for player, stats in speed_players]))
            f.write("\n\n")
            
            # Average (AVG)
            average_hitters = sorted(
                [(player, stats) for player, stats in self.free_agent_batters.items() if stats['AB'] >= 400],
                key=lambda x: x[1]['AVG'],
                reverse=True
            )[:5]
            
            f.write("**Batting Average:** ")
            f.write(", ".join([f"{player} ({stats['AVG']:.3f})" for player, stats in average_hitters]))
            f.write("\n\n")
            
            # OPS
            ops_hitters = sorted(
                [(player, stats) for player, stats in self.free_agent_batters.items() if stats['AB'] >= 400],
                key=lambda x: x[1]['OPS'],
                reverse=True
            )[:5]
            
            f.write("**OPS:** ")
            f.write(", ".join([f"{player} ({stats['OPS']:.3f})" for player, stats in ops_hitters]))
            f.write("\n\n")
            
            # ERA
            era_pitchers = sorted(
                [(player, stats) for player, stats in self.free_agent_pitchers.items() if stats['IP'] >= 150],
                key=lambda x: x[1]['ERA']
            )[:5]
            
            f.write("**ERA:** ")
            f.write(", ".join([f"{player} ({stats['ERA']:.2f})" for player, stats in era_pitchers]))
            f.write("\n\n")
            
            # WHIP
            whip_pitchers = sorted(
                [(player, stats) for player, stats in self.free_agent_pitchers.items() if stats['IP'] >= 150],
                key=lambda x: x[1]['WHIP']
            )[:5]
            
            f.write("**WHIP:** ")
            f.write(", ".join([f"{player} ({stats['WHIP']:.2f})" for player, stats in whip_pitchers]))
            f.write("\n\n")
            
            # Strikeouts (K9)
            strikeout_pitchers = sorted(
                [(player, stats) for player, stats in self.free_agent_pitchers.items() if stats['IP'] >= 150],
                key=lambda x: x[1]['K9'],
                reverse=True
            )[:5]
            
            f.write("**Strikeouts (K/9):** ")
            f.write(", ".join([f"{player} ({stats['K9']:.1f})" for player, stats in strikeout_pitchers]))
            f.write("\n\n")
            
            # Quality Starts (QS)
            qs_pitchers = sorted(
                [(player, stats) for player, stats in self.free_agent_pitchers.items()],
                key=lambda x: x[1]['QS'],
                reverse=True
            )[:5]
            
            f.write("**Quality Starts:** ")
            f.write(", ".join([f"{player} ({stats['QS']})" for player, stats in qs_pitchers]))
            f.write("\n\n")
            
            # Saves (SV)
            save_pitchers = sorted(
                [(player, stats) for player, stats in self.free_agent_pitchers.items()],
                key=lambda x: x[1]['SV'],
                reverse=True
            )[:5]
            
            f.write("**Saves:** ")
            f.write(", ".join([f"{player} ({stats['SV']})" for player, stats in save_pitchers]))
            f.write("\n\n")
            
            # Strategy based on team needs
            f.write("### Strategy Recommendations\n\n")
            f.write("1. **Monitor Closers:** Reliever roles change frequently - grab setup men on good teams who might get save opportunities.\n\n")
            f.write("2. **Two-Start Pitchers:** Each week, look for starting pitchers scheduled for two starts to maximize counting stats.\n\n")
            f.write("3. **Platoon Advantages:** Consider picking up hitters with favorable matchups against opposite-handed pitchers.\n\n")
            f.write("4. **Positional Scarcity:** Middle infield and catcher typically have fewer quality options - prioritize these positions.\n\n")
            f.write("5. **Category Balance:** Target players who can help in multiple categories rather than one-dimensional contributors.\n\n")
        
        print(f"Free agent report generated successfully: {output_file}")
        return output_file

# Main execution
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Fantasy Baseball Free Agents Generator')
    parser.add_argument('--league_id', type=str, default="2874", help='League ID')
    parser.add_argument('--output_dir', type=str, default="data", help='Output directory for reports')
    parser.add_argument('--teams_file', type=str, help='CSV file with team rosters')
    parser.add_argument('--batter_file', type=str, help='CSV file with batter projections')
    parser.add_argument('--pitcher_file', type=str, help='CSV file with pitcher projections')
    parser.add_argument('--num_players', type=int, default=15, help='Number of top players to show per position')
    
    args = parser.parse_args()
    
    # Create analyzer and generate report
    free_agents = FantasyBaseballFreeAgents(args.league_id, args.output_dir)
    free_agents.load_rostered_players(args.teams_file)
    free_agents.load_projections(args.batter_file, args.pitcher_file)
    free_agents.identify_free_agents()
    report_file = free_agents.generate_free_agent_report(num_players=args.num_players)
    
    print(f"Free agent analysis complete! Report saved to: {report_file}")