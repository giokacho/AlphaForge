import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from shared.assets import ASSETS  # noqa: F401  — re-exported for data_fetcher import

LOOKBACK_DAYS = 300
SIGNAL_EXPIRY_HOURS = 8
MIN_RR = 1.5
