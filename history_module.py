import json
import copy
import pathlib
import datetime as dt
from typing import (List,
                    Dict,)
from my_logging_module import (my_logger,
                               log_exception,
                               log_exception_decorator)


@log_exception_decorator(log_exception)
class HistoryManager:
    """
    Allows to undo changes. Creates history files for every record (separate files) and for a whole project.
    """

    def __init__(self, brain, *args, **kwargs) -> None:
        self.brain = brain

    def del_file(self, file_id: str) -> None:
        self.brain.project["del_files"][file_id] = copy.deepcopy(self.brain.project["files"][file_id])

        del self.brain.project["files"][file_id]

    def del_file_definietly(self) -> None:
        ...

    def save_previous_state(self, _uuid: str, key: str, value: Dict) -> None:  # should be done with try/except or dict?
        time_record = str(int(dt.datetime.today().timestamp()))

        if self.check_if_history_file_exists(_uuid):
            h_data = self.load_history_file(_uuid)

            h_data[f"{key}_{time_record}"] = value

            self.save_history_file(_uuid, h_data)
            self.save_to_general_history(_uuid, key, value, time_record)
        else:
            h_data = dict()
            h_data[f"{key}_{time_record}"] = value

            self.save_history_file(_uuid, h_data)
            self.save_to_general_history(_uuid, key, value, time_record)

    def save_to_general_history(self, _uuid_or_project: str, key: str, value: Dict, time_record=None) -> None:
        time_record = time_record if time_record else str(int(dt.datetime.today().timestamp()))

        gh_data = json.load_history_file('general_history')
        gh_data[f"{_uuid_or_project}_{time_record}"] = {key: value}

        self.save_history_file('general_history', gh_data)

    def restore_previous_state(self) -> None:
        ...

    def get_history(self, _uuid: str) -> None | Dict:
        history_dir = self.brain.project_path.joinpath('history')
        files = [x.stem for x in history_dir.iterdir()]
        if _uuid in files:
            f_path = history_dir.joinpath(f"{_uuid}.json")
            with open(f_path, "r") as f:
                return json.load(f)

    def get_general_history(self) -> Dict:
        with open(self.brain.project_path.joinpath('history\general_history.json'), mode="r") as f:
            return json.load(f)

    def create_history_dir(self) -> None:
        self.brain.project_path.joinpath("history").mkdir()

    def create_general_history_file(self) -> None:
        with open(self.brain.project_path.joinpath(f"history/general_history.json"), mode="w") as f:
            general_history_file = dict()
            json.dump(general_history_file, f, indent=4)

    def check_if_history_file_exists(self, _uuid: str) -> bool:
        hd_path = self.brain.project_path.joinpath(f"history/{_uuid}.json")
        return hd_path.exists()

    def load_history_file(self, _uuid_or_general: str) -> Dict:
        with open(self.brain.project_path.joinpath(f"history/{_uuid_or_general}.json"), mode="r") as f:
            return json.load(f)

    def save_history_file(self, _uuid_or_general: str, h_file: Dict) -> None:
        with open(self.brain.project_path.joinpath(f"history/{_uuid_or_general}.json"), mode="w") as f:
            json.dump(h_file, f, indent=4)
