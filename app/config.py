import pathlib

from pydantic import BaseModel, ValidationError

from app.settings import logging

# ---------------------------------------------------------
# Define the configuration based to the JSON structure
# ---------------------------------------------------------


class _CronJob(BaseModel):
    refresh_tickers: list[str] = []


class Config(BaseModel):
    cronjob: _CronJob = _CronJob(refresh_tickers=[])


# ---------------------------------------------------------
# Read and validate the configuration file
# ---------------------------------------------------------


def load_configuration(file_path: str) -> Config | None:
    try:
        json_string = pathlib.Path(file_path).read_text()
        config = Config.model_validate_json(json_string)
        return config
    except FileNotFoundError:
        logging.error(f"Error: The file '{file_path}' was not found.")
        return None
    except ValidationError:
        logging.error(f"Error: Configuration data in '{file_path}' is invalid.")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None


configuration_file = "app/configuration.json"
config = load_configuration(configuration_file)
