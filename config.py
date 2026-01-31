import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID', 0))

COMMAND_PREFIX = '.'

DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

CONFIG_FILE = f'{DATA_DIR}/config.json'
HARDBANS_FILE = f'{DATA_DIR}/hardbans.json'
FAKE_PERMS_FILE = f'{DATA_DIR}/fake_perms.json'
ROLEPLAY_GIFS_FILE = f'{DATA_DIR}/roleplay_gifs.json'
VC_DATA_FILE = f'{DATA_DIR}/vc_data.json'
ANTINUKE_DATA_FILE = f'{DATA_DIR}/antinuke_data.json'
LEVELING_DATA_FILE = f'{DATA_DIR}/leveling_data.json'
ECONOMY_DATA_FILE = f'{DATA_DIR}/economy_data.json'
WARNS_DATA_FILE = f'{DATA_DIR}/warns_data.json'
MUTES_DATA_FILE = f'{DATA_DIR}/mutes_data.json'
BOOSTERS_DATA_FILE = f'{DATA_DIR}/boosters_data.json'
