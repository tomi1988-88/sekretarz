import json
import copy
import datetime as dt
from typing import (List,
                    Dict,
                    Tuple)
from my_logging_module import (my_logger,
                               log_exception,
                               log_exception_decorator)


@log_exception_decorator(log_exception)
class HistoryManager:
    """Allows to undo changes. Creates history files for every record (separate files) and for a whole project.
    """

    def __init__(self, brain, *args, **kwargs) -> None:
        self.brain = brain
        my_logger.debug("HistoryManager created")

    def del_file(self, file_id: str) -> None:
        self.save_to_general_history("Project", "Project", file_id, self.brain.project["files"][file_id])

        self.brain.project["del_files"][file_id] = copy.deepcopy(self.brain.project["files"][file_id])

        del self.brain.project["files"][file_id]

        self.brain.save_project()

        my_logger.debug(f"HistoryManager.del_file: {file_id} - accomplished")

    def del_file_definitely(self) -> None:
        ...

    def save_to_general_history(self,
                                f_name_or_project: str,
                                _uuid_or_project: str,
                                data: Dict) -> None:
        """If file_id_or_project and _uuid_or_project referees to the project: file_id_or_project = 'Project', _uuid_or_project = 'Project'.
        Called by HistoryManager.del_file, TheBrain.delete_label
        """
        my_logger.debug(
            f"HistoryManager.save_to_general_history: {f_name_or_project}: {_uuid_or_project}: {data}")

        # if time_record:
        #     time_record = time_record
        # else:
        #     time_record = str(dt.datetime.today().timestamp())
        time_record = str(dt.datetime.today().timestamp())

        gh_data = self.load_history_file('general_history')

        gh_data[f"{f_name_or_project}, {_uuid_or_project}, {time_record}"] = data

        self.save_history_file('general_history', gh_data)
        my_logger.debug(f"HistoryManager.save_to_general_history: {_uuid_or_project}: successful")

    def clear_previous_state(self, key_history: str) -> None:
        """Called by TheBrain.restore_previous_state
        """
        project_data = self.load_history_file("general_history")
        del project_data[key_history]
        self.save_history_file("general_history", project_data)

        my_logger.debug(f"HistoryManager.clear_previous_state: {key_history}")

    def create_history_dir(self) -> None:
        """Invoked by TheBrain.create_project"""
        self.brain.project_path.joinpath(r"history").mkdir()

    def create_general_history_file(self) -> None:
        """Invoked by TheBrain.create_project"""
        with open(self.brain.project_path.joinpath(r"history/general_history.json"), mode="w") as f:
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
