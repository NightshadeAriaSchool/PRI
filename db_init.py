import sys
import subprocess

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests
try:
    import sqlalchemy
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "sqlalchemy"])
    import sqlalchemy
try:
    import psycopg2
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2"])
    import psycopg2

import json
import threading
from abc import ABC, abstractmethod
import time
import subprocess
import os

class Data:
    @staticmethod
    def get_url_index(url:str):
        segments = url.rstrip('/').split('/')
        
        return int(segments[-1])
        
    @staticmethod
    def fetch_json(name:str, id:[int|None]=None):
        url = f'https://pokeapi.co/api/v2/{name}'
        if id is None:
            url = url + "?limit=100000&offset=0"
        else:
            url = url + f'/{id}/'
    
        response = requests.get(url)
    
        data = response.json()
    
        return data

class FetchThread(threading.Thread):
    def __init__(self, name:str):
        super().__init__()
        self.name = name
        self.has_finished = False
        self.exception = None
        self.listeners = []
        self.max = 1
        self.progress = 0
        self.exception_count = 0
        self.conn = None
    
    def notify_listeners(self, data):
        for l in self.listeners:
            l.notify(data)
    
    def run(self):
        try:
            data = Data.fetch_json(self.name)
            indexes = [Data.get_url_index(node['url']) for node in data['results']]
            self.max = data['count']
        
            for i in indexes:
                self.notify_listeners(Data.fetch_json(self.name, i))
                self.progress += 1
        except Exception as e:
            self.exception = e
            self.exception_count += 1
        
        self.has_finished = True

class ProcessThread(threading.Thread, ABC):
    def __init__(self, name:str, fetch_thread:FetchThread):
        super().__init__()
        self.name = name
        self.fetch_thread = fetch_thread
        self.fetch_thread.listeners.append(self)
        self.listeners = []
        self.buffer = []
        self._progress = 0
        self.exception_count = 0
    
    @property
    def max(self):
        return self.fetch_thread.max
    
    @property
    def has_finished(self):
        return self.fetch_thread.has_finished and len(self.buffer) == 0
    
    @property
    def next(self):
        return self.buffer.pop() if len(self.buffer) > 0 else None
    
    @property
    def progress(self):
        return self._progress if not self.has_finished else self.max
    
    @progress.setter
    def progress(self, value):
        self._progress = value
    
    def notify_listeners(self, data):
        for l in self.listeners:
            l.notify(data)
        
    def notify(self, data):
        self.buffer.append(data)
    
    def run(self):
        while not self.has_finished:
            try:
                data = self.next
                if not data:
                    continue
                processed = self.process(data)
                if not isinstance(processed, list):
                    processed = [processed]
                
                self.notify_listeners(processed)
            
            except Exception as e:
                self.exception = e
                print(e)
                self.exception_count += 1
            self.progress += 1
    
    @abstractmethod
    def process(self, data):
        #Should return a list of dicts
        pass

class SQLEngine:
    _URL = 'postgresql://postgres@localhost:5432/postgres'
    _engine = None
    
    @staticmethod
    def get():
        if SQLEngine._engine is None:
            SQLEngine._engine = sqlalchemy.create_engine(SQLEngine._URL)
        return SQLEngine._engine

class SQLThread(threading.Thread, ABC):
    def __init__(self, name, process_thread:ProcessThread):
        super().__init__()
        self.name = name
        self.table_name = name.replace("-", "_")
        self.process_thread = process_thread
        self.process_thread.listeners.append(self)
        self.buffer = []
        self._progress = 0
        self.exception_count = 0
        self._session = None
        self._metadata = sqlalchemy.MetaData()
        self._table = self.define_table(self._metadata)
    
    @property
    def max(self):
        return self.process_thread.max
    
    @property
    def has_finished(self):
        return self.process_thread.has_finished and not len(self.buffer) > 0
    
    @property
    def next(self):
        return self.buffer.pop() if len(self.buffer) > 0 else None
    
    @property
    def progress(self):
        return self._progress if not self.has_finished else self.max
    
    @progress.setter
    def progress(self, value):
        self._progress = value
    
    def notify(self, data):
        self.buffer.append(data)
    
    def connect(self):
        engine = SQLEngine.get()
        session = sessionmaker(bind=engine)
        self._session = session()
    
    def close(self):
        self._session.close()
    
    def run(self):
        self.connect()
        self.create_sql()
        
        while not self.has_finished:
            try:
                data = self.next
                if not data:
                    continue
                for d in data:
                    self.insert_sql(d)
                self.commit()
            except:
                self.exception_count += 1
            self.progress += 1

    
    @abstractmethod
    def define_table(self, metadata:sqlalchemy.MetaData) -> sqlalchemy.Table:
        pass
    
    def create_sql(self):
        self._metadata.create_all(SQLEngine.get())
    
    def insert_sql(self, d):
        self._session.execute(self._table.insert(), d if isinstance(d, list) else [d])

    def commit(self):
        self._session.commit()
    
class AbilityProcessThread(ProcessThread):
    def __init__(self, fetch_thread:FetchThread):
        super().__init__("ability", fetch_thread)
    
    def process(self, data):
        #Ignoring effect_changes
        #Ignoring is_nain_series
        #Ignoring pokemon
        
        pokemon_dict = {}
        
        #Effect
        pokemon_dict['effect'] = "No description."
        pokemon_dict['short_effect'] = "No description."
        for l in data['effect_entries']:
            if l['language']['name'] == "en":
                pokemon_dict['effect'] = l['effect']
                pokemon_dict['short_effect'] = l['short_effect']
        
        #Description
        pokemon_dict['description'] = "No description."
        for l in data['flavor_text_entries']:
            if l['language']['name'] == "en":
                pokemon_dict['description'] = l['flavor_text']
        
        #Generation
        pokemon_dict['generation'] = Data.get_url_index(data['generation']['url'])
        
        #ID
        pokemon_dict['id'] = data['id']
        
        #Name
        pokemon_dict['name'] = data['name']
        for l in data['names']:
            if l['language']['name'] == "en":
                pokemon_dict['name'] = l['name']
        
        return pokemon_dict

class MoveProcessThread(ProcessThread):
    def __init__(self, fetch_thread:FetchThread):
        super().__init__("move", fetch_thread)
    
    def process(self, data):
        #Ignoring contest_combos
        #Ignoring contest_effect
        #Ignoring contest_type
        #Ignoring effect_chance
        #Ignoring effect_changes
        #Ignoring effect_entries
        #Ignoring flavor_text_entries
        #Ignoring learned_by_pokemon
        #Ignoring machines
        #Ignoring past_values
        #Ignoring super_contest_effect
        #Ignoring stat_changes
        
        pokemon_dict = {}
    
        #Accuracy
        pokemon_dict['accuracy'] = data['accuracy']
        
        #Damage class
        pokemon_dict['damage_class'] = data['damage_class']['name']
        
        #Effect
        pokemon_dict['effect_chance'] = data['effect_chance']
        
        #Generation
        pokemon_dict['generation'] = Data.get_url_index(data['generation']['url'])
        
        #ID
        pokemon_dict['id'] = data['id']
        
        #Ailment
        pokemon_dict['ailment'] = (data['meta']['ailment']['name'] if data['meta']['ailment'] else None) if data['meta'] else None
        pokemon_dict['ailment_chance'] = data['meta']['ailment_chance'] if data['meta'] else None
        
        #Meta
        for key in ['crit_rate', 'drain', 'flinch_chance', 'healing', 'max_hits', 'max_turns', 'min_hits', 'min_turns', 'stat_chance']:
            pokemon_dict[key] = data['meta'][key]
        
        #Name
        pokemon_dict['name'] = data['name']
        for l in data['names']:
            if l['language']['name'] == "en":
                pokemon_dict['name'] = l['name']
        
        #Power
        pokemon_dict['power'] = data['power']
        
        #PP
        pokemon_dict['pp'] = data['pp']
        
        #Priority
        pokemon_dict['priority'] = data['priority']
        
        #Target
        pokemon_dict['target'] = data['target']['name']
    
        #Type
        pokemon_dict['type'] = data['type']['name']
        
        #Description
        pokemon_dict['description'] = "No description."
        for l in data['flavor_text_entries']:
            if l['language']['name'] == "en":
                pokemon_dict['descriprion'] = l['flavor_text']
        
        return pokemon_dict

class PokemonSpeciesProcessThread(ProcessThread):
    def __init__(self, fetch_thread:FetchThread):
        super().__init__("pokemon-species", fetch_thread)
    
    def process(self, data):
        #Needs species
        #Needs evolution-chain
        #Needs shape (optional)
        
        #Ignoring flavor_text_entries
        #Ignoring form_descriptions
        #Ignoring forms_switchable
        #Ignoring has_gender_differences
        #Ignoring pal_park_encounters
        
        #Simplified pokémon numbers
        
        pokemon_dict = {}
        
        for key in ['base_happiness', 'capture_rate', 'gender_rate', 'hatch_counter', 'id', 'order', 'is_baby', 'is_legendary', 'is_mythical']:
            pokemon_dict[key] = data[key]
        
        for key in ['color', 'growth_rate', 'habitat', 'shape']:
            pokemon_dict[key] = data[key]['name'].replace("-", " ") if data[key] else None
        
        #Egg groups
        pokemon_dict['egg_group'] = str([g['name'] for g in data['egg_groups']]) if data['egg_groups'] else None
        
        #Genera
        pokemon_dict['genera'] = ""
        for l in data['genera']:
            if l['language']['name'] == 'en':
                pokemon_dict['genera'] = l['genus']
        
        #Generation
        pokemon_dict['generation'] = Data.get_url_index(data['generation']['url'])
        
        #Name
        try:
            pokemon_dict['name'] = data['name']
            for l in data['names']:
                if l['language']['name'] == 'en':
                    pokemon_dict['name'] = l['name']
        except:
            pass
        
        #National Pokédex number
        try:
            pokemon_dict['national_pokedex_number'] = -1
            for l in data['pokedex_numbers']:
                if l['pokedex']['name'] == 'national':
                    pokemon_dict['national_pokedex_number'] = l['entry_number']
        except:
            pass
       
        #Varieties
        try:
            pokemon_dict['varieties'] = ""
            for i, s in enumerate([Data.get_url_index(v['pokemon']['url']) for v in data['varieties']]):
                pokemon_dict['varieties'] += str(s)
                if i > 0:
                    pokemon_dict['varieties'] += ", "
            pokemon_dict['varieties'] = "[" + pokemon_dict['varieties'] + "]"
        except:
            pass
        
        #Description
        pokemon_dict['description'] = "No description."
        try:
            for l in data['flavor_text_entries']:
                if l['language']['name'] == "en":
                    pokemon_dict['description'] = l['flavor_text']
        except:
            pass

        return pokemon_dict

class PokemonProcessThread(ProcessThread):
    def __init__(self, fetch_thread:FetchThread):
        super().__init__("pokemon", fetch_thread)
    
    def process(self, data):
        #Needs abilities
        #Needs move
        #Needs pokemon-species
        
        #Relation move
        
        #Ignoring forms
        #Ignoring game_indices
        #Ignoring held_items
        #Ignoring location_area_encounters
        #Ignoring past_abilities
        #Ignoring past_types
        
        pokemon_dict = {}
        
        #Abilities
        pokemon_dict['primary_ability'] = -1
        pokemon_dict['secondary_ability'] = -1
        pokemon_dict['hidden_ability'] = -1
        ability_keys = ['', 'primary_ability', 'secondary_ability', 'hidden_ability']
        for a in data['abilities']:
            value = Data.get_url_index(a['ability']['url'])
            key = ability_keys[a['slot']]
            pokemon_dict[key] = value
        
        for key in ['base_experience', 'height', 'weight', 'id', 'order', 'name']:
            pokemon_dict[key] = data[key]
        
        for side in ['front', 'back']:
            for sp in ['default', 'female', 'shiny_female', 'shiny']:
                pokemon_dict['sprite_' + side + '_' + sp] = data['sprites'][side + '_' + sp]
        
        #Cries
        pokemon_dict['cry'] = data['cries']['latest']
        pokemon_dict['cry_legacy'] = data['cries']['legacy']
        
        #Species
        pokemon_dict['species'] = Data.get_url_index(data['species']['url'])
    
        #Stats
        for stat in data['stats']:
            key = stat['stat']['name'].replace("-", "_")
            value = stat['base_stat']
            effort = stat['effort']
            pokemon_dict[key] = value
            pokemon_dict[key + '_effort'] = effort
    
        #Types
        pokemon_dict['primary_type'] = data['types'][0]['type']['name'] if len(data['types']) > 0 else None
        pokemon_dict['secondary_type'] = data['types'][1]['type']['name'] if len(data['types']) > 1 else None
    
        return pokemon_dict

class PokemonMoveProcessThread(ProcessThread):
    def __init__(self, fetch_thread:FetchThread):
        super().__init__("pokemon-move", fetch_thread)
    
    def process(self, data):
        #Ignoring effect_changes
        #Ignoring is_nain_series
        #Ignoring pokemon
        
        pokemon_index = data['id']
    
        pokemon_move_list = []
        for move in data['moves']:
            pokemon_dict = {
                'pokemon' : pokemon_index,
                'move' : Data.get_url_index(move['move']['url'])
            }
            
            index = len(move['version_group_details']) - 1
            pokemon_dict['level_learned_at'] = move['version_group_details'][index]['level_learned_at']
            pokemon_dict['learn_method'] = move['version_group_details'][index]['move_learn_method']['name']
        
            pokemon_move_list.append(pokemon_dict)
        
        return pokemon_move_list

class EvolutionChainProcessThread(ProcessThread):
    def __init__(self, fetch_thread:FetchThread):
        super().__init__("evolution-chain", fetch_thread)
    
    def process(self, data, recursion=False):
        if recursion:
            evolution_list = []
            
            for evolution in data['evolves_to']:
                pokemon_dict = {}
                
                pokemon_dict['from'] = Data.get_url_index(data['species']['url'])
                pokemon_dict['to'] = Data.get_url_index(evolution['species']['url'])
                
                if len(evolution['evolution_details']) == 0:
                    for key in ['item', 'held_item', 'known_move_type', 'trigger', 'party_type']:
                       pokemon_dict[key] = None
                     
                    for key in ['gender', 'min_beauty', 'min_happiness', 'min_level', 'needs_overworld_rain', 'time_of_day', 'trade_species', 'turn_upside_down', 'relative_physical_stats']:
                        pokemon_dict[key] = None
                    
                    continue
                else:
                    det = evolution['evolution_details'][0]
                    for key in ['item', 'held_item', 'known_move', 'known_move_type', 'trigger', 'party_species', 'party_type']:
                        pokemon_dict[key] = det[key]['name'] if det[key] else None
                    
                    for key in ['gender', 'min_beauty', 'min_happiness', 'min_level', 'needs_overworld_rain', 'time_of_day', 'turn_upside_down', 'relative_physical_stats']:
                        pokemon_dict[key] = det[key] if det[key] else None
                    
                    for key in ['trade_species', 'known_move', 'party_species']:
                        pokemon_dict[key] = Data.get_url_index(det[key]['url']) if det[key] else None
    
                evolution_list.append(pokemon_dict)
                
                for entry in self.process(evolution, True):
                    evolution_list.append(entry)
            
            return evolution_list
        
        return self.process(data['chain'], recursion=True)

class AbilitySQLThread(SQLThread):
    def __init__(self, process_thread:ProcessThread):
        super().__init__("ability", process_thread)

    def define_table(self, metadata:sqlalchemy.MetaData) -> sqlalchemy.Table:
        return sqlalchemy.Table(
            'ability', metadata,
            sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
            sqlalchemy.Column('name', sqlalchemy.Text),
            sqlalchemy.Column('effect', sqlalchemy.Text),
            sqlalchemy.Column('short_effect', sqlalchemy.Text),
            sqlalchemy.Column('description', sqlalchemy.Text),
            sqlalchemy.Column('generation', sqlalchemy.Integer)
        )
    
class MoveSQLThread(SQLThread):
    def __init__(self, process_thread:ProcessThread):
        super().__init__("move", process_thread)
    
    def define_table(self, metadata:sqlalchemy.MetaData) -> sqlalchemy.Table:
        return sqlalchemy.Table(
            'move', metadata,
            sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
            sqlalchemy.Column('name', sqlalchemy.Text),
            sqlalchemy.Column('accuracy', sqlalchemy.Integer),
            sqlalchemy.Column('damage_class', sqlalchemy.Text),
            sqlalchemy.Column('effect_chance', sqlalchemy.Integer),
            sqlalchemy.Column('generation', sqlalchemy.Integer),
            sqlalchemy.Column('ailment', sqlalchemy.Text),
            sqlalchemy.Column('ailment_chance', sqlalchemy.Integer),
            sqlalchemy.Column('crit_rate', sqlalchemy.Integer),
            sqlalchemy.Column('drain', sqlalchemy.Integer),
            sqlalchemy.Column('flinch_chance', sqlalchemy.Integer),
            sqlalchemy.Column('healing', sqlalchemy.Integer),
            sqlalchemy.Column('max_hits', sqlalchemy.Integer),
            sqlalchemy.Column('max_turns', sqlalchemy.Integer),
            sqlalchemy.Column('min_hits', sqlalchemy.Integer),
            sqlalchemy.Column('min_turns', sqlalchemy.Integer),
            sqlalchemy.Column('stat_chance', sqlalchemy.Integer),
            sqlalchemy.Column('power', sqlalchemy.Integer),
            sqlalchemy.Column('pp', sqlalchemy.Integer),
            sqlalchemy.Column('priority', sqlalchemy.Integer),
            sqlalchemy.Column('target', sqlalchemy.Text),
            sqlalchemy.Column('type', sqlalchemy.Text),
            sqlalchemy.Column('description', sqlalchemy.Text)
        )

class PokemonSQLThread(SQLThread):
    def __init__(self, process_thread:ProcessThread):
        super().__init__("pokemon", process_thread)
    
    def define_table(self, metadata:sqlalchemy.MetaData) -> sqlalchemy.Table:
        return sqlalchemy.Table(
            'pokemon', metadata,
            sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
            sqlalchemy.Column('base_experience', sqlalchemy.Integer),
            sqlalchemy.Column('height', sqlalchemy.Integer),
            sqlalchemy.Column('weight', sqlalchemy.Integer),
            sqlalchemy.Column('order', sqlalchemy.Integer),
            sqlalchemy.Column('primary_ability', sqlalchemy.Integer),
            sqlalchemy.Column('secondary_ability', sqlalchemy.Integer),
            sqlalchemy.Column('hidden_ability', sqlalchemy.Integer),
            sqlalchemy.Column('species', sqlalchemy.Integer, sqlalchemy.ForeignKey('pokemon_species.id')),
            sqlalchemy.Column('hp', sqlalchemy.Integer),
            sqlalchemy.Column('hp_effort', sqlalchemy.Integer),
            sqlalchemy.Column('attack', sqlalchemy.Integer),
            sqlalchemy.Column('attack_effort', sqlalchemy.Integer),
            sqlalchemy.Column('defense', sqlalchemy.Integer),
            sqlalchemy.Column('defense_effort', sqlalchemy.Integer),
            sqlalchemy.Column('special_attack', sqlalchemy.Integer),
            sqlalchemy.Column('special_attack_effort', sqlalchemy.Integer),
            sqlalchemy.Column('special_defense', sqlalchemy.Integer),
            sqlalchemy.Column('special_defense_effort', sqlalchemy.Integer),
            sqlalchemy.Column('speed', sqlalchemy.Integer),
            sqlalchemy.Column('speed_effort', sqlalchemy.Integer),
            sqlalchemy.Column('sprite_front_default', sqlalchemy.Text),
            sqlalchemy.Column('sprite_front_female', sqlalchemy.Text),
            sqlalchemy.Column('sprite_front_shiny_female', sqlalchemy.Text),
            sqlalchemy.Column('sprite_front_shiny', sqlalchemy.Text),
            sqlalchemy.Column('sprite_back_default', sqlalchemy.Text),
            sqlalchemy.Column('sprite_back_female', sqlalchemy.Text),
            sqlalchemy.Column('sprite_back_shiny_female', sqlalchemy.Text),
            sqlalchemy.Column('sprite_back_shiny', sqlalchemy.Text),
            sqlalchemy.Column('cry', sqlalchemy.Text),
            sqlalchemy.Column('cry_legacy', sqlalchemy.Text),
            sqlalchemy.Column('name', sqlalchemy.Text),
            sqlalchemy.Column('primary_type', sqlalchemy.Text),
            sqlalchemy.Column('secondary_type', sqlalchemy.Text)
        )

class PokemonSpeciesSQLThread(SQLThread):
    def __init__(self, process_thread:ProcessThread):
        super().__init__("pokemon-species", process_thread)
    
    def define_table(self, metadata:sqlalchemy.MetaData) -> sqlalchemy.Table:
        return sqlalchemy.Table(
            'pokemon_species', metadata,
            sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
            sqlalchemy.Column('base_happiness', sqlalchemy.Integer),
            sqlalchemy.Column('capture_rate', sqlalchemy.Integer),
            sqlalchemy.Column('gender_rate', sqlalchemy.Integer),
            sqlalchemy.Column('hatch_counter', sqlalchemy.Integer),
            sqlalchemy.Column('order', sqlalchemy.Integer),
            sqlalchemy.Column('generation', sqlalchemy.Integer),
            sqlalchemy.Column('national_pokedex_number', sqlalchemy.Integer),
            sqlalchemy.Column('is_baby', sqlalchemy.Boolean),
            sqlalchemy.Column('is_legendary', sqlalchemy.Boolean),
            sqlalchemy.Column('is_mythical', sqlalchemy.Boolean),
            sqlalchemy.Column('color', sqlalchemy.Text),
            sqlalchemy.Column('growth_rate', sqlalchemy.Text),
            sqlalchemy.Column('habitat', sqlalchemy.Text),
            sqlalchemy.Column('shape', sqlalchemy.Text),
            sqlalchemy.Column('genera', sqlalchemy.Text),
            sqlalchemy.Column('name', sqlalchemy.Text),
            sqlalchemy.Column('egg_group', sqlalchemy.Text),
            sqlalchemy.Column('varieties', sqlalchemy.Text),
            sqlalchemy.Column('description', sqlalchemy.Text)
        )

class PokemonMoveSQLThread(SQLThread):
    def __init__(self, process_thread:ProcessThread):
        super().__init__("pokemon-move", process_thread)
    
    def define_table(self, metadata:sqlalchemy.MetaData) -> sqlalchemy.Table:
        return sqlalchemy.Table(
            'pokemon_move', metadata,
            sqlalchemy.Column('pokemon', sqlalchemy.Integer, sqlalchemy.ForeignKey('pokemon.id')),
            sqlalchemy.Column('move', sqlalchemy.Integer, sqlalchemy.ForeignKey('move.id')),
            sqlalchemy.Column('level_learned_at', sqlalchemy.Integer),
            sqlalchemy.Column('learn_method', sqlalchemy.Text)
        )

class EvolutionChainSQLThread(SQLThread):
    def __init__(self, process_thread:ProcessThread):
        super().__init__("evolution-chain", process_thread)
    
    def define_table(self, metadata:sqlalchemy.MetaData) -> sqlalchemy.Table:
        return sqlalchemy.Table(
            'evolution_chain', metadata,
            sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
            sqlalchemy.Column('"from"', sqlalchemy.Integer, sqlalchemy.ForeignKey('pokemon.id')),
            sqlalchemy.Column('"to"', sqlalchemy.Integer, sqlalchemy.ForeignKey('pokemon.id')),
            sqlalchemy.Column('gender', sqlalchemy.Integer),
            sqlalchemy.Column('min_beauty', sqlalchemy.Integer),
            sqlalchemy.Column('min_happiness', sqlalchemy.Integer),
            sqlalchemy.Column('min_level', sqlalchemy.Integer),
            sqlalchemy.Column('trade_species', sqlalchemy.Text),
            sqlalchemy.Column('relative_physical_stats', sqlalchemy.Integer),
            sqlalchemy.Column('item', sqlalchemy.Text),
            sqlalchemy.Column('held_item', sqlalchemy.Text),
            sqlalchemy.Column('known_move', sqlalchemy.Text),
            sqlalchemy.Column('known_move_type', sqlalchemy.Text),
            sqlalchemy.Column('trigger', sqlalchemy.Text),
            sqlalchemy.Column('party_species', sqlalchemy.Text),
            sqlalchemy.Column('party_type', sqlalchemy.Text),
            sqlalchemy.Column('time_of_day', sqlalchemy.Text),
            sqlalchemy.Column('needs_overworld_rain', sqlalchemy.Boolean),
            sqlalchemy.Column('turn_upside_down', sqlalchemy.Boolean)
        )

class ThreadPool(threading.Thread):
    def __init__(self, print_coordinates = (0, 0), update_time:float = 0.2, fancy_print = False):
        super().__init__()
        
        self.threads = []
        
        ability_fetch_thread = FetchThread("ability")
        self.threads.append(ability_fetch_thread)
        
        ability_process_thread = AbilityProcessThread(ability_fetch_thread)
        self.threads.append(ability_process_thread)
        
        move_fetch_thread = FetchThread("move")
        self.threads.append(move_fetch_thread)
        
        move_process_thread = MoveProcessThread(move_fetch_thread)
        self.threads.append(move_process_thread)
        
        pokemon_fetch_thread = FetchThread("pokemon")
        self.threads.append(pokemon_fetch_thread)
        
        pokemon_process_thread = PokemonProcessThread(pokemon_fetch_thread)
        self.threads.append(pokemon_process_thread)
        
        pokemon_move_process_thread = PokemonMoveProcessThread(pokemon_fetch_thread)
        self.threads.append(pokemon_move_process_thread)
        
        pokemon_species_fetch_thread = FetchThread("pokemon-species")
        self.threads.append(pokemon_species_fetch_thread)
        
        pokemon_species_process_thread = PokemonSpeciesProcessThread(pokemon_species_fetch_thread)
        self.threads.append(pokemon_species_process_thread)
        
        evolution_chain_fetch_thread = FetchThread("evolution-chain")
        self.threads.append(evolution_chain_fetch_thread)
        
        evolution_chain_process_thread = EvolutionChainProcessThread(evolution_chain_fetch_thread)
        self.threads.append(evolution_chain_process_thread)

        ability_sql_thread = AbilitySQLThread(ability_process_thread)
        self.threads.append(ability_sql_thread)

        move_sql_thread = MoveSQLThread(move_process_thread)
        self.threads.append(move_sql_thread)

        pokemon_sql_thread = PokemonSQLThread(pokemon_process_thread)
        self.threads.append(pokemon_sql_thread)

        pokemon_species_sql_thread = PokemonSpeciesSQLThread(pokemon_species_process_thread)
        self.threads.append(pokemon_species_sql_thread)

        pokemon_move_sql_thread = PokemonMoveSQLThread(pokemon_move_process_thread)
        self.threads.append(pokemon_move_sql_thread)

        evolution_chain_sql_thread = EvolutionChainSQLThread(evolution_chain_process_thread)
        self.threads.append(evolution_chain_sql_thread)
        
        self.print_x, self.print_y = print_coordinates
        
        self.update_time = update_time
        self.fancy_print = fancy_print
    
    def get_strings(self) -> list[str]:
        names = []
        for thread in self.threads:
            string = ""
            if isinstance(thread, FetchThread):
                string += "Fetch "
            if isinstance(thread, ProcessThread):
                string += "Process "
            if isinstance(thread, SQLThread):
                string += "SQL "
            
            string += f'Thread {thread.name}'
            names.append(string)
        
        output = []
        
        longest = max([len(name) for name in names])
        for i in range(len(self.threads)):
            thread = self.threads[i]
            name = names[i]
            spaces = longest - len(name) + 1
            
            string = name
            for i in range(spaces):
                string += " "
            
            for i in range(30):
                if thread.progress * 30.0 / thread.max >= i + 1:
                    string += "="
                else:
                    string += "-"
                
            string += f' {thread.progress} / {thread.max}' if not thread.has_finished else f' Finished {thread.max}'
            if thread.exception_count > 0:
                string += f' ({thread.exception_count} exception{"s" if thread.exception_count > 1 else ""})'
            output.append(string + "                ")
        
        return output
    
    @property
    def has_finished(self) -> bool:
        for thread in self.threads:
            if not thread.has_finished:
                return False
        return True
    
    def print(self, string, x, y):
        print(f"\033[{y};{x}H{string}")
    
    def run(self):
        for thread in self.threads:
            thread.start()
        
        while not self.has_finished:
            strings = self.get_strings()
            if self.fancy_print:
                for i in range(self.print_y - 1):
                    print()
                space = ""
                for i in range(self.print_x):
                    space += " "
                print(space)
                
                for i, string in enumerate(strings):
                    self.print(string, self.print_x, self.print_y + i + 1)
            else:
                for string in strings:
                    print(string)
            time.sleep(self.update_time)
        for i in self.threads:
            if isinstance(i, SQLThread):
                i.commit()

pool = ThreadPool(update_time=1, fancy_print=True)
pool.start()
pool.join()
print("Done")