import os
from pathlib import Path
from kivy.resources import resource_add_path
from kivy.core.text import LabelBase
from dotenv import load_dotenv
from kivy.config import Config

resource_add_path(os.path.join(os.path.dirname(__file__), './assets/fonts'))

LabelBase.register(
    name='DejaVuSans',
    fn_regular='DejaVuSans.ttf',
    fn_bold='DejaVuSans-Bold.ttf'
)

load_dotenv()

MAL_CLIENT_ID = os.getenv('MAL_CLIENT_ID')
MAL_CLIENT_SECRET = os.getenv('MAL_CLIENT_SECRET')

if not MAL_CLIENT_ID:
    raise ValueError("MAL_CLIENT_ID not found in .env file")

if not MAL_CLIENT_SECRET:
    raise ValueError("MAL_CLIENT_SECRET not found in .env file")

CONFIG_FILE = Path(os.path.dirname(__file__) + '/generated/mihon_tracker_config.json')

Config.set('kivy', 'default_font', ['DejaVuSans'])
