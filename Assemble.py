import os
import zipfile
import shutil
import subprocess
import urllib.request
import sqlalchemy
from sqlalchemy import create_engine, text
from typing import Dict, Any

class PostgreSQL:
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
  def run() ->None:
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

class Data:
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

    def insert_sql(self) -> (str, Dict[str, Any]):
      return (
        "INSERT INTO ability (id, name, effect, short_effect, description, generation) VALUES (:id, :name, :effect, :short_effect, :description, :generation);",
        self.__dict__
      )

  class Move:
    def __init__(self, id: int, name: str, accuracy: int, damage_class: str, effect_chance: int, generation: int,
            ailment: str, ailment_chance: int, crit_rate: int, drain: int, flinch_chance: int, healing: int,
            max_hits: int, max_turns: int, min_hits: int, min_turns: int, stat_chance: int, power: int, pp: int,
            priority: int, target: str, type: str, description: str):
      self.id = id
      self.name = name
      self.accuracy = accuracy
      self.damage_class = damage_class
      self.effect_chance = effect_chance
      self.generation = generation
      self.ailment = ailment
      self.ailment_chance = ailment_chance
      self.crit_rate = crit_rate
      self.drain = drain
      self.flinch_chance = flinch_chance
      self.healing = healing
      self.max_hits = max_hits
      self.max_turns = max_turns
      self.min_hits = min_hits
      self.min_turns = min_turns
      self.stat_chance = stat_chance
      self.power = power
      self.pp = pp
      self.priority = priority
      self.target = target
      self.type = type
      self.description = description

    @staticmethod
    def create_table_sql() -> str:
      return """
      CREATE TABLE IF NOT EXISTS move (
        id INTEGER PRIMARY KEY,
        name TEXT,
        accuracy INTEGER,
        damage_class TEXT,
        effect_chance INTEGER,
        generation INTEGER,
        ailment TEXT,
        ailment_chance INTEGER,
        crit_rate INTEGER,
        drain INTEGER,
        flinch_chance INTEGER,
        healing INTEGER,
        max_hits INTEGER,
        max_turns INTEGER,
        min_hits INTEGER,
        min_turns INTEGER,
        stat_chance INTEGER,
        power INTEGER,
        pp INTEGER,
        priority INTEGER,
        target TEXT,
        type TEXT,
        description TEXT
      );
      """

    def insert_sql(self) -> (str, Dict[str, Any]):
      return (
        "INSERT INTO move (id, name, accuracy, damage_class, effect_chance, generation, ailment, ailment_chance, crit_rate, drain, flinch_chance, healing, max_hits, max_turns, min_hits, min_turns, stat_chance, power, pp, priority, target, type, description) VALUES (:id, :name, :accuracy, :damage_class, :effect_chance, :generation, :ailment, :ailment_chance, :crit_rate, :drain, :flinch_chance, :healing, :max_hits, :max_turns, :min_hits, :min_turns, :stat_chance, :power, :pp, :priority, :target, :type, :description);",
        self.__dict__
      )

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

    def insert_sql(self) -> (str, Dict[str, Any]):
      return (
        "INSERT INTO pokemon (id, base_experience, height, weight, \"order\", primary_ability, secondary_ability, hidden_ability, species, hp, hp_effort, attack, attack_effort, defense, defense_effort, special_attack, special_attack_effort, special_defense, special_defense_effort, speed, speed_effort, sprite_front_default, sprite_front_female, sprite_front_shiny_female, sprite_front_shiny, sprite_back_default, sprite_back_female, sprite_back_shiny_female, sprite_back_shiny, cry, cry_legacy, name, primary_type, secondary_type) VALUES (:id, :base_experience, :height, :weight, :order, :primary_ability, :secondary_ability, :hidden_ability, :species, :hp, :hp_effort, :attack, :attack_effort, :defense, :defense_effort, :special_attack, :special_attack_effort, :special_defense, :special_defense_effort, :speed, :speed_effort, :sprite_front_default, :sprite_front_female, :sprite_front_shiny_female, :sprite_front_shiny, :sprite_back_default, :sprite_back_female, :sprite_back_shiny_female, :sprite_back_shiny, :cry, :cry_legacy, :name, :primary_type, :secondary_type);",
        self.__dict__
      )

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

    def insert_sql(self) -> (str, Dict[str, Any]):
      return (
        "INSERT INTO pokemon_species (id, base_happiness, capture_rate, gender_rate, hatch_counter, \"order\", generation, national_pokedex_number, is_baby, is_legendary, is_mythical, color, growth_rate, habitat, shape, genera, name, egg_group, varieties, description) VALUES (:id, :base_happiness, :capture_rate, :gender_rate, :hatch_counter, :order, :generation, :national_pokedex_number, :is_baby, :is_legendary, :is_mythical, :color, :growth_rate, :habitat, :shape, :genera, :name, :egg_group, :varieties, :description);",
        self.__dict__
      )

  class PokemonMove:
    def __init__(self, pokemon: int, move: int, level_learned_at: int, learn_method: str):
      self.pokemon = pokemon
      self.move = move
      self.level_learned_at = level_learned_at
      self.learn_method = learn_method

    @staticmethod
    def create_table_sql() -> str:
      return """
      CREATE TABLE IF NOT EXISTS pokemon_move (
        pokemon INTEGER REFERENCES pokemon(id),
        move INTEGER REFERENCES move(id),
        level_learned_at INTEGER,
        learn_method TEXT
      );
      """

    def insert_sql(self) -> (str, Dict[str, Any]):
      return (
        "INSERT INTO pokemon_move (pokemon, move, level_learned_at, learn_method) VALUES (:pokemon, :move, :level_learned_at, :learn_method);",
        self.__dict__
      )

  class EvolutionChain:
    def __init__(self, id: int, from_id: int, to_id: int, gender: int, min_beauty: int, min_happiness: int,
            min_level: int, trade_species: str, relative_physical_stats: int, item: str, held_item: str,
            known_move: str, known_move_type: str, trigger: str, party_species: str, party_type: str,
            time_of_day: str, needs_overworld_rain: bool, turn_upside_down: bool):
      self.id = id
      self.from_id = from_id
      self.to_id = to_id
      self.gender = gender
      self.min_beauty = min_beauty
      self.min_happiness = min_happiness
      self.min_level = min_level
      self.trade_species = trade_species
      self.relative_physical_stats = relative_physical_stats
      self.item = item
      self.held_item = held_item
      self.known_move = known_move
      self.known_move_type = known_move_type
      self.trigger = trigger
      self.party_species = party_species
      self.party_type = party_type
      self.time_of_day = time_of_day
      self.needs_overworld_rain = needs_overworld_rain
      self.turn_upside_down = turn_upside_down

    @staticmethod
    def create_table_sql() -> str:
      return """
      CREATE TABLE IF NOT EXISTS evolution_chain (
        id INTEGER PRIMARY KEY,
        "from" INTEGER REFERENCES pokemon(id),
        "to" INTEGER REFERENCES pokemon(id),
        gender INTEGER,
        min_beauty INTEGER,
        min_happiness INTEGER,
        min_level INTEGER,
        trade_species TEXT,
        relative_physical_stats INTEGER,
        item TEXT,
        held_item TEXT,
        known_move TEXT,
        known_move_type TEXT,
        trigger TEXT,
        party_species TEXT,
        party_type TEXT,
        time_of_day TEXT,
        needs_overworld_rain BOOLEAN,
        turn_upside_down BOOLEAN
      );
      """

    def insert_sql(self) -> (str, Dict[str, Any]):
      return (
        "INSERT INTO evolution_chain (id, \"from\", \"to\", gender, min_beauty, min_happiness, min_level, trade_species, relative_physical_stats, item, held_item, known_move, known_move_type, trigger, party_species, party_type, time_of_day, needs_overworld_rain, turn_upside_down) VALUES (:id, :from_id, :to_id, :gender, :min_beauty, :min_happiness, :min_level, :trade_species, :relative_physical_stats, :item, :held_item, :known_move, :known_move_type, :trigger, :party_species, :party_type, :time_of_day, :needs_overworld_rain, :turn_upside_down);",
        {
          "id": self.id,
          "from_id": self.from_id,
          "to_id": self.to_id,
          "gender": self.gender,
          "min_beauty": self.min_beauty,
          "min_happiness": self.min_happiness,
          "min_level": self.min_level,
          "trade_species": self.trade_species,
          "relative_physical_stats": self.relative_physical_stats,
          "item": self.item,
          "held_item": self.held_item,
          "known_move": self.known_move,
          "known_move_type": self.known_move_type,
          "trigger": self.trigger,
          "party_species": self.party_species,
          "party_type": self.party_type,
          "time_of_day": self.time_of_day,
          "needs_overworld_rain": self.needs_overworld_rain,
          "turn_upside_down": self.turn_upside_down
        }
      )

