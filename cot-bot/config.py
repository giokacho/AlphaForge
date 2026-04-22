import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from shared.assets import CFTC_MAP, COT_ASSETS

CFTC_MAPPING = CFTC_MAP
ASSETS       = COT_ASSETS
DATA_DIR     = "cot-bot/outputs/"
