from enum import Enum

# ---------------------------------------------------------
# Constants
# ---------------------------------------------------------


class EnvType(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"

    @property
    def is_development(self):
        return self == self.DEVELOPMENT
