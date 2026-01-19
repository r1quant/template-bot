from app.database.model_ohlc import ohlc_methods
from app.database.model_setting import settings_methods
from app.database.model_signal import signals_methods

# ---------------------------------------------------------
# Methods
# ---------------------------------------------------------


class db:
    ohlc = ohlc_methods
    settings = settings_methods
    signals = signals_methods
