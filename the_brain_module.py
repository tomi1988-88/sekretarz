import json
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
                    Dict,)
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
from views_module import (AddFilesFromDirView,
                          BaseProjectView,
                          OpenProjectView,
                          NewProjectView,
                          MainMenuView)
from base_classes import MyLabel


@log_exception_decorator(log_exception)
class TheBrain:
    """The core of the program. All interactions between windows, panels and project data go through TheBrain. Some minor operations are left in relevant objects.
    What's important it looks after projects files. Only TheBrain is granted to save and load the project - it keeps the reference likewise.
    It's a quite large object so it should be parted into sub-brain managers.
    """

    def __init__(self, main_window) -> None:
        """Initiated by TheMainWindow.
        """
        self.main_window = main_window
        self.project_path = None
        self.project = None
        # self.d_path = tk.StringVar() # (maybe unnsecesary) variable for different dir_paths - is cleared to "" every time when a particular func is called

        self.history_manager = HistoryManager(brain=self)
        # self.temp_layer = TempLayer()
        self.file_pat_formats = re.compile(r"(.png$|.jpg$|.jpeg$)", flags=re.IGNORECASE)

        my_logger.debug("TheBrain initiated successfully")
        # self.file_pat_formats_str_list = [".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"]

    def move_or_remove_file_labels(self, file_id: str, source: str, path: str, labels: List, c_time: str) -> None:
        """Called by DetailPan.remove_labels.
        """
        self.history_manager.save_previous_state(
            self.project["files"][file_id]["uuid"], 
            "labels", 
            self.project["files"][file_id]["labels"]
        )
        
        self.project["files"][file_id]["labels"] = labels

        self.save_project()
        
        self.main_window.main_frame.tree_pan.tree.item(
            file_id,
            values=(
                (
                    file_id,
                    source,
                    path,
                    labels,
                    c_time,
                )
            )
        )

        my_logger.debug(f"TheBrain: {file_id} new sequence of labels: {labels}")

    def set_file_or_project_history(self) -> None:
        """Called from DetailPan.__init__, RotatingPan buttons: command=self.file_history_pan; command=self.project_history_pan
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
            else:
                project_history = ["empty list"]
                project_history_pan.set_project_history(project_history)

        elif detail_pan_instance and file_history_pan_instance:
            my_logger.debug(f"TheBrain.file_history_pan_instance and TheBrain.detail_pan_instance: True")
          
            file_history_pan = self.main_window.main_frame.rotating_pan.pan
            detail_pan = self.main_window.main_frame.detail_pan

            _uuid = detail_pan._uuid
            file_id = detail_pan.file_id

            file_history_path = self.project_path.joinpath(f"history/{_uuid}")
            if file_history_path.exists():
                with open(file_history_path, "r") as f:
                    file_history = json.load(f)

                file_history_pan.set_file_history(file_id, file_history)
            else:
                file_history = ["empty list"]
                file_history_pan.set_file_history(file_id, file_history)

    def add_labels_to_file(self, detail_pan) -> None:

        if not isinstance(self.main_window.main_frame.rotating_pan.pan, LabelPan):
            return

        all_lbls_listbox = self.main_window.main_frame.rotating_pan.pan.all_lbls_listbox
        file_id = detail_pan.file_id

        indexes = all_lbls_listbox.curselection()
        if not indexes:
            return

        current_labels = detail_pan.lbls_listbox.get(0, tk.END)
        for index in indexes:
            label_to_add = all_lbls_listbox.get(index)
            if label_to_add in current_labels:
                continue
            detail_pan.lbls_listbox.insert(tk.END, label_to_add)
            self.project["files"][file_id]["labels"].append(label_to_add)

        self.save_project()

        tree = self.main_window.main_frame.tree_pan.tree

        tree.item(
                file_id,
                values=(
                    (file_id,
                     self.project["files"][file_id]["source"],
                     self.project["files"][file_id]["path"],
                     self.project["files"][file_id]["labels"],
                     dt.datetime.fromtimestamp(self.project["files"][file_id]["c_time"]).strftime("%Y-%m-%d %H:%M:%S"))
                )
            )

    def delete_label(self, label: str) -> None:
        """Called by LabelPan.delete_label
        """
        
        self.project["labels"].remove(label)
        my_logger.debug(f"TheBrain: label {label} deleted, current labels in the project: {self.project["labels"]}")
        self.history_manager.save_to_general_history("Project", "labels", self.project["files"][file_id]["labels"])
        
        for file_id, data in self.project["files"].items():
            if label in data["labels"]:
                data["labels"].remove(label)
                my_logger.debug(f"TheBrain: delete_label for {file_id} - label deleted: {label}, current labels: {data["labels"]}")
        
        tree = self.main_window.main_frame.tree_pan.tree
        for file_id in tree.winfo_children():
            tree.item(
            file_id,
            values=(
                    (file_id,
                     self.project["files"][file_id]["source"],
                     self.project["files"][file_id]["path"],
                     self.project["files"][file_id]["labels"],
                     dt.datetime.fromtimestamp(self.project["files"][file_id]["c_time"]).strftime("%Y-%m-%d %H:%M:%S")
                    )
                )
            )
            my_logger.debug(f"TheBrain: tree_pan.tree view updated for {file_id}")

    def rename_label(self, old_label: str, new_label: str, all_labels: List) -> None:

        self.project["labels"] = all_labels

        for file, data in self.project["files"].items():
            if old_label in data["labels"]:
                index = data["labels"].index(old_label)
                data["labels"].insert(index, new_label)

        self.save_project()

    def save_new_order_all_labels(self, all_labels: List) -> None:
        self.project["labels"] = all_labels
        self.save_project()

    def add_label_to_project(self, new_label: str) -> None:
        self.project["labels"].append(new_label)
        self.save_project()

    def open_in_new_window_pan(self, file_id: str) -> None:
        ...  # and create a list with all opened windows and set changes in master and top level window?

    def move_down_tree(self) -> None:
        tree = self.main_window.main_frame.tree_pan.tree
        item = tree.focus()

        next_item = tree.next(item)
        # that's the reason why it should have been done with SQL
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
        path = self.project_path.joinpath(path)
        my_logger.debug(f"TheBrain.open_in_default_viewer: {path}")
        try:
            os.system(path)
        except FileNotFoundError as e:
            my_logger.debug(f"TheBrain.open_in_default_viewer: {path} - FileNotFoundError")
            messagebox.error(e)
        except PermissionError as e:
            my_logger.debug(f"TheBrain.open_in_default_viewer: {path} - PermissionError")
            messagebox.error(e)

    def open_source_in_browser(self, src: str) -> None:
        my_logger.debug(f"TheBrain.open_source_in_browser: {src}")
        webbrowser.open(src, new=2)

    def open_in_new_browser(self, path: pathlib.Path) -> None:
        path = self.project_path.joinpath(path)
        my_logger.debug(f"TheBrain.open_in_new_browser: {path}")
        webbrowser.open(str(path), new=2)

    def alter_comment(self, file_id, comment) -> None:
        self.history_manager.save_previous_state(
            self.project["files"][file_id]["uuid"], 
            "comment", 
            self.project["files"][file_id]["comment"]
        )
        my_logger.debug(f"TheBrain.alter_comment: new comment for {file_id}: {comment}")
        
        self.project["files"][file_id]["comment"] = comment
        self.save_project()

    def rename_file(self, old_name, file_id_new_name, file_data) -> None:
        my_logger.debug(f"TheBrain.rename_file({old_name}, {file_id_new_name}, {file_data})")

        self.project["files"][file_id_new_name] = file_data

        del self.project["files"][old_name]

        self.project["files"] = dict(sorted(self.project["files"].items(), key=lambda item: item[1]["index"]))

        self.save_project()
        self.project = self.load_project()

        index_of_old_name = self.main_window.main_frame.tree_pan.tree.index(old_name)

        self.main_window.main_frame.tree_pan.tree.insert(
            "",
            index_of_old_name,
            iid=file_id_new_name,
            values=(
                (
                    file_id_new_name,
                    self.project["files"][file_id_new_name]["source"],
                    self.project["files"][file_id_new_name]["path"],
                    self.project["files"][file_id_new_name]["labels"],
                    f'{dt.datetime.fromtimestamp(int(self.project["files"][file_id_new_name]["c_time"])):%Y-%m-%d %H:%M:%S}'
                )
            )
        )

        self.main_window.main_frame.tree_pan.tree.focus(file_id_new_name)
        self.main_window.main_frame.tree_pan.tree.selection_set(file_id_new_name)

        self.main_window.main_frame.tree_pan.tree.delete(old_name)

        self.history_manager.save_previous_state(
            self.project["files"][file_id_new_name]["uuid"],
            "f_name",
            old_name
        )

    def rename_source(self, file_id, old_source, path, labels, c_time, new_src) -> None:
        self.project["files"][file_id]["source"] = new_src

        self.save_project()

        self.main_window.main_frame.tree_pan.tree.item(
            file_id,
            values=(
                (
                    file_id,
                    new_src,
                    path,
                    labels,
                    c_time,
                )
            )
        )

        self.history_manager.save_previous_state(
            self.project["files"][file_id]["uuid"],
            f"source",
            old_source
        )

    def del_file(self, file_id) -> None:
        self.history_manager.del_file(file_id)

        self.main_window.main_frame.zoom_pan.destroy()
        self.main_window.main_frame.detail_pan.destroy()

        self.main_window.main_frame.tree_pan.tree.delete(file_id)

    def add_files_from_dir_view(self) -> None:
        self.main_window.main_frame.destroy()
        self.main_window.main_frame = AddFilesFromDirView(master=self.main_window)

    def __add_files_from_dir__ignore_patterns(self, path, names) -> List:
        return [f for f in names if pathlib.Path(path, f).is_file() and not self.file_pat_formats.search(f)]

    def __check_circular_reference(self, d_with_files_path) -> None | bool:
        """
        Important function: shutil.copytree in self.add_files_from_dir() doesn't check
        if a destination dir includes a source dir - it prevents an infinite loop.
        """
        project_path = str(self.project_path)
        d_with_files_path = str(d_with_files_path)
        for (_dpath, dirs, files) in os.walk(d_with_files_path):
            if _dpath == project_path:
                messagebox.showerror(title="Circular reference",
                                     message="A circular reference spotted: You tried to add to the project a directory that contains this project")
                return True

    def add_files_from_dir(self, path, all_or_some_files_var) -> None:
        d_with_files_path = pathlib.Path(path)

        if not d_with_files_path.is_absolute():
            messagebox.showerror(title="Wrong path", message="Pass an absolute path, eg. C:\\My documents\\Files...")
            return

        if not d_with_files_path.is_dir():
            d_with_files_path = d_with_files_path.parent
            res = messagebox.askyesno(title="Wrong path",
                                      message=f"It's not a directory. Do you want to add files from {d_with_files_path}")
            if not res:
                return

        if self.__check_circular_reference(d_with_files_path):
            return

        target_dir = pathlib.Path(self.project_path, d_with_files_path.stem)

        res = messagebox.askyesno(title="Confirm",
                                  message="Copying ready to start. It may last a few minutes depending on the scale.")
        if not res:
            return

        if target_dir.exists():
            target_dir = pathlib.Path(self.project_path,
                                      d_with_files_path.stem + str(int(dt.datetime.today().timestamp())))

        if all_or_some_files_var:
            shutil.copytree(d_with_files_path, target_dir)
        else:
            shutil.copytree(d_with_files_path, target_dir, ignore=self.__add_files_from_dir__ignore_patterns)

        pro_counter = int(self.project["last_index"])

        project_path_parts = self.project_path.parts

        for (dpath, dirs, files) in os.walk(target_dir):
            for file in files:
                path = pathlib.Path(dpath, file)

                path_parts = path.parts

                relative_path = path_parts[len(project_path_parts) - len(path_parts):]
                relative_path = "/".join(relative_path)

                pro_counter += 1
                self.project["files"][f"{pro_counter} - {path.name}"] = {
                    "uuid": str(uuid.uuid1()),
                    "index": pro_counter,
                    "source": "",
                    "f_name": path.name,
                    "path": relative_path,
                    # paths are cut so that user can move whole dir with project (dir with base.json and files)
                    "labels": [],
                    "comment": "",
                    "extra_fields": {},
                    "c_time": path.stat().st_mtime,
                    "binds": [],
                }

            files_added = pro_counter - self.project["last_index"]

            messagebox.showinfo(title="Files added", message=f"{files_added} file(s) added to the project.")

            self.project["last_index"] = pro_counter

            self.save_project()
            self.main_window.main_frame.destroy()
            self.go_to_base_project_view(self.project_path)
            # todo: simplify this func to omit loading part? - procejt just has been saved

            self.collect_garbage()

    def create_project(self, project_path: pathlib.Path) -> None:
        """Creates a base project file in json format.
        Automatically adds the project to a list of projects and creates base history files
        """
        self.project_path = project_path
        try:
            self.project_path.mkdir(parents=True)
        except FileExistsError:
            check_base_file_path = self.project_path.joinpath("base.json").exists()
            if check_base_file_path:
                messagebox.showerror(title="Project already created in that location.",
                                     message="Delete an existing project in that location and then set a new one.")
                my_logger.debug(
                    f"TheBrain.create_project: Project {self.project_path} already created in that location.")
                return

            check_is_dir = self.project_path.is_dir()
            if check_is_dir:
                res = messagebox.askyesno(title="Path exists.",
                                          message="Do you want to create a project in that location?")
                my_logger.debug(f"TheBrain.create_project: Path exists: {self.project_path} ")
                if not res:
                    my_logger.debug(f"TheBrain.create_project: Path declined: {self.project_path} ")
                    return
                my_logger.debug(f"TheBrain.create_project: Path accepted: {self.project_path} ")
            else:
                messagebox.showerror(title="Choose a path to a directory.",
                                     message="A chosen path leads to a file not to a directory.")
                my_logger.debug(f"TheBrain.create_project: Path leads to a file: {self.project_path} ")
                return

        except OSError:
            messagebox.showerror(title="Wrong path.",
                                 message="Wrong path name. Some characters might be not allowed (check: < > : \" / \\ | ? *).")
            my_logger.debug(f"TheBrain.create_project: Wrong path: {self.project_path}")
            return

        project_name = self.project_path.name

        base_proj_data = {
            "name": project_name,
            # "main_dir": str(project_path),
            "files": {},
            "labels": [],
            "last_index": 0,
            "links": [],
            "binds": {},
            "last_id_binds": 0,
            "dist_schemas": {},
            "del_files": {}
        }

        self.project = base_proj_data

        self.save_project()
        self.add_project_to_list_of_projects()

        self.history_manager.create_history_dir()  # should be in try/except with save project -
        # if a history dir still exists after manual del of a project
        self.history_manager.create_general_history_file()

        my_logger.debug(f"TheBrain.create_project: Project {self.project_path} created successfully")
        my_logger.debug(f"TheBrain.create_project: Go to go_to_base_project_view(self.project_path)")

        self.go_to_base_project_view(self.project_path)

    def go_to_base_project_view(self, project_path: pathlib.Path) -> None:
        """Prepares TheBrain to service a project"""
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

    def load_project(self) -> Dict:
        with open(self.project_path.joinpath("base.json"), mode="r") as f:
            self.project = json.load(f)
        my_logger.debug(f"TheBrain.load_project(): {self.project_path} loaded successfully")
        return self.project

    def save_project(self) -> None:
        with open(self.project_path.joinpath("base.json"), mode="w") as file:
            json.dump(self.project, file, indent=4)
        my_logger.debug(f"TheBrain.save_project(): {self.project_path} saved successfully")

    def add_project_to_list_of_projects(self) -> None:
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

    def load_list_of_projects(self) -> List:
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

    def settings_view(self):
        """Called by MainMenuView. Allowes to change view mode and lang
        """
        # lang, dark - light view mode
        ...
        my_logger.debug("TheBrain.settings_view: settings_view established")

    def open_project_view(self) -> None:
        """Called by MainMenuView. Apart from setting a OpenProjectView it loads a list of previously created projects
        """
        self.main_window.main_frame.destroy()
        projects_list = self.load_list_of_projects()
        my_logger.debug(f"Projects loaded{projects_list}")

        self.main_window.main_frame = OpenProjectView(master=self.main_window, projects_list=projects_list)

        my_logger.debug("OpenProjectView established")

    def new_project_view(self) -> None:
        """Called by MainMenuView. Switches it to NewProjectView(master=self.main_window)"""
        self.main_window.main_frame.destroy()
        self.main_window.main_frame = NewProjectView(master=self.main_window)

        my_logger.debug("TheBrain.new_project_view: NewProjectView established")

    def main_menu_view(self) -> None:
        self.main_window.main_frame.destroy()
        self.main_window.main_frame = MainMenuView(master=self.main_window)

        my_logger.debug("TheBrain.main_menu_view: MainMenuView established")

    def collect_garbage(self) -> None:
        """An automatic garbage collection is disabled in MainWindow"""
        gc.collect()
        my_logger.debug("TheBrain.collect_garbage: garbage collected")

    def clear_detail_and_zoom_pan(self) -> None:
        self.main_window.main_frame.zoom_pan.destroy()
        self.main_window.main_frame.detail_pan.destroy()
        my_logger.debug("TheBrain.clear_detail_and_zoom_pan: zoom_pan and detail_pan cleared")

    def enable_menubar_btns(self) -> None:
        self.main_window.menu_bar.enable_buttons()
        my_logger.debug("TheBrain.enable_menubar_btns: menu_bar buttons enabled")

    def mount_detail_and_zoom_pan(self, file_id) -> None:
        my_logger.debug(f"TheBrain.mount_detail_and_zoom_pan: tries to load detail and zoom pans for {file_id}")

        path_to_img = self.project["files"][file_id]["path"]
        path_to_img = self.project_path.joinpath(path_to_img)

        my_logger.debug(f"TheBrain.mount_detail_and_zoom_pan: path to img {path_to_img}")

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
                                                           text="Available formats: .jpg, .jpeg, .png")
            self.main_window.main_frame.zoom_pan.grid(row=0, column=1)
            my_logger.debug(f"TheBrain.mount_detail_and_zoom_pan: unavailable format: {path_to_img}")

        self.main_window.main_frame.detail_pan = DetailPan(master=self.main_window.main_frame, file_id=file_id)
        self.main_window.main_frame.detail_pan.grid(row=1, column=0)

        my_logger.debug(f"TheBrain.mount_detail_and_zoom_pan: detail_pan established")

        self.collect_garbage()
