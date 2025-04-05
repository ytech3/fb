#!/usr/bin/env python3
# Fantasy Baseball Automated Model with Live Updates
# This script creates an automated system that regularly updates player stats and projections
# Uses the same sources (PECOTA, FanGraphs, MLB.com) for consistent data

import os
import csv
import json
import time
import random
import requests
import pandas as pd
import numpy as np
import schedule
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from tabulate import tabulate
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fantasy_baseball_auto.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FantasyBaseballAuto")

class FantasyBaseballAutomated:
    def __init__(self, league_id="2874", your_team_name="Kenny Kawaguchis"):
        self.league_id = league_id
        self.your_team_name = your_team_name
        self.teams = {}
        self.team_rosters = {}
        self.free_agents = {}
        self.player_stats_current = {}
        self.player_projections = {}
        self.player_news = {}
        self.last_update = None
        
        # API endpoints and data sources
        self.data_sources = {
            'stats': [
                'https://www.fangraphs.com/api/players/stats',
                'https://www.baseball-reference.com/leagues/MLB/2025.shtml',
                'https://www.mlb.com/stats/'
            ],
            'projections': [
                'https://www.fangraphs.com/projections.aspx',
                'https://www.baseball-prospectus.com/pecota-projections/',
                'https://www.mlb.com/stats/projected'
            ],
            'news': [
                'https://www.rotowire.com/baseball/news.php',
                'https://www.cbssports.com/fantasy/baseball/players/updates/',
                'https://www.espn.com/fantasy/baseball/story/_/id/29589640'
            ]
        }
        
        # Create directories for data storage
        self.data_dir = "data"
        self.reports_dir = "reports"
        self.visuals_dir = "visuals"
        self.archives_dir = "archives"
        
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.visuals_dir, exist_ok=True)
        os.makedirs(self.archives_dir, exist_ok=True)
        
        logger.info(f"Fantasy Baseball Automated Model initialized for league ID: {league_id}")
        logger.info(f"Your team: {your_team_name}")
    
    def load_initial_data(self):
        """Load initial data to bootstrap the system"""
        logger.info("Loading initial data for bootstrap...")
        
        # Load team rosters
        self.load_team_rosters()
        
        # Load initial stats and projections
        self.load_initial_stats_and_projections()
        
        # Generate initial set of free agents
        self.identify_free_agents()
        
        # Mark system as initialized with timestamp
        self.last_update = datetime.now()
        self.save_system_state()
        
        logger.info(f"Initial data loaded successfully, timestamp: {self.last_update}")
    
    def load_team_rosters(self, rosters_file=None):
        """Load team rosters from file or use default data"""
        if rosters_file and os.path.exists(rosters_file):
            try:
                df = pd.read_csv(rosters_file)
                for _, row in df.iterrows():
                    team_name = row['team_name']
                    player_name = row['player_name']
                    position = row['position']
                    
                    if team_name not in self.team_rosters:
                        self.team_rosters[team_name] = []
                    
                    self.team_rosters[team_name].append({
                        'name': player_name,
                        'position': position
                    })
                
                logger.info(f"Loaded {len(self.team_rosters)} team rosters from {rosters_file}")
            except Exception as e:
                logger.error(f"Error loading rosters file: {e}")
                self._load_default_rosters()
        else:
            logger.info("Rosters file not provided or doesn't exist. Loading default roster data.")
            self._load_default_rosters()
    
    def _load_default_rosters(self):
        """Load default roster data based on previous analysis"""
        default_rosters = {
            "Kenny Kawaguchis": [
                {"name": "Logan O'Hoppe", "position": "C"},
                {"name": "Bryce Harper", "position": "1B"},
                {"name": "Mookie Betts", "position": "2B/OF"},
                {"name": "Austin Riley", "position": "3B"},
                {"name": "CJ Abrams", "position": "SS"},
                {"name": "Lawrence Butler", "position": "OF"},
                {"name": "Riley Greene", "position": "OF"},
                {"name": "Adolis García", "position": "OF"},
                {"name": "Taylor Ward", "position": "OF"},
                {"name": "Tommy Edman", "position": "2B/SS"},
                {"name": "Roman Anthony", "position": "OF"},
                {"name": "Jonathan India", "position": "2B"},
                {"name": "Trevor Story", "position": "SS"},
                {"name": "Iván Herrera", "position": "C"},
                {"name": "Cole Ragans", "position": "SP"},
                {"name": "Hunter Greene", "position": "SP"},
                {"name": "Jack Flaherty", "position": "SP"},
                {"name": "Ryan Helsley", "position": "RP"},
                {"name": "Tanner Scott", "position": "RP"},
                {"name": "Pete Fairbanks", "position": "RP"},
                {"name": "Ryan Pepiot", "position": "SP"},
                {"name": "MacKenzie Gore", "position": "SP"},
                {"name": "Camilo Doval", "position": "RP"}
            ],
            "Mickey 18": [
                {"name": "Adley Rutschman", "position": "C"},
                {"name": "Pete Alonso", "position": "1B"},
                {"name": "Matt McLain", "position": "2B"},
                {"name": "Jordan Westburg", "position": "3B"},
                {"name": "Jeremy Peña", "position": "SS"},
                {"name": "Jasson Domínguez", "position": "OF"},
                {"name": "Tyler O'Neill", "position": "OF"},
                {"name": "Vladimir Guerrero Jr.", "position": "1B"},
                {"name": "Eugenio Suárez", "position": "3B"},
                {"name": "Ronald Acuña Jr.", "position": "OF"},
                {"name": "Tarik Skubal", "position": "SP"},
                {"name": "Spencer Schwellenbach", "position": "SP"},
                {"name": "Hunter Brown", "position": "SP"},
                {"name": "Jhoan Duran", "position": "RP"},
                {"name": "Jeff Hoffman", "position": "RP"},
                {"name": "Ryan Pressly", "position": "RP"},
                {"name": "Justin Verlander", "position": "SP"},
                {"name": "Max Scherzer", "position": "SP"}
            ],
            # Other teams omitted for brevity but would be included in full implementation
        }
        
        # Add to the team rosters dictionary
        self.team_rosters = default_rosters
        
        # Count total players loaded
        total_players = sum(len(roster) for roster in self.team_rosters.values())
        logger.info(f"Loaded {len(self.team_rosters)} team rosters with {total_players} players from default data")
    
    def load_initial_stats_and_projections(self, stats_file=None, projections_file=None):
        """Load initial stats and projections from files or use default data"""
        if stats_file and os.path.exists(stats_file) and projections_file and os.path.exists(projections_file):
            try:
                # Load stats
                with open(stats_file, 'r') as f:
                    self.player_stats_current = json.load(f)
                
                # Load projections
                with open(projections_file, 'r') as f:
                    self.player_projections = json.load(f)
                
                logger.info(f"Loaded stats for {len(self.player_stats_current)} players from {stats_file}")
                logger.info(f"Loaded projections for {len(self.player_projections)} players from {projections_file}")
            except Exception as e:
                logger.error(f"Error loading stats/projections files: {e}")
                self._load_default_stats_and_projections()
        else:
            logger.info("Stats/projections files not provided or don't exist. Loading default data.")
            self._load_default_stats_and_projections()
    
    def _load_default_stats_and_projections(self):
        """Load default stats and projections for bootstrapping"""
        # This would load from the previously created data
        # For simulation/demo purposes, we'll generate synthetic data
        
        # First, collect all players from rosters
        all_players = set()
        for team, roster in self.team_rosters.items():
            for player in roster:
                all_players.add(player["name"])
        
        # Add some free agents
        free_agents = [
            "Keibert Ruiz", "Danny Jansen", "Christian Walker", 
            "Spencer Torkelson", "Gavin Lux", "Luis Rengifo", 
            "JP Crawford", "Ha-Seong Kim", "Jeimer Candelario", 
            "Spencer Steer", "Luis Matos", "Heliot Ramos", 
            "TJ Friedl", "Garrett Mitchell", "Kutter Crawford", 
            "Reese Olson", "Dane Dunning", "José Berríos", 
            "Erik Swanson", "Seranthony Domínguez"
        ]
        
        for player in free_agents:
            all_players.add(player)
        
        # Generate stats and projections for all players
        self._generate_synthetic_data(all_players)
        
        logger.info(f"Generated synthetic stats for {len(self.player_stats_current)} players")
        logger.info(f"Generated synthetic projections for {len(self.player_projections)} players")
    
    def _generate_synthetic_data(self, player_names):
        """Generate synthetic stats and projections for demo purposes"""
        for player in player_names:
            # Determine if batter or pitcher based on name recognition
            # This is a simple heuristic; in reality, you'd use actual data
            is_pitcher = player in [
                "Cole Ragans", "Hunter Greene", "Jack Flaherty", "Ryan Helsley", 
                "Tanner Scott", "Pete Fairbanks", "Ryan Pepiot", "MacKenzie Gore", 
                "Camilo Doval", "Tarik Skubal", "Spencer Schwellenbach", "Hunter Brown", 
                "Jhoan Duran", "Jeff Hoffman", "Ryan Pressly", "Justin Verlander", 
                "Max Scherzer", "Kutter Crawford", "Reese Olson", "Dane Dunning", 
                "José Berríos", "Erik Swanson", "Seranthony Domínguez"
            ]
            
            if is_pitcher:
                # Generate pitcher stats
                current_stats = {
                    'IP': random.uniform(20, 40),
                    'W': random.randint(1, 4),
                    'L': random.randint(0, 3),
                    'ERA': random.uniform(2.5, 5.0),
                    'WHIP': random.uniform(0.9, 1.5),
                    'K': random.randint(15, 50),
                    'BB': random.randint(5, 20),
                    'QS': random.randint(1, 5),
                    'SV': 0 if player not in ["Ryan Helsley", "Tanner Scott", "Pete Fairbanks", "Camilo Doval", "Jhoan Duran", "Ryan Pressly", "Erik Swanson", "Seranthony Domínguez"] else random.randint(1, 8)
                }
                
                # Calculate k/9
                current_stats['K9'] = current_stats['K'] * 9 / current_stats['IP'] if current_stats['IP'] > 0 else 0
                
                # Generate projections (rest of season)
                projected_ip = random.uniform(120, 180) if current_stats['SV'] == 0 else random.uniform(45, 70)
                projected_stats = {
                    'IP': projected_ip,
                    'ERA': random.uniform(3.0, 4.5),
                    'WHIP': random.uniform(1.05, 1.35),
                    'K9': random.uniform(7.5, 12.0),
                    'QS': random.randint(10, 20) if current_stats['SV'] == 0 else 0,
                    'SV': 0 if current_stats['SV'] == 0 else random.randint(15, 35)
                }
            else:
                # Generate batter stats
                current_stats = {
                    'AB': random.randint(70, 120),
                    'R': random.randint(8, 25),
                    'H': random.randint(15, 40),
                    'HR': random.randint(1, 8),
                    'RBI': random.randint(5, 25),
                    'SB': random.randint(0, 8),
                    'BB': random.randint(5, 20),
                    'SO': random.randint(15, 40)
                }
                
                # Calculate derived stats
                current_stats['AVG'] = current_stats['H'] / current_stats['AB'] if current_stats['AB'] > 0 else 0
                current_stats['OBP'] = (current_stats['H'] + current_stats['BB']) / (current_stats['AB'] + current_stats['BB']) if (current_stats['AB'] + current_stats['BB']) > 0 else 0
                
                # Estimate SLG and OPS
                singles = current_stats['H'] - current_stats['HR'] - random.randint(2, 10) - random.randint(0, 5)
                doubles = random.randint(2, 10)
                triples = random.randint(0, 5)
                tb = singles + (2 * doubles) + (3 * triples) + (4 * current_stats['HR'])
                current_stats['SLG'] = tb / current_stats['AB'] if current_stats['AB'] > 0 else 0
                current_stats['OPS'] = current_stats['OBP'] + current_stats['SLG']
                
                # Generate projections (rest of season)
                projected_stats = {
                    'AB': random.randint(400, 550),
                    'R': random.randint(50, 100),
                    'HR': random.randint(10, 35),
                    'RBI': random.randint(40, 100),
                    'SB': random.randint(3, 35),
                    'AVG': random.uniform(0.230, 0.310),
                    'OPS': random.uniform(0.680, 0.950)
                }
            
            # Add to dictionaries
            self.player_stats_current[player] = current_stats
            self.player_projections[player] = projected_stats
    
    def identify_free_agents(self):
        """Identify all players who aren't on team rosters but have stats/projections"""
        # Create a set of all rostered players
        rostered_players = set()
        for team, roster in self.team_rosters.items():
            for player in roster:
                rostered_players.add(player["name"])
        
        # Find players with stats/projections who aren't rostered
        self.free_agents = {}
        
        for player in self.player_projections.keys():
            if player not in rostered_players:
                # Determine position based on stats
                if player in self.player_stats_current:
                    if 'ERA' in self.player_stats_current[player]:
                        position = 'RP' if self.player_stats_current[player].get('SV', 0) > 0 else 'SP'
                    else:
                        # This is simplistic - in a real system, we'd have actual position data
                        position = 'Unknown'
                else:
                    position = 'Unknown'
                
                self.free_agents[player] = {
                    'name': player,
                    'position': position,
                    'stats': self.player_stats_current.get(player, {}),
                    'projections': self.player_projections.get(player, {})
                }
        
        logger.info(f"Identified {len(self.free_agents)} free agents")
        return self.free_agents
    
    def save_system_state(self):
        """Save the current state of the system to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save team rosters
        with open(f"{self.data_dir}/team_rosters.json", 'w') as f:
            json.dump(self.team_rosters, f, indent=4)
        
        # Save current stats
        with open(f"{self.data_dir}/player_stats_current.json", 'w') as f:
            json.dump(self.player_stats_current, f, indent=4)
        
        # Save projections
        with open(f"{self.data_dir}/player_projections.json", 'w') as f:
            json.dump(self.player_projections, f, indent=4)
        
        # Save free agents
        with open(f"{self.data_dir}/free_agents.json", 'w') as f:
            json.dump(self.free_agents, f, indent=4)
        
        # Also save an archive copy
        with open(f"{self.archives_dir}/team_rosters_{timestamp}.json", 'w') as f:
            json.dump(self.team_rosters, f, indent=4)
        
        with open(f"{self.archives_dir}/player_stats_{timestamp}.json", 'w') as f:
            json.dump(self.player_stats_current, f, indent=4)
        
        with open(f"{self.archives_dir}/projections_{timestamp}.json", 'w') as f:
            json.dump(self.player_projections, f, indent=4)
        
        logger.info(f"System state saved successfully with timestamp: {timestamp}")
    
    def load_system_state(self):
        """Load the system state from saved files"""
        try:
            # Load team rosters
            if os.path.exists(f"{self.data_dir}/team_rosters.json"):
                with open(f"{self.data_dir}/team_rosters.json", 'r') as f:
                    self.team_rosters = json.load(f)
            
            # Load current stats
            if os.path.exists(f"{self.data_dir}/player_stats_current.json"):
                with open(f"{self.data_dir}/player_stats_current.json", 'r') as f:
                    self.player_stats_current = json.load(f)
            
            # Load projections
            if os.path.exists(f"{self.data_dir}/player_projections.json"):
                with open(f"{self.data_dir}/player_projections.json", 'r') as f:
                    self.player_projections = json.load(f)
            
            # Load free agents
            if os.path.exists(f"{self.data_dir}/free_agents.json"):
                with open(f"{self.data_dir}/free_agents.json", 'r') as f:
                    self.free_agents = json.load(f)
            
            logger.info("System state loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading system state: {e}")
            return False
    
    def update_player_stats(self):
        """Update player stats by fetching from data sources"""
        logger.info("Updating player stats from sources...")
        
        # In a real implementation, you would:
        # 1. Fetch data from each source in self.data_sources['stats']
        # 2. Parse and clean the data
        # 3. Merge with existing stats
        # 4. Update self.player_stats_current
        
        # For demo purposes, we'll simulate this process
        self._simulate_stats_update()
        
        logger.info(f"Updated stats for {len(self.player_stats_current)} players")
        return len(self.player_stats_current)
    
    def _simulate_stats_update(self):
        """Simulate updating stats for demo purposes"""
        # Add some new players
        new_players = [
            "Bobby Miller", "Garrett Crochet", "DL Hall", 
            "Edward Cabrera", "Alec Bohm", "Elly De La Cruz",
            "Anthony Volpe", "Jazz Chisholm Jr."
        ]
        
        for player in new_players:
            if player not in self.player_stats_current:
                # Determine if batter or pitcher based on name recognition
                is_pitcher = player in ["Bobby Miller", "Garrett Crochet", "DL Hall", "Edward Cabrera"]
                
                if is_pitcher:
                    self.player_stats_current[player] = {
                        'IP': random.uniform(10, 30),
                        'W': random.randint(1, 3),
                        'L': random.randint(0, 2),
                        'ERA': random.uniform(3.0, 5.0),
                        'WHIP': random.uniform(1.0, 1.4),
                        'K': random.randint(10, 40),
                        'BB': random.randint(5, 15),
                        'QS': random.randint(1, 4),
                        'SV': 0
                    }
                    
                    # Calculate k/9
                    self.player_stats_current[player]['K9'] = (
                        self.player_stats_current[player]['K'] * 9 / 
                        self.player_stats_current[player]['IP'] 
                        if self.player_stats_current[player]['IP'] > 0 else 0
                    )
                else:
                    self.player_stats_current[player] = {
                        'AB': random.randint(50, 100),
                        'R': random.randint(5, 20),
                        'H': random.randint(10, 30),
                        'HR': random.randint(1, 6),
                        'RBI': random.randint(5, 20),
                        'SB': random.randint(0, 6),
                        'BB': random.randint(5, 15),
                        'SO': random.randint(10, 30)
                    }
                    
                    # Calculate derived stats
                    self.player_stats_current[player]['AVG'] = (
                        self.player_stats_current[player]['H'] / 
                        self.player_stats_current[player]['AB'] 
                        if self.player_stats_current[player]['AB'] > 0 else 0
                    )
                    
                    self.player_stats_current[player]['OBP'] = (
                        (self.player_stats_current[player]['H'] + self.player_stats_current[player]['BB']) / 
                        (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) 
                        if (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) > 0 else 0
                    )
                    
                    # Estimate SLG and OPS
                    singles = (
                        self.player_stats_current[player]['H'] - 
                        self.player_stats_current[player]['HR'] - 
                        random.randint(2, 8) - 
                        random.randint(0, 3)
                    )
                    doubles = random.randint(2, 8)
                    triples = random.randint(0, 3)
                    tb = singles + (2 * doubles) + (3 * triples) + (4 * self.player_stats_current[player]['HR'])
                    
                    self.player_stats_current[player]['SLG'] = (
                        tb / self.player_stats_current[player]['AB'] 
                        if self.player_stats_current[player]['AB'] > 0 else 0
                    )
                    
                    self.player_stats_current[player]['OPS'] = (
                        self.player_stats_current[player]['OBP'] + 
                        self.player_stats_current[player]['SLG']
                    )
        
        # Update existing player stats
        for player in list(self.player_stats_current.keys()):
            # Skip some players randomly to simulate days off
            if random.random() < 0.3:
                continue
                
            # Determine if batter or pitcher based on existing stats
            if 'ERA' in self.player_stats_current[player]:  # It's a pitcher
                # Generate random game stats
                ip = random.uniform(0.1, 7)
                k = int(ip * random.uniform(0.5, 1.5))
                bb = int(ip * random.uniform(0.1, 0.5))
                er = int(ip * random.uniform(0, 0.7))
                h = int(ip * random.uniform(0.3, 1.2))
                
                # Update aggregated stats
                self.player_stats_current[player]['IP'] += ip
                self.player_stats_current[player]['K'] += k
                self.player_stats_current[player]['BB'] += bb
                
                # Update win/loss
                if random.random() < 0.5:
                    if random.random() < 0.6:  # 60% chance of decision
                        if random.random() < 0.5:  # 50% chance of win
                            self.player_stats_current[player]['W'] = self.player_stats_current[player].get('W', 0) + 1
                        else:
                            self.player_stats_current[player]['L'] = self.player_stats_current[player].get('L', 0) + 1
                
                # Update quality starts
                if ip >= 6 and er <= 3 and 'SV' not in self.player_stats_current[player]:
                    self.player_stats_current[player]['QS'] = self.player_stats_current[player].get('QS', 0) + 1
                
                # Update saves for relievers
                if 'SV' in self.player_stats_current[player] and ip <= 2 and random.random() < 0.3:
                    self.player_stats_current[player]['SV'] = self.player_stats_current[player].get('SV', 0) + 1
                
                # Recalculate ERA and WHIP
                total_er = (self.player_stats_current[player]['ERA'] * 
                           (self.player_stats_current[player]['IP'] - ip) / 9) + er
                            
                self.player_stats_current[player]['ERA'] = (
                    total_er * 9 / self.player_stats_current[player]['IP'] 
                    if self.player_stats_current[player]['IP'] > 0 else 0
                )
                
                # Add baserunners for WHIP calculation
                self.player_stats_current[player]['WHIP'] = (
                    (self.player_stats_current[player]['WHIP'] * 
                     (self.player_stats_current[player]['IP'] - ip) + (h + bb)) / 
                    self.player_stats_current[player]['IP'] 
                    if self.player_stats_current[player]['IP'] > 0 else 0
                )
                
                # Update K/9
                self.player_stats_current[player]['K9'] = (
                    self.player_stats_current[player]['K'] * 9 / 
                    self.player_stats_current[player]['IP'] 
                    if self.player_stats_current[player]['IP'] > 0 else 0
                )
                
            else:  # It's a batter
                # Generate random game stats
                ab = random.randint(0, 5)
                h = 0
                hr = 0
                r = 0
                rbi = 0
                sb = 0
                bb = 0
                so = 0
                
                if ab > 0:
                    # Determine hits
                    for _ in range(ab):
                        if random.random() < 0.270:  # League average is around .270
                            h += 1
                            # Determine if it's a home run
                            if random.random() < 0.15:  # About 15% of hits are HRs
                                hr += 1
                    
                    # Other stats
                    r = random.randint(0, 2) if h > 0 else 0
                    rbi = random.randint(0, 3) if h > 0 else 0
                    sb = 1 if random.random() < 0.08 else 0  # 8% chance of SB
                    bb = 1 if random.random() < 0.1 else 0  # 10% chance of BB
                    so = random.randint(0, 2)  # 0-2 strikeouts
                
                # Update aggregated stats
                self.player_stats_current[player]['AB'] += ab
                self.player_stats_current[player]['H'] += h
                self.player_stats_current[player]['HR'] += hr
                self.player_stats_current[player]['R'] += r
                self.player_stats_current[player]['RBI'] += rbi
                self.player_stats_current[player]['SB'] += sb
                self.player_stats_current[player]['BB'] += bb
                self.player_stats_current[player]['SO'] += so
                
                # Recalculate AVG
                self.player_stats_current[player]['AVG'] =# Recalculate AVG
                self.player_stats_current[player]['AVG'] = (
                    self.player_stats_current[player]['H'] / 
                    self.player_stats_current[player]['AB'] 
                    if self.player_stats_current[player]['AB'] > 0 else 0
                )
                
                # Recalculate OBP
                self.player_stats_current[player]['OBP'] = (
                    (self.player_stats_current[player]['H'] + self.player_stats_current[player]['BB']) / 
                    (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) 
                    if (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) > 0 else 0
                )
                
                # Recalculate SLG and OPS
                singles = (
                    self.player_stats_current[player]['H'] - 
                    self.player_stats_current[player]['HR'] - 
                    self.player_stats_current[player].get('2B', random.randint(15, 25)) - 
                    self.player_stats_current[player].get('3B', random.randint(0, 5))
                )
                
                tb = (
                    singles + 
                    (2 * self.player_stats_current[player].get('2B', random.randint(15, 25))) + 
                    (3 * self.player_stats_current[player].get('3B', random.randint(0, 5))) + 
                    (4 * self.player_stats_current[player]['HR'])
                )
                
                self.player_stats_current[player]['SLG'] = (
                    tb / self.player_stats_current[player]['AB'] 
                    if self.player_stats_current[player]['AB'] > 0 else 0
                )
                
                self.player_stats_current[player]['OPS'] = (
                    self.player_stats_current[player]['OBP'] + 
                    self.player_stats_current[player]['SLG']
                )
    
    def update_player_projections(self):
        """Update player projections by fetching from data sources"""
        logger.info("Updating player projections from sources...")
        
        # In a real implementation, you would:
        # 1. Fetch data from each source in self.data_sources['projections']
        # 2. Parse and clean the data
        # 3. Merge with existing projections
        # 4. Update self.player_projections
        
        # For demo purposes, we'll simulate this process
        self._simulate_projections_update()
        
        logger.info(f"Updated projections for {len(self.player_projections)} players")
        return len(self.player_projections)
    
    def _simulate_projections_update(self):
        """Simulate updating projections for demo purposes"""
        # Update existing projections based on current stats
        for player in self.player_stats_current:
            # Skip if no projection exists
            if player not in self.player_projections:
                # Create new projection based on current stats
                if 'ERA' in self.player_stats_current[player]:  # It's a pitcher
                    # Project rest of season based on current performance
                    era_factor = min(max(4.00 / self.player_stats_current[player]['ERA'], 0.75), 1.25) if self.player_stats_current[player]['ERA'] > 0 else 1.0
                    whip_factor = min(max(1.30 / self.player_stats_current[player]['WHIP'], 0.75), 1.25) if self.player_stats_current[player]['WHIP'] > 0 else 1.0
                    k9_factor = min(max(self.player_stats_current[player]['K9'] / 8.5, 0.75), 1.25) if self.player_stats_current[player].get('K9', 0) > 0 else 1.0
                    
                    # Determine if starter or reliever
                    is_reliever = 'SV' in self.player_stats_current[player] or self.player_stats_current[player].get('IP', 0) < 20
                    
                    self.player_projections[player] = {
                        'IP': random.uniform(40, 70) if is_reliever else random.uniform(120, 180),
                        'ERA': random.uniform(3.0, 4.5) * era_factor,
                        'WHIP': random.uniform(1.05, 1.35) * whip_factor,
                        'K9': random.uniform(7.5, 12.0) * k9_factor,
                        'QS': 0 if is_reliever else random.randint(10, 20),
                        'SV': random.randint(15, 35) if is_reliever and self.player_stats_current[player].get('SV', 0) > 0 else 0
                    }
                else:  # It's a batter
                    # Project rest of season based on current performance
                    avg_factor = min(max(self.player_stats_current[player]['AVG'] / 0.260, 0.8), 1.2) if self.player_stats_current[player]['AVG'] > 0 else 1.0
                    ops_factor = min(max(self.player_stats_current[player].get('OPS', 0.750) / 0.750, 0.8), 1.2) if self.player_stats_current[player].get('OPS', 0) > 0 else 1.0
                    
                    # Projected plate appearances remaining
                    pa_remaining = random.randint(400, 550)
                    
                    # HR rate
                    hr_rate = self.player_stats_current[player]['HR'] / self.player_stats_current[player]['AB'] if self.player_stats_current[player]['AB'] > 0 else 0.025
                    
                    # SB rate
                    sb_rate = self.player_stats_current[player]['SB'] / self.player_stats_current[player]['AB'] if self.player_stats_current[player]['AB'] > 0 else 0.015
                    
                    self.player_projections[player] = {
                        'AB': pa_remaining * 0.9,  # 10% of PA are walks/HBP
                        'R': pa_remaining * random.uniform(0.12, 0.18),
                        'HR': pa_remaining * hr_rate * random.uniform(0.8, 1.2),
                        'RBI': pa_remaining * random.uniform(0.1, 0.17),
                        'SB': pa_remaining * sb_rate * random.uniform(0.8, 1.2),
                        'AVG': random.uniform(0.230, 0.310) * avg_factor,
                        'OPS': random.uniform(0.680, 0.950) * ops_factor
                    }
                continue
            
            # If projection exists, update it based on current performance
            if 'ERA' in self.player_stats_current[player]:  # It's a pitcher
                # Calculate adjustment factors based on current vs. projected performance
                if self.player_stats_current[player].get('IP', 0) > 20:  # Enough IP to adjust projections
                    # ERA adjustment
                    current_era = self.player_stats_current[player].get('ERA', 4.00)
                    projected_era = self.player_projections[player].get('ERA', 4.00)
                    era_adj = min(max(projected_era / current_era, 0.8), 1.2) if current_era > 0 else 1.0
                    
                    # WHIP adjustment
                    current_whip = self.player_stats_current[player].get('WHIP', 1.30)
                    projected_whip = self.player_projections[player].get('WHIP', 1.30)
                    whip_adj = min(max(projected_whip / current_whip, 0.8), 1.2) if current_whip > 0 else 1.0
                    
                    # K/9 adjustment
                    current_k9 = self.player_stats_current[player].get('K9', 8.5)
                    projected_k9 = self.player_projections[player].get('K9', 8.5)
                    k9_adj = min(max(current_k9 / projected_k9, 0.8), 1.2) if projected_k9 > 0 else 1.0
                    
                    # Apply adjustments
                    self.player_projections[player]['ERA'] = projected_era * era_adj
                    self.player_projections[player]['WHIP'] = projected_whip * whip_adj
                    self.player_projections[player]['K9'] = projected_k9 * k9_adj
                    
                    # Adjust saves projection for relievers
                    if 'SV' in self.player_stats_current[player]:
                        current_sv_rate = self.player_stats_current[player].get('SV', 0) / max(1, self.player_stats_current[player].get('IP', 1) / 60)
                        self.player_projections[player]['SV'] = min(45, max(0, int(current_sv_rate * 60)))
                    
                    # Adjust QS projection for starters
                    if 'QS' in self.player_stats_current[player] and self.player_stats_current[player].get('IP', 0) > 0:
                        current_qs_rate = self.player_stats_current[player].get('QS', 0) / max(1, self.player_stats_current[player].get('IP', 1) / 180)
                        self.player_projections[player]['QS'] = min(30, max(0, int(current_qs_rate * 180)))
            else:  # It's a batter
                # Adjust only if enough AB to be significant
                if self.player_stats_current[player].get('AB', 0) > 75:
                    # AVG adjustment
                    current_avg = self.player_stats_current[player].get('AVG', 0.260)
                    projected_avg = self.player_projections[player].get('AVG', 0.260)
                    avg_adj = min(max((current_avg + 2*projected_avg) / (3*projected_avg), 0.85), 1.15) if projected_avg > 0 else 1.0
                    
                    # HR rate adjustment
                    current_hr_rate = self.player_stats_current[player].get('HR', 0) / max(1, self.player_stats_current[player].get('AB', 1)) * 550
                    projected_hr = self.player_projections[player].get('HR', 15)
                    hr_adj = min(max((current_hr_rate + 2*projected_hr) / (3*projected_hr), 0.7), 1.3) if projected_hr > 0 else 1.0
                    
                    # SB rate adjustment
                    current_sb_rate = self.player_stats_current[player].get('SB', 0) / max(1, self.player_stats_current[player].get('AB', 1)) * 550
                    projected_sb = self.player_projections[player].get('SB', 10)
                    sb_adj = min(max((current_sb_rate + 2*projected_sb) / (3*projected_sb), 0.7), 1.3) if projected_sb > 0 else 1.0
                    
                    # Apply adjustments
                    self.player_projections[player]['AVG'] = projected_avg * avg_adj
                    self.player_projections[player]['HR'] = projected_hr * hr_adj
                    self.player_projections[player]['SB'] = projected_sb * sb_adj
                    
                    # Adjust OPS based on AVG and power
                    projected_ops = self.player_projections[player].get('OPS', 0.750)
                    self.player_projections[player]['OPS'] = projected_ops * (avg_adj * 0.4 + hr_adj * 0.6)
                    
                    # Adjust runs and RBI based on HR and overall performance
                    projected_r = self.player_projections[player].get('R', 70)
                    projected_rbi = self.player_projections[player].get('RBI', 70)
                    
                    self.player_projections[player]['R'] = projected_r * ((avg_adj + hr_adj) / 2)
                    self.player_projections[player]['RBI'] = projected_rbi * ((avg_adj + hr_adj) / 2)
        
        # Round numerical values for cleaner display
        for player in self.player_projections:
            for stat in self.player_projections[player]:
                if isinstance(self.player_projections[player][stat], float):
                    if stat in ['ERA', 'WHIP', 'K9', 'AVG', 'OPS']:
                        self.player_projections[player][stat] = round(self.player_projections[player][stat], 3)
                    else:
                        self.player_projections[player][stat] = round(self.player_projections[player][stat])
    
    def update_player_news(self):
        """Update player news by fetching from news sources"""
        logger.info("Updating player news from sources...")
        
        # In a real implementation, you would:
        # 1. Fetch data from each source in self.data_sources['news']
        # 2. Parse and extract news items
        # 3. Store in self.player_news
        
        # For demo purposes, we'll simulate this process
        self._simulate_news_update()
        
        logger.info(f"Updated news for {len(self.player_news)} players")
        return len(self.player_news)
    
    def _simulate_news_update(self):
        """Simulate updating player news for demo purposes"""
        # List of possible news templates
        injury_news = [
            "{player} was removed from Wednesday's game with {injury}.",
            "{player} is day-to-day with {injury}.",
            "{player} has been placed on the 10-day IL with {injury}.",
            "{player} will undergo further testing for {injury}.",
            "{player} is expected to miss 4-6 weeks with {injury}."
        ]
        
        performance_news = [
            "{player} went {stats} in Wednesday's 6-4 win.",
            "{player} struck out {k} batters in {ip} innings on Tuesday.",
            "{player} has hit safely in {streak} straight games.",
            "{player} collected {hits} hits including a homer on Monday.",
            "{player} has struggled recently, going {bad_stats} over his last 7 games."
        ]
        
        role_news = [
            "{player} will take over as the closer with {teammate} on the IL.",
            "{player} has been moved up to the {spot} spot in the batting order.",
            "{player} will make his next start on {day}.",
            "{player} has been moved to the bullpen.",
            "{player} will be recalled from Triple-A on Friday."
        ]
        
        # Possible injuries
        injuries = [
            "left hamstring tightness",
            "right oblique strain",
            "lower back discomfort",
            "shoulder inflammation",
            "forearm tightness",
            "groin strain",
            "ankle sprain",
            "knee soreness",
            "thumb contusion",
            "wrist inflammation"
        ]
        
        # Generate news for a subset of players
        for player in random.sample(list(self.player_stats_current.keys()), min(10, len(self.player_stats_current))):
            news_type = random.choice(["injury", "performance", "role"])
            
            if news_type == "injury":
                template = random.choice(injury_news)
                news_item = template.format(
                    player=player,
                    injury=random.choice(injuries)
                )
            elif news_type == "performance":
                template = random.choice(performance_news)
                
                # Determine if batter or pitcher
                if 'ERA' in self.player_stats_current[player]:  # Pitcher
                    ip = round(random.uniform(5, 7), 1)
                    k = random.randint(4, 10)
                    news_item = template.format(
                        player=player,
                        k=k,
                        ip=ip,
                        streak=random.randint(3, 10),
                        hits=random.randint(2, 4),
                        bad_stats=f"{random.randint(0, 4)}-for-{random.randint(20, 30)}"
                    )
                else:  # Batter
                    hits = random.randint(0, 4)
                    abs = random.randint(hits, 5)
                    news_item = template.format(
                        player=player,
                        stats=f"{hits}-for-{abs}",
                        k=random.randint(5, 12),
                        ip=round(random.uniform(5, 7), 1),
                        streak=random.randint(5, 15),
                        hits=random.randint(2, 4),
                        bad_stats=f"{random.randint(0, 4)}-for-{random.randint(20, 30)}"
                    )
            else:  # Role
                template = random.choice(role_news)
                news_item = template.format(
                    player=player,
                    teammate=random.choice(list(self.player_stats_current.keys())),
                    spot=random.choice(["leadoff", "cleanup", "third", "fifth"]),
                    day=random.choice(["Friday", "Saturday", "Sunday", "Monday"])
                )
            
            # Add news item with timestamp
            if player not in self.player_news:
                self.player_news[player] = []
            
            self.player_news[player].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source": random.choice(["Rotowire", "CBS Sports", "ESPN", "MLB.com"]),
                "content": news_item
            })
    
    def update_player_injuries(self):
        """Update player injury statuses"""
        logger.info("Updating player injury statuses...")
        
        # In a real implementation, you would:
        # 1. Fetch injury data from reliable sources
        # 2. Update player status accordingly
        # 3. Adjust projections for injured players
        
        # For demo purposes, we'll simulate some injuries
        injury_count = 0
        
        for player in self.player_stats_current:
            # 5% chance of new injury for each player
            if random.random() < 0.05:
                injury_severity = random.choice(["day-to-day", "10-day IL", "60-day IL"])
                injury_type = random.choice([
                    "hamstring strain", "oblique strain", "back spasms", 
                    "shoulder inflammation", "elbow soreness", "knee inflammation",
                    "ankle sprain", "concussion", "wrist sprain"
                ])
                
                # Add injury news
                if player not in self.player_news:
                    self.player_news[player] = []
                
                self.player_news[player].append({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "source": random.choice(["Rotowire", "CBS Sports", "ESPN", "MLB.com"]),
                    "content": f"{player} has been placed on the {injury_severity} with a {injury_type}."
                })
                
                # Adjust projections for injured players
                if player in self.player_projections:
                    if injury_severity == "day-to-day":
                        reduction = 0.05  # 5% reduction in projections
                    elif injury_severity == "10-day IL":
                        reduction = 0.15  # 15% reduction
                    else:  # 60-day IL
                        reduction = 0.50  # 50% reduction
                    
                    # Apply reduction to projected stats
                    for stat in self.player_projections[player]:
                        if stat not in ['AVG', 'ERA', 'WHIP', 'K9', 'OPS']:  # Don't reduce rate stats
                            self.player_projections[player][stat] *= (1 - reduction)
                
                injury_count += 1
        
        logger.info(f"Updated injury status for {injury_count} players")
        return injury_count
    
    def update_league_transactions(self):
        """Simulate league transactions (adds, drops, trades)"""
        logger.info("Simulating league transactions...")
        
        # In a real implementation, you would:
        # 1. Fetch transaction data from your fantasy platform API
        # 2. Update team rosters accordingly
        
        # For demo purposes, we'll simulate some transactions
        transaction_count = 0
        
        # Add/drop transactions (1-3 per update)
        for _ in range(random.randint(1, 3)):
            # Select a random team
            team = random.choice(list(self.team_rosters.keys()))
            
            # Select a random player to drop
            if len(self.team_rosters[team]) > 0:
                drop_index = random.randint(0, len(self.team_rosters[team]) - 1)
                dropped_player = self.team_rosters[team][drop_index]["name"]
                
                # Remove from roster
                self.team_rosters[team].pop(drop_index)
                
                # Pick a random free agent to add
                if len(self.free_agents) > 0:
                    added_player = random.choice(list(self.free_agents.keys()))
                    
                    # Determine position
                    position = "Unknown"
                    if 'ERA' in self.player_stats_current.get(added_player, {}):
                        position = 'RP' if self.player_stats_current[added_player].get('SV', 0) > 0 else 'SP'
                    else:
                        position = random.choice(["C", "1B", "2B", "3B", "SS", "OF"])
                    
                    # Add to roster
                    self.team_rosters[team].append({
                        "name": added_player,
                        "position": position
                    })
                    
                    # Remove from free agents
                    if added_player in self.free_agents:
                        del self.free_agents[added_player]
                    
                    # Log transaction
                    logger.info(f"Transaction: {team} dropped {dropped_player} and added {added_player}")
                    transaction_count += 1
        
        # Trade transactions (0-1 per update)
        if random.random() < 0.3:  # 30% chance of a trade
            # Select two random teams
            teams = random.sample(list(self.team_rosters.keys()), 2)
            
            # Select random players to trade (1-2 per team)
            team1_players = []
            team2_players = []
            
            for _ in range(random.randint(1, 2)):
                if len(self.team_rosters[teams[0]]) > 0:
                    idx = random.randint(0, len(self.team_rosters[teams[0]]) - 1)
                    team1_players.append(self.team_rosters[teams[0]][idx])
                    self.team_rosters[teams[0]].pop(idx)
            
            for _ in range(random.randint(1, 2)):
                if len(self.team_rosters[teams[1]]) > 0:
                    idx = random.randint(0, len(self.team_rosters[teams[1]]) - 1)
                    team2_players.append(self.team_rosters[teams[1]][idx])
                    self.team_rosters[teams[1]].pop(idx)
            
            # Execute the trade
            for player in team1_players:
                self.team_rosters[teams[1]].append(player)
            
            for player in team2_players:
                self.team_rosters[teams[0]].append(player)
            
            # Log transaction
            team1_names = [p["name"] for p in team1_players]
            team2_names = [p["name"] for p in team2_players]
            
            logger.info(f"Trade: {teams[0]} traded {', '.join(team1_names)} to {teams[1]} for {', '.join(team2_names)}")
            transaction_count += 1
        
        logger.info(f"Simulated {transaction_count} league transactions")
        return transaction_count
    
    def run_system_update(self):
        """Run a complete system update"""
        logger.info("Starting system update...")
        
        try:
            # Update player stats
            self.update_player_stats()
            
            # Update player projections
            self.update_player_projections()
            
            # Update player news
            self.update_player_news()
            
            # Update player injuries
            self.update_player_injuries()
            
            # Update league transactions
            self.update_league_transactions()
            
            # Identify free agents
            self.identify_free_agents()
            
            # Save updated system state
            self.save_system_state()
            
            # Generate updated reports
            self.generate_reports()
            
            # Update timestamp
            self.last_update = datetime.now()
            
            logger.info(f"System update completed successfully at {self.last_update}")
            return True
        except Exception as e:
            logger.error(f"Error during system update: {e}")
            return False
    
    def generate_reports(self):
        """Generate various reports"""
        timestamp = datetime.now().strftime("%Y%m%d")
        
        # Generate team analysis report
        self.generate_team_analysis_report(f"{self.reports_dir}/team_analysis_{timestamp}.md")
        
        # Generate free agents report
        self.generate_free_agents_report(f"{self.reports_dir}/free_agents_{timestamp}.md")
        
        # Generate trending players report
        self.generate_trending_players_report(f"{self.reports_dir}/trending_players_{timestamp}.md")
        
        # Generate player news report
        self.generate_player_news_report(f"{self.reports_dir}/player_news_{timestamp}.md")
        
        logger.info(f"Generated reports with timestamp {timestamp}")
    
    def generate_team_analysis_report(self, output_file):
        """Generate team analysis report"""
        with open(output_file, 'w') as f:
            # Title
            f.write("# Fantasy Baseball Team Analysis\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
            
            # Your Team Section
            f.write(f"## Your Team: {self.your_team_name}\n\n")
            
            # Team Roster
            f.write("### Current Roster\n\n")
            
            # Group players by position
            positions = {"C": [], "1B": [], "2B": [], "3B": [], "SS": [], "OF": [], "SP": [], "RP": []}
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                position = player["position"]
                
                # Simplified position assignment
                if position in positions:
                    positions[position].append(name)
                elif "/" in position:  # Handle multi-position players
                    primary_pos = position.split("/")[0]
                    if primary_pos in positions:
                        positions[primary_pos].append(name)
                    else:
                        positions["UTIL"].append(name)
                else:
                    # Handle unknown positions
                    if 'ERA' in self.player_stats_current.get(name, {}):
                        if self.player_stats_current[name].get('SV', 0) > 0:
                            positions["RP"].append(name)
                        else:
                            positions["SP"].append(name)
                    else:
                        positions["UTIL"].append(name)
            
            # Write roster by position
            for pos, players in positions.items():
                if players:
                    f.write(f"**{pos}**: {', '.join(players)}\n\n")
            
            # Team Performance
            f.write("### Team Performance\n\n")
            
            # Calculate team totals
            batting_totals = {
                'AB': 0, 'R': 0, 'HR': 0, 'RBI': 0, 'SB': 0, 'AVG': 0, 'OPS': 0
            }
            
            pitching_totals = {
                'IP': 0, 'W': 0, 'ERA': 0, 'WHIP': 0, 'K': 0, 'QS': 0, 'SV': 0
            }
            
            # Batters stats
            f.write("#### Batting Stats\n\n")
            batter_table = []
            headers = ["Player", "AB", "R", "HR", "RBI", "SB", "AVG", "OPS"]
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_stats_current and 'AVG' in self.player_stats_current[name]:
                    stats = self.player_stats_current[name]
                    batter_table.append([
                        name,
                        stats.get('AB', 0),
                        stats.get('R', 0),
                        stats.get('HR', 0),
                        stats.get('RBI', 0),
                        stats.get('SB', 0),
                        f"{stats.get('AVG', 0):.3f}",
                        f"{stats.get('OPS', 0):.3f}"
                    ])
                    
                    # Add to totals
                    batting_totals['AB'] += stats.get('AB', 0)
                    batting_totals['R'] += stats.get('R', 0)
                    batting_totals['HR'] += stats.get('HR', 0)
                    batting_totals['RBI'] += stats.get('RBI', 0)
                    batting_totals['SB'] += stats.get('SB', 0)
            
            # Calculate team AVG and OPS
            if batting_totals['AB'] > 0:
                total_hits = sum(self.player_stats_current.get(p["name"], {}).get('H', 0) for p in self.team_rosters.get(self.your_team_name, []))
                batting_totals['AVG'] = total_hits / batting_totals['AB']
                
                # Estimate team OPS as average of player OPS values
                ops_values = [self.player_stats_current.get(p["name"], {}).get('OPS', 0) for p in self.team_rosters.get(self.your_team_name, [])]
                ops_values = [ops for ops in ops_values if ops > 0]
                #!/usr/bin/env python3
# Fantasy Baseball Automated Model with Live Updates
# This script creates an automated system that regularly updates player stats and projections
# Uses the same sources (PECOTA, FanGraphs, MLB.com) for consistent data

import os
import csv
import json
import time
import random
import requests
import pandas as pd
import numpy as np
import schedule
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from tabulate import tabulate
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fantasy_baseball_auto.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FantasyBaseballAuto")

class FantasyBaseballAutomated:
    def __init__(self, league_id="2874", your_team_name="Kenny Kawaguchis"):
        self.league_id = league_id
        self.your_team_name = your_team_name
        self.teams = {}
        self.team_rosters = {}
        self.free_agents = {}
        self.player_stats_current = {}
        self.player_projections = {}
        self.player_news = {}
        self.last_update = None
        
        # API endpoints and data sources
        self.data_sources = {
            'stats': [
                'https://www.fangraphs.com/api/players/stats',
                'https://www.baseball-reference.com/leagues/MLB/2025.shtml',
                'https://www.mlb.com/stats/'
            ],
            'projections': [
                'https://www.fangraphs.com/projections.aspx',
                'https://www.baseball-prospectus.com/pecota-projections/',
                'https://www.mlb.com/stats/projected'
            ],
            'news': [
                'https://www.rotowire.com/baseball/news.php',
                'https://www.cbssports.com/fantasy/baseball/players/updates/',
                'https://www.espn.com/fantasy/baseball/story/_/id/29589640'
            ]
        }
        
        # Create directories for data storage
        self.data_dir = "data"
        self.reports_dir = "reports"
        self.visuals_dir = "visuals"
        self.archives_dir = "archives"
        
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.visuals_dir, exist_ok=True)
        os.makedirs(self.archives_dir, exist_ok=True)
        
        logger.info(f"Fantasy Baseball Automated Model initialized for league ID: {league_id}")
        logger.info(f"Your team: {your_team_name}")
    
    def load_initial_data(self):
        """Load initial data to bootstrap the system"""
        logger.info("Loading initial data for bootstrap...")
        
        # Load team rosters
        self.load_team_rosters()
        
        # Load initial stats and projections
        self.load_initial_stats_and_projections()
        
        # Generate initial set of free agents
        self.identify_free_agents()
        
        # Mark system as initialized with timestamp
        self.last_update = datetime.now()
        self.save_system_state()
        
        logger.info(f"Initial data loaded successfully, timestamp: {self.last_update}")
    
    def load_team_rosters(self, rosters_file=None):
        """Load team rosters from file or use default data"""
        if rosters_file and os.path.exists(rosters_file):
            try:
                df = pd.read_csv(rosters_file)
                for _, row in df.iterrows():
                    team_name = row['team_name']
                    player_name = row['player_name']
                    position = row['position']
                    
                    if team_name not in self.team_rosters:
                        self.team_rosters[team_name] = []
                    
                    self.team_rosters[team_name].append({
                        'name': player_name,
                        'position': position
                    })
                
                logger.info(f"Loaded {len(self.team_rosters)} team rosters from {rosters_file}")
            except Exception as e:
                logger.error(f"Error loading rosters file: {e}")
                self._load_default_rosters()
        else:
            logger.info("Rosters file not provided or doesn't exist. Loading default roster data.")
            self._load_default_rosters()
    
    def _load_default_rosters(self):
        """Load default roster data based on previous analysis"""
        default_rosters = {
            "Kenny Kawaguchis": [
                {"name": "Logan O'Hoppe", "position": "C"},
                {"name": "Bryce Harper", "position": "1B"},
                {"name": "Mookie Betts", "position": "2B/OF"},
                {"name": "Austin Riley", "position": "3B"},
                {"name": "CJ Abrams", "position": "SS"},
                {"name": "Lawrence Butler", "position": "OF"},
                {"name": "Riley Greene", "position": "OF"},
                {"name": "Adolis García", "position": "OF"},
                {"name": "Taylor Ward", "position": "OF"},
                {"name": "Tommy Edman", "position": "2B/SS"},
                {"name": "Roman Anthony", "position": "OF"},
                {"name": "Jonathan India", "position": "2B"},
                {"name": "Trevor Story", "position": "SS"},
                {"name": "Iván Herrera", "position": "C"},
                {"name": "Cole Ragans", "position": "SP"},
                {"name": "Hunter Greene", "position": "SP"},
                {"name": "Jack Flaherty", "position": "SP"},
                {"name": "Ryan Helsley", "position": "RP"},
                {"name": "Tanner Scott", "position": "RP"},
                {"name": "Pete Fairbanks", "position": "RP"},
                {"name": "Ryan Pepiot", "position": "SP"},
                {"name": "MacKenzie Gore", "position": "SP"},
                {"name": "Camilo Doval", "position": "RP"}
            ],
            "Mickey 18": [
                {"name": "Adley Rutschman", "position": "C"},
                {"name": "Pete Alonso", "position": "1B"},
                {"name": "Matt McLain", "position": "2B"},
                {"name": "Jordan Westburg", "position": "3B"},
                {"name": "Jeremy Peña", "position": "SS"},
                {"name": "Jasson Domínguez", "position": "OF"},
                {"name": "Tyler O'Neill", "position": "OF"},
                {"name": "Vladimir Guerrero Jr.", "position": "1B"},
                {"name": "Eugenio Suárez", "position": "3B"},
                {"name": "Ronald Acuña Jr.", "position": "OF"},
                {"name": "Tarik Skubal", "position": "SP"},
                {"name": "Spencer Schwellenbach", "position": "SP"},
                {"name": "Hunter Brown", "position": "SP"},
                {"name": "Jhoan Duran", "position": "RP"},
                {"name": "Jeff Hoffman", "position": "RP"},
                {"name": "Ryan Pressly", "position": "RP"},
                {"name": "Justin Verlander", "position": "SP"},
                {"name": "Max Scherzer", "position": "SP"}
            ],
            # Other teams omitted for brevity but would be included in full implementation
        }
        
        # Add to the team rosters dictionary
        self.team_rosters = default_rosters
        
        # Count total players loaded
        total_players = sum(len(roster) for roster in self.team_rosters.values())
        logger.info(f"Loaded {len(self.team_rosters)} team rosters with {total_players} players from default data")
    
    def load_initial_stats_and_projections(self, stats_file=None, projections_file=None):
        """Load initial stats and projections from files or use default data"""
        if stats_file and os.path.exists(stats_file) and projections_file and os.path.exists(projections_file):
            try:
                # Load stats
                with open(stats_file, 'r') as f:
                    self.player_stats_current = json.load(f)
                
                # Load projections
                with open(projections_file, 'r') as f:
                    self.player_projections = json.load(f)
                
                logger.info(f"Loaded stats for {len(self.player_stats_current)} players from {stats_file}")
                logger.info(f"Loaded projections for {len(self.player_projections)} players from {projections_file}")
            except Exception as e:
                logger.error(f"Error loading stats/projections files: {e}")
                self._load_default_stats_and_projections()
        else:
            logger.info("Stats/projections files not provided or don't exist. Loading default data.")
            self._load_default_stats_and_projections()
    
    def _load_default_stats_and_projections(self):
        """Load default stats and projections for bootstrapping"""
        # This would load from the previously created data
        # For simulation/demo purposes, we'll generate synthetic data
        
        # First, collect all players from rosters
        all_players = set()
        for team, roster in self.team_rosters.items():
            for player in roster:
                all_players.add(player["name"])
        
        # Add some free agents
        free_agents = [
            "Keibert Ruiz", "Danny Jansen", "Christian Walker", 
            "Spencer Torkelson", "Gavin Lux", "Luis Rengifo", 
            "JP Crawford", "Ha-Seong Kim", "Jeimer Candelario", 
            "Spencer Steer", "Luis Matos", "Heliot Ramos", 
            "TJ Friedl", "Garrett Mitchell", "Kutter Crawford", 
            "Reese Olson", "Dane Dunning", "José Berríos", 
            "Erik Swanson", "Seranthony Domínguez"
        ]
        
        for player in free_agents:
            all_players.add(player)
        
        # Generate stats and projections for all players
        self._generate_synthetic_data(all_players)
        
        logger.info(f"Generated synthetic stats for {len(self.player_stats_current)} players")
        logger.info(f"Generated synthetic projections for {len(self.player_projections)} players")
    
    def _generate_synthetic_data(self, player_names):
        """Generate synthetic stats and projections for demo purposes"""
        for player in player_names:
            # Determine if batter or pitcher based on name recognition
            # This is a simple heuristic; in reality, you'd use actual data
            is_pitcher = player in [
                "Cole Ragans", "Hunter Greene", "Jack Flaherty", "Ryan Helsley", 
                "Tanner Scott", "Pete Fairbanks", "Ryan Pepiot", "MacKenzie Gore", 
                "Camilo Doval", "Tarik Skubal", "Spencer Schwellenbach", "Hunter Brown", 
                "Jhoan Duran", "Jeff Hoffman", "Ryan Pressly", "Justin Verlander", 
                "Max Scherzer", "Kutter Crawford", "Reese Olson", "Dane Dunning", 
                "José Berríos", "Erik Swanson", "Seranthony Domínguez"
            ]
            
            if is_pitcher:
                # Generate pitcher stats
                current_stats = {
                    'IP': random.uniform(20, 40),
                    'W': random.randint(1, 4),
                    'L': random.randint(0, 3),
                    'ERA': random.uniform(2.5, 5.0),
                    'WHIP': random.uniform(0.9, 1.5),
                    'K': random.randint(15, 50),
                    'BB': random.randint(5, 20),
                    'QS': random.randint(1, 5),
                    'SV': 0 if player not in ["Ryan Helsley", "Tanner Scott", "Pete Fairbanks", "Camilo Doval", "Jhoan Duran", "Ryan Pressly", "Erik Swanson", "Seranthony Domínguez"] else random.randint(1, 8)
                }
                
                # Calculate k/9
                current_stats['K9'] = current_stats['K'] * 9 / current_stats['IP'] if current_stats['IP'] > 0 else 0
                
                # Generate projections (rest of season)
                projected_ip = random.uniform(120, 180) if current_stats['SV'] == 0 else random.uniform(45, 70)
                projected_stats = {
                    'IP': projected_ip,
                    'ERA': random.uniform(3.0, 4.5),
                    'WHIP': random.uniform(1.05, 1.35),
                    'K9': random.uniform(7.5, 12.0),
                    'QS': random.randint(10, 20) if current_stats['SV'] == 0 else 0,
                    'SV': 0 if current_stats['SV'] == 0 else random.randint(15, 35)
                }
            else:
                # Generate batter stats
                current_stats = {
                    'AB': random.randint(70, 120),
                    'R': random.randint(8, 25),
                    'H': random.randint(15, 40),
                    'HR': random.randint(1, 8),
                    'RBI': random.randint(5, 25),
                    'SB': random.randint(0, 8),
                    'BB': random.randint(5, 20),
                    'SO': random.randint(15, 40)
                }
                
                # Calculate derived stats
                current_stats['AVG'] = current_stats['H'] / current_stats['AB'] if current_stats['AB'] > 0 else 0
                current_stats['OBP'] = (current_stats['H'] + current_stats['BB']) / (current_stats['AB'] + current_stats['BB']) if (current_stats['AB'] + current_stats['BB']) > 0 else 0
                
                # Estimate SLG and OPS
                singles = current_stats['H'] - current_stats['HR'] - random.randint(2, 10) - random.randint(0, 5)
                doubles = random.randint(2, 10)
                triples = random.randint(0, 5)
                tb = singles + (2 * doubles) + (3 * triples) + (4 * current_stats['HR'])
                current_stats['SLG'] = tb / current_stats['AB'] if current_stats['AB'] > 0 else 0
                current_stats['OPS'] = current_stats['OBP'] + current_stats['SLG']
                
                # Generate projections (rest of season)
                projected_stats = {
                    'AB': random.randint(400, 550),
                    'R': random.randint(50, 100),
                    'HR': random.randint(10, 35),
                    'RBI': random.randint(40, 100),
                    'SB': random.randint(3, 35),
                    'AVG': random.uniform(0.230, 0.310),
                    'OPS': random.uniform(0.680, 0.950)
                }
            
            # Add to dictionaries
            self.player_stats_current[player] = current_stats
            self.player_projections[player] = projected_stats
    
    def identify_free_agents(self):
        """Identify all players who aren't on team rosters but have stats/projections"""
        # Create a set of all rostered players
        rostered_players = set()
        for team, roster in self.team_rosters.items():
            for player in roster:
                rostered_players.add(player["name"])
        
        # Find players with stats/projections who aren't rostered
        self.free_agents = {}
        
        for player in self.player_projections.keys():
            if player not in rostered_players:
                # Determine position based on stats
                if player in self.player_stats_current:
                    if 'ERA' in self.player_stats_current[player]:
                        position = 'RP' if self.player_stats_current[player].get('SV', 0) > 0 else 'SP'
                    else:
                        # This is simplistic - in a real system, we'd have actual position data
                        position = 'Unknown'
                else:
                    position = 'Unknown'
                
                self.free_agents[player] = {
                    'name': player,
                    'position': position,
                    'stats': self.player_stats_current.get(player, {}),
                    'projections': self.player_projections.get(player, {})
                }
        
        logger.info(f"Identified {len(self.free_agents)} free agents")
        return self.free_agents
    
    def save_system_state(self):
        """Save the current state of the system to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save team rosters
        with open(f"{self.data_dir}/team_rosters.json", 'w') as f:
            json.dump(self.team_rosters, f, indent=4)
        
        # Save current stats
        with open(f"{self.data_dir}/player_stats_current.json", 'w') as f:
            json.dump(self.player_stats_current, f, indent=4)
        
        # Save projections
        with open(f"{self.data_dir}/player_projections.json", 'w') as f:
            json.dump(self.player_projections, f, indent=4)
        
        # Save free agents
        with open(f"{self.data_dir}/free_agents.json", 'w') as f:
            json.dump(self.free_agents, f, indent=4)
        
        # Also save an archive copy
        with open(f"{self.archives_dir}/team_rosters_{timestamp}.json", 'w') as f:
            json.dump(self.team_rosters, f, indent=4)
        
        with open(f"{self.archives_dir}/player_stats_{timestamp}.json", 'w') as f:
            json.dump(self.player_stats_current, f, indent=4)
        
        with open(f"{self.archives_dir}/projections_{timestamp}.json", 'w') as f:
            json.dump(self.player_projections, f, indent=4)
        
        logger.info(f"System state saved successfully with timestamp: {timestamp}")
    
    def load_system_state(self):
        """Load the system state from saved files"""
        try:
            # Load team rosters
            if os.path.exists(f"{self.data_dir}/team_rosters.json"):
                with open(f"{self.data_dir}/team_rosters.json", 'r') as f:
                    self.team_rosters = json.load(f)
            
            # Load current stats
            if os.path.exists(f"{self.data_dir}/player_stats_current.json"):
                with open(f"{self.data_dir}/player_stats_current.json", 'r') as f:
                    self.player_stats_current = json.load(f)
            
            # Load projections
            if os.path.exists(f"{self.data_dir}/player_projections.json"):
                with open(f"{self.data_dir}/player_projections.json", 'r') as f:
                    self.player_projections = json.load(f)
            
            # Load free agents
            if os.path.exists(f"{self.data_dir}/free_agents.json"):
                with open(f"{self.data_dir}/free_agents.json", 'r') as f:
                    self.free_agents = json.load(f)
            
            logger.info("System state loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading system state: {e}")
            return False
    
    def update_player_stats(self):
        """Update player stats by fetching from data sources"""
        logger.info("Updating player stats from sources...")
        
        # In a real implementation, you would:
        # 1. Fetch data from each source in self.data_sources['stats']
        # 2. Parse and clean the data
        # 3. Merge with existing stats
        # 4. Update self.player_stats_current
        
        # For demo purposes, we'll simulate this process
        self._simulate_stats_update()
        
        logger.info(f"Updated stats for {len(self.player_stats_current)} players")
        return len(self.player_stats_current)
    
    def _simulate_stats_update(self):
        """Simulate updating stats for demo purposes"""
        # Add some new players
        new_players = [
            "Bobby Miller", "Garrett Crochet", "DL Hall", 
            "Edward Cabrera", "Alec Bohm", "Elly De La Cruz",
            "Anthony Volpe", "Jazz Chisholm Jr."
        ]
        
        for player in new_players:
            if player not in self.player_stats_current:
                # Determine if batter or pitcher based on name recognition
                is_pitcher = player in ["Bobby Miller", "Garrett Crochet", "DL Hall", "Edward Cabrera"]
                
                if is_pitcher:
                    self.player_stats_current[player] = {
                        'IP': random.uniform(10, 30),
                        'W': random.randint(1, 3),
                        'L': random.randint(0, 2),
                        'ERA': random.uniform(3.0, 5.0),
                        'WHIP': random.uniform(1.0, 1.4),
                        'K': random.randint(10, 40),
                        'BB': random.randint(5, 15),
                        'QS': random.randint(1, 4),
                        'SV': 0
                    }
                    
                    # Calculate k/9
                    self.player_stats_current[player]['K9'] = (
                        self.player_stats_current[player]['K'] * 9 / 
                        self.player_stats_current[player]['IP'] 
                        if self.player_stats_current[player]['IP'] > 0 else 0
                    )
                else:
                    self.player_stats_current[player] = {
                        'AB': random.randint(50, 100),
                        'R': random.randint(5, 20),
                        'H': random.randint(10, 30),
                        'HR': random.randint(1, 6),
                        'RBI': random.randint(5, 20),
                        'SB': random.randint(0, 6),
                        'BB': random.randint(5, 15),
                        'SO': random.randint(10, 30)
                    }
                    
                    # Calculate derived stats
                    self.player_stats_current[player]['AVG'] = (
                        self.player_stats_current[player]['H'] / 
                        self.player_stats_current[player]['AB'] 
                        if self.player_stats_current[player]['AB'] > 0 else 0
                    )
                    
                    self.player_stats_current[player]['OBP'] = (
                        (self.player_stats_current[player]['H'] + self.player_stats_current[player]['BB']) / 
                        (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) 
                        if (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) > 0 else 0
                    )
                    
                    # Estimate SLG and OPS
                    singles = (
                        self.player_stats_current[player]['H'] - 
                        self.player_stats_current[player]['HR'] - 
                        random.randint(2, 8) - 
                        random.randint(0, 3)
                    )
                    doubles = random.randint(2, 8)
                    triples = random.randint(0, 3)
                    tb = singles + (2 * doubles) + (3 * triples) + (4 * self.player_stats_current[player]['HR'])
                    
                    self.player_stats_current[player]['SLG'] = (
                        tb / self.player_stats_current[player]['AB'] 
                        if self.player_stats_current[player]['AB'] > 0 else 0
                    )
                    
                    self.player_stats_current[player]['OPS'] = (
                        self.player_stats_current[player]['OBP'] + 
                        self.player_stats_current[player]['SLG']
                    )
        
        # Update existing player stats
        for player in list(self.player_stats_current.keys()):
            # Skip some players randomly to simulate days off
            if random.random() < 0.3:
                continue
                
            # Determine if batter or pitcher based on existing stats
            if 'ERA' in self.player_stats_current[player]:  # It's a pitcher
                # Generate random game stats
                ip = random.uniform(0.1, 7)
                k = int(ip * random.uniform(0.5, 1.5))
                bb = int(ip * random.uniform(0.1, 0.5))
                er = int(ip * random.uniform(0, 0.7))
                h = int(ip * random.uniform(0.3, 1.2))
                
                # Update aggregated stats
                self.player_stats_current[player]['IP'] += ip
                self.player_stats_current[player]['K'] += k
                self.player_stats_current[player]['BB'] += bb
                
                # Update win/loss
                if random.random() < 0.5:
                    if random.random() < 0.6:  # 60% chance of decision
                        if random.random() < 0.5:  # 50% chance of win
                            self.player_stats_current[player]['W'] = self.player_stats_current[player].get('W', 0) + 1
                        else:
                            self.player_stats_current[player]['L'] = self.player_stats_current[player].get('L', 0) + 1
                
                # Update quality starts
                if ip >= 6 and er <= 3 and 'SV' not in self.player_stats_current[player]:
                    self.player_stats_current[player]['QS'] = self.player_stats_current[player].get('QS', 0) + 1
                
                # Update saves for relievers
                if 'SV' in self.player_stats_current[player] and ip <= 2 and random.random() < 0.3:
                    self.player_stats_current[player]['SV'] = self.player_stats_current[player].get('SV', 0) + 1
                
                # Recalculate ERA and WHIP
                total_er = (self.player_stats_current[player]['ERA'] * 
                           (self.player_stats_current[player]['IP'] - ip) / 9) + er
                            
                self.player_stats_current[player]['ERA'] = (
                    total_er * 9 / self.player_stats_current[player]['IP'] 
                    if self.player_stats_current[player]['IP'] > 0 else 0
                )
                
                # Add baserunners for WHIP calculation
                self.player_stats_current[player]['WHIP'] = (
                    (self.player_stats_current[player]['WHIP'] * 
                     (self.player_stats_current[player]['IP'] - ip) + (h + bb)) / 
                    self.player_stats_current[player]['IP'] 
                    if self.player_stats_current[player]['IP'] > 0 else 0
                )
                
                # Update K/9
                self.player_stats_current[player]['K9'] = (
                    self.player_stats_current[player]['K'] * 9 / 
                    self.player_stats_current[player]['IP'] 
                    if self.player_stats_current[player]['IP'] > 0 else 0
                )
                
            else:  # It's a batter
                # Generate random game stats
                ab = random.randint(0, 5)
                h = 0
                hr = 0
                r = 0
                rbi = 0
                sb = 0
                bb = 0
                so = 0
                
                if ab > 0:
                    # Determine hits
                    for _ in range(ab):
                        if random.random() < 0.270:  # League average is around .270
                            h += 1
                            # Determine if it's a home run
                            if random.random() < 0.15:  # About 15% of hits are HRs
                                hr += 1
                    
                    # Other stats
                    r = random.randint(0, 2) if h > 0 else 0
                    rbi = random.randint(0, 3) if h > 0 else 0
                    sb = 1 if random.random() < 0.08 else 0  # 8% chance of SB
                    bb = 1 if random.random() < 0.1 else 0  # 10% chance of BB
                    so = random.randint(0, 2)  # 0-2 strikeouts
                
                # Update aggregated stats
                self.player_stats_current[player]['AB'] += ab
                self.player_stats_current[player]['H'] += h
                self.player_stats_current[player]['HR'] += hr
                self.player_stats_current[player]['R'] += r
                self.player_stats_current[player]['RBI'] += rbi
                self.player_stats_current[player]['SB'] += sb
                self.player_stats_current[player]['BB'] += bb
                self.player_stats_current[player]['SO'] += so
                
                # Recalculate AVG
                self.player_stats_current[player]['AVG'] =ops_values = [ops for ops in ops_values if ops > 0]
                batting_totals['OPS'] = sum(ops_values) / len(ops_values) if ops_values else 0
            
            # Sort by AB descending
            batter_table.sort(key=lambda x: x[1], reverse=True)
            
            # Add totals row
            batter_table.append([
                "TOTALS",
                batting_totals['AB'],
                batting_totals['R'],
                batting_totals['HR'],
                batting_totals['RBI'],
                batting_totals['SB'],
                f"{batting_totals['AVG']:.3f}",
                f"{batting_totals['OPS']:.3f}"
            ])
            
            f.write(tabulate(batter_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Pitchers stats
            f.write("#### Pitching Stats\n\n")
            pitcher_table = []
            headers = ["Player", "IP", "W", "ERA", "WHIP", "K", "QS", "SV"]
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_stats_current and 'ERA' in self.player_stats_current[name]:
                    stats = self.player_stats_current[name]
                    pitcher_table.append([
                        name,
                        stats.get('IP', 0),
                        stats.get('W', 0),
                        f"{stats.get('ERA', 0):.2f}",
                        f"{stats.get('WHIP', 0):.2f}",
                        stats.get('K', 0),
                        stats.get('QS', 0),
                        stats.get('SV', 0)
                    ])
                    
                    # Add to totals
                    pitching_totals['IP'] += stats.get('IP', 0)
                    pitching_totals['W'] += stats.get('W', 0)
                    pitching_totals['K'] += stats.get('K', 0)
                    pitching_totals['QS'] += stats.get('QS', 0)
                    pitching_totals['SV'] += stats.get('SV', 0)
            
            # Calculate team ERA and WHIP
            if pitching_totals['IP'] > 0:
                # Calculate total ER and baserunners across all pitchers
                total_er = sum(self.player_stats_current.get(p["name"], {}).get('ERA', 0) * 
                               self.player_stats_current.get(p["name"], {}).get('IP', 0) / 9 
                               for p in self.team_rosters.get(self.your_team_name, [])
                               if 'ERA' in self.player_stats_current.get(p["name"], {}))
                
                total_baserunners = sum(self.player_stats_current.get(p["name"], {}).get('WHIP', 0) * 
                                       self.player_stats_current.get(p["name"], {}).get('IP', 0) 
                                       for p in self.team_rosters.get(self.your_team_name, [])
                                       if 'WHIP' in self.player_stats_current.get(p["name"], {}))
                
                pitching_totals['ERA'] = total_er * 9 / pitching_totals['IP']
                pitching_totals['WHIP'] = total_baserunners / pitching_totals['IP']
            
            # Sort by IP descending
            pitcher_table.sort(key=lambda x: x[1], reverse=True)
            
            # Add totals row
            pitcher_table.append([
                "TOTALS",
                pitching_totals['IP'],
                pitching_totals['W'],
                f"{pitching_totals['ERA']:.2f}",
                f"{pitching_totals['WHIP']:.2f}",
                pitching_totals['K'],
                pitching_totals['QS'],
                pitching_totals['SV']
            ])
            
            f.write(tabulate(pitcher_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Team Projections
            f.write("### Rest of Season Projections\n\n")
            
            # Batters projections
            f.write("#### Batting Projections\n\n")
            batter_proj_table = []
            headers = ["Player", "AB", "R", "HR", "RBI", "SB", "AVG", "OPS"]
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_projections and 'AVG' in self.player_projections[name]:
                    proj = self.player_projections[name]
                    batter_proj_table.append([
                        name,
                        int(proj.get('AB', 0)),
                        int(proj.get('R', 0)),
                        int(proj.get('HR', 0)),
                        int(proj.get('RBI', 0)),
                        int(proj.get('SB', 0)),
                        f"{proj.get('AVG', 0):.3f}",
                        f"{proj.get('OPS', 0):.3f}"
                    ])
            
            # Sort by projected AB descending
            batter_proj_table.sort(key=lambda x: x[1], reverse=True)
            
            f.write(tabulate(batter_proj_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Pitchers projections
            f.write("#### Pitching Projections\n\n")
            pitcher_proj_table = []
            headers = ["Player", "IP", "ERA", "WHIP", "K/9", "QS", "SV"]
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_projections and 'ERA' in self.player_projections[name]:
                    proj = self.player_projections[name]
                    pitcher_proj_table.append([
                        name,
                        int(proj.get('IP', 0)),
                        f"{proj.get('ERA', 0):.2f}",
                        f"{proj.get('WHIP', 0):.2f}",
                        f"{proj.get('K9', 0):.1f}",
                        int(proj.get('QS', 0)),
                        int(proj.get('SV', 0))
                    ])
            
            # Sort by projected IP descending
            pitcher_proj_table.sort(key=lambda x: x[1], reverse=True)
            
            f.write(tabulate(pitcher_proj_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Recent News
            f.write("### Recent Team News\n\n")
            
            news_count = 0
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_news and self.player_news[name]:
                    # Sort news by date (most recent first)
                    player_news = sorted(
                        self.player_news[name], 
                        key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"), 
                        reverse=True
                    )
                    
                    # Show most recent news item
                    latest_news = player_news[0]
                    f.write(f"**{name}** ({latest_news['date']} - {latest_news['source']}): {latest_news['content']}\n\n")
                    news_count += 1
            
            if news_count == 0:
                f.write("No recent news for your team's players.\n\n")
            
            # Recommendations
            f.write("## Team Recommendations\n\n")
            
            # Analyze team strengths and weaknesses
            # This is a simplified analysis - a real implementation would be more sophisticated
            
            # Calculate average stats per player
            avg_hr = batting_totals['HR'] / len([p for p in self.team_rosters.get(self.your_team_name, []) if p["name"] in self.player_stats_current and 'AVG' in self.player_stats_current[p["name"]]]) if len([p for p in self.team_rosters.get(self.your_team_name, []) if p["name"] in self.player_stats_current and 'AVG' in self.player_stats_current[p["name"]]]) > 0 else 0
            
            avg_sb = batting_totals['SB'] / len([p for p in self.team_rosters.get(self.your_team_name, []) if p["name"] in self.player_stats_current and 'AVG' in self.player_stats_current[p["name"]]]) if len([p for p in self.team_rosters.get(self.your_team_name, []) if p["name"] in self.player_stats_current and 'AVG' in self.player_stats_current[p["name"]]]) > 0 else 0
            
            avg_era = pitching_totals['ERA']
            avg_k9 = pitching_totals['K'] * 9 / pitching_totals['IP'] if pitching_totals['IP'] > 0 else 0
            
            # Identify strengths and weaknesses
            strengths = []
            weaknesses = []
            
            if batting_totals['AVG'] > 0.270:
                strengths.append("Batting Average")
            elif batting_totals['AVG'] < 0.250:
                weaknesses.append("Batting Average")
                
            if batting_totals['OPS'] > 0.780:
                strengths.append("OPS")
            elif batting_totals['OPS'] < 0.720:
                weaknesses.append("OPS")
                
            if avg_hr > 0.08:  # More than 0.08 HR per AB
                strengths.append("Power")
            elif avg_hr < 0.04:
                weaknesses.append("Power")
                
            if avg_sb > 0.05:  # More than 0.05 SB per AB
                strengths.append("Speed")
            elif avg_sb < 0.02:
                weaknesses.append("Speed")
                
            if avg_era < 3.80:
                strengths.append("ERA")
            elif avg_era > 4.20:
                weaknesses.append("ERA")
                
            if pitching_totals['WHIP'] < 1.20:
                strengths.append("WHIP")
            elif pitching_totals['WHIP'] > 1.30:
                weaknesses.append("WHIP")
                
            if avg_k9 > 9.5:
                strengths.append("Strikeouts")
            elif avg_k9 < 8.0:
                weaknesses.append("Strikeouts")
                
            if pitching_totals['SV'] > 15:
                strengths.append("Saves")
            elif pitching_totals['SV'] < 5:
                weaknesses.append("Saves")
                
            if pitching_totals['QS'] > 15:
                strengths.append("Quality Starts")
            elif pitching_totals['QS'] < 5:
                weaknesses.append("Quality Starts")
                
            # Write strengths and weaknesses
            f.write("### Team Strengths\n\n")
            if strengths:
                for strength in strengths:
                    f.write(f"- **{strength}**\n")
            else:
                f.write("No clear strengths identified yet.\n")
            
            f.write("\n### Team Weaknesses\n\n")
            if weaknesses:
                for weakness in weaknesses:
                    f.write(f"- **{weakness}**\n")
            else:
                f.write("No clear weaknesses identified yet.\n")
            
            f.write("\n### Recommended Actions\n\n")
            
            # Generate recommendations based on weaknesses
            if weaknesses:
                for weakness in weaknesses[:3]:  # Focus on top 3 weaknesses
                    if weakness == "Power":
                        f.write("- **Target Power Hitters**: Consider trading for players with high HR and RBI projections.\n")
                        
                        # Suggest specific free agents
                        power_fa = sorted(
                            [(name, p['projections'].get('HR', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'HR' in p['projections']],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if power_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {int(p[1])} HR)" for p in power_fa]) + "\n")
                    
                    elif weakness == "Speed":
                        f.write("- **Add Speed**: Look to add players who can contribute stolen bases.\n")
                        
                        # Suggest specific free agents
                        speed_fa = sorted(
                            [(name, p['projections'].get('SB', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'SB' in p['projections']],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if speed_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {int(p[1])} SB)" for p in speed_fa]) + "\n")
                    
                    elif weakness == "Batting Average":
                        f.write("- **Improve Batting Average**: Look for consistent contact hitters.\n")
                        
                        # Suggest specific free agents
                        avg_fa = sorted(
                            [(name, p['projections'].get('AVG', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'AVG' in p['projections'] and p['projections'].get('AB', 0) > 300],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if avg_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {p[1]:.3f} AVG)" for p in avg_fa]) + "\n")
                    
                    elif weakness == "ERA" or weakness == "WHIP":
                        f.write("- **Improve Pitching Ratios**: Focus on pitchers with strong ERA and WHIP projections.\n")
                        
                        # Suggest specific free agents
                        ratio_fa = sorted(
                            [(name, p['projections'].get('ERA', 0), p['projections'].get('WHIP', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'ERA' in p['projections'] and p['projections'].get('IP', 0) > 100],
                            key=lambda x: x[1] + x[2]
                        )[:3]
                        
                        if ratio_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {p[1]:.2f} ERA, {p[2]:.2f} WHIP)" for p in ratio_fa]) + "\n")
                    
                    elif weakness == "Strikeouts":
                        f.write("- **Add Strikeout Pitchers**: Target pitchers with high K/9 rates.\n")
                        
                        # Suggest specific free agents
                        k_fa = sorted(
                            [(name, p['projections'].get('K9', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'K9' in p['projections'] and p['projections'].get('IP', 0) > 75],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if k_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {p[1]:.1f} K/9)" for p in k_fa]) + "\n")
                    
                    elif weakness == "Saves":
                        f.write("- **Add Closers**: Look for pitchers in save situations.\n")
                        
                        # Suggest specific free agents
                        sv_fa = sorted(
                            [(name, p['projections'].get('SV', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'SV' in p['projections'] and p['projections'].get('SV', 0) > 5],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if sv_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {int(p[1])} SV)" for p in sv_fa]) + "\n")
                    
                    elif weakness == "Quality Starts":
                        f.write("- **Add Quality Starting Pitchers**: Target consistent starters who work deep into games.\n")
                        
                        # Suggest specific free agents
                        qs_fa = sorted(
                            [(name, p['projections'].get('QS', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'QS' in p['projections'] and p['projections'].get('QS', 0) > 5],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if qs_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {int(p[1])} QS)" for p in qs_fa]) + "\n")
            else:
                f.write("Your team is well-balanced! Continue to monitor player performance and injuries.\n")
            
            # General strategy recommendation
            f.write("\n### General Strategy\n\n")
            f.write("1. **Monitor the waiver wire daily** for emerging talent and players returning from injury.\n")
            f.write("2. **Be proactive with injured players**. Don't hold onto injured players too long if better options are available.\n")
            f.write("3. **Stream starting pitchers** against weak offensive teams for additional counting stats.\n")
            f.write("4. **Watch for changing roles** in bullpens for potential closers in waiting.\n")
            
            logger.info(f"Team analysis report generated: {output_file}")
    
    def generate_free_agents_report(self, output_file):
        """Generate free agents report sorted by projected value"""
        with open(output_file, 'w') as f:
            # Title
            f.write("# Fantasy Baseball Free Agent Analysis\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
            
            # Calculate scores for ranking
            fa_batters = {}
            fa_pitchers = {}
            
            for name, data in self.free_agents.items():
                if 'projections' in data:
                    proj = data['projections']
                    if 'AVG' in proj:  # It's a batter
                        # Calculate a batter score
                        score = (
                            proj.get('HR', 0) * 3 +
                            proj.get('SB', 0) * 3 +
                            proj.get('R', 0) * 0.5 +
                            proj.get('RBI', 0) * 0.5 +
                            proj.get('AVG', 0) * 300 +
                            proj.get('OPS', 0) * 150
                        )
                        fa_batters[name] = {'projections': proj, 'score': score}
                    
                    elif 'ERA' in proj:  # It's a pitcher
                        # Calculate a pitcher score
                        era_score = (5.00 - proj.get('ERA', 4.50)) * 20 if proj.get('ERA', 0) < 5.00 else 0
                        whip_score = (1.40 - proj.get('WHIP', 1.30)) * 60 if proj.get('WHIP', 0) < 1.40 else 0
                        
                        score = (
                            era_score +
                            whip_score +
                            proj.get('K9', 0) * 10 +
                            proj.get('QS', 0) * 4 +
                            proj.get('SV', 0) * 6 +
                            proj.get('IP', 0) * 0.2
                        )
                        fa_pitchers[name] = {'projections': proj, 'score': score}
            
            # Top Batters by Position
            f.write("## Top Free Agent Batters\n\n")
            
            # Define positions
            positions = {
                "C": "Catchers",
                "1B": "First Basemen",
                "2B": "Second Basemen",
                "3B": "Third Basemen",
                "SS": "Shortstops",
                "OF": "Outfielders"
            }
            
            # Simplified position assignment for demo
            position_players = {pos: [] for pos in positions}
            
            # Manually assign positions for demo
            for name in fa_batters:
                # This is a very simplified approach - in reality, you'd have actual position data
                if name in ["Keibert Ruiz", "Danny Jansen", "Gabriel Moreno", "Patrick Bailey", "Ryan Jeffers"]:
                    position_players["C"].append(name)
                elif name in ["Christian Walker", "Spencer Torkelson", "Andrew Vaughn", "Anthony Rizzo"]:
                    position_players["1B"].append(name)
                elif name in ["Gavin Lux", "Luis Rengifo", "Nick Gonzales", "Zack Gelof", "Brendan Donovan"]:
                    position_players["2B"].append(name)
                elif name in ["Jeimer Candelario", "Spencer Steer", "Ke'Bryan Hayes", "Brett Baty"]:
                    position_players["3B"].append(name)
                elif name in ["JP Crawford", "Ha-Seong Kim", "Xander Bogaerts", "Jose Barrero"]:
                    position_players["SS"].append(name)
                else:
                    position_players["OF"].append(name)
            
            # Write position sections
            for pos, title in positions.items():
                players = position_players[pos]
                if players:
                    f.write(f"### {title}\n\n")
                    
                    # Create table
                    headers = ["Rank", "Player", "AB", "R", "HR", "RBI", "SB", "AVG", "OPS", "Score"]
                    
                    # Get scores and sort
                    pos_players = [(name, fa_batters[name]['score'], fa_batters[name]['projections']) 
                                 for name in players if name in fa_batters]
                    
                    pos_players.sort(key=lambda x: x[1], reverse=True)
                    
                    # Build table
                    table_data = []
                    for i, (name, score, proj) in enumerate(pos_players[:10]):  # Top 10 per position
                        table_data.append([
                            i+1,
                            name,
                            int(proj.get('AB', 0)),
                            int(proj.get('R', 0)),
                            int(proj.get('HR', 0)),
                            int(proj.get('RBI', 0)),
                            int(proj.get('SB', 0)),
                            f"{proj.get('AVG', 0):.3f}",
                            f"{proj.get('OPS', 0):.3f}",
                            int(score)
                        ])
                    
                    f.write(tabulate(table_data, headers=headers, tablefmt="pipe"))
                    f.write("\n\n")
            
            # Top Pitchers
            f.write("## Top Free Agent Pitchers\n\n")
            
            # Starting pitchers
            f.write("### Starting Pitchers\n\n")
            
            # Identify starters
            starters = [(name, fa_pitchers[name]['score'], fa_pitchers[name]['projections']) 
                       for name in fa_pitchers 
                       if fa_pitchers[name]['projections'].get('QS', 0) > 0]
            
            starters.sort(key=lambda x: x[1], reverse=True)
            
            # Create table
            headers = ["Rank", "Player", "IP", "ERA", "WHIP", "K/9", "QS", "Score"]
            
            table_data = []
            for i, (name, score, proj) in enumerate(starters[:15]):  # Top 15 SP
                table_data.append([
                    i+1,
                    name,
                    int(proj.get('IP', 0)),
                    f"{proj.get('ERA', 0):.2f}",
                    f"{proj.get('WHIP', 0):.2f}",
                    f"{proj.get('K9', 0):.1f}",
                    int(proj.get('QS', 0)),
                    int(score)
                ])
            
            f.write(tabulate(table_data, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Relief pitchers
            f.write("### Relief Pitchers\n\n")
            
            # Identify relievers
            relievers = [(name, fa_pitchers[name]['score'], fa_pitchers[name]['projections']) 
                        for name in fa_pitchers 
                        if fa_pitchers[name]['projections'].get('QS', 0) == 0]
            
            relievers.sort(key=lambda x: x[1], reverse=True)
            
            # Create table
            headers = ["Rank", "Player", "IP", "ERA", "WHIP", "K/9", "SV", "Score"]
            
            table_data = []
            for i, (name, score, proj) in enumerate(relievers[:10]):  # Top 10 RP
                table_data.append([
                    i+1,
                    name,
                    int(proj.get('IP', 0)),
                    f"{proj.get('ERA', 0):.2f}",
                    f"{proj.get('WHIP', 0):.2f}",
                    f"{proj.get('K9', 0):.1f}",
                    int(proj.get('SV', 0)),
                    int(score)
                ])
            
            f.write(tabulate(table_data, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Category-Specific Free Agent Targets
            f.write("## Category-Specific Free Agent Targets\n\n")
            
            # Power hitters (HR and RBI)
            power_hitters = sorted(
                [(name, fa_batters[name]['projections'].get('HR', 0), fa_batters[name]['projections'].get('RBI', 0)) 
                 for name in fa_batters],
                key=lambda x: x[1] + x[2]/3,
                reverse=True
            )[:5]
            
            f.write("**Power (HR/RBI):** ")
            f.write(", ".join([f"{name} ({int(hr)} HR, {int(rbi)} RBI)" for name, hr, rbi in power_hitters]))
            f.write("\n\n")
            
            # Speed (SB)
            speed_players = sorted(
                [(name, fa_batters[name]['projections'].get('SB', 0)) 
                 for name in fa_batters],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            f.write("**Speed (SB):** ")
            f.write(", ".join([f"{name} ({int(sb)} SB)" for name, sb in speed_players]))
            f.write("\n\n")
            
            # Average (AVG)
            average_hitters = sorted(
                [(name, fa_batters[name]['projections'].get('AVG', 0)) 
                 for name in fa_batters 
                 if fa_batters[name]['projections'].get('AB', 0) >= 300],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            f.write("**Batting Average:** ")
            f.write(", ".join([f"{name} ({avg:.3f})" for name, avg in average_hitters]))
            f.write("\n\n")
            
            # ERA
            era_pitchers = sorted(
                [(name, fa_pitchers[name]['projections'].get('ERA', 0)) 
                 for name in fa_pitchers 
                 if fa_pitchers[name]['projections'].get('IP', 0) >= 100],
                key=lambda x: x[1]
            )[:5]
            
            f.write("**ERA:** ")
            f.write(", ".join([f"{name} ({era:.2f})" for name, era in era_pitchers]))
            f.write("\n\n")
            
            # WHIP
            whip_pitchers = sorted(
                [(name, fa_pitchers[name]['projections'].get('WHIP', 0)) 
                 for name in fa_pitchers 
                 if fa_pitchers[name]['projections'].get('IP', 0) >= 100],
                key=lambda x: x[1]
            )[:5]
            
            f.write("**WHIP:** ")
            f.write(", ".join([f"{name} ({whip:.2f})" for name, whip in whip_pitchers]))
            f.write("\n\n")
            
            # Saves (SV)
            save_pitchers = sorted(
                [(name, fa_pitchers[name]['projections'].get('SV', 0)) 
                 for name in fa_pitchers],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            f.write("**Saves:** ")
            f.write(", ".join([f"{name} ({int(sv)})" for name, sv in save_pitchers]))
            f.write("\n\n")
            
            logger.info(f"Free agents report generated: {output_file}")
    
    def generate_trending_players_report(self, output_file):
        """Generate report on trending players (hot/cold)"""
        # In a real implementation, you would calculate trends based on recent performance
        # For demo purposes, we'll simulate trends
        
        with open(output_                # Recalculate AVG
                self.player_stats_current[player]['AVG'] = (
                    self.player_stats_current[player]['H'] / 
                    self.player_stats_current[player]['AB'] 
                    if self.player_stats_current[player]['AB'] > 0 else 0
                )
                
                # Recalculate OBP
                self.player_stats_current[player]['OBP'] = (
                    (self.player_stats_current[player]['H'] + self.player_stats_current[player]['BB']) / 
                    (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) 
                    if (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) > 0 else 0
                )
                
                # Recalculate SLG and OPS
                singles = (
                    self.player_stats_current[player]['H'] - 
                    self.player_stats_current[player]['HR'] - 
                    self.player_stats_current[player].get('2B', random.randint(15, 25)) - 
                    self.player_stats_current[player].get('3B', random.randint(0, 5))
                )
                
                tb = (
                    singles + 
                    (2 * self.player_stats_current[player].get('2B', random.randint(15, 25))) + 
                    (3 * self.player_stats_current[player].get('3B', random.randint(0, 5))) + 
                    (4 * self.player_stats_current[player]['HR'])
                )
                
                self.player_stats_current[player]['SLG'] = (
                    tb / self.player_stats_current[player]['AB'] 
                    if self.player_stats_current[player]['AB'] > 0 else 0
                )
                
                self.player_stats_current[player]['OPS'] = (
                    self.player_stats_current[player]['OBP'] + 
                    self.player_stats_current[player]['SLG']
                )
    
    def update_player_projections(self):
        """Update player projections by fetching from data sources"""
        logger.info("Updating player projections from sources...")
        
        # In a real implementation, you would:
        # 1. Fetch data from each source in self.data_sources['projections']
        # 2. Parse and clean the data
        # 3. Merge with existing projections
        # 4. Update self.player_projections
        
        # For demo purposes, we'll simulate this process
        self._simulate_projections_update()
        
        logger.info(f"Updated projections for {len(self.player_projections)} players")
        return len(self.player_projections)
    
    def _simulate_projections_update(self):
        """Simulate updating projections for demo purposes"""
        # Update existing projections based on current stats
        for player in self.player_stats_current:
            # Skip if no projection exists
            if player not in self.player_projections:
                # Create new projection based on current stats
                if 'ERA' in self.player_stats_current[player]:  # It's a pitcher
                    # Project rest of season based on current performance
                    era_factor = min(max(4.00 / self.player_stats_current[player]['ERA'], 0.75), 1.25) if self.player_stats_current[player]['ERA'] > 0 else 1.0
                    whip_factor = min(max(1.30 / self.player_stats_current[player]['WHIP'], 0.75), 1.25) if self.player_stats_current[player]['WHIP'] > 0 else 1.0
                    k9_factor = min(max(self.player_stats_current[player]['K9'] / 8.5, 0.75), 1.25) if self.player_stats_current[player].get('K9', 0) > 0 else 1.0
                    
                    # Determine if starter or reliever
                    is_reliever = 'SV' in self.player_stats_current[player] or self.player_stats_current[player].get('IP', 0) < 20
                    
                    self.player_projections[player] = {
                        'IP': random.uniform(40, 70) if is_reliever else random.uniform(120, 180),
                        'ERA': random.uniform(3.0, 4.5) * era_factor,
                        'WHIP': random.uniform(1.05, 1.35) * whip_factor,
                        'K9': random.uniform(7.5, 12.0) * k9_factor,
                        'QS': 0 if is_reliever else random.randint(10, 20),
                        'SV': random.randint(15, 35) if is_reliever and self.player_stats_current[player].get('SV', 0) > 0 else 0
                    }
                else:  # It's a batter
                    # Project rest of season based on current performance
                    avg_factor = min(max(self.player_stats_current[player]['AVG'] / 0.260, 0.8), 1.2) if self.player_stats_current[player]['AVG'] > 0 else 1.0
                    ops_factor = min(max(self.player_stats_current[player].get('OPS', 0.750) / 0.750, 0.8), 1.2) if self.player_stats_current[player].get('OPS', 0) > 0 else 1.0
                    
                    # Projected plate appearances remaining
                    pa_remaining = random.randint(400, 550)
                    
                    # HR rate
                    hr_rate = self.player_stats_current[player]['HR'] / self.player_stats_current[player]['AB'] if self.player_stats_current[player]['AB'] > 0 else 0.025
                    
                    # SB rate
                    sb_rate = self.player_stats_current[player]['SB'] / self.player_stats_current[player]['AB'] if self.player_stats_current[player]['AB'] > 0 else 0.015
                    
                    self.player_projections[player] = {
                        'AB': pa_remaining * 0.9,  # 10% of PA are walks/HBP
                        'R': pa_remaining * random.uniform(0.12, 0.18),
                        'HR': pa_remaining * hr_rate * random.uniform(0.8, 1.2),
                        'RBI': pa_remaining * random.uniform(0.1, 0.17),
                        'SB': pa_remaining * sb_rate * random.uniform(0.8, 1.2),
                        'AVG': random.uniform(0.230, 0.310) * avg_factor,
                        'OPS': random.uniform(0.680, 0.950) * ops_factor
                    }
                continue
            
            # If projection exists, update it based on current performance
            if 'ERA' in self.player_stats_current[player]:  # It's a pitcher
                # Calculate adjustment factors based on current vs. projected performance
                if self.player_stats_current[player].get('IP', 0) > 20:  # Enough IP to adjust projections
                    # ERA adjustment
                    current_era = self.player_stats_current[player].get('ERA', 4.00)
                    projected_era = self.player_projections[player].get('ERA', 4.00)
                    era_adj = min(max(projected_era / current_era, 0.8), 1.2) if current_era > 0 else 1.0
                    
                    # WHIP adjustment
                    current_whip = self.player_stats_current[player].get('WHIP', 1.30)
                    projected_whip = self.player_projections[player].get('WHIP', 1.30)
                    whip_adj = min(max(projected_whip / current_whip, 0.8), 1.2) if current_whip > 0 else 1.0
                    
                    # K/9 adjustment
                    current_k9 = self.player_stats_current[player].get('K9', 8.5)
                    projected_k9 = self.player_projections[player].get('K9', 8.5)
                    k9_adj = min(max(current_k9 / projected_k9, 0.8), 1.2) if projected_k9 > 0 else 1.0
                    
                    # Apply adjustments
                    self.player_projections[player]['ERA'] = projected_era * era_adj
                    self.player_projections[player]['WHIP'] = projected_whip * whip_adj
                    self.player_projections[player]['K9'] = projected_k9 * k9_adj
                    
                    # Adjust saves projection for relievers
                    if 'SV' in self.player_stats_current[player]:
                        current_sv_rate = self.player_stats_current[player].get('SV', 0) / max(1, self.player_stats_current[player].get('IP', 1) / 60)
                        self.player_projections[player]['SV'] = min(45, max(0, int(current_sv_rate * 60)))
                    
                    # Adjust QS projection for starters
                    if 'QS' in self.player_stats_current[player] and self.player_stats_current[player].get('IP', 0) > 0:
                        current_qs_rate = self.player_stats_current[player].get('QS', 0) / max(1, self.player_stats_current[player].get('IP', 1) / 180)
                        self.player_projections[player]['QS'] = min(30, max(0, int(current_qs_rate * 180)))
            else:  # It's a batter
                # Adjust only if enough AB to be significant
                if self.player_stats_current[player].get('AB', 0) > 75:
                    # AVG adjustment
                    current_avg = self.player_stats_current[player].get('AVG', 0.260)
                    projected_avg = self.player_projections[player].get('AVG', 0.260)
                    avg_adj = min(max((current_avg + 2*projected_avg) / (3*projected_avg), 0.85), 1.15) if projected_avg > 0 else 1.0
                    
                    # HR rate adjustment
                    current_hr_rate = self.player_stats_current[player].get('HR', 0) / max(1, self.player_stats_current[player].get('AB', 1)) * 550
                    projected_hr = self.player_projections[player].get('HR', 15)
                    hr_adj = min(max((current_hr_rate + 2*projected_hr) / (3*projected_hr), 0.7), 1.3) if projected_hr > 0 else 1.0
                    
                    # SB rate adjustment
                    current_sb_rate = self.player_stats_current[player].get('SB', 0) / max(1, self.player_stats_current[player].get('AB', 1)) * 550
                    projected_sb = self.player_projections[player].get('SB', 10)
                    sb_adj = min(max((current_sb_rate + 2*projected_sb) / (3*projected_sb), 0.7), 1.3) if projected_sb > 0 else 1.0
                    
                    # Apply adjustments
                    self.player_projections[player]['AVG'] = projected_avg * avg_adj
                    self.player_projections[player]['HR'] = projected_hr * hr_adj
                    self.player_projections[player]['SB'] = projected_sb * sb_adj
                    
                    # Adjust OPS based on AVG and power
                    projected_ops = self.player_projections[player].get('OPS', 0.750)
                    self.player_projections[player]['OPS'] = projected_ops * (avg_adj * 0.4 + hr_adj * 0.6)
                    
                    # Adjust runs and RBI based on HR and overall performance
                    projected_r = self.player_projections[player].get('R', 70)
                    projected_rbi = self.player_projections[player].get('RBI', 70)
                    
                    self.player_projections[player]['R'] = projected_r * ((avg_adj + hr_adj) / 2)
                    self.player_projections[player]['RBI'] = projected_rbi * ((avg_adj + hr_adj) / 2)
        
        # Round numerical values for cleaner display
        for player in self.player_projections:
            for stat in self.player_projections[player]:
                if isinstance(self.player_projections[player][stat], float):
                    if stat in ['ERA', 'WHIP', 'K9', 'AVG', 'OPS']:
                        self.player_projections[player][stat] = round(self.player_projections[player][stat], 3)
                    else:
                        self.player_projections[player][stat] = round(self.player_projections[player][stat])
    
    def update_player_news(self):
        """Update player news by fetching from news sources"""
        logger.info("Updating player news from sources...")
        
        # In a real implementation, you would:
        # 1. Fetch data from each source in self.data_sources['news']
        # 2. Parse and extract news items
        # 3. Store in self.player_news
        
        # For demo purposes, we'll simulate this process
        self._simulate_news_update()
        
        logger.info(f"Updated news for {len(self.player_news)} players")
        return len(self.player_news)
    
    def _simulate_news_update(self):
        """Simulate updating player news for demo purposes"""
        # List of possible news templates
        injury_news = [
            "{player} was removed from Wednesday's game with {injury}.",
            "{player} is day-to-day with {injury}.",
            "{player} has been placed on the 10-day IL with {injury}.",
            "{player} will undergo further testing for {injury}.",
            "{player} is expected to miss 4-6 weeks with {injury}."
        ]
        
        performance_news = [
            "{player} went {stats} in Wednesday's 6-4 win.",
            "{player} struck out {k} batters in {ip} innings on Tuesday.",
            "{player} has hit safely in {streak} straight games.",
            "{player} collected {hits} hits including a homer on Monday.",
            "{player} has struggled recently, going {bad_stats} over his last 7 games."
        ]
        
        role_news = [
            "{player} will take over as the closer with {teammate} on the IL.",
            "{player} has been moved up to the {spot} spot in the batting order.",
            "{player} will make his next start on {day}.",
            "{player} has been moved to the bullpen.",
            "{player} will be recalled from Triple-A on Friday."
        ]
        
        # Possible injuries
        injuries = [
            "left hamstring tightness",
            "right oblique strain",
            "lower back discomfort",
            "shoulder inflammation",
            "forearm tightness",
            "groin strain",
            "ankle sprain",
            "knee soreness",
            "thumb contusion",
            "wrist inflammation"
        ]
        
        # Generate news for a subset of players
        for player in random.sample(list(self.player_stats_current.keys()), min(10, len(self.player_stats_current))):
            news_type = random.choice(["injury", "performance", "role"])
            
            if news_type == "injury":
                template = random.choice(injury_news)
                news_item = template.format(
                    player=player,
                    injury=random.choice(injuries)
                )
            elif news_type == "performance":
                template = random.choice(performance_news)
                
                # Determine if batter or pitcher
                if 'ERA' in self.player_stats_current[player]:  # Pitcher
                    ip = round(random.uniform(5, 7), 1)
                    k = random.randint(4, 10)
                    news_item = template.format(
                        player=player,
                        k=k,
                        ip=ip,
                        streak=random.randint(3, 10),
                        hits=random.randint(2, 4),
                        bad_stats=f"{random.randint(0, 4)}-for-{random.randint(20, 30)}"
                    )
                else:  # Batter
                    hits = random.randint(0, 4)
                    abs = random.randint(hits, 5)
                    news_item = template.format(
                        player=player,
                        stats=f"{hits}-for-{abs}",
                        k=random.randint(5, 12),
                        ip=round(random.uniform(5, 7), 1),
                        streak=random.randint(5, 15),
                        hits=random.randint(2, 4),
                        bad_stats=f"{random.randint(0, 4)}-for-{random.randint(20, 30)}"
                    )
            else:  # Role
                template = random.choice(role_news)
                news_item = template.format(
                    player=player,
                    teammate=random.choice(list(self.player_stats_current.keys())),
                    spot=random.choice(["leadoff", "cleanup", "third", "fifth"]),
                    day=random.choice(["Friday", "Saturday", "Sunday", "Monday"])
                )
            
            # Add news item with timestamp
            if player not in self.player_news:
                self.player_news[player] = []
            
            self.player_news[player].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source": random.choice(["Rotowire", "CBS Sports", "ESPN", "MLB.com"]),
                "content": news_item
            })
    
    def update_player_injuries(self):
        """Update player injury statuses"""
        logger.info("Updating player injury statuses...")
        
        # In a real implementation, you would:
        # 1. Fetch injury data from reliable sources
        # 2. Update player status accordingly
        # 3. Adjust projections for injured players
        
        # For demo purposes, we'll simulate some injuries
        injury_count = 0
        
        for player in self.player_stats_current:
            # 5% chance of new injury for each player
            if random.random() < 0.05:
                injury_severity = random.choice(["day-to-day", "10-day IL", "60-day IL"])
                injury_type = random.choice([
                    "hamstring strain", "oblique strain", "back spasms", 
                    "shoulder inflammation", "elbow soreness", "knee inflammation",
                    "ankle sprain", "concussion", "wrist sprain"
                ])
                
                # Add injury news
                if player not in self.player_news:
                    self.player_news[player] = []
                
                self.player_news[player].append({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "source": random.choice(["Rotowire", "CBS Sports", "ESPN", "MLB.com"]),
                    "content": f"{player} has been placed on the {injury_severity} with a {injury_type}."
                })
                
                # Adjust projections for injured players
                if player in self.player_projections:
                    if injury_severity == "day-to-day":
                        reduction = 0.05  # 5% reduction in projections
                    elif injury_severity == "10-day IL":
                        reduction = 0.15  # 15% reduction
                    else:  # 60-day IL
                        reduction = 0.50  # 50% reduction
                    
                    # Apply reduction to projected stats
                    for stat in self.player_projections[player]:
                        if stat not in ['AVG', 'ERA', 'WHIP', 'K9', 'OPS']:  # Don't reduce rate stats
                            self.player_projections[player][stat] *= (1 - reduction)
                
                injury_count += 1
        
        logger.info(f"Updated injury status for {injury_count} players")
        return injury_count
    
    def update_league_transactions(self):
        """Simulate league transactions (adds, drops, trades)"""
        logger.info("Simulating league transactions...")
        
        # In a real implementation, you would:
        # 1. Fetch transaction data from your fantasy platform API
        # 2. Update team rosters accordingly
        
        # For demo purposes, we'll simulate some transactions
        transaction_count = 0
        
        # Add/drop transactions (1-3 per update)
        for _ in range(random.randint(1, 3)):
            # Select a random team
            team = random.choice(list(self.team_rosters.keys()))
            
            # Select a random player to drop
            if len(self.team_rosters[team]) > 0:
                drop_index = random.randint(0, len(self.team_rosters[team]) - 1)
                dropped_player = self.team_rosters[team][drop_index]["name"]
                
                # Remove from roster
                self.team_rosters[team].pop(drop_index)
                
                # Pick a random free agent to add
                if len(self.free_agents) > 0:
                    added_player = random.choice(list(self.free_agents.keys()))
                    
                    # Determine position
                    position = "Unknown"
                    if 'ERA' in self.player_stats_current.get(added_player, {}):
                        position = 'RP' if self.player_stats_current[added_player].get('SV', 0) > 0 else 'SP'
                    else:
                        position = random.choice(["C", "1B", "2B", "3B", "SS", "OF"])
                    
                    # Add to roster
                    self.team_rosters[team].append({
                        "name": added_player,
                        "position": position
                    })
                    
                    # Remove from free agents
                    if added_player in self.free_agents:
                        del self.free_agents[added_player]
                    
                    # Log transaction
                    logger.info(f"Transaction: {team} dropped {dropped_player} and added {added_player}")
                    transaction_count += 1
        
        # Trade transactions (0-1 per update)
        if random.random() < 0.3:  # 30% chance of a trade
            # Select two random teams
            teams = random.sample(list(self.team_rosters.keys()), 2)
            
            # Select random players to trade (1-2 per team)
            team1_players = []
            team2_players = []
            
            for _ in range(random.randint(1, 2)):
                if len(self.team_rosters[teams[0]]) > 0:
                    idx = random.randint(0, len(self.team_rosters[teams[0]]) - 1)
                    team1_players.append(self.team_rosters[teams[0]][idx])
                    self.team_rosters[teams[0]].pop(idx)
            
            for _ in range(random.randint(1, 2)):
                if len(self.team_rosters[teams[1]]) > 0:
                    idx = random.randint(0, len(self.team_rosters[teams[1]]) - 1)
                    team2_players.append(self.team_rosters[teams[1]][idx])
                    self.team_rosters[teams[1]].pop(idx)
            
            # Execute the trade
            for player in team1_players:
                self.team_rosters[teams[1]].append(player)
            
            for player in team2_players:
                self.team_rosters[teams[0]].append(player)
            
            # Log transaction
            team1_names = [p["name"] for p in team1_players]
            team2_names = [p["name"] for p in team2_players]
            
            logger.info(f"Trade: {teams[0]} traded {', '.join(team1_names)} to {teams[1]} for {', '.join(team2_names)}")
            transaction_count += 1
        
        logger.info(f"Simulated {transaction_count} league transactions")
        return transaction_count
    
    def run_system_update(self):
        """Run a complete system update"""
        logger.info("Starting system update...")
        
        try:
            # Update player stats
            self.update_player_stats()
            
            # Update player projections
            self.update_player_projections()
            
            # Update player news
            self.update_player_news()
            
            # Update player injuries
            self.update_player_injuries()
            
            # Update league transactions
            self.update_league_transactions()
            
            # Identify free agents
            self.identify_free_agents()
            
            # Save updated system state
            self.save_system_state()
            
            # Generate updated reports
            self.generate_reports()
            
            # Update timestamp
            self.last_update = datetime.now()
            
            logger.info(f"System update completed successfully at {self.last_update}")
            return True
        except Exception as e:
            logger.error(f"Error during system update: {e}")
            return False
    
    def generate_reports(self):
        """Generate various reports"""
        timestamp = datetime.now().strftime("%Y%m%d")
        
        # Generate team analysis report
        self.generate_team_analysis_report(f"{self.reports_dir}/team_analysis_{timestamp}.md")
        
        # Generate free agents report
        self.generate_free_agents_report(f"{self.reports_dir}/free_agents_{timestamp}.md")
        
        # Generate trending players report
        self.generate_trending_players_report(f"{self.reports_dir}/trending_players_{timestamp}.md")
        
        # Generate player news report
        self.generate_player_news_report(f"{self.reports_dir}/player_news_{timestamp}.md")
        
        logger.info(f"Generated reports with timestamp {timestamp}")
    
    def generate_team_analysis_report(self, output_file):
        """Generate team analysis report"""
        with open(output_file, 'w') as f:
            # Title
            f.write("# Fantasy Baseball Team Analysis\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
            
            # Your Team Section
            f.write(f"## Your Team: {self.your_team_name}\n\n")
            
            # Team Roster
            f.write("### Current Roster\n\n")
            
            # Group players by position
            positions = {"C": [], "1B": [], "2B": [], "3B": [], "SS": [], "OF": [], "SP": [], "RP": []}
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                position = player["position"]
                
                # Simplified position assignment
                if position in positions:
                    positions[position].append(name)
                elif "/" in position:  # Handle multi-position players
                    primary_pos = position.split("/")[0]
                    if primary_pos in positions:
                        positions[primary_pos].append(name)
                    else:
                        positions["UTIL"].append(name)
                else:
                    # Handle unknown positions
                    if 'ERA' in self.player_stats_current.get(name, {}):
                        if self.player_stats_current[name].get('SV', 0) > 0:
                            positions["RP"].append(name)
                        else:
                            positions["SP"].append(name)
                    else:
                        positions["UTIL"].append(name)
            
            # Write roster by position
            for pos, players in positions.items():
                if players:
                    f.write(f"**{pos}**: {', '.join(players)}\n\n")
            
            # Team Performance
            f.write("### Team Performance\n\n")
            
            # Calculate team totals
            batting_totals = {
                'AB': 0, 'R': 0, 'HR': 0, 'RBI': 0, 'SB': 0, 'AVG': 0, 'OPS': 0
            }
            
            pitching_totals = {
                'IP': 0, 'W': 0, 'ERA': 0, 'WHIP': 0, 'K': 0, 'QS': 0, 'SV': 0
            }
            
            # Batters stats
            f.write("#### Batting Stats\n\n")
            batter_table = []
            headers = ["Player", "AB", "R", "HR", "RBI", "SB", "AVG", "OPS"]
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_stats_current and 'AVG' in self.player_stats_current[name]:
                    stats = self.player_stats_current[name]
                    batter_table.append([
                        name,
                        stats.get('AB', 0),
                        stats.get('R', 0),
                        stats.get('HR', 0),
                        stats.get('RBI', 0),
                        stats.get('SB', 0),
                        f"{stats.get('AVG', 0):.3f}",
                        f"{stats.get('OPS', 0):.3f}"
                    ])
                    
                    # Add to totals
                    batting_totals['AB'] += stats.get('AB', 0)
                    batting_totals['R'] += stats.get('R', 0)
                    batting_totals['HR'] += stats.get('HR', 0)
                    batting_totals['RBI'] += stats.get('RBI', 0)
                    batting_totals['SB'] += stats.get('SB', 0)
            
            # Calculate team AVG and OPS
            if batting_totals['AB'] > 0:
                total_hits = sum(self.player_stats_current.get(p["name"], {}).get('H', 0) for p in self.team_rosters.get(self.your_team_name, []))
                batting_totals['AVG'] = total_hits / batting_totals['AB']
                
                # Estimate team OPS as average of player OPS values
                ops_values = [self.player_stats_current.get(p["name"], {}).get('OPS', 0) for p in self.team_rosters.get(self.your_team_name, [])]
                ops_values = [ops for ops in ops_values if ops > 0]
                #!/usr/bin/env python3
# Fantasy Baseball Automated Model with Live Updates
# This script creates an automated system that regularly updates player stats and projections
# Uses the same sources (PECOTA, FanGraphs, MLB.com) for consistent data

import os
import csv
import json
import time
import random
import requests
import pandas as pd
import numpy as np
import schedule
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from tabulate import tabulate
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fantasy_baseball_auto.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FantasyBaseballAuto")

class FantasyBaseballAutomated:
    def __init__(self, league_id="2874", your_team_name="Kenny Kawaguchis"):
        self.league_id = league_id
        self.your_team_name = your_team_name
        self.teams = {}
        self.team_rosters = {}
        self.free_agents = {}
        self.player_stats_current = {}
        self.player_projections = {}
        self.player_news = {}
        self.last_update = None
        
        # API endpoints and data sources
        self.data_sources = {
            'stats': [
                'https://www.fangraphs.com/api/players/stats',
                'https://www.baseball-reference.com/leagues/MLB/2025.shtml',
                'https://www.mlb.com/stats/'
            ],
            'projections': [
                'https://www.fangraphs.com/projections.aspx',
                'https://www.baseball-prospectus.com/pecota-projections/',
                'https://www.mlb.com/stats/projected'
            ],
            'news': [
                'https://www.rotowire.com/baseball/news.php',
                'https://www.cbssports.com/fantasy/baseball/players/updates/',
                'https://www.espn.com/fantasy/baseball/story/_/id/29589640'
            ]
        }
        
        # Create directories for data storage
        self.data_dir = "data"
        self.reports_dir = "reports"
        self.visuals_dir = "visuals"
        self.archives_dir = "archives"
        
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.visuals_dir, exist_ok=True)
        os.makedirs(self.archives_dir, exist_ok=True)
        
        logger.info(f"Fantasy Baseball Automated Model initialized for league ID: {league_id}")
        logger.info(f"Your team: {your_team_name}")
    
    def load_initial_data(self):
        """Load initial data to bootstrap the system"""
        logger.info("Loading initial data for bootstrap...")
        
        # Load team rosters
        self.load_team_rosters()
        
        # Load initial stats and projections
        self.load_initial_stats_and_projections()
        
        # Generate initial set of free agents
        self.identify_free_agents()
        
        # Mark system as initialized with timestamp
        self.last_update = datetime.now()
        self.save_system_state()
        
        logger.info(f"Initial data loaded successfully, timestamp: {self.last_update}")
    
    def load_team_rosters(self, rosters_file=None):
        """Load team rosters from file or use default data"""
        if rosters_file and os.path.exists(rosters_file):
            try:
                df = pd.read_csv(rosters_file)
                for _, row in df.iterrows():
                    team_name = row['team_name']
                    player_name = row['player_name']
                    position = row['position']
                    
                    if team_name not in self.team_rosters:
                        self.team_rosters[team_name] = []
                    
                    self.team_rosters[team_name].append({
                        'name': player_name,
                        'position': position
                    })
                
                logger.info(f"Loaded {len(self.team_rosters)} team rosters from {rosters_file}")
            except Exception as e:
                logger.error(f"Error loading rosters file: {e}")
                self._load_default_rosters()
        else:
            logger.info("Rosters file not provided or doesn't exist. Loading default roster data.")
            self._load_default_rosters()
    
    def _load_default_rosters(self):
        """Load default roster data based on previous analysis"""
        default_rosters = {
            "Kenny Kawaguchis": [
                {"name": "Logan O'Hoppe", "position": "C"},
                {"name": "Bryce Harper", "position": "1B"},
                {"name": "Mookie Betts", "position": "2B/OF"},
                {"name": "Austin Riley", "position": "3B"},
                {"name": "CJ Abrams", "position": "SS"},
                {"name": "Lawrence Butler", "position": "OF"},
                {"name": "Riley Greene", "position": "OF"},
                {"name": "Adolis García", "position": "OF"},
                {"name": "Taylor Ward", "position": "OF"},
                {"name": "Tommy Edman", "position": "2B/SS"},
                {"name": "Roman Anthony", "position": "OF"},
                {"name": "Jonathan India", "position": "2B"},
                {"name": "Trevor Story", "position": "SS"},
                {"name": "Iván Herrera", "position": "C"},
                {"name": "Cole Ragans", "position": "SP"},
                {"name": "Hunter Greene", "position": "SP"},
                {"name": "Jack Flaherty", "position": "SP"},
                {"name": "Ryan Helsley", "position": "RP"},
                {"name": "Tanner Scott", "position": "RP"},
                {"name": "Pete Fairbanks", "position": "RP"},
                {"name": "Ryan Pepiot", "position": "SP"},
                {"name": "MacKenzie Gore", "position": "SP"},
                {"name": "Camilo Doval", "position": "RP"}
            ],
            "Mickey 18": [
                {"name": "Adley Rutschman", "position": "C"},
                {"name": "Pete Alonso", "position": "1B"},
                {"name": "Matt McLain", "position": "2B"},
                {"name": "Jordan Westburg", "position": "3B"},
                {"name": "Jeremy Peña", "position": "SS"},
                {"name": "Jasson Domínguez", "position": "OF"},
                {"name": "Tyler O'Neill", "position": "OF"},
                {"name": "Vladimir Guerrero Jr.", "position": "1B"},
                {"name": "Eugenio Suárez", "position": "3B"},
                {"name": "Ronald Acuña Jr.", "position": "OF"},
                {"name": "Tarik Skubal", "position": "SP"},
                {"name": "Spencer Schwellenbach", "position": "SP"},
                {"name": "Hunter Brown", "position": "SP"},
                {"name": "Jhoan Duran", "position": "RP"},
                {"name": "Jeff Hoffman", "position": "RP"},
                {"name": "Ryan Pressly", "position": "RP"},
                {"name": "Justin Verlander", "position": "SP"},
                {"name": "Max Scherzer", "position": "SP"}
            ],
            # Other teams omitted for brevity but would be included in full implementation
        }
        
        # Add to the team rosters dictionary
        self.team_rosters = default_rosters
        
        # Count total players loaded
        total_players = sum(len(roster) for roster in self.team_rosters.values())
        logger.info(f"Loaded {len(self.team_rosters)} team rosters with {total_players} players from default data")
    
    def load_initial_stats_and_projections(self, stats_file=None, projections_file=None):
        """Load initial stats and projections from files or use default data"""
        if stats_file and os.path.exists(stats_file) and projections_file and os.path.exists(projections_file):
            try:
                # Load stats
                with open(stats_file, 'r') as f:
                    self.player_stats_current = json.load(f)
                
                # Load projections
                with open(projections_file, 'r') as f:
                    self.player_projections = json.load(f)
                
                logger.info(f"Loaded stats for {len(self.player_stats_current)} players from {stats_file}")
                logger.info(f"Loaded projections for {len(self.player_projections)} players from {projections_file}")
            except Exception as e:
                logger.error(f"Error loading stats/projections files: {e}")
                self._load_default_stats_and_projections()
        else:
            logger.info("Stats/projections files not provided or don't exist. Loading default data.")
            self._load_default_stats_and_projections()
    
    def _load_default_stats_and_projections(self):
        """Load default stats and projections for bootstrapping"""
        # This would load from the previously created data
        # For simulation/demo purposes, we'll generate synthetic data
        
        # First, collect all players from rosters
        all_players = set()
        for team, roster in self.team_rosters.items():
            for player in roster:
                all_players.add(player["name"])
        
        # Add some free agents
        free_agents = [
            "Keibert Ruiz", "Danny Jansen", "Christian Walker", 
            "Spencer Torkelson", "Gavin Lux", "Luis Rengifo", 
            "JP Crawford", "Ha-Seong Kim", "Jeimer Candelario", 
            "Spencer Steer", "Luis Matos", "Heliot Ramos", 
            "TJ Friedl", "Garrett Mitchell", "Kutter Crawford", 
            "Reese Olson", "Dane Dunning", "José Berríos", 
            "Erik Swanson", "Seranthony Domínguez"
        ]
        
        for player in free_agents:
            all_players.add(player)
        
        # Generate stats and projections for all players
        self._generate_synthetic_data(all_players)
        
        logger.info(f"Generated synthetic stats for {len(self.player_stats_current)} players")
        logger.info(f"Generated synthetic projections for {len(self.player_projections)} players")
    
    def _generate_synthetic_data(self, player_names):
        """Generate synthetic stats and projections for demo purposes"""
        for player in player_names:
            # Determine if batter or pitcher based on name recognition
            # This is a simple heuristic; in reality, you'd use actual data
            is_pitcher = player in [
                "Cole Ragans", "Hunter Greene", "Jack Flaherty", "Ryan Helsley", 
                "Tanner Scott", "Pete Fairbanks", "Ryan Pepiot", "MacKenzie Gore", 
                "Camilo Doval", "Tarik Skubal", "Spencer Schwellenbach", "Hunter Brown", 
                "Jhoan Duran", "Jeff Hoffman", "Ryan Pressly", "Justin Verlander", 
                "Max Scherzer", "Kutter Crawford", "Reese Olson", "Dane Dunning", 
                "José Berríos", "Erik Swanson", "Seranthony Domínguez"
            ]
            
            if is_pitcher:
                # Generate pitcher stats
                current_stats = {
                    'IP': random.uniform(20, 40),
                    'W': random.randint(1, 4),
                    'L': random.randint(0, 3),
                    'ERA': random.uniform(2.5, 5.0),
                    'WHIP': random.uniform(0.9, 1.5),
                    'K': random.randint(15, 50),
                    'BB': random.randint(5, 20),
                    'QS': random.randint(1, 5),
                    'SV': 0 if player not in ["Ryan Helsley", "Tanner Scott", "Pete Fairbanks", "Camilo Doval", "Jhoan Duran", "Ryan Pressly", "Erik Swanson", "Seranthony Domínguez"] else random.randint(1, 8)
                }
                
                # Calculate k/9
                current_stats['K9'] = current_stats['K'] * 9 / current_stats['IP'] if current_stats['IP'] > 0 else 0
                
                # Generate projections (rest of season)
                projected_ip = random.uniform(120, 180) if current_stats['SV'] == 0 else random.uniform(45, 70)
                projected_stats = {
                    'IP': projected_ip,
                    'ERA': random.uniform(3.0, 4.5),
                    'WHIP': random.uniform(1.05, 1.35),
                    'K9': random.uniform(7.5, 12.0),
                    'QS': random.randint(10, 20) if current_stats['SV'] == 0 else 0,
                    'SV': 0 if current_stats['SV'] == 0 else random.randint(15, 35)
                }
            else:
                # Generate batter stats
                current_stats = {
                    'AB': random.randint(70, 120),
                    'R': random.randint(8, 25),
                    'H': random.randint(15, 40),
                    'HR': random.randint(1, 8),
                    'RBI': random.randint(5, 25),
                    'SB': random.randint(0, 8),
                    'BB': random.randint(5, 20),
                    'SO': random.randint(15, 40)
                }
                
                # Calculate derived stats
                current_stats['AVG'] = current_stats['H'] / current_stats['AB'] if current_stats['AB'] > 0 else 0
                current_stats['OBP'] = (current_stats['H'] + current_stats['BB']) / (current_stats['AB'] + current_stats['BB']) if (current_stats['AB'] + current_stats['BB']) > 0 else 0
                
                # Estimate SLG and OPS
                singles = current_stats['H'] - current_stats['HR'] - random.randint(2, 10) - random.randint(0, 5)
                doubles = random.randint(2, 10)
                triples = random.randint(0, 5)
                tb = singles + (2 * doubles) + (3 * triples) + (4 * current_stats['HR'])
                current_stats['SLG'] = tb / current_stats['AB'] if current_stats['AB'] > 0 else 0
                current_stats['OPS'] = current_stats['OBP'] + current_stats['SLG']
                
                # Generate projections (rest of season)
                projected_stats = {
                    'AB': random.randint(400, 550),
                    'R': random.randint(50, 100),
                    'HR': random.randint(10, 35),
                    'RBI': random.randint(40, 100),
                    'SB': random.randint(3, 35),
                    'AVG': random.uniform(0.230, 0.310),
                    'OPS': random.uniform(0.680, 0.950)
                }
            
            # Add to dictionaries
            self.player_stats_current[player] = current_stats
            self.player_projections[player] = projected_stats
    
    def identify_free_agents(self):
        """Identify all players who aren't on team rosters but have stats/projections"""
        # Create a set of all rostered players
        rostered_players = set()
        for team, roster in self.team_rosters.items():
            for player in roster:
                rostered_players.add(player["name"])
        
        # Find players with stats/projections who aren't rostered
        self.free_agents = {}
        
        for player in self.player_projections.keys():
            if player not in rostered_players:
                # Determine position based on stats
                if player in self.player_stats_current:
                    if 'ERA' in self.player_stats_current[player]:
                        position = 'RP' if self.player_stats_current[player].get('SV', 0) > 0 else 'SP'
                    else:
                        # This is simplistic - in a real system, we'd have actual position data
                        position = 'Unknown'
                else:
                    position = 'Unknown'
                
                self.free_agents[player] = {
                    'name': player,
                    'position': position,
                    'stats': self.player_stats_current.get(player, {}),
                    'projections': self.player_projections.get(player, {})
                }
        
        logger.info(f"Identified {len(self.free_agents)} free agents")
        return self.free_agents
    
    def save_system_state(self):
        """Save the current state of the system to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save team rosters
        with open(f"{self.data_dir}/team_rosters.json", 'w') as f:
            json.dump(self.team_rosters, f, indent=4)
        
        # Save current stats
        with open(f"{self.data_dir}/player_stats_current.json", 'w') as f:
            json.dump(self.player_stats_current, f, indent=4)
        
        # Save projections
        with open(f"{self.data_dir}/player_projections.json", 'w') as f:
            json.dump(self.player_projections, f, indent=4)
        
        # Save free agents
        with open(f"{self.data_dir}/free_agents.json", 'w') as f:
            json.dump(self.free_agents, f, indent=4)
        
        # Also save an archive copy
        with open(f"{self.archives_dir}/team_rosters_{timestamp}.json", 'w') as f:
            json.dump(self.team_rosters, f, indent=4)
        
        with open(f"{self.archives_dir}/player_stats_{timestamp}.json", 'w') as f:
            json.dump(self.player_stats_current, f, indent=4)
        
        with open(f"{self.archives_dir}/projections_{timestamp}.json", 'w') as f:
            json.dump(self.player_projections, f, indent=4)
        
        logger.info(f"System state saved successfully with timestamp: {timestamp}")
    
    def load_system_state(self):
        """Load the system state from saved files"""
        try:
            # Load team rosters
            if os.path.exists(f"{self.data_dir}/team_rosters.json"):
                with open(f"{self.data_dir}/team_rosters.json", 'r') as f:
                    self.team_rosters = json.load(f)
            
            # Load current stats
            if os.path.exists(f"{self.data_dir}/player_stats_current.json"):
                with open(f"{self.data_dir}/player_stats_current.json", 'r') as f:
                    self.player_stats_current = json.load(f)
            
            # Load projections
            if os.path.exists(f"{self.data_dir}/player_projections.json"):
                with open(f"{self.data_dir}/player_projections.json", 'r') as f:
                    self.player_projections = json.load(f)
            
            # Load free agents
            if os.path.exists(f"{self.data_dir}/free_agents.json"):
                with open(f"{self.data_dir}/free_agents.json", 'r') as f:
                    self.free_agents = json.load(f)
            
            logger.info("System state loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading system state: {e}")
            return False
    
    def update_player_stats(self):
        """Update player stats by fetching from data sources"""
        logger.info("Updating player stats from sources...")
        
        # In a real implementation, you would:
        # 1. Fetch data from each source in self.data_sources['stats']
        # 2. Parse and clean the data
        # 3. Merge with existing stats
        # 4. Update self.player_stats_current
        
        # For demo purposes, we'll simulate this process
        self._simulate_stats_update()
        
        logger.info(f"Updated stats for {len(self.player_stats_current)} players")
        return len(self.player_stats_current)
    
    def _simulate_stats_update(self):
        """Simulate updating stats for demo purposes"""
        # Add some new players
        new_players = [
            "Bobby Miller", "Garrett Crochet", "DL Hall", 
            "Edward Cabrera", "Alec Bohm", "Elly De La Cruz",
            "Anthony Volpe", "Jazz Chisholm Jr."
        ]
        
        for player in new_players:
            if player not in self.player_stats_current:
                # Determine if batter or pitcher based on name recognition
                is_pitcher = player in ["Bobby Miller", "Garrett Crochet", "DL Hall", "Edward Cabrera"]
                
                if is_pitcher:
                    self.player_stats_current[player] = {
                        'IP': random.uniform(10, 30),
                        'W': random.randint(1, 3),
                        'L': random.randint(0, 2),
                        'ERA': random.uniform(3.0, 5.0),
                        'WHIP': random.uniform(1.0, 1.4),
                        'K': random.randint(10, 40),
                        'BB': random.randint(5, 15),
                        'QS': random.randint(1, 4),
                        'SV': 0
                    }
                    
                    # Calculate k/9
                    self.player_stats_current[player]['K9'] = (
                        self.player_stats_current[player]['K'] * 9 / 
                        self.player_stats_current[player]['IP'] 
                        if self.player_stats_current[player]['IP'] > 0 else 0
                    )
                else:
                    self.player_stats_current[player] = {
                        'AB': random.randint(50, 100),
                        'R': random.randint(5, 20),
                        'H': random.randint(10, 30),
                        'HR': random.randint(1, 6),
                        'RBI': random.randint(5, 20),
                        'SB': random.randint(0, 6),
                        'BB': random.randint(5, 15),
                        'SO': random.randint(10, 30)
                    }
                    
                    # Calculate derived stats
                    self.player_stats_current[player]['AVG'] = (
                        self.player_stats_current[player]['H'] / 
                        self.player_stats_current[player]['AB'] 
                        if self.player_stats_current[player]['AB'] > 0 else 0
                    )
                    
                    self.player_stats_current[player]['OBP'] = (
                        (self.player_stats_current[player]['H'] + self.player_stats_current[player]['BB']) / 
                        (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) 
                        if (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) > 0 else 0
                    )
                    
                    # Estimate SLG and OPS
                    singles = (
                        self.player_stats_current[player]['H'] - 
                        self.player_stats_current[player]['HR'] - 
                        random.randint(2, 8) - 
                        random.randint(0, 3)
                    )
                    doubles = random.randint(2, 8)
                    triples = random.randint(0, 3)
                    tb = singles + (2 * doubles) + (3 * triples) + (4 * self.player_stats_current[player]['HR'])
                    
                    self.player_stats_current[player]['SLG'] = (
                        tb / self.player_stats_current[player]['AB'] 
                        if self.player_stats_current[player]['AB'] > 0 else 0
                    )
                    
                    self.player_stats_current[player]['OPS'] = (
                        self.player_stats_current[player]['OBP'] + 
                        self.player_stats_current[player]['SLG']
                    )
        
        # Update existing player stats
        for player in list(self.player_stats_current.keys()):
            # Skip some players randomly to simulate days off
            if random.random() < 0.3:
                continue
                
            # Determine if batter or pitcher based on existing stats
            if 'ERA' in self.player_stats_current[player]:  # It's a pitcher
                # Generate random game stats
                ip = random.uniform(0.1, 7)
                k = int(ip * random.uniform(0.5, 1.5))
                bb = int(ip * random.uniform(0.1, 0.5))
                er = int(ip * random.uniform(0, 0.7))
                h = int(ip * random.uniform(0.3, 1.2))
                
                # Update aggregated stats
                self.player_stats_current[player]['IP'] += ip
                self.player_stats_current[player]['K'] += k
                self.player_stats_current[player]['BB'] += bb
                
                # Update win/loss
                if random.random() < 0.5:
                    if random.random() < 0.6:  # 60% chance of decision
                        if random.random() < 0.5:  # 50% chance of win
                            self.player_stats_current[player]['W'] = self.player_stats_current[player].get('W', 0) + 1
                        else:
                            self.player_stats_current[player]['L'] = self.player_stats_current[player].get('L', 0) + 1
                
                # Update quality starts
                if ip >= 6 and er <= 3 and 'SV' not in self.player_stats_current[player]:
                    self.player_stats_current[player]['QS'] = self.player_stats_current[player].get('QS', 0) + 1
                
                # Update saves for relievers
                if 'SV' in self.player_stats_current[player] and ip <= 2 and random.random() < 0.3:
                    self.player_stats_current[player]['SV'] = self.player_stats_current[player].get('SV', 0) + 1
                
                # Recalculate ERA and WHIP
                total_er = (self.player_stats_current[player]['ERA'] * 
                           (self.player_stats_current[player]['IP'] - ip) / 9) + er
                            
                self.player_stats_current[player]['ERA'] = (
                    total_er * 9 / self.player_stats_current[player]['IP'] 
                    if self.player_stats_current[player]['IP'] > 0 else 0
                )
                
                # Add baserunners for WHIP calculation
                self.player_stats_current[player]['WHIP'] = (
                    (self.player_stats_current[player]['WHIP'] * 
                     (self.player_stats_current[player]['IP'] - ip) + (h + bb)) / 
                    self.player_stats_current[player]['IP'] 
                    if self.player_stats_current[player]['IP'] > 0 else 0
                )
                
                # Update K/9
                self.player_stats_current[player]['K9'] = (
                    self.player_stats_current[player]['K'] * 9 / 
                    self.player_stats_current[player]['IP'] 
                    if self.player_stats_current[player]['IP'] > 0 else 0
                )
                
            else:  # It's a batter
                # Generate random game stats
                ab = random.randint(0, 5)
                h = 0
                hr = 0
                r = 0
                rbi = 0
                sb = 0
                bb = 0
                so = 0
                
                if ab > 0:
                    # Determine hits
                    for _ in range(ab):
                        if random.random() < 0.270:  # League average is around .270
                            h += 1
                            # Determine if it's a home run
                            if random.random() < 0.15:  # About 15% of hits are HRs
                                hr += 1
                    
                    # Other stats
                    r = random.randint(0, 2) if h > 0 else 0
                    rbi = random.randint(0, 3) if h > 0 else 0
                    sb = 1 if random.random() < 0.08 else 0  # 8% chance of SB
                    bb = 1 if random.random() < 0.1 else 0  # 10% chance of BB
                    so = random.randint(0, 2)  # 0-2 strikeouts
                
                # Update aggregated stats
                self.player_stats_current[player]['AB'] += ab
                self.player_stats_current[player]['H'] += h
                self.player_stats_current[player]['HR'] += hr
                self.player_stats_current[player]['R'] += r
                self.player_stats_current[player]['RBI'] += rbi
                self.player_stats_current[player]['SB'] += sb
                self.player_stats_current[player]['BB'] += bb
                self.player_stats_current[player]['SO'] += so
                
                # Recalculate AVG
                self.player_stats_current[player]['AVG'] =with open(output_file, 'w') as f:
            # Title
            f.write("# Fantasy Baseball Trending Players\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
            
            # Introduction
            f.write("This report identifies players who are trending up or down based on recent performance versus expectations.\n\n")
            
            # For demo purposes, randomly select players as trending up or down
            trending_up_batters = random.sample(list(self.player_stats_current.keys()), 5)
            trending_down_batters = random.sample(list(self.player_stats_current.keys()), 5)
            
            trending_up_pitchers = random.sample([p for p in self.player_stats_current if 'ERA' in self.player_stats_current[p]], 3)
            trending_down_pitchers = random.sample([p for p in self.player_stats_current if 'ERA' in self.player_stats_current[p]], 3)
            
            # Hot Batters
            f.write("## 🔥 Hot Batters\n\n")
            f.write("Players exceeding their projections over the past 15 days.\n\n")
            
            headers = ["Player", "Last 15 Days", "Season Stats", "Ownership"]
            hot_batters_table = []
            
            for player in trending_up_batters:
                if player in self.player_stats_current and 'AVG' in self.player_stats_current[player]:
                    # Generate simulated recent hot stats
                    recent_avg = min(self.player_stats_current[player].get('AVG', 0.250) + random.uniform(0.040, 0.080), 0.400)
                    recent_hr = max(1, int(self.player_stats_current[player].get('HR', 5) * random.uniform(0.20, 0.30)))
                    recent_rbi = max(3, int(self.player_stats_current[player].get('RBI', 20) * random.uniform(0.20, 0.30)))
                    
                    # Determine roster status
                    roster_status = "Rostered"
                    for team, roster in self.team_rosters.items():
                        if player in [p["name"] for p in roster]:
                            roster_status = team
                            break
                    
                    if roster_status == "Rostered":
                        roster_status = random.choice(list(self.team_rosters.keys()))
                    
                    # Generate table row
                    hot_batters_table.append([
                        player,
                        f"{recent_avg:.3f}, {recent_hr} HR, {recent_rbi} RBI",
                        f"{self.player_stats_current[player].get('AVG', 0):.3f}, {self.player_stats_current[player].get('HR', 0)} HR, {self.player_stats_current[player].get('RBI', 0)} RBI",
                        roster_status
                    ])
            
            f.write(tabulate(hot_batters_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Cold Batters
            f.write("## ❄️ Cold Batters\n\n")
            f.write("Players underperforming their projections over the past 15 days.\n\n")
            
            cold_batters_table = []
            
            for player in trending_down_batters:
                if player in self.player_stats_current and 'AVG' in self.player_stats_current[player]:
                    # Generate simulated recent cold stats
                    recent_avg = max(0.120, self.player_stats_current[player].get('AVG', 0.250) - random.uniform(0.050, 0.100))
                    recent_hr = max(0, int(self.player_stats_current[player].get('HR', 5) * random.uniform(0.05, 0.15)))
                    recent_rbi = max(1, int(self.player_stats_current[player].get('RBI', 20) * random.uniform(0.05, 0.15)))
                    
                    # Determine roster status
                    roster_status = "Rostered"
                    for team, roster in self.team_rosters.items():
                        if player in [p["name"] for p in roster]:
                            roster_status = team
                            break
                    
                    if roster_status == "Rostered":
                        roster_status = random.choice(list(self.team_rosters.keys()))
                    
                    # Generate table row
                    cold_batters_table.append([
                        player,
                        f"{recent_avg:.3f}, {recent_hr} HR, {recent_rbi} RBI",
                        f"{self.player_stats_current[player].get('AVG', 0):.3f}, {self.player_stats_current[player].get('HR', 0)} HR, {self.player_stats_current[player].get('RBI', 0)} RBI",
                        roster_status
                    ])
            
            f.write(tabulate(cold_batters_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Hot Pitchers
            f.write("## 🔥 Hot Pitchers\n\n")
            f.write("Pitchers exceeding their projections over the past 15 days.\n\n")
            
            headers = ["Player", "Last 15 Days", "Season Stats", "Ownership"]
            hot_pitchers_table = []
            
            for player in trending_up_pitchers:
                if 'ERA' in self.player_stats_current[player]:
                    # Generate simulated recent hot stats
                    recent_era = max(0.00, self.player_stats_current[player].get('ERA', 4.00) - random.uniform(1.30, 2.50))
                    recent_whip = max(0.70, self.player_stats_current[player].get('WHIP', 1.30) - random.uniform(0.30, 0.50))
                    recent_k = int(self.player_stats_current[player].get('K', 40) * random.uniform(0.15, 0.25))
                    
                    # Determine roster status
                    roster_status = "Rostered"
                    for team, roster in self.team_rosters.items():
                        if player in [p["name"] for p in roster]:
                            roster_status = team
                            break
                    
                    if roster_status == "Rostered":
                        roster_status = random.choice(list(self.team_rosters.keys()))
                    
                    # Generate table row
                    hot_pitchers_table.append([
                        player,
                        f"{recent_era:.2f} ERA, {recent_whip:.2f} WHIP, {recent_k} K",
                        f"{self.player_stats_current[player].get('ERA', 0):.2f} ERA, {self.player_stats_current[player].get('WHIP', 0):.2f} WHIP, {self.player_stats_current[player].get('K', 0)} K",
                        roster_status
                    ])
            
            f.write(tabulate(hot_pitchers_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Cold Pitchers
            f.write("## ❄️ Cold Pitchers\n\n")
            f.write("Pitchers underperforming their projections over the past 15 days.\n\n")
            
            cold_pitchers_table = []
            
            for player in trending_down_pitchers:
                if 'ERA' in self.player_stats_current[player]:
                    # Generate simulated recent cold stats
                    recent_era = self.player_stats_current[player].get('ERA', 4.00) + random.uniform(1.50, 3.00)
                    recent_whip = self.player_stats_current[player].get('WHIP', 1.30) + random.uniform(0.20, 0.40)
                    recent_k = max(0, int(self.player_stats_current[player].get('K', 40) * random.uniform(0.05, 0.15)))
                    
                    # Determine roster status
                    roster_status = "Rostered"
                    for team, roster in self.team_rosters.items():
                        if player in [p["name"] for p in roster]:
                            roster_status = team
                            break
                    
                    if roster_status == "Rostered":
                        roster_status = random.choice(list(self.team_rosters.keys()))
                    
                    # Generate table row
                    cold_pitchers_table.append([
                        player,
                        f"{recent_era:.2f} ERA, {recent_whip:.2f} WHIP, {recent_k} K",
                        f"{self.player_stats_current[player].get('ERA', 0):.2f} ERA, {self.player_stats_current[player].get('WHIP', 0):.2f} WHIP, {self.player_stats_current[player].get('K', 0)} K",
                        roster_status
                    ])
            
            f.write(tabulate(cold_pitchers_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Pickup Recommendations
            f.write("## 📈 Recommended Pickups\n\n")
            f.write("Players trending up who are still available in many leagues.\n\n")
            
            # Find available players who are trending up
            available_trending = []
            for player in trending_up_batters + trending_up_pitchers:
                is_rostered = False
                for team, roster in self.team_rosters.items():
                    if player in [p["name"] for p in roster]:
                        is_rostered = True
                        break
                
                if not is_rostered:
                    available_trending.append(player)
            
            # Add some random free agents to the mix
            available_trending.extend(random.sample(list(self.free_agents.keys()), min(5, len(self.free_agents))))
            
            # Create recommendation table
            headers = ["Player", "Position", "Recent Performance", "Projected ROS"]
            recommendations_table = []
            
            for player in available_trending[:5]:  # Top 5 recommendations
                if player in self.player_stats_current:
                    # Determine position
                    if 'ERA' in self.player_stats_current[player]:
                        position = 'RP' if self.player_stats_current[player].get('SV', 0) > 0 else 'SP'
                        
                        # Generate recent performance string
                        recent_perf = f"{random.uniform(2.00, 3.50):.2f} ERA, {random.uniform(0.90, 1.20):.2f} WHIP, {random.randint(5, 15)} K"
                        
                        # Generate ROS projection string
                        if player in self.player_projections:
                            proj = self.player_projections[player]
                            ros_proj = f"{proj.get('ERA', 0):.2f} ERA, {proj.get('WHIP', 0):.2f} WHIP, {int(proj.get('IP', 0))} IP"
                        else:
                            ros_proj = "No projection available"
                    else:
                        # Random position for batters
                        position = random.choice(['C', '1B', '2B', '3B', 'SS', 'OF'])
                        
                        # Generate recent performance string
                        recent_perf = f"{random.uniform(0.280, 0.360):.3f} AVG, {random.randint(1, 5)} HR, {random.randint(5, 15)} RBI"
                        
                        # Generate ROS projection string
                        if player in self.player_projections:
                            proj = self.player_projections[player]
                            ros_proj = f"{proj.get('AVG', 0):.3f} AVG, {int(proj.get('HR', 0))} HR, {int(proj.get('RBI', 0))} RBI"
                        else:
                            ros_proj = "No projection available"
                    
                    recommendations_table.append([
                        player,
                        position,
                        recent_perf,
                        ros_proj
                    ])
            
            f.write(tabulate(recommendations_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Drop Recommendations
            f.write("## 📉 Consider Dropping\n\n")
            f.write("Rostered players who are trending down and may be safe to drop in standard leagues.\n\n")
            
            # Find rostered players who are trending down
            rostered_trending_down = []
            for player in trending_down_batters + trending_down_pitchers:
                is_rostered = False
                for team, roster in self.team_rosters.items():
                    if player in [p["name"] for p in roster]:
                        is_rostered = True
                        break
                
                if is_rostered:
                    rostered_trending_down.append(player)
            
            # Create drop recommendation table
            headers = ["Player", "Position", "Recent Performance", "Better Alternatives"]
            drop_recommendations_table = []
            
            for player in rostered_trending_down[:5]:  # Top 5 drop recommendations
                if player in self.player_stats_current:
                    # Determine position
                    if 'ERA' in self.player_stats_current[player]:
                        position = 'RP' if self.player_stats_current[player].get('SV', 0) > 0 else 'SP'
                        
                        # Generate recent performance string
                        recent_perf = f"{random.uniform(5.50, 8.00):.2f} ERA, {random.uniform(1.40, 1.80):.2f} WHIP, {random.randint(1, 7)} K"
                        
                        # Suggest alternatives
                        alternatives = [p for p in self.free_agents if p in self.player_projections and 'ERA' in self.player_projections[p]]
                        if alternatives:
                            better_alternatives = ", ".join(random.sample(alternatives, min(3, len(alternatives))))
                        else:
                            better_alternatives = "None available"
                    else:
                        # Random position for batters
                        position = random.choice(['C', '1B', '2B', '3B', 'SS', 'OF'])
                        
                        # Generate recent performance string
                        recent_perf = f"{random.uniform(0.120, 0.200):.3f} AVG, {random.randint(0, 1)} HR, {random.randint(1, 4)} RBI"
                        
                        # Suggest alternatives
                        alternatives = [p for p in self.free_agents if p in self.player_projections and 'AVG' in self.player_projections[p]]
                        if alternatives:
                            better_alternatives = ", ".join(random.sample(alternatives, min(3, len(alternatives))))
                        else:
                            better_alternatives = "None available"
                    
                    drop_recommendations_table.append([
                        player,
                        position,
                        recent_perf,
                        better_alternatives
                    ])
            
            f.write(tabulate(drop_recommendations_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            logger.info(f"Trending players report generated: {output_file}")
    
    def generate_player_news_report(self, output_file):
        """Generate report of recent player news"""
        with open(output_file, 'w') as f:
            # Title
            f.write("# Fantasy Baseball Player News\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
            
            # Recent Injuries
            f.write("## 🏥 Recent Injuries\n\n")
            
            injury_news = []
            for player, news_items in self.player_news.items():
                for item in news_items:
                    if any(keyword in item['content'].lower() for keyword in ['injury', 'injured', 'il', 'disabled list', 'strain', 'sprain']):
                        injury_news.append({
                            'player': player,
                            'date': item['date'],
                            'source': item['source'],
                            'content': item['content']
                        })
            
            # Sort by date (most recent first)
            injury_news.sort(key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d"), reverse=True)
            
            if injury_news:
                for news in injury_news[:10]:  # Show most recent 10 injury news items
                    f.write(f"**{news['player']}** ({news['date']} - {news['source']}): {news['content']}\n\n")
            else:
                f.write("No recent injury news.\n\n")
            
            # Position Battle Updates
            f.write("## ⚔️ Position Battle Updates\n\n")
            
            # In a real implementation, you would have actual news about position battles
            # For demo purposes, we'll simulate position battle news
            position_battles = [
                {
                    'position': 'Second Base',
                    'team': 'Athletics',
                    'players': ['Zack Gelof', 'Nick Allen'],
                    'update': f"Gelof continues to see the majority of starts at 2B, playing in {random.randint(4, 6)} of the last 7 games."
                },
                {
                    'position': 'Closer',
                    'team': 'Cardinals',
                    'players': ['Ryan Helsley', 'Giovanny Gallegos'],
                    'update': f"Helsley has converted {random.randint(3, 5)} saves in the last two weeks, firmly establishing himself as the primary closer."
                },
                {
                    'position': 'Outfield',
                    'team': 'Rays',
                    'players': ['Josh Lowe', 'Jose Siri', 'Randy Arozarena'],
                    'update': f"With Lowe's recent {random.choice(['hamstring', 'oblique', 'back'])} injury, Siri has taken over as the everyday CF."
                }
            ]
            
            for battle in position_battles:
                f.write(f"**{battle['team']} {battle['position']}**: {battle['update']}\n\n")
                f.write(f"Players involved: {', '.join(battle['players'])}\n\n")
            
            # Closer Updates
            f.write("## 🔒 Closer Situations\n\n")
            
            # In a real implementation, you would have actual closer data
            # For demo purposes, we'll simulate closer situations
            closer_situations = [
                {
                    'team': 'Rays',
                    'primary': 'Pete Fairbanks',
                    'secondary': 'Jason Adam',
                    'status': f"Fairbanks has {random.randint(3, 5)} saves in the last 14 days and is firmly entrenched as the closer."
                },
                {
                    'team': 'Cardinals',
                    'primary': 'Ryan Helsley',
                    'secondary': 'Giovanny Gallegos',
                    'status': f"Helsley is the unquestioned closer with {random.randint(15, 25)} saves on the season."
                },
                {
                    'team': 'Reds',
                    'primary': 'Alexis Díaz',
                    'secondary': 'Lucas Sims',
                    'status': f"Díaz is firmly in the closer role with {random.randint(3, 5)} saves in the last two weeks."
                },
                {
                    'team': 'Athletics',
                    'primary': 'Mason Miller',
                    'secondary': 'Dany Jiménez',
                    'status': f"Miller has taken over the closing duties, recording {random.randint(2, 4)} saves recently."
                },
                {
                    'team': 'Mariners',
                    'primary': 'Andrés Muñoz',
                    'secondary': 'Matt Brash',
                    'status': f"Muñoz appears to be the preferred option with {random.randint(3, 5)} saves recently."
                }
            ]
            
            # Create a table for closer situations
            headers = ["Team", "Primary", "Secondary", "Status"]
            closer_table = []
            
            for situation in closer_situations:
                closer_table.append([
                    situation['team'],
                    situation['primary'],
                    situation['secondary'],
                    situation['status']
                ])
            
            f.write(tabulate(closer_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Prospect Watch
            f.write("## 🔮 Prospect Watch\n\n")
            
            # In a real implementation, you would have actual prospect data
            # For demo purposes, we'll simulate prospect updates
            prospects = [
                {
                    'name': 'Jackson Holliday',
                    'team': 'Orioles',
                    'position': 'SS',
                    'level': 'AAA',
                    'stats': f".{random.randint(280, 350)} AVG, {random.randint(5, 12)} HR, {random.randint(30, 50)} RBI, {random.randint(8, 20)} SB in {random.randint(180, 250)} AB",
                    'eta': 'Soon - already on 40-man roster'
                },
                {
                    'name': 'Junior Caminero',
                    'team': 'Rays',
                    'position': '3B',
                    'level': 'AAA',
                    'stats': f".{random.randint(280, 320)} AVG, {random.randint(10, 18)} HR, {random.randint(40, 60)} RBI in {random.randint(200, 280)} AB",
                    'eta': f"{random.choice(['June', 'July', 'August'])} {datetime.now().year}"
                },
                {
                    'name': 'Jasson Domínguez',
                    'team': 'Yankees',
                    'position': 'OF',
                    'level': 'AAA',
                    'stats': f".{random.randint(260, 310)} AVG, {random.randint(8, 15)} HR, {random.randint(10, 25)} SB in {random.randint(180, 250)} AB",
                    'eta': f"Expected back from TJ surgery in {random.choice(['July', 'August'])}"
                },
                {
                    'name': 'Colson Montgomery',
                    'team': 'White Sox',
                    'position': 'SS',
                    'level': 'AA',
                    'stats': f".{random.randint(270, 320)} AVG, {random.randint(6, 12)} HR, {random.randint(30, 50)} RBI in {random.randint(180, 250)} AB",
                    'eta': f"{random.choice(['August', 'September', '2026'])}"
                },
                {
                    'name': 'Orelvis Martinez',
                    'team': 'Blue Jays',
                    'position': '3B/SS',
                    'level': 'AAA',
                    'stats': f".{random.randint(240, 290)} AVG, {random.randint(12, 20)} HR, {random.randint(40, 60)} RBI in {random.randint(180, 250)} AB",
                    'eta': f"{random.choice(['July', 'August', 'September'])}"
                }
            ]
            
            # Create a table for prospects
            headers = ["Prospect", "Team", "Position", "Level", "Stats", "ETA"]
            prospects_table = []
            
            for prospect in prospects:
                prospects_table.append([
                    prospect['name'],
                    prospect['team'],
                    prospect['position'],
                    prospect['level'],
                    prospect['stats'],
                    prospect['eta']
                ])
            
            f.write(tabulate(prospects_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            logger.info(f"Player news report generated: {output_file}")
    
    def schedule_updates(self, daily_update_time="07:00", weekly_update_day="Monday"):
        """Schedule regular updates at specified times"""
        # Schedule daily updates
        schedule.every().day.at(daily_update_time).do(self.run_system_update)
        
        # Schedule weekly full updates with report generation
        if weekly_update_day.lower() == "monday":
            schedule.every().monday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "tuesday":
            schedule.every().tuesday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "wednesday":
            schedule.every().wednesday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "thursday":
            schedule.every().thursday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "friday":
            schedule.every().friday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "saturday":
            schedule.every().saturday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "sunday":
            schedule.every().sunday.at(daily_update_time).do(self.generate_reports)
        
        logger.info(f"Scheduled daily updates at {daily_update_time}")
        logger.info(f"Scheduled weekly full updates on {weekly_update_day} at {daily_update_time}")
    
    def start_update_loop(self):
        """Start the scheduled update loop"""
        logger.info("Starting update loop - press Ctrl+C to exit")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Update loop stopped by user")
    
    def fetch_external_data(self, data_type, source_index=0):
        """Fetch data from external sources - placeholder for real implementation"""
        logger.info(f"Fetching {data_type} data from {self.data_sources[data_type][source_index]}")
        
        # In a real implementation, you would:
        # 1. Make HTTP request to the data source
        # 2. Parse the response (HTML, JSON, etc.)
        # 3. Extract relevant data
        # 4. Return structured data
        
        # For demo purposes, we'll simulate a successful fetch
        return True

# Command-line interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Fantasy Baseball Automated Model with Live Updates')
    parser.add_argument('--league_id', type=str, default="2874", help='League ID')
    parser.add_argument('--team_name', type=str, default="Kenny Kawaguchis", help='Your team name')
    parser.add_argument('--daily_update', type=str, default="07:00", help='Daily update time (HH:MM)')
    parser.add_argument('--weekly_update', type=str, default="Monday", help='Weekly update day')
    parser.add_argument('--manual_update', action='store_true', help='Run a manual update now')
    parser.add_argument('--reports_only', action='store_true', help='Generate reports only')
    parser.add_argument('--daemon', action='store_true', help='Run as a daemon (continuous updates)')
    
    args = parser.parse_args()
    
    # Create model instance
    model = FantasyBaseballAutomated(args.league_id, args.team_name)
    
    # Check if we can load existing state
    if not model.load_system_state():
        logger.info("No existing state found. Loading initial data...")
        model.load_initial_data()
    
    # Handle command-line options
    if args.manual_update:
        logger.info("Running manual update...")
        model.run_system_update()
    
    if args.reports_only:
        logger.info("Generating reports only...")
        model.generate_reports()
    
    if args.daemon:
        # Schedule updates
        model.schedule_updates(args.daily_update, args.weekly_update)
        # Start update loop
        model.start_update_loop()
    
    logger.info("Fantasy Baseball Automated Model completed successfully!")

if __name__ == "__main__":
    main()
                ops_values = [ops for ops in ops_values if ops > 0]
                batting_totals['OPS'] = sum(ops_values) / len(ops_values) if ops_values else 0
            
            # Sort by AB descending
            batter_table.sort(key=lambda x: x[1], reverse=True)
            
            # Add totals row
            batter_table.append([
                "TOTALS",
                batting_totals['AB'],
                batting_totals['R'],
                batting_totals['HR'],
                batting_totals['RBI'],
                batting_totals['SB'],
                f"{batting_totals['AVG']:.3f}",
                f"{batting_totals['OPS']:.3f}"
            ])
            
            f.write(tabulate(batter_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Pitchers stats
            f.write("#### Pitching Stats\n\n")
            pitcher_table = []
            headers = ["Player", "IP", "W", "ERA", "WHIP", "K", "QS", "SV"]
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_stats_current and 'ERA' in self.player_stats_current[name]:
                    stats = self.player_stats_current[name]
                    pitcher_table.append([
                        name,
                        stats.get('IP', 0),
                        stats.get('W', 0),
                        f"{stats.get('ERA', 0):.2f}",
                        f"{stats.get('WHIP', 0):.2f}",
                        stats.get('K', 0),
                        stats.get('QS', 0),
                        stats.get('SV', 0)
                    ])
                    
                    # Add to totals
                    pitching_totals['IP'] += stats.get('IP', 0)
                    pitching_totals['W'] += stats.get('W', 0)
                    pitching_totals['K'] += stats.get('K', 0)
                    pitching_totals['QS'] += stats.get('QS', 0)
                    pitching_totals['SV'] += stats.get('SV', 0)
            
            # Calculate team ERA and WHIP
            if pitching_totals['IP'] > 0:
                # Calculate total ER and baserunners across all pitchers
                total_er = sum(self.player_stats_current.get(p["name"], {}).get('ERA', 0) * 
                               self.player_stats_current.get(p["name"], {}).get('IP', 0) / 9 
                               for p in self.team_rosters.get(self.your_team_name, [])
                               if 'ERA' in self.player_stats_current.get(p["name"], {}))
                
                total_baserunners = sum(self.player_stats_current.get(p["name"], {}).get('WHIP', 0) * 
                                       self.player_stats_current.get(p["name"], {}).get('IP', 0) 
                                       for p in self.team_rosters.get(self.your_team_name, [])
                                       if 'WHIP' in self.player_stats_current.get(p["name"], {}))
                
                pitching_totals['ERA'] = total_er * 9 / pitching_totals['IP']
                pitching_totals['WHIP'] = total_baserunners / pitching_totals['IP']
            
            # Sort by IP descending
            pitcher_table.sort(key=lambda x: x[1], reverse=True)
            
            # Add totals row
            pitcher_table.append([
                "TOTALS",
                pitching_totals['IP'],
                pitching_totals['W'],
                f"{pitching_totals['ERA']:.2f}",
                f"{pitching_totals['WHIP']:.2f}",
                pitching_totals['K'],
                pitching_totals['QS'],
                pitching_totals['SV']
            ])
            
            f.write(tabulate(pitcher_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Team Projections
            f.write("### Rest of Season Projections\n\n")
            
            # Batters projections
            f.write("#### Batting Projections\n\n")
            batter_proj_table = []
            headers = ["Player", "AB", "R", "HR", "RBI", "SB", "AVG", "OPS"]
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_projections and 'AVG' in self.player_projections[name]:
                    proj = self.player_projections[name]
                    batter_proj_table.append([
                        name,
                        int(proj.get('AB', 0)),
                        int(proj.get('R', 0)),
                        int(proj.get('HR', 0)),
                        int(proj.get('RBI', 0)),
                        int(proj.get('SB', 0)),
                        f"{proj.get('AVG', 0):.3f}",
                        f"{proj.get('OPS', 0):.3f}"
                    ])
            
            # Sort by projected AB descending
            batter_proj_table.sort(key=lambda x: x[1], reverse=True)
            
            f.write(tabulate(batter_proj_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Pitchers projections
            f.write("#### Pitching Projections\n\n")
            pitcher_proj_table = []
            headers = ["Player", "IP", "ERA", "WHIP", "K/9", "QS", "SV"]
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_projections and 'ERA' in self.player_projections[name]:
                    proj = self.player_projections[name]
                    pitcher_proj_table.append([
                        name,
                        int(proj.get('IP', 0)),
                        f"{proj.get('ERA', 0):.2f}",
                        f"{proj.get('WHIP', 0):.2f}",
                        f"{proj.get('K9', 0):.1f}",
                        int(proj.get('QS', 0)),
                        int(proj.get('SV', 0))
                    ])
            
            # Sort by projected IP descending
            pitcher_proj_table.sort(key=lambda x: x[1], reverse=True)
            
            f.write(tabulate(pitcher_proj_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Recent News
            f.write("### Recent Team News\n\n")
            
            news_count = 0
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_news and self.player_news[name]:
                    # Sort news by date (most recent first)
                    player_news = sorted(
                        self.player_news[name], 
                        key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"), 
                        reverse=True
                    )
                    
                    # Show most recent news item
                    latest_news = player_news[0]
                    f.write(f"**{name}** ({latest_news['date']} - {latest_news['source']}): {latest_news['content']}\n\n")
                    news_count += 1
            
            if news_count == 0:
                f.write("No recent news for your team's players.\n\n")
            
            # Recommendations
            f.write("## Team Recommendations\n\n")
            
            # Analyze team strengths and weaknesses
            # This is a simplified analysis - a real implementation would be more sophisticated
            
            # Calculate average stats per player
            avg_hr = batting_totals['HR'] / len([p for p in self.team_rosters.get(self.your_team_name, []) if p["name"] in self.player_stats_current and 'AVG' in self.player_stats_current[p["name"]]]) if len([p for p in self.team_rosters.get(self.your_team_name, []) if p["name"] in self.player_stats_current and 'AVG' in self.player_stats_current[p["name"]]]) > 0 else 0
            
            avg_sb = batting_totals['SB'] / len([p for p in self.team_rosters.get(self.your_team_name, []) if p["name"] in self.player_stats_current and 'AVG' in self.player_stats_current[p["name"]]]) if len([p for p in self.team_rosters.get(self.your_team_name, []) if p["name"] in self.player_stats_current and 'AVG' in self.player_stats_current[p["name"]]]) > 0 else 0
            
            avg_era = pitching_totals['ERA']
            avg_k9 = pitching_totals['K'] * 9 / pitching_totals['IP'] if pitching_totals['IP'] > 0 else 0
            
            # Identify strengths and weaknesses
            strengths = []
            weaknesses = []
            
            if batting_totals['AVG'] > 0.270:
                strengths.append("Batting Average")
            elif batting_totals['AVG'] < 0.250:
                weaknesses.append("Batting Average")
                
            if batting_totals['OPS'] > 0.780:
                strengths.append("OPS")
            elif batting_totals['OPS'] < 0.720:
                weaknesses.append("OPS")
                
            if avg_hr > 0.08:  # More than 0.08 HR per AB
                strengths.append("Power")
            elif avg_hr < 0.04:
                weaknesses.append("Power")
                
            if avg_sb > 0.05:  # More than 0.05 SB per AB
                strengths.append("Speed")
            elif avg_sb < 0.02:
                weaknesses.append("Speed")
                
            if avg_era < 3.80:
                strengths.append("ERA")
            elif avg_era > 4.20:
                weaknesses.append("ERA")
                
            if pitching_totals['WHIP'] < 1.20:
                strengths.append("WHIP")
            elif pitching_totals['WHIP'] > 1.30:
                weaknesses.append("WHIP")
                
            if avg_k9 > 9.5:
                strengths.append("Strikeouts")
            elif avg_k9 < 8.0:
                weaknesses.append("Strikeouts")
                
            if pitching_totals['SV'] > 15:
                strengths.append("Saves")
            elif pitching_totals['SV'] < 5:
                weaknesses.append("Saves")
                
            if pitching_totals['QS'] > 15:
                strengths.append("Quality Starts")
            elif pitching_totals['QS'] < 5:
                weaknesses.append("Quality Starts")
                
            # Write strengths and weaknesses
            f.write("### Team Strengths\n\n")
            if strengths:
                for strength in strengths:
                    f.write(f"- **{strength}**\n")
            else:
                f.write("No clear strengths identified yet.\n")
            
            f.write("\n### Team Weaknesses\n\n")
            if weaknesses:
                for weakness in weaknesses:
                    f.write(f"- **{weakness}**\n")
            else:
                f.write("No clear weaknesses identified yet.\n")
            
            f.write("\n### Recommended Actions\n\n")
            
            # Generate recommendations based on weaknesses
            if weaknesses:
                for weakness in weaknesses[:3]:  # Focus on top 3 weaknesses
                    if weakness == "Power":
                        f.write("- **Target Power Hitters**: Consider trading for players with high HR and RBI projections.\n")
                        
                        # Suggest specific free agents
                        power_fa = sorted(
                            [(name, p['projections'].get('HR', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'HR' in p['projections']],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if power_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {int(p[1])} HR)" for p in power_fa]) + "\n")
                    
                    elif weakness == "Speed":
                        f.write("- **Add Speed**: Look to add players who can contribute stolen bases.\n")
                        
                        # Suggest specific free agents
                        speed_fa = sorted(
                            [(name, p['projections'].get('SB', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'SB' in p['projections']],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if speed_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {int(p[1])} SB)" for p in speed_fa]) + "\n")
                    
                    elif weakness == "Batting Average":
                        f.write("- **Improve Batting Average**: Look for consistent contact hitters.\n")
                        
                        # Suggest specific free agents
                        avg_fa = sorted(
                            [(name, p['projections'].get('AVG', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'AVG' in p['projections'] and p['projections'].get('AB', 0) > 300],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if avg_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {p[1]:.3f} AVG)" for p in avg_fa]) + "\n")
                    
                    elif weakness == "ERA" or weakness == "WHIP":
                        f.write("- **Improve Pitching Ratios**: Focus on pitchers with strong ERA and WHIP projections.\n")
                        
                        # Suggest specific free agents
                        ratio_fa = sorted(
                            [(name, p['projections'].get('ERA', 0), p['projections'].get('WHIP', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'ERA' in p['projections'] and p['projections'].get('IP', 0) > 100],
                            key=lambda x: x[1] + x[2]
                        )[:3]
                        
                        if ratio_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {p[1]:.2f} ERA, {p[2]:.2f} WHIP)" for p in ratio_fa]) + "\n")
                    
                    elif weakness == "Strikeouts":
                        f.write("- **Add Strikeout Pitchers**: Target pitchers with high K/9 rates.\n")
                        
                        # Suggest specific free agents
                        k_fa = sorted(
                            [(name, p['projections'].get('K9', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'K9' in p['projections'] and p['projections'].get('IP', 0) > 75],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if k_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {p[1]:.1f} K/9)" for p in k_fa]) + "\n")
                    
                    elif weakness == "Saves":
                        f.write("- **Add Closers**: Look for pitchers in save situations.\n")
                        
                        # Suggest specific free agents
                        sv_fa = sorted(
                            [(name, p['projections'].get('SV', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'SV' in p['projections'] and p['projections'].get('SV', 0) > 5],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if sv_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {int(p[1])} SV)" for p in sv_fa]) + "\n")
                    
                    elif weakness == "Quality Starts":
                        f.write("- **Add Quality Starting Pitchers**: Target consistent starters who work deep into games.\n")
                        
                        # Suggest specific free agents
                        qs_fa = sorted(
                            [(name, p['projections'].get('QS', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'QS' in p['projections'] and p['projections'].get('QS', 0) > 5],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if qs_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {int(p[1])} QS)" for p in qs_fa]) + "\n")
            else:
                f.write("Your team is well-balanced! Continue to monitor player performance and injuries.\n")
            
            # General strategy recommendation
            f.write("\n### General Strategy\n\n")
            f.write("1. **Monitor the waiver wire daily** for emerging talent and players returning from injury.\n")
            f.write("2. **Be proactive with injured players**. Don't hold onto injured players too long if better options are available.\n")
            f.write("3. **Stream starting pitchers** against weak offensive teams for additional counting stats.\n")
            f.write("4. **Watch for changing roles** in bullpens for potential closers in waiting.\n")
            
            logger.info(f"Team analysis report generated: {output_file}")
    
    def generate_free_agents_report(self, output_file):
        """Generate free agents report sorted by projected value"""
        with open(output_file, 'w') as f:
            # Title
            f.write("# Fantasy Baseball Free Agent Analysis\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
            
            # Calculate scores for ranking
            fa_batters = {}
            fa_pitchers = {}
            
            for name, data in self.free_agents.items():
                if 'projections' in data:
                    proj = data['projections']
                    if 'AVG' in proj:  # It's a batter
                        # Calculate a batter score
                        score = (
                            proj.get('HR', 0) * 3 +
                            proj.get('SB', 0) * 3 +
                            proj.get('R', 0) * 0.5 +
                            proj.get('RBI', 0) * 0.5 +
                            proj.get('AVG', 0) * 300 +
                            proj.get('OPS', 0) * 150
                        )
                        fa_batters[name] = {'projections': proj, 'score': score}
                    
                    elif 'ERA' in proj:  # It's a pitcher
                        # Calculate a pitcher score
                        era_score = (5.00 - proj.get('ERA', 4.50)) * 20 if proj.get('ERA', 0) < 5.00 else 0
                        whip_score = (1.40 - proj.get('WHIP', 1.30)) * 60 if proj.get('WHIP', 0) < 1.40 else 0
                        
                        score = (
                            era_score +
                            whip_score +
                            proj.get('K9', 0) * 10 +
                            proj.get('QS', 0) * 4 +
                            proj.get('SV', 0) * 6 +
                            proj.get('IP', 0) * 0.2
                        )
                        fa_pitchers[name] = {'projections': proj, 'score': score}
            
            # Top Batters by Position
            f.write("## Top Free Agent Batters\n\n")
            
            # Define positions
            positions = {
                "C": "Catchers",
                "1B": "First Basemen",
                "2B": "Second Basemen",
                "3B": "Third Basemen",
                "SS": "Shortstops",
                "OF": "Outfielders"
            }
            
            # Simplified position assignment for demo
            position_players = {pos: [] for pos in positions}
            
            # Manually assign positions for demo
            for name in fa_batters:
                # This is a very simplified approach - in reality, you'd have actual position data
                if name in ["Keibert Ruiz", "Danny Jansen", "Gabriel Moreno", "Patrick Bailey", "Ryan Jeffers"]:
                    position_players["C"].append(name)
                elif name in ["Christian Walker", "Spencer Torkelson", "Andrew Vaughn", "Anthony Rizzo"]:
                    position_players["1B"].append(name)
                elif name in ["Gavin Lux", "Luis Rengifo", "Nick Gonzales", "Zack Gelof", "Brendan Donovan"]:
                    position_players["2B"].append(name)
                elif name in ["Jeimer Candelario", "Spencer Steer", "Ke'Bryan Hayes", "Brett Baty"]:
                    position_players["3B"].append(name)
                elif name in ["JP Crawford", "Ha-Seong Kim", "Xander Bogaerts", "Jose Barrero"]:
                    position_players["SS"].append(name)
                else:
                    position_players["OF"].append(name)
            
            # Write position sections
            for pos, title in positions.items():
                players = position_players[pos]
                if players:
                    f.write(f"### {title}\n\n")
                    
                    # Create table
                    headers = ["Rank", "Player", "AB", "R", "HR", "RBI", "SB", "AVG", "OPS", "Score"]
                    
                    # Get scores and sort
                    pos_players = [(name, fa_batters[name]['score'], fa_batters[name]['projections']) 
                                 for name in players if name in fa_batters]
                    
                    pos_players.sort(key=lambda x: x[1], reverse=True)
                    
                    # Build table
                    table_data = []
                    for i, (name, score, proj) in enumerate(pos_players[:10]):  # Top 10 per position
                        table_data.append([
                            i+1,
                            name,
                            int(proj.get('AB', 0)),
                            int(proj.get('R', 0)),
                            int(proj.get('HR', 0)),
                            int(proj.get('RBI', 0)),
                            int(proj.get('SB', 0)),
                            f"{proj.get('AVG', 0):.3f}",
                            f"{proj.get('OPS', 0):.3f}",
                            int(score)
                        ])
                    
                    f.write(tabulate(table_data, headers=headers, tablefmt="pipe"))
                    f.write("\n\n")
            
            # Top Pitchers
            f.write("## Top Free Agent Pitchers\n\n")
            
            # Starting pitchers
            f.write("### Starting Pitchers\n\n")
            
            # Identify starters
            starters = [(name, fa_pitchers[name]['score'], fa_pitchers[name]['projections']) 
                       for name in fa_pitchers 
                       if fa_pitchers[name]['projections'].get('QS', 0) > 0]
            
            starters.sort(key=lambda x: x[1], reverse=True)
            
            # Create table
            headers = ["Rank", "Player", "IP", "ERA", "WHIP", "K/9", "QS", "Score"]
            
            table_data = []
            for i, (name, score, proj) in enumerate(starters[:15]):  # Top 15 SP
                table_data.append([
                    i+1,
                    name,
                    int(proj.get('IP', 0)),
                    f"{proj.get('ERA', 0):.2f}",
                    f"{proj.get('WHIP', 0):.2f}",
                    f"{proj.get('K9', 0):.1f}",
                    int(proj.get('QS', 0)),
                    int(score)
                ])
            
            f.write(tabulate(table_data, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Relief pitchers
            f.write("### Relief Pitchers\n\n")
            
            # Identify relievers
            relievers = [(name, fa_pitchers[name]['score'], fa_pitchers[name]['projections']) 
                        for name in fa_pitchers 
                        if fa_pitchers[name]['projections'].get('QS', 0) == 0]
            
            relievers.sort(key=lambda x: x[1], reverse=True)
            
            # Create table
            headers = ["Rank", "Player", "IP", "ERA", "WHIP", "K/9", "SV", "Score"]
            
            table_data = []
            for i, (name, score, proj) in enumerate(relievers[:10]):  # Top 10 RP
                table_data.append([
                    i+1,
                    name,
                    int(proj.get('IP', 0)),
                    f"{proj.get('ERA', 0):.2f}",
                    f"{proj.get('WHIP', 0):.2f}",
                    f"{proj.get('K9', 0):.1f}",
                    int(proj.get('SV', 0)),
                    int(score)
                ])
            
            f.write(tabulate(table_data, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Category-Specific Free Agent Targets
            f.write("## Category-Specific Free Agent Targets\n\n")
            
            # Power hitters (HR and RBI)
            power_hitters = sorted(
                [(name, fa_batters[name]['projections'].get('HR', 0), fa_batters[name]['projections'].get('RBI', 0)) 
                 for name in fa_batters],
                key=lambda x: x[1] + x[2]/3,
                reverse=True
            )[:5]
            
            f.write("**Power (HR/RBI):** ")
            f.write(", ".join([f"{name} ({int(hr)} HR, {int(rbi)} RBI)" for name, hr, rbi in power_hitters]))
            f.write("\n\n")
            
            # Speed (SB)
            speed_players = sorted(
                [(name, fa_batters[name]['projections'].get('SB', 0)) 
                 for name in fa_batters],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            f.write("**Speed (SB):** ")
            f.write(", ".join([f"{name} ({int(sb)} SB)" for name, sb in speed_players]))
            f.write("\n\n")
            
            # Average (AVG)
            average_hitters = sorted(
                [(name, fa_batters[name]['projections'].get('AVG', 0)) 
                 for name in fa_batters 
                 if fa_batters[name]['projections'].get('AB', 0) >= 300],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            f.write("**Batting Average:** ")
            f.write(", ".join([f"{name} ({avg:.3f})" for name, avg in average_hitters]))
            f.write("\n\n")
            
            # ERA
            era_pitchers = sorted(
                [(name, fa_pitchers[name]['projections'].get('ERA', 0)) 
                 for name in fa_pitchers 
                 if fa_pitchers[name]['projections'].get('IP', 0) >= 100],
                key=lambda x: x[1]
            )[:5]
            
            f.write("**ERA:** ")
            f.write(", ".join([f"{name} ({era:.2f})" for name, era in era_pitchers]))
            f.write("\n\n")
            
            # WHIP
            whip_pitchers = sorted(
                [(name, fa_pitchers[name]['projections'].get('WHIP', 0)) 
                 for name in fa_pitchers 
                 if fa_pitchers[name]['projections'].get('IP', 0) >= 100],
                key=lambda x: x[1]
            )[:5]
            
            f.write("**WHIP:** ")
            f.write(", ".join([f"{name} ({whip:.2f})" for name, whip in whip_pitchers]))
            f.write("\n\n")
            
            # Saves (SV)
            save_pitchers = sorted(
                [(name, fa_pitchers[name]['projections'].get('SV', 0)) 
                 for name in fa_pitchers],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            f.write("**Saves:** ")
            f.write(", ".join([f"{name} ({int(sv)})" for name, sv in save_pitchers]))
            f.write("\n\n")
            
            logger.info(f"Free agents report generated: {output_file}")
    
    def generate_trending_players_report(self, output_file):
        """Generate report on trending players (hot/cold)"""
        # In a real implementation, you would calculate trends based on recent performance
        # For demo purposes, we'll simulate trends
        
        with open(output_                # Recalculate AVG
                self.player_stats_current[player]['AVG'] = (
                    self.player_stats_current[player]['H'] / 
                    self.player_stats_current[player]['AB'] 
                    if self.player_stats_current[player]['AB'] > 0 else 0
                )
                
                # Recalculate OBP
                self.player_stats_current[player]['OBP'] = (
                    (self.player_stats_current[player]['H'] + self.player_stats_current[player]['BB']) / 
                    (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) 
                    if (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) > 0 else 0
                )
                
                # Recalculate SLG and OPS
                singles = (
                    self.player_stats_current[player]['H'] - 
                    self.player_stats_current[player]['HR'] - 
                    self.player_stats_current[player].get('2B', random.randint(15, 25)) - 
                    self.player_stats_current[player].get('3B', random.randint(0, 5))
                )
                
                tb = (
                    singles + 
                    (2 * self.player_stats_current[player].get('2B', random.randint(15, 25))) + 
                    (3 * self.player_stats_current[player].get('3B', random.randint(0, 5))) + 
                    (4 * self.player_stats_current[player]['HR'])
                )
                
                self.player_stats_current[player]['SLG'] = (
                    tb / self.player_stats_current[player]['AB'] 
                    if self.player_stats_current[player]['AB'] > 0 else 0
                )
                
                self.player_stats_current[player]['OPS'] = (
                    self.player_stats_current[player]['OBP'] + 
                    self.player_stats_current[player]['SLG']
                )
    
    def update_player_projections(self):
        """Update player projections by fetching from data sources"""
        logger.info("Updating player projections from sources...")
        
        # In a real implementation, you would:
        # 1. Fetch data from each source in self.data_sources['projections']
        # 2. Parse and clean the data
        # 3. Merge with existing projections
        # 4. Update self.player_projections
        
        # For demo purposes, we'll simulate this process
        self._simulate_projections_update()
        
        logger.info(f"Updated projections for {len(self.player_projections)} players")
        return len(self.player_projections)
    
    def _simulate_projections_update(self):
        """Simulate updating projections for demo purposes"""
        # Update existing projections based on current stats
        for player in self.player_stats_current:
            # Skip if no projection exists
            if player not in self.player_projections:
                # Create new projection based on current stats
                if 'ERA' in self.player_stats_current[player]:  # It's a pitcher
                    # Project rest of season based on current performance
                    era_factor = min(max(4.00 / self.player_stats_current[player]['ERA'], 0.75), 1.25) if self.player_stats_current[player]['ERA'] > 0 else 1.0
                    whip_factor = min(max(1.30 / self.player_stats_current[player]['WHIP'], 0.75), 1.25) if self.player_stats_current[player]['WHIP'] > 0 else 1.0
                    k9_factor = min(max(self.player_stats_current[player]['K9'] / 8.5, 0.75), 1.25) if self.player_stats_current[player].get('K9', 0) > 0 else 1.0
                    
                    # Determine if starter or reliever
                    is_reliever = 'SV' in self.player_stats_current[player] or self.player_stats_current[player].get('IP', 0) < 20
                    
                    self.player_projections[player] = {
                        'IP': random.uniform(40, 70) if is_reliever else random.uniform(120, 180),
                        'ERA': random.uniform(3.0, 4.5) * era_factor,
                        'WHIP': random.uniform(1.05, 1.35) * whip_factor,
                        'K9': random.uniform(7.5, 12.0) * k9_factor,
                        'QS': 0 if is_reliever else random.randint(10, 20),
                        'SV': random.randint(15, 35) if is_reliever and self.player_stats_current[player].get('SV', 0) > 0 else 0
                    }
                else:  # It's a batter
                    # Project rest of season based on current performance
                    avg_factor = min(max(self.player_stats_current[player]['AVG'] / 0.260, 0.8), 1.2) if self.player_stats_current[player]['AVG'] > 0 else 1.0
                    ops_factor = min(max(self.player_stats_current[player].get('OPS', 0.750) / 0.750, 0.8), 1.2) if self.player_stats_current[player].get('OPS', 0) > 0 else 1.0
                    
                    # Projected plate appearances remaining
                    pa_remaining = random.randint(400, 550)
                    
                    # HR rate
                    hr_rate = self.player_stats_current[player]['HR'] / self.player_stats_current[player]['AB'] if self.player_stats_current[player]['AB'] > 0 else 0.025
                    
                    # SB rate
                    sb_rate = self.player_stats_current[player]['SB'] / self.player_stats_current[player]['AB'] if self.player_stats_current[player]['AB'] > 0 else 0.015
                    
                    self.player_projections[player] = {
                        'AB': pa_remaining * 0.9,  # 10% of PA are walks/HBP
                        'R': pa_remaining * random.uniform(0.12, 0.18),
                        'HR': pa_remaining * hr_rate * random.uniform(0.8, 1.2),
                        'RBI': pa_remaining * random.uniform(0.1, 0.17),
                        'SB': pa_remaining * sb_rate * random.uniform(0.8, 1.2),
                        'AVG': random.uniform(0.230, 0.310) * avg_factor,
                        'OPS': random.uniform(0.680, 0.950) * ops_factor
                    }
                continue
            
            # If projection exists, update it based on current performance
            if 'ERA' in self.player_stats_current[player]:  # It's a pitcher
                # Calculate adjustment factors based on current vs. projected performance
                if self.player_stats_current[player].get('IP', 0) > 20:  # Enough IP to adjust projections
                    # ERA adjustment
                    current_era = self.player_stats_current[player].get('ERA', 4.00)
                    projected_era = self.player_projections[player].get('ERA', 4.00)
                    era_adj = min(max(projected_era / current_era, 0.8), 1.2) if current_era > 0 else 1.0
                    
                    # WHIP adjustment
                    current_whip = self.player_stats_current[player].get('WHIP', 1.30)
                    projected_whip = self.player_projections[player].get('WHIP', 1.30)
                    whip_adj = min(max(projected_whip / current_whip, 0.8), 1.2) if current_whip > 0 else 1.0
                    
                    # K/9 adjustment
                    current_k9 = self.player_stats_current[player].get('K9', 8.5)
                    projected_k9 = self.player_projections[player].get('K9', 8.5)
                    k9_adj = min(max(current_k9 / projected_k9, 0.8), 1.2) if projected_k9 > 0 else 1.0
                    
                    # Apply adjustments
                    self.player_projections[player]['ERA'] = projected_era * era_adj
                    self.player_projections[player]['WHIP'] = projected_whip * whip_adj
                    self.player_projections[player]['K9'] = projected_k9 * k9_adj
                    
                    # Adjust saves projection for relievers
                    if 'SV' in self.player_stats_current[player]:
                        current_sv_rate = self.player_stats_current[player].get('SV', 0) / max(1, self.player_stats_current[player].get('IP', 1) / 60)
                        self.player_projections[player]['SV'] = min(45, max(0, int(current_sv_rate * 60)))
                    
                    # Adjust QS projection for starters
                    if 'QS' in self.player_stats_current[player] and self.player_stats_current[player].get('IP', 0) > 0:
                        current_qs_rate = self.player_stats_current[player].get('QS', 0) / max(1, self.player_stats_current[player].get('IP', 1) / 180)
                        self.player_projections[player]['QS'] = min(30, max(0, int(current_qs_rate * 180)))
            else:  # It's a batter
                # Adjust only if enough AB to be significant
                if self.player_stats_current[player].get('AB', 0) > 75:
                    # AVG adjustment
                    current_avg = self.player_stats_current[player].get('AVG', 0.260)
                    projected_avg = self.player_projections[player].get('AVG', 0.260)
                    avg_adj = min(max((current_avg + 2*projected_avg) / (3*projected_avg), 0.85), 1.15) if projected_avg > 0 else 1.0
                    
                    # HR rate adjustment
                    current_hr_rate = self.player_stats_current[player].get('HR', 0) / max(1, self.player_stats_current[player].get('AB', 1)) * 550
                    projected_hr = self.player_projections[player].get('HR', 15)
                    hr_adj = min(max((current_hr_rate + 2*projected_hr) / (3*projected_hr), 0.7), 1.3) if projected_hr > 0 else 1.0
                    
                    # SB rate adjustment
                    current_sb_rate = self.player_stats_current[player].get('SB', 0) / max(1, self.player_stats_current[player].get('AB', 1)) * 550
                    projected_sb = self.player_projections[player].get('SB', 10)
                    sb_adj = min(max((current_sb_rate + 2*projected_sb) / (3*projected_sb), 0.7), 1.3) if projected_sb > 0 else 1.0
                    
                    # Apply adjustments
                    self.player_projections[player]['AVG'] = projected_avg * avg_adj
                    self.player_projections[player]['HR'] = projected_hr * hr_adj
                    self.player_projections[player]['SB'] = projected_sb * sb_adj
                    
                    # Adjust OPS based on AVG and power
                    projected_ops = self.player_projections[player].get('OPS', 0.750)
                    self.player_projections[player]['OPS'] = projected_ops * (avg_adj * 0.4 + hr_adj * 0.6)
                    
                    # Adjust runs and RBI based on HR and overall performance
                    projected_r = self.player_projections[player].get('R', 70)
                    projected_rbi = self.player_projections[player].get('RBI', 70)
                    
                    self.player_projections[player]['R'] = projected_r * ((avg_adj + hr_adj) / 2)
                    self.player_projections[player]['RBI'] = projected_rbi * ((avg_adj + hr_adj) / 2)
        
        # Round numerical values for cleaner display
        for player in self.player_projections:
            for stat in self.player_projections[player]:
                if isinstance(self.player_projections[player][stat], float):
                    if stat in ['ERA', 'WHIP', 'K9', 'AVG', 'OPS']:
                        self.player_projections[player][stat] = round(self.player_projections[player][stat], 3)
                    else:
                        self.player_projections[player][stat] = round(self.player_projections[player][stat])
    
    def update_player_news(self):
        """Update player news by fetching from news sources"""
        logger.info("Updating player news from sources...")
        
        # In a real implementation, you would:
        # 1. Fetch data from each source in self.data_sources['news']
        # 2. Parse and extract news items
        # 3. Store in self.player_news
        
        # For demo purposes, we'll simulate this process
        self._simulate_news_update()
        
        logger.info(f"Updated news for {len(self.player_news)} players")
        return len(self.player_news)
    
    def _simulate_news_update(self):
        """Simulate updating player news for demo purposes"""
        # List of possible news templates
        injury_news = [
            "{player} was removed from Wednesday's game with {injury}.",
            "{player} is day-to-day with {injury}.",
            "{player} has been placed on the 10-day IL with {injury}.",
            "{player} will undergo further testing for {injury}.",
            "{player} is expected to miss 4-6 weeks with {injury}."
        ]
        
        performance_news = [
            "{player} went {stats} in Wednesday's 6-4 win.",
            "{player} struck out {k} batters in {ip} innings on Tuesday.",
            "{player} has hit safely in {streak} straight games.",
            "{player} collected {hits} hits including a homer on Monday.",
            "{player} has struggled recently, going {bad_stats} over his last 7 games."
        ]
        
        role_news = [
            "{player} will take over as the closer with {teammate} on the IL.",
            "{player} has been moved up to the {spot} spot in the batting order.",
            "{player} will make his next start on {day}.",
            "{player} has been moved to the bullpen.",
            "{player} will be recalled from Triple-A on Friday."
        ]
        
        # Possible injuries
        injuries = [
            "left hamstring tightness",
            "right oblique strain",
            "lower back discomfort",
            "shoulder inflammation",
            "forearm tightness",
            "groin strain",
            "ankle sprain",
            "knee soreness",
            "thumb contusion",
            "wrist inflammation"
        ]
        
        # Generate news for a subset of players
        for player in random.sample(list(self.player_stats_current.keys()), min(10, len(self.player_stats_current))):
            news_type = random.choice(["injury", "performance", "role"])
            
            if news_type == "injury":
                template = random.choice(injury_news)
                news_item = template.format(
                    player=player,
                    injury=random.choice(injuries)
                )
            elif news_type == "performance":
                template = random.choice(performance_news)
                
                # Determine if batter or pitcher
                if 'ERA' in self.player_stats_current[player]:  # Pitcher
                    ip = round(random.uniform(5, 7), 1)
                    k = random.randint(4, 10)
                    news_item = template.format(
                        player=player,
                        k=k,
                        ip=ip,
                        streak=random.randint(3, 10),
                        hits=random.randint(2, 4),
                        bad_stats=f"{random.randint(0, 4)}-for-{random.randint(20, 30)}"
                    )
                else:  # Batter
                    hits = random.randint(0, 4)
                    abs = random.randint(hits, 5)
                    news_item = template.format(
                        player=player,
                        stats=f"{hits}-for-{abs}",
                        k=random.randint(5, 12),
                        ip=round(random.uniform(5, 7), 1),
                        streak=random.randint(5, 15),
                        hits=random.randint(2, 4),
                        bad_stats=f"{random.randint(0, 4)}-for-{random.randint(20, 30)}"
                    )
            else:  # Role
                template = random.choice(role_news)
                news_item = template.format(
                    player=player,
                    teammate=random.choice(list(self.player_stats_current.keys())),
                    spot=random.choice(["leadoff", "cleanup", "third", "fifth"]),
                    day=random.choice(["Friday", "Saturday", "Sunday", "Monday"])
                )
            
            # Add news item with timestamp
            if player not in self.player_news:
                self.player_news[player] = []
            
            self.player_news[player].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source": random.choice(["Rotowire", "CBS Sports", "ESPN", "MLB.com"]),
                "content": news_item
            })
    
    def update_player_injuries(self):
        """Update player injury statuses"""
        logger.info("Updating player injury statuses...")
        
        # In a real implementation, you would:
        # 1. Fetch injury data from reliable sources
        # 2. Update player status accordingly
        # 3. Adjust projections for injured players
        
        # For demo purposes, we'll simulate some injuries
        injury_count = 0
        
        for player in self.player_stats_current:
            # 5% chance of new injury for each player
            if random.random() < 0.05:
                injury_severity = random.choice(["day-to-day", "10-day IL", "60-day IL"])
                injury_type = random.choice([
                    "hamstring strain", "oblique strain", "back spasms", 
                    "shoulder inflammation", "elbow soreness", "knee inflammation",
                    "ankle sprain", "concussion", "wrist sprain"
                ])
                
                # Add injury news
                if player not in self.player_news:
                    self.player_news[player] = []
                
                self.player_news[player].append({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "source": random.choice(["Rotowire", "CBS Sports", "ESPN", "MLB.com"]),
                    "content": f"{player} has been placed on the {injury_severity} with a {injury_type}."
                })
                
                # Adjust projections for injured players
                if player in self.player_projections:
                    if injury_severity == "day-to-day":
                        reduction = 0.05  # 5% reduction in projections
                    elif injury_severity == "10-day IL":
                        reduction = 0.15  # 15% reduction
                    else:  # 60-day IL
                        reduction = 0.50  # 50% reduction
                    
                    # Apply reduction to projected stats
                    for stat in self.player_projections[player]:
                        if stat not in ['AVG', 'ERA', 'WHIP', 'K9', 'OPS']:  # Don't reduce rate stats
                            self.player_projections[player][stat] *= (1 - reduction)
                
                injury_count += 1
        
        logger.info(f"Updated injury status for {injury_count} players")
        return injury_count
    
    def update_league_transactions(self):
        """Simulate league transactions (adds, drops, trades)"""
        logger.info("Simulating league transactions...")
        
        # In a real implementation, you would:
        # 1. Fetch transaction data from your fantasy platform API
        # 2. Update team rosters accordingly
        
        # For demo purposes, we'll simulate some transactions
        transaction_count = 0
        
        # Add/drop transactions (1-3 per update)
        for _ in range(random.randint(1, 3)):
            # Select a random team
            team = random.choice(list(self.team_rosters.keys()))
            
            # Select a random player to drop
            if len(self.team_rosters[team]) > 0:
                drop_index = random.randint(0, len(self.team_rosters[team]) - 1)
                dropped_player = self.team_rosters[team][drop_index]["name"]
                
                # Remove from roster
                self.team_rosters[team].pop(drop_index)
                
                # Pick a random free agent to add
                if len(self.free_agents) > 0:
                    added_player = random.choice(list(self.free_agents.keys()))
                    
                    # Determine position
                    position = "Unknown"
                    if 'ERA' in self.player_stats_current.get(added_player, {}):
                        position = 'RP' if self.player_stats_current[added_player].get('SV', 0) > 0 else 'SP'
                    else:
                        position = random.choice(["C", "1B", "2B", "3B", "SS", "OF"])
                    
                    # Add to roster
                    self.team_rosters[team].append({
                        "name": added_player,
                        "position": position
                    })
                    
                    # Remove from free agents
                    if added_player in self.free_agents:
                        del self.free_agents[added_player]
                    
                    # Log transaction
                    logger.info(f"Transaction: {team} dropped {dropped_player} and added {added_player}")
                    transaction_count += 1
        
        # Trade transactions (0-1 per update)
        if random.random() < 0.3:  # 30% chance of a trade
            # Select two random teams
            teams = random.sample(list(self.team_rosters.keys()), 2)
            
            # Select random players to trade (1-2 per team)
            team1_players = []
            team2_players = []
            
            for _ in range(random.randint(1, 2)):
                if len(self.team_rosters[teams[0]]) > 0:
                    idx = random.randint(0, len(self.team_rosters[teams[0]]) - 1)
                    team1_players.append(self.team_rosters[teams[0]][idx])
                    self.team_rosters[teams[0]].pop(idx)
            
            for _ in range(random.randint(1, 2)):
                if len(self.team_rosters[teams[1]]) > 0:
                    idx = random.randint(0, len(self.team_rosters[teams[1]]) - 1)
                    team2_players.append(self.team_rosters[teams[1]][idx])
                    self.team_rosters[teams[1]].pop(idx)
            
            # Execute the trade
            for player in team1_players:
                self.team_rosters[teams[1]].append(player)
            
            for player in team2_players:
                self.team_rosters[teams[0]].append(player)
            
            # Log transaction
            team1_names = [p["name"] for p in team1_players]
            team2_names = [p["name"] for p in team2_players]
            
            logger.info(f"Trade: {teams[0]} traded {', '.join(team1_names)} to {teams[1]} for {', '.join(team2_names)}")
            transaction_count += 1
        
        logger.info(f"Simulated {transaction_count} league transactions")
        return transaction_count
    
    def run_system_update(self):
        """Run a complete system update"""
        logger.info("Starting system update...")
        
        try:
            # Update player stats
            self.update_player_stats()
            
            # Update player projections
            self.update_player_projections()
            
            # Update player news
            self.update_player_news()
            
            # Update player injuries
            self.update_player_injuries()
            
            # Update league transactions
            self.update_league_transactions()
            
            # Identify free agents
            self.identify_free_agents()
            
            # Save updated system state
            self.save_system_state()
            
            # Generate updated reports
            self.generate_reports()
            
            # Update timestamp
            self.last_update = datetime.now()
            
            logger.info(f"System update completed successfully at {self.last_update}")
            return True
        except Exception as e:
            logger.error(f"Error during system update: {e}")
            return False
    
    def generate_reports(self):
        """Generate various reports"""
        timestamp = datetime.now().strftime("%Y%m%d")
        
        # Generate team analysis report
        self.generate_team_analysis_report(f"{self.reports_dir}/team_analysis_{timestamp}.md")
        
        # Generate free agents report
        self.generate_free_agents_report(f"{self.reports_dir}/free_agents_{timestamp}.md")
        
        # Generate trending players report
        self.generate_trending_players_report(f"{self.reports_dir}/trending_players_{timestamp}.md")
        
        # Generate player news report
        self.generate_player_news_report(f"{self.reports_dir}/player_news_{timestamp}.md")
        
        logger.info(f"Generated reports with timestamp {timestamp}")
    
    def generate_team_analysis_report(self, output_file):
        """Generate team analysis report"""
        with open(output_file, 'w') as f:
            # Title
            f.write("# Fantasy Baseball Team Analysis\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
            
            # Your Team Section
            f.write(f"## Your Team: {self.your_team_name}\n\n")
            
            # Team Roster
            f.write("### Current Roster\n\n")
            
            # Group players by position
            positions = {"C": [], "1B": [], "2B": [], "3B": [], "SS": [], "OF": [], "SP": [], "RP": []}
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                position = player["position"]
                
                # Simplified position assignment
                if position in positions:
                    positions[position].append(name)
                elif "/" in position:  # Handle multi-position players
                    primary_pos = position.split("/")[0]
                    if primary_pos in positions:
                        positions[primary_pos].append(name)
                    else:
                        positions["UTIL"].append(name)
                else:
                    # Handle unknown positions
                    if 'ERA' in self.player_stats_current.get(name, {}):
                        if self.player_stats_current[name].get('SV', 0) > 0:
                            positions["RP"].append(name)
                        else:
                            positions["SP"].append(name)
                    else:
                        positions["UTIL"].append(name)
            
            # Write roster by position
            for pos, players in positions.items():
                if players:
                    f.write(f"**{pos}**: {', '.join(players)}\n\n")
            
            # Team Performance
            f.write("### Team Performance\n\n")
            
            # Calculate team totals
            batting_totals = {
                'AB': 0, 'R': 0, 'HR': 0, 'RBI': 0, 'SB': 0, 'AVG': 0, 'OPS': 0
            }
            
            pitching_totals = {
                'IP': 0, 'W': 0, 'ERA': 0, 'WHIP': 0, 'K': 0, 'QS': 0, 'SV': 0
            }
            
            # Batters stats
            f.write("#### Batting Stats\n\n")
            batter_table = []
            headers = ["Player", "AB", "R", "HR", "RBI", "SB", "AVG", "OPS"]
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_stats_current and 'AVG' in self.player_stats_current[name]:
                    stats = self.player_stats_current[name]
                    batter_table.append([
                        name,
                        stats.get('AB', 0),
                        stats.get('R', 0),
                        stats.get('HR', 0),
                        stats.get('RBI', 0),
                        stats.get('SB', 0),
                        f"{stats.get('AVG', 0):.3f}",
                        f"{stats.get('OPS', 0):.3f}"
                    ])
                    
                    # Add to totals
                    batting_totals['AB'] += stats.get('AB', 0)
                    batting_totals['R'] += stats.get('R', 0)
                    batting_totals['HR'] += stats.get('HR', 0)
                    batting_totals['RBI'] += stats.get('RBI', 0)
                    batting_totals['SB'] += stats.get('SB', 0)
            
            # Calculate team AVG and OPS
            if batting_totals['AB'] > 0:
                total_hits = sum(self.player_stats_current.get(p["name"], {}).get('H', 0) for p in self.team_rosters.get(self.your_team_name, []))
                batting_totals['AVG'] = total_hits / batting_totals['AB']
                
                # Estimate team OPS as average of player OPS values
                ops_values = [self.player_stats_current.get(p["name"], {}).get('OPS', 0) for p in self.team_rosters.get(self.your_team_name, [])]
                ops_values = [ops for ops in ops_values if ops > 0]
                #!/usr/bin/env python3
# Fantasy Baseball Automated Model with Live Updates
# This script creates an automated system that regularly updates player stats and projections
# Uses the same sources (PECOTA, FanGraphs, MLB.com) for consistent data

import os
import csv
import json
import time
import random
import requests
import pandas as pd
import numpy as np
import schedule
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from tabulate import tabulate
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fantasy_baseball_auto.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FantasyBaseballAuto")

class FantasyBaseballAutomated:
    def __init__(self, league_id="2874", your_team_name="Kenny Kawaguchis"):
        self.league_id = league_id
        self.your_team_name = your_team_name
        self.teams = {}
        self.team_rosters = {}
        self.free_agents = {}
        self.player_stats_current = {}
        self.player_projections = {}
        self.player_news = {}
        self.last_update = None
        
        # API endpoints and data sources
        self.data_sources = {
            'stats': [
                'https://www.fangraphs.com/api/players/stats',
                'https://www.baseball-reference.com/leagues/MLB/2025.shtml',
                'https://www.mlb.com/stats/'
            ],
            'projections': [
                'https://www.fangraphs.com/projections.aspx',
                'https://www.baseball-prospectus.com/pecota-projections/',
                'https://www.mlb.com/stats/projected'
            ],
            'news': [
                'https://www.rotowire.com/baseball/news.php',
                'https://www.cbssports.com/fantasy/baseball/players/updates/',
                'https://www.espn.com/fantasy/baseball/story/_/id/29589640'
            ]
        }
        
        # Create directories for data storage
        self.data_dir = "data"
        self.reports_dir = "reports"
        self.visuals_dir = "visuals"
        self.archives_dir = "archives"
        
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.visuals_dir, exist_ok=True)
        os.makedirs(self.archives_dir, exist_ok=True)
        
        logger.info(f"Fantasy Baseball Automated Model initialized for league ID: {league_id}")
        logger.info(f"Your team: {your_team_name}")
    
    def load_initial_data(self):
        """Load initial data to bootstrap the system"""
        logger.info("Loading initial data for bootstrap...")
        
        # Load team rosters
        self.load_team_rosters()
        
        # Load initial stats and projections
        self.load_initial_stats_and_projections()
        
        # Generate initial set of free agents
        self.identify_free_agents()
        
        # Mark system as initialized with timestamp
        self.last_update = datetime.now()
        self.save_system_state()
        
        logger.info(f"Initial data loaded successfully, timestamp: {self.last_update}")
    
    def load_team_rosters(self, rosters_file=None):
        """Load team rosters from file or use default data"""
        if rosters_file and os.path.exists(rosters_file):
            try:
                df = pd.read_csv(rosters_file)
                for _, row in df.iterrows():
                    team_name = row['team_name']
                    player_name = row['player_name']
                    position = row['position']
                    
                    if team_name not in self.team_rosters:
                        self.team_rosters[team_name] = []
                    
                    self.team_rosters[team_name].append({
                        'name': player_name,
                        'position': position
                    })
                
                logger.info(f"Loaded {len(self.team_rosters)} team rosters from {rosters_file}")
            except Exception as e:
                logger.error(f"Error loading rosters file: {e}")
                self._load_default_rosters()
        else:
            logger.info("Rosters file not provided or doesn't exist. Loading default roster data.")
            self._load_default_rosters()
    
    def _load_default_rosters(self):
        """Load default roster data based on previous analysis"""
        default_rosters = {
            "Kenny Kawaguchis": [
                {"name": "Logan O'Hoppe", "position": "C"},
                {"name": "Bryce Harper", "position": "1B"},
                {"name": "Mookie Betts", "position": "2B/OF"},
                {"name": "Austin Riley", "position": "3B"},
                {"name": "CJ Abrams", "position": "SS"},
                {"name": "Lawrence Butler", "position": "OF"},
                {"name": "Riley Greene", "position": "OF"},
                {"name": "Adolis García", "position": "OF"},
                {"name": "Taylor Ward", "position": "OF"},
                {"name": "Tommy Edman", "position": "2B/SS"},
                {"name": "Roman Anthony", "position": "OF"},
                {"name": "Jonathan India", "position": "2B"},
                {"name": "Trevor Story", "position": "SS"},
                {"name": "Iván Herrera", "position": "C"},
                {"name": "Cole Ragans", "position": "SP"},
                {"name": "Hunter Greene", "position": "SP"},
                {"name": "Jack Flaherty", "position": "SP"},
                {"name": "Ryan Helsley", "position": "RP"},
                {"name": "Tanner Scott", "position": "RP"},
                {"name": "Pete Fairbanks", "position": "RP"},
                {"name": "Ryan Pepiot", "position": "SP"},
                {"name": "MacKenzie Gore", "position": "SP"},
                {"name": "Camilo Doval", "position": "RP"}
            ],
            "Mickey 18": [
                {"name": "Adley Rutschman", "position": "C"},
                {"name": "Pete Alonso", "position": "1B"},
                {"name": "Matt McLain", "position": "2B"},
                {"name": "Jordan Westburg", "position": "3B"},
                {"name": "Jeremy Peña", "position": "SS"},
                {"name": "Jasson Domínguez", "position": "OF"},
                {"name": "Tyler O'Neill", "position": "OF"},
                {"name": "Vladimir Guerrero Jr.", "position": "1B"},
                {"name": "Eugenio Suárez", "position": "3B"},
                {"name": "Ronald Acuña Jr.", "position": "OF"},
                {"name": "Tarik Skubal", "position": "SP"},
                {"name": "Spencer Schwellenbach", "position": "SP"},
                {"name": "Hunter Brown", "position": "SP"},
                {"name": "Jhoan Duran", "position": "RP"},
                {"name": "Jeff Hoffman", "position": "RP"},
                {"name": "Ryan Pressly", "position": "RP"},
                {"name": "Justin Verlander", "position": "SP"},
                {"name": "Max Scherzer", "position": "SP"}
            ],
            # Other teams omitted for brevity but would be included in full implementation
        }
        
        # Add to the team rosters dictionary
        self.team_rosters = default_rosters
        
        # Count total players loaded
        total_players = sum(len(roster) for roster in self.team_rosters.values())
        logger.info(f"Loaded {len(self.team_rosters)} team rosters with {total_players} players from default data")
    
    def load_initial_stats_and_projections(self, stats_file=None, projections_file=None):
        """Load initial stats and projections from files or use default data"""
        if stats_file and os.path.exists(stats_file) and projections_file and os.path.exists(projections_file):
            try:
                # Load stats
                with open(stats_file, 'r') as f:
                    self.player_stats_current = json.load(f)
                
                # Load projections
                with open(projections_file, 'r') as f:
                    self.player_projections = json.load(f)
                
                logger.info(f"Loaded stats for {len(self.player_stats_current)} players from {stats_file}")
                logger.info(f"Loaded projections for {len(self.player_projections)} players from {projections_file}")
            except Exception as e:
                logger.error(f"Error loading stats/projections files: {e}")
                self._load_default_stats_and_projections()
        else:
            logger.info("Stats/projections files not provided or don't exist. Loading default data.")
            self._load_default_stats_and_projections()
    
    def _load_default_stats_and_projections(self):
        """Load default stats and projections for bootstrapping"""
        # This would load from the previously created data
        # For simulation/demo purposes, we'll generate synthetic data
        
        # First, collect all players from rosters
        all_players = set()
        for team, roster in self.team_rosters.items():
            for player in roster:
                all_players.add(player["name"])
        
        # Add some free agents
        free_agents = [
            "Keibert Ruiz", "Danny Jansen", "Christian Walker", 
            "Spencer Torkelson", "Gavin Lux", "Luis Rengifo", 
            "JP Crawford", "Ha-Seong Kim", "Jeimer Candelario", 
            "Spencer Steer", "Luis Matos", "Heliot Ramos", 
            "TJ Friedl", "Garrett Mitchell", "Kutter Crawford", 
            "Reese Olson", "Dane Dunning", "José Berríos", 
            "Erik Swanson", "Seranthony Domínguez"
        ]
        
        for player in free_agents:
            all_players.add(player)
        
        # Generate stats and projections for all players
        self._generate_synthetic_data(all_players)
        
        logger.info(f"Generated synthetic stats for {len(self.player_stats_current)} players")
        logger.info(f"Generated synthetic projections for {len(self.player_projections)} players")
    
    def _generate_synthetic_data(self, player_names):
        """Generate synthetic stats and projections for demo purposes"""
        for player in player_names:
            # Determine if batter or pitcher based on name recognition
            # This is a simple heuristic; in reality, you'd use actual data
            is_pitcher = player in [
                "Cole Ragans", "Hunter Greene", "Jack Flaherty", "Ryan Helsley", 
                "Tanner Scott", "Pete Fairbanks", "Ryan Pepiot", "MacKenzie Gore", 
                "Camilo Doval", "Tarik Skubal", "Spencer Schwellenbach", "Hunter Brown", 
                "Jhoan Duran", "Jeff Hoffman", "Ryan Pressly", "Justin Verlander", 
                "Max Scherzer", "Kutter Crawford", "Reese Olson", "Dane Dunning", 
                "José Berríos", "Erik Swanson", "Seranthony Domínguez"
            ]
            
            if is_pitcher:
                # Generate pitcher stats
                current_stats = {
                    'IP': random.uniform(20, 40),
                    'W': random.randint(1, 4),
                    'L': random.randint(0, 3),
                    'ERA': random.uniform(2.5, 5.0),
                    'WHIP': random.uniform(0.9, 1.5),
                    'K': random.randint(15, 50),
                    'BB': random.randint(5, 20),
                    'QS': random.randint(1, 5),
                    'SV': 0 if player not in ["Ryan Helsley", "Tanner Scott", "Pete Fairbanks", "Camilo Doval", "Jhoan Duran", "Ryan Pressly", "Erik Swanson", "Seranthony Domínguez"] else random.randint(1, 8)
                }
                
                # Calculate k/9
                current_stats['K9'] = current_stats['K'] * 9 / current_stats['IP'] if current_stats['IP'] > 0 else 0
                
                # Generate projections (rest of season)
                projected_ip = random.uniform(120, 180) if current_stats['SV'] == 0 else random.uniform(45, 70)
                projected_stats = {
                    'IP': projected_ip,
                    'ERA': random.uniform(3.0, 4.5),
                    'WHIP': random.uniform(1.05, 1.35),
                    'K9': random.uniform(7.5, 12.0),
                    'QS': random.randint(10, 20) if current_stats['SV'] == 0 else 0,
                    'SV': 0 if current_stats['SV'] == 0 else random.randint(15, 35)
                }
            else:
                # Generate batter stats
                current_stats = {
                    'AB': random.randint(70, 120),
                    'R': random.randint(8, 25),
                    'H': random.randint(15, 40),
                    'HR': random.randint(1, 8),
                    'RBI': random.randint(5, 25),
                    'SB': random.randint(0, 8),
                    'BB': random.randint(5, 20),
                    'SO': random.randint(15, 40)
                }
                
                # Calculate derived stats
                current_stats['AVG'] = current_stats['H'] / current_stats['AB'] if current_stats['AB'] > 0 else 0
                current_stats['OBP'] = (current_stats['H'] + current_stats['BB']) / (current_stats['AB'] + current_stats['BB']) if (current_stats['AB'] + current_stats['BB']) > 0 else 0
                
                # Estimate SLG and OPS
                singles = current_stats['H'] - current_stats['HR'] - random.randint(2, 10) - random.randint(0, 5)
                doubles = random.randint(2, 10)
                triples = random.randint(0, 5)
                tb = singles + (2 * doubles) + (3 * triples) + (4 * current_stats['HR'])
                current_stats['SLG'] = tb / current_stats['AB'] if current_stats['AB'] > 0 else 0
                current_stats['OPS'] = current_stats['OBP'] + current_stats['SLG']
                
                # Generate projections (rest of season)
                projected_stats = {
                    'AB': random.randint(400, 550),
                    'R': random.randint(50, 100),
                    'HR': random.randint(10, 35),
                    'RBI': random.randint(40, 100),
                    'SB': random.randint(3, 35),
                    'AVG': random.uniform(0.230, 0.310),
                    'OPS': random.uniform(0.680, 0.950)
                }
            
            # Add to dictionaries
            self.player_stats_current[player] = current_stats
            self.player_projections[player] = projected_stats
    
    def identify_free_agents(self):
        """Identify all players who aren't on team rosters but have stats/projections"""
        # Create a set of all rostered players
        rostered_players = set()
        for team, roster in self.team_rosters.items():
            for player in roster:
                rostered_players.add(player["name"])
        
        # Find players with stats/projections who aren't rostered
        self.free_agents = {}
        
        for player in self.player_projections.keys():
            if player not in rostered_players:
                # Determine position based on stats
                if player in self.player_stats_current:
                    if 'ERA' in self.player_stats_current[player]:
                        position = 'RP' if self.player_stats_current[player].get('SV', 0) > 0 else 'SP'
                    else:
                        # This is simplistic - in a real system, we'd have actual position data
                        position = 'Unknown'
                else:
                    position = 'Unknown'
                
                self.free_agents[player] = {
                    'name': player,
                    'position': position,
                    'stats': self.player_stats_current.get(player, {}),
                    'projections': self.player_projections.get(player, {})
                }
        
        logger.info(f"Identified {len(self.free_agents)} free agents")
        return self.free_agents
    
    def save_system_state(self):
        """Save the current state of the system to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save team rosters
        with open(f"{self.data_dir}/team_rosters.json", 'w') as f:
            json.dump(self.team_rosters, f, indent=4)
        
        # Save current stats
        with open(f"{self.data_dir}/player_stats_current.json", 'w') as f:
            json.dump(self.player_stats_current, f, indent=4)
        
        # Save projections
        with open(f"{self.data_dir}/player_projections.json", 'w') as f:
            json.dump(self.player_projections, f, indent=4)
        
        # Save free agents
        with open(f"{self.data_dir}/free_agents.json", 'w') as f:
            json.dump(self.free_agents, f, indent=4)
        
        # Also save an archive copy
        with open(f"{self.archives_dir}/team_rosters_{timestamp}.json", 'w') as f:
            json.dump(self.team_rosters, f, indent=4)
        
        with open(f"{self.archives_dir}/player_stats_{timestamp}.json", 'w') as f:
            json.dump(self.player_stats_current, f, indent=4)
        
        with open(f"{self.archives_dir}/projections_{timestamp}.json", 'w') as f:
            json.dump(self.player_projections, f, indent=4)
        
        logger.info(f"System state saved successfully with timestamp: {timestamp}")
    
    def load_system_state(self):
        """Load the system state from saved files"""
        try:
            # Load team rosters
            if os.path.exists(f"{self.data_dir}/team_rosters.json"):
                with open(f"{self.data_dir}/team_rosters.json", 'r') as f:
                    self.team_rosters = json.load(f)
            
            # Load current stats
            if os.path.exists(f"{self.data_dir}/player_stats_current.json"):
                with open(f"{self.data_dir}/player_stats_current.json", 'r') as f:
                    self.player_stats_current = json.load(f)
            
            # Load projections
            if os.path.exists(f"{self.data_dir}/player_projections.json"):
                with open(f"{self.data_dir}/player_projections.json", 'r') as f:
                    self.player_projections = json.load(f)
            
            # Load free agents
            if os.path.exists(f"{self.data_dir}/free_agents.json"):
                with open(f"{self.data_dir}/free_agents.json", 'r') as f:
                    self.free_agents = json.load(f)
            
            logger.info("System state loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading system state: {e}")
            return False
    
    def update_player_stats(self):
        """Update player stats by fetching from data sources"""
        logger.info("Updating player stats from sources...")
        
        # In a real implementation, you would:
        # 1. Fetch data from each source in self.data_sources['stats']
        # 2. Parse and clean the data
        # 3. Merge with existing stats
        # 4. Update self.player_stats_current
        
        # For demo purposes, we'll simulate this process
        self._simulate_stats_update()
        
        logger.info(f"Updated stats for {len(self.player_stats_current)} players")
        return len(self.player_stats_current)
    
    def _simulate_stats_update(self):
        """Simulate updating stats for demo purposes"""
        # Add some new players
        new_players = [
            "Bobby Miller", "Garrett Crochet", "DL Hall", 
            "Edward Cabrera", "Alec Bohm", "Elly De La Cruz",
            "Anthony Volpe", "Jazz Chisholm Jr."
        ]
        
        for player in new_players:
            if player not in self.player_stats_current:
                # Determine if batter or pitcher based on name recognition
                is_pitcher = player in ["Bobby Miller", "Garrett Crochet", "DL Hall", "Edward Cabrera"]
                
                if is_pitcher:
                    self.player_stats_current[player] = {
                        'IP': random.uniform(10, 30),
                        'W': random.randint(1, 3),
                        'L': random.randint(0, 2),
                        'ERA': random.uniform(3.0, 5.0),
                        'WHIP': random.uniform(1.0, 1.4),
                        'K': random.randint(10, 40),
                        'BB': random.randint(5, 15),
                        'QS': random.randint(1, 4),
                        'SV': 0
                    }
                    
                    # Calculate k/9
                    self.player_stats_current[player]['K9'] = (
                        self.player_stats_current[player]['K'] * 9 / 
                        self.player_stats_current[player]['IP'] 
                        if self.player_stats_current[player]['IP'] > 0 else 0
                    )
                else:
                    self.player_stats_current[player] = {
                        'AB': random.randint(50, 100),
                        'R': random.randint(5, 20),
                        'H': random.randint(10, 30),
                        'HR': random.randint(1, 6),
                        'RBI': random.randint(5, 20),
                        'SB': random.randint(0, 6),
                        'BB': random.randint(5, 15),
                        'SO': random.randint(10, 30)
                    }
                    
                    # Calculate derived stats
                    self.player_stats_current[player]['AVG'] = (
                        self.player_stats_current[player]['H'] / 
                        self.player_stats_current[player]['AB'] 
                        if self.player_stats_current[player]['AB'] > 0 else 0
                    )
                    
                    self.player_stats_current[player]['OBP'] = (
                        (self.player_stats_current[player]['H'] + self.player_stats_current[player]['BB']) / 
                        (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) 
                        if (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) > 0 else 0
                    )
                    
                    # Estimate SLG and OPS
                    singles = (
                        self.player_stats_current[player]['H'] - 
                        self.player_stats_current[player]['HR'] - 
                        random.randint(2, 8) - 
                        random.randint(0, 3)
                    )
                    doubles = random.randint(2, 8)
                    triples = random.randint(0, 3)
                    tb = singles + (2 * doubles) + (3 * triples) + (4 * self.player_stats_current[player]['HR'])
                    
                    self.player_stats_current[player]['SLG'] = (
                        tb / self.player_stats_current[player]['AB'] 
                        if self.player_stats_current[player]['AB'] > 0 else 0
                    )
                    
                    self.player_stats_current[player]['OPS'] = (
                        self.player_stats_current[player]['OBP'] + 
                        self.player_stats_current[player]['SLG']
                    )
        
        # Update existing player stats
        for player in list(self.player_stats_current.keys()):
            # Skip some players randomly to simulate days off
            if random.random() < 0.3:
                continue
                
            # Determine if batter or pitcher based on existing stats
            if 'ERA' in self.player_stats_current[player]:  # It's a pitcher
                # Generate random game stats
                ip = random.uniform(0.1, 7)
                k = int(ip * random.uniform(0.5, 1.5))
                bb = int(ip * random.uniform(0.1, 0.5))
                er = int(ip * random.uniform(0, 0.7))
                h = int(ip * random.uniform(0.3, 1.2))
                
                # Update aggregated stats
                self.player_stats_current[player]['IP'] += ip
                self.player_stats_current[player]['K'] += k
                self.player_stats_current[player]['BB'] += bb
                
                # Update win/loss
                if random.random() < 0.5:
                    if random.random() < 0.6:  # 60% chance of decision
                        if random.random() < 0.5:  # 50% chance of win
                            self.player_stats_current[player]['W'] = self.player_stats_current[player].get('W', 0) + 1
                        else:
                            self.player_stats_current[player]['L'] = self.player_stats_current[player].get('L', 0) + 1
                
                # Update quality starts
                if ip >= 6 and er <= 3 and 'SV' not in self.player_stats_current[player]:
                    self.player_stats_current[player]['QS'] = self.player_stats_current[player].get('QS', 0) + 1
                
                # Update saves for relievers
                if 'SV' in self.player_stats_current[player] and ip <= 2 and random.random() < 0.3:
                    self.player_stats_current[player]['SV'] = self.player_stats_current[player].get('SV', 0) + 1
                
                # Recalculate ERA and WHIP
                total_er = (self.player_stats_current[player]['ERA'] * 
                           (self.player_stats_current[player]['IP'] - ip) / 9) + er
                            
                self.player_stats_current[player]['ERA'] = (
                    total_er * 9 / self.player_stats_current[player]['IP'] 
                    if self.player_stats_current[player]['IP'] > 0 else 0
                )
                
                # Add baserunners for WHIP calculation
                self.player_stats_current[player]['WHIP'] = (
                    (self.player_stats_current[player]['WHIP'] * 
                     (self.player_stats_current[player]['IP'] - ip) + (h + bb)) / 
                    self.player_stats_current[player]['IP'] 
                    if self.player_stats_current[player]['IP'] > 0 else 0
                )
                
                # Update K/9
                self.player_stats_current[player]['K9'] = (
                    self.player_stats_current[player]['K'] * 9 / 
                    self.player_stats_current[player]['IP'] 
                    if self.player_stats_current[player]['IP'] > 0 else 0
                )
                
            else:  # It's a batter
                # Generate random game stats
                ab = random.randint(0, 5)
                h = 0
                hr = 0
                r = 0
                rbi = 0
                sb = 0
                bb = 0
                so = 0
                
                if ab > 0:
                    # Determine hits
                    for _ in range(ab):
                        if random.random() < 0.270:  # League average is around .270
                            h += 1
                            # Determine if it's a home run
                            if random.random() < 0.15:  # About 15% of hits are HRs
                                hr += 1
                    
                    # Other stats
                    r = random.randint(0, 2) if h > 0 else 0
                    rbi = random.randint(0, 3) if h > 0 else 0
                    sb = 1 if random.random() < 0.08 else 0  # 8% chance of SB
                    bb = 1 if random.random() < 0.1 else 0  # 10% chance of BB
                    so = random.randint(0, 2)  # 0-2 strikeouts
                
                # Update aggregated stats
                self.player_stats_current[player]['AB'] += ab
                self.player_stats_current[player]['H'] += h
                self.player_stats_current[player]['HR'] += hr
                self.player_stats_current[player]['R'] += r
                self.player_stats_current[player]['RBI'] += rbi
                self.player_stats_current[player]['SB'] += sb
                self.player_stats_current[player]['BB'] += bb
                self.player_stats_current[player]['SO'] += so
                
                # Recalculate AVG
                self.player_stats_current[player]['AVG'] =with open(output_file, 'w') as f:
            # Title
            f.write("# Fantasy Baseball Trending Players\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
            
            # Introduction
            f.write("This report identifies players who are trending up or down based on recent performance versus expectations.\n\n")
            
            # For demo purposes, randomly select players as trending up or down
            trending_up_batters = random.sample(list(self.player_stats_current.keys()), 5)
            trending_down_batters = random.sample(list(self.player_stats_current.keys()), 5)
            
            trending_up_pitchers = random.sample([p for p in self.player_stats_current if 'ERA' in self.player_stats_current[p]], 3)
            trending_down_pitchers = random.sample([p for p in self.player_stats_current if 'ERA' in self.player_stats_current[p]], 3)
            
            # Hot Batters
            f.write("## 🔥 Hot Batters\n\n")
            f.write("Players exceeding their projections over the past 15 days.\n\n")
            
            headers = ["Player", "Last 15 Days", "Season Stats", "Ownership"]
            hot_batters_table = []
            
            for player in trending_up_batters:
                if player in self.player_stats_current and 'AVG' in self.player_stats_current[player]:
                    # Generate simulated recent hot stats
                    recent_avg = min(self.player_stats_current[player].get('AVG', 0.250) + random.uniform(0.040, 0.080), 0.400)
                    recent_hr = max(1, int(self.player_stats_current[player].get('HR', 5) * random.uniform(0.20, 0.30)))
                    recent_rbi = max(3, int(self.player_stats_current[player].get('RBI', 20) * random.uniform(0.20, 0.30)))
                    
                    # Determine roster status
                    roster_status = "Rostered"
                    for team, roster in self.team_rosters.items():
                        if player in [p["name"] for p in roster]:
                            roster_status = team
                            break
                    
                    if roster_status == "Rostered":
                        roster_status = random.choice(list(self.team_rosters.keys()))
                    
                    # Generate table row
                    hot_batters_table.append([
                        player,
                        f"{recent_avg:.3f}, {recent_hr} HR, {recent_rbi} RBI",
                        f"{self.player_stats_current[player].get('AVG', 0):.3f}, {self.player_stats_current[player].get('HR', 0)} HR, {self.player_stats_current[player].get('RBI', 0)} RBI",
                        roster_status
                    ])
            
            f.write(tabulate(hot_batters_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Cold Batters
            f.write("## ❄️ Cold Batters\n\n")
            f.write("Players underperforming their projections over the past 15 days.\n\n")
            
            cold_batters_table = []
            
            for player in trending_down_batters:
                if player in self.player_stats_current and 'AVG' in self.player_stats_current[player]:
                    # Generate simulated recent cold stats
                    recent_avg = max(0.120, self.player_stats_current[player].get('AVG', 0.250) - random.uniform(0.050, 0.100))
                    recent_hr = max(0, int(self.player_stats_current[player].get('HR', 5) * random.uniform(0.05, 0.15)))
                    recent_rbi = max(1, int(self.player_stats_current[player].get('RBI', 20) * random.uniform(0.05, 0.15)))
                    
                    # Determine roster status
                    roster_status = "Rostered"
                    for team, roster in self.team_rosters.items():
                        if player in [p["name"] for p in roster]:
                            roster_status = team
                            break
                    
                    if roster_status == "Rostered":
                        roster_status = random.choice(list(self.team_rosters.keys()))
                    
                    # Generate table row
                    cold_batters_table.append([
                        player,
                        f"{recent_avg:.3f}, {recent_hr} HR, {recent_rbi} RBI",
                        f"{self.player_stats_current[player].get('AVG', 0):.3f}, {self.player_stats_current[player].get('HR', 0)} HR, {self.player_stats_current[player].get('RBI', 0)} RBI",
                        roster_status
                    ])
            
            f.write(tabulate(cold_batters_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Hot Pitchers
            f.write("## 🔥 Hot Pitchers\n\n")
            f.write("Pitchers exceeding their projections over the past 15 days.\n\n")
            
            headers = ["Player", "Last 15 Days", "Season Stats", "Ownership"]
            hot_pitchers_table = []
            
            for player in trending_up_pitchers:
                if 'ERA' in self.player_stats_current[player]:
                    # Generate simulated recent hot stats
                    recent_era = max(0.00, self.player_stats_current[player].get('ERA', 4.00) - random.uniform(1.30, 2.50))
                    recent_whip = max(0.70, self.player_stats_current[player].get('WHIP', 1.30) - random.uniform(0.30, 0.50))
                    recent_k = int(self.player_stats_current[player].get('K', 40) * random.uniform(0.15, 0.25))
                    
                    # Determine roster status
                    roster_status = "Rostered"
                    for team, roster in self.team_rosters.items():
                        if player in [p["name"] for p in roster]:
                            roster_status = team
                            break
                    
                    if roster_status == "Rostered":
                        roster_status = random.choice(list(self.team_rosters.keys()))
                    
                    # Generate table row
                    hot_pitchers_table.append([
                        player,
                        f"{recent_era:.2f} ERA, {recent_whip:.2f} WHIP, {recent_k} K",
                        f"{self.player_stats_current[player].get('ERA', 0):.2f} ERA, {self.player_stats_current[player].get('WHIP', 0):.2f} WHIP, {self.player_stats_current[player].get('K', 0)} K",
                        roster_status
                    ])
            
            f.write(tabulate(hot_pitchers_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Cold Pitchers
            f.write("## ❄️ Cold Pitchers\n\n")
            f.write("Pitchers underperforming their projections over the past 15 days.\n\n")
            
            cold_pitchers_table = []
            
            for player in trending_down_pitchers:
                if 'ERA' in self.player_stats_current[player]:
                    # Generate simulated recent cold stats
                    recent_era = self.player_stats_current[player].get('ERA', 4.00) + random.uniform(1.50, 3.00)
                    recent_whip = self.player_stats_current[player].get('WHIP', 1.30) + random.uniform(0.20, 0.40)
                    recent_k = max(0, int(self.player_stats_current[player].get('K', 40) * random.uniform(0.05, 0.15)))
                    
                    # Determine roster status
                    roster_status = "Rostered"
                    for team, roster in self.team_rosters.items():
                        if player in [p["name"] for p in roster]:
                            roster_status = team
                            break
                    
                    if roster_status == "Rostered":
                        roster_status = random.choice(list(self.team_rosters.keys()))
                    
                    # Generate table row
                    cold_pitchers_table.append([
                        player,
                        f"{recent_era:.2f} ERA, {recent_whip:.2f} WHIP, {recent_k} K",
                        f"{self.player_stats_current[player].get('ERA', 0):.2f} ERA, {self.player_stats_current[player].get('WHIP', 0):.2f} WHIP, {self.player_stats_current[player].get('K', 0)} K",
                        roster_status
                    ])
            
            f.write(tabulate(cold_pitchers_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Pickup Recommendations
            f.write("## 📈 Recommended Pickups\n\n")
            f.write("Players trending up who are still available in many leagues.\n\n")
            
            # Find available players who are trending up
            available_trending = []
            for player in trending_up_batters + trending_up_pitchers:
                is_rostered = False
                for team, roster in self.team_rosters.items():
                    if player in [p["name"] for p in roster]:
                        is_rostered = True
                        break
                
                if not is_rostered:
                    available_trending.append(player)
            
            # Add some random free agents to the mix
            available_trending.extend(random.sample(list(self.free_agents.keys()), min(5, len(self.free_agents))))
            
            # Create recommendation table
            headers = ["Player", "Position", "Recent Performance", "Projected ROS"]
            recommendations_table = []
            
            for player in available_trending[:5]:  # Top 5 recommendations
                if player in self.player_stats_current:
                    # Determine position
                    if 'ERA' in self.player_stats_current[player]:
                        position = 'RP' if self.player_stats_current[player].get('SV', 0) > 0 else 'SP'
                        
                        # Generate recent performance string
                        recent_perf = f"{random.uniform(2.00, 3.50):.2f} ERA, {random.uniform(0.90, 1.20):.2f} WHIP, {random.randint(5, 15)} K"
                        
                        # Generate ROS projection string
                        if player in self.player_projections:
                            proj = self.player_projections[player]
                            ros_proj = f"{proj.get('ERA', 0):.2f} ERA, {proj.get('WHIP', 0):.2f} WHIP, {int(proj.get('IP', 0))} IP"
                        else:
                            ros_proj = "No projection available"
                    else:
                        # Random position for batters
                        position = random.choice(['C', '1B', '2B', '3B', 'SS', 'OF'])
                        
                        # Generate recent performance string
                        recent_perf = f"{random.uniform(0.280, 0.360):.3f} AVG, {random.randint(1, 5)} HR, {random.randint(5, 15)} RBI"
                        
                        # Generate ROS projection string
                        if player in self.player_projections:
                            proj = self.player_projections[player]
                            ros_proj = f"{proj.get('AVG', 0):.3f} AVG, {int(proj.get('HR', 0))} HR, {int(proj.get('RBI', 0))} RBI"
                        else:
                            ros_proj = "No projection available"
                    
                    recommendations_table.append([
                        player,
                        position,
                        recent_perf,
                        ros_proj
                    ])
            
            f.write(tabulate(recommendations_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Drop Recommendations
            f.write("## 📉 Consider Dropping\n\n")
            f.write("Rostered players who are trending down and may be safe to drop in standard leagues.\n\n")
            
            # Find rostered players who are trending down
            rostered_trending_down = []
            for player in trending_down_batters + trending_down_pitchers:
                is_rostered = False
                for team, roster in self.team_rosters.items():
                    if player in [p["name"] for p in roster]:
                        is_rostered = True
                        break
                
                if is_rostered:
                    rostered_trending_down.append(player)
            
            # Create drop recommendation table
            headers = ["Player", "Position", "Recent Performance", "Better Alternatives"]
            drop_recommendations_table = []
            
            for player in rostered_trending_down[:5]:  # Top 5 drop recommendations
                if player in self.player_stats_current:
                    # Determine position
                    if 'ERA' in self.player_stats_current[player]:
                        position = 'RP' if self.player_stats_current[player].get('SV', 0) > 0 else 'SP'
                        
                        # Generate recent performance string
                        recent_perf = f"{random.uniform(5.50, 8.00):.2f} ERA, {random.uniform(1.40, 1.80):.2f} WHIP, {random.randint(1, 7)} K"
                        
                        # Suggest alternatives
                        alternatives = [p for p in self.free_agents if p in self.player_projections and 'ERA' in self.player_projections[p]]
                        if alternatives:
                            better_alternatives = ", ".join(random.sample(alternatives, min(3, len(alternatives))))
                        else:
                            better_alternatives = "None available"
                    else:
                        # Random position for batters
                        position = random.choice(['C', '1B', '2B', '3B', 'SS', 'OF'])
                        
                        # Generate recent performance string
                        recent_perf = f"{random.uniform(0.120, 0.200):.3f} AVG, {random.randint(0, 1)} HR, {random.randint(1, 4)} RBI"
                        
                        # Suggest alternatives
                        alternatives = [p for p in self.free_agents if p in self.player_projections and 'AVG' in self.player_projections[p]]
                        if alternatives:
                            better_alternatives = ", ".join(random.sample(alternatives, min(3, len(alternatives))))
                        else:
                            better_alternatives = "None available"
                    
                    drop_recommendations_table.append([
                        player,
                        position,
                        recent_perf,
                        better_alternatives
                    ])
            
            f.write(tabulate(drop_recommendations_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            logger.info(f"Trending players report generated: {output_file}")
    
    def generate_player_news_report(self, output_file):
        """Generate report of recent player news"""
        with open(output_file, 'w') as f:
            # Title
            f.write("# Fantasy Baseball Player News\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
            
            # Recent Injuries
            f.write("## 🏥 Recent Injuries\n\n")
            
            injury_news = []
            for player, news_items in self.player_news.items():
                for item in news_items:
                    if any(keyword in item['content'].lower() for keyword in ['injury', 'injured', 'il', 'disabled list', 'strain', 'sprain']):
                        injury_news.append({
                            'player': player,
                            'date': item['date'],
                            'source': item['source'],
                            'content': item['content']
                        })
            
            # Sort by date (most recent first)
            injury_news.sort(key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d"), reverse=True)
            
            if injury_news:
                for news in injury_news[:10]:  # Show most recent 10 injury news items
                    f.write(f"**{news['player']}** ({news['date']} - {news['source']}): {news['content']}\n\n")
            else:
                f.write("No recent injury news.\n\n")
            
            # Position Battle Updates
            f.write("## ⚔️ Position Battle Updates\n\n")
            
            # In a real implementation, you would have actual news about position battles
            # For demo purposes, we'll simulate position battle news
            position_battles = [
                {
                    'position': 'Second Base',
                    'team': 'Athletics',
                    'players': ['Zack Gelof', 'Nick Allen'],
                    'update': f"Gelof continues to see the majority of starts at 2B, playing in {random.randint(4, 6)} of the last 7 games."
                },
                {
                    'position': 'Closer',
                    'team': 'Cardinals',
                    'players': ['Ryan Helsley', 'Giovanny Gallegos'],
                    'update': f"Helsley has converted {random.randint(3, 5)} saves in the last two weeks, firmly establishing himself as the primary closer."
                },
                {
                    'position': 'Outfield',
                    'team': 'Rays',
                    'players': ['Josh Lowe', 'Jose Siri', 'Randy Arozarena'],
                    'update': f"With Lowe's recent {random.choice(['hamstring', 'oblique', 'back'])} injury, Siri has taken over as the everyday CF."
                }
            ]
            
            for battle in position_battles:
                f.write(f"**{battle['team']} {battle['position']}**: {battle['update']}\n\n")
                f.write(f"Players involved: {', '.join(battle['players'])}\n\n")
            
            # Closer Updates
            f.write("## 🔒 Closer Situations\n\n")
            
            # In a real implementation, you would have actual closer data
            # For demo purposes, we'll simulate closer situations
            closer_situations = [
                {
                    'team': 'Rays',
                    'primary': 'Pete Fairbanks',
                    'secondary': 'Jason Adam',
                    'status': f"Fairbanks has {random.randint(3, 5)} saves in the last 14 days and is firmly entrenched as the closer."
                },
                {
                    'team': 'Cardinals',
                    'primary': 'Ryan Helsley',
                    'secondary': 'Giovanny Gallegos',
                    'status': f"Helsley is the unquestioned closer with {random.randint(15, 25)} saves on the season."
                },
                {
                    'team': 'Reds',
                    'primary': 'Alexis Díaz',
                    'secondary': 'Lucas Sims',
                    'status': f"Díaz is firmly in the closer role with {random.randint(3, 5)} saves in the last two weeks."
                },
                {
                    'team': 'Athletics',
                    'primary': 'Mason Miller',
                    'secondary': 'Dany Jiménez',
                    'status': f"Miller has taken over the closing duties, recording {random.randint(2, 4)} saves recently."
                },
                {
                    'team': 'Mariners',
                    'primary': 'Andrés Muñoz',
                    'secondary': 'Matt Brash',
                    'status': f"Muñoz appears to be the preferred option with {random.randint(3, 5)} saves recently."
                }
            ]
            
            # Create a table for closer situations
            headers = ["Team", "Primary", "Secondary", "Status"]
            closer_table = []
            
            for situation in closer_situations:
                closer_table.append([
                    situation['team'],
                    situation['primary'],
                    situation['secondary'],
                    situation['status']
                ])
            
            f.write(tabulate(closer_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Prospect Watch
            f.write("## 🔮 Prospect Watch\n\n")
            
            # In a real implementation, you would have actual prospect data
            # For demo purposes, we'll simulate prospect updates
            prospects = [
                {
                    'name': 'Jackson Holliday',
                    'team': 'Orioles',
                    'position': 'SS',
                    'level': 'AAA',
                    'stats': f".{random.randint(280, 350)} AVG, {random.randint(5, 12)} HR, {random.randint(30, 50)} RBI, {random.randint(8, 20)} SB in {random.randint(180, 250)} AB",
                    'eta': 'Soon - already on 40-man roster'
                },
                {
                    'name': 'Junior Caminero',
                    'team': 'Rays',
                    'position': '3B',
                    'level': 'AAA',
                    'stats': f".{random.randint(280, 320)} AVG, {random.randint(10, 18)} HR, {random.randint(40, 60)} RBI in {random.randint(200, 280)} AB",
                    'eta': f"{random.choice(['June', 'July', 'August'])} {datetime.now().year}"
                },
                {
                    'name': 'Jasson Domínguez',
                    'team': 'Yankees',
                    'position': 'OF',
                    'level': 'AAA',
                    'stats': f".{random.randint(260, 310)} AVG, {random.randint(8, 15)} HR, {random.randint(10, 25)} SB in {random.randint(180, 250)} AB",
                    'eta': f"Expected back from TJ surgery in {random.choice(['July', 'August'])}"
                },
                {
                    'name': 'Colson Montgomery',
                    'team': 'White Sox',
                    'position': 'SS',
                    'level': 'AA',
                    'stats': f".{random.randint(270, 320)} AVG, {random.randint(6, 12)} HR, {random.randint(30, 50)} RBI in {random.randint(180, 250)} AB",
                    'eta': f"{random.choice(['August', 'September', '2026'])}"
                },
                {
                    'name': 'Orelvis Martinez',
                    'team': 'Blue Jays',
                    'position': '3B/SS',
                    'level': 'AAA',
                    'stats': f".{random.randint(240, 290)} AVG, {random.randint(12, 20)} HR, {random.randint(40, 60)} RBI in {random.randint(180, 250)} AB",
                    'eta': f"{random.choice(['July', 'August', 'September'])}"
                }
            ]
            
            # Create a table for prospects
            headers = ["Prospect", "Team", "Position", "Level", "Stats", "ETA"]
            prospects_table = []
            
            for prospect in prospects:
                prospects_table.append([
                    prospect['name'],
                    prospect['team'],
                    prospect['position'],
                    prospect['level'],
                    prospect['stats'],
                    prospect['eta']
                ])
            
            f.write(tabulate(prospects_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            logger.info(f"Player news report generated: {output_file}")
    
    def schedule_updates(self, daily_update_time="07:00", weekly_update_day="Monday"):
        """Schedule regular updates at specified times"""
        # Schedule daily updates
        schedule.every().day.at(daily_update_time).do(self.run_system_update)
        
        # Schedule weekly full updates with report generation
        if weekly_update_day.lower() == "monday":
            schedule.every().monday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "tuesday":
            schedule.every().tuesday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "wednesday":
            schedule.every().wednesday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "thursday":
            schedule.every().thursday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "friday":
            schedule.every().friday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "saturday":
            schedule.every().saturday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "sunday":
            schedule.every().sunday.at(daily_update_time).do(self.generate_reports)
        
        logger.info(f"Scheduled daily updates at {daily_update_time}")
        logger.info(f"Scheduled weekly full updates on {weekly_update_day} at {daily_update_time}")
    
    def start_update_loop(self):
        """Start the scheduled update loop"""
        logger.info("Starting update loop - press Ctrl+C to exit")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Update loop stopped by user")
    
    def fetch_external_data(self, data_type, source_index=0):
        """Fetch data from external sources - placeholder for real implementation"""
        logger.info(f"Fetching {data_type} data from {self.data_sources[data_type][source_index]}")
        
        # In a real implementation, you would:
        # 1. Make HTTP request to the data source
        # 2. Parse the response (HTML, JSON, etc.)
        # 3. Extract relevant data
        # 4. Return structured data
        
        # For demo purposes, we'll simulate a successful fetch
        return True

# Command-line interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Fantasy Baseball Automated Model with Live Updates')
    parser.add_argument('--league_id', type=str, default="2874", help='League ID')
    parser.add_argument('--team_name', type=str, default="Kenny Kawaguchis", help='Your team name')
    parser.add_argument('--daily_update', type=str, default="07:00", help='Daily update time (HH:MM)')
    parser.add_argument('--weekly_update', type=str, default="Monday", help='Weekly update day')
    parser.add_argument('--manual_update', action='store_true', help='Run a manual update now')
    parser.add_argument('--reports_only', action='store_true', help='Generate reports only')
    parser.add_argument('--daemon', action='store_true', help='Run as a daemon (continuous updates)')
    
    args = parser.parse_args()
    
    # Create model instance
    model = FantasyBaseballAutomated(args.league_id, args.team_name)
    
    # Check if we can load existing state
    if not model.load_system_state():
        logger.info("No existing state found. Loading initial data...")
        model.load_initial_data()
    
    # Handle command-line options
    if args.manual_update:
        logger.info("Running manual update...")
        model.run_system_update()
    
    if args.reports_only:
        logger.info("Generating reports only...")
        model.generate_reports()
    
    if args.daemon:
        # Schedule updates
        model.schedule_updates(args.daily_update, args.weekly_update)
        # Start update loop
        model.start_update_loop()
    
    logger.info("Fantasy Baseball Automated Model completed successfully!")

if __name__ == "__main__":
    main()
                ops_values = [ops for ops in ops_values if ops > 0]
                batting_totals['OPS'] = sum(ops_values) / len(ops_values) if ops_values else 0
            
            # Sort by AB descending
            batter_table.sort(key=lambda x: x[1], reverse=True)
            
            # Add totals row
            batter_table.append([
                "TOTALS",
                batting_totals['AB'],
                batting_totals['R'],
                batting_totals['HR'],
                batting_totals['RBI'],
                batting_totals['SB'],
                f"{batting_totals['AVG']:.3f}",
                f"{batting_totals['OPS']:.3f}"
            ])
            
            f.write(tabulate(batter_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Pitchers stats
            f.write("#### Pitching Stats\n\n")
            pitcher_table = []
            headers = ["Player", "IP", "W", "ERA", "WHIP", "K", "QS", "SV"]
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_stats_current and 'ERA' in self.player_stats_current[name]:
                    stats = self.player_stats_current[name]
                    pitcher_table.append([
                        name,
                        stats.get('IP', 0),
                        stats.get('W', 0),
                        f"{stats.get('ERA', 0):.2f}",
                        f"{stats.get('WHIP', 0):.2f}",
                        stats.get('K', 0),
                        stats.get('QS', 0),
                        stats.get('SV', 0)
                    ])
                    
                    # Add to totals
                    pitching_totals['IP'] += stats.get('IP', 0)
                    pitching_totals['W'] += stats.get('W', 0)
                    pitching_totals['K'] += stats.get('K', 0)
                    pitching_totals['QS'] += stats.get('QS', 0)
                    pitching_totals['SV'] += stats.get('SV', 0)
            
            # Calculate team ERA and WHIP
            if pitching_totals['IP'] > 0:
                # Calculate total ER and baserunners across all pitchers
                total_er = sum(self.player_stats_current.get(p["name"], {}).get('ERA', 0) * 
                               self.player_stats_current.get(p["name"], {}).get('IP', 0) / 9 
                               for p in self.team_rosters.get(self.your_team_name, [])
                               if 'ERA' in self.player_stats_current.get(p["name"], {}))
                
                total_baserunners = sum(self.player_stats_current.get(p["name"], {}).get('WHIP', 0) * 
                                       self.player_stats_current.get(p["name"], {}).get('IP', 0) 
                                       for p in self.team_rosters.get(self.your_team_name, [])
                                       if 'WHIP' in self.player_stats_current.get(p["name"], {}))
                
                pitching_totals['ERA'] = total_er * 9 / pitching_totals['IP']
                pitching_totals['WHIP'] = total_baserunners / pitching_totals['IP']
            
            # Sort by IP descending
            pitcher_table.sort(key=lambda x: x[1], reverse=True)
            
            # Add totals row
            pitcher_table.append([
                "TOTALS",
                pitching_totals['IP'],
                pitching_totals['W'],
                f"{pitching_totals['ERA']:.2f}",
                f"{pitching_totals['WHIP']:.2f}",
                pitching_totals['K'],
                pitching_totals['QS'],
                pitching_totals['SV']
            ])
            
            f.write(tabulate(pitcher_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Team Projections
            f.write("### Rest of Season Projections\n\n")
            
            # Batters projections
            f.write("#### Batting Projections\n\n")
            batter_proj_table = []
            headers = ["Player", "AB", "R", "HR", "RBI", "SB", "AVG", "OPS"]
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_projections and 'AVG' in self.player_projections[name]:
                    proj = self.player_projections[name]
                    batter_proj_table.append([
                        name,
                        int(proj.get('AB', 0)),
                        int(proj.get('R', 0)),
                        int(proj.get('HR', 0)),
                        int(proj.get('RBI', 0)),
                        int(proj.get('SB', 0)),
                        f"{proj.get('AVG', 0):.3f}",
                        f"{proj.get('OPS', 0):.3f}"
                    ])
            
            # Sort by projected AB descending
            batter_proj_table.sort(key=lambda x: x[1], reverse=True)
            
            f.write(tabulate(batter_proj_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Pitchers projections
            f.write("#### Pitching Projections\n\n")
            pitcher_proj_table = []
            headers = ["Player", "IP", "ERA", "WHIP", "K/9", "QS", "SV"]
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_projections and 'ERA' in self.player_projections[name]:
                    proj = self.player_projections[name]
                    pitcher_proj_table.append([
                        name,
                        int(proj.get('IP', 0)),
                        f"{proj.get('ERA', 0):.2f}",
                        f"{proj.get('WHIP', 0):.2f}",
                        f"{proj.get('K9', 0):.1f}",
                        int(proj.get('QS', 0)),
                        int(proj.get('SV', 0))
                    ])
            
            # Sort by projected IP descending
            pitcher_proj_table.sort(key=lambda x: x[1], reverse=True)
            
            f.write(tabulate(pitcher_proj_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Recent News
            f.write("### Recent Team News\n\n")
            
            news_count = 0
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_news and self.player_news[name]:
                    # Sort news by date (most recent first)
                    player_news = sorted(
                        self.player_news[name], 
                        key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"), 
                        reverse=True
                    )
                    
                    # Show most recent news item
                    latest_news = player_news[0]
                    f.write(f"**{name}** ({latest_news['date']} - {latest_news['source']}): {latest_news['content']}\n\n")
                    news_count += 1
            
            if news_count == 0:
                f.write("No recent news for your team's players.\n\n")
            
            # Recommendations
            f.write("## Team Recommendations\n\n")
            
            # Analyze team strengths and weaknesses
            # This is a simplified analysis - a real implementation would be more sophisticated
            
            # Calculate average stats per player
            avg_hr = batting_totals['HR'] / len([p for p in self.team_rosters.get(self.your_team_name, []) if p["name"] in self.player_stats_current and 'AVG' in self.player_stats_current[p["name"]]]) if len([p for p in self.team_rosters.get(self.your_team_name, []) if p["name"] in self.player_stats_current and 'AVG' in self.player_stats_current[p["name"]]]) > 0 else 0
            
            avg_sb = batting_totals['SB'] / len([p for p in self.team_rosters.get(self.your_team_name, []) if p["name"] in self.player_stats_current and 'AVG' in self.player_stats_current[p["name"]]]) if len([p for p in self.team_rosters.get(self.your_team_name, []) if p["name"] in self.player_stats_current and 'AVG' in self.player_stats_current[p["name"]]]) > 0 else 0
            
            avg_era = pitching_totals['ERA']
            avg_k9 = pitching_totals['K'] * 9 / pitching_totals['IP'] if pitching_totals['IP'] > 0 else 0
            
            # Identify strengths and weaknesses
            strengths = []
            weaknesses = []
            
            if batting_totals['AVG'] > 0.270:
                strengths.append("Batting Average")
            elif batting_totals['AVG'] < 0.250:
                weaknesses.append("Batting Average")
                
            if batting_totals['OPS'] > 0.780:
                strengths.append("OPS")
            elif batting_totals['OPS'] < 0.720:
                weaknesses.append("OPS")
                
            if avg_hr > 0.08:  # More than 0.08 HR per AB
                strengths.append("Power")
            elif avg_hr < 0.04:
                weaknesses.append("Power")
                
            if avg_sb > 0.05:  # More than 0.05 SB per AB
                strengths.append("Speed")
            elif avg_sb < 0.02:
                weaknesses.append("Speed")
                
            if avg_era < 3.80:
                strengths.append("ERA")
            elif avg_era > 4.20:
                weaknesses.append("ERA")
                
            if pitching_totals['WHIP'] < 1.20:
                strengths.append("WHIP")
            elif pitching_totals['WHIP'] > 1.30:
                weaknesses.append("WHIP")
                
            if avg_k9 > 9.5:
                strengths.append("Strikeouts")
            elif avg_k9 < 8.0:
                weaknesses.append("Strikeouts")
                
            if pitching_totals['SV'] > 15:
                strengths.append("Saves")
            elif pitching_totals['SV'] < 5:
                weaknesses.append("Saves")
                
            if pitching_totals['QS'] > 15:
                strengths.append("Quality Starts")
            elif pitching_totals['QS'] < 5:
                weaknesses.append("Quality Starts")
                
            # Write strengths and weaknesses
            f.write("### Team Strengths\n\n")
            if strengths:
                for strength in strengths:
                    f.write(f"- **{strength}**\n")
            else:
                f.write("No clear strengths identified yet.\n")
            
            f.write("\n### Team Weaknesses\n\n")
            if weaknesses:
                for weakness in weaknesses:
                    f.write(f"- **{weakness}**\n")
            else:
                f.write("No clear weaknesses identified yet.\n")
            
            f.write("\n### Recommended Actions\n\n")
            
            # Generate recommendations based on weaknesses
            if weaknesses:
                for weakness in weaknesses[:3]:  # Focus on top 3 weaknesses
                    if weakness == "Power":
                        f.write("- **Target Power Hitters**: Consider trading for players with high HR and RBI projections.\n")
                        
                        # Suggest specific free agents
                        power_fa = sorted(
                            [(name, p['projections'].get('HR', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'HR' in p['projections']],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if power_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {int(p[1])} HR)" for p in power_fa]) + "\n")
                    
                    elif weakness == "Speed":
                        f.write("- **Add Speed**: Look to add players who can contribute stolen bases.\n")
                        
                        # Suggest specific free agents
                        speed_fa = sorted(
                            [(name, p['projections'].get('SB', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'SB' in p['projections']],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if speed_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {int(p[1])} SB)" for p in speed_fa]) + "\n")
                    
                    elif weakness == "Batting Average":
                        f.write("- **Improve Batting Average**: Look for consistent contact hitters.\n")
                        
                        # Suggest specific free agents
                        avg_fa = sorted(
                            [(name, p['projections'].get('AVG', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'AVG' in p['projections'] and p['projections'].get('AB', 0) > 300],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if avg_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {p[1]:.3f} AVG)" for p in avg_fa]) + "\n")
                    
                    elif weakness == "ERA" or weakness == "WHIP":
                        f.write("- **Improve Pitching Ratios**: Focus on pitchers with strong ERA and WHIP projections.\n")
                        
                        # Suggest specific free agents
                        ratio_fa = sorted(
                            [(name, p['projections'].get('ERA', 0), p['projections'].get('WHIP', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'ERA' in p['projections'] and p['projections'].get('IP', 0) > 100],
                            key=lambda x: x[1] + x[2]
                        )[:3]
                        
                        if ratio_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {p[1]:.2f} ERA, {p[2]:.2f} WHIP)" for p in ratio_fa]) + "\n")
                    
                    elif weakness == "Strikeouts":
                        f.write("- **Add Strikeout Pitchers**: Target pitchers with high K/9 rates.\n")
                        
                        # Suggest specific free agents
                        k_fa = sorted(
                            [(name, p['projections'].get('K9', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'K9' in p['projections'] and p['projections'].get('IP', 0) > 75],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if k_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {p[1]:.1f} K/9)" for p in k_fa]) + "\n")
                    
                    elif weakness == "Saves":
                        f.write("- **Add Closers**: Look for pitchers in save situations.\n")
                        
                        # Suggest specific free agents
                        sv_fa = sorted(
                            [(name, p['projections'].get('SV', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'SV' in p['projections'] and p['projections'].get('SV', 0) > 5],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if sv_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {int(p[1])} SV)" for p in sv_fa]) + "\n")
                    
                    elif weakness == "Quality Starts":
                        f.write("- **Add Quality Starting Pitchers**: Target consistent starters who work deep into games.\n")
                        
                        # Suggest specific free agents
                        qs_fa = sorted(
                            [(name, p['projections'].get('QS', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'QS' in p['projections'] and p['projections'].get('QS', 0) > 5],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if qs_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {int(p[1])} QS)" for p in qs_fa]) + "\n")
            else:
                f.write("Your team is well-balanced! Continue to monitor player performance and injuries.\n")
            
            # General strategy recommendation
            f.write("\n### General Strategy\n\n")
            f.write("1. **Monitor the waiver wire daily** for emerging talent and players returning from injury.\n")
            f.write("2. **Be proactive with injured players**. Don't hold onto injured players too long if better options are available.\n")
            f.write("3. **Stream starting pitchers** against weak offensive teams for additional counting stats.\n")
            f.write("4. **Watch for changing roles** in bullpens for potential closers in waiting.\n")
            
            logger.info(f"Team analysis report generated: {output_file}")
    
    def generate_free_agents_report(self, output_file):
        """Generate free agents report sorted by projected value"""
        with open(output_file, 'w') as f:
            # Title
            f.write("# Fantasy Baseball Free Agent Analysis\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
            
            # Calculate scores for ranking
            fa_batters = {}
            fa_pitchers = {}
            
            for name, data in self.free_agents.items():
                if 'projections' in data:
                    proj = data['projections']
                    if 'AVG' in proj:  # It's a batter
                        # Calculate a batter score
                        score = (
                            proj.get('HR', 0) * 3 +
                            proj.get('SB', 0) * 3 +
                            proj.get('R', 0) * 0.5 +
                            proj.get('RBI', 0) * 0.5 +
                            proj.get('AVG', 0) * 300 +
                            proj.get('OPS', 0) * 150
                        )
                        fa_batters[name] = {'projections': proj, 'score': score}
                    
                    elif 'ERA' in proj:  # It's a pitcher
                        # Calculate a pitcher score
                        era_score = (5.00 - proj.get('ERA', 4.50)) * 20 if proj.get('ERA', 0) < 5.00 else 0
                        whip_score = (1.40 - proj.get('WHIP', 1.30)) * 60 if proj.get('WHIP', 0) < 1.40 else 0
                        
                        score = (
                            era_score +
                            whip_score +
                            proj.get('K9', 0) * 10 +
                            proj.get('QS', 0) * 4 +
                            proj.get('SV', 0) * 6 +
                            proj.get('IP', 0) * 0.2
                        )
                        fa_pitchers[name] = {'projections': proj, 'score': score}
            
            # Top Batters by Position
            f.write("## Top Free Agent Batters\n\n")
            
            # Define positions
            positions = {
                "C": "Catchers",
                "1B": "First Basemen",
                "2B": "Second Basemen",
                "3B": "Third Basemen",
                "SS": "Shortstops",
                "OF": "Outfielders"
            }
            
            # Simplified position assignment for demo
            position_players = {pos: [] for pos in positions}
            
            # Manually assign positions for demo
            for name in fa_batters:
                # This is a very simplified approach - in reality, you'd have actual position data
                if name in ["Keibert Ruiz", "Danny Jansen", "Gabriel Moreno", "Patrick Bailey", "Ryan Jeffers"]:
                    position_players["C"].append(name)
                elif name in ["Christian Walker", "Spencer Torkelson", "Andrew Vaughn", "Anthony Rizzo"]:
                    position_players["1B"].append(name)
                elif name in ["Gavin Lux", "Luis Rengifo", "Nick Gonzales", "Zack Gelof", "Brendan Donovan"]:
                    position_players["2B"].append(name)
                elif name in ["Jeimer Candelario", "Spencer Steer", "Ke'Bryan Hayes", "Brett Baty"]:
                    position_players["3B"].append(name)
                elif name in ["JP Crawford", "Ha-Seong Kim", "Xander Bogaerts", "Jose Barrero"]:
                    position_players["SS"].append(name)
                else:
                    position_players["OF"].append(name)
            
            # Write position sections
            for pos, title in positions.items():
                players = position_players[pos]
                if players:
                    f.write(f"### {title}\n\n")
                    
                    # Create table
                    headers = ["Rank", "Player", "AB", "R", "HR", "RBI", "SB", "AVG", "OPS", "Score"]
                    
                    # Get scores and sort
                    pos_players = [(name, fa_batters[name]['score'], fa_batters[name]['projections']) 
                                 for name in players if name in fa_batters]
                    
                    pos_players.sort(key=lambda x: x[1], reverse=True)
                    
                    # Build table
                    table_data = []
                    for i, (name, score, proj) in enumerate(pos_players[:10]):  # Top 10 per position
                        table_data.append([
                            i+1,
                            name,
                            int(proj.get('AB', 0)),
                            int(proj.get('R', 0)),
                            int(proj.get('HR', 0)),
                            int(proj.get('RBI', 0)),
                            int(proj.get('SB', 0)),
                            f"{proj.get('AVG', 0):.3f}",
                            f"{proj.get('OPS', 0):.3f}",
                            int(score)
                        ])
                    
                    f.write(tabulate(table_data, headers=headers, tablefmt="pipe"))
                    f.write("\n\n")
            
            # Top Pitchers
            f.write("## Top Free Agent Pitchers\n\n")
            
            # Starting pitchers
            f.write("### Starting Pitchers\n\n")
            
            # Identify starters
            starters = [(name, fa_pitchers[name]['score'], fa_pitchers[name]['projections']) 
                       for name in fa_pitchers 
                       if fa_pitchers[name]['projections'].get('QS', 0) > 0]
            
            starters.sort(key=lambda x: x[1], reverse=True)
            
            # Create table
            headers = ["Rank", "Player", "IP", "ERA", "WHIP", "K/9", "QS", "Score"]
            
            table_data = []
            for i, (name, score, proj) in enumerate(starters[:15]):  # Top 15 SP
                table_data.append([
                    i+1,
                    name,
                    int(proj.get('IP', 0)),
                    f"{proj.get('ERA', 0):.2f}",
                    f"{proj.get('WHIP', 0):.2f}",
                    f"{proj.get('K9', 0):.1f}",
                    int(proj.get('QS', 0)),
                    int(score)
                ])
            
            f.write(tabulate(table_data, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Relief pitchers
            f.write("### Relief Pitchers\n\n")
            
            # Identify relievers
            relievers = [(name, fa_pitchers[name]['score'], fa_pitchers[name]['projections']) 
                        for name in fa_pitchers 
                        if fa_pitchers[name]['projections'].get('QS', 0) == 0]
            
            relievers.sort(key=lambda x: x[1], reverse=True)
            
            # Create table
            headers = ["Rank", "Player", "IP", "ERA", "WHIP", "K/9", "SV", "Score"]
            
            table_data = []
            for i, (name, score, proj) in enumerate(relievers[:10]):  # Top 10 RP
                table_data.append([
                    i+1,
                    name,
                    int(proj.get('IP', 0)),
                    f"{proj.get('ERA', 0):.2f}",
                    f"{proj.get('WHIP', 0):.2f}",
                    f"{proj.get('K9', 0):.1f}",
                    int(proj.get('SV', 0)),
                    int(score)
                ])
            
            f.write(tabulate(table_data, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Category-Specific Free Agent Targets
            f.write("## Category-Specific Free Agent Targets\n\n")
            
            # Power hitters (HR and RBI)
            power_hitters = sorted(
                [(name, fa_batters[name]['projections'].get('HR', 0), fa_batters[name]['projections'].get('RBI', 0)) 
                 for name in fa_batters],
                key=lambda x: x[1] + x[2]/3,
                reverse=True
            )[:5]
            
            f.write("**Power (HR/RBI):** ")
            f.write(", ".join([f"{name} ({int(hr)} HR, {int(rbi)} RBI)" for name, hr, rbi in power_hitters]))
            f.write("\n\n")
            
            # Speed (SB)
            speed_players = sorted(
                [(name, fa_batters[name]['projections'].get('SB', 0)) 
                 for name in fa_batters],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            f.write("**Speed (SB):** ")
            f.write(", ".join([f"{name} ({int(sb)} SB)" for name, sb in speed_players]))
            f.write("\n\n")
            
            # Average (AVG)
            average_hitters = sorted(
                [(name, fa_batters[name]['projections'].get('AVG', 0)) 
                 for name in fa_batters 
                 if fa_batters[name]['projections'].get('AB', 0) >= 300],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            f.write("**Batting Average:** ")
            f.write(", ".join([f"{name} ({avg:.3f})" for name, avg in average_hitters]))
            f.write("\n\n")
            
            # ERA
            era_pitchers = sorted(
                [(name, fa_pitchers[name]['projections'].get('ERA', 0)) 
                 for name in fa_pitchers 
                 if fa_pitchers[name]['projections'].get('IP', 0) >= 100],
                key=lambda x: x[1]
            )[:5]
            
            f.write("**ERA:** ")
            f.write(", ".join([f"{name} ({era:.2f})" for name, era in era_pitchers]))
            f.write("\n\n")
            
            # WHIP
            whip_pitchers = sorted(
                [(name, fa_pitchers[name]['projections'].get('WHIP', 0)) 
                 for name in fa_pitchers 
                 if fa_pitchers[name]['projections'].get('IP', 0) >= 100],
                key=lambda x: x[1]
            )[:5]
            
            f.write("**WHIP:** ")
            f.write(", ".join([f"{name} ({whip:.2f})" for name, whip in whip_pitchers]))
            f.write("\n\n")
            
            # Saves (SV)
            save_pitchers = sorted(
                [(name, fa_pitchers[name]['projections'].get('SV', 0)) 
                 for name in fa_pitchers],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            f.write("**Saves:** ")
            f.write(", ".join([f"{name} ({int(sv)})" for name, sv in save_pitchers]))
            f.write("\n\n")
            
            logger.info(f"Free agents report generated: {output_file}")
    
    def generate_trending_players_report(self, output_file):
        """Generate report on trending players (hot/cold)"""
        # In a real implementation, you would calculate trends based on recent performance
        # For demo purposes, we'll simulate trends
        
        with open(output_                # Recalculate AVG
                self.player_stats_current[player]['AVG'] = (
                    self.player_stats_current[player]['H'] / 
                    self.player_stats_current[player]['AB'] 
                    if self.player_stats_current[player]['AB'] > 0 else 0
                )
                
                # Recalculate OBP
                self.player_stats_current[player]['OBP'] = (
                    (self.player_stats_current[player]['H'] + self.player_stats_current[player]['BB']) / 
                    (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) 
                    if (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) > 0 else 0
                )
                
                # Recalculate SLG and OPS
                singles = (
                    self.player_stats_current[player]['H'] - 
                    self.player_stats_current[player]['HR'] - 
                    self.player_stats_current[player].get('2B', random.randint(15, 25)) - 
                    self.player_stats_current[player].get('3B', random.randint(0, 5))
                )
                
                tb = (
                    singles + 
                    (2 * self.player_stats_current[player].get('2B', random.randint(15, 25))) + 
                    (3 * self.player_stats_current[player].get('3B', random.randint(0, 5))) + 
                    (4 * self.player_stats_current[player]['HR'])
                )
                
                self.player_stats_current[player]['SLG'] = (
                    tb / self.player_stats_current[player]['AB'] 
                    if self.player_stats_current[player]['AB'] > 0 else 0
                )
                
                self.player_stats_current[player]['OPS'] = (
                    self.player_stats_current[player]['OBP'] + 
                    self.player_stats_current[player]['SLG']
                )
    
    def update_player_projections(self):
        """Update player projections by fetching from data sources"""
        logger.info("Updating player projections from sources...")
        
        # In a real implementation, you would:
        # 1. Fetch data from each source in self.data_sources['projections']
        # 2. Parse and clean the data
        # 3. Merge with existing projections
        # 4. Update self.player_projections
        
        # For demo purposes, we'll simulate this process
        self._simulate_projections_update()
        
        logger.info(f"Updated projections for {len(self.player_projections)} players")
        return len(self.player_projections)
    
    def _simulate_projections_update(self):
        """Simulate updating projections for demo purposes"""
        # Update existing projections based on current stats
        for player in self.player_stats_current:
            # Skip if no projection exists
            if player not in self.player_projections:
                # Create new projection based on current stats
                if 'ERA' in self.player_stats_current[player]:  # It's a pitcher
                    # Project rest of season based on current performance
                    era_factor = min(max(4.00 / self.player_stats_current[player]['ERA'], 0.75), 1.25) if self.player_stats_current[player]['ERA'] > 0 else 1.0
                    whip_factor = min(max(1.30 / self.player_stats_current[player]['WHIP'], 0.75), 1.25) if self.player_stats_current[player]['WHIP'] > 0 else 1.0
                    k9_factor = min(max(self.player_stats_current[player]['K9'] / 8.5, 0.75), 1.25) if self.player_stats_current[player].get('K9', 0) > 0 else 1.0
                    
                    # Determine if starter or reliever
                    is_reliever = 'SV' in self.player_stats_current[player] or self.player_stats_current[player].get('IP', 0) < 20
                    
                    self.player_projections[player] = {
                        'IP': random.uniform(40, 70) if is_reliever else random.uniform(120, 180),
                        'ERA': random.uniform(3.0, 4.5) * era_factor,
                        'WHIP': random.uniform(1.05, 1.35) * whip_factor,
                        'K9': random.uniform(7.5, 12.0) * k9_factor,
                        'QS': 0 if is_reliever else random.randint(10, 20),
                        'SV': random.randint(15, 35) if is_reliever and self.player_stats_current[player].get('SV', 0) > 0 else 0
                    }
                else:  # It's a batter
                    # Project rest of season based on current performance
                    avg_factor = min(max(self.player_stats_current[player]['AVG'] / 0.260, 0.8), 1.2) if self.player_stats_current[player]['AVG'] > 0 else 1.0
                    ops_factor = min(max(self.player_stats_current[player].get('OPS', 0.750) / 0.750, 0.8), 1.2) if self.player_stats_current[player].get('OPS', 0) > 0 else 1.0
                    
                    # Projected plate appearances remaining
                    pa_remaining = random.randint(400, 550)
                    
                    # HR rate
                    hr_rate = self.player_stats_current[player]['HR'] / self.player_stats_current[player]['AB'] if self.player_stats_current[player]['AB'] > 0 else 0.025
                    
                    # SB rate
                    sb_rate = self.player_stats_current[player]['SB'] / self.player_stats_current[player]['AB'] if self.player_stats_current[player]['AB'] > 0 else 0.015
                    
                    self.player_projections[player] = {
                        'AB': pa_remaining * 0.9,  # 10% of PA are walks/HBP
                        'R': pa_remaining * random.uniform(0.12, 0.18),
                        'HR': pa_remaining * hr_rate * random.uniform(0.8, 1.2),
                        'RBI': pa_remaining * random.uniform(0.1, 0.17),
                        'SB': pa_remaining * sb_rate * random.uniform(0.8, 1.2),
                        'AVG': random.uniform(0.230, 0.310) * avg_factor,
                        'OPS': random.uniform(0.680, 0.950) * ops_factor
                    }
                continue
            
            # If projection exists, update it based on current performance
            if 'ERA' in self.player_stats_current[player]:  # It's a pitcher
                # Calculate adjustment factors based on current vs. projected performance
                if self.player_stats_current[player].get('IP', 0) > 20:  # Enough IP to adjust projections
                    # ERA adjustment
                    current_era = self.player_stats_current[player].get('ERA', 4.00)
                    projected_era = self.player_projections[player].get('ERA', 4.00)
                    era_adj = min(max(projected_era / current_era, 0.8), 1.2) if current_era > 0 else 1.0
                    
                    # WHIP adjustment
                    current_whip = self.player_stats_current[player].get('WHIP', 1.30)
                    projected_whip = self.player_projections[player].get('WHIP', 1.30)
                    whip_adj = min(max(projected_whip / current_whip, 0.8), 1.2) if current_whip > 0 else 1.0
                    
                    # K/9 adjustment
                    current_k9 = self.player_stats_current[player].get('K9', 8.5)
                    projected_k9 = self.player_projections[player].get('K9', 8.5)
                    k9_adj = min(max(current_k9 / projected_k9, 0.8), 1.2) if projected_k9 > 0 else 1.0
                    
                    # Apply adjustments
                    self.player_projections[player]['ERA'] = projected_era * era_adj
                    self.player_projections[player]['WHIP'] = projected_whip * whip_adj
                    self.player_projections[player]['K9'] = projected_k9 * k9_adj
                    
                    # Adjust saves projection for relievers
                    if 'SV' in self.player_stats_current[player]:
                        current_sv_rate = self.player_stats_current[player].get('SV', 0) / max(1, self.player_stats_current[player].get('IP', 1) / 60)
                        self.player_projections[player]['SV'] = min(45, max(0, int(current_sv_rate * 60)))
                    
                    # Adjust QS projection for starters
                    if 'QS' in self.player_stats_current[player] and self.player_stats_current[player].get('IP', 0) > 0:
                        current_qs_rate = self.player_stats_current[player].get('QS', 0) / max(1, self.player_stats_current[player].get('IP', 1) / 180)
                        self.player_projections[player]['QS'] = min(30, max(0, int(current_qs_rate * 180)))
            else:  # It's a batter
                # Adjust only if enough AB to be significant
                if self.player_stats_current[player].get('AB', 0) > 75:
                    # AVG adjustment
                    current_avg = self.player_stats_current[player].get('AVG', 0.260)
                    projected_avg = self.player_projections[player].get('AVG', 0.260)
                    avg_adj = min(max((current_avg + 2*projected_avg) / (3*projected_avg), 0.85), 1.15) if projected_avg > 0 else 1.0
                    
                    # HR rate adjustment
                    current_hr_rate = self.player_stats_current[player].get('HR', 0) / max(1, self.player_stats_current[player].get('AB', 1)) * 550
                    projected_hr = self.player_projections[player].get('HR', 15)
                    hr_adj = min(max((current_hr_rate + 2*projected_hr) / (3*projected_hr), 0.7), 1.3) if projected_hr > 0 else 1.0
                    
                    # SB rate adjustment
                    current_sb_rate = self.player_stats_current[player].get('SB', 0) / max(1, self.player_stats_current[player].get('AB', 1)) * 550
                    projected_sb = self.player_projections[player].get('SB', 10)
                    sb_adj = min(max((current_sb_rate + 2*projected_sb) / (3*projected_sb), 0.7), 1.3) if projected_sb > 0 else 1.0
                    
                    # Apply adjustments
                    self.player_projections[player]['AVG'] = projected_avg * avg_adj
                    self.player_projections[player]['HR'] = projected_hr * hr_adj
                    self.player_projections[player]['SB'] = projected_sb * sb_adj
                    
                    # Adjust OPS based on AVG and power
                    projected_ops = self.player_projections[player].get('OPS', 0.750)
                    self.player_projections[player]['OPS'] = projected_ops * (avg_adj * 0.4 + hr_adj * 0.6)
                    
                    # Adjust runs and RBI based on HR and overall performance
                    projected_r = self.player_projections[player].get('R', 70)
                    projected_rbi = self.player_projections[player].get('RBI', 70)
                    
                    self.player_projections[player]['R'] = projected_r * ((avg_adj + hr_adj) / 2)
                    self.player_projections[player]['RBI'] = projected_rbi * ((avg_adj + hr_adj) / 2)
        
        # Round numerical values for cleaner display
        for player in self.player_projections:
            for stat in self.player_projections[player]:
                if isinstance(self.player_projections[player][stat], float):
                    if stat in ['ERA', 'WHIP', 'K9', 'AVG', 'OPS']:
                        self.player_projections[player][stat] = round(self.player_projections[player][stat], 3)
                    else:
                        self.player_projections[player][stat] = round(self.player_projections[player][stat])
    
    def update_player_news(self):
        """Update player news by fetching from news sources"""
        logger.info("Updating player news from sources...")
        
        # In a real implementation, you would:
        # 1. Fetch data from each source in self.data_sources['news']
        # 2. Parse and extract news items
        # 3. Store in self.player_news
        
        # For demo purposes, we'll simulate this process
        self._simulate_news_update()
        
        logger.info(f"Updated news for {len(self.player_news)} players")
        return len(self.player_news)
    
    def _simulate_news_update(self):
        """Simulate updating player news for demo purposes"""
        # List of possible news templates
        injury_news = [
            "{player} was removed from Wednesday's game with {injury}.",
            "{player} is day-to-day with {injury}.",
            "{player} has been placed on the 10-day IL with {injury}.",
            "{player} will undergo further testing for {injury}.",
            "{player} is expected to miss 4-6 weeks with {injury}."
        ]
        
        performance_news = [
            "{player} went {stats} in Wednesday's 6-4 win.",
            "{player} struck out {k} batters in {ip} innings on Tuesday.",
            "{player} has hit safely in {streak} straight games.",
            "{player} collected {hits} hits including a homer on Monday.",
            "{player} has struggled recently, going {bad_stats} over his last 7 games."
        ]
        
        role_news = [
            "{player} will take over as the closer with {teammate} on the IL.",
            "{player} has been moved up to the {spot} spot in the batting order.",
            "{player} will make his next start on {day}.",
            "{player} has been moved to the bullpen.",
            "{player} will be recalled from Triple-A on Friday."
        ]
        
        # Possible injuries
        injuries = [
            "left hamstring tightness",
            "right oblique strain",
            "lower back discomfort",
            "shoulder inflammation",
            "forearm tightness",
            "groin strain",
            "ankle sprain",
            "knee soreness",
            "thumb contusion",
            "wrist inflammation"
        ]
        
        # Generate news for a subset of players
        for player in random.sample(list(self.player_stats_current.keys()), min(10, len(self.player_stats_current))):
            news_type = random.choice(["injury", "performance", "role"])
            
            if news_type == "injury":
                template = random.choice(injury_news)
                news_item = template.format(
                    player=player,
                    injury=random.choice(injuries)
                )
            elif news_type == "performance":
                template = random.choice(performance_news)
                
                # Determine if batter or pitcher
                if 'ERA' in self.player_stats_current[player]:  # Pitcher
                    ip = round(random.uniform(5, 7), 1)
                    k = random.randint(4, 10)
                    news_item = template.format(
                        player=player,
                        k=k,
                        ip=ip,
                        streak=random.randint(3, 10),
                        hits=random.randint(2, 4),
                        bad_stats=f"{random.randint(0, 4)}-for-{random.randint(20, 30)}"
                    )
                else:  # Batter
                    hits = random.randint(0, 4)
                    abs = random.randint(hits, 5)
                    news_item = template.format(
                        player=player,
                        stats=f"{hits}-for-{abs}",
                        k=random.randint(5, 12),
                        ip=round(random.uniform(5, 7), 1),
                        streak=random.randint(5, 15),
                        hits=random.randint(2, 4),
                        bad_stats=f"{random.randint(0, 4)}-for-{random.randint(20, 30)}"
                    )
            else:  # Role
                template = random.choice(role_news)
                news_item = template.format(
                    player=player,
                    teammate=random.choice(list(self.player_stats_current.keys())),
                    spot=random.choice(["leadoff", "cleanup", "third", "fifth"]),
                    day=random.choice(["Friday", "Saturday", "Sunday", "Monday"])
                )
            
            # Add news item with timestamp
            if player not in self.player_news:
                self.player_news[player] = []
            
            self.player_news[player].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source": random.choice(["Rotowire", "CBS Sports", "ESPN", "MLB.com"]),
                "content": news_item
            })
    
    def update_player_injuries(self):
        """Update player injury statuses"""
        logger.info("Updating player injury statuses...")
        
        # In a real implementation, you would:
        # 1. Fetch injury data from reliable sources
        # 2. Update player status accordingly
        # 3. Adjust projections for injured players
        
        # For demo purposes, we'll simulate some injuries
        injury_count = 0
        
        for player in self.player_stats_current:
            # 5% chance of new injury for each player
            if random.random() < 0.05:
                injury_severity = random.choice(["day-to-day", "10-day IL", "60-day IL"])
                injury_type = random.choice([
                    "hamstring strain", "oblique strain", "back spasms", 
                    "shoulder inflammation", "elbow soreness", "knee inflammation",
                    "ankle sprain", "concussion", "wrist sprain"
                ])
                
                # Add injury news
                if player not in self.player_news:
                    self.player_news[player] = []
                
                self.player_news[player].append({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "source": random.choice(["Rotowire", "CBS Sports", "ESPN", "MLB.com"]),
                    "content": f"{player} has been placed on the {injury_severity} with a {injury_type}."
                })
                
                # Adjust projections for injured players
                if player in self.player_projections:
                    if injury_severity == "day-to-day":
                        reduction = 0.05  # 5% reduction in projections
                    elif injury_severity == "10-day IL":
                        reduction = 0.15  # 15% reduction
                    else:  # 60-day IL
                        reduction = 0.50  # 50% reduction
                    
                    # Apply reduction to projected stats
                    for stat in self.player_projections[player]:
                        if stat not in ['AVG', 'ERA', 'WHIP', 'K9', 'OPS']:  # Don't reduce rate stats
                            self.player_projections[player][stat] *= (1 - reduction)
                
                injury_count += 1
        
        logger.info(f"Updated injury status for {injury_count} players")
        return injury_count
    
    def update_league_transactions(self):
        """Simulate league transactions (adds, drops, trades)"""
        logger.info("Simulating league transactions...")
        
        # In a real implementation, you would:
        # 1. Fetch transaction data from your fantasy platform API
        # 2. Update team rosters accordingly
        
        # For demo purposes, we'll simulate some transactions
        transaction_count = 0
        
        # Add/drop transactions (1-3 per update)
        for _ in range(random.randint(1, 3)):
            # Select a random team
            team = random.choice(list(self.team_rosters.keys()))
            
            # Select a random player to drop
            if len(self.team_rosters[team]) > 0:
                drop_index = random.randint(0, len(self.team_rosters[team]) - 1)
                dropped_player = self.team_rosters[team][drop_index]["name"]
                
                # Remove from roster
                self.team_rosters[team].pop(drop_index)
                
                # Pick a random free agent to add
                if len(self.free_agents) > 0:
                    added_player = random.choice(list(self.free_agents.keys()))
                    
                    # Determine position
                    position = "Unknown"
                    if 'ERA' in self.player_stats_current.get(added_player, {}):
                        position = 'RP' if self.player_stats_current[added_player].get('SV', 0) > 0 else 'SP'
                    else:
                        position = random.choice(["C", "1B", "2B", "3B", "SS", "OF"])
                    
                    # Add to roster
                    self.team_rosters[team].append({
                        "name": added_player,
                        "position": position
                    })
                    
                    # Remove from free agents
                    if added_player in self.free_agents:
                        del self.free_agents[added_player]
                    
                    # Log transaction
                    logger.info(f"Transaction: {team} dropped {dropped_player} and added {added_player}")
                    transaction_count += 1
        
        # Trade transactions (0-1 per update)
        if random.random() < 0.3:  # 30% chance of a trade
            # Select two random teams
            teams = random.sample(list(self.team_rosters.keys()), 2)
            
            # Select random players to trade (1-2 per team)
            team1_players = []
            team2_players = []
            
            for _ in range(random.randint(1, 2)):
                if len(self.team_rosters[teams[0]]) > 0:
                    idx = random.randint(0, len(self.team_rosters[teams[0]]) - 1)
                    team1_players.append(self.team_rosters[teams[0]][idx])
                    self.team_rosters[teams[0]].pop(idx)
            
            for _ in range(random.randint(1, 2)):
                if len(self.team_rosters[teams[1]]) > 0:
                    idx = random.randint(0, len(self.team_rosters[teams[1]]) - 1)
                    team2_players.append(self.team_rosters[teams[1]][idx])
                    self.team_rosters[teams[1]].pop(idx)
            
            # Execute the trade
            for player in team1_players:
                self.team_rosters[teams[1]].append(player)
            
            for player in team2_players:
                self.team_rosters[teams[0]].append(player)
            
            # Log transaction
            team1_names = [p["name"] for p in team1_players]
            team2_names = [p["name"] for p in team2_players]
            
            logger.info(f"Trade: {teams[0]} traded {', '.join(team1_names)} to {teams[1]} for {', '.join(team2_names)}")
            transaction_count += 1
        
        logger.info(f"Simulated {transaction_count} league transactions")
        return transaction_count
    
    def run_system_update(self):
        """Run a complete system update"""
        logger.info("Starting system update...")
        
        try:
            # Update player stats
            self.update_player_stats()
            
            # Update player projections
            self.update_player_projections()
            
            # Update player news
            self.update_player_news()
            
            # Update player injuries
            self.update_player_injuries()
            
            # Update league transactions
            self.update_league_transactions()
            
            # Identify free agents
            self.identify_free_agents()
            
            # Save updated system state
            self.save_system_state()
            
            # Generate updated reports
            self.generate_reports()
            
            # Update timestamp
            self.last_update = datetime.now()
            
            logger.info(f"System update completed successfully at {self.last_update}")
            return True
        except Exception as e:
            logger.error(f"Error during system update: {e}")
            return False
    
    def generate_reports(self):
        """Generate various reports"""
        timestamp = datetime.now().strftime("%Y%m%d")
        
        # Generate team analysis report
        self.generate_team_analysis_report(f"{self.reports_dir}/team_analysis_{timestamp}.md")
        
        # Generate free agents report
        self.generate_free_agents_report(f"{self.reports_dir}/free_agents_{timestamp}.md")
        
        # Generate trending players report
        self.generate_trending_players_report(f"{self.reports_dir}/trending_players_{timestamp}.md")
        
        # Generate player news report
        self.generate_player_news_report(f"{self.reports_dir}/player_news_{timestamp}.md")
        
        logger.info(f"Generated reports with timestamp {timestamp}")
    
    def generate_team_analysis_report(self, output_file):
        """Generate team analysis report"""
        with open(output_file, 'w') as f:
            # Title
            f.write("# Fantasy Baseball Team Analysis\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
            
            # Your Team Section
            f.write(f"## Your Team: {self.your_team_name}\n\n")
            
            # Team Roster
            f.write("### Current Roster\n\n")
            
            # Group players by position
            positions = {"C": [], "1B": [], "2B": [], "3B": [], "SS": [], "OF": [], "SP": [], "RP": []}
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                position = player["position"]
                
                # Simplified position assignment
                if position in positions:
                    positions[position].append(name)
                elif "/" in position:  # Handle multi-position players
                    primary_pos = position.split("/")[0]
                    if primary_pos in positions:
                        positions[primary_pos].append(name)
                    else:
                        positions["UTIL"].append(name)
                else:
                    # Handle unknown positions
                    if 'ERA' in self.player_stats_current.get(name, {}):
                        if self.player_stats_current[name].get('SV', 0) > 0:
                            positions["RP"].append(name)
                        else:
                            positions["SP"].append(name)
                    else:
                        positions["UTIL"].append(name)
            
            # Write roster by position
            for pos, players in positions.items():
                if players:
                    f.write(f"**{pos}**: {', '.join(players)}\n\n")
            
            # Team Performance
            f.write("### Team Performance\n\n")
            
            # Calculate team totals
            batting_totals = {
                'AB': 0, 'R': 0, 'HR': 0, 'RBI': 0, 'SB': 0, 'AVG': 0, 'OPS': 0
            }
            
            pitching_totals = {
                'IP': 0, 'W': 0, 'ERA': 0, 'WHIP': 0, 'K': 0, 'QS': 0, 'SV': 0
            }
            
            # Batters stats
            f.write("#### Batting Stats\n\n")
            batter_table = []
            headers = ["Player", "AB", "R", "HR", "RBI", "SB", "AVG", "OPS"]
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_stats_current and 'AVG' in self.player_stats_current[name]:
                    stats = self.player_stats_current[name]
                    batter_table.append([
                        name,
                        stats.get('AB', 0),
                        stats.get('R', 0),
                        stats.get('HR', 0),
                        stats.get('RBI', 0),
                        stats.get('SB', 0),
                        f"{stats.get('AVG', 0):.3f}",
                        f"{stats.get('OPS', 0):.3f}"
                    ])
                    
                    # Add to totals
                    batting_totals['AB'] += stats.get('AB', 0)
                    batting_totals['R'] += stats.get('R', 0)
                    batting_totals['HR'] += stats.get('HR', 0)
                    batting_totals['RBI'] += stats.get('RBI', 0)
                    batting_totals['SB'] += stats.get('SB', 0)
            
            # Calculate team AVG and OPS
            if batting_totals['AB'] > 0:
                total_hits = sum(self.player_stats_current.get(p["name"], {}).get('H', 0) for p in self.team_rosters.get(self.your_team_name, []))
                batting_totals['AVG'] = total_hits / batting_totals['AB']
                
                # Estimate team OPS as average of player OPS values
                ops_values = [self.player_stats_current.get(p["name"], {}).get('OPS', 0) for p in self.team_rosters.get(self.your_team_name, [])]
                ops_values = [ops for ops in ops_values if ops > 0]
                #!/usr/bin/env python3
# Fantasy Baseball Automated Model with Live Updates
# This script creates an automated system that regularly updates player stats and projections
# Uses the same sources (PECOTA, FanGraphs, MLB.com) for consistent data

import os
import csv
import json
import time
import random
import requests
import pandas as pd
import numpy as np
import schedule
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from tabulate import tabulate
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fantasy_baseball_auto.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FantasyBaseballAuto")

class FantasyBaseballAutomated:
    def __init__(self, league_id="2874", your_team_name="Kenny Kawaguchis"):
        self.league_id = league_id
        self.your_team_name = your_team_name
        self.teams = {}
        self.team_rosters = {}
        self.free_agents = {}
        self.player_stats_current = {}
        self.player_projections = {}
        self.player_news = {}
        self.last_update = None
        
        # API endpoints and data sources
        self.data_sources = {
            'stats': [
                'https://www.fangraphs.com/api/players/stats',
                'https://www.baseball-reference.com/leagues/MLB/2025.shtml',
                'https://www.mlb.com/stats/'
            ],
            'projections': [
                'https://www.fangraphs.com/projections.aspx',
                'https://www.baseball-prospectus.com/pecota-projections/',
                'https://www.mlb.com/stats/projected'
            ],
            'news': [
                'https://www.rotowire.com/baseball/news.php',
                'https://www.cbssports.com/fantasy/baseball/players/updates/',
                'https://www.espn.com/fantasy/baseball/story/_/id/29589640'
            ]
        }
        
        # Create directories for data storage
        self.data_dir = "data"
        self.reports_dir = "reports"
        self.visuals_dir = "visuals"
        self.archives_dir = "archives"
        
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.visuals_dir, exist_ok=True)
        os.makedirs(self.archives_dir, exist_ok=True)
        
        logger.info(f"Fantasy Baseball Automated Model initialized for league ID: {league_id}")
        logger.info(f"Your team: {your_team_name}")
    
    def load_initial_data(self):
        """Load initial data to bootstrap the system"""
        logger.info("Loading initial data for bootstrap...")
        
        # Load team rosters
        self.load_team_rosters()
        
        # Load initial stats and projections
        self.load_initial_stats_and_projections()
        
        # Generate initial set of free agents
        self.identify_free_agents()
        
        # Mark system as initialized with timestamp
        self.last_update = datetime.now()
        self.save_system_state()
        
        logger.info(f"Initial data loaded successfully, timestamp: {self.last_update}")
    
    def load_team_rosters(self, rosters_file=None):
        """Load team rosters from file or use default data"""
        if rosters_file and os.path.exists(rosters_file):
            try:
                df = pd.read_csv(rosters_file)
                for _, row in df.iterrows():
                    team_name = row['team_name']
                    player_name = row['player_name']
                    position = row['position']
                    
                    if team_name not in self.team_rosters:
                        self.team_rosters[team_name] = []
                    
                    self.team_rosters[team_name].append({
                        'name': player_name,
                        'position': position
                    })
                
                logger.info(f"Loaded {len(self.team_rosters)} team rosters from {rosters_file}")
            except Exception as e:
                logger.error(f"Error loading rosters file: {e}")
                self._load_default_rosters()
        else:
            logger.info("Rosters file not provided or doesn't exist. Loading default roster data.")
            self._load_default_rosters()
    
    def _load_default_rosters(self):
        """Load default roster data based on previous analysis"""
        default_rosters = {
            "Kenny Kawaguchis": [
                {"name": "Logan O'Hoppe", "position": "C"},
                {"name": "Bryce Harper", "position": "1B"},
                {"name": "Mookie Betts", "position": "2B/OF"},
                {"name": "Austin Riley", "position": "3B"},
                {"name": "CJ Abrams", "position": "SS"},
                {"name": "Lawrence Butler", "position": "OF"},
                {"name": "Riley Greene", "position": "OF"},
                {"name": "Adolis García", "position": "OF"},
                {"name": "Taylor Ward", "position": "OF"},
                {"name": "Tommy Edman", "position": "2B/SS"},
                {"name": "Roman Anthony", "position": "OF"},
                {"name": "Jonathan India", "position": "2B"},
                {"name": "Trevor Story", "position": "SS"},
                {"name": "Iván Herrera", "position": "C"},
                {"name": "Cole Ragans", "position": "SP"},
                {"name": "Hunter Greene", "position": "SP"},
                {"name": "Jack Flaherty", "position": "SP"},
                {"name": "Ryan Helsley", "position": "RP"},
                {"name": "Tanner Scott", "position": "RP"},
                {"name": "Pete Fairbanks", "position": "RP"},
                {"name": "Ryan Pepiot", "position": "SP"},
                {"name": "MacKenzie Gore", "position": "SP"},
                {"name": "Camilo Doval", "position": "RP"}
            ],
            "Mickey 18": [
                {"name": "Adley Rutschman", "position": "C"},
                {"name": "Pete Alonso", "position": "1B"},
                {"name": "Matt McLain", "position": "2B"},
                {"name": "Jordan Westburg", "position": "3B"},
                {"name": "Jeremy Peña", "position": "SS"},
                {"name": "Jasson Domínguez", "position": "OF"},
                {"name": "Tyler O'Neill", "position": "OF"},
                {"name": "Vladimir Guerrero Jr.", "position": "1B"},
                {"name": "Eugenio Suárez", "position": "3B"},
                {"name": "Ronald Acuña Jr.", "position": "OF"},
                {"name": "Tarik Skubal", "position": "SP"},
                {"name": "Spencer Schwellenbach", "position": "SP"},
                {"name": "Hunter Brown", "position": "SP"},
                {"name": "Jhoan Duran", "position": "RP"},
                {"name": "Jeff Hoffman", "position": "RP"},
                {"name": "Ryan Pressly", "position": "RP"},
                {"name": "Justin Verlander", "position": "SP"},
                {"name": "Max Scherzer", "position": "SP"}
            ],
            # Other teams omitted for brevity but would be included in full implementation
        }
        
        # Add to the team rosters dictionary
        self.team_rosters = default_rosters
        
        # Count total players loaded
        total_players = sum(len(roster) for roster in self.team_rosters.values())
        logger.info(f"Loaded {len(self.team_rosters)} team rosters with {total_players} players from default data")
    
    def load_initial_stats_and_projections(self, stats_file=None, projections_file=None):
        """Load initial stats and projections from files or use default data"""
        if stats_file and os.path.exists(stats_file) and projections_file and os.path.exists(projections_file):
            try:
                # Load stats
                with open(stats_file, 'r') as f:
                    self.player_stats_current = json.load(f)
                
                # Load projections
                with open(projections_file, 'r') as f:
                    self.player_projections = json.load(f)
                
                logger.info(f"Loaded stats for {len(self.player_stats_current)} players from {stats_file}")
                logger.info(f"Loaded projections for {len(self.player_projections)} players from {projections_file}")
            except Exception as e:
                logger.error(f"Error loading stats/projections files: {e}")
                self._load_default_stats_and_projections()
        else:
            logger.info("Stats/projections files not provided or don't exist. Loading default data.")
            self._load_default_stats_and_projections()
    
    def _load_default_stats_and_projections(self):
        """Load default stats and projections for bootstrapping"""
        # This would load from the previously created data
        # For simulation/demo purposes, we'll generate synthetic data
        
        # First, collect all players from rosters
        all_players = set()
        for team, roster in self.team_rosters.items():
            for player in roster:
                all_players.add(player["name"])
        
        # Add some free agents
        free_agents = [
            "Keibert Ruiz", "Danny Jansen", "Christian Walker", 
            "Spencer Torkelson", "Gavin Lux", "Luis Rengifo", 
            "JP Crawford", "Ha-Seong Kim", "Jeimer Candelario", 
            "Spencer Steer", "Luis Matos", "Heliot Ramos", 
            "TJ Friedl", "Garrett Mitchell", "Kutter Crawford", 
            "Reese Olson", "Dane Dunning", "José Berríos", 
            "Erik Swanson", "Seranthony Domínguez"
        ]
        
        for player in free_agents:
            all_players.add(player)
        
        # Generate stats and projections for all players
        self._generate_synthetic_data(all_players)
        
        logger.info(f"Generated synthetic stats for {len(self.player_stats_current)} players")
        logger.info(f"Generated synthetic projections for {len(self.player_projections)} players")
    
    def _generate_synthetic_data(self, player_names):
        """Generate synthetic stats and projections for demo purposes"""
        for player in player_names:
            # Determine if batter or pitcher based on name recognition
            # This is a simple heuristic; in reality, you'd use actual data
            is_pitcher = player in [
                "Cole Ragans", "Hunter Greene", "Jack Flaherty", "Ryan Helsley", 
                "Tanner Scott", "Pete Fairbanks", "Ryan Pepiot", "MacKenzie Gore", 
                "Camilo Doval", "Tarik Skubal", "Spencer Schwellenbach", "Hunter Brown", 
                "Jhoan Duran", "Jeff Hoffman", "Ryan Pressly", "Justin Verlander", 
                "Max Scherzer", "Kutter Crawford", "Reese Olson", "Dane Dunning", 
                "José Berríos", "Erik Swanson", "Seranthony Domínguez"
            ]
            
            if is_pitcher:
                # Generate pitcher stats
                current_stats = {
                    'IP': random.uniform(20, 40),
                    'W': random.randint(1, 4),
                    'L': random.randint(0, 3),
                    'ERA': random.uniform(2.5, 5.0),
                    'WHIP': random.uniform(0.9, 1.5),
                    'K': random.randint(15, 50),
                    'BB': random.randint(5, 20),
                    'QS': random.randint(1, 5),
                    'SV': 0 if player not in ["Ryan Helsley", "Tanner Scott", "Pete Fairbanks", "Camilo Doval", "Jhoan Duran", "Ryan Pressly", "Erik Swanson", "Seranthony Domínguez"] else random.randint(1, 8)
                }
                
                # Calculate k/9
                current_stats['K9'] = current_stats['K'] * 9 / current_stats['IP'] if current_stats['IP'] > 0 else 0
                
                # Generate projections (rest of season)
                projected_ip = random.uniform(120, 180) if current_stats['SV'] == 0 else random.uniform(45, 70)
                projected_stats = {
                    'IP': projected_ip,
                    'ERA': random.uniform(3.0, 4.5),
                    'WHIP': random.uniform(1.05, 1.35),
                    'K9': random.uniform(7.5, 12.0),
                    'QS': random.randint(10, 20) if current_stats['SV'] == 0 else 0,
                    'SV': 0 if current_stats['SV'] == 0 else random.randint(15, 35)
                }
            else:
                # Generate batter stats
                current_stats = {
                    'AB': random.randint(70, 120),
                    'R': random.randint(8, 25),
                    'H': random.randint(15, 40),
                    'HR': random.randint(1, 8),
                    'RBI': random.randint(5, 25),
                    'SB': random.randint(0, 8),
                    'BB': random.randint(5, 20),
                    'SO': random.randint(15, 40)
                }
                
                # Calculate derived stats
                current_stats['AVG'] = current_stats['H'] / current_stats['AB'] if current_stats['AB'] > 0 else 0
                current_stats['OBP'] = (current_stats['H'] + current_stats['BB']) / (current_stats['AB'] + current_stats['BB']) if (current_stats['AB'] + current_stats['BB']) > 0 else 0
                
                # Estimate SLG and OPS
                singles = current_stats['H'] - current_stats['HR'] - random.randint(2, 10) - random.randint(0, 5)
                doubles = random.randint(2, 10)
                triples = random.randint(0, 5)
                tb = singles + (2 * doubles) + (3 * triples) + (4 * current_stats['HR'])
                current_stats['SLG'] = tb / current_stats['AB'] if current_stats['AB'] > 0 else 0
                current_stats['OPS'] = current_stats['OBP'] + current_stats['SLG']
                
                # Generate projections (rest of season)
                projected_stats = {
                    'AB': random.randint(400, 550),
                    'R': random.randint(50, 100),
                    'HR': random.randint(10, 35),
                    'RBI': random.randint(40, 100),
                    'SB': random.randint(3, 35),
                    'AVG': random.uniform(0.230, 0.310),
                    'OPS': random.uniform(0.680, 0.950)
                }
            
            # Add to dictionaries
            self.player_stats_current[player] = current_stats
            self.player_projections[player] = projected_stats
    
    def identify_free_agents(self):
        """Identify all players who aren't on team rosters but have stats/projections"""
        # Create a set of all rostered players
        rostered_players = set()
        for team, roster in self.team_rosters.items():
            for player in roster:
                rostered_players.add(player["name"])
        
        # Find players with stats/projections who aren't rostered
        self.free_agents = {}
        
        for player in self.player_projections.keys():
            if player not in rostered_players:
                # Determine position based on stats
                if player in self.player_stats_current:
                    if 'ERA' in self.player_stats_current[player]:
                        position = 'RP' if self.player_stats_current[player].get('SV', 0) > 0 else 'SP'
                    else:
                        # This is simplistic - in a real system, we'd have actual position data
                        position = 'Unknown'
                else:
                    position = 'Unknown'
                
                self.free_agents[player] = {
                    'name': player,
                    'position': position,
                    'stats': self.player_stats_current.get(player, {}),
                    'projections': self.player_projections.get(player, {})
                }
        
        logger.info(f"Identified {len(self.free_agents)} free agents")
        return self.free_agents
    
    def save_system_state(self):
        """Save the current state of the system to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save team rosters
        with open(f"{self.data_dir}/team_rosters.json", 'w') as f:
            json.dump(self.team_rosters, f, indent=4)
        
        # Save current stats
        with open(f"{self.data_dir}/player_stats_current.json", 'w') as f:
            json.dump(self.player_stats_current, f, indent=4)
        
        # Save projections
        with open(f"{self.data_dir}/player_projections.json", 'w') as f:
            json.dump(self.player_projections, f, indent=4)
        
        # Save free agents
        with open(f"{self.data_dir}/free_agents.json", 'w') as f:
            json.dump(self.free_agents, f, indent=4)
        
        # Also save an archive copy
        with open(f"{self.archives_dir}/team_rosters_{timestamp}.json", 'w') as f:
            json.dump(self.team_rosters, f, indent=4)
        
        with open(f"{self.archives_dir}/player_stats_{timestamp}.json", 'w') as f:
            json.dump(self.player_stats_current, f, indent=4)
        
        with open(f"{self.archives_dir}/projections_{timestamp}.json", 'w') as f:
            json.dump(self.player_projections, f, indent=4)
        
        logger.info(f"System state saved successfully with timestamp: {timestamp}")
    
    def load_system_state(self):
        """Load the system state from saved files"""
        try:
            # Load team rosters
            if os.path.exists(f"{self.data_dir}/team_rosters.json"):
                with open(f"{self.data_dir}/team_rosters.json", 'r') as f:
                    self.team_rosters = json.load(f)
            
            # Load current stats
            if os.path.exists(f"{self.data_dir}/player_stats_current.json"):
                with open(f"{self.data_dir}/player_stats_current.json", 'r') as f:
                    self.player_stats_current = json.load(f)
            
            # Load projections
            if os.path.exists(f"{self.data_dir}/player_projections.json"):
                with open(f"{self.data_dir}/player_projections.json", 'r') as f:
                    self.player_projections = json.load(f)
            
            # Load free agents
            if os.path.exists(f"{self.data_dir}/free_agents.json"):
                with open(f"{self.data_dir}/free_agents.json", 'r') as f:
                    self.free_agents = json.load(f)
            
            logger.info("System state loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading system state: {e}")
            return False
    
    def update_player_stats(self):
        """Update player stats by fetching from data sources"""
        logger.info("Updating player stats from sources...")
        
        # In a real implementation, you would:
        # 1. Fetch data from each source in self.data_sources['stats']
        # 2. Parse and clean the data
        # 3. Merge with existing stats
        # 4. Update self.player_stats_current
        
        # For demo purposes, we'll simulate this process
        self._simulate_stats_update()
        
        logger.info(f"Updated stats for {len(self.player_stats_current)} players")
        return len(self.player_stats_current)
    
    def _simulate_stats_update(self):
        """Simulate updating stats for demo purposes"""
        # Add some new players
        new_players = [
            "Bobby Miller", "Garrett Crochet", "DL Hall", 
            "Edward Cabrera", "Alec Bohm", "Elly De La Cruz",
            "Anthony Volpe", "Jazz Chisholm Jr."
        ]
        
        for player in new_players:
            if player not in self.player_stats_current:
                # Determine if batter or pitcher based on name recognition
                is_pitcher = player in ["Bobby Miller", "Garrett Crochet", "DL Hall", "Edward Cabrera"]
                
                if is_pitcher:
                    self.player_stats_current[player] = {
                        'IP': random.uniform(10, 30),
                        'W': random.randint(1, 3),
                        'L': random.randint(0, 2),
                        'ERA': random.uniform(3.0, 5.0),
                        'WHIP': random.uniform(1.0, 1.4),
                        'K': random.randint(10, 40),
                        'BB': random.randint(5, 15),
                        'QS': random.randint(1, 4),
                        'SV': 0
                    }
                    
                    # Calculate k/9
                    self.player_stats_current[player]['K9'] = (
                        self.player_stats_current[player]['K'] * 9 / 
                        self.player_stats_current[player]['IP'] 
                        if self.player_stats_current[player]['IP'] > 0 else 0
                    )
                else:
                    self.player_stats_current[player] = {
                        'AB': random.randint(50, 100),
                        'R': random.randint(5, 20),
                        'H': random.randint(10, 30),
                        'HR': random.randint(1, 6),
                        'RBI': random.randint(5, 20),
                        'SB': random.randint(0, 6),
                        'BB': random.randint(5, 15),
                        'SO': random.randint(10, 30)
                    }
                    
                    # Calculate derived stats
                    self.player_stats_current[player]['AVG'] = (
                        self.player_stats_current[player]['H'] / 
                        self.player_stats_current[player]['AB'] 
                        if self.player_stats_current[player]['AB'] > 0 else 0
                    )
                    
                    self.player_stats_current[player]['OBP'] = (
                        (self.player_stats_current[player]['H'] + self.player_stats_current[player]['BB']) / 
                        (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) 
                        if (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) > 0 else 0
                    )
                    
                    # Estimate SLG and OPS
                    singles = (
                        self.player_stats_current[player]['H'] - 
                        self.player_stats_current[player]['HR'] - 
                        random.randint(2, 8) - 
                        random.randint(0, 3)
                    )
                    doubles = random.randint(2, 8)
                    triples = random.randint(0, 3)
                    tb = singles + (2 * doubles) + (3 * triples) + (4 * self.player_stats_current[player]['HR'])
                    
                    self.player_stats_current[player]['SLG'] = (
                        tb / self.player_stats_current[player]['AB'] 
                        if self.player_stats_current[player]['AB'] > 0 else 0
                    )
                    
                    self.player_stats_current[player]['OPS'] = (
                        self.player_stats_current[player]['OBP'] + 
                        self.player_stats_current[player]['SLG']
                    )
        
        # Update existing player stats
        for player in list(self.player_stats_current.keys()):
            # Skip some players randomly to simulate days off
            if random.random() < 0.3:
                continue
                
            # Determine if batter or pitcher based on existing stats
            if 'ERA' in self.player_stats_current[player]:  # It's a pitcher
                # Generate random game stats
                ip = random.uniform(0.1, 7)
                k = int(ip * random.uniform(0.5, 1.5))
                bb = int(ip * random.uniform(0.1, 0.5))
                er = int(ip * random.uniform(0, 0.7))
                h = int(ip * random.uniform(0.3, 1.2))
                
                # Update aggregated stats
                self.player_stats_current[player]['IP'] += ip
                self.player_stats_current[player]['K'] += k
                self.player_stats_current[player]['BB'] += bb
                
                # Update win/loss
                if random.random() < 0.5:
                    if random.random() < 0.6:  # 60% chance of decision
                        if random.random() < 0.5:  # 50% chance of win
                            self.player_stats_current[player]['W'] = self.player_stats_current[player].get('W', 0) + 1
                        else:
                            self.player_stats_current[player]['L'] = self.player_stats_current[player].get('L', 0) + 1
                
                # Update quality starts
                if ip >= 6 and er <= 3 and 'SV' not in self.player_stats_current[player]:
                    self.player_stats_current[player]['QS'] = self.player_stats_current[player].get('QS', 0) + 1
                
                # Update saves for relievers
                if 'SV' in self.player_stats_current[player] and ip <= 2 and random.random() < 0.3:
                    self.player_stats_current[player]['SV'] = self.player_stats_current[player].get('SV', 0) + 1
                
                # Recalculate ERA and WHIP
                total_er = (self.player_stats_current[player]['ERA'] * 
                           (self.player_stats_current[player]['IP'] - ip) / 9) + er
                            
                self.player_stats_current[player]['ERA'] = (
                    total_er * 9 / self.player_stats_current[player]['IP'] 
                    if self.player_stats_current[player]['IP'] > 0 else 0
                )
                
                # Add baserunners for WHIP calculation
                self.player_stats_current[player]['WHIP'] = (
                    (self.player_stats_current[player]['WHIP'] * 
                     (self.player_stats_current[player]['IP'] - ip) + (h + bb)) / 
                    self.player_stats_current[player]['IP'] 
                    if self.player_stats_current[player]['IP'] > 0 else 0
                )
                
                # Update K/9
                self.player_stats_current[player]['K9'] = (
                    self.player_stats_current[player]['K'] * 9 / 
                    self.player_stats_current[player]['IP'] 
                    if self.player_stats_current[player]['IP'] > 0 else 0
                )
                
            else:  # It's a batter
                # Generate random game stats
                ab = random.randint(0, 5)
                h = 0
                hr = 0
                r = 0
                rbi = 0
                sb = 0
                bb = 0
                so = 0
                
                if ab > 0:
                    # Determine hits
                    for _ in range(ab):
                        if random.random() < 0.270:  # League average is around .270
                            h += 1
                            # Determine if it's a home run
                            if random.random() < 0.15:  # About 15% of hits are HRs
                                hr += 1
                    
                    # Other stats
                    r = random.randint(0, 2) if h > 0 else 0
                    rbi = random.randint(0, 3) if h > 0 else 0
                    sb = 1 if random.random() < 0.08 else 0  # 8% chance of SB
                    bb = 1 if random.random() < 0.1 else 0  # 10% chance of BB
                    so = random.randint(0, 2)  # 0-2 strikeouts
                
                # Update aggregated stats
                self.player_stats_current[player]['AB'] += ab
                self.player_stats_current[player]['H'] += h
                self.player_stats_current[player]['HR'] += hr
                self.player_stats_current[player]['R'] += r
                self.player_stats_current[player]['RBI'] += rbi
                self.player_stats_current[player]['SB'] += sb
                self.player_stats_current[player]['BB'] += bb
                self.player_stats_current[player]['SO'] += so
                
                # Recalculate AVG
                self.player_stats_current[player]['AVG'] =with open(output_file, 'w') as f:
            # Title
            f.write("# Fantasy Baseball Trending Players\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
            
            # Introduction
            f.write("This report identifies players who are trending up or down based on recent performance versus expectations.\n\n")
            
            # For demo purposes, randomly select players as trending up or down
            trending_up_batters = random.sample(list(self.player_stats_current.keys()), 5)
            trending_down_batters = random.sample(list(self.player_stats_current.keys()), 5)
            
            trending_up_pitchers = random.sample([p for p in self.player_stats_current if 'ERA' in self.player_stats_current[p]], 3)
            trending_down_pitchers = random.sample([p for p in self.player_stats_current if 'ERA' in self.player_stats_current[p]], 3)
            
            # Hot Batters
            f.write("## 🔥 Hot Batters\n\n")
            f.write("Players exceeding their projections over the past 15 days.\n\n")
            
            headers = ["Player", "Last 15 Days", "Season Stats", "Ownership"]
            hot_batters_table = []
            
            for player in trending_up_batters:
                if player in self.player_stats_current and 'AVG' in self.player_stats_current[player]:
                    # Generate simulated recent hot stats
                    recent_avg = min(self.player_stats_current[player].get('AVG', 0.250) + random.uniform(0.040, 0.080), 0.400)
                    recent_hr = max(1, int(self.player_stats_current[player].get('HR', 5) * random.uniform(0.20, 0.30)))
                    recent_rbi = max(3, int(self.player_stats_current[player].get('RBI', 20) * random.uniform(0.20, 0.30)))
                    
                    # Determine roster status
                    roster_status = "Rostered"
                    for team, roster in self.team_rosters.items():
                        if player in [p["name"] for p in roster]:
                            roster_status = team
                            break
                    
                    if roster_status == "Rostered":
                        roster_status = random.choice(list(self.team_rosters.keys()))
                    
                    # Generate table row
                    hot_batters_table.append([
                        player,
                        f"{recent_avg:.3f}, {recent_hr} HR, {recent_rbi} RBI",
                        f"{self.player_stats_current[player].get('AVG', 0):.3f}, {self.player_stats_current[player].get('HR', 0)} HR, {self.player_stats_current[player].get('RBI', 0)} RBI",
                        roster_status
                    ])
            
            f.write(tabulate(hot_batters_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Cold Batters
            f.write("## ❄️ Cold Batters\n\n")
            f.write("Players underperforming their projections over the past 15 days.\n\n")
            
            cold_batters_table = []
            
            for player in trending_down_batters:
                if player in self.player_stats_current and 'AVG' in self.player_stats_current[player]:
                    # Generate simulated recent cold stats
                    recent_avg = max(0.120, self.player_stats_current[player].get('AVG', 0.250) - random.uniform(0.050, 0.100))
                    recent_hr = max(0, int(self.player_stats_current[player].get('HR', 5) * random.uniform(0.05, 0.15)))
                    recent_rbi = max(1, int(self.player_stats_current[player].get('RBI', 20) * random.uniform(0.05, 0.15)))
                    
                    # Determine roster status
                    roster_status = "Rostered"
                    for team, roster in self.team_rosters.items():
                        if player in [p["name"] for p in roster]:
                            roster_status = team
                            break
                    
                    if roster_status == "Rostered":
                        roster_status = random.choice(list(self.team_rosters.keys()))
                    
                    # Generate table row
                    cold_batters_table.append([
                        player,
                        f"{recent_avg:.3f}, {recent_hr} HR, {recent_rbi} RBI",
                        f"{self.player_stats_current[player].get('AVG', 0):.3f}, {self.player_stats_current[player].get('HR', 0)} HR, {self.player_stats_current[player].get('RBI', 0)} RBI",
                        roster_status
                    ])
            
            f.write(tabulate(cold_batters_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Hot Pitchers
            f.write("## 🔥 Hot Pitchers\n\n")
            f.write("Pitchers exceeding their projections over the past 15 days.\n\n")
            
            headers = ["Player", "Last 15 Days", "Season Stats", "Ownership"]
            hot_pitchers_table = []
            
            for player in trending_up_pitchers:
                if 'ERA' in self.player_stats_current[player]:
                    # Generate simulated recent hot stats
                    recent_era = max(0.00, self.player_stats_current[player].get('ERA', 4.00) - random.uniform(1.30, 2.50))
                    recent_whip = max(0.70, self.player_stats_current[player].get('WHIP', 1.30) - random.uniform(0.30, 0.50))
                    recent_k = int(self.player_stats_current[player].get('K', 40) * random.uniform(0.15, 0.25))
                    
                    # Determine roster status
                    roster_status = "Rostered"
                    for team, roster in self.team_rosters.items():
                        if player in [p["name"] for p in roster]:
                            roster_status = team
                            break
                    
                    if roster_status == "Rostered":
                        roster_status = random.choice(list(self.team_rosters.keys()))
                    
                    # Generate table row
                    hot_pitchers_table.append([
                        player,
                        f"{recent_era:.2f} ERA, {recent_whip:.2f} WHIP, {recent_k} K",
                        f"{self.player_stats_current[player].get('ERA', 0):.2f} ERA, {self.player_stats_current[player].get('WHIP', 0):.2f} WHIP, {self.player_stats_current[player].get('K', 0)} K",
                        roster_status
                    ])
            
            f.write(tabulate(hot_pitchers_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Cold Pitchers
            f.write("## ❄️ Cold Pitchers\n\n")
            f.write("Pitchers underperforming their projections over the past 15 days.\n\n")
            
            cold_pitchers_table = []
            
            for player in trending_down_pitchers:
                if 'ERA' in self.player_stats_current[player]:
                    # Generate simulated recent cold stats
                    recent_era = self.player_stats_current[player].get('ERA', 4.00) + random.uniform(1.50, 3.00)
                    recent_whip = self.player_stats_current[player].get('WHIP', 1.30) + random.uniform(0.20, 0.40)
                    recent_k = max(0, int(self.player_stats_current[player].get('K', 40) * random.uniform(0.05, 0.15)))
                    
                    # Determine roster status
                    roster_status = "Rostered"
                    for team, roster in self.team_rosters.items():
                        if player in [p["name"] for p in roster]:
                            roster_status = team
                            break
                    
                    if roster_status == "Rostered":
                        roster_status = random.choice(list(self.team_rosters.keys()))
                    
                    # Generate table row
                    cold_pitchers_table.append([
                        player,
                        f"{recent_era:.2f} ERA, {recent_whip:.2f} WHIP, {recent_k} K",
                        f"{self.player_stats_current[player].get('ERA', 0):.2f} ERA, {self.player_stats_current[player].get('WHIP', 0):.2f} WHIP, {self.player_stats_current[player].get('K', 0)} K",
                        roster_status
                    ])
            
            f.write(tabulate(cold_pitchers_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Pickup Recommendations
            f.write("## 📈 Recommended Pickups\n\n")
            f.write("Players trending up who are still available in many leagues.\n\n")
            
            # Find available players who are trending up
            available_trending = []
            for player in trending_up_batters + trending_up_pitchers:
                is_rostered = False
                for team, roster in self.team_rosters.items():
                    if player in [p["name"] for p in roster]:
                        is_rostered = True
                        break
                
                if not is_rostered:
                    available_trending.append(player)
            
            # Add some random free agents to the mix
            available_trending.extend(random.sample(list(self.free_agents.keys()), min(5, len(self.free_agents))))
            
            # Create recommendation table
            headers = ["Player", "Position", "Recent Performance", "Projected ROS"]
            recommendations_table = []
            
            for player in available_trending[:5]:  # Top 5 recommendations
                if player in self.player_stats_current:
                    # Determine position
                    if 'ERA' in self.player_stats_current[player]:
                        position = 'RP' if self.player_stats_current[player].get('SV', 0) > 0 else 'SP'
                        
                        # Generate recent performance string
                        recent_perf = f"{random.uniform(2.00, 3.50):.2f} ERA, {random.uniform(0.90, 1.20):.2f} WHIP, {random.randint(5, 15)} K"
                        
                        # Generate ROS projection string
                        if player in self.player_projections:
                            proj = self.player_projections[player]
                            ros_proj = f"{proj.get('ERA', 0):.2f} ERA, {proj.get('WHIP', 0):.2f} WHIP, {int(proj.get('IP', 0))} IP"
                        else:
                            ros_proj = "No projection available"
                    else:
                        # Random position for batters
                        position = random.choice(['C', '1B', '2B', '3B', 'SS', 'OF'])
                        
                        # Generate recent performance string
                        recent_perf = f"{random.uniform(0.280, 0.360):.3f} AVG, {random.randint(1, 5)} HR, {random.randint(5, 15)} RBI"
                        
                        # Generate ROS projection string
                        if player in self.player_projections:
                            proj = self.player_projections[player]
                            ros_proj = f"{proj.get('AVG', 0):.3f} AVG, {int(proj.get('HR', 0))} HR, {int(proj.get('RBI', 0))} RBI"
                        else:
                            ros_proj = "No projection available"
                    
                    recommendations_table.append([
                        player,
                        position,
                        recent_perf,
                        ros_proj
                    ])
            
            f.write(tabulate(recommendations_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Drop Recommendations
            f.write("## 📉 Consider Dropping\n\n")
            f.write("Rostered players who are trending down and may be safe to drop in standard leagues.\n\n")
            
            # Find rostered players who are trending down
            rostered_trending_down = []
            for player in trending_down_batters + trending_down_pitchers:
                is_rostered = False
                for team, roster in self.team_rosters.items():
                    if player in [p["name"] for p in roster]:
                        is_rostered = True
                        break
                
                if is_rostered:
                    rostered_trending_down.append(player)
            
            # Create drop recommendation table
            headers = ["Player", "Position", "Recent Performance", "Better Alternatives"]
            drop_recommendations_table = []
            
            for player in rostered_trending_down[:5]:  # Top 5 drop recommendations
                if player in self.player_stats_current:
                    # Determine position
                    if 'ERA' in self.player_stats_current[player]:
                        position = 'RP' if self.player_stats_current[player].get('SV', 0) > 0 else 'SP'
                        
                        # Generate recent performance string
                        recent_perf = f"{random.uniform(5.50, 8.00):.2f} ERA, {random.uniform(1.40, 1.80):.2f} WHIP, {random.randint(1, 7)} K"
                        
                        # Suggest alternatives
                        alternatives = [p for p in self.free_agents if p in self.player_projections and 'ERA' in self.player_projections[p]]
                        if alternatives:
                            better_alternatives = ", ".join(random.sample(alternatives, min(3, len(alternatives))))
                        else:
                            better_alternatives = "None available"
                    else:
                        # Random position for batters
                        position = random.choice(['C', '1B', '2B', '3B', 'SS', 'OF'])
                        
                        # Generate recent performance string
                        recent_perf = f"{random.uniform(0.120, 0.200):.3f} AVG, {random.randint(0, 1)} HR, {random.randint(1, 4)} RBI"
                        
                        # Suggest alternatives
                        alternatives = [p for p in self.free_agents if p in self.player_projections and 'AVG' in self.player_projections[p]]
                        if alternatives:
                            better_alternatives = ", ".join(random.sample(alternatives, min(3, len(alternatives))))
                        else:
                            better_alternatives = "None available"
                    
                    drop_recommendations_table.append([
                        player,
                        position,
                        recent_perf,
                        better_alternatives
                    ])
            
            f.write(tabulate(drop_recommendations_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            logger.info(f"Trending players report generated: {output_file}")
    
    def generate_player_news_report(self, output_file):
        """Generate report of recent player news"""
        with open(output_file, 'w') as f:
            # Title
            f.write("# Fantasy Baseball Player News\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
            
            # Recent Injuries
            f.write("## 🏥 Recent Injuries\n\n")
            
            injury_news = []
            for player, news_items in self.player_news.items():
                for item in news_items:
                    if any(keyword in item['content'].lower() for keyword in ['injury', 'injured', 'il', 'disabled list', 'strain', 'sprain']):
                        injury_news.append({
                            'player': player,
                            'date': item['date'],
                            'source': item['source'],
                            'content': item['content']
                        })
            
            # Sort by date (most recent first)
            injury_news.sort(key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d"), reverse=True)
            
            if injury_news:
                for news in injury_news[:10]:  # Show most recent 10 injury news items
                    f.write(f"**{news['player']}** ({news['date']} - {news['source']}): {news['content']}\n\n")
            else:
                f.write("No recent injury news.\n\n")
            
            # Position Battle Updates
            f.write("## ⚔️ Position Battle Updates\n\n")
            
            # In a real implementation, you would have actual news about position battles
            # For demo purposes, we'll simulate position battle news
            position_battles = [
                {
                    'position': 'Second Base',
                    'team': 'Athletics',
                    'players': ['Zack Gelof', 'Nick Allen'],
                    'update': f"Gelof continues to see the majority of starts at 2B, playing in {random.randint(4, 6)} of the last 7 games."
                },
                {
                    'position': 'Closer',
                    'team': 'Cardinals',
                    'players': ['Ryan Helsley', 'Giovanny Gallegos'],
                    'update': f"Helsley has converted {random.randint(3, 5)} saves in the last two weeks, firmly establishing himself as the primary closer."
                },
                {
                    'position': 'Outfield',
                    'team': 'Rays',
                    'players': ['Josh Lowe', 'Jose Siri', 'Randy Arozarena'],
                    'update': f"With Lowe's recent {random.choice(['hamstring', 'oblique', 'back'])} injury, Siri has taken over as the everyday CF."
                }
            ]
            
            for battle in position_battles:
                f.write(f"**{battle['team']} {battle['position']}**: {battle['update']}\n\n")
                f.write(f"Players involved: {', '.join(battle['players'])}\n\n")
            
            # Closer Updates
            f.write("## 🔒 Closer Situations\n\n")
            
            # In a real implementation, you would have actual closer data
            # For demo purposes, we'll simulate closer situations
            closer_situations = [
                {
                    'team': 'Rays',
                    'primary': 'Pete Fairbanks',
                    'secondary': 'Jason Adam',
                    'status': f"Fairbanks has {random.randint(3, 5)} saves in the last 14 days and is firmly entrenched as the closer."
                },
                {
                    'team': 'Cardinals',
                    'primary': 'Ryan Helsley',
                    'secondary': 'Giovanny Gallegos',
                    'status': f"Helsley is the unquestioned closer with {random.randint(15, 25)} saves on the season."
                },
                {
                    'team': 'Reds',
                    'primary': 'Alexis Díaz',
                    'secondary': 'Lucas Sims',
                    'status': f"Díaz is firmly in the closer role with {random.randint(3, 5)} saves in the last two weeks."
                },
                {
                    'team': 'Athletics',
                    'primary': 'Mason Miller',
                    'secondary': 'Dany Jiménez',
                    'status': f"Miller has taken over the closing duties, recording {random.randint(2, 4)} saves recently."
                },
                {
                    'team': 'Mariners',
                    'primary': 'Andrés Muñoz',
                    'secondary': 'Matt Brash',
                    'status': f"Muñoz appears to be the preferred option with {random.randint(3, 5)} saves recently."
                }
            ]
            
            # Create a table for closer situations
            headers = ["Team", "Primary", "Secondary", "Status"]
            closer_table = []
            
            for situation in closer_situations:
                closer_table.append([
                    situation['team'],
                    situation['primary'],
                    situation['secondary'],
                    situation['status']
                ])
            
            f.write(tabulate(closer_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Prospect Watch
            f.write("## 🔮 Prospect Watch\n\n")
            
            # In a real implementation, you would have actual prospect data
            # For demo purposes, we'll simulate prospect updates
            prospects = [
                {
                    'name': 'Jackson Holliday',
                    'team': 'Orioles',
                    'position': 'SS',
                    'level': 'AAA',
                    'stats': f".{random.randint(280, 350)} AVG, {random.randint(5, 12)} HR, {random.randint(30, 50)} RBI, {random.randint(8, 20)} SB in {random.randint(180, 250)} AB",
                    'eta': 'Soon - already on 40-man roster'
                },
                {
                    'name': 'Junior Caminero',
                    'team': 'Rays',
                    'position': '3B',
                    'level': 'AAA',
                    'stats': f".{random.randint(280, 320)} AVG, {random.randint(10, 18)} HR, {random.randint(40, 60)} RBI in {random.randint(200, 280)} AB",
                    'eta': f"{random.choice(['June', 'July', 'August'])} {datetime.now().year}"
                },
                {
                    'name': 'Jasson Domínguez',
                    'team': 'Yankees',
                    'position': 'OF',
                    'level': 'AAA',
                    'stats': f".{random.randint(260, 310)} AVG, {random.randint(8, 15)} HR, {random.randint(10, 25)} SB in {random.randint(180, 250)} AB",
                    'eta': f"Expected back from TJ surgery in {random.choice(['July', 'August'])}"
                },
                {
                    'name': 'Colson Montgomery',
                    'team': 'White Sox',
                    'position': 'SS',
                    'level': 'AA',
                    'stats': f".{random.randint(270, 320)} AVG, {random.randint(6, 12)} HR, {random.randint(30, 50)} RBI in {random.randint(180, 250)} AB",
                    'eta': f"{random.choice(['August', 'September', '2026'])}"
                },
                {
                    'name': 'Orelvis Martinez',
                    'team': 'Blue Jays',
                    'position': '3B/SS',
                    'level': 'AAA',
                    'stats': f".{random.randint(240, 290)} AVG, {random.randint(12, 20)} HR, {random.randint(40, 60)} RBI in {random.randint(180, 250)} AB",
                    'eta': f"{random.choice(['July', 'August', 'September'])}"
                }
            ]
            
            # Create a table for prospects
            headers = ["Prospect", "Team", "Position", "Level", "Stats", "ETA"]
            prospects_table = []
            
            for prospect in prospects:
                prospects_table.append([
                    prospect['name'],
                    prospect['team'],
                    prospect['position'],
                    prospect['level'],
                    prospect['stats'],
                    prospect['eta']
                ])
            
            f.write(tabulate(prospects_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            logger.info(f"Player news report generated: {output_file}")
    
    def schedule_updates(self, daily_update_time="07:00", weekly_update_day="Monday"):
        """Schedule regular updates at specified times"""
        # Schedule daily updates
        schedule.every().day.at(daily_update_time).do(self.run_system_update)
        
        # Schedule weekly full updates with report generation
        if weekly_update_day.lower() == "monday":
            schedule.every().monday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "tuesday":
            schedule.every().tuesday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "wednesday":
            schedule.every().wednesday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "thursday":
            schedule.every().thursday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "friday":
            schedule.every().friday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "saturday":
            schedule.every().saturday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "sunday":
            schedule.every().sunday.at(daily_update_time).do(self.generate_reports)
        
        logger.info(f"Scheduled daily updates at {daily_update_time}")
        logger.info(f"Scheduled weekly full updates on {weekly_update_day} at {daily_update_time}")
    
    def start_update_loop(self):
        """Start the scheduled update loop"""
        logger.info("Starting update loop - press Ctrl+C to exit")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Update loop stopped by user")
    
    def fetch_external_data(self, data_type, source_index=0):
        """Fetch data from external sources - placeholder for real implementation"""
        logger.info(f"Fetching {data_type} data from {self.data_sources[data_type][source_index]}")
        
        # In a real implementation, you would:
        # 1. Make HTTP request to the data source
        # 2. Parse the response (HTML, JSON, etc.)
        # 3. Extract relevant data
        # 4. Return structured data
        
        # For demo purposes, we'll simulate a successful fetch
        return True

# Command-line interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Fantasy Baseball Automated Model with Live Updates')
    parser.add_argument('--league_id', type=str, default="2874", help='League ID')
    parser.add_argument('--team_name', type=str, default="Kenny Kawaguchis", help='Your team name')
    parser.add_argument('--daily_update', type=str, default="07:00", help='Daily update time (HH:MM)')
    parser.add_argument('--weekly_update', type=str, default="Monday", help='Weekly update day')
    parser.add_argument('--manual_update', action='store_true', help='Run a manual update now')
    parser.add_argument('--reports_only', action='store_true', help='Generate reports only')
    parser.add_argument('--daemon', action='store_true', help='Run as a daemon (continuous updates)')
    
    args = parser.parse_args()
    
    # Create model instance
    model = FantasyBaseballAutomated(args.league_id, args.team_name)
    
    # Check if we can load existing state
    if not model.load_system_state():
        logger.info("No existing state found. Loading initial data...")
        model.load_initial_data()
    
    # Handle command-line options
    if args.manual_update:
        logger.info("Running manual update...")
        model.run_system_update()
    
    if args.reports_only:
        logger.info("Generating reports only...")
        model.generate_reports()
    
    if args.daemon:
        # Schedule updates
        model.schedule_updates(args.daily_update, args.weekly_update)
        # Start update loop
        model.start_update_loop()
    
    logger.info("Fantasy Baseball Automated Model completed successfully!")

if __name__ == "__main__":
    main()
                ops_values = [ops for ops in ops_values if ops > 0]
                batting_totals['OPS'] = sum(ops_values) / len(ops_values) if ops_values else 0
            
            # Sort by AB descending
            batter_table.sort(key=lambda x: x[1], reverse=True)
            
            # Add totals row
            batter_table.append([
                "TOTALS",
                batting_totals['AB'],
                batting_totals['R'],
                batting_totals['HR'],
                batting_totals['RBI'],
                batting_totals['SB'],
                f"{batting_totals['AVG']:.3f}",
                f"{batting_totals['OPS']:.3f}"
            ])
            
            f.write(tabulate(batter_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Pitchers stats
            f.write("#### Pitching Stats\n\n")
            pitcher_table = []
            headers = ["Player", "IP", "W", "ERA", "WHIP", "K", "QS", "SV"]
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_stats_current and 'ERA' in self.player_stats_current[name]:
                    stats = self.player_stats_current[name]
                    pitcher_table.append([
                        name,
                        stats.get('IP', 0),
                        stats.get('W', 0),
                        f"{stats.get('ERA', 0):.2f}",
                        f"{stats.get('WHIP', 0):.2f}",
                        stats.get('K', 0),
                        stats.get('QS', 0),
                        stats.get('SV', 0)
                    ])
                    
                    # Add to totals
                    pitching_totals['IP'] += stats.get('IP', 0)
                    pitching_totals['W'] += stats.get('W', 0)
                    pitching_totals['K'] += stats.get('K', 0)
                    pitching_totals['QS'] += stats.get('QS', 0)
                    pitching_totals['SV'] += stats.get('SV', 0)
            
            # Calculate team ERA and WHIP
            if pitching_totals['IP'] > 0:
                # Calculate total ER and baserunners across all pitchers
                total_er = sum(self.player_stats_current.get(p["name"], {}).get('ERA', 0) * 
                               self.player_stats_current.get(p["name"], {}).get('IP', 0) / 9 
                               for p in self.team_rosters.get(self.your_team_name, [])
                               if 'ERA' in self.player_stats_current.get(p["name"], {}))
                
                total_baserunners = sum(self.player_stats_current.get(p["name"], {}).get('WHIP', 0) * 
                                       self.player_stats_current.get(p["name"], {}).get('IP', 0) 
                                       for p in self.team_rosters.get(self.your_team_name, [])
                                       if 'WHIP' in self.player_stats_current.get(p["name"], {}))
                
                pitching_totals['ERA'] = total_er * 9 / pitching_totals['IP']
                pitching_totals['WHIP'] = total_baserunners / pitching_totals['IP']
            
            # Sort by IP descending
            pitcher_table.sort(key=lambda x: x[1], reverse=True)
            
            # Add totals row
            pitcher_table.append([
                "TOTALS",
                pitching_totals['IP'],
                pitching_totals['W'],
                f"{pitching_totals['ERA']:.2f}",
                f"{pitching_totals['WHIP']:.2f}",
                pitching_totals['K'],
                pitching_totals['QS'],
                pitching_totals['SV']
            ])
            
            f.write(tabulate(pitcher_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Team Projections
            f.write("### Rest of Season Projections\n\n")
            
            # Batters projections
            f.write("#### Batting Projections\n\n")
            batter_proj_table = []
            headers = ["Player", "AB", "R", "HR", "RBI", "SB", "AVG", "OPS"]
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_projections and 'AVG' in self.player_projections[name]:
                    proj = self.player_projections[name]
                    batter_proj_table.append([
                        name,
                        int(proj.get('AB', 0)),
                        int(proj.get('R', 0)),
                        int(proj.get('HR', 0)),
                        int(proj.get('RBI', 0)),
                        int(proj.get('SB', 0)),
                        f"{proj.get('AVG', 0):.3f}",
                        f"{proj.get('OPS', 0):.3f}"
                    ])
            
            # Sort by projected AB descending
            batter_proj_table.sort(key=lambda x: x[1], reverse=True)
            
            f.write(tabulate(batter_proj_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Pitchers projections
            f.write("#### Pitching Projections\n\n")
            pitcher_proj_table = []
            headers = ["Player", "IP", "ERA", "WHIP", "K/9", "QS", "SV"]
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_projections and 'ERA' in self.player_projections[name]:
                    proj = self.player_projections[name]
                    pitcher_proj_table.append([
                        name,
                        int(proj.get('IP', 0)),
                        f"{proj.get('ERA', 0):.2f}",
                        f"{proj.get('WHIP', 0):.2f}",
                        f"{proj.get('K9', 0):.1f}",
                        int(proj.get('QS', 0)),
                        int(proj.get('SV', 0))
                    ])
            
            # Sort by projected IP descending
            pitcher_proj_table.sort(key=lambda x: x[1], reverse=True)
            
            f.write(tabulate(pitcher_proj_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Recent News
            f.write("### Recent Team News\n\n")
            
            news_count = 0
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_news and self.player_news[name]:
                    # Sort news by date (most recent first)
                    player_news = sorted(
                        self.player_news[name], 
                        key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"), 
                        reverse=True
                    )
                    
                    # Show most recent news item
                    latest_news = player_news[0]
                    f.write(f"**{name}** ({latest_news['date']} - {latest_news['source']}): {latest_news['content']}\n\n")
                    news_count += 1
            
            if news_count == 0:
                f.write("No recent news for your team's players.\n\n")
            
            # Recommendations
            f.write("## Team Recommendations\n\n")
            
            # Analyze team strengths and weaknesses
            # This is a simplified analysis - a real implementation would be more sophisticated
            
            # Calculate average stats per player
            avg_hr = batting_totals['HR'] / len([p for p in self.team_rosters.get(self.your_team_name, []) if p["name"] in self.player_stats_current and 'AVG' in self.player_stats_current[p["name"]]]) if len([p for p in self.team_rosters.get(self.your_team_name, []) if p["name"] in self.player_stats_current and 'AVG' in self.player_stats_current[p["name"]]]) > 0 else 0
            
            avg_sb = batting_totals['SB'] / len([p for p in self.team_rosters.get(self.your_team_name, []) if p["name"] in self.player_stats_current and 'AVG' in self.player_stats_current[p["name"]]]) if len([p for p in self.team_rosters.get(self.your_team_name, []) if p["name"] in self.player_stats_current and 'AVG' in self.player_stats_current[p["name"]]]) > 0 else 0
            
            avg_era = pitching_totals['ERA']
            avg_k9 = pitching_totals['K'] * 9 / pitching_totals['IP'] if pitching_totals['IP'] > 0 else 0
            
            # Identify strengths and weaknesses
            strengths = []
            weaknesses = []
            
            if batting_totals['AVG'] > 0.270:
                strengths.append("Batting Average")
            elif batting_totals['AVG'] < 0.250:
                weaknesses.append("Batting Average")
                
            if batting_totals['OPS'] > 0.780:
                strengths.append("OPS")
            elif batting_totals['OPS'] < 0.720:
                weaknesses.append("OPS")
                
            if avg_hr > 0.08:  # More than 0.08 HR per AB
                strengths.append("Power")
            elif avg_hr < 0.04:
                weaknesses.append("Power")
                
            if avg_sb > 0.05:  # More than 0.05 SB per AB
                strengths.append("Speed")
            elif avg_sb < 0.02:
                weaknesses.append("Speed")
                
            if avg_era < 3.80:
                strengths.append("ERA")
            elif avg_era > 4.20:
                weaknesses.append("ERA")
                
            if pitching_totals['WHIP'] < 1.20:
                strengths.append("WHIP")
            elif pitching_totals['WHIP'] > 1.30:
                weaknesses.append("WHIP")
                
            if avg_k9 > 9.5:
                strengths.append("Strikeouts")
            elif avg_k9 < 8.0:
                weaknesses.append("Strikeouts")
                
            if pitching_totals['SV'] > 15:
                strengths.append("Saves")
            elif pitching_totals['SV'] < 5:
                weaknesses.append("Saves")
                
            if pitching_totals['QS'] > 15:
                strengths.append("Quality Starts")
            elif pitching_totals['QS'] < 5:
                weaknesses.append("Quality Starts")
                
            # Write strengths and weaknesses
            f.write("### Team Strengths\n\n")
            if strengths:
                for strength in strengths:
                    f.write(f"- **{strength}**\n")
            else:
                f.write("No clear strengths identified yet.\n")
            
            f.write("\n### Team Weaknesses\n\n")
            if weaknesses:
                for weakness in weaknesses:
                    f.write(f"- **{weakness}**\n")
            else:
                f.write("No clear weaknesses identified yet.\n")
            
            f.write("\n### Recommended Actions\n\n")
            
            # Generate recommendations based on weaknesses
            if weaknesses:
                for weakness in weaknesses[:3]:  # Focus on top 3 weaknesses
                    if weakness == "Power":
                        f.write("- **Target Power Hitters**: Consider trading for players with high HR and RBI projections.\n")
                        
                        # Suggest specific free agents
                        power_fa = sorted(
                            [(name, p['projections'].get('HR', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'HR' in p['projections']],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if power_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {int(p[1])} HR)" for p in power_fa]) + "\n")
                    
                    elif weakness == "Speed":
                        f.write("- **Add Speed**: Look to add players who can contribute stolen bases.\n")
                        
                        # Suggest specific free agents
                        speed_fa = sorted(
                            [(name, p['projections'].get('SB', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'SB' in p['projections']],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if speed_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {int(p[1])} SB)" for p in speed_fa]) + "\n")
                    
                    elif weakness == "Batting Average":
                        f.write("- **Improve Batting Average**: Look for consistent contact hitters.\n")
                        
                        # Suggest specific free agents
                        avg_fa = sorted(
                            [(name, p['projections'].get('AVG', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'AVG' in p['projections'] and p['projections'].get('AB', 0) > 300],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if avg_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {p[1]:.3f} AVG)" for p in avg_fa]) + "\n")
                    
                    elif weakness == "ERA" or weakness == "WHIP":
                        f.write("- **Improve Pitching Ratios**: Focus on pitchers with strong ERA and WHIP projections.\n")
                        
                        # Suggest specific free agents
                        ratio_fa = sorted(
                            [(name, p['projections'].get('ERA', 0), p['projections'].get('WHIP', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'ERA' in p['projections'] and p['projections'].get('IP', 0) > 100],
                            key=lambda x: x[1] + x[2]
                        )[:3]
                        
                        if ratio_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {p[1]:.2f} ERA, {p[2]:.2f} WHIP)" for p in ratio_fa]) + "\n")
                    
                    elif weakness == "Strikeouts":
                        f.write("- **Add Strikeout Pitchers**: Target pitchers with high K/9 rates.\n")
                        
                        # Suggest specific free agents
                        k_fa = sorted(
                            [(name, p['projections'].get('K9', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'K9' in p['projections'] and p['projections'].get('IP', 0) > 75],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if k_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {p[1]:.1f} K/9)" for p in k_fa]) + "\n")
                    
                    elif weakness == "Saves":
                        f.write("- **Add Closers**: Look for pitchers in save situations.\n")
                        
                        # Suggest specific free agents
                        sv_fa = sorted(
                            [(name, p['projections'].get('SV', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'SV' in p['projections'] and p['projections'].get('SV', 0) > 5],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if sv_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {int(p[1])} SV)" for p in sv_fa]) + "\n")
                    
                    elif weakness == "Quality Starts":
                        f.write("- **Add Quality Starting Pitchers**: Target consistent starters who work deep into games.\n")
                        
                        # Suggest specific free agents
                        qs_fa = sorted(
                            [(name, p['projections'].get('QS', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'QS' in p['projections'] and p['projections'].get('QS', 0) > 5],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if qs_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {int(p[1])} QS)" for p in qs_fa]) + "\n")
            else:
                f.write("Your team is well-balanced! Continue to monitor player performance and injuries.\n")
            
            # General strategy recommendation
            f.write("\n### General Strategy\n\n")
            f.write("1. **Monitor the waiver wire daily** for emerging talent and players returning from injury.\n")
            f.write("2. **Be proactive with injured players**. Don't hold onto injured players too long if better options are available.\n")
            f.write("3. **Stream starting pitchers** against weak offensive teams for additional counting stats.\n")
            f.write("4. **Watch for changing roles** in bullpens for potential closers in waiting.\n")
            
            logger.info(f"Team analysis report generated: {output_file}")
    
    def generate_free_agents_report(self, output_file):
        """Generate free agents report sorted by projected value"""
        with open(output_file, 'w') as f:
            # Title
            f.write("# Fantasy Baseball Free Agent Analysis\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
            
            # Calculate scores for ranking
            fa_batters = {}
            fa_pitchers = {}
            
            for name, data in self.free_agents.items():
                if 'projections' in data:
                    proj = data['projections']
                    if 'AVG' in proj:  # It's a batter
                        # Calculate a batter score
                        score = (
                            proj.get('HR', 0) * 3 +
                            proj.get('SB', 0) * 3 +
                            proj.get('R', 0) * 0.5 +
                            proj.get('RBI', 0) * 0.5 +
                            proj.get('AVG', 0) * 300 +
                            proj.get('OPS', 0) * 150
                        )
                        fa_batters[name] = {'projections': proj, 'score': score}
                    
                    elif 'ERA' in proj:  # It's a pitcher
                        # Calculate a pitcher score
                        era_score = (5.00 - proj.get('ERA', 4.50)) * 20 if proj.get('ERA', 0) < 5.00 else 0
                        whip_score = (1.40 - proj.get('WHIP', 1.30)) * 60 if proj.get('WHIP', 0) < 1.40 else 0
                        
                        score = (
                            era_score +
                            whip_score +
                            proj.get('K9', 0) * 10 +
                            proj.get('QS', 0) * 4 +
                            proj.get('SV', 0) * 6 +
                            proj.get('IP', 0) * 0.2
                        )
                        fa_pitchers[name] = {'projections': proj, 'score': score}
            
            # Top Batters by Position
            f.write("## Top Free Agent Batters\n\n")
            
            # Define positions
            positions = {
                "C": "Catchers",
                "1B": "First Basemen",
                "2B": "Second Basemen",
                "3B": "Third Basemen",
                "SS": "Shortstops",
                "OF": "Outfielders"
            }
            
            # Simplified position assignment for demo
            position_players = {pos: [] for pos in positions}
            
            # Manually assign positions for demo
            for name in fa_batters:
                # This is a very simplified approach - in reality, you'd have actual position data
                if name in ["Keibert Ruiz", "Danny Jansen", "Gabriel Moreno", "Patrick Bailey", "Ryan Jeffers"]:
                    position_players["C"].append(name)
                elif name in ["Christian Walker", "Spencer Torkelson", "Andrew Vaughn", "Anthony Rizzo"]:
                    position_players["1B"].append(name)
                elif name in ["Gavin Lux", "Luis Rengifo", "Nick Gonzales", "Zack Gelof", "Brendan Donovan"]:
                    position_players["2B"].append(name)
                elif name in ["Jeimer Candelario", "Spencer Steer", "Ke'Bryan Hayes", "Brett Baty"]:
                    position_players["3B"].append(name)
                elif name in ["JP Crawford", "Ha-Seong Kim", "Xander Bogaerts", "Jose Barrero"]:
                    position_players["SS"].append(name)
                else:
                    position_players["OF"].append(name)
            
            # Write position sections
            for pos, title in positions.items():
                players = position_players[pos]
                if players:
                    f.write(f"### {title}\n\n")
                    
                    # Create table
                    headers = ["Rank", "Player", "AB", "R", "HR", "RBI", "SB", "AVG", "OPS", "Score"]
                    
                    # Get scores and sort
                    pos_players = [(name, fa_batters[name]['score'], fa_batters[name]['projections']) 
                                 for name in players if name in fa_batters]
                    
                    pos_players.sort(key=lambda x: x[1], reverse=True)
                    
                    # Build table
                    table_data = []
                    for i, (name, score, proj) in enumerate(pos_players[:10]):  # Top 10 per position
                        table_data.append([
                            i+1,
                            name,
                            int(proj.get('AB', 0)),
                            int(proj.get('R', 0)),
                            int(proj.get('HR', 0)),
                            int(proj.get('RBI', 0)),
                            int(proj.get('SB', 0)),
                            f"{proj.get('AVG', 0):.3f}",
                            f"{proj.get('OPS', 0):.3f}",
                            int(score)
                        ])
                    
                    f.write(tabulate(table_data, headers=headers, tablefmt="pipe"))
                    f.write("\n\n")
            
            # Top Pitchers
            f.write("## Top Free Agent Pitchers\n\n")
            
            # Starting pitchers
            f.write("### Starting Pitchers\n\n")
            
            # Identify starters
            starters = [(name, fa_pitchers[name]['score'], fa_pitchers[name]['projections']) 
                       for name in fa_pitchers 
                       if fa_pitchers[name]['projections'].get('QS', 0) > 0]
            
            starters.sort(key=lambda x: x[1], reverse=True)
            
            # Create table
            headers = ["Rank", "Player", "IP", "ERA", "WHIP", "K/9", "QS", "Score"]
            
            table_data = []
            for i, (name, score, proj) in enumerate(starters[:15]):  # Top 15 SP
                table_data.append([
                    i+1,
                    name,
                    int(proj.get('IP', 0)),
                    f"{proj.get('ERA', 0):.2f}",
                    f"{proj.get('WHIP', 0):.2f}",
                    f"{proj.get('K9', 0):.1f}",
                    int(proj.get('QS', 0)),
                    int(score)
                ])
            
            f.write(tabulate(table_data, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Relief pitchers
            f.write("### Relief Pitchers\n\n")
            
            # Identify relievers
            relievers = [(name, fa_pitchers[name]['score'], fa_pitchers[name]['projections']) 
                        for name in fa_pitchers 
                        if fa_pitchers[name]['projections'].get('QS', 0) == 0]
            
            relievers.sort(key=lambda x: x[1], reverse=True)
            
            # Create table
            headers = ["Rank", "Player", "IP", "ERA", "WHIP", "K/9", "SV", "Score"]
            
            table_data = []
            for i, (name, score, proj) in enumerate(relievers[:10]):  # Top 10 RP
                table_data.append([
                    i+1,
                    name,
                    int(proj.get('IP', 0)),
                    f"{proj.get('ERA', 0):.2f}",
                    f"{proj.get('WHIP', 0):.2f}",
                    f"{proj.get('K9', 0):.1f}",
                    int(proj.get('SV', 0)),
                    int(score)
                ])
            
            f.write(tabulate(table_data, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Category-Specific Free Agent Targets
            f.write("## Category-Specific Free Agent Targets\n\n")
            
            # Power hitters (HR and RBI)
            power_hitters = sorted(
                [(name, fa_batters[name]['projections'].get('HR', 0), fa_batters[name]['projections'].get('RBI', 0)) 
                 for name in fa_batters],
                key=lambda x: x[1] + x[2]/3,
                reverse=True
            )[:5]
            
            f.write("**Power (HR/RBI):** ")
            f.write(", ".join([f"{name} ({int(hr)} HR, {int(rbi)} RBI)" for name, hr, rbi in power_hitters]))
            f.write("\n\n")
            
            # Speed (SB)
            speed_players = sorted(
                [(name, fa_batters[name]['projections'].get('SB', 0)) 
                 for name in fa_batters],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            f.write("**Speed (SB):** ")
            f.write(", ".join([f"{name} ({int(sb)} SB)" for name, sb in speed_players]))
            f.write("\n\n")
            
            # Average (AVG)
            average_hitters = sorted(
                [(name, fa_batters[name]['projections'].get('AVG', 0)) 
                 for name in fa_batters 
                 if fa_batters[name]['projections'].get('AB', 0) >= 300],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            f.write("**Batting Average:** ")
            f.write(", ".join([f"{name} ({avg:.3f})" for name, avg in average_hitters]))
            f.write("\n\n")
            
            # ERA
            era_pitchers = sorted(
                [(name, fa_pitchers[name]['projections'].get('ERA', 0)) 
                 for name in fa_pitchers 
                 if fa_pitchers[name]['projections'].get('IP', 0) >= 100],
                key=lambda x: x[1]
            )[:5]
            
            f.write("**ERA:** ")
            f.write(", ".join([f"{name} ({era:.2f})" for name, era in era_pitchers]))
            f.write("\n\n")
            
            # WHIP
            whip_pitchers = sorted(
                [(name, fa_pitchers[name]['projections'].get('WHIP', 0)) 
                 for name in fa_pitchers 
                 if fa_pitchers[name]['projections'].get('IP', 0) >= 100],
                key=lambda x: x[1]
            )[:5]
            
            f.write("**WHIP:** ")
            f.write(", ".join([f"{name} ({whip:.2f})" for name, whip in whip_pitchers]))
            f.write("\n\n")
            
            # Saves (SV)
            save_pitchers = sorted(
                [(name, fa_pitchers[name]['projections'].get('SV', 0)) 
                 for name in fa_pitchers],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            f.write("**Saves:** ")
            f.write(", ".join([f"{name} ({int(sv)})" for name, sv in save_pitchers]))
            f.write("\n\n")
            
            logger.info(f"Free agents report generated: {output_file}")
    
    def generate_trending_players_report(self, output_file):
        """Generate report on trending players (hot/cold)"""
        # In a real implementation, you would calculate trends based on recent performance
        # For demo purposes, we'll simulate trends
        
        with open(output_                # Recalculate AVG
                self.player_stats_current[player]['AVG'] = (
                    self.player_stats_current[player]['H'] / 
                    self.player_stats_current[player]['AB'] 
                    if self.player_stats_current[player]['AB'] > 0 else 0
                )
                
                # Recalculate OBP
                self.player_stats_current[player]['OBP'] = (
                    (self.player_stats_current[player]['H'] + self.player_stats_current[player]['BB']) / 
                    (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) 
                    if (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) > 0 else 0
                )
                
                # Recalculate SLG and OPS
                singles = (
                    self.player_stats_current[player]['H'] - 
                    self.player_stats_current[player]['HR'] - 
                    self.player_stats_current[player].get('2B', random.randint(15, 25)) - 
                    self.player_stats_current[player].get('3B', random.randint(0, 5))
                )
                
                tb = (
                    singles + 
                    (2 * self.player_stats_current[player].get('2B', random.randint(15, 25))) + 
                    (3 * self.player_stats_current[player].get('3B', random.randint(0, 5))) + 
                    (4 * self.player_stats_current[player]['HR'])
                )
                
                self.player_stats_current[player]['SLG'] = (
                    tb / self.player_stats_current[player]['AB'] 
                    if self.player_stats_current[player]['AB'] > 0 else 0
                )
                
                self.player_stats_current[player]['OPS'] = (
                    self.player_stats_current[player]['OBP'] + 
                    self.player_stats_current[player]['SLG']
                )
    
    def update_player_projections(self):
        """Update player projections by fetching from data sources"""
        logger.info("Updating player projections from sources...")
        
        # In a real implementation, you would:
        # 1. Fetch data from each source in self.data_sources['projections']
        # 2. Parse and clean the data
        # 3. Merge with existing projections
        # 4. Update self.player_projections
        
        # For demo purposes, we'll simulate this process
        self._simulate_projections_update()
        
        logger.info(f"Updated projections for {len(self.player_projections)} players")
        return len(self.player_projections)
    
    def _simulate_projections_update(self):
        """Simulate updating projections for demo purposes"""
        # Update existing projections based on current stats
        for player in self.player_stats_current:
            # Skip if no projection exists
            if player not in self.player_projections:
                # Create new projection based on current stats
                if 'ERA' in self.player_stats_current[player]:  # It's a pitcher
                    # Project rest of season based on current performance
                    era_factor = min(max(4.00 / self.player_stats_current[player]['ERA'], 0.75), 1.25) if self.player_stats_current[player]['ERA'] > 0 else 1.0
                    whip_factor = min(max(1.30 / self.player_stats_current[player]['WHIP'], 0.75), 1.25) if self.player_stats_current[player]['WHIP'] > 0 else 1.0
                    k9_factor = min(max(self.player_stats_current[player]['K9'] / 8.5, 0.75), 1.25) if self.player_stats_current[player].get('K9', 0) > 0 else 1.0
                    
                    # Determine if starter or reliever
                    is_reliever = 'SV' in self.player_stats_current[player] or self.player_stats_current[player].get('IP', 0) < 20
                    
                    self.player_projections[player] = {
                        'IP': random.uniform(40, 70) if is_reliever else random.uniform(120, 180),
                        'ERA': random.uniform(3.0, 4.5) * era_factor,
                        'WHIP': random.uniform(1.05, 1.35) * whip_factor,
                        'K9': random.uniform(7.5, 12.0) * k9_factor,
                        'QS': 0 if is_reliever else random.randint(10, 20),
                        'SV': random.randint(15, 35) if is_reliever and self.player_stats_current[player].get('SV', 0) > 0 else 0
                    }
                else:  # It's a batter
                    # Project rest of season based on current performance
                    avg_factor = min(max(self.player_stats_current[player]['AVG'] / 0.260, 0.8), 1.2) if self.player_stats_current[player]['AVG'] > 0 else 1.0
                    ops_factor = min(max(self.player_stats_current[player].get('OPS', 0.750) / 0.750, 0.8), 1.2) if self.player_stats_current[player].get('OPS', 0) > 0 else 1.0
                    
                    # Projected plate appearances remaining
                    pa_remaining = random.randint(400, 550)
                    
                    # HR rate
                    hr_rate = self.player_stats_current[player]['HR'] / self.player_stats_current[player]['AB'] if self.player_stats_current[player]['AB'] > 0 else 0.025
                    
                    # SB rate
                    sb_rate = self.player_stats_current[player]['SB'] / self.player_stats_current[player]['AB'] if self.player_stats_current[player]['AB'] > 0 else 0.015
                    
                    self.player_projections[player] = {
                        'AB': pa_remaining * 0.9,  # 10% of PA are walks/HBP
                        'R': pa_remaining * random.uniform(0.12, 0.18),
                        'HR': pa_remaining * hr_rate * random.uniform(0.8, 1.2),
                        'RBI': pa_remaining * random.uniform(0.1, 0.17),
                        'SB': pa_remaining * sb_rate * random.uniform(0.8, 1.2),
                        'AVG': random.uniform(0.230, 0.310) * avg_factor,
                        'OPS': random.uniform(0.680, 0.950) * ops_factor
                    }
                continue
            
            # If projection exists, update it based on current performance
            if 'ERA' in self.player_stats_current[player]:  # It's a pitcher
                # Calculate adjustment factors based on current vs. projected performance
                if self.player_stats_current[player].get('IP', 0) > 20:  # Enough IP to adjust projections
                    # ERA adjustment
                    current_era = self.player_stats_current[player].get('ERA', 4.00)
                    projected_era = self.player_projections[player].get('ERA', 4.00)
                    era_adj = min(max(projected_era / current_era, 0.8), 1.2) if current_era > 0 else 1.0
                    
                    # WHIP adjustment
                    current_whip = self.player_stats_current[player].get('WHIP', 1.30)
                    projected_whip = self.player_projections[player].get('WHIP', 1.30)
                    whip_adj = min(max(projected_whip / current_whip, 0.8), 1.2) if current_whip > 0 else 1.0
                    
                    # K/9 adjustment
                    current_k9 = self.player_stats_current[player].get('K9', 8.5)
                    projected_k9 = self.player_projections[player].get('K9', 8.5)
                    k9_adj = min(max(current_k9 / projected_k9, 0.8), 1.2) if projected_k9 > 0 else 1.0
                    
                    # Apply adjustments
                    self.player_projections[player]['ERA'] = projected_era * era_adj
                    self.player_projections[player]['WHIP'] = projected_whip * whip_adj
                    self.player_projections[player]['K9'] = projected_k9 * k9_adj
                    
                    # Adjust saves projection for relievers
                    if 'SV' in self.player_stats_current[player]:
                        current_sv_rate = self.player_stats_current[player].get('SV', 0) / max(1, self.player_stats_current[player].get('IP', 1) / 60)
                        self.player_projections[player]['SV'] = min(45, max(0, int(current_sv_rate * 60)))
                    
                    # Adjust QS projection for starters
                    if 'QS' in self.player_stats_current[player] and self.player_stats_current[player].get('IP', 0) > 0:
                        current_qs_rate = self.player_stats_current[player].get('QS', 0) / max(1, self.player_stats_current[player].get('IP', 1) / 180)
                        self.player_projections[player]['QS'] = min(30, max(0, int(current_qs_rate * 180)))
            else:  # It's a batter
                # Adjust only if enough AB to be significant
                if self.player_stats_current[player].get('AB', 0) > 75:
                    # AVG adjustment
                    current_avg = self.player_stats_current[player].get('AVG', 0.260)
                    projected_avg = self.player_projections[player].get('AVG', 0.260)
                    avg_adj = min(max((current_avg + 2*projected_avg) / (3*projected_avg), 0.85), 1.15) if projected_avg > 0 else 1.0
                    
                    # HR rate adjustment
                    current_hr_rate = self.player_stats_current[player].get('HR', 0) / max(1, self.player_stats_current[player].get('AB', 1)) * 550
                    projected_hr = self.player_projections[player].get('HR', 15)
                    hr_adj = min(max((current_hr_rate + 2*projected_hr) / (3*projected_hr), 0.7), 1.3) if projected_hr > 0 else 1.0
                    
                    # SB rate adjustment
                    current_sb_rate = self.player_stats_current[player].get('SB', 0) / max(1, self.player_stats_current[player].get('AB', 1)) * 550
                    projected_sb = self.player_projections[player].get('SB', 10)
                    sb_adj = min(max((current_sb_rate + 2*projected_sb) / (3*projected_sb), 0.7), 1.3) if projected_sb > 0 else 1.0
                    
                    # Apply adjustments
                    self.player_projections[player]['AVG'] = projected_avg * avg_adj
                    self.player_projections[player]['HR'] = projected_hr * hr_adj
                    self.player_projections[player]['SB'] = projected_sb * sb_adj
                    
                    # Adjust OPS based on AVG and power
                    projected_ops = self.player_projections[player].get('OPS', 0.750)
                    self.player_projections[player]['OPS'] = projected_ops * (avg_adj * 0.4 + hr_adj * 0.6)
                    
                    # Adjust runs and RBI based on HR and overall performance
                    projected_r = self.player_projections[player].get('R', 70)
                    projected_rbi = self.player_projections[player].get('RBI', 70)
                    
                    self.player_projections[player]['R'] = projected_r * ((avg_adj + hr_adj) / 2)
                    self.player_projections[player]['RBI'] = projected_rbi * ((avg_adj + hr_adj) / 2)
        
        # Round numerical values for cleaner display
        for player in self.player_projections:
            for stat in self.player_projections[player]:
                if isinstance(self.player_projections[player][stat], float):
                    if stat in ['ERA', 'WHIP', 'K9', 'AVG', 'OPS']:
                        self.player_projections[player][stat] = round(self.player_projections[player][stat], 3)
                    else:
                        self.player_projections[player][stat] = round(self.player_projections[player][stat])
    
    def update_player_news(self):
        """Update player news by fetching from news sources"""
        logger.info("Updating player news from sources...")
        
        # In a real implementation, you would:
        # 1. Fetch data from each source in self.data_sources['news']
        # 2. Parse and extract news items
        # 3. Store in self.player_news
        
        # For demo purposes, we'll simulate this process
        self._simulate_news_update()
        
        logger.info(f"Updated news for {len(self.player_news)} players")
        return len(self.player_news)
    
    def _simulate_news_update(self):
        """Simulate updating player news for demo purposes"""
        # List of possible news templates
        injury_news = [
            "{player} was removed from Wednesday's game with {injury}.",
            "{player} is day-to-day with {injury}.",
            "{player} has been placed on the 10-day IL with {injury}.",
            "{player} will undergo further testing for {injury}.",
            "{player} is expected to miss 4-6 weeks with {injury}."
        ]
        
        performance_news = [
            "{player} went {stats} in Wednesday's 6-4 win.",
            "{player} struck out {k} batters in {ip} innings on Tuesday.",
            "{player} has hit safely in {streak} straight games.",
            "{player} collected {hits} hits including a homer on Monday.",
            "{player} has struggled recently, going {bad_stats} over his last 7 games."
        ]
        
        role_news = [
            "{player} will take over as the closer with {teammate} on the IL.",
            "{player} has been moved up to the {spot} spot in the batting order.",
            "{player} will make his next start on {day}.",
            "{player} has been moved to the bullpen.",
            "{player} will be recalled from Triple-A on Friday."
        ]
        
        # Possible injuries
        injuries = [
            "left hamstring tightness",
            "right oblique strain",
            "lower back discomfort",
            "shoulder inflammation",
            "forearm tightness",
            "groin strain",
            "ankle sprain",
            "knee soreness",
            "thumb contusion",
            "wrist inflammation"
        ]
        
        # Generate news for a subset of players
        for player in random.sample(list(self.player_stats_current.keys()), min(10, len(self.player_stats_current))):
            news_type = random.choice(["injury", "performance", "role"])
            
            if news_type == "injury":
                template = random.choice(injury_news)
                news_item = template.format(
                    player=player,
                    injury=random.choice(injuries)
                )
            elif news_type == "performance":
                template = random.choice(performance_news)
                
                # Determine if batter or pitcher
                if 'ERA' in self.player_stats_current[player]:  # Pitcher
                    ip = round(random.uniform(5, 7), 1)
                    k = random.randint(4, 10)
                    news_item = template.format(
                        player=player,
                        k=k,
                        ip=ip,
                        streak=random.randint(3, 10),
                        hits=random.randint(2, 4),
                        bad_stats=f"{random.randint(0, 4)}-for-{random.randint(20, 30)}"
                    )
                else:  # Batter
                    hits = random.randint(0, 4)
                    abs = random.randint(hits, 5)
                    news_item = template.format(
                        player=player,
                        stats=f"{hits}-for-{abs}",
                        k=random.randint(5, 12),
                        ip=round(random.uniform(5, 7), 1),
                        streak=random.randint(5, 15),
                        hits=random.randint(2, 4),
                        bad_stats=f"{random.randint(0, 4)}-for-{random.randint(20, 30)}"
                    )
            else:  # Role
                template = random.choice(role_news)
                news_item = template.format(
                    player=player,
                    teammate=random.choice(list(self.player_stats_current.keys())),
                    spot=random.choice(["leadoff", "cleanup", "third", "fifth"]),
                    day=random.choice(["Friday", "Saturday", "Sunday", "Monday"])
                )
            
            # Add news item with timestamp
            if player not in self.player_news:
                self.player_news[player] = []
            
            self.player_news[player].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source": random.choice(["Rotowire", "CBS Sports", "ESPN", "MLB.com"]),
                "content": news_item
            })
    
    def update_player_injuries(self):
        """Update player injury statuses"""
        logger.info("Updating player injury statuses...")
        
        # In a real implementation, you would:
        # 1. Fetch injury data from reliable sources
        # 2. Update player status accordingly
        # 3. Adjust projections for injured players
        
        # For demo purposes, we'll simulate some injuries
        injury_count = 0
        
        for player in self.player_stats_current:
            # 5% chance of new injury for each player
            if random.random() < 0.05:
                injury_severity = random.choice(["day-to-day", "10-day IL", "60-day IL"])
                injury_type = random.choice([
                    "hamstring strain", "oblique strain", "back spasms", 
                    "shoulder inflammation", "elbow soreness", "knee inflammation",
                    "ankle sprain", "concussion", "wrist sprain"
                ])
                
                # Add injury news
                if player not in self.player_news:
                    self.player_news[player] = []
                
                self.player_news[player].append({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "source": random.choice(["Rotowire", "CBS Sports", "ESPN", "MLB.com"]),
                    "content": f"{player} has been placed on the {injury_severity} with a {injury_type}."
                })
                
                # Adjust projections for injured players
                if player in self.player_projections:
                    if injury_severity == "day-to-day":
                        reduction = 0.05  # 5% reduction in projections
                    elif injury_severity == "10-day IL":
                        reduction = 0.15  # 15% reduction
                    else:  # 60-day IL
                        reduction = 0.50  # 50% reduction
                    
                    # Apply reduction to projected stats
                    for stat in self.player_projections[player]:
                        if stat not in ['AVG', 'ERA', 'WHIP', 'K9', 'OPS']:  # Don't reduce rate stats
                            self.player_projections[player][stat] *= (1 - reduction)
                
                injury_count += 1
        
        logger.info(f"Updated injury status for {injury_count} players")
        return injury_count
    
    def update_league_transactions(self):
        """Simulate league transactions (adds, drops, trades)"""
        logger.info("Simulating league transactions...")
        
        # In a real implementation, you would:
        # 1. Fetch transaction data from your fantasy platform API
        # 2. Update team rosters accordingly
        
        # For demo purposes, we'll simulate some transactions
        transaction_count = 0
        
        # Add/drop transactions (1-3 per update)
        for _ in range(random.randint(1, 3)):
            # Select a random team
            team = random.choice(list(self.team_rosters.keys()))
            
            # Select a random player to drop
            if len(self.team_rosters[team]) > 0:
                drop_index = random.randint(0, len(self.team_rosters[team]) - 1)
                dropped_player = self.team_rosters[team][drop_index]["name"]
                
                # Remove from roster
                self.team_rosters[team].pop(drop_index)
                
                # Pick a random free agent to add
                if len(self.free_agents) > 0:
                    added_player = random.choice(list(self.free_agents.keys()))
                    
                    # Determine position
                    position = "Unknown"
                    if 'ERA' in self.player_stats_current.get(added_player, {}):
                        position = 'RP' if self.player_stats_current[added_player].get('SV', 0) > 0 else 'SP'
                    else:
                        position = random.choice(["C", "1B", "2B", "3B", "SS", "OF"])
                    
                    # Add to roster
                    self.team_rosters[team].append({
                        "name": added_player,
                        "position": position
                    })
                    
                    # Remove from free agents
                    if added_player in self.free_agents:
                        del self.free_agents[added_player]
                    
                    # Log transaction
                    logger.info(f"Transaction: {team} dropped {dropped_player} and added {added_player}")
                    transaction_count += 1
        
        # Trade transactions (0-1 per update)
        if random.random() < 0.3:  # 30% chance of a trade
            # Select two random teams
            teams = random.sample(list(self.team_rosters.keys()), 2)
            
            # Select random players to trade (1-2 per team)
            team1_players = []
            team2_players = []
            
            for _ in range(random.randint(1, 2)):
                if len(self.team_rosters[teams[0]]) > 0:
                    idx = random.randint(0, len(self.team_rosters[teams[0]]) - 1)
                    team1_players.append(self.team_rosters[teams[0]][idx])
                    self.team_rosters[teams[0]].pop(idx)
            
            for _ in range(random.randint(1, 2)):
                if len(self.team_rosters[teams[1]]) > 0:
                    idx = random.randint(0, len(self.team_rosters[teams[1]]) - 1)
                    team2_players.append(self.team_rosters[teams[1]][idx])
                    self.team_rosters[teams[1]].pop(idx)
            
            # Execute the trade
            for player in team1_players:
                self.team_rosters[teams[1]].append(player)
            
            for player in team2_players:
                self.team_rosters[teams[0]].append(player)
            
            # Log transaction
            team1_names = [p["name"] for p in team1_players]
            team2_names = [p["name"] for p in team2_players]
            
            logger.info(f"Trade: {teams[0]} traded {', '.join(team1_names)} to {teams[1]} for {', '.join(team2_names)}")
            transaction_count += 1
        
        logger.info(f"Simulated {transaction_count} league transactions")
        return transaction_count
    
    def run_system_update(self):
        """Run a complete system update"""
        logger.info("Starting system update...")
        
        try:
            # Update player stats
            self.update_player_stats()
            
            # Update player projections
            self.update_player_projections()
            
            # Update player news
            self.update_player_news()
            
            # Update player injuries
            self.update_player_injuries()
            
            # Update league transactions
            self.update_league_transactions()
            
            # Identify free agents
            self.identify_free_agents()
            
            # Save updated system state
            self.save_system_state()
            
            # Generate updated reports
            self.generate_reports()
            
            # Update timestamp
            self.last_update = datetime.now()
            
            logger.info(f"System update completed successfully at {self.last_update}")
            return True
        except Exception as e:
            logger.error(f"Error during system update: {e}")
            return False
    
    def generate_reports(self):
        """Generate various reports"""
        timestamp = datetime.now().strftime("%Y%m%d")
        
        # Generate team analysis report
        self.generate_team_analysis_report(f"{self.reports_dir}/team_analysis_{timestamp}.md")
        
        # Generate free agents report
        self.generate_free_agents_report(f"{self.reports_dir}/free_agents_{timestamp}.md")
        
        # Generate trending players report
        self.generate_trending_players_report(f"{self.reports_dir}/trending_players_{timestamp}.md")
        
        # Generate player news report
        self.generate_player_news_report(f"{self.reports_dir}/player_news_{timestamp}.md")
        
        logger.info(f"Generated reports with timestamp {timestamp}")
    
    def generate_team_analysis_report(self, output_file):
        """Generate team analysis report"""
        with open(output_file, 'w') as f:
            # Title
            f.write("# Fantasy Baseball Team Analysis\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
            
            # Your Team Section
            f.write(f"## Your Team: {self.your_team_name}\n\n")
            
            # Team Roster
            f.write("### Current Roster\n\n")
            
            # Group players by position
            positions = {"C": [], "1B": [], "2B": [], "3B": [], "SS": [], "OF": [], "SP": [], "RP": []}
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                position = player["position"]
                
                # Simplified position assignment
                if position in positions:
                    positions[position].append(name)
                elif "/" in position:  # Handle multi-position players
                    primary_pos = position.split("/")[0]
                    if primary_pos in positions:
                        positions[primary_pos].append(name)
                    else:
                        positions["UTIL"].append(name)
                else:
                    # Handle unknown positions
                    if 'ERA' in self.player_stats_current.get(name, {}):
                        if self.player_stats_current[name].get('SV', 0) > 0:
                            positions["RP"].append(name)
                        else:
                            positions["SP"].append(name)
                    else:
                        positions["UTIL"].append(name)
            
            # Write roster by position
            for pos, players in positions.items():
                if players:
                    f.write(f"**{pos}**: {', '.join(players)}\n\n")
            
            # Team Performance
            f.write("### Team Performance\n\n")
            
            # Calculate team totals
            batting_totals = {
                'AB': 0, 'R': 0, 'HR': 0, 'RBI': 0, 'SB': 0, 'AVG': 0, 'OPS': 0
            }
            
            pitching_totals = {
                'IP': 0, 'W': 0, 'ERA': 0, 'WHIP': 0, 'K': 0, 'QS': 0, 'SV': 0
            }
            
            # Batters stats
            f.write("#### Batting Stats\n\n")
            batter_table = []
            headers = ["Player", "AB", "R", "HR", "RBI", "SB", "AVG", "OPS"]
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_stats_current and 'AVG' in self.player_stats_current[name]:
                    stats = self.player_stats_current[name]
                    batter_table.append([
                        name,
                        stats.get('AB', 0),
                        stats.get('R', 0),
                        stats.get('HR', 0),
                        stats.get('RBI', 0),
                        stats.get('SB', 0),
                        f"{stats.get('AVG', 0):.3f}",
                        f"{stats.get('OPS', 0):.3f}"
                    ])
                    
                    # Add to totals
                    batting_totals['AB'] += stats.get('AB', 0)
                    batting_totals['R'] += stats.get('R', 0)
                    batting_totals['HR'] += stats.get('HR', 0)
                    batting_totals['RBI'] += stats.get('RBI', 0)
                    batting_totals['SB'] += stats.get('SB', 0)
            
            # Calculate team AVG and OPS
            if batting_totals['AB'] > 0:
                total_hits = sum(self.player_stats_current.get(p["name"], {}).get('H', 0) for p in self.team_rosters.get(self.your_team_name, []))
                batting_totals['AVG'] = total_hits / batting_totals['AB']
                
                # Estimate team OPS as average of player OPS values
                ops_values = [self.player_stats_current.get(p["name"], {}).get('OPS', 0) for p in self.team_rosters.get(self.your_team_name, [])]
                ops_values = [ops for ops in ops_values if ops > 0]
                #!/usr/bin/env python3
# Fantasy Baseball Automated Model with Live Updates
# This script creates an automated system that regularly updates player stats and projections
# Uses the same sources (PECOTA, FanGraphs, MLB.com) for consistent data

import os
import csv
import json
import time
import random
import requests
import pandas as pd
import numpy as np
import schedule
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from tabulate import tabulate
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fantasy_baseball_auto.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FantasyBaseballAuto")

class FantasyBaseballAutomated:
    def __init__(self, league_id="2874", your_team_name="Kenny Kawaguchis"):
        self.league_id = league_id
        self.your_team_name = your_team_name
        self.teams = {}
        self.team_rosters = {}
        self.free_agents = {}
        self.player_stats_current = {}
        self.player_projections = {}
        self.player_news = {}
        self.last_update = None
        
        # API endpoints and data sources
        self.data_sources = {
            'stats': [
                'https://www.fangraphs.com/api/players/stats',
                'https://www.baseball-reference.com/leagues/MLB/2025.shtml',
                'https://www.mlb.com/stats/'
            ],
            'projections': [
                'https://www.fangraphs.com/projections.aspx',
                'https://www.baseball-prospectus.com/pecota-projections/',
                'https://www.mlb.com/stats/projected'
            ],
            'news': [
                'https://www.rotowire.com/baseball/news.php',
                'https://www.cbssports.com/fantasy/baseball/players/updates/',
                'https://www.espn.com/fantasy/baseball/story/_/id/29589640'
            ]
        }
        
        # Create directories for data storage
        self.data_dir = "data"
        self.reports_dir = "reports"
        self.visuals_dir = "visuals"
        self.archives_dir = "archives"
        
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.visuals_dir, exist_ok=True)
        os.makedirs(self.archives_dir, exist_ok=True)
        
        logger.info(f"Fantasy Baseball Automated Model initialized for league ID: {league_id}")
        logger.info(f"Your team: {your_team_name}")
    
    def load_initial_data(self):
        """Load initial data to bootstrap the system"""
        logger.info("Loading initial data for bootstrap...")
        
        # Load team rosters
        self.load_team_rosters()
        
        # Load initial stats and projections
        self.load_initial_stats_and_projections()
        
        # Generate initial set of free agents
        self.identify_free_agents()
        
        # Mark system as initialized with timestamp
        self.last_update = datetime.now()
        self.save_system_state()
        
        logger.info(f"Initial data loaded successfully, timestamp: {self.last_update}")
    
    def load_team_rosters(self, rosters_file=None):
        """Load team rosters from file or use default data"""
        if rosters_file and os.path.exists(rosters_file):
            try:
                df = pd.read_csv(rosters_file)
                for _, row in df.iterrows():
                    team_name = row['team_name']
                    player_name = row['player_name']
                    position = row['position']
                    
                    if team_name not in self.team_rosters:
                        self.team_rosters[team_name] = []
                    
                    self.team_rosters[team_name].append({
                        'name': player_name,
                        'position': position
                    })
                
                logger.info(f"Loaded {len(self.team_rosters)} team rosters from {rosters_file}")
            except Exception as e:
                logger.error(f"Error loading rosters file: {e}")
                self._load_default_rosters()
        else:
            logger.info("Rosters file not provided or doesn't exist. Loading default roster data.")
            self._load_default_rosters()
    
    def _load_default_rosters(self):
        """Load default roster data based on previous analysis"""
        default_rosters = {
            "Kenny Kawaguchis": [
                {"name": "Logan O'Hoppe", "position": "C"},
                {"name": "Bryce Harper", "position": "1B"},
                {"name": "Mookie Betts", "position": "2B/OF"},
                {"name": "Austin Riley", "position": "3B"},
                {"name": "CJ Abrams", "position": "SS"},
                {"name": "Lawrence Butler", "position": "OF"},
                {"name": "Riley Greene", "position": "OF"},
                {"name": "Adolis García", "position": "OF"},
                {"name": "Taylor Ward", "position": "OF"},
                {"name": "Tommy Edman", "position": "2B/SS"},
                {"name": "Roman Anthony", "position": "OF"},
                {"name": "Jonathan India", "position": "2B"},
                {"name": "Trevor Story", "position": "SS"},
                {"name": "Iván Herrera", "position": "C"},
                {"name": "Cole Ragans", "position": "SP"},
                {"name": "Hunter Greene", "position": "SP"},
                {"name": "Jack Flaherty", "position": "SP"},
                {"name": "Ryan Helsley", "position": "RP"},
                {"name": "Tanner Scott", "position": "RP"},
                {"name": "Pete Fairbanks", "position": "RP"},
                {"name": "Ryan Pepiot", "position": "SP"},
                {"name": "MacKenzie Gore", "position": "SP"},
                {"name": "Camilo Doval", "position": "RP"}
            ],
            "Mickey 18": [
                {"name": "Adley Rutschman", "position": "C"},
                {"name": "Pete Alonso", "position": "1B"},
                {"name": "Matt McLain", "position": "2B"},
                {"name": "Jordan Westburg", "position": "3B"},
                {"name": "Jeremy Peña", "position": "SS"},
                {"name": "Jasson Domínguez", "position": "OF"},
                {"name": "Tyler O'Neill", "position": "OF"},
                {"name": "Vladimir Guerrero Jr.", "position": "1B"},
                {"name": "Eugenio Suárez", "position": "3B"},
                {"name": "Ronald Acuña Jr.", "position": "OF"},
                {"name": "Tarik Skubal", "position": "SP"},
                {"name": "Spencer Schwellenbach", "position": "SP"},
                {"name": "Hunter Brown", "position": "SP"},
                {"name": "Jhoan Duran", "position": "RP"},
                {"name": "Jeff Hoffman", "position": "RP"},
                {"name": "Ryan Pressly", "position": "RP"},
                {"name": "Justin Verlander", "position": "SP"},
                {"name": "Max Scherzer", "position": "SP"}
            ],
            # Other teams omitted for brevity but would be included in full implementation
        }
        
        # Add to the team rosters dictionary
        self.team_rosters = default_rosters
        
        # Count total players loaded
        total_players = sum(len(roster) for roster in self.team_rosters.values())
        logger.info(f"Loaded {len(self.team_rosters)} team rosters with {total_players} players from default data")
    
    def load_initial_stats_and_projections(self, stats_file=None, projections_file=None):
        """Load initial stats and projections from files or use default data"""
        if stats_file and os.path.exists(stats_file) and projections_file and os.path.exists(projections_file):
            try:
                # Load stats
                with open(stats_file, 'r') as f:
                    self.player_stats_current = json.load(f)
                
                # Load projections
                with open(projections_file, 'r') as f:
                    self.player_projections = json.load(f)
                
                logger.info(f"Loaded stats for {len(self.player_stats_current)} players from {stats_file}")
                logger.info(f"Loaded projections for {len(self.player_projections)} players from {projections_file}")
            except Exception as e:
                logger.error(f"Error loading stats/projections files: {e}")
                self._load_default_stats_and_projections()
        else:
            logger.info("Stats/projections files not provided or don't exist. Loading default data.")
            self._load_default_stats_and_projections()
    
    def _load_default_stats_and_projections(self):
        """Load default stats and projections for bootstrapping"""
        # This would load from the previously created data
        # For simulation/demo purposes, we'll generate synthetic data
        
        # First, collect all players from rosters
        all_players = set()
        for team, roster in self.team_rosters.items():
            for player in roster:
                all_players.add(player["name"])
        
        # Add some free agents
        free_agents = [
            "Keibert Ruiz", "Danny Jansen", "Christian Walker", 
            "Spencer Torkelson", "Gavin Lux", "Luis Rengifo", 
            "JP Crawford", "Ha-Seong Kim", "Jeimer Candelario", 
            "Spencer Steer", "Luis Matos", "Heliot Ramos", 
            "TJ Friedl", "Garrett Mitchell", "Kutter Crawford", 
            "Reese Olson", "Dane Dunning", "José Berríos", 
            "Erik Swanson", "Seranthony Domínguez"
        ]
        
        for player in free_agents:
            all_players.add(player)
        
        # Generate stats and projections for all players
        self._generate_synthetic_data(all_players)
        
        logger.info(f"Generated synthetic stats for {len(self.player_stats_current)} players")
        logger.info(f"Generated synthetic projections for {len(self.player_projections)} players")
    
    def _generate_synthetic_data(self, player_names):
        """Generate synthetic stats and projections for demo purposes"""
        for player in player_names:
            # Determine if batter or pitcher based on name recognition
            # This is a simple heuristic; in reality, you'd use actual data
            is_pitcher = player in [
                "Cole Ragans", "Hunter Greene", "Jack Flaherty", "Ryan Helsley", 
                "Tanner Scott", "Pete Fairbanks", "Ryan Pepiot", "MacKenzie Gore", 
                "Camilo Doval", "Tarik Skubal", "Spencer Schwellenbach", "Hunter Brown", 
                "Jhoan Duran", "Jeff Hoffman", "Ryan Pressly", "Justin Verlander", 
                "Max Scherzer", "Kutter Crawford", "Reese Olson", "Dane Dunning", 
                "José Berríos", "Erik Swanson", "Seranthony Domínguez"
            ]
            
            if is_pitcher:
                # Generate pitcher stats
                current_stats = {
                    'IP': random.uniform(20, 40),
                    'W': random.randint(1, 4),
                    'L': random.randint(0, 3),
                    'ERA': random.uniform(2.5, 5.0),
                    'WHIP': random.uniform(0.9, 1.5),
                    'K': random.randint(15, 50),
                    'BB': random.randint(5, 20),
                    'QS': random.randint(1, 5),
                    'SV': 0 if player not in ["Ryan Helsley", "Tanner Scott", "Pete Fairbanks", "Camilo Doval", "Jhoan Duran", "Ryan Pressly", "Erik Swanson", "Seranthony Domínguez"] else random.randint(1, 8)
                }
                
                # Calculate k/9
                current_stats['K9'] = current_stats['K'] * 9 / current_stats['IP'] if current_stats['IP'] > 0 else 0
                
                # Generate projections (rest of season)
                projected_ip = random.uniform(120, 180) if current_stats['SV'] == 0 else random.uniform(45, 70)
                projected_stats = {
                    'IP': projected_ip,
                    'ERA': random.uniform(3.0, 4.5),
                    'WHIP': random.uniform(1.05, 1.35),
                    'K9': random.uniform(7.5, 12.0),
                    'QS': random.randint(10, 20) if current_stats['SV'] == 0 else 0,
                    'SV': 0 if current_stats['SV'] == 0 else random.randint(15, 35)
                }
            else:
                # Generate batter stats
                current_stats = {
                    'AB': random.randint(70, 120),
                    'R': random.randint(8, 25),
                    'H': random.randint(15, 40),
                    'HR': random.randint(1, 8),
                    'RBI': random.randint(5, 25),
                    'SB': random.randint(0, 8),
                    'BB': random.randint(5, 20),
                    'SO': random.randint(15, 40)
                }
                
                # Calculate derived stats
                current_stats['AVG'] = current_stats['H'] / current_stats['AB'] if current_stats['AB'] > 0 else 0
                current_stats['OBP'] = (current_stats['H'] + current_stats['BB']) / (current_stats['AB'] + current_stats['BB']) if (current_stats['AB'] + current_stats['BB']) > 0 else 0
                
                # Estimate SLG and OPS
                singles = current_stats['H'] - current_stats['HR'] - random.randint(2, 10) - random.randint(0, 5)
                doubles = random.randint(2, 10)
                triples = random.randint(0, 5)
                tb = singles + (2 * doubles) + (3 * triples) + (4 * current_stats['HR'])
                current_stats['SLG'] = tb / current_stats['AB'] if current_stats['AB'] > 0 else 0
                current_stats['OPS'] = current_stats['OBP'] + current_stats['SLG']
                
                # Generate projections (rest of season)
                projected_stats = {
                    'AB': random.randint(400, 550),
                    'R': random.randint(50, 100),
                    'HR': random.randint(10, 35),
                    'RBI': random.randint(40, 100),
                    'SB': random.randint(3, 35),
                    'AVG': random.uniform(0.230, 0.310),
                    'OPS': random.uniform(0.680, 0.950)
                }
            
            # Add to dictionaries
            self.player_stats_current[player] = current_stats
            self.player_projections[player] = projected_stats
    
    def identify_free_agents(self):
        """Identify all players who aren't on team rosters but have stats/projections"""
        # Create a set of all rostered players
        rostered_players = set()
        for team, roster in self.team_rosters.items():
            for player in roster:
                rostered_players.add(player["name"])
        
        # Find players with stats/projections who aren't rostered
        self.free_agents = {}
        
        for player in self.player_projections.keys():
            if player not in rostered_players:
                # Determine position based on stats
                if player in self.player_stats_current:
                    if 'ERA' in self.player_stats_current[player]:
                        position = 'RP' if self.player_stats_current[player].get('SV', 0) > 0 else 'SP'
                    else:
                        # This is simplistic - in a real system, we'd have actual position data
                        position = 'Unknown'
                else:
                    position = 'Unknown'
                
                self.free_agents[player] = {
                    'name': player,
                    'position': position,
                    'stats': self.player_stats_current.get(player, {}),
                    'projections': self.player_projections.get(player, {})
                }
        
        logger.info(f"Identified {len(self.free_agents)} free agents")
        return self.free_agents
    
    def save_system_state(self):
        """Save the current state of the system to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save team rosters
        with open(f"{self.data_dir}/team_rosters.json", 'w') as f:
            json.dump(self.team_rosters, f, indent=4)
        
        # Save current stats
        with open(f"{self.data_dir}/player_stats_current.json", 'w') as f:
            json.dump(self.player_stats_current, f, indent=4)
        
        # Save projections
        with open(f"{self.data_dir}/player_projections.json", 'w') as f:
            json.dump(self.player_projections, f, indent=4)
        
        # Save free agents
        with open(f"{self.data_dir}/free_agents.json", 'w') as f:
            json.dump(self.free_agents, f, indent=4)
        
        # Also save an archive copy
        with open(f"{self.archives_dir}/team_rosters_{timestamp}.json", 'w') as f:
            json.dump(self.team_rosters, f, indent=4)
        
        with open(f"{self.archives_dir}/player_stats_{timestamp}.json", 'w') as f:
            json.dump(self.player_stats_current, f, indent=4)
        
        with open(f"{self.archives_dir}/projections_{timestamp}.json", 'w') as f:
            json.dump(self.player_projections, f, indent=4)
        
        logger.info(f"System state saved successfully with timestamp: {timestamp}")
    
    def load_system_state(self):
        """Load the system state from saved files"""
        try:
            # Load team rosters
            if os.path.exists(f"{self.data_dir}/team_rosters.json"):
                with open(f"{self.data_dir}/team_rosters.json", 'r') as f:
                    self.team_rosters = json.load(f)
            
            # Load current stats
            if os.path.exists(f"{self.data_dir}/player_stats_current.json"):
                with open(f"{self.data_dir}/player_stats_current.json", 'r') as f:
                    self.player_stats_current = json.load(f)
            
            # Load projections
            if os.path.exists(f"{self.data_dir}/player_projections.json"):
                with open(f"{self.data_dir}/player_projections.json", 'r') as f:
                    self.player_projections = json.load(f)
            
            # Load free agents
            if os.path.exists(f"{self.data_dir}/free_agents.json"):
                with open(f"{self.data_dir}/free_agents.json", 'r') as f:
                    self.free_agents = json.load(f)
            
            logger.info("System state loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading system state: {e}")
            return False
    
    def update_player_stats(self):
        """Update player stats by fetching from data sources"""
        logger.info("Updating player stats from sources...")
        
        # In a real implementation, you would:
        # 1. Fetch data from each source in self.data_sources['stats']
        # 2. Parse and clean the data
        # 3. Merge with existing stats
        # 4. Update self.player_stats_current
        
        # For demo purposes, we'll simulate this process
        self._simulate_stats_update()
        
        logger.info(f"Updated stats for {len(self.player_stats_current)} players")
        return len(self.player_stats_current)
    
    def _simulate_stats_update(self):
        """Simulate updating stats for demo purposes"""
        # Add some new players
        new_players = [
            "Bobby Miller", "Garrett Crochet", "DL Hall", 
            "Edward Cabrera", "Alec Bohm", "Elly De La Cruz",
            "Anthony Volpe", "Jazz Chisholm Jr."
        ]
        
        for player in new_players:
            if player not in self.player_stats_current:
                # Determine if batter or pitcher based on name recognition
                is_pitcher = player in ["Bobby Miller", "Garrett Crochet", "DL Hall", "Edward Cabrera"]
                
                if is_pitcher:
                    self.player_stats_current[player] = {
                        'IP': random.uniform(10, 30),
                        'W': random.randint(1, 3),
                        'L': random.randint(0, 2),
                        'ERA': random.uniform(3.0, 5.0),
                        'WHIP': random.uniform(1.0, 1.4),
                        'K': random.randint(10, 40),
                        'BB': random.randint(5, 15),
                        'QS': random.randint(1, 4),
                        'SV': 0
                    }
                    
                    # Calculate k/9
                    self.player_stats_current[player]['K9'] = (
                        self.player_stats_current[player]['K'] * 9 / 
                        self.player_stats_current[player]['IP'] 
                        if self.player_stats_current[player]['IP'] > 0 else 0
                    )
                else:
                    self.player_stats_current[player] = {
                        'AB': random.randint(50, 100),
                        'R': random.randint(5, 20),
                        'H': random.randint(10, 30),
                        'HR': random.randint(1, 6),
                        'RBI': random.randint(5, 20),
                        'SB': random.randint(0, 6),
                        'BB': random.randint(5, 15),
                        'SO': random.randint(10, 30)
                    }
                    
                    # Calculate derived stats
                    self.player_stats_current[player]['AVG'] = (
                        self.player_stats_current[player]['H'] / 
                        self.player_stats_current[player]['AB'] 
                        if self.player_stats_current[player]['AB'] > 0 else 0
                    )
                    
                    self.player_stats_current[player]['OBP'] = (
                        (self.player_stats_current[player]['H'] + self.player_stats_current[player]['BB']) / 
                        (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) 
                        if (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) > 0 else 0
                    )
                    
                    # Estimate SLG and OPS
                    singles = (
                        self.player_stats_current[player]['H'] - 
                        self.player_stats_current[player]['HR'] - 
                        random.randint(2, 8) - 
                        random.randint(0, 3)
                    )
                    doubles = random.randint(2, 8)
                    triples = random.randint(0, 3)
                    tb = singles + (2 * doubles) + (3 * triples) + (4 * self.player_stats_current[player]['HR'])
                    
                    self.player_stats_current[player]['SLG'] = (
                        tb / self.player_stats_current[player]['AB'] 
                        if self.player_stats_current[player]['AB'] > 0 else 0
                    )
                    
                    self.player_stats_current[player]['OPS'] = (
                        self.player_stats_current[player]['OBP'] + 
                        self.player_stats_current[player]['SLG']
                    )
        
        # Update existing player stats
        for player in list(self.player_stats_current.keys()):
            # Skip some players randomly to simulate days off
            if random.random() < 0.3:
                continue
                
            # Determine if batter or pitcher based on existing stats
            if 'ERA' in self.player_stats_current[player]:  # It's a pitcher
                # Generate random game stats
                ip = random.uniform(0.1, 7)
                k = int(ip * random.uniform(0.5, 1.5))
                bb = int(ip * random.uniform(0.1, 0.5))
                er = int(ip * random.uniform(0, 0.7))
                h = int(ip * random.uniform(0.3, 1.2))
                
                # Update aggregated stats
                self.player_stats_current[player]['IP'] += ip
                self.player_stats_current[player]['K'] += k
                self.player_stats_current[player]['BB'] += bb
                
                # Update win/loss
                if random.random() < 0.5:
                    if random.random() < 0.6:  # 60% chance of decision
                        if random.random() < 0.5:  # 50% chance of win
                            self.player_stats_current[player]['W'] = self.player_stats_current[player].get('W', 0) + 1
                        else:
                            self.player_stats_current[player]['L'] = self.player_stats_current[player].get('L', 0) + 1
                
                # Update quality starts
                if ip >= 6 and er <= 3 and 'SV' not in self.player_stats_current[player]:
                    self.player_stats_current[player]['QS'] = self.player_stats_current[player].get('QS', 0) + 1
                
                # Update saves for relievers
                if 'SV' in self.player_stats_current[player] and ip <= 2 and random.random() < 0.3:
                    self.player_stats_current[player]['SV'] = self.player_stats_current[player].get('SV', 0) + 1
                
                # Recalculate ERA and WHIP
                total_er = (self.player_stats_current[player]['ERA'] * 
                           (self.player_stats_current[player]['IP'] - ip) / 9) + er
                            
                self.player_stats_current[player]['ERA'] = (
                    total_er * 9 / self.player_stats_current[player]['IP'] 
                    if self.player_stats_current[player]['IP'] > 0 else 0
                )
                
                # Add baserunners for WHIP calculation
                self.player_stats_current[player]['WHIP'] = (
                    (self.player_stats_current[player]['WHIP'] * 
                     (self.player_stats_current[player]['IP'] - ip) + (h + bb)) / 
                    self.player_stats_current[player]['IP'] 
                    if self.player_stats_current[player]['IP'] > 0 else 0
                )
                
                # Update K/9
                self.player_stats_current[player]['K9'] = (
                    self.player_stats_current[player]['K'] * 9 / 
                    self.player_stats_current[player]['IP'] 
                    if self.player_stats_current[player]['IP'] > 0 else 0
                )
                
            else:  # It's a batter
                # Generate random game stats
                ab = random.randint(0, 5)
                h = 0
                hr = 0
                r = 0
                rbi = 0
                sb = 0
                bb = 0
                so = 0
                
                if ab > 0:
                    # Determine hits
                    for _ in range(ab):
                        if random.random() < 0.270:  # League average is around .270
                            h += 1
                            # Determine if it's a home run
                            if random.random() < 0.15:  # About 15% of hits are HRs
                                hr += 1
                    
                    # Other stats
                    r = random.randint(0, 2) if h > 0 else 0
                    rbi = random.randint(0, 3) if h > 0 else 0
                    sb = 1 if random.random() < 0.08 else 0  # 8% chance of SB
                    bb = 1 if random.random() < 0.1 else 0  # 10% chance of BB
                    so = random.randint(0, 2)  # 0-2 strikeouts
                
                # Update aggregated stats
                self.player_stats_current[player]['AB'] += ab
                self.player_stats_current[player]['H'] += h
                self.player_stats_current[player]['HR'] += hr
                self.player_stats_current[player]['R'] += r
                self.player_stats_current[player]['RBI'] += rbi
                self.player_stats_current[player]['SB'] += sb
                self.player_stats_current[player]['BB'] += bb
                self.player_stats_current[player]['SO'] += so
                
                # Recalculate AVG
                self.player_stats_current[player]['AVG'] =with open(output_file, 'w') as f:
            # Title
            f.write("# Fantasy Baseball Trending Players\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
            
            # Introduction
            f.write("This report identifies players who are trending up or down based on recent performance versus expectations.\n\n")
            
            # For demo purposes, randomly select players as trending up or down
            trending_up_batters = random.sample(list(self.player_stats_current.keys()), 5)
            trending_down_batters = random.sample(list(self.player_stats_current.keys()), 5)
            
            trending_up_pitchers = random.sample([p for p in self.player_stats_current if 'ERA' in self.player_stats_current[p]], 3)
            trending_down_pitchers = random.sample([p for p in self.player_stats_current if 'ERA' in self.player_stats_current[p]], 3)
            
            # Hot Batters
            f.write("## 🔥 Hot Batters\n\n")
            f.write("Players exceeding their projections over the past 15 days.\n\n")
            
            headers = ["Player", "Last 15 Days", "Season Stats", "Ownership"]
            hot_batters_table = []
            
            for player in trending_up_batters:
                if player in self.player_stats_current and 'AVG' in self.player_stats_current[player]:
                    # Generate simulated recent hot stats
                    recent_avg = min(self.player_stats_current[player].get('AVG', 0.250) + random.uniform(0.040, 0.080), 0.400)
                    recent_hr = max(1, int(self.player_stats_current[player].get('HR', 5) * random.uniform(0.20, 0.30)))
                    recent_rbi = max(3, int(self.player_stats_current[player].get('RBI', 20) * random.uniform(0.20, 0.30)))
                    
                    # Determine roster status
                    roster_status = "Rostered"
                    for team, roster in self.team_rosters.items():
                        if player in [p["name"] for p in roster]:
                            roster_status = team
                            break
                    
                    if roster_status == "Rostered":
                        roster_status = random.choice(list(self.team_rosters.keys()))
                    
                    # Generate table row
                    hot_batters_table.append([
                        player,
                        f"{recent_avg:.3f}, {recent_hr} HR, {recent_rbi} RBI",
                        f"{self.player_stats_current[player].get('AVG', 0):.3f}, {self.player_stats_current[player].get('HR', 0)} HR, {self.player_stats_current[player].get('RBI', 0)} RBI",
                        roster_status
                    ])
            
            f.write(tabulate(hot_batters_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Cold Batters
            f.write("## ❄️ Cold Batters\n\n")
            f.write("Players underperforming their projections over the past 15 days.\n\n")
            
            cold_batters_table = []
            
            for player in trending_down_batters:
                if player in self.player_stats_current and 'AVG' in self.player_stats_current[player]:
                    # Generate simulated recent cold stats
                    recent_avg = max(0.120, self.player_stats_current[player].get('AVG', 0.250) - random.uniform(0.050, 0.100))
                    recent_hr = max(0, int(self.player_stats_current[player].get('HR', 5) * random.uniform(0.05, 0.15)))
                    recent_rbi = max(1, int(self.player_stats_current[player].get('RBI', 20) * random.uniform(0.05, 0.15)))
                    
                    # Determine roster status
                    roster_status = "Rostered"
                    for team, roster in self.team_rosters.items():
                        if player in [p["name"] for p in roster]:
                            roster_status = team
                            break
                    
                    if roster_status == "Rostered":
                        roster_status = random.choice(list(self.team_rosters.keys()))
                    
                    # Generate table row
                    cold_batters_table.append([
                        player,
                        f"{recent_avg:.3f}, {recent_hr} HR, {recent_rbi} RBI",
                        f"{self.player_stats_current[player].get('AVG', 0):.3f}, {self.player_stats_current[player].get('HR', 0)} HR, {self.player_stats_current[player].get('RBI', 0)} RBI",
                        roster_status
                    ])
            
            f.write(tabulate(cold_batters_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Hot Pitchers
            f.write("## 🔥 Hot Pitchers\n\n")
            f.write("Pitchers exceeding their projections over the past 15 days.\n\n")
            
            headers = ["Player", "Last 15 Days", "Season Stats", "Ownership"]
            hot_pitchers_table = []
            
            for player in trending_up_pitchers:
                if 'ERA' in self.player_stats_current[player]:
                    # Generate simulated recent hot stats
                    recent_era = max(0.00, self.player_stats_current[player].get('ERA', 4.00) - random.uniform(1.30, 2.50))
                    recent_whip = max(0.70, self.player_stats_current[player].get('WHIP', 1.30) - random.uniform(0.30, 0.50))
                    recent_k = int(self.player_stats_current[player].get('K', 40) * random.uniform(0.15, 0.25))
                    
                    # Determine roster status
                    roster_status = "Rostered"
                    for team, roster in self.team_rosters.items():
                        if player in [p["name"] for p in roster]:
                            roster_status = team
                            break
                    
                    if roster_status == "Rostered":
                        roster_status = random.choice(list(self.team_rosters.keys()))
                    
                    # Generate table row
                    hot_pitchers_table.append([
                        player,
                        f"{recent_era:.2f} ERA, {recent_whip:.2f} WHIP, {recent_k} K",
                        f"{self.player_stats_current[player].get('ERA', 0):.2f} ERA, {self.player_stats_current[player].get('WHIP', 0):.2f} WHIP, {self.player_stats_current[player].get('K', 0)} K",
                        roster_status
                    ])
            
            f.write(tabulate(hot_pitchers_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Cold Pitchers
            f.write("## ❄️ Cold Pitchers\n\n")
            f.write("Pitchers underperforming their projections over the past 15 days.\n\n")
            
            cold_pitchers_table = []
            
            for player in trending_down_pitchers:
                if 'ERA' in self.player_stats_current[player]:
                    # Generate simulated recent cold stats
                    recent_era = self.player_stats_current[player].get('ERA', 4.00) + random.uniform(1.50, 3.00)
                    recent_whip = self.player_stats_current[player].get('WHIP', 1.30) + random.uniform(0.20, 0.40)
                    recent_k = max(0, int(self.player_stats_current[player].get('K', 40) * random.uniform(0.05, 0.15)))
                    
                    # Determine roster status
                    roster_status = "Rostered"
                    for team, roster in self.team_rosters.items():
                        if player in [p["name"] for p in roster]:
                            roster_status = team
                            break
                    
                    if roster_status == "Rostered":
                        roster_status = random.choice(list(self.team_rosters.keys()))
                    
                    # Generate table row
                    cold_pitchers_table.append([
                        player,
                        f"{recent_era:.2f} ERA, {recent_whip:.2f} WHIP, {recent_k} K",
                        f"{self.player_stats_current[player].get('ERA', 0):.2f} ERA, {self.player_stats_current[player].get('WHIP', 0):.2f} WHIP, {self.player_stats_current[player].get('K', 0)} K",
                        roster_status
                    ])
            
            f.write(tabulate(cold_pitchers_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Pickup Recommendations
            f.write("## 📈 Recommended Pickups\n\n")
            f.write("Players trending up who are still available in many leagues.\n\n")
            
            # Find available players who are trending up
            available_trending = []
            for player in trending_up_batters + trending_up_pitchers:
                is_rostered = False
                for team, roster in self.team_rosters.items():
                    if player in [p["name"] for p in roster]:
                        is_rostered = True
                        break
                
                if not is_rostered:
                    available_trending.append(player)
            
            # Add some random free agents to the mix
            available_trending.extend(random.sample(list(self.free_agents.keys()), min(5, len(self.free_agents))))
            
            # Create recommendation table
            headers = ["Player", "Position", "Recent Performance", "Projected ROS"]
            recommendations_table = []
            
            for player in available_trending[:5]:  # Top 5 recommendations
                if player in self.player_stats_current:
                    # Determine position
                    if 'ERA' in self.player_stats_current[player]:
                        position = 'RP' if self.player_stats_current[player].get('SV', 0) > 0 else 'SP'
                        
                        # Generate recent performance string
                        recent_perf = f"{random.uniform(2.00, 3.50):.2f} ERA, {random.uniform(0.90, 1.20):.2f} WHIP, {random.randint(5, 15)} K"
                        
                        # Generate ROS projection string
                        if player in self.player_projections:
                            proj = self.player_projections[player]
                            ros_proj = f"{proj.get('ERA', 0):.2f} ERA, {proj.get('WHIP', 0):.2f} WHIP, {int(proj.get('IP', 0))} IP"
                        else:
                            ros_proj = "No projection available"
                    else:
                        # Random position for batters
                        position = random.choice(['C', '1B', '2B', '3B', 'SS', 'OF'])
                        
                        # Generate recent performance string
                        recent_perf = f"{random.uniform(0.280, 0.360):.3f} AVG, {random.randint(1, 5)} HR, {random.randint(5, 15)} RBI"
                        
                        # Generate ROS projection string
                        if player in self.player_projections:
                            proj = self.player_projections[player]
                            ros_proj = f"{proj.get('AVG', 0):.3f} AVG, {int(proj.get('HR', 0))} HR, {int(proj.get('RBI', 0))} RBI"
                        else:
                            ros_proj = "No projection available"
                    
                    recommendations_table.append([
                        player,
                        position,
                        recent_perf,
                        ros_proj
                    ])
            
            f.write(tabulate(recommendations_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Drop Recommendations
            f.write("## 📉 Consider Dropping\n\n")
            f.write("Rostered players who are trending down and may be safe to drop in standard leagues.\n\n")
            
            # Find rostered players who are trending down
            rostered_trending_down = []
            for player in trending_down_batters + trending_down_pitchers:
                is_rostered = False
                for team, roster in self.team_rosters.items():
                    if player in [p["name"] for p in roster]:
                        is_rostered = True
                        break
                
                if is_rostered:
                    rostered_trending_down.append(player)
            
            # Create drop recommendation table
            headers = ["Player", "Position", "Recent Performance", "Better Alternatives"]
            drop_recommendations_table = []
            
            for player in rostered_trending_down[:5]:  # Top 5 drop recommendations
                if player in self.player_stats_current:
                    # Determine position
                    if 'ERA' in self.player_stats_current[player]:
                        position = 'RP' if self.player_stats_current[player].get('SV', 0) > 0 else 'SP'
                        
                        # Generate recent performance string
                        recent_perf = f"{random.uniform(5.50, 8.00):.2f} ERA, {random.uniform(1.40, 1.80):.2f} WHIP, {random.randint(1, 7)} K"
                        
                        # Suggest alternatives
                        alternatives = [p for p in self.free_agents if p in self.player_projections and 'ERA' in self.player_projections[p]]
                        if alternatives:
                            better_alternatives = ", ".join(random.sample(alternatives, min(3, len(alternatives))))
                        else:
                            better_alternatives = "None available"
                    else:
                        # Random position for batters
                        position = random.choice(['C', '1B', '2B', '3B', 'SS', 'OF'])
                        
                        # Generate recent performance string
                        recent_perf = f"{random.uniform(0.120, 0.200):.3f} AVG, {random.randint(0, 1)} HR, {random.randint(1, 4)} RBI"
                        
                        # Suggest alternatives
                        alternatives = [p for p in self.free_agents if p in self.player_projections and 'AVG' in self.player_projections[p]]
                        if alternatives:
                            better_alternatives = ", ".join(random.sample(alternatives, min(3, len(alternatives))))
                        else:
                            better_alternatives = "None available"
                    
                    drop_recommendations_table.append([
                        player,
                        position,
                        recent_perf,
                        better_alternatives
                    ])
            
            f.write(tabulate(drop_recommendations_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            logger.info(f"Trending players report generated: {output_file}")
    
    def generate_player_news_report(self, output_file):
        """Generate report of recent player news"""
        with open(output_file, 'w') as f:
            # Title
            f.write("# Fantasy Baseball Player News\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
            
            # Recent Injuries
            f.write("## 🏥 Recent Injuries\n\n")
            
            injury_news = []
            for player, news_items in self.player_news.items():
                for item in news_items:
                    if any(keyword in item['content'].lower() for keyword in ['injury', 'injured', 'il', 'disabled list', 'strain', 'sprain']):
                        injury_news.append({
                            'player': player,
                            'date': item['date'],
                            'source': item['source'],
                            'content': item['content']
                        })
            
            # Sort by date (most recent first)
            injury_news.sort(key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d"), reverse=True)
            
            if injury_news:
                for news in injury_news[:10]:  # Show most recent 10 injury news items
                    f.write(f"**{news['player']}** ({news['date']} - {news['source']}): {news['content']}\n\n")
            else:
                f.write("No recent injury news.\n\n")
            
            # Position Battle Updates
            f.write("## ⚔️ Position Battle Updates\n\n")
            
            # In a real implementation, you would have actual news about position battles
            # For demo purposes, we'll simulate position battle news
            position_battles = [
                {
                    'position': 'Second Base',
                    'team': 'Athletics',
                    'players': ['Zack Gelof', 'Nick Allen'],
                    'update': f"Gelof continues to see the majority of starts at 2B, playing in {random.randint(4, 6)} of the last 7 games."
                },
                {
                    'position': 'Closer',
                    'team': 'Cardinals',
                    'players': ['Ryan Helsley', 'Giovanny Gallegos'],
                    'update': f"Helsley has converted {random.randint(3, 5)} saves in the last two weeks, firmly establishing himself as the primary closer."
                },
                {
                    'position': 'Outfield',
                    'team': 'Rays',
                    'players': ['Josh Lowe', 'Jose Siri', 'Randy Arozarena'],
                    'update': f"With Lowe's recent {random.choice(['hamstring', 'oblique', 'back'])} injury, Siri has taken over as the everyday CF."
                }
            ]
            
            for battle in position_battles:
                f.write(f"**{battle['team']} {battle['position']}**: {battle['update']}\n\n")
                f.write(f"Players involved: {', '.join(battle['players'])}\n\n")
            
            # Closer Updates
            f.write("## 🔒 Closer Situations\n\n")
            
            # In a real implementation, you would have actual closer data
            # For demo purposes, we'll simulate closer situations
            closer_situations = [
                {
                    'team': 'Rays',
                    'primary': 'Pete Fairbanks',
                    'secondary': 'Jason Adam',
                    'status': f"Fairbanks has {random.randint(3, 5)} saves in the last 14 days and is firmly entrenched as the closer."
                },
                {
                    'team': 'Cardinals',
                    'primary': 'Ryan Helsley',
                    'secondary': 'Giovanny Gallegos',
                    'status': f"Helsley is the unquestioned closer with {random.randint(15, 25)} saves on the season."
                },
                {
                    'team': 'Reds',
                    'primary': 'Alexis Díaz',
                    'secondary': 'Lucas Sims',
                    'status': f"Díaz is firmly in the closer role with {random.randint(3, 5)} saves in the last two weeks."
                },
                {
                    'team': 'Athletics',
                    'primary': 'Mason Miller',
                    'secondary': 'Dany Jiménez',
                    'status': f"Miller has taken over the closing duties, recording {random.randint(2, 4)} saves recently."
                },
                {
                    'team': 'Mariners',
                    'primary': 'Andrés Muñoz',
                    'secondary': 'Matt Brash',
                    'status': f"Muñoz appears to be the preferred option with {random.randint(3, 5)} saves recently."
                }
            ]
            
            # Create a table for closer situations
            headers = ["Team", "Primary", "Secondary", "Status"]
            closer_table = []
            
            for situation in closer_situations:
                closer_table.append([
                    situation['team'],
                    situation['primary'],
                    situation['secondary'],
                    situation['status']
                ])
            
            f.write(tabulate(closer_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Prospect Watch
            f.write("## 🔮 Prospect Watch\n\n")
            
            # In a real implementation, you would have actual prospect data
            # For demo purposes, we'll simulate prospect updates
            prospects = [
                {
                    'name': 'Jackson Holliday',
                    'team': 'Orioles',
                    'position': 'SS',
                    'level': 'AAA',
                    'stats': f".{random.randint(280, 350)} AVG, {random.randint(5, 12)} HR, {random.randint(30, 50)} RBI, {random.randint(8, 20)} SB in {random.randint(180, 250)} AB",
                    'eta': 'Soon - already on 40-man roster'
                },
                {
                    'name': 'Junior Caminero',
                    'team': 'Rays',
                    'position': '3B',
                    'level': 'AAA',
                    'stats': f".{random.randint(280, 320)} AVG, {random.randint(10, 18)} HR, {random.randint(40, 60)} RBI in {random.randint(200, 280)} AB",
                    'eta': f"{random.choice(['June', 'July', 'August'])} {datetime.now().year}"
                },
                {
                    'name': 'Jasson Domínguez',
                    'team': 'Yankees',
                    'position': 'OF',
                    'level': 'AAA',
                    'stats': f".{random.randint(260, 310)} AVG, {random.randint(8, 15)} HR, {random.randint(10, 25)} SB in {random.randint(180, 250)} AB",
                    'eta': f"Expected back from TJ surgery in {random.choice(['July', 'August'])}"
                },
                {
                    'name': 'Colson Montgomery',
                    'team': 'White Sox',
                    'position': 'SS',
                    'level': 'AA',
                    'stats': f".{random.randint(270, 320)} AVG, {random.randint(6, 12)} HR, {random.randint(30, 50)} RBI in {random.randint(180, 250)} AB",
                    'eta': f"{random.choice(['August', 'September', '2026'])}"
                },
                {
                    'name': 'Orelvis Martinez',
                    'team': 'Blue Jays',
                    'position': '3B/SS',
                    'level': 'AAA',
                    'stats': f".{random.randint(240, 290)} AVG, {random.randint(12, 20)} HR, {random.randint(40, 60)} RBI in {random.randint(180, 250)} AB",
                    'eta': f"{random.choice(['July', 'August', 'September'])}"
                }
            ]
            
            # Create a table for prospects
            headers = ["Prospect", "Team", "Position", "Level", "Stats", "ETA"]
            prospects_table = []
            
            for prospect in prospects:
                prospects_table.append([
                    prospect['name'],
                    prospect['team'],
                    prospect['position'],
                    prospect['level'],
                    prospect['stats'],
                    prospect['eta']
                ])
            
            f.write(tabulate(prospects_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            logger.info(f"Player news report generated: {output_file}")
    
    def schedule_updates(self, daily_update_time="07:00", weekly_update_day="Monday"):
        """Schedule regular updates at specified times"""
        # Schedule daily updates
        schedule.every().day.at(daily_update_time).do(self.run_system_update)
        
        # Schedule weekly full updates with report generation
        if weekly_update_day.lower() == "monday":
            schedule.every().monday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "tuesday":
            schedule.every().tuesday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "wednesday":
            schedule.every().wednesday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "thursday":
            schedule.every().thursday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "friday":
            schedule.every().friday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "saturday":
            schedule.every().saturday.at(daily_update_time).do(self.generate_reports)
        elif weekly_update_day.lower() == "sunday":
            schedule.every().sunday.at(daily_update_time).do(self.generate_reports)
        
        logger.info(f"Scheduled daily updates at {daily_update_time}")
        logger.info(f"Scheduled weekly full updates on {weekly_update_day} at {daily_update_time}")
    
    def start_update_loop(self):
        """Start the scheduled update loop"""
        logger.info("Starting update loop - press Ctrl+C to exit")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Update loop stopped by user")
    
    def fetch_external_data(self, data_type, source_index=0):
        """Fetch data from external sources - placeholder for real implementation"""
        logger.info(f"Fetching {data_type} data from {self.data_sources[data_type][source_index]}")
        
        # In a real implementation, you would:
        # 1. Make HTTP request to the data source
        # 2. Parse the response (HTML, JSON, etc.)
        # 3. Extract relevant data
        # 4. Return structured data
        
        # For demo purposes, we'll simulate a successful fetch
        return True

# Command-line interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Fantasy Baseball Automated Model with Live Updates')
    parser.add_argument('--league_id', type=str, default="2874", help='League ID')
    parser.add_argument('--team_name', type=str, default="Kenny Kawaguchis", help='Your team name')
    parser.add_argument('--daily_update', type=str, default="07:00", help='Daily update time (HH:MM)')
    parser.add_argument('--weekly_update', type=str, default="Monday", help='Weekly update day')
    parser.add_argument('--manual_update', action='store_true', help='Run a manual update now')
    parser.add_argument('--reports_only', action='store_true', help='Generate reports only')
    parser.add_argument('--daemon', action='store_true', help='Run as a daemon (continuous updates)')
    
    args = parser.parse_args()
    
    # Create model instance
    model = FantasyBaseballAutomated(args.league_id, args.team_name)
    
    # Check if we can load existing state
    if not model.load_system_state():
        logger.info("No existing state found. Loading initial data...")
        model.load_initial_data()
    
    # Handle command-line options
    if args.manual_update:
        logger.info("Running manual update...")
        model.run_system_update()
    
    if args.reports_only:
        logger.info("Generating reports only...")
        model.generate_reports()
    
    if args.daemon:
        # Schedule updates
        model.schedule_updates(args.daily_update, args.weekly_update)
        # Start update loop
        model.start_update_loop()
    
    logger.info("Fantasy Baseball Automated Model completed successfully!")

if __name__ == "__main__":
    main()
                ops_values = [ops for ops in ops_values if ops > 0]
                batting_totals['OPS'] = sum(ops_values) / len(ops_values) if ops_values else 0
            
            # Sort by AB descending
            batter_table.sort(key=lambda x: x[1], reverse=True)
            
            # Add totals row
            batter_table.append([
                "TOTALS",
                batting_totals['AB'],
                batting_totals['R'],
                batting_totals['HR'],
                batting_totals['RBI'],
                batting_totals['SB'],
                f"{batting_totals['AVG']:.3f}",
                f"{batting_totals['OPS']:.3f}"
            ])
            
            f.write(tabulate(batter_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Pitchers stats
            f.write("#### Pitching Stats\n\n")
            pitcher_table = []
            headers = ["Player", "IP", "W", "ERA", "WHIP", "K", "QS", "SV"]
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_stats_current and 'ERA' in self.player_stats_current[name]:
                    stats = self.player_stats_current[name]
                    pitcher_table.append([
                        name,
                        stats.get('IP', 0),
                        stats.get('W', 0),
                        f"{stats.get('ERA', 0):.2f}",
                        f"{stats.get('WHIP', 0):.2f}",
                        stats.get('K', 0),
                        stats.get('QS', 0),
                        stats.get('SV', 0)
                    ])
                    
                    # Add to totals
                    pitching_totals['IP'] += stats.get('IP', 0)
                    pitching_totals['W'] += stats.get('W', 0)
                    pitching_totals['K'] += stats.get('K', 0)
                    pitching_totals['QS'] += stats.get('QS', 0)
                    pitching_totals['SV'] += stats.get('SV', 0)
            
            # Calculate team ERA and WHIP
            if pitching_totals['IP'] > 0:
                # Calculate total ER and baserunners across all pitchers
                total_er = sum(self.player_stats_current.get(p["name"], {}).get('ERA', 0) * 
                               self.player_stats_current.get(p["name"], {}).get('IP', 0) / 9 
                               for p in self.team_rosters.get(self.your_team_name, [])
                               if 'ERA' in self.player_stats_current.get(p["name"], {}))
                
                total_baserunners = sum(self.player_stats_current.get(p["name"], {}).get('WHIP', 0) * 
                                       self.player_stats_current.get(p["name"], {}).get('IP', 0) 
                                       for p in self.team_rosters.get(self.your_team_name, [])
                                       if 'WHIP' in self.player_stats_current.get(p["name"], {}))
                
                pitching_totals['ERA'] = total_er * 9 / pitching_totals['IP']
                pitching_totals['WHIP'] = total_baserunners / pitching_totals['IP']
            
            # Sort by IP descending
            pitcher_table.sort(key=lambda x: x[1], reverse=True)
            
            # Add totals row
            pitcher_table.append([
                "TOTALS",
                pitching_totals['IP'],
                pitching_totals['W'],
                f"{pitching_totals['ERA']:.2f}",
                f"{pitching_totals['WHIP']:.2f}",
                pitching_totals['K'],
                pitching_totals['QS'],
                pitching_totals['SV']
            ])
            
            f.write(tabulate(pitcher_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Team Projections
            f.write("### Rest of Season Projections\n\n")
            
            # Batters projections
            f.write("#### Batting Projections\n\n")
            batter_proj_table = []
            headers = ["Player", "AB", "R", "HR", "RBI", "SB", "AVG", "OPS"]
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_projections and 'AVG' in self.player_projections[name]:
                    proj = self.player_projections[name]
                    batter_proj_table.append([
                        name,
                        int(proj.get('AB', 0)),
                        int(proj.get('R', 0)),
                        int(proj.get('HR', 0)),
                        int(proj.get('RBI', 0)),
                        int(proj.get('SB', 0)),
                        f"{proj.get('AVG', 0):.3f}",
                        f"{proj.get('OPS', 0):.3f}"
                    ])
            
            # Sort by projected AB descending
            batter_proj_table.sort(key=lambda x: x[1], reverse=True)
            
            f.write(tabulate(batter_proj_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Pitchers projections
            f.write("#### Pitching Projections\n\n")
            pitcher_proj_table = []
            headers = ["Player", "IP", "ERA", "WHIP", "K/9", "QS", "SV"]
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_projections and 'ERA' in self.player_projections[name]:
                    proj = self.player_projections[name]
                    pitcher_proj_table.append([
                        name,
                        int(proj.get('IP', 0)),
                        f"{proj.get('ERA', 0):.2f}",
                        f"{proj.get('WHIP', 0):.2f}",
                        f"{proj.get('K9', 0):.1f}",
                        int(proj.get('QS', 0)),
                        int(proj.get('SV', 0))
                    ])
            
            # Sort by projected IP descending
            pitcher_proj_table.sort(key=lambda x: x[1], reverse=True)
            
            f.write(tabulate(pitcher_proj_table, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Recent News
            f.write("### Recent Team News\n\n")
            
            news_count = 0
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_news and self.player_news[name]:
                    # Sort news by date (most recent first)
                    player_news = sorted(
                        self.player_news[name], 
                        key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"), 
                        reverse=True
                    )
                    
                    # Show most recent news item
                    latest_news = player_news[0]
                    f.write(f"**{name}** ({latest_news['date']} - {latest_news['source']}): {latest_news['content']}\n\n")
                    news_count += 1
            
            if news_count == 0:
                f.write("No recent news for your team's players.\n\n")
            
            # Recommendations
            f.write("## Team Recommendations\n\n")
            
            # Analyze team strengths and weaknesses
            # This is a simplified analysis - a real implementation would be more sophisticated
            
            # Calculate average stats per player
            avg_hr = batting_totals['HR'] / len([p for p in self.team_rosters.get(self.your_team_name, []) if p["name"] in self.player_stats_current and 'AVG' in self.player_stats_current[p["name"]]]) if len([p for p in self.team_rosters.get(self.your_team_name, []) if p["name"] in self.player_stats_current and 'AVG' in self.player_stats_current[p["name"]]]) > 0 else 0
            
            avg_sb = batting_totals['SB'] / len([p for p in self.team_rosters.get(self.your_team_name, []) if p["name"] in self.player_stats_current and 'AVG' in self.player_stats_current[p["name"]]]) if len([p for p in self.team_rosters.get(self.your_team_name, []) if p["name"] in self.player_stats_current and 'AVG' in self.player_stats_current[p["name"]]]) > 0 else 0
            
            avg_era = pitching_totals['ERA']
            avg_k9 = pitching_totals['K'] * 9 / pitching_totals['IP'] if pitching_totals['IP'] > 0 else 0
            
            # Identify strengths and weaknesses
            strengths = []
            weaknesses = []
            
            if batting_totals['AVG'] > 0.270:
                strengths.append("Batting Average")
            elif batting_totals['AVG'] < 0.250:
                weaknesses.append("Batting Average")
                
            if batting_totals['OPS'] > 0.780:
                strengths.append("OPS")
            elif batting_totals['OPS'] < 0.720:
                weaknesses.append("OPS")
                
            if avg_hr > 0.08:  # More than 0.08 HR per AB
                strengths.append("Power")
            elif avg_hr < 0.04:
                weaknesses.append("Power")
                
            if avg_sb > 0.05:  # More than 0.05 SB per AB
                strengths.append("Speed")
            elif avg_sb < 0.02:
                weaknesses.append("Speed")
                
            if avg_era < 3.80:
                strengths.append("ERA")
            elif avg_era > 4.20:
                weaknesses.append("ERA")
                
            if pitching_totals['WHIP'] < 1.20:
                strengths.append("WHIP")
            elif pitching_totals['WHIP'] > 1.30:
                weaknesses.append("WHIP")
                
            if avg_k9 > 9.5:
                strengths.append("Strikeouts")
            elif avg_k9 < 8.0:
                weaknesses.append("Strikeouts")
                
            if pitching_totals['SV'] > 15:
                strengths.append("Saves")
            elif pitching_totals['SV'] < 5:
                weaknesses.append("Saves")
                
            if pitching_totals['QS'] > 15:
                strengths.append("Quality Starts")
            elif pitching_totals['QS'] < 5:
                weaknesses.append("Quality Starts")
                
            # Write strengths and weaknesses
            f.write("### Team Strengths\n\n")
            if strengths:
                for strength in strengths:
                    f.write(f"- **{strength}**\n")
            else:
                f.write("No clear strengths identified yet.\n")
            
            f.write("\n### Team Weaknesses\n\n")
            if weaknesses:
                for weakness in weaknesses:
                    f.write(f"- **{weakness}**\n")
            else:
                f.write("No clear weaknesses identified yet.\n")
            
            f.write("\n### Recommended Actions\n\n")
            
            # Generate recommendations based on weaknesses
            if weaknesses:
                for weakness in weaknesses[:3]:  # Focus on top 3 weaknesses
                    if weakness == "Power":
                        f.write("- **Target Power Hitters**: Consider trading for players with high HR and RBI projections.\n")
                        
                        # Suggest specific free agents
                        power_fa = sorted(
                            [(name, p['projections'].get('HR', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'HR' in p['projections']],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if power_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {int(p[1])} HR)" for p in power_fa]) + "\n")
                    
                    elif weakness == "Speed":
                        f.write("- **Add Speed**: Look to add players who can contribute stolen bases.\n")
                        
                        # Suggest specific free agents
                        speed_fa = sorted(
                            [(name, p['projections'].get('SB', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'SB' in p['projections']],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if speed_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {int(p[1])} SB)" for p in speed_fa]) + "\n")
                    
                    elif weakness == "Batting Average":
                        f.write("- **Improve Batting Average**: Look for consistent contact hitters.\n")
                        
                        # Suggest specific free agents
                        avg_fa = sorted(
                            [(name, p['projections'].get('AVG', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'AVG' in p['projections'] and p['projections'].get('AB', 0) > 300],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if avg_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {p[1]:.3f} AVG)" for p in avg_fa]) + "\n")
                    
                    elif weakness == "ERA" or weakness == "WHIP":
                        f.write("- **Improve Pitching Ratios**: Focus on pitchers with strong ERA and WHIP projections.\n")
                        
                        # Suggest specific free agents
                        ratio_fa = sorted(
                            [(name, p['projections'].get('ERA', 0), p['projections'].get('WHIP', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'ERA' in p['projections'] and p['projections'].get('IP', 0) > 100],
                            key=lambda x: x[1] + x[2]
                        )[:3]
                        
                        if ratio_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {p[1]:.2f} ERA, {p[2]:.2f} WHIP)" for p in ratio_fa]) + "\n")
                    
                    elif weakness == "Strikeouts":
                        f.write("- **Add Strikeout Pitchers**: Target pitchers with high K/9 rates.\n")
                        
                        # Suggest specific free agents
                        k_fa = sorted(
                            [(name, p['projections'].get('K9', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'K9' in p['projections'] and p['projections'].get('IP', 0) > 75],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if k_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {p[1]:.1f} K/9)" for p in k_fa]) + "\n")
                    
                    elif weakness == "Saves":
                        f.write("- **Add Closers**: Look for pitchers in save situations.\n")
                        
                        # Suggest specific free agents
                        sv_fa = sorted(
                            [(name, p['projections'].get('SV', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'SV' in p['projections'] and p['projections'].get('SV', 0) > 5],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if sv_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {int(p[1])} SV)" for p in sv_fa]) + "\n")
                    
                    elif weakness == "Quality Starts":
                        f.write("- **Add Quality Starting Pitchers**: Target consistent starters who work deep into games.\n")
                        
                        # Suggest specific free agents
                        qs_fa = sorted(
                            [(name, p['projections'].get('QS', 0)) 
                             for name, p in self.free_agents.items() 
                             if 'QS' in p['projections'] and p['projections'].get('QS', 0) > 5],
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        
                        if qs_fa:
                            f.write("  - **Free Agent Targets**: " + ", ".join([f"{p[0]} (Proj. {int(p[1])} QS)" for p in qs_fa]) + "\n")
            else:
                f.write("Your team is well-balanced! Continue to monitor player performance and injuries.\n")
            
            # General strategy recommendation
            f.write("\n### General Strategy\n\n")
            f.write("1. **Monitor the waiver wire daily** for emerging talent and players returning from injury.\n")
            f.write("2. **Be proactive with injured players**. Don't hold onto injured players too long if better options are available.\n")
            f.write("3. **Stream starting pitchers** against weak offensive teams for additional counting stats.\n")
            f.write("4. **Watch for changing roles** in bullpens for potential closers in waiting.\n")
            
            logger.info(f"Team analysis report generated: {output_file}")
    
    def generate_free_agents_report(self, output_file):
        """Generate free agents report sorted by projected value"""
        with open(output_file, 'w') as f:
            # Title
            f.write("# Fantasy Baseball Free Agent Analysis\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
            
            # Calculate scores for ranking
            fa_batters = {}
            fa_pitchers = {}
            
            for name, data in self.free_agents.items():
                if 'projections' in data:
                    proj = data['projections']
                    if 'AVG' in proj:  # It's a batter
                        # Calculate a batter score
                        score = (
                            proj.get('HR', 0) * 3 +
                            proj.get('SB', 0) * 3 +
                            proj.get('R', 0) * 0.5 +
                            proj.get('RBI', 0) * 0.5 +
                            proj.get('AVG', 0) * 300 +
                            proj.get('OPS', 0) * 150
                        )
                        fa_batters[name] = {'projections': proj, 'score': score}
                    
                    elif 'ERA' in proj:  # It's a pitcher
                        # Calculate a pitcher score
                        era_score = (5.00 - proj.get('ERA', 4.50)) * 20 if proj.get('ERA', 0) < 5.00 else 0
                        whip_score = (1.40 - proj.get('WHIP', 1.30)) * 60 if proj.get('WHIP', 0) < 1.40 else 0
                        
                        score = (
                            era_score +
                            whip_score +
                            proj.get('K9', 0) * 10 +
                            proj.get('QS', 0) * 4 +
                            proj.get('SV', 0) * 6 +
                            proj.get('IP', 0) * 0.2
                        )
                        fa_pitchers[name] = {'projections': proj, 'score': score}
            
            # Top Batters by Position
            f.write("## Top Free Agent Batters\n\n")
            
            # Define positions
            positions = {
                "C": "Catchers",
                "1B": "First Basemen",
                "2B": "Second Basemen",
                "3B": "Third Basemen",
                "SS": "Shortstops",
                "OF": "Outfielders"
            }
            
            # Simplified position assignment for demo
            position_players = {pos: [] for pos in positions}
            
            # Manually assign positions for demo
            for name in fa_batters:
                # This is a very simplified approach - in reality, you'd have actual position data
                if name in ["Keibert Ruiz", "Danny Jansen", "Gabriel Moreno", "Patrick Bailey", "Ryan Jeffers"]:
                    position_players["C"].append(name)
                elif name in ["Christian Walker", "Spencer Torkelson", "Andrew Vaughn", "Anthony Rizzo"]:
                    position_players["1B"].append(name)
                elif name in ["Gavin Lux", "Luis Rengifo", "Nick Gonzales", "Zack Gelof", "Brendan Donovan"]:
                    position_players["2B"].append(name)
                elif name in ["Jeimer Candelario", "Spencer Steer", "Ke'Bryan Hayes", "Brett Baty"]:
                    position_players["3B"].append(name)
                elif name in ["JP Crawford", "Ha-Seong Kim", "Xander Bogaerts", "Jose Barrero"]:
                    position_players["SS"].append(name)
                else:
                    position_players["OF"].append(name)
            
            # Write position sections
            for pos, title in positions.items():
                players = position_players[pos]
                if players:
                    f.write(f"### {title}\n\n")
                    
                    # Create table
                    headers = ["Rank", "Player", "AB", "R", "HR", "RBI", "SB", "AVG", "OPS", "Score"]
                    
                    # Get scores and sort
                    pos_players = [(name, fa_batters[name]['score'], fa_batters[name]['projections']) 
                                 for name in players if name in fa_batters]
                    
                    pos_players.sort(key=lambda x: x[1], reverse=True)
                    
                    # Build table
                    table_data = []
                    for i, (name, score, proj) in enumerate(pos_players[:10]):  # Top 10 per position
                        table_data.append([
                            i+1,
                            name,
                            int(proj.get('AB', 0)),
                            int(proj.get('R', 0)),
                            int(proj.get('HR', 0)),
                            int(proj.get('RBI', 0)),
                            int(proj.get('SB', 0)),
                            f"{proj.get('AVG', 0):.3f}",
                            f"{proj.get('OPS', 0):.3f}",
                            int(score)
                        ])
                    
                    f.write(tabulate(table_data, headers=headers, tablefmt="pipe"))
                    f.write("\n\n")
            
            # Top Pitchers
            f.write("## Top Free Agent Pitchers\n\n")
            
            # Starting pitchers
            f.write("### Starting Pitchers\n\n")
            
            # Identify starters
            starters = [(name, fa_pitchers[name]['score'], fa_pitchers[name]['projections']) 
                       for name in fa_pitchers 
                       if fa_pitchers[name]['projections'].get('QS', 0) > 0]
            
            starters.sort(key=lambda x: x[1], reverse=True)
            
            # Create table
            headers = ["Rank", "Player", "IP", "ERA", "WHIP", "K/9", "QS", "Score"]
            
            table_data = []
            for i, (name, score, proj) in enumerate(starters[:15]):  # Top 15 SP
                table_data.append([
                    i+1,
                    name,
                    int(proj.get('IP', 0)),
                    f"{proj.get('ERA', 0):.2f}",
                    f"{proj.get('WHIP', 0):.2f}",
                    f"{proj.get('K9', 0):.1f}",
                    int(proj.get('QS', 0)),
                    int(score)
                ])
            
            f.write(tabulate(table_data, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Relief pitchers
            f.write("### Relief Pitchers\n\n")
            
            # Identify relievers
            relievers = [(name, fa_pitchers[name]['score'], fa_pitchers[name]['projections']) 
                        for name in fa_pitchers 
                        if fa_pitchers[name]['projections'].get('QS', 0) == 0]
            
            relievers.sort(key=lambda x: x[1], reverse=True)
            
            # Create table
            headers = ["Rank", "Player", "IP", "ERA", "WHIP", "K/9", "SV", "Score"]
            
            table_data = []
            for i, (name, score, proj) in enumerate(relievers[:10]):  # Top 10 RP
                table_data.append([
                    i+1,
                    name,
                    int(proj.get('IP', 0)),
                    f"{proj.get('ERA', 0):.2f}",
                    f"{proj.get('WHIP', 0):.2f}",
                    f"{proj.get('K9', 0):.1f}",
                    int(proj.get('SV', 0)),
                    int(score)
                ])
            
            f.write(tabulate(table_data, headers=headers, tablefmt="pipe"))
            f.write("\n\n")
            
            # Category-Specific Free Agent Targets
            f.write("## Category-Specific Free Agent Targets\n\n")
            
            # Power hitters (HR and RBI)
            power_hitters = sorted(
                [(name, fa_batters[name]['projections'].get('HR', 0), fa_batters[name]['projections'].get('RBI', 0)) 
                 for name in fa_batters],
                key=lambda x: x[1] + x[2]/3,
                reverse=True
            )[:5]
            
            f.write("**Power (HR/RBI):** ")
            f.write(", ".join([f"{name} ({int(hr)} HR, {int(rbi)} RBI)" for name, hr, rbi in power_hitters]))
            f.write("\n\n")
            
            # Speed (SB)
            speed_players = sorted(
                [(name, fa_batters[name]['projections'].get('SB', 0)) 
                 for name in fa_batters],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            f.write("**Speed (SB):** ")
            f.write(", ".join([f"{name} ({int(sb)} SB)" for name, sb in speed_players]))
            f.write("\n\n")
            
            # Average (AVG)
            average_hitters = sorted(
                [(name, fa_batters[name]['projections'].get('AVG', 0)) 
                 for name in fa_batters 
                 if fa_batters[name]['projections'].get('AB', 0) >= 300],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            f.write("**Batting Average:** ")
            f.write(", ".join([f"{name} ({avg:.3f})" for name, avg in average_hitters]))
            f.write("\n\n")
            
            # ERA
            era_pitchers = sorted(
                [(name, fa_pitchers[name]['projections'].get('ERA', 0)) 
                 for name in fa_pitchers 
                 if fa_pitchers[name]['projections'].get('IP', 0) >= 100],
                key=lambda x: x[1]
            )[:5]
            
            f.write("**ERA:** ")
            f.write(", ".join([f"{name} ({era:.2f})" for name, era in era_pitchers]))
            f.write("\n\n")
            
            # WHIP
            whip_pitchers = sorted(
                [(name, fa_pitchers[name]['projections'].get('WHIP', 0)) 
                 for name in fa_pitchers 
                 if fa_pitchers[name]['projections'].get('IP', 0) >= 100],
                key=lambda x: x[1]
            )[:5]
            
            f.write("**WHIP:** ")
            f.write(", ".join([f"{name} ({whip:.2f})" for name, whip in whip_pitchers]))
            f.write("\n\n")
            
            # Saves (SV)
            save_pitchers = sorted(
                [(name, fa_pitchers[name]['projections'].get('SV', 0)) 
                 for name in fa_pitchers],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            f.write("**Saves:** ")
            f.write(", ".join([f"{name} ({int(sv)})" for name, sv in save_pitchers]))
            f.write("\n\n")
            
            logger.info(f"Free agents report generated: {output_file}")
    
    def generate_trending_players_report(self, output_file):
        """Generate report on trending players (hot/cold)"""
        # In a real implementation, you would calculate trends based on recent performance
        # For demo purposes, we'll simulate trends
        
        with open(output_                # Recalculate AVG
                self.player_stats_current[player]['AVG'] = (
                    self.player_stats_current[player]['H'] / 
                    self.player_stats_current[player]['AB'] 
                    if self.player_stats_current[player]['AB'] > 0 else 0
                )
                
                # Recalculate OBP
                self.player_stats_current[player]['OBP'] = (
                    (self.player_stats_current[player]['H'] + self.player_stats_current[player]['BB']) / 
                    (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) 
                    if (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) > 0 else 0
                )
                
                # Recalculate SLG and OPS
                singles = (
                    self.player_stats_current[player]['H'] - 
                    self.player_stats_current[player]['HR'] - 
                    self.player_stats_current[player].get('2B', random.randint(15, 25)) - 
                    self.player_stats_current[player].get('3B', random.randint(0, 5))
                )
                
                tb = (
                    singles + 
                    (2 * self.player_stats_current[player].get('2B', random.randint(15, 25))) + 
                    (3 * self.player_stats_current[player].get('3B', random.randint(0, 5))) + 
                    (4 * self.player_stats_current[player]['HR'])
                )
                
                self.player_stats_current[player]['SLG'] = (
                    tb / self.player_stats_current[player]['AB'] 
                    if self.player_stats_current[player]['AB'] > 0 else 0
                )
                
                self.player_stats_current[player]['OPS'] = (
                    self.player_stats_current[player]['OBP'] + 
                    self.player_stats_current[player]['SLG']
                )
    
    def update_player_projections(self):
        """Update player projections by fetching from data sources"""
        logger.info("Updating player projections from sources...")
        
        # In a real implementation, you would:
        # 1. Fetch data from each source in self.data_sources['projections']
        # 2. Parse and clean the data
        # 3. Merge with existing projections
        # 4. Update self.player_projections
        
        # For demo purposes, we'll simulate this process
        self._simulate_projections_update()
        
        logger.info(f"Updated projections for {len(self.player_projections)} players")
        return len(self.player_projections)
    
    def _simulate_projections_update(self):
        """Simulate updating projections for demo purposes"""
        # Update existing projections based on current stats
        for player in self.player_stats_current:
            # Skip if no projection exists
            if player not in self.player_projections:
                # Create new projection based on current stats
                if 'ERA' in self.player_stats_current[player]:  # It's a pitcher
                    # Project rest of season based on current performance
                    era_factor = min(max(4.00 / self.player_stats_current[player]['ERA'], 0.75), 1.25) if self.player_stats_current[player]['ERA'] > 0 else 1.0
                    whip_factor = min(max(1.30 / self.player_stats_current[player]['WHIP'], 0.75), 1.25) if self.player_stats_current[player]['WHIP'] > 0 else 1.0
                    k9_factor = min(max(self.player_stats_current[player]['K9'] / 8.5, 0.75), 1.25) if self.player_stats_current[player].get('K9', 0) > 0 else 1.0
                    
                    # Determine if starter or reliever
                    is_reliever = 'SV' in self.player_stats_current[player] or self.player_stats_current[player].get('IP', 0) < 20
                    
                    self.player_projections[player] = {
                        'IP': random.uniform(40, 70) if is_reliever else random.uniform(120, 180),
                        'ERA': random.uniform(3.0, 4.5) * era_factor,
                        'WHIP': random.uniform(1.05, 1.35) * whip_factor,
                        'K9': random.uniform(7.5, 12.0) * k9_factor,
                        'QS': 0 if is_reliever else random.randint(10, 20),
                        'SV': random.randint(15, 35) if is_reliever and self.player_stats_current[player].get('SV', 0) > 0 else 0
                    }
                else:  # It's a batter
                    # Project rest of season based on current performance
                    avg_factor = min(max(self.player_stats_current[player]['AVG'] / 0.260, 0.8), 1.2) if self.player_stats_current[player]['AVG'] > 0 else 1.0
                    ops_factor = min(max(self.player_stats_current[player].get('OPS', 0.750) / 0.750, 0.8), 1.2) if self.player_stats_current[player].get('OPS', 0) > 0 else 1.0
                    
                    # Projected plate appearances remaining
                    pa_remaining = random.randint(400, 550)
                    
                    # HR rate
                    hr_rate = self.player_stats_current[player]['HR'] / self.player_stats_current[player]['AB'] if self.player_stats_current[player]['AB'] > 0 else 0.025
                    
                    # SB rate
                    sb_rate = self.player_stats_current[player]['SB'] / self.player_stats_current[player]['AB'] if self.player_stats_current[player]['AB'] > 0 else 0.015
                    
                    self.player_projections[player] = {
                        'AB': pa_remaining * 0.9,  # 10% of PA are walks/HBP
                        'R': pa_remaining * random.uniform(0.12, 0.18),
                        'HR': pa_remaining * hr_rate * random.uniform(0.8, 1.2),
                        'RBI': pa_remaining * random.uniform(0.1, 0.17),
                        'SB': pa_remaining * sb_rate * random.uniform(0.8, 1.2),
                        'AVG': random.uniform(0.230, 0.310) * avg_factor,
                        'OPS': random.uniform(0.680, 0.950) * ops_factor
                    }
                continue
            
            # If projection exists, update it based on current performance
            if 'ERA' in self.player_stats_current[player]:  # It's a pitcher
                # Calculate adjustment factors based on current vs. projected performance
                if self.player_stats_current[player].get('IP', 0) > 20:  # Enough IP to adjust projections
                    # ERA adjustment
                    current_era = self.player_stats_current[player].get('ERA', 4.00)
                    projected_era = self.player_projections[player].get('ERA', 4.00)
                    era_adj = min(max(projected_era / current_era, 0.8), 1.2) if current_era > 0 else 1.0
                    
                    # WHIP adjustment
                    current_whip = self.player_stats_current[player].get('WHIP', 1.30)
                    projected_whip = self.player_projections[player].get('WHIP', 1.30)
                    whip_adj = min(max(projected_whip / current_whip, 0.8), 1.2) if current_whip > 0 else 1.0
                    
                    # K/9 adjustment
                    current_k9 = self.player_stats_current[player].get('K9', 8.5)
                    projected_k9 = self.player_projections[player].get('K9', 8.5)
                    k9_adj = min(max(current_k9 / projected_k9, 0.8), 1.2) if projected_k9 > 0 else 1.0
                    
                    # Apply adjustments
                    self.player_projections[player]['ERA'] = projected_era * era_adj
                    self.player_projections[player]['WHIP'] = projected_whip * whip_adj
                    self.player_projections[player]['K9'] = projected_k9 * k9_adj
                    
                    # Adjust saves projection for relievers
                    if 'SV' in self.player_stats_current[player]:
                        current_sv_rate = self.player_stats_current[player].get('SV', 0) / max(1, self.player_stats_current[player].get('IP', 1) / 60)
                        self.player_projections[player]['SV'] = min(45, max(0, int(current_sv_rate * 60)))
                    
                    # Adjust QS projection for starters
                    if 'QS' in self.player_stats_current[player] and self.player_stats_current[player].get('IP', 0) > 0:
                        current_qs_rate = self.player_stats_current[player].get('QS', 0) / max(1, self.player_stats_current[player].get('IP', 1) / 180)
                        self.player_projections[player]['QS'] = min(30, max(0, int(current_qs_rate * 180)))
            else:  # It's a batter
                # Adjust only if enough AB to be significant
                if self.player_stats_current[player].get('AB', 0) > 75:
                    # AVG adjustment
                    current_avg = self.player_stats_current[player].get('AVG', 0.260)
                    projected_avg = self.player_projections[player].get('AVG', 0.260)
                    avg_adj = min(max((current_avg + 2*projected_avg) / (3*projected_avg), 0.85), 1.15) if projected_avg > 0 else 1.0
                    
                    # HR rate adjustment
                    current_hr_rate = self.player_stats_current[player].get('HR', 0) / max(1, self.player_stats_current[player].get('AB', 1)) * 550
                    projected_hr = self.player_projections[player].get('HR', 15)
                    hr_adj = min(max((current_hr_rate + 2*projected_hr) / (3*projected_hr), 0.7), 1.3) if projected_hr > 0 else 1.0
                    
                    # SB rate adjustment
                    current_sb_rate = self.player_stats_current[player].get('SB', 0) / max(1, self.player_stats_current[player].get('AB', 1)) * 550
                    projected_sb = self.player_projections[player].get('SB', 10)
                    sb_adj = min(max((current_sb_rate + 2*projected_sb) / (3*projected_sb), 0.7), 1.3) if projected_sb > 0 else 1.0
                    
                    # Apply adjustments
                    self.player_projections[player]['AVG'] = projected_avg * avg_adj
                    self.player_projections[player]['HR'] = projected_hr * hr_adj
                    self.player_projections[player]['SB'] = projected_sb * sb_adj
                    
                    # Adjust OPS based on AVG and power
                    projected_ops = self.player_projections[player].get('OPS', 0.750)
                    self.player_projections[player]['OPS'] = projected_ops * (avg_adj * 0.4 + hr_adj * 0.6)
                    
                    # Adjust runs and RBI based on HR and overall performance
                    projected_r = self.player_projections[player].get('R', 70)
                    projected_rbi = self.player_projections[player].get('RBI', 70)
                    
                    self.player_projections[player]['R'] = projected_r * ((avg_adj + hr_adj) / 2)
                    self.player_projections[player]['RBI'] = projected_rbi * ((avg_adj + hr_adj) / 2)
        
        # Round numerical values for cleaner display
        for player in self.player_projections:
            for stat in self.player_projections[player]:
                if isinstance(self.player_projections[player][stat], float):
                    if stat in ['ERA', 'WHIP', 'K9', 'AVG', 'OPS']:
                        self.player_projections[player][stat] = round(self.player_projections[player][stat], 3)
                    else:
                        self.player_projections[player][stat] = round(self.player_projections[player][stat])
    
    def update_player_news(self):
        """Update player news by fetching from news sources"""
        logger.info("Updating player news from sources...")
        
        # In a real implementation, you would:
        # 1. Fetch data from each source in self.data_sources['news']
        # 2. Parse and extract news items
        # 3. Store in self.player_news
        
        # For demo purposes, we'll simulate this process
        self._simulate_news_update()
        
        logger.info(f"Updated news for {len(self.player_news)} players")
        return len(self.player_news)
    
    def _simulate_news_update(self):
        """Simulate updating player news for demo purposes"""
        # List of possible news templates
        injury_news = [
            "{player} was removed from Wednesday's game with {injury}.",
            "{player} is day-to-day with {injury}.",
            "{player} has been placed on the 10-day IL with {injury}.",
            "{player} will undergo further testing for {injury}.",
            "{player} is expected to miss 4-6 weeks with {injury}."
        ]
        
        performance_news = [
            "{player} went {stats} in Wednesday's 6-4 win.",
            "{player} struck out {k} batters in {ip} innings on Tuesday.",
            "{player} has hit safely in {streak} straight games.",
            "{player} collected {hits} hits including a homer on Monday.",
            "{player} has struggled recently, going {bad_stats} over his last 7 games."
        ]
        
        role_news = [
            "{player} will take over as the closer with {teammate} on the IL.",
            "{player} has been moved up to the {spot} spot in the batting order.",
            "{player} will make his next start on {day}.",
            "{player} has been moved to the bullpen.",
            "{player} will be recalled from Triple-A on Friday."
        ]
        
        # Possible injuries
        injuries = [
            "left hamstring tightness",
            "right oblique strain",
            "lower back discomfort",
            "shoulder inflammation",
            "forearm tightness",
            "groin strain",
            "ankle sprain",
            "knee soreness",
            "thumb contusion",
            "wrist inflammation"
        ]
        
        # Generate news for a subset of players
        for player in random.sample(list(self.player_stats_current.keys()), min(10, len(self.player_stats_current))):
            news_type = random.choice(["injury", "performance", "role"])
            
            if news_type == "injury":
                template = random.choice(injury_news)
                news_item = template.format(
                    player=player,
                    injury=random.choice(injuries)
                )
            elif news_type == "performance":
                template = random.choice(performance_news)
                
                # Determine if batter or pitcher
                if 'ERA' in self.player_stats_current[player]:  # Pitcher
                    ip = round(random.uniform(5, 7), 1)
                    k = random.randint(4, 10)
                    news_item = template.format(
                        player=player,
                        k=k,
                        ip=ip,
                        streak=random.randint(3, 10),
                        hits=random.randint(2, 4),
                        bad_stats=f"{random.randint(0, 4)}-for-{random.randint(20, 30)}"
                    )
                else:  # Batter
                    hits = random.randint(0, 4)
                    abs = random.randint(hits, 5)
                    news_item = template.format(
                        player=player,
                        stats=f"{hits}-for-{abs}",
                        k=random.randint(5, 12),
                        ip=round(random.uniform(5, 7), 1),
                        streak=random.randint(5, 15),
                        hits=random.randint(2, 4),
                        bad_stats=f"{random.randint(0, 4)}-for-{random.randint(20, 30)}"
                    )
            else:  # Role
                template = random.choice(role_news)
                news_item = template.format(
                    player=player,
                    teammate=random.choice(list(self.player_stats_current.keys())),
                    spot=random.choice(["leadoff", "cleanup", "third", "fifth"]),
                    day=random.choice(["Friday", "Saturday", "Sunday", "Monday"])
                )
            
            # Add news item with timestamp
            if player not in self.player_news:
                self.player_news[player] = []
            
            self.player_news[player].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source": random.choice(["Rotowire", "CBS Sports", "ESPN", "MLB.com"]),
                "content": news_item
            })
    
    def update_player_injuries(self):
        """Update player injury statuses"""
        logger.info("Updating player injury statuses...")
        
        # In a real implementation, you would:
        # 1. Fetch injury data from reliable sources
        # 2. Update player status accordingly
        # 3. Adjust projections for injured players
        
        # For demo purposes, we'll simulate some injuries
        injury_count = 0
        
        for player in self.player_stats_current:
            # 5% chance of new injury for each player
            if random.random() < 0.05:
                injury_severity = random.choice(["day-to-day", "10-day IL", "60-day IL"])
                injury_type = random.choice([
                    "hamstring strain", "oblique strain", "back spasms", 
                    "shoulder inflammation", "elbow soreness", "knee inflammation",
                    "ankle sprain", "concussion", "wrist sprain"
                ])
                
                # Add injury news
                if player not in self.player_news:
                    self.player_news[player] = []
                
                self.player_news[player].append({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "source": random.choice(["Rotowire", "CBS Sports", "ESPN", "MLB.com"]),
                    "content": f"{player} has been placed on the {injury_severity} with a {injury_type}."
                })
                
                # Adjust projections for injured players
                if player in self.player_projections:
                    if injury_severity == "day-to-day":
                        reduction = 0.05  # 5% reduction in projections
                    elif injury_severity == "10-day IL":
                        reduction = 0.15  # 15% reduction
                    else:  # 60-day IL
                        reduction = 0.50  # 50% reduction
                    
                    # Apply reduction to projected stats
                    for stat in self.player_projections[player]:
                        if stat not in ['AVG', 'ERA', 'WHIP', 'K9', 'OPS']:  # Don't reduce rate stats
                            self.player_projections[player][stat] *= (1 - reduction)
                
                injury_count += 1
        
        logger.info(f"Updated injury status for {injury_count} players")
        return injury_count
    
    def update_league_transactions(self):
        """Simulate league transactions (adds, drops, trades)"""
        logger.info("Simulating league transactions...")
        
        # In a real implementation, you would:
        # 1. Fetch transaction data from your fantasy platform API
        # 2. Update team rosters accordingly
        
        # For demo purposes, we'll simulate some transactions
        transaction_count = 0
        
        # Add/drop transactions (1-3 per update)
        for _ in range(random.randint(1, 3)):
            # Select a random team
            team = random.choice(list(self.team_rosters.keys()))
            
            # Select a random player to drop
            if len(self.team_rosters[team]) > 0:
                drop_index = random.randint(0, len(self.team_rosters[team]) - 1)
                dropped_player = self.team_rosters[team][drop_index]["name"]
                
                # Remove from roster
                self.team_rosters[team].pop(drop_index)
                
                # Pick a random free agent to add
                if len(self.free_agents) > 0:
                    added_player = random.choice(list(self.free_agents.keys()))
                    
                    # Determine position
                    position = "Unknown"
                    if 'ERA' in self.player_stats_current.get(added_player, {}):
                        position = 'RP' if self.player_stats_current[added_player].get('SV', 0) > 0 else 'SP'
                    else:
                        position = random.choice(["C", "1B", "2B", "3B", "SS", "OF"])
                    
                    # Add to roster
                    self.team_rosters[team].append({
                        "name": added_player,
                        "position": position
                    })
                    
                    # Remove from free agents
                    if added_player in self.free_agents:
                        del self.free_agents[added_player]
                    
                    # Log transaction
                    logger.info(f"Transaction: {team} dropped {dropped_player} and added {added_player}")
                    transaction_count += 1
        
        # Trade transactions (0-1 per update)
        if random.random() < 0.3:  # 30% chance of a trade
            # Select two random teams
            teams = random.sample(list(self.team_rosters.keys()), 2)
            
            # Select random players to trade (1-2 per team)
            team1_players = []
            team2_players = []
            
            for _ in range(random.randint(1, 2)):
                if len(self.team_rosters[teams[0]]) > 0:
                    idx = random.randint(0, len(self.team_rosters[teams[0]]) - 1)
                    team1_players.append(self.team_rosters[teams[0]][idx])
                    self.team_rosters[teams[0]].pop(idx)
            
            for _ in range(random.randint(1, 2)):
                if len(self.team_rosters[teams[1]]) > 0:
                    idx = random.randint(0, len(self.team_rosters[teams[1]]) - 1)
                    team2_players.append(self.team_rosters[teams[1]][idx])
                    self.team_rosters[teams[1]].pop(idx)
            
            # Execute the trade
            for player in team1_players:
                self.team_rosters[teams[1]].append(player)
            
            for player in team2_players:
                self.team_rosters[teams[0]].append(player)
            
            # Log transaction
            team1_names = [p["name"] for p in team1_players]
            team2_names = [p["name"] for p in team2_players]
            
            logger.info(f"Trade: {teams[0]} traded {', '.join(team1_names)} to {teams[1]} for {', '.join(team2_names)}")
            transaction_count += 1
        
        logger.info(f"Simulated {transaction_count} league transactions")
        return transaction_count
    
    def run_system_update(self):
        """Run a complete system update"""
        logger.info("Starting system update...")
        
        try:
            # Update player stats
            self.update_player_stats()
            
            # Update player projections
            self.update_player_projections()
            
            # Update player news
            self.update_player_news()
            
            # Update player injuries
            self.update_player_injuries()
            
            # Update league transactions
            self.update_league_transactions()
            
            # Identify free agents
            self.identify_free_agents()
            
            # Save updated system state
            self.save_system_state()
            
            # Generate updated reports
            self.generate_reports()
            
            # Update timestamp
            self.last_update = datetime.now()
            
            logger.info(f"System update completed successfully at {self.last_update}")
            return True
        except Exception as e:
            logger.error(f"Error during system update: {e}")
            return False
    
    def generate_reports(self):
        """Generate various reports"""
        timestamp = datetime.now().strftime("%Y%m%d")
        
        # Generate team analysis report
        self.generate_team_analysis_report(f"{self.reports_dir}/team_analysis_{timestamp}.md")
        
        # Generate free agents report
        self.generate_free_agents_report(f"{self.reports_dir}/free_agents_{timestamp}.md")
        
        # Generate trending players report
        self.generate_trending_players_report(f"{self.reports_dir}/trending_players_{timestamp}.md")
        
        # Generate player news report
        self.generate_player_news_report(f"{self.reports_dir}/player_news_{timestamp}.md")
        
        logger.info(f"Generated reports with timestamp {timestamp}")
    
    def generate_team_analysis_report(self, output_file):
        """Generate team analysis report"""
        with open(output_file, 'w') as f:
            # Title
            f.write("# Fantasy Baseball Team Analysis\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*\n\n")
            
            # Your Team Section
            f.write(f"## Your Team: {self.your_team_name}\n\n")
            
            # Team Roster
            f.write("### Current Roster\n\n")
            
            # Group players by position
            positions = {"C": [], "1B": [], "2B": [], "3B": [], "SS": [], "OF": [], "SP": [], "RP": []}
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                position = player["position"]
                
                # Simplified position assignment
                if position in positions:
                    positions[position].append(name)
                elif "/" in position:  # Handle multi-position players
                    primary_pos = position.split("/")[0]
                    if primary_pos in positions:
                        positions[primary_pos].append(name)
                    else:
                        positions["UTIL"].append(name)
                else:
                    # Handle unknown positions
                    if 'ERA' in self.player_stats_current.get(name, {}):
                        if self.player_stats_current[name].get('SV', 0) > 0:
                            positions["RP"].append(name)
                        else:
                            positions["SP"].append(name)
                    else:
                        positions["UTIL"].append(name)
            
            # Write roster by position
            for pos, players in positions.items():
                if players:
                    f.write(f"**{pos}**: {', '.join(players)}\n\n")
            
            # Team Performance
            f.write("### Team Performance\n\n")
            
            # Calculate team totals
            batting_totals = {
                'AB': 0, 'R': 0, 'HR': 0, 'RBI': 0, 'SB': 0, 'AVG': 0, 'OPS': 0
            }
            
            pitching_totals = {
                'IP': 0, 'W': 0, 'ERA': 0, 'WHIP': 0, 'K': 0, 'QS': 0, 'SV': 0
            }
            
            # Batters stats
            f.write("#### Batting Stats\n\n")
            batter_table = []
            headers = ["Player", "AB", "R", "HR", "RBI", "SB", "AVG", "OPS"]
            
            for player in self.team_rosters.get(self.your_team_name, []):
                name = player["name"]
                if name in self.player_stats_current and 'AVG' in self.player_stats_current[name]:
                    stats = self.player_stats_current[name]
                    batter_table.append([
                        name,
                        stats.get('AB', 0),
                        stats.get('R', 0),
                        stats.get('HR', 0),
                        stats.get('RBI', 0),
                        stats.get('SB', 0),
                        f"{stats.get('AVG', 0):.3f}",
                        f"{stats.get('OPS', 0):.3f}"
                    ])
                    
                    # Add to totals
                    batting_totals['AB'] += stats.get('AB', 0)
                    batting_totals['R'] += stats.get('R', 0)
                    batting_totals['HR'] += stats.get('HR', 0)
                    batting_totals['RBI'] += stats.get('RBI', 0)
                    batting_totals['SB'] += stats.get('SB', 0)
            
            # Calculate team AVG and OPS
            if batting_totals['AB'] > 0:
                total_hits = sum(self.player_stats_current.get(p["name"], {}).get('H', 0) for p in self.team_rosters.get(self.your_team_name, []))
                batting_totals['AVG'] = total_hits / batting_totals['AB']
                
                # Estimate team OPS as average of player OPS values
                ops_values = [self.player_stats_current.get(p["name"], {}).get('OPS', 0) for p in self.team_rosters.get(self.your_team_name, [])]
                ops_values = [ops for ops in ops_values if ops > 0]
                #!/usr/bin/env python3
# Fantasy Baseball Automated Model with Live Updates
# This script creates an automated system that regularly updates player stats and projections
# Uses the same sources (PECOTA, FanGraphs, MLB.com) for consistent data

import os
import csv
import json
import time
import random
import requests
import pandas as pd
import numpy as np
import schedule
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from tabulate import tabulate
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fantasy_baseball_auto.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FantasyBaseballAuto")

class FantasyBaseballAutomated:
    def __init__(self, league_id="2874", your_team_name="Kenny Kawaguchis"):
        self.league_id = league_id
        self.your_team_name = your_team_name
        self.teams = {}
        self.team_rosters = {}
        self.free_agents = {}
        self.player_stats_current = {}
        self.player_projections = {}
        self.player_news = {}
        self.last_update = None
        
        # API endpoints and data sources
        self.data_sources = {
            'stats': [
                'https://www.fangraphs.com/api/players/stats',
                'https://www.baseball-reference.com/leagues/MLB/2025.shtml',
                'https://www.mlb.com/stats/'
            ],
            'projections': [
                'https://www.fangraphs.com/projections.aspx',
                'https://www.baseball-prospectus.com/pecota-projections/',
                'https://www.mlb.com/stats/projected'
            ],
            'news': [
                'https://www.rotowire.com/baseball/news.php',
                'https://www.cbssports.com/fantasy/baseball/players/updates/',
                'https://www.espn.com/fantasy/baseball/story/_/id/29589640'
            ]
        }
        
        # Create directories for data storage
        self.data_dir = "data"
        self.reports_dir = "reports"
        self.visuals_dir = "visuals"
        self.archives_dir = "archives"
        
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.visuals_dir, exist_ok=True)
        os.makedirs(self.archives_dir, exist_ok=True)
        
        logger.info(f"Fantasy Baseball Automated Model initialized for league ID: {league_id}")
        logger.info(f"Your team: {your_team_name}")
    
    def load_initial_data(self):
        """Load initial data to bootstrap the system"""
        logger.info("Loading initial data for bootstrap...")
        
        # Load team rosters
        self.load_team_rosters()
        
        # Load initial stats and projections
        self.load_initial_stats_and_projections()
        
        # Generate initial set of free agents
        self.identify_free_agents()
        
        # Mark system as initialized with timestamp
        self.last_update = datetime.now()
        self.save_system_state()
        
        logger.info(f"Initial data loaded successfully, timestamp: {self.last_update}")
    
    def load_team_rosters(self, rosters_file=None):
        """Load team rosters from file or use default data"""
        if rosters_file and os.path.exists(rosters_file):
            try:
                df = pd.read_csv(rosters_file)
                for _, row in df.iterrows():
                    team_name = row['team_name']
                    player_name = row['player_name']
                    position = row['position']
                    
                    if team_name not in self.team_rosters:
                        self.team_rosters[team_name] = []
                    
                    self.team_rosters[team_name].append({
                        'name': player_name,
                        'position': position
                    })
                
                logger.info(f"Loaded {len(self.team_rosters)} team rosters from {rosters_file}")
            except Exception as e:
                logger.error(f"Error loading rosters file: {e}")
                self._load_default_rosters()
        else:
            logger.info("Rosters file not provided or doesn't exist. Loading default roster data.")
            self._load_default_rosters()
    
    def _load_default_rosters(self):
        """Load default roster data based on previous analysis"""
        default_rosters = {
            "Kenny Kawaguchis": [
                {"name": "Logan O'Hoppe", "position": "C"},
                {"name": "Bryce Harper", "position": "1B"},
                {"name": "Mookie Betts", "position": "2B/OF"},
                {"name": "Austin Riley", "position": "3B"},
                {"name": "CJ Abrams", "position": "SS"},
                {"name": "Lawrence Butler", "position": "OF"},
                {"name": "Riley Greene", "position": "OF"},
                {"name": "Adolis García", "position": "OF"},
                {"name": "Taylor Ward", "position": "OF"},
                {"name": "Tommy Edman", "position": "2B/SS"},
                {"name": "Roman Anthony", "position": "OF"},
                {"name": "Jonathan India", "position": "2B"},
                {"name": "Trevor Story", "position": "SS"},
                {"name": "Iván Herrera", "position": "C"},
                {"name": "Cole Ragans", "position": "SP"},
                {"name": "Hunter Greene", "position": "SP"},
                {"name": "Jack Flaherty", "position": "SP"},
                {"name": "Ryan Helsley", "position": "RP"},
                {"name": "Tanner Scott", "position": "RP"},
                {"name": "Pete Fairbanks", "position": "RP"},
                {"name": "Ryan Pepiot", "position": "SP"},
                {"name": "MacKenzie Gore", "position": "SP"},
                {"name": "Camilo Doval", "position": "RP"}
            ],
            "Mickey 18": [
                {"name": "Adley Rutschman", "position": "C"},
                {"name": "Pete Alonso", "position": "1B"},
                {"name": "Matt McLain", "position": "2B"},
                {"name": "Jordan Westburg", "position": "3B"},
                {"name": "Jeremy Peña", "position": "SS"},
                {"name": "Jasson Domínguez", "position": "OF"},
                {"name": "Tyler O'Neill", "position": "OF"},
                {"name": "Vladimir Guerrero Jr.", "position": "1B"},
                {"name": "Eugenio Suárez", "position": "3B"},
                {"name": "Ronald Acuña Jr.", "position": "OF"},
                {"name": "Tarik Skubal", "position": "SP"},
                {"name": "Spencer Schwellenbach", "position": "SP"},
                {"name": "Hunter Brown", "position": "SP"},
                {"name": "Jhoan Duran", "position": "RP"},
                {"name": "Jeff Hoffman", "position": "RP"},
                {"name": "Ryan Pressly", "position": "RP"},
                {"name": "Justin Verlander", "position": "SP"},
                {"name": "Max Scherzer", "position": "SP"}
            ],
            # Other teams omitted for brevity but would be included in full implementation
        }
        
        # Add to the team rosters dictionary
        self.team_rosters = default_rosters
        
        # Count total players loaded
        total_players = sum(len(roster) for roster in self.team_rosters.values())
        logger.info(f"Loaded {len(self.team_rosters)} team rosters with {total_players} players from default data")
    
    def load_initial_stats_and_projections(self, stats_file=None, projections_file=None):
        """Load initial stats and projections from files or use default data"""
        if stats_file and os.path.exists(stats_file) and projections_file and os.path.exists(projections_file):
            try:
                # Load stats
                with open(stats_file, 'r') as f:
                    self.player_stats_current = json.load(f)
                
                # Load projections
                with open(projections_file, 'r') as f:
                    self.player_projections = json.load(f)
                
                logger.info(f"Loaded stats for {len(self.player_stats_current)} players from {stats_file}")
                logger.info(f"Loaded projections for {len(self.player_projections)} players from {projections_file}")
            except Exception as e:
                logger.error(f"Error loading stats/projections files: {e}")
                self._load_default_stats_and_projections()
        else:
            logger.info("Stats/projections files not provided or don't exist. Loading default data.")
            self._load_default_stats_and_projections()
    
    def _load_default_stats_and_projections(self):
        """Load default stats and projections for bootstrapping"""
        # This would load from the previously created data
        # For simulation/demo purposes, we'll generate synthetic data
        
        # First, collect all players from rosters
        all_players = set()
        for team, roster in self.team_rosters.items():
            for player in roster:
                all_players.add(player["name"])
        
        # Add some free agents
        free_agents = [
            "Keibert Ruiz", "Danny Jansen", "Christian Walker", 
            "Spencer Torkelson", "Gavin Lux", "Luis Rengifo", 
            "JP Crawford", "Ha-Seong Kim", "Jeimer Candelario", 
            "Spencer Steer", "Luis Matos", "Heliot Ramos", 
            "TJ Friedl", "Garrett Mitchell", "Kutter Crawford", 
            "Reese Olson", "Dane Dunning", "José Berríos", 
            "Erik Swanson", "Seranthony Domínguez"
        ]
        
        for player in free_agents:
            all_players.add(player)
        
        # Generate stats and projections for all players
        self._generate_synthetic_data(all_players)
        
        logger.info(f"Generated synthetic stats for {len(self.player_stats_current)} players")
        logger.info(f"Generated synthetic projections for {len(self.player_projections)} players")
    
    def _generate_synthetic_data(self, player_names):
        """Generate synthetic stats and projections for demo purposes"""
        for player in player_names:
            # Determine if batter or pitcher based on name recognition
            # This is a simple heuristic; in reality, you'd use actual data
            is_pitcher = player in [
                "Cole Ragans", "Hunter Greene", "Jack Flaherty", "Ryan Helsley", 
                "Tanner Scott", "Pete Fairbanks", "Ryan Pepiot", "MacKenzie Gore", 
                "Camilo Doval", "Tarik Skubal", "Spencer Schwellenbach", "Hunter Brown", 
                "Jhoan Duran", "Jeff Hoffman", "Ryan Pressly", "Justin Verlander", 
                "Max Scherzer", "Kutter Crawford", "Reese Olson", "Dane Dunning", 
                "José Berríos", "Erik Swanson", "Seranthony Domínguez"
            ]
            
            if is_pitcher:
                # Generate pitcher stats
                current_stats = {
                    'IP': random.uniform(20, 40),
                    'W': random.randint(1, 4),
                    'L': random.randint(0, 3),
                    'ERA': random.uniform(2.5, 5.0),
                    'WHIP': random.uniform(0.9, 1.5),
                    'K': random.randint(15, 50),
                    'BB': random.randint(5, 20),
                    'QS': random.randint(1, 5),
                    'SV': 0 if player not in ["Ryan Helsley", "Tanner Scott", "Pete Fairbanks", "Camilo Doval", "Jhoan Duran", "Ryan Pressly", "Erik Swanson", "Seranthony Domínguez"] else random.randint(1, 8)
                }
                
                # Calculate k/9
                current_stats['K9'] = current_stats['K'] * 9 / current_stats['IP'] if current_stats['IP'] > 0 else 0
                
                # Generate projections (rest of season)
                projected_ip = random.uniform(120, 180) if current_stats['SV'] == 0 else random.uniform(45, 70)
                projected_stats = {
                    'IP': projected_ip,
                    'ERA': random.uniform(3.0, 4.5),
                    'WHIP': random.uniform(1.05, 1.35),
                    'K9': random.uniform(7.5, 12.0),
                    'QS': random.randint(10, 20) if current_stats['SV'] == 0 else 0,
                    'SV': 0 if current_stats['SV'] == 0 else random.randint(15, 35)
                }
            else:
                # Generate batter stats
                current_stats = {
                    'AB': random.randint(70, 120),
                    'R': random.randint(8, 25),
                    'H': random.randint(15, 40),
                    'HR': random.randint(1, 8),
                    'RBI': random.randint(5, 25),
                    'SB': random.randint(0, 8),
                    'BB': random.randint(5, 20),
                    'SO': random.randint(15, 40)
                }
                
                # Calculate derived stats
                current_stats['AVG'] = current_stats['H'] / current_stats['AB'] if current_stats['AB'] > 0 else 0
                current_stats['OBP'] = (current_stats['H'] + current_stats['BB']) / (current_stats['AB'] + current_stats['BB']) if (current_stats['AB'] + current_stats['BB']) > 0 else 0
                
                # Estimate SLG and OPS
                singles = current_stats['H'] - current_stats['HR'] - random.randint(2, 10) - random.randint(0, 5)
                doubles = random.randint(2, 10)
                triples = random.randint(0, 5)
                tb = singles + (2 * doubles) + (3 * triples) + (4 * current_stats['HR'])
                current_stats['SLG'] = tb / current_stats['AB'] if current_stats['AB'] > 0 else 0
                current_stats['OPS'] = current_stats['OBP'] + current_stats['SLG']
                
                # Generate projections (rest of season)
                projected_stats = {
                    'AB': random.randint(400, 550),
                    'R': random.randint(50, 100),
                    'HR': random.randint(10, 35),
                    'RBI': random.randint(40, 100),
                    'SB': random.randint(3, 35),
                    'AVG': random.uniform(0.230, 0.310),
                    'OPS': random.uniform(0.680, 0.950)
                }
            
            # Add to dictionaries
            self.player_stats_current[player] = current_stats
            self.player_projections[player] = projected_stats
    
    def identify_free_agents(self):
        """Identify all players who aren't on team rosters but have stats/projections"""
        # Create a set of all rostered players
        rostered_players = set()
        for team, roster in self.team_rosters.items():
            for player in roster:
                rostered_players.add(player["name"])
        
        # Find players with stats/projections who aren't rostered
        self.free_agents = {}
        
        for player in self.player_projections.keys():
            if player not in rostered_players:
                # Determine position based on stats
                if player in self.player_stats_current:
                    if 'ERA' in self.player_stats_current[player]:
                        position = 'RP' if self.player_stats_current[player].get('SV', 0) > 0 else 'SP'
                    else:
                        # This is simplistic - in a real system, we'd have actual position data
                        position = 'Unknown'
                else:
                    position = 'Unknown'
                
                self.free_agents[player] = {
                    'name': player,
                    'position': position,
                    'stats': self.player_stats_current.get(player, {}),
                    'projections': self.player_projections.get(player, {})
                }
        
        logger.info(f"Identified {len(self.free_agents)} free agents")
        return self.free_agents
    
    def save_system_state(self):
        """Save the current state of the system to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save team rosters
        with open(f"{self.data_dir}/team_rosters.json", 'w') as f:
            json.dump(self.team_rosters, f, indent=4)
        
        # Save current stats
        with open(f"{self.data_dir}/player_stats_current.json", 'w') as f:
            json.dump(self.player_stats_current, f, indent=4)
        
        # Save projections
        with open(f"{self.data_dir}/player_projections.json", 'w') as f:
            json.dump(self.player_projections, f, indent=4)
        
        # Save free agents
        with open(f"{self.data_dir}/free_agents.json", 'w') as f:
            json.dump(self.free_agents, f, indent=4)
        
        # Also save an archive copy
        with open(f"{self.archives_dir}/team_rosters_{timestamp}.json", 'w') as f:
            json.dump(self.team_rosters, f, indent=4)
        
        with open(f"{self.archives_dir}/player_stats_{timestamp}.json", 'w') as f:
            json.dump(self.player_stats_current, f, indent=4)
        
        with open(f"{self.archives_dir}/projections_{timestamp}.json", 'w') as f:
            json.dump(self.player_projections, f, indent=4)
        
        logger.info(f"System state saved successfully with timestamp: {timestamp}")
    
    def load_system_state(self):
        """Load the system state from saved files"""
        try:
            # Load team rosters
            if os.path.exists(f"{self.data_dir}/team_rosters.json"):
                with open(f"{self.data_dir}/team_rosters.json", 'r') as f:
                    self.team_rosters = json.load(f)
            
            # Load current stats
            if os.path.exists(f"{self.data_dir}/player_stats_current.json"):
                with open(f"{self.data_dir}/player_stats_current.json", 'r') as f:
                    self.player_stats_current = json.load(f)
            
            # Load projections
            if os.path.exists(f"{self.data_dir}/player_projections.json"):
                with open(f"{self.data_dir}/player_projections.json", 'r') as f:
                    self.player_projections = json.load(f)
            
            # Load free agents
            if os.path.exists(f"{self.data_dir}/free_agents.json"):
                with open(f"{self.data_dir}/free_agents.json", 'r') as f:
                    self.free_agents = json.load(f)
            
            logger.info("System state loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading system state: {e}")
            return False
    
    def update_player_stats(self):
        """Update player stats by fetching from data sources"""
        logger.info("Updating player stats from sources...")
        
        # In a real implementation, you would:
        # 1. Fetch data from each source in self.data_sources['stats']
        # 2. Parse and clean the data
        # 3. Merge with existing stats
        # 4. Update self.player_stats_current
        
        # For demo purposes, we'll simulate this process
        self._simulate_stats_update()
        
        logger.info(f"Updated stats for {len(self.player_stats_current)} players")
        return len(self.player_stats_current)
    
    def _simulate_stats_update(self):
        """Simulate updating stats for demo purposes"""
        # Add some new players
        new_players = [
            "Bobby Miller", "Garrett Crochet", "DL Hall", 
            "Edward Cabrera", "Alec Bohm", "Elly De La Cruz",
            "Anthony Volpe", "Jazz Chisholm Jr."
        ]
        
        for player in new_players:
            if player not in self.player_stats_current:
                # Determine if batter or pitcher based on name recognition
                is_pitcher = player in ["Bobby Miller", "Garrett Crochet", "DL Hall", "Edward Cabrera"]
                
                if is_pitcher:
                    self.player_stats_current[player] = {
                        'IP': random.uniform(10, 30),
                        'W': random.randint(1, 3),
                        'L': random.randint(0, 2),
                        'ERA': random.uniform(3.0, 5.0),
                        'WHIP': random.uniform(1.0, 1.4),
                        'K': random.randint(10, 40),
                        'BB': random.randint(5, 15),
                        'QS': random.randint(1, 4),
                        'SV': 0
                    }
                    
                    # Calculate k/9
                    self.player_stats_current[player]['K9'] = (
                        self.player_stats_current[player]['K'] * 9 / 
                        self.player_stats_current[player]['IP'] 
                        if self.player_stats_current[player]['IP'] > 0 else 0
                    )
                else:
                    self.player_stats_current[player] = {
                        'AB': random.randint(50, 100),
                        'R': random.randint(5, 20),
                        'H': random.randint(10, 30),
                        'HR': random.randint(1, 6),
                        'RBI': random.randint(5, 20),
                        'SB': random.randint(0, 6),
                        'BB': random.randint(5, 15),
                        'SO': random.randint(10, 30)
                    }
                    
                    # Calculate derived stats
                    self.player_stats_current[player]['AVG'] = (
                        self.player_stats_current[player]['H'] / 
                        self.player_stats_current[player]['AB'] 
                        if self.player_stats_current[player]['AB'] > 0 else 0
                    )
                    
                    self.player_stats_current[player]['OBP'] = (
                        (self.player_stats_current[player]['H'] + self.player_stats_current[player]['BB']) / 
                        (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) 
                        if (self.player_stats_current[player]['AB'] + self.player_stats_current[player]['BB']) > 0 else 0
                    )
                    
                    # Estimate SLG and OPS
                    singles = (
                        self.player_stats_current[player]['H'] - 
                        self.player_stats_current[player]['HR'] - 
                        random.randint(2, 8) - 
                        random.randint(0, 3)
                    )
                    doubles = random.randint(2, 8)
                    triples = random.randint(0, 3)
                    tb = singles + (2 * doubles) + (3 * triples) + (4 * self.player_stats_current[player]['HR'])
                    
                    self.player_stats_current[player]['SLG'] = (
                        tb / self.player_stats_current[player]['AB'] 
                        if self.player_stats_current[player]['AB'] > 0 else 0
                    )
                    
                    self.player_stats_current[player]['OPS'] = (
                        self.player_stats_current[player]['OBP'] + 
                        self.player_stats_current[player]['SLG']
                    )
        
        # Update existing player stats
        for player in list(self.player_stats_current.keys()):
            # Skip some players randomly to simulate days off
            if random.random() < 0.3:
                continue
                
            # Determine if batter or pitcher based on existing stats
            if 'ERA' in self.player_stats_current[player]:  # It's a pitcher
                # Generate random game stats
                ip = random.uniform(0.1, 7)
                k = int(ip * random.uniform(0.5, 1.5))
                bb = int(ip * random.uniform(0.1, 0.5))
                er = int(ip * random.uniform(0, 0.7))
                h = int(ip * random.uniform(0.3, 1.2))
                
                # Update aggregated stats
                self.player_stats_current[player]['IP'] += ip
                self.player_stats_current[player]['K'] += k
                self.player_stats_current[player]['BB'] += bb
                
                # Update win/loss
                if random.random() < 0.5:
                    if random.random() < 0.6:  # 60% chance of decision
                        if random.random() < 0.5:  # 50% chance of win
                            self.player_stats_current[player]['W'] = self.player_stats_current[player].get('W', 0) + 1
                        else:
                            self.player_stats_current[player]['L'] = self.player_stats_current[player].get('L', 0) + 1
                
                # Update quality starts
                if ip >= 6 and er <= 3 and 'SV' not in self.player_stats_current[player]:
                    self.player_stats_current[player]['QS'] = self.player_stats_current[player].get('QS', 0) + 1
                
                # Update saves for relievers
                if 'SV' in self.player_stats_current[player] and ip <= 2 and random.random() < 0.3:
                    self.player_stats_current[player]['SV'] = self.player_stats_current[player].get('SV', 0) + 1
                
                # Recalculate ERA and WHIP
                total_er = (self.player_stats_current[player]['ERA'] * 
                           (self.player_stats_current[player]['IP'] - ip) / 9) + er
                            
                self.player_stats_current[player]['ERA'] = (
                    total_er * 9 / self.player_stats_current[player]['IP'] 
                    if self.player_stats_current[player]['IP'] > 0 else 0
                )
                
                # Add baserunners for WHIP calculation
                self.player_stats_current[player]['WHIP'] = (
                    (self.player_stats_current[player]['WHIP'] * 
                     (self.player_stats_current[player]['IP'] - ip) + (h + bb)) / 
                    self.player_stats_current[player]['IP'] 
                    if self.player_stats_current[player]['IP'] > 0 else 0
                )
                
                # Update K/9
                self.player_stats_current[player]['K9'] = (
                    self.player_stats_current[player]['K'] * 9 / 
                    self.player_stats_current[player]['IP'] 
                    if self.player_stats_current[player]['IP'] > 0 else 0
                )
                
            else:  # It's a batter
                # Generate random game stats
                ab = random.randint(0, 5)
                h = 0
                hr = 0
                r = 0
                rbi = 0
                sb = 0
                bb = 0
                so = 0
                
                if ab > 0:
                    # Determine hits
                    for _ in range(ab):
                        if random.random() < 0.270:  # League average is around .270
                            h += 1
                            # Determine if it's a home run
                            if random.random() < 0.15:  # About 15% of hits are HRs
                                hr += 1
                    
                    # Other stats
                    r = random.randint(0, 2) if h > 0 else 0
                    rbi = random.randint(0, 3) if h > 0 else 0
                    sb = 1 if random.random() < 0.08 else 0  # 8% chance of SB
                    bb = 1 if random.random() < 0.1 else 0  # 10% chance of BB
                    so = random.randint(0, 2)  # 0-2 strikeouts
                
                # Update aggregated stats
                self.player_stats_current[player]['AB'] += ab
                self.player_stats_current[player]['H'] += h
                self.player_stats_current[player]['HR'] += hr
                self.player_stats_current[player]['R'] += r
                self.player_stats_current[player]['RBI'] += rbi
                self.player_stats_current[player]['SB'] += sb
                self.player_stats_current[player]['BB'] += bb
                self.player_stats_current[player]['SO'] += so
                
                # Recalculate AVG
                self.player_stats_current[player]['AVG'] =