import datetime
import json
import platform
import re
import pathlib
import os
import webbrowser
import shutil
import uuid
import gc
import tkinter as tk
import datetime as dt
from typing import (List,
                    Dict,
                    Tuple)
from tkinter import messagebox
from history_module import HistoryManager
from my_logging_module import (log_exception_decorator,
                               log_exception,
                               my_logger)
from panels import (ProjectHistoryPan,
                    FileHistoryPan,
                    DetailPan,
                    ZoomPan,
                    LabelPan)
from views_module import (AddDirView,
                          AddFilesView,
                          ManageSourcesView,
                          BaseProjectView,
                          OpenProjectView,
                          NewProjectView,
                          MainMenuView)
from base_classes import MyLabel
from lang_module import LANG


@log_exception_decorator(log_exception)
class TheBrain:
    """The core of the program. All interactions between windows, panels and project data go through TheBrain. Some minor operations are left in relevant objects.
    What's important it looks after projects files. Only TheBrain is granted to save and load the project - it keeps the reference likewise.
    It's a quite large object, so it should be parted into sub-brain managers.
    """

    def __init__(self, main_window) -> None:
        """Initiated by TheMainWindow.
        """
        self.main_window = main_window
        self.project_path = None
        self.project = None

        self.history_manager = HistoryManager(brain=self)
        self.file_pat_formats = re.compile(r"(.png$|.jpg$|.jpeg$)", flags=re.IGNORECASE)

        my_logger.debug("TheBrain initiated successfully")

    def reset_tree(self) -> None:
        """FilterPan.show_all
        """
        self.main_window.main_frame.tree_pan.populate()

        my_logger.debug("TheBrain.reset_tree: tree populated.")

    def filter_tree(self, file_id_lst: List) -> None:
        """FilterPan.filter
        """
        self.main_window.main_frame.tree_pan.populate(file_id_lst)

        my_logger.debug("TheBrain.filter_tree: tree filtered.")

    def look_up(self, to_include: List, to_exclude: List):
        """LookUpPan.look_up
        Lazy implementation: if
        """
        tree = self.main_window.main_frame.tree_pan.tree

        tree_children = tree.get_children()

        if any(to_include):
            for _uuid in tree_children:
                if to_include[0]:
                    if to_include[0] in self.project["files"][_uuid]["f_name"]:
                        continue
                if to_include[1]:
                    if to_include[1] in self.project["files"][_uuid]["source"]:
                        continue
                if to_include[2]:
                    if to_include[2] in self.project["files"][_uuid]["comment"]:
                        continue
                tree.delete(_uuid)

        if any(to_exclude):
            for _uuid in tree_children:
                if to_exclude[0]:
                    if to_exclude[0] not in self.project["files"][_uuid]["f_name"]:
                        continue
                if to_exclude[1]:
                    if to_exclude[1] not in self.project["files"][_uuid]["source"]:
                        continue
                if to_exclude[2]:
                    if to_exclude[2] not in self.project["files"][_uuid]["comment"]:
                        continue
                tree.delete(_uuid)

    def restore_previous_state(self, key: str, data: Dict) -> None:
        """Called by ProjectHistoryPan.restore_for_project, FileHistoryPan.restore_for_file
        """
        print(key)
        # key_history = record[0]
        _, _uuid_or_pro, _ = key.split(", ")
        # data = record[1]

        if _uuid_or_pro == "Project":
            for key_, val in data.items():
                self.project[key_] = val
            self.save_project()
        else:
            for key_, val in data.items():
                self.project["files"][_uuid_or_pro][key_] = val
            self.save_project()

        self.history_manager.clear_previous_state(key)

        if _uuid_or_pro in self.main_window.main_frame.tree_pan.tree.get_children():
            self.main_window.main_frame.tree_pan.tree.item(
                _uuid_or_pro,
                values=(
                    (
                        self.project["files"][_uuid_or_pro]["f_name"],
                        self.project["files"][_uuid_or_pro]["source"],
                        self.project["files"][_uuid_or_pro]["path"],
                        self.project["files"][_uuid_or_pro]["labels"],
                        dt.datetime.fromtimestamp(self.project["files"][_uuid_or_pro]["c_time"]).strftime(
                            "%Y-%m-%d %H:%M:%S")
                    )
                )
            )

        detail_pan = self.main_window.main_frame.detail_pan
        if isinstance(detail_pan, DetailPan) and _uuid_or_pro == detail_pan._uuid:
            detail_pan.update_pan(_uuid_or_pro)

    def move_or_remove_file_labels(self, _uuid: str, new_labels: List) -> None:
                                   # file_id: str, source: str, path: str, labels: List, c_time: str) -> None:
        """Called by DetailPan.remove_labels, DetailPan.move_lbl_up, DetailPan.move_lbl_down
        """

        self.history_manager.save_to_general_history(
            self.project["files"][_uuid]["f_name"],
            _uuid,
            {"labels": self.project["files"][_uuid]["labels"]}
        )

        self.project["files"][_uuid]["labels"] = new_labels

        self.save_project()

        self.main_window.main_frame.tree_pan.tree.item(
            _uuid,
            values=(
                (
                    self.project["files"][_uuid]["f_name"],
                    self.project["files"][_uuid]["source"],
                    self.project["files"][_uuid]["path"],
                    self.project["files"][_uuid]["labels"],
                    dt.datetime.fromtimestamp(self.project["files"][_uuid]["c_time"]).strftime("%Y-%m-%d %H:%M:%S"),
                )
            )
        )

        my_logger.debug(f"TheBrain: {_uuid} new sequence of labels: {new_labels}")

    def set_file_or_project_history(self) -> None:
        """Called from DetailPan.__init__(?), RotatingPan buttons: command=self.file_history_pan; command=self.project_history_pan
        """
        my_logger.debug("TheBrain.set_file_or_project_history function initiated")

        project_history_pan_instance = isinstance(self.main_window.main_frame.rotating_pan.pan, ProjectHistoryPan)
        file_history_pan_instance = isinstance(self.main_window.main_frame.rotating_pan.pan, FileHistoryPan)
        detail_pan_instance = isinstance(self.main_window.main_frame.detail_pan, DetailPan)

        if project_history_pan_instance:
            my_logger.debug(f"TheBrain.project_history_pan_instance: True")

            project_history_pan = self.main_window.main_frame.rotating_pan.pan

            project_history_path = self.project_path.joinpath(f"history/general_history.json")

            if project_history_path.exists():
                with open(project_history_path, "r") as f:
                    project_history = json.load(f)

                project_history_pan.set_project_history(project_history)

        elif detail_pan_instance and file_history_pan_instance:
            my_logger.debug(f"TheBrain.file_history_pan_instance and TheBrain.detail_pan_instance: True")

            file_history_pan = self.main_window.main_frame.rotating_pan.pan
            detail_pan = self.main_window.main_frame.detail_pan

            _uuid = detail_pan._uuid
            f_name = detail_pan.f_name

            project_history_path = self.project_path.joinpath(f"history/general_history.json")

            if project_history_path.exists():
                with open(project_history_path, "r") as f:
                    project_history = json.load(f)

                file_history = {}

                for key, record in project_history.items():
                    _, __uuid, _ = key.split(", ")
                    if __uuid == _uuid:
                        file_history[key] = record

                file_history_pan.set_file_history(_uuid, f_name, file_history)
            else:
                file_history = {}
                file_history_pan.set_file_history(_uuid, f_name, file_history)

    def add_labels_to_file(self, detail_pan) -> None:

        my_logger.debug("TheBrain.add_labels_to_file - procedure started.")

        if not isinstance(self.main_window.main_frame.rotating_pan.pan, LabelPan):
            return

        all_lbls_listbox = self.main_window.main_frame.rotating_pan.pan.all_lbls_listbox
        _uuid = detail_pan._uuid

        indexes = all_lbls_listbox.curselection()
        if not indexes:
            return

        current_labels = detail_pan.lbls_listbox.get(0, tk.END)
        for index in indexes:
            label_to_add = all_lbls_listbox.get(index)
            if label_to_add in current_labels:
                continue
            detail_pan.lbls_listbox.insert(tk.END, label_to_add)
            self.history_manager.save_to_general_history(
                self.project["files"][_uuid]["f_name"],
                _uuid,
                {"labels": self.project["files"][_uuid]["labels"]}
            )
            self.project["files"][_uuid]["labels"].append(label_to_add)

        self.save_project()

        tree = self.main_window.main_frame.tree_pan.tree

        tree.item(
            _uuid,
            values=(
                    (
                        self.project["files"][_uuid]["f_name"],
                        self.project["files"][_uuid]["source"],
                        self.project["files"][_uuid]["path"],
                        self.project["files"][_uuid]["labels"],
                        dt.datetime.fromtimestamp(self.project["files"][_uuid]["c_time"]).strftime("%Y-%m-%d %H:%M:%S")
                    )
            )
        )
        my_logger.debug("TheBrain.add_labels_to_file - accomplished")

    def delete_label(self, label: str) -> None:
        """Called by LabelPan.delete_label
        """
        self.history_manager.save_to_general_history("Project",
                                                     "Project",
                                                     {"labels": self.project["labels"]})

        self.project["labels"].remove(label)
        self.save_project()
        my_logger.debug(f"TheBrain: label {label} deleted, current labels in the project: {self.project["labels"]}")

        for _uuid, data in self.project["files"].items():
            if label in data["labels"]:
                self.history_manager.save_to_general_history(self.project["files"][_uuid]["f_name"], _uuid, {"labels": data["labels"]})

                data["labels"].remove(label)
                my_logger.debug(
                    f"TheBrain: delete_label for {_uuid}, {self.project["files"][_uuid]["f_name"]} - label deleted: {label}, current labels: {data["labels"]}")
        self.save_project()

        curr_uuid = self.main_window.main_frame.detail_pan._uuid
        if curr_uuid:
            self.main_window.main_frame.detail_pan.update_pan(curr_uuid)

        tree = self.main_window.main_frame.tree_pan.tree
        for _uuid in tree.get_children():
            tree.item(
                _uuid,
                values=(
                        (
                            self.project["files"][_uuid]["f_name"],
                            self.project["files"][_uuid]["source"],
                            self.project["files"][_uuid]["path"],
                            self.project["files"][_uuid]["labels"],
                            dt.datetime.fromtimestamp(self.project["files"][_uuid]["c_time"]).strftime("%Y-%m-%d %H:%M:%S")
                        )
                )
            )
            my_logger.debug(f"TheBrain: tree_pan.tree view updated for {_uuid}, {self.project["files"][_uuid]["f_name"]} ")

    def rename_label(self, old_label: str, new_label: str, all_labels: List) -> None:
        my_logger.debug(f"TheBrain.rename_label: old: {old_label}, new: {new_label}, labels: {all_labels}")

        self.history_manager.save_to_general_history("Project", "Project", {"labels": all_labels})

        self.project["labels"] = all_labels

        for _uuid, data in self.project["files"].items():
            if old_label in data["labels"]:
                index = data["labels"].index(old_label)

                self.history_manager.save_to_general_history(self.project["files"][_uuid]["f_name"], _uuid, {"labels": data["labels"]})

                data["labels"].remove(old_label)
                data["labels"].insert(index, new_label)

        self.save_project()
        self.project = self.load_project()

        curr_uuid = self.main_window.main_frame.detail_pan._uuid
        if curr_uuid:
            self.main_window.main_frame.detail_pan.update_pan(curr_uuid)

        tree = self.main_window.main_frame.tree_pan.tree

        for _uuid in tree.get_children():
            tree.item(
                _uuid,
                values=(
                        (
                            self.project["files"][_uuid]["f_name"],
                            self.project["files"][_uuid]["source"],
                            self.project["files"][_uuid]["path"],
                            self.project["files"][_uuid]["labels"],
                            dt.datetime.fromtimestamp(self.project["files"][_uuid]["c_time"]).strftime("%Y-%m-%d %H:%M:%S")
                        )
                )
            )
        my_logger.debug(f"TheBrain: tree_pan.tree view updated.")

    def save_new_order_all_labels(self, all_labels: List) -> None:
        my_logger.debug(f"TheBrain.save_new_order_all_labels: {all_labels}")

        self.history_manager.save_to_general_history("Project",
                                                     "Project",
                                                     {"labels": self.project["labels"]},
                                                     )

        self.project["labels"] = all_labels
        self.save_project()

        my_logger.debug(f"TheBrain.save_new_order_all_labels: {all_labels} - successful")

    def add_label_to_project(self, new_label: str) -> None:
        my_logger.debug(f"TheBrain.add_label_to_project: label: {new_label}")

        labels_temp = " /// ".join(self.project["labels"]) if self.project["labels"] else ""

        data_to_save = {"labels": self.project["labels"]}

        self.history_manager.save_to_general_history("Project",
                                                     "Project",
                                                     data_to_save)
        self.project["labels"].append(new_label)
        self.save_project()

        my_logger.debug(f"TheBrain.add_label_to_project: label: {new_label} - successful")

    def move_down_tree(self) -> None:
        my_logger.debug("TheBrain.move_down_tree")

        tree = self.main_window.main_frame.tree_pan.tree
        item = tree.focus()

        next_item = tree.next(item)

        self.project["files"][item]["index"], self.project["files"][next_item]["index"] \
            = self.project["files"][next_item]["index"], self.project["files"][item]["index"]
        self.project["files"] = dict(sorted(self.project["files"].items(), key=lambda x: x[1]["index"]))

        self.save_project()

        tree.move(
            item,
            tree.parent(item),
            tree.index(item) + 1
        )

    def move_up_tree(self) -> None:
        my_logger.debug("TheBrain.move_up_tree")

        tree = self.main_window.main_frame.tree_pan.tree
        item = tree.focus()

        prev_item = tree.prev(item)

        self.project["files"][item]["index"], self.project["files"][prev_item]["index"] \
            = self.project["files"][prev_item]["index"], self.project["files"][item]["index"]

        self.project["files"] = dict(sorted(self.project["files"].items(), key=lambda x: x[1]["index"]))

        self.save_project()

        tree.move(
            item,
            tree.parent(item),
            tree.index(item) - 1
        )

    def open_in_default_viewer(self, path: pathlib.Path) -> None:
        my_logger.debug("TheBrain.open_in_default_viewer")

        path = self.project_path.joinpath(path)
        my_logger.debug(f"TheBrain.open_in_default_viewer: {path}")
        try:
            if platform.system() == "Windows":
                path = str(pathlib.PureWindowsPath(path))
                os.startfile(path)
            else:
                os.system(path)
        except FileNotFoundError as e:
            my_logger.debug(f"TheBrain.open_in_default_viewer: {path} - FileNotFoundError")
            messagebox.showerror(str(e))
        except PermissionError as e:
            my_logger.debug(f"TheBrain.open_in_default_viewer: {path} - PermissionError")
            messagebox.showerror(str(e))

    def open_source_in_browser(self, src: str) -> None:
        my_logger.debug(f"TheBrain.open_source_in_browser: {src}")
        webbrowser.open(src, new=2)

    def open_in_new_browser(self, path: pathlib.Path) -> None:
        my_logger.debug("TheBrain.open_in_new_browser")

        path = self.project_path.joinpath(path)
        my_logger.debug(f"TheBrain.open_in_new_browser: {path}")
        webbrowser.open(str(path), new=2)

    def alter_comment(self, _uuid, comment) -> None: # todo
        self.history_manager.save_to_general_history(self.project["files"][_uuid]["f_name"], _uuid, {"comment": self.project["files"][_uuid]["comment"]})
        my_logger.debug(f"TheBrain.alter_comment: new comment for {_uuid}: {comment}")

        self.project["files"][_uuid]["comment"] = comment
        self.save_project()

    def rename_file(self, _uuid, f_name_new, path_new) -> None:
        my_logger.debug(f"TheBrain.rename_file({_uuid}, {f_name_new}, {path_new})")

        old_name = self.project["files"][_uuid]["f_name"]
        old_path = self.project["files"][_uuid]["path"]

        self.project["files"][_uuid]["f_name"] = f_name_new
        self.project["files"][_uuid]["path"] = path_new

        self.save_project()
        self.project = self.load_project()

        self.main_window.main_frame.tree_pan.tree.item(
            _uuid,
            values=(
                (
                    self.project["files"][_uuid]["f_name"],
                    self.project["files"][_uuid]["source"],
                    self.project["files"][_uuid]["path"],
                    self.project["files"][_uuid]["labels"],
                    f'{dt.datetime.fromtimestamp(int(self.project["files"][_uuid]["c_time"])):%Y-%m-%d %H:%M:%S}'
                )
            )
        )

        # self.main_window.main_frame.tree_pan.tree.focus(_uuid)
        # self.main_window.main_frame.tree_pan.tree.selection_set(_uuid)

        # self.main_window.main_frame.tree_pan.tree.delete(old_name)

        self.history_manager.save_to_general_history(
            self.project["files"][_uuid]["f_name"],
            _uuid,
            {"f_name": old_name, "path": old_path}
        )

    def rename_source(self, _uuid, source_new) -> None:
        my_logger.debug(f"TheBrain.rename_source {_uuid}, old: {self.project["files"][_uuid]["source"]}, new: {source_new})")

        old_source = self.project["files"][_uuid]["source"]
        self.project["files"][_uuid]["source"] = source_new

        self.save_project()

        self.main_window.main_frame.tree_pan.tree.item(
            _uuid,
            values=(
                (
                    self.project["files"][_uuid]["f_name"],
                    self.project["files"][_uuid]["source"],
                    self.project["files"][_uuid]["path"],
                    self.project["files"][_uuid]["labels"],
                    f'{dt.datetime.fromtimestamp(int(self.project["files"][_uuid]["c_time"])):%Y-%m-%d %H:%M:%S}'
                )
            )
        )

        self.history_manager.save_to_general_history(
            self.project["files"][_uuid]["f_name"],
            _uuid,
            {"source": old_source}
        )

    def del_file(self, _uuid: str) -> None: # todo command
        ...
        # my_logger.debug(f"TheBrain.del_file {file_id}")
        #
        # self.history_manager.del_file(file_id)
        #
        # self.main_window.main_frame.zoom_pan.destroy()
        # self.main_window.main_frame.detail_pan.destroy()
        # self.main_window.main_frame.detail_pan = DetailPan(master=self.main_window.main_frame)
        # self.main_window.main_frame.detail_pan.grid(row=1, column=0)
        #
        # self.main_window.main_frame.tree_pan.tree.delete(file_id)

        # todo coś żeby potem odzyskać plik?

    def add_dir_view(self) -> None:
        my_logger.debug(f"TheBrain.add_dir_view")

        self.main_window.main_frame.destroy()
        self.main_window.main_frame = AddDirView(master=self.main_window)

    def add_files_view(self) -> None:
        my_logger.debug(f"TheBrain.add_files_view")

        self.main_window.main_frame.destroy()
        self.main_window.main_frame = AddFilesView(master=self.main_window)

    def manage_sources_view(self) -> None:
        my_logger.debug(f"TheBrain.manage_sources_view")

        self.main_window.main_frame.destroy()
        self.main_window.main_frame = ManageSourcesView(master=self.main_window)

    def add_files(self, f_paths: Tuple) -> None:
        """Invoked by AddFilesView.add_files"""
        my_logger.debug(f"TheBrain.add_files: path: {'\n'.join(f_paths)}")

        f_paths = [pathlib.Path(p) for p in f_paths]

        for p in f_paths:
            # p = pathlib.Path(p)
            if not (p.exists() or p.is_file()):
                messagebox.showerror(title="Ścieżka do katalogu", message="Niedozwolona ścieżka do katalogu.\nJeśli chcesz dodać katalog skorzystaj z opcji 'Dodaj folder z plikami'")
                my_logger.debug(f"TheBrain.add_files: path: {str(p)} - wrong")
                return

        for p in f_paths:
            # p = pathlib.Path(p)
            if not p.is_absolute():
                messagebox.showerror(title=LANG.get("wrong_path_2"), message=LANG.get("wrong_path_2_msg"))
                return

        target_dir = pathlib.Path(self.project_path, datetime.date.today().strftime('%Y-%m-%d'))

        if target_dir.exists():
            target_dir = pathlib.Path(self.project_path,
                                      target_dir.name + "_" + str(int(dt.datetime.today().timestamp())))

        res = messagebox.askyesno(title=LANG.get("confirm"),
                                  message=LANG.get("confirm_msg"))
        if not res:
            return

        target_dir.mkdir()

        for file in f_paths:
            shutil.copy2(file, target_dir)

        pro_counter = int(self.project["last_index"])

        project_path_parts = self.project_path.parts

        for (dpath, dirs, files) in os.walk(target_dir):
            for file in files:
                path = pathlib.Path(dpath, file)

                path_parts = path.parts

                relative_path = path_parts[len(project_path_parts) - len(path_parts):]
                relative_path = "/".join(relative_path)

                pro_counter += 1
                self.project["files"][str(uuid.uuid1())] = {
                    "f_name": path.name,
                    "index": pro_counter,
                    "source": "",
                    "path": relative_path,
                    # paths are cut so that user can move whole dir with project (dir with base.json and files)
                    "labels": [],
                    "comment": "",
                    "extra_fields": {},
                    "c_time": path.stat().st_mtime,
                    "binds": [],
                }

        files_added = pro_counter - self.project["last_index"]

        messagebox.showinfo(title=LANG.get("Files_added"), message=f"{files_added}{LANG.get("Files_added_msg")}")

        self.project["last_index"] = pro_counter

        self.save_project()
        self.main_window.main_frame.destroy()
        self.go_to_base_project_view(self.project_path)

        self.collect_garbage()

        my_logger.debug(f"TheBrain.add_files: - accomplished")

    def __add_dir__ignore_patterns(self, path, names) -> List:
        return [f for f in names if pathlib.Path(path, f).is_file() and not self.file_pat_formats.search(f)]

    def __check_circular_reference(self, d_with_files_path) -> None | bool:
        """
        Important function: shutil.copytree in self.add_dir_view() doesn't check
        if a destination dir includes a source dir - it prevents an infinite loop.
        """
        project_path = str(self.project_path)
        d_with_files_path = str(d_with_files_path)
        for (_dpath, dirs, files) in os.walk(d_with_files_path):
            if _dpath == project_path:
                messagebox.showerror(title=LANG.get("circ_ref"),
                                     message=LANG.get("circ_ref_msg"))
                return True

    def add_dir(self, path: str, all_or_some_files_var: int) -> None:
        """Invoked by AddDirView.add_dir"""
        my_logger.debug(f"TheBrain.add_dir: path: {path}, all: {all_or_some_files_var}")

        d_with_files_path = pathlib.Path(path)

        if not d_with_files_path.is_absolute():
            messagebox.showerror(title=LANG.get("wrong_path_2"), message=LANG.get("wrong_path_2_msg"))
            return

        if not d_with_files_path.is_dir():
            d_with_files_path = d_with_files_path.parent
            res = messagebox.askyesno(title=LANG.get("wrong_path_2"),
                                      message=f"{"wrong_path_2_msg_2"} {d_with_files_path}")
            if not res:
                return

        if self.__check_circular_reference(d_with_files_path):
            return

        target_dir = pathlib.Path(self.project_path, d_with_files_path.stem)

        res = messagebox.askyesno(title=LANG.get("confirm"),
                                  message=LANG.get("confirm_msg"))
        if not res:
            return

        if target_dir.exists():
            target_dir = pathlib.Path(self.project_path,
                                      d_with_files_path.stem + str(int(dt.datetime.today().timestamp())))

        if all_or_some_files_var:
            shutil.copytree(d_with_files_path, target_dir)
        else:
            shutil.copytree(d_with_files_path, target_dir, ignore=self.__add_dir__ignore_patterns)

        pro_counter = int(self.project["last_index"])

        project_path_parts = self.project_path.parts

        for (dpath, dirs, files) in os.walk(target_dir):
            for file in files:
                path = pathlib.Path(dpath, file)

                path_parts = path.parts

                relative_path = path_parts[len(project_path_parts) - len(path_parts):]
                relative_path = "/".join(relative_path)

                pro_counter += 1
                self.project["files"][str(uuid.uuid1())] = {
                    "f_name": path.name,
                    "index": pro_counter,
                    "source": "",
                    "path": relative_path,
                    # paths are cut so that user can move whole dir with project (dir with base.json and files)
                    "labels": [],
                    "comment": "",
                    "extra_fields": {},
                    "c_time": path.stat().st_mtime,
                    "binds": [],
                }

        files_added = pro_counter - self.project["last_index"]

        messagebox.showinfo(title=LANG.get("Files_added"), message=f"{files_added}{LANG.get("Files_added_msg")}")

        self.project["last_index"] = pro_counter

        self.save_project()
        self.main_window.main_frame.destroy()
        self.go_to_base_project_view(self.project_path)

        self.collect_garbage()

        my_logger.debug(f"TheBrain.add_dir: path: {path}, all: {all_or_some_files_var} - accomplished")


    def open_project_view(self) -> None:
        """Called by MainMenuView. Apart from setting a OpenProjectView it loads a list of previously created projects
        """
        self.main_window.main_frame.destroy()
        projects_list = self.load_list_of_projects()
        my_logger.debug(f"Projects loaded{projects_list}")

        self.main_window.main_frame = OpenProjectView(master=self.main_window, projects_list=projects_list)

        my_logger.debug("OpenProjectView established")

    def main_menu_view(self) -> None:
        self.main_window.main_frame.destroy()
        self.main_window.main_frame = MainMenuView(master=self.main_window)

        my_logger.debug("TheBrain.main_menu_view: MainMenuView established")

    def collect_garbage(self) -> None:
        """An automatic garbage collection is disabled in MainWindow"""
        gc.collect()
        my_logger.debug("TheBrain.collect_garbage: garbage collected")

    # def clear_detail_and_zoom_pan(self) -> None:
    #     self.main_window.main_frame.zoom_pan.destroy()
    #     self.main_window.main_frame.detail_pan.destroy()
    #     my_logger.debug("TheBrain.clear_detail_and_zoom_pan: zoom_pan and detail_pan cleared")

    def enable_menubar_btns(self) -> None:
        """Invoked by BaseProjectView.__init__"""
        self.main_window.menu_bar.enable_buttons()
        my_logger.debug("TheBrain.enable_menubar_btns: menu_bar buttons enabled")

    def mount_detail_and_zoom_pan(self, _uuid) -> None:
        my_logger.debug(f"TheBrain.mount_detail_and_zoom_pan: tries to load detail and zoom pans for {_uuid}")

        try:
            path_to_img = self.project["files"][_uuid]["path"]
        except KeyError as key_error:
            my_logger.debug(f"TheBrain.mount_detail_and_zoom_pan: zoom_pan error: {key_error}")
            return

        path_to_img = self.project_path.joinpath(path_to_img)

        my_logger.debug(f"TheBrain.mount_detail_and_zoom_pan: path to img {path_to_img}")

        self.main_window.main_frame.zoom_pan.destroy()
        my_logger.debug(f"TheBrain.mount_detail_and_zoom_pan: zoom_pan destroyed")

        if self.file_pat_formats.search(path_to_img.suffix):
            try:
                self.main_window.main_frame.zoom_pan = ZoomPan(master=self.main_window.main_frame,
                                                               path_to_img=path_to_img)
                self.main_window.main_frame.zoom_pan.grid(row=0, column=1)
                my_logger.debug(f"TheBrain.mount_detail_and_zoom_pan: zoom_pan established")
            except tk.TclError as tk_error:
                my_logger.debug(f"TheBrain.mount_detail_and_zoom_pan: zoom_pan error: {tk_error}")
                return
            except KeyError as key_error:
                my_logger.debug(f"TheBrain.mount_detail_and_zoom_pan: zoom_pan error: {key_error}")
                return
        else:
            self.main_window.main_frame.zoom_pan = MyLabel(master=self.main_window.main_frame,
                                                           text=LANG.get("Available_formats"))
            self.main_window.main_frame.zoom_pan.grid(row=0, column=1)
            my_logger.debug(f"TheBrain.mount_detail_and_zoom_pan: unavailable format: {path_to_img}")

        self.main_window.main_frame.detail_pan.update_pan(_uuid=_uuid)
        # self.main_window.main_frame.detail_pan= DetailPan(master=self.main_window.main_frame, file_id=file_id)
        # self9.main_window.main_frame.detail_pan.grid(row=1, column=0)

        my_logger.debug(f"TheBrain.mount_detail_and_zoom_pan: detail_pan established")

        self.collect_garbage()

    def go_to_base_project_view(self, project_path: pathlib.Path) -> None:
        """Invoked by TheBrain.create_project or TheBrain.go_back_to_main_menu_or_base_pro_view.
        Prepares TheBrain to service a project"""
        self.project_path = project_path
        my_logger.debug(f"TheBrain.go_to_base_project_view: {self.project_path} ready to load")

        self.project = self.load_project()
        my_logger.debug(f"TheBrain.go_to_base_project_view: {self.project_path} loaded successfully")

        self.main_window.main_frame.destroy()
        self.main_window.main_frame = BaseProjectView(master=self.main_window)

    def go_back_to_main_menu_or_base_pro_view(self) -> None:
        if self.project_path:
            self.go_to_base_project_view(self.project_path)
        else:
            self.main_menu_view()

    def load_list_of_projects(self) -> List:
        """Invoked by TheBrain."""
        cwd_path = pathlib.Path(os.getcwd())
        check_if_project_list_exists = cwd_path.joinpath("projects_list.json").exists()
        if check_if_project_list_exists:
            with open(cwd_path.joinpath("projects_list.json"), mode="r") as file:
                projects_list = json.load(file)

            my_logger.debug(
                f"TheBrain.add_project_to_list_of_projects: List of projects loaded: {cwd_path.joinpath('projects_list.json')}")
            return projects_list["projects"]
        my_logger.debug(
            f"TheBrain.add_project_to_list_of_projects: List of projects does not exist: {cwd_path.joinpath('projects_list.json')}")
        return []

    def create_project(self, project_path: pathlib.Path) -> None:
        """Invoked by NewProjectView.
        Creates a base project file in json format.
        Automatically adds the project to a list of projects and creates base history files
        """
        my_logger.debug(f"TheBrain.create_project: project_path: {project_path}")

        self.project_path = project_path
        try:
            self.project_path.mkdir(parents=True)
        except FileExistsError:
            check_base_file_path = self.project_path.joinpath("base.json").exists()
            if check_base_file_path:
                messagebox.showerror(title=LANG.get("pro_already_created") ,
                                     message=LANG.get("pro_already_created_msg"))
                my_logger.debug(
                    f"TheBrain.create_project: Project {self.project_path} already created in that location.")
                return

            check_is_dir = self.project_path.is_dir()
            if check_is_dir:
                res = messagebox.askyesno(title=LANG.get("path_exists"),
                                          message=LANG.get("path_exists_msg"))
                my_logger.debug(f"TheBrain.create_project: Path exists: {self.project_path} ")
                if not res:
                    my_logger.debug(f"TheBrain.create_project: Path declined: {self.project_path} ")
                    return
                my_logger.debug(f"TheBrain.create_project: Path accepted: {self.project_path} ")
            else:
                messagebox.showerror(title=LANG.get("wrong_path"),
                                     message=LANG.get("wrong_path_msg"))
                my_logger.debug(f"TheBrain.create_project: Path leads to a file: {self.project_path} ")
                return

        except OSError:
            messagebox.showerror(title=LANG.get("wrong_path_name"),
                                 message=LANG.get("wrong_path_name_msg"))
            my_logger.debug(f"TheBrain.create_project: Wrong path: {self.project_path}")
            return

        project_name = self.project_path.name

        base_proj_data = {
            "name": project_name,
            "files": {},
            "labels": [],
            "last_index": 0,
            "sources": [],
            "binds": {},
            "last_id_binds": 0,
            "dist_schemas": {},
            "del_files": {},
        }

        self.project = base_proj_data

        try:
            self.save_project()
            self.add_project_to_list_of_projects()

            self.history_manager.create_history_dir()
            self.history_manager.create_general_history_file()
            my_logger.debug(f"TheBrain.create_project: Project {self.project_path} created successfully")
            my_logger.debug(f"TheBrain.create_project: Go to go_to_base_project_view(self.project_path)")

            self.go_to_base_project_view(self.project_path)
        except FileExistsError:
            messagebox.showerror(title=LANG.get("Unable_to_save"), message=LANG.get("Unable_to_save_msg"))
            my_logger.debug(f"TheBrain.create_project: Project {self.project_path} not created - FileExistsError")

    def add_project_to_list_of_projects(self) -> None:
        """Invoked by TheBrain.create_project"""
        cwd_path = pathlib.Path(os.getcwd())
        check_if_project_list_exists = cwd_path.joinpath("projects_list.json").exists()
        if check_if_project_list_exists:
            with open(cwd_path.joinpath("projects_list.json"), mode="r") as file:
                projects_list = json.load(file)
            projects_list["projects"].append(str(self.project_path))
            my_logger.debug(
                f"TheBrain.add_project_to_list_of_projects: List of projects is going to be updated: {cwd_path.joinpath('projects_list.json')}")

        else:
            projects_list = {"projects": [str(self.project_path)]}
            my_logger.debug(
                f"TheBrain.add_project_to_list_of_projects: List of projects is going to be created: {cwd_path.joinpath('projects_list.json')}")

        with open(cwd_path.joinpath("projects_list.json"), mode="w") as file:
            json.dump(projects_list, file, indent=4)

        my_logger.debug(
            f"TheBrain.add_project_to_list_of_projects: List of projects created/updated: {cwd_path.joinpath('projects_list.json')}")


    def new_project_view(self) -> None:
        """Invoked by MainMenuView.
        Switches MainMenuView to NewProjectView"""
        self.main_window.main_frame.destroy()
        self.main_window.main_frame = NewProjectView(master=self.main_window)

        my_logger.debug("TheBrain.new_project_view: NewProjectView established")

    def load_project(self) -> Dict:
        with open(self.project_path.joinpath("base.json"), mode="r") as f:
            self.project = json.load(f)
        my_logger.debug(f"TheBrain.load_project(): {self.project_path} loaded successfully")
        return self.project

    def save_project(self) -> None:
        with open(self.project_path.joinpath("base.json"), mode="w") as file:
            json.dump(self.project, file, indent=4)
        my_logger.debug(f"TheBrain.save_project(): {self.project_path} saved successfully")
