from __future__ import annotations
import sys
import os
import zipfile
import shutil
import subprocess
import urllib.request
import sqlalchemy
from sqlalchemy import create_engine, text
from typing import Dict, Any, Optional
import requests
import threading

class PostgreSQLLinux:
    @staticmethod
    def is_installed() -> bool:
      try:
        subprocess.check_call(["psql", "--version"])
        return True
      except FileNotFoundError:
        return False
    
    # Install to posgresql folder
    @staticmethod
    def install() -> None:
      print("Checking if PostgreSQL is installed...")
      try:
        subprocess.check_call(["psql", "--version"])
        print("PostgreSQL is already installed.")
      except FileNotFoundError:
        print("PostgreSQL is not installed. Installing...")
        subprocess.check_call(["sudo", "apt-get", "install", "-y", "postgresql", "postgresql-contrib"])
        print("PostgreSQL installation complete.")

    @staticmethod
    def is_initialized() -> bool:
        db_dir = os.path.abspath("Database")
        return os.path.isfile(os.path.join(db_dir, "PG_VERSION"))

    @staticmethod
    def create_db() -> None:
      """
      Initialize the database.
      """
      
      subprocess.check_call(["mkdir", "-p", "Database"])
      subprocess.check_call(["sudo", "initdb", "-D", os.path.abspath("Database"), "--username=postgres", "--encoding=UTF8", "--no-locale"])
      print("PostgreSQL database initialized at:", os.path.abspath("Database"))
      print("You can now start the PostgreSQL server with 'pg_ctl -D Database start'.")

    @staticmethod
    def run() -> None:
        db_dir = os.path.abspath("Database")
        print("Starting PostgreSQL server...")
        subprocess.check_call([
            "pg_ctl",
            "-D", db_dir,
            "-l", os.path.join(db_dir, "logfile.txt"),
            "start"
        ])
        print("PostgreSQL server started.")

    @staticmethod
    def stop() -> None:
        db_dir = os.path.abspath("Database")
        print("Stopping PostgreSQL server...")
        subprocess.check_call([
            "pg_ctl",
            "-D", db_dir,
            "stop",
            "-m", "immediate"
        ])
        print("PostgreSQL server stopped.")

    @staticmethod
    def create_engine():
        return create_engine('postgresql+psycopg2://postgres@localhost:5432/postgres', echo=False)

    @staticmethod
    def fetch_and_insert_pokemon_data():
        engine = PostgreSQLLinux.create_engine()
        with engine.connect() as conn:
            print("Creating tables if they do not exist...")
            conn.execute(text(Ability.create_table_sql()))
            conn.execute(text(PokemonSpecies.create_table_sql()))
            conn.execute(text(Pokemon.create_table_sql()))
            print("Tables created.")

            print("Fetching and inserting abilities...")
            for i, ability in enumerate(Ability.read(), 1):
                sql, params = ability.insert_sql()
                conn.execute(text(sql), params)
                if i % 50 == 0:
                    print(f"Inserted {i} abilities...")

            print("Fetching and inserting species...")
            for i, species in enumerate(PokemonSpecies.read(), 1):
                sql, params = species.insert_sql()
                conn.execute(text(sql), params)
                if i % 50 == 0:
                    print(f"Inserted {i} species...")

            print("Fetching and inserting pokemon...")
            for i, pokemon in enumerate(Pokemon.read(), 1):
                sql, params = pokemon.insert_sql()
                conn.execute(text(sql), params)
                if i % 50 == 0:
                    print(f"Inserted {i} pokemon...")

            conn.commit()
            print("Database commit complete.")

    @staticmethod
    def uninstall():
        db_dir = os.path.abspath("Database")
        print("Stopping PostgreSQL server if running...")
        try:
            subprocess.check_call([
                "pg_ctl",
                "-D", db_dir,
                "stop",
                "-m", "immediate"
            ])
            print("Server stopped.")
        except Exception as e:
            print("Could not stop server or it wasn't running:", e)

        if os.path.exists(db_dir):
            print(f"Removing database directory: {db_dir}")
            shutil.rmtree(db_dir)

class PostgreSQLWindows:
  @staticmethod
  def is_installed() -> bool:
    for path in os.environ["PATH"].split(os.pathsep):
      exe_file = os.path.join(path, "psql.exe")
      if os.path.isfile(exe_file):
        return True
    return False
  
  @staticmethod
  def install() -> None:
    # Configuration
    POSTGRESQL_VERSION = "16.2-1"
    POSTGRESQL_URL = f"https://get.enterprisedb.com/postgresql/postgresql-{POSTGRESQL_VERSION}-windows-x64-binaries.zip"
    DOWNLOAD_PATH = "postgresql.zip"
    UNPACK_DIR = "postgresql"

    # Download PostgreSQL binaries
    print("Downloading PostgreSQL...")
    urllib.request.urlretrieve(POSTGRESQL_URL, DOWNLOAD_PATH)
    print("Download complete.")

    # Unpack the zip file
    print("Unpacking...")
    with zipfile.ZipFile(DOWNLOAD_PATH, 'r') as zip_ref:
      zip_ref.extractall(UNPACK_DIR)
    print("Unpack complete.")

    # Clean up zip file
    os.remove(DOWNLOAD_PATH)
    print("Cleanup complete. PostgreSQL is unpacked in:", os.path.abspath(UNPACK_DIR))
    
    # Remove unnecessary folders (e.g., pgAdmin, StackBuilder, symbols)
    unneeded_dirs = [
      "pgAdmin 4",
      "StackBuilder",
      "symbols",
      "doc",
      "include",
      "pgAdmin4",
      "pgadmin4",
      "pgadmin",
      "pgadmin 4"
    ]
    for dirname in unneeded_dirs:
      dirpath = os.path.join(UNPACK_DIR, dirname)
      if os.path.isdir(dirpath):
        print(f"Removing unnecessary folder: {dirpath}")

  @staticmethod
  def is_initialized():
    UNPACK_DIR = "postgresql"
    DB_DIR = os.path.abspath("Database")
    PG_VERSION_FILE = os.path.join(DB_DIR, "PG_VERSION")
    return os.path.isfile(PG_VERSION_FILE)
  
  @staticmethod
  def create_db() -> None:
    UNPACK_DIR = "postgresql"
    DB_DIR = os.path.abspath("Database")
    BIN_DIR = os.path.join(UNPACK_DIR, "pgsql", "bin")
    INITDB_PATH = os.path.join(BIN_DIR, "initdb.exe")

    if not os.path.exists(DB_DIR):
      os.makedirs(DB_DIR)

    print("Initializing new PostgreSQL database cluster...")
    subprocess.check_call([
      INITDB_PATH,
      "-D", DB_DIR,
      "--username=postgres",
      "--encoding=UTF8",
      "--no-locale"
    ])
    print("Database initialized at:", DB_DIR)
  
  @staticmethod
  def run() -> None:
    UNPACK_DIR = "postgresql"
    DB_DIR = os.path.abspath("Database")
    BIN_DIR = os.path.join(UNPACK_DIR, "pgsql", "bin")
    PG_CTL_PATH = os.path.join(BIN_DIR, "pg_ctl.exe")

    print("Starting PostgreSQL server...")
    subprocess.check_call([
      PG_CTL_PATH,
      "-D", DB_DIR,
      "-l", os.path.join(DB_DIR, "logfile.txt"),
      "start"
    ])
    print("PostgreSQL server started.")

  @staticmethod
  def stop() -> None:
    UNPACK_DIR = "postgresql"
    DB_DIR = os.path.abspath("Database")
    BIN_DIR = os.path.join(UNPACK_DIR, "pgsql", "bin")
    PG_CTL_PATH = os.path.join(BIN_DIR, "pg_ctl.exe")

    print("Stopping PostgreSQL server...")
    subprocess.check_call([
      PG_CTL_PATH,
      "-D", DB_DIR,
      "stop",
      "-m", "immediate"
    ])
    print("PostgreSQL server stopped.")
    
  @staticmethod
  def create_engine():
    DB_DIR = os.path.abspath("Database")
    engine = create_engine(f'postgresql+psycopg2://postgres@localhost:5432/postgres', echo=False)
    return engine
  
  @staticmethod
  def fetch_and_insert_pokemon_data():
    engine = PostgreSQL.create_engine()
    with engine.connect() as conn:
      print("Creating tables if they do not exist...")
      conn.execute(text(Ability.create_table_sql()))
      conn.execute(text(PokemonSpecies.create_table_sql()))
      conn.execute(text(Pokemon.create_table_sql()))
      print("Tables created.")

      print("Fetching abilities from API...")
      abilities = Ability.read()
      print(f"Fetched {len(abilities)} abilities. Inserting into database...")
      for i, ability in enumerate(abilities, 1):
        sql, params = ability.insert_sql()
        conn.execute(text(sql), params)
        if i % 50 == 0:
          print(f"Inserted {i} abilities...")
      print("All abilities inserted.")

      print("Fetching pokemon species from API...")
      species_list = PokemonSpecies.read()
      print(f"Fetched {len(species_list)} species. Inserting into database...")
      for i, species in enumerate(species_list, 1):
        sql, params = species.insert_sql()
        conn.execute(text(sql), params)
        if i % 50 == 0:
          print(f"Inserted {i} species...")
      print("All species inserted.")

      print("Fetching pokemon from API...")
      pokemons = Pokemon.read()
      print(f"Fetched {len(pokemons)} pokemon. Inserting into database...")
      for i, pokemon in enumerate(pokemons, 1):
        sql, params = pokemon.insert_sql()
        conn.execute(text(sql), params)
        if i % 50 == 0:
          print(f"Inserted {i} pokemon...")
      print("All pokemon inserted.")

      conn.commit()
      print("Database commit complete.")
  
  @staticmethod
  def uninstall():
    # Stop PostgreSQL server if running
    UNPACK_DIR = "postgresql"
    DB_DIR = os.path.abspath("Database")
    BIN_DIR = os.path.join(UNPACK_DIR, "pgsql", "bin")
    PG_CTL_PATH = os.path.join(BIN_DIR, "pg_ctl.exe")

    if os.path.exists(DB_DIR):
      try:
        print("Stopping PostgreSQL server...")
        subprocess.check_call([
          PG_CTL_PATH,
          "-D", DB_DIR,
          "stop",
          "-m", "immediate"
        ])
        print("PostgreSQL server stopped.")
      except Exception as e:
        print("Could not stop PostgreSQL server (it may not be running):", e)

    # Remove database directory
    if os.path.exists(DB_DIR):
      print(f"Removing database directory: {DB_DIR}")
      shutil.rmtree(DB_DIR)

    # Remove PostgreSQL binaries directory
    if os.path.exists(UNPACK_DIR):
      print(f"Removing PostgreSQL binaries directory: {os.path.abspath(UNPACK_DIR)}")
      shutil.rmtree(UNPACK_DIR)

PostgreSQL = PostgreSQLWindows if sys.platform.startswith('win') else PostgreSQLLinux

class Data:
  @staticmethod
  def get_url_index(url:str):
    segments = url.rstrip('/').split('/')
    
    return int(segments[-1])
      
  @staticmethod
  def fetch_json(name:str, id:int|None=None):
    url = f'https://pokeapi.co/api/v2/{name}'
    if id is None:
      url = url + "?limit=100000&offset=0"
    else:
      url = url + f'/{id}/'

    response = requests.get(url)

    data = response.json()

    return data

class PokemonSpecies:
  def __init__(self, id: int, base_happiness: int, capture_rate: int, gender_rate: int, hatch_counter: int,
          order: int, generation: int, national_pokedex_number: int, is_baby: bool, is_legendary: bool,
          is_mythical: bool, color: str, growth_rate: str, habitat: str, shape: str, genera: str, name: str,
          egg_group: str, varieties: str, description: str):
    self.id = id
    self.base_happiness = base_happiness
    self.capture_rate = capture_rate
    self.gender_rate = gender_rate
    self.hatch_counter = hatch_counter
    self.order = order
    self.generation = generation
    self.national_pokedex_number = national_pokedex_number
    self.is_baby = is_baby
    self.is_legendary = is_legendary
    self.is_mythical = is_mythical
    self.color = color
    self.growth_rate = growth_rate
    self.habitat = habitat
    self.shape = shape
    self.genera = genera
    self.name = name
    self.egg_group = egg_group
    self.varieties = varieties
    self.description = description

  @staticmethod
  def create_table_sql() -> str:
    return """
    CREATE TABLE IF NOT EXISTS pokemon_species (
      id INTEGER PRIMARY KEY,
      base_happiness INTEGER,
      capture_rate INTEGER,
      gender_rate INTEGER,
      hatch_counter INTEGER,
      "order" INTEGER,
      generation INTEGER,
      national_pokedex_number INTEGER,
      is_baby BOOLEAN,
      is_legendary BOOLEAN,
      is_mythical BOOLEAN,
      color TEXT,
      growth_rate TEXT,
      habitat TEXT,
      shape TEXT,
      genera TEXT,
      name TEXT,
      egg_group TEXT,
      varieties TEXT,
      description TEXT
    );
    """

  def insert_sql(self) -> tuple[str, Dict[str, Any]]:
    return (
      "INSERT INTO pokemon_species (id, base_happiness, capture_rate, gender_rate, hatch_counter, \"order\", generation, national_pokedex_number, is_baby, is_legendary, is_mythical, color, growth_rate, habitat, shape, genera, name, egg_group, varieties, description) VALUES (:id, :base_happiness, :capture_rate, :gender_rate, :hatch_counter, :order, :generation, :national_pokedex_number, :is_baby, :is_legendary, :is_mythical, :color, :growth_rate, :habitat, :shape, :genera, :name, :egg_group, :varieties, :description);",
      self.__dict__
    )

  @staticmethod
  def from_json(json:str) -> PokemonSpecies:
    pokemon_dict = {}
    
    for key in ['base_happiness', 'capture_rate', 'gender_rate', 'hatch_counter', 'id', 'order', 'is_baby', 'is_legendary', 'is_mythical']:
      pokemon_dict[key] = json[key]
    
    for key in ['color', 'growth_rate', 'habitat', 'shape']:
      pokemon_dict[key] = json[key]['name'].replace("-", " ") if json[key] else None
    
    #Egg groups
    pokemon_dict['egg_group'] = str([g['name'] for g in json['egg_groups']]) if json['egg_groups'] else None
    
    #Genera
    pokemon_dict['genera'] = ""
    for l in json['genera']:
      if l['language']['name'] == 'en':
        pokemon_dict['genera'] = l['genus']
    
    #Generation
    pokemon_dict['generation'] = Data.get_url_index(json['generation']['url'])
    
    #Name
    try:
      pokemon_dict['name'] = json['name']
      for l in json['names']:
        if l['language']['name'] == 'en':
          pokemon_dict['name'] = l['name']
    except:
      pass
    
    #National Pokédex number
    try:
      pokemon_dict['national_pokedex_number'] = -1
      for l in json['pokedex_numbers']:
        if l['pokedex']['name'] == 'national':
          pokemon_dict['national_pokedex_number'] = l['entry_number']
    except:
      pass
    
    #Varieties
    try:
      pokemon_dict['varieties'] = ""
      for i, s in enumerate([Data.get_url_index(v['pokemon']['url']) for v in json['varieties']]):
        pokemon_dict['varieties'] += str(s)
        if i > 0:
          pokemon_dict['varieties'] += ", "
      pokemon_dict['varieties'] = "[" + pokemon_dict['varieties'] + "]"
    except:
      pass
    
    #Description
    pokemon_dict['description'] = "No description."
    try:
      for l in json['flavor_text_entries']:
        if l['language']['name'] == "en":
          pokemon_dict['description'] = l['flavor_text']
    except:
      pass

    return PokemonSpecies(
      id=pokemon_dict.get('id'),
      base_happiness=pokemon_dict.get('base_happiness'),
      capture_rate=pokemon_dict.get('capture_rate'),
      gender_rate=pokemon_dict.get('gender_rate'),
      hatch_counter=pokemon_dict.get('hatch_counter'),
      order=pokemon_dict.get('order'),
      generation=pokemon_dict.get('generation'),
      national_pokedex_number=pokemon_dict.get('national_pokedex_number'),
      is_baby=pokemon_dict.get('is_baby'),
      is_legendary=pokemon_dict.get('is_legendary'),
      is_mythical=pokemon_dict.get('is_mythical'),
      color=pokemon_dict.get('color'),
      growth_rate=pokemon_dict.get('growth_rate'),
      habitat=pokemon_dict.get('habitat'),
      shape=pokemon_dict.get('shape'),
      genera=pokemon_dict.get('genera'),
      name=pokemon_dict.get('name'),
      egg_group=pokemon_dict.get('egg_group'),
      varieties=pokemon_dict.get('varieties'),
      description=pokemon_dict.get('description')
    )
    
  @staticmethod
  def read() -> list[PokemonSpecies]:
    url = "https://pokeapi.co/api/v2/pokemon-species?limit=100000"
    response = requests.get(url)
    results = response.json().get("results", [])
    
    rows = []
    for entry in results:
      row_url = entry.get("url")
      if not row_url:
        continue
      row_json = requests.get(row_url).json()
      rows.append(PokemonSpecies.from_json(row_json))
    return rows

class Pokemon:
  def __init__(self, id: int, base_experience: int, height: int, weight: int, order: int, primary_ability: int,
          secondary_ability: int, hidden_ability: int, species: int, hp: int, hp_effort: int, attack: int,
          attack_effort: int, defense: int, defense_effort: int, special_attack: int, special_attack_effort: int,
          special_defense: int, special_defense_effort: int, speed: int, speed_effort: int,
          sprite_front_default: str, sprite_front_female: str, sprite_front_shiny_female: str,
          sprite_front_shiny: str, sprite_back_default: str, sprite_back_female: str,
          sprite_back_shiny_female: str, sprite_back_shiny: str, cry: str, cry_legacy: str, name: str,
          primary_type: str, secondary_type: str):
    self.id = id
    self.base_experience = base_experience
    self.height = height
    self.weight = weight
    self.order = order
    self.primary_ability = primary_ability
    self.secondary_ability = secondary_ability
    self.hidden_ability = hidden_ability
    self.species = species
    self.hp = hp
    self.hp_effort = hp_effort
    self.attack = attack
    self.attack_effort = attack_effort
    self.defense = defense
    self.defense_effort = defense_effort
    self.special_attack = special_attack
    self.special_attack_effort = special_attack_effort
    self.special_defense = special_defense
    self.special_defense_effort = special_defense_effort
    self.speed = speed
    self.speed_effort = speed_effort
    self.sprite_front_default = sprite_front_default
    self.sprite_front_female = sprite_front_female
    self.sprite_front_shiny_female = sprite_front_shiny_female
    self.sprite_front_shiny = sprite_front_shiny
    self.sprite_back_default = sprite_back_default
    self.sprite_back_female = sprite_back_female
    self.sprite_back_shiny_female = sprite_back_shiny_female
    self.sprite_back_shiny = sprite_back_shiny
    self.cry = cry
    self.cry_legacy = cry_legacy
    self.name = name
    self.primary_type = primary_type
    self.secondary_type = secondary_type

  @staticmethod
  def create_table_sql() -> str:
    return """
    CREATE TABLE IF NOT EXISTS pokemon (
      id INTEGER PRIMARY KEY,
      base_experience INTEGER,
      height INTEGER,
      weight INTEGER,
      "order" INTEGER,
      primary_ability INTEGER,
      secondary_ability INTEGER,
      hidden_ability INTEGER,
      species INTEGER REFERENCES pokemon_species(id),
      hp INTEGER,
      hp_effort INTEGER,
      attack INTEGER,
      attack_effort INTEGER,
      defense INTEGER,
      defense_effort INTEGER,
      special_attack INTEGER,
      special_attack_effort INTEGER,
      special_defense INTEGER,
      special_defense_effort INTEGER,
      speed INTEGER,
      speed_effort INTEGER,
      sprite_front_default TEXT,
      sprite_front_female TEXT,
      sprite_front_shiny_female TEXT,
      sprite_front_shiny TEXT,
      sprite_back_default TEXT,
      sprite_back_female TEXT,
      sprite_back_shiny_female TEXT,
      sprite_back_shiny TEXT,
      cry TEXT,
      cry_legacy TEXT,
      name TEXT,
      primary_type TEXT,
      secondary_type TEXT
    );
    """

  def insert_sql(self) -> tuple[str, Dict[str, Any]]:
    return (
      "INSERT INTO pokemon (id, base_experience, height, weight, \"order\", primary_ability, secondary_ability, hidden_ability, species, hp, hp_effort, attack, attack_effort, defense, defense_effort, special_attack, special_attack_effort, special_defense, special_defense_effort, speed, speed_effort, sprite_front_default, sprite_front_female, sprite_front_shiny_female, sprite_front_shiny, sprite_back_default, sprite_back_female, sprite_back_shiny_female, sprite_back_shiny, cry, cry_legacy, name, primary_type, secondary_type) VALUES (:id, :base_experience, :height, :weight, :order, :primary_ability, :secondary_ability, :hidden_ability, :species, :hp, :hp_effort, :attack, :attack_effort, :defense, :defense_effort, :special_attack, :special_attack_effort, :special_defense, :special_defense_effort, :speed, :speed_effort, :sprite_front_default, :sprite_front_female, :sprite_front_shiny_female, :sprite_front_shiny, :sprite_back_default, :sprite_back_female, :sprite_back_shiny_female, :sprite_back_shiny, :cry, :cry_legacy, :name, :primary_type, :secondary_type);",
      self.__dict__
    )

  @staticmethod
  def from_json(json:str) -> Pokemon:
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
    for a in json['abilities']:
      value = Data.get_url_index(a['ability']['url'])
      key = ability_keys[a['slot']]
      pokemon_dict[key] = value
    
    for key in ['base_experience', 'height', 'weight', 'id', 'order', 'name']:
      pokemon_dict[key] = json[key]
    
    for side in ['front', 'back']:
      for sp in ['default', 'female', 'shiny_female', 'shiny']:
        pokemon_dict['sprite_' + side + '_' + sp] = json['sprites'][side + '_' + sp]
    
    #Cries
    pokemon_dict['cry'] = json['cries']['latest']
    pokemon_dict['cry_legacy'] = json['cries']['legacy']
    
    #Species
    pokemon_dict['species'] = Data.get_url_index(json['species']['url'])

    #Stats
    for stat in json['stats']:
      key = stat['stat']['name'].replace("-", "_")
      value = stat['base_stat']
      effort = stat['effort']
      pokemon_dict[key] = value
      pokemon_dict[key + '_effort'] = effort

    #Types
    pokemon_dict['primary_type'] = json['types'][0]['type']['name'] if len(json['types']) > 0 else None
    pokemon_dict['secondary_type'] = json['types'][1]['type']['name'] if len(json['types']) > 1 else None

    return Pokemon(
      id=pokemon_dict.get('id'),
      base_experience=pokemon_dict.get('base_experience'),
      height=pokemon_dict.get('height'),
      weight=pokemon_dict.get('weight'),
      order=pokemon_dict.get('order'),
      primary_ability=pokemon_dict.get('primary_ability'),
      secondary_ability=pokemon_dict.get('secondary_ability'),
      hidden_ability=pokemon_dict.get('hidden_ability'),
      species=pokemon_dict.get('species'),
      hp=pokemon_dict.get('hp'),
      hp_effort=pokemon_dict.get('hp_effort'),
      attack=pokemon_dict.get('attack'),
      attack_effort=pokemon_dict.get('attack_effort'),
      defense=pokemon_dict.get('defense'),
      defense_effort=pokemon_dict.get('defense_effort'),
      special_attack=pokemon_dict.get('special_attack'),
      special_attack_effort=pokemon_dict.get('special_attack_effort'),
      special_defense=pokemon_dict.get('special_defense'),
      special_defense_effort=pokemon_dict.get('special_defense_effort'),
      speed=pokemon_dict.get('speed'),
      speed_effort=pokemon_dict.get('speed_effort'),
      sprite_front_default=pokemon_dict.get('sprite_front_default'),
      sprite_front_female=pokemon_dict.get('sprite_front_female'),
      sprite_front_shiny_female=pokemon_dict.get('sprite_front_shiny_female'),
      sprite_front_shiny=pokemon_dict.get('sprite_front_shiny'),
      sprite_back_default=pokemon_dict.get('sprite_back_default'),
      sprite_back_female=pokemon_dict.get('sprite_back_female'),
      sprite_back_shiny_female=pokemon_dict.get('sprite_back_shiny_female'),
      sprite_back_shiny=pokemon_dict.get('sprite_back_shiny'),
      cry=pokemon_dict.get('cry'),
      cry_legacy=pokemon_dict.get('cry_legacy'),
      name=pokemon_dict.get('name'),
      primary_type=pokemon_dict.get('primary_type'),
      secondary_type=pokemon_dict.get('secondary_type')
    )
    
  @staticmethod
  def read() -> list[Pokemon]:
    url = "https://pokeapi.co/api/v2/pokemon?limit=100000"
    response = requests.get(url)
    results = response.json().get("results", [])
    
    abilities = []
    for entry in results:
      ability_url = entry.get("url")
      if not ability_url:
        continue
      ability_json = requests.get(ability_url).json()
      abilities.append(Pokemon.from_json(ability_json))
    return abilities

class Ability:
  def __init__(self, id: int, name: str, effect: str, short_effect: str, description: str, generation: int):
    self.id = id
    self.name = name
    self.effect = effect
    self.short_effect = short_effect
    self.description = description
    self.generation = generation

  @staticmethod
  def create_table_sql() -> str:
    return """
    CREATE TABLE IF NOT EXISTS ability (
      id INTEGER PRIMARY KEY,
      name TEXT,
      effect TEXT,
      short_effect TEXT,
      description TEXT,
      generation INTEGER
    );
    """

  def insert_sql(self) -> tuple[str, Dict[str, Any]]:
    return (
      "INSERT INTO ability (id, name, effect, short_effect, description, generation) VALUES (:id, :name, :effect, :short_effect, :description, :generation);",
      self.__dict__
    )

  @staticmethod
  def from_json(json: dict) -> 'Ability':
    #Ignoring effect_changes
    #Ignoring is_nain_series
    #Ignoring pokemon
    
    pokemon_dict = {}
    
    #Effect
    pokemon_dict['effect'] = "No description."
    pokemon_dict['short_effect'] = "No description."
    for l in json['effect_entries']:
      if l['language']['name'] == "en":
        pokemon_dict['effect'] = l['effect']
        pokemon_dict['short_effect'] = l['short_effect']
    
    #Description
    pokemon_dict['description'] = "No description."
    for l in json['flavor_text_entries']:
      if l['language']['name'] == "en":
        pokemon_dict['description'] = l['flavor_text']
    
    #Generation
    pokemon_dict['generation'] = Data.get_url_index(json['generation']['url'])
    
    #ID
    pokemon_dict['id'] = json['id']
    
    #Name
    pokemon_dict['name'] = json['name']
    for l in json['names']:
      if l['language']['name'] == "en":
        pokemon_dict['name'] = l['name']
      
    return Ability(
      id=pokemon_dict.get('id'),
      name=pokemon_dict.get('name'),
      effect=pokemon_dict.get('effect'),
      short_effect=pokemon_dict.get('short_effect'),
      description=pokemon_dict.get('description'),
      generation=pokemon_dict.get('generation')
    )

  @staticmethod
  def read() -> list[Ability]:
    url = "https://pokeapi.co/api/v2/ability?limit=100000"
    response = requests.get(url)
    results = response.json().get("results", [])

    abilities = []
    for entry in results:
      ability_url = entry.get("url")
      if not ability_url:
        continue
      ability_json = requests.get(ability_url).json()
      abilities.append(Ability.from_json(ability_json))
    return abilities

mode = sys.argv[1] if len(sys.argv) > 1 else "default"

if __name__ == "__main__":
  if mode == "uninstall" or mode == "reinstall":
    PostgreSQL.uninstall()
  if mode == "stop":
    PostgreSQL.stop()
  if mode == "default" or mode == "reinstall":
    run = False
    if not PostgreSQL.is_installed():
      PostgreSQL.install()
    if not PostgreSQL.is_initialized():
      PostgreSQL.create_db()
      PostgreSQL.run()
      run = True
      t = threading.Thread(target=PostgreSQL.fetch_and_insert_pokemon_data)
      t.start()
      t.join()
    if not run:
      PostgreSQL.run()
  
  
