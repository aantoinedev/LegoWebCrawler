from pathlib import Path
import yaml
import sys

PATH = Path(__file__).resolve().parent.parent

if str(PATH) not in sys.path:
    sys.path.append(str(PATH))

with open(PATH.joinpath("config.yml"), "r", encoding="utf-8") as file:
    config: dict = yaml.safe_load(file)


class Browser:
    _browser: dict = config.get("browser")
    headless: bool = _browser.get("headless")


class Data:
    _data: dict = config.get("data")
    path: str = _data.get("path")
