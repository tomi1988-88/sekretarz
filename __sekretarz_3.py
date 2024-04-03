import copy
import tkinter as tk
import customtkinter as ctk
import os
import re
import pathlib
import json
import gc
import shutil
import uuid
from tkinter import ttk
import datetime as dt
from tkinter import filedialog, messagebox
from __sekretarz_lang import LANG
from __base_classes import (MyFrame,
                            MyLabel,
                            MyButton,
                            MyEntry,
                            MyListbox,
                            MyTopLevel,
                            MyMenu,
                            MyScrollableFrame,
                            MyRadiobutton,
                            MyDialogWindow_AskDir,
                            MyDialogWindow_AskDir_CreateDir)
from __panels import (TreePan,
                      ZoomPan,
                      DetailPan)



class HistoryManager:
    """It's not tkinter obj but 'master' attr is set for simplicity"""
    def __init__(self, brain, *args, **kwargs):
        self.brain = brain

    def del_file(self, file_id):
        self.master.project["del_files"][file_id] = copy.deepcopy(self.master.project["files"][file_id])

        del self.master.project["files"][file_id]

    def del_file_definietly(self):
        ...

    def save_previous_state(self, _uuid, key, value): # should be done with try/except or dict?
        if self.check_if_history_file_exists(_uuid):
            h_data = self.load_history_file(_uuid)

            h_data[f"{key}_{str(int(dt.datetime.today().timestamp()))}"] = value

            self.save_history_file(_uuid, h_data)
        else:
            h_data = dict()

            h_data[f"{key}_{str(int(dt.datetime.today().timestamp()))}"] = value

            self.save_history_file(_uuid, h_data)

    def restore_previous_state(self):
        ...

    def show_previous_states(self):
        ...

    def create_history_dir(self, project_path):
        project_path.joinpath("history").mkdir()

    def check_if_history_file_exists(self, _uuid):
        hd_path = self.brain.project_path.joinpath(f"history/{_uuid}.json")
        return hd_path.exists()

    def load_history_file(self, _uuid):
        with open(self.brain.project_path.joinpath(f"history/{_uuid}.json"), mode="r") as f:
            return json.load(f)

    def save_history_file(self, _uuid, h_file):
        with open(self.brain.project_path.joinpath(f"history/{_uuid}.json"), mode="w") as f: # todo: sth went wrong
            json.dump(h_file, f, indent=4)

class TempLayer:
    def __init__(self, *args, **kwargs):
        ... # todo: maybe it might work as a variable storage for the whole base view eg:
        # temp_layer.curr_widget = base pro view which is not displayed in main window?
        # class TempLayer(MyFrame)

class LangVariables:
    def __init__(self, *args, **kwargs):
        ...


def _log_it(project_path):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                log_path = TheBrain.PROJECT_PATH.joinpath("log.log")
                with open(log_path, "a") as log_file:
                    line_to_save = f"{func.__name__}, {args}, {kwargs}\n"
                    log_file.write(line_to_save)
            except AttributeError as e:
                print(e)

            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_it(func):
    def wrapper(*args, **kwargs):
        try:
            log_path = TheBrain.PROJECT_PATH.joinpath("log.log")
            with open(log_path, "a") as log_file:
                line_to_save = f"{func.__name__}, {args}, {kwargs}\n"
                log_file.write(line_to_save)
        except AttributeError as e:
            print(e)

        return func(*args, **kwargs)
    return wrapper
# my_logger = log_it(TheBrain.PROJECT_PATH)

class TheBrain:

    PROJECT_PATH = None

    def __init__(self, main_window, *args, **kwargs):
        self.main_window = main_window
        self.project_path = None
        self.project = None
        # self.d_path = tk.StringVar() # (maybe unnsecesary) variable for different dir_paths - is cleared to "" every time when a particular func is called

        self.history_manager = HistoryManager(brain=self)
        self.temp_layer = TempLayer()
        self.file_pat_formats = re.compile(r"(.png$|.jpg$|.jpeg$)", flags=re.IGNORECASE)
        # self.file_pat_formats_str_list = [".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"]

    @log_it
    def rename_file(self, old_name, file_id_new_name, file_data):
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

    @log_it
    def rename_source(self, file_id, old_source, path, labels,c_time, new_src):
        self.project["files"][file_id]["source"] = new_src

        # self.source = src

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

    @log_it
    def del_file(self, file_id):
        self.history_manager.del_file(file_id)

        self.main_window.main_frame.zoom_pan.destroy()
        self.main_window.main_frame.detail_pan.destroy()

        self.main_window.main_frame.tree_pan.tree.delete(file_id)

    @log_it
    def add_files_from_dir_view(self):
        self.main_window.main_frame.destroy()
        self.main_window.main_frame = AddFilesFromDirView(master=self.main_window)

    @log_it
    def __add_files_from_dir__ignore_patterns(self, path, names):
        return [f for f in names if pathlib.Path(path, f).is_file() and not self.file_pat_formats.search(f)]

    @log_it
    def __check_circular_reference(self, d_with_files_path):
        project_path = str(self.project_path)
        d_with_files_path = str(d_with_files_path)
        for (_dpath, dirs, files) in os.walk(d_with_files_path):
            if _dpath == project_path:
                messagebox.showerror(title="Circular reference", message="A circular reference spotted: You tried to add to the project a directory that contains this project")
                return True

    @log_it
    def add_files_from_dir(self, path, all_or_some_files_var):
        d_with_files_path = pathlib.Path(path)

        if not d_with_files_path.is_absolute():
            messagebox.showerror(title="Wrong path", message="Pass an absolute path, eg. C:\\My documents\\Files...")
            return

        if not d_with_files_path.is_dir():
            d_with_files_path = d_with_files_path.parent
            res = messagebox.askyesno(title="Wrong path", message=f"It's not a directory. Do you want to add files from {d_with_files_path}")
            if not res:
                return

        if self.__check_circular_reference(d_with_files_path): # todo: check once agian sth is wrong
            return  # current cwd is venv/python

        target_dir = pathlib.Path(self.project_path, d_with_files_path.stem)

        res = messagebox.askyesno(title="Confirm", message="Copying ready to start. It may last a few minutes depending on the scale.")
        if not res:
            return

        if target_dir.exists():
            target_dir = pathlib.Path(self.project_path, d_with_files_path.stem + str(int(dt.datetime.today().timestamp())))

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
                    "path": relative_path,  # paths are cut so that user can move whole dir with project (dir with base.json and files)
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

    @log_it
    def create_project(self, project_path: pathlib.Path):
        self.project_path = project_path
        try:
            self.project_path.mkdir(parents=True)
        except FileExistsError:
            check_base_file_path = self.project_path.joinpath("base.json").exists()
            if check_base_file_path:
                messagebox.showerror(title="Project already created in that location.", message="Delete an existing project in that location and then set a new one.")
                return

            check_is_dir = self.project_path.is_dir()
            if check_is_dir:
                res = messagebox.askyesno(title="Path exists.", message="Do you want to create a project in that location?")
                if not res:
                    return
            else:
                messagebox.showerror(title="Choose a path to directory.", message="A chosen path leads to a file not to a directory.")
                return
        # except WindowsError:
        #     messagebox.showerror(title="Wrong path. No < > : \" / \\ | ? * allowed.")
        #     return
        # except NotADirectoryError:
        #     messagebox.showerror(title="Wrong path.", message="Wrong path name. Some characters might be not allowed (check: < > : \" / \\ | ? *).")
        #     return
        except OSError:
            messagebox.showerror(title="Wrong path.", message="Wrong path name. Some characters might be not allowed (check: < > : \" / \\ | ? *).")
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

        self.history_manager.create_history_dir(self.project_path) # should be in try/except with save project -
        # if a history dir still exists after manual del of a project

        self.go_to_base_project_view(self.project_path)

        TheBrain.PROJECT_PATH = self.project_path

    @log_it
    def go_to_base_project_view(self, project_path: pathlib.Path):
        self.project_path = project_path

        TheBrain.PROJECT_PATH = self.project_path

        self.project = self.load_project()

        self.main_window.main_frame.destroy()
        self.main_window.main_frame = BaseProjectView(master=self.main_window) # todo

    @log_it
    def go_back_to_main_menu_or_base_pro_view(self):
        if self.project_path:
            self.go_to_base_project_view(self.project_path) # todo: if temp_layer load from temp layer
        else:
            self.main_menu_view()

    @log_it
    def load_project(self):
        with open(self.project_path.joinpath("base.json"), mode="r") as f:
            self.project = json.load(f)
        return self.project

    @log_it
    def save_project(self):
        with open(self.project_path.joinpath("base.json"), mode="w") as file:
            json.dump(self.project, file, indent=4)

    @log_it
    def add_project_to_list_of_projects(self):
        cwd_path = pathlib.Path(os.getcwd())
        check_if_project_list_exists = cwd_path.joinpath("projects_list.json").exists()
        if check_if_project_list_exists:
            with open(cwd_path.joinpath("projects_list.json"), mode="r") as file:
                projects_list = json.load(file)
            projects_list["projects"].append(str(self.project_path))
        else:
            projects_list = {"projects": [str(self.project_path)]}

        with open(cwd_path.joinpath("projects_list.json"), mode="w") as file:
            json.dump(projects_list, file, indent=4)

    @log_it
    def load_list_of_projects(self):
        cwd_path = pathlib.Path(os.getcwd())
        check_if_project_list_exists = cwd_path.joinpath("projects_list.json").exists()
        if check_if_project_list_exists:
            with open(cwd_path.joinpath("projects_list.json"), mode="r") as file:
                projects_list = json.load(file)
            return projects_list["projects"]
        return []

    @log_it
    def settings_view(self):
        # lang, dark - light view mode
        ...

    @log_it
    def open_project_view(self):
        self.main_window.main_frame.destroy()
        projects_list = self.load_list_of_projects()
        self.main_window.main_frame = OpenProjectView(master=self.main_window, projects_list=projects_list)

    @log_it
    def new_project_view(self):
        self.main_window.main_frame.destroy()
        self.main_window.main_frame = NewProjectView(master=self.main_window)

    @log_it
    def main_menu_view(self):
        self.main_window.main_frame.destroy()
        self.main_window.main_frame = MainMenuView(master=self.main_window)

    @log_it
    def collect_garbage(self):
        gc.collect()

    @log_it
    def clear_detail_and_zoom_pan(self):
        self.main_window.main_frame.zoom_pan.destroy()
        self.main_window.main_frame.detail_pan.destroy()

    @log_it
    def enable_menubar_btns(self):
        self.main_window.menu_bar.enable_buttons()

    @log_it
    def mount_detail_and_zoom_pan(self, file_id):

        path_to_img = self.project["files"][file_id]["path"]
        path_to_img = self.project_path.joinpath(path_to_img)

        if self.file_pat_formats.search(path_to_img.suffix):
            try:

                self.main_window.main_frame.zoom_pan = ZoomPan(master=self.main_window.main_frame, path_to_img=path_to_img)
                self.main_window.main_frame.zoom_pan.grid(row=0, column=1)
            except tk.TclError:
                return
            except KeyError:
                return
        else:
            self.main_window.main_frame.zoom_pan = MyLabel(master=self.main_window.main_frame, text="Available formats: .jpg, .jpeg, .png")
            self.main_window.main_frame.zoom_pan.grid(row=0, column=1)

        self.main_window.main_frame.detail_pan = DetailPan(master=self.main_window.main_frame, file_id=file_id)
        self.main_window.main_frame.detail_pan.grid(row=1, column=0)

        # try:
        #     self.main_window.main_frame.detail_pan = DetailPan(master=self.main_window.main_frame, file_id=file_id)
        #     self.main_window.main_frame.detail_pan.grid(row=1, column=0)
        # except tk.TclError:
        #     return
        # except KeyError:
        #     return
        #
        #     # self.driver.detail_view = DetailPan(master=self.driver.detail_pan, driver=self.driver,
        #     #                                     item_index=item_index, file_id=file_id)
        #     # todo: ZoomPan
        #     self.master.brain.mount_detail_and_zoom_pan(file_id=file_id, path_to_screen=path_to_screen)
        #     self.driver.zoom_view = ZoomPan(master=self.driver.right_pan, path=path_to_screen)

        self.collect_garbage()

class AddFilesFromDirView(MyFrame):
    @log_it
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.grid()
        self.file_pat_formats = self.master.brain.file_pat_formats
        # self.file_pat_formats = re.compile(r"(.png$|.jpg$|.jpeg$|.pdf$)", flags=re.IGNORECASE)
        self.project = None
        self.project_path = None
        self.d_path = tk.StringVar()

        self.columnconfigure((0, 2), weight=1)
        self.columnconfigure((1), weight=0, minsize=550)
        self.rowconfigure((0, 5), weight=1)
        self.rowconfigure((1, 2, 3, 4), weight=0)

        MyLabel(master=self, text="Add files from selected directory").grid(column=0, row=0, columnspan=3, sticky=tk.S)
        MyLabel(master=self, text="Selected directory:").grid(column=0, row=1, sticky=tk.E)

        self.ent_selected_directory = MyEntry(master=self, textvariable=self.d_path, width=500)
        self.ent_selected_directory.grid(column=1, row=1)

        MyButton(master=self, text="Browse", command=self.browse).grid(column=2, row=1, sticky=tk.W)

        MyLabel(master=self, text="Options").grid(column=1, row=2)

        self.all_or_some_files_var = tk.IntVar()

        self.copy_all_files = MyRadiobutton(master=self,
                                            text="Copy all files",
                                            variable=self.all_or_some_files_var,
                                            value=1)
        self.copy_all_files.grid(column=1, row=3)
        self.copy_all_files.select()

        self.copy_some_files = MyRadiobutton(master=self,
                                             text="Copy only .jpg, .jpeg, .png files. (The rest will be ignored) ",
                                             variable=self.all_or_some_files_var,
                                             value=0)
        self.copy_some_files.grid(column=1, row=4)

        MyButton(master=self, text="Go back", command=self.go_back).grid(column=0, row=4, sticky=tk.E)
        MyButton(master=self, text="Add files", command=self.add_files_from_dir).grid(column=2, row=4, sticky=tk.W)

    @log_it
    def browse(self):
        dialog = MyDialogWindow_AskDir(self.d_path, title="Select a directory with files to add")
        self.master.brain.main_window.wait_window(dialog)

    @log_it
    def go_back(self):
        self.master.brain.go_to_base_project_view(self.master.brain.project_path)

    @log_it
    def add_files_from_dir(self):

        self.master.brain.add_files_from_dir(self.d_path.get(), self.all_or_some_files_var.get())



class MenuBar(MyMenu):
    @log_it
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.file_menu = MyMenu(master=self, tearoff=0)
        self.add_cascade(label="File", menu=self.file_menu)

        self.file_menu.add_command(label=LANG.get("new_pro"), command=self.new_project)
        self.file_menu.add_command(label=LANG.get("open_pro"), command=self.open_project)
        self.file_menu.add_command(label="Settings", command=self.settings)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=LANG.get("quit"), command=self.close)

        # MyButton(master=self.menu, text=LANG.get("new_pro"), command=self.new_project).grid()
        # MyButton(master=self.menu, text=LANG.get("open_pro"), command=self.open_project).grid()
        # MyButton(master=self.menu, text="Settings", command=self.settings).grid()
        # MyButton(master=self.menu, text=LANG.get("quit"), command=self.close).grid()

        self.add_command(label="Add files to project", command=self.add_files_from_dir_view, state=tk.DISABLED)  # todo : del or activate/deactivate - currently not necessary

    @log_it
    def enable_buttons(self):
        self.entryconfigure("Add files to project", state=tk.NORMAL)

    @log_it
    def new_project(self):
        self.master.brain.new_project_view()

    @log_it
    def open_project(self):
        self.master.brain.open_project_view()

    @log_it
    def settings(self):
        self.master.brain.settings_view()

    @log_it
    def add_files_from_dir_view(self):
        self.master.brain.add_files_from_dir_view()

    @log_it
    def close(self):
        self.destroy()
        self.master.destroy()

class BaseProjectView(MyFrame):
    @log_it
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grid()
        self.master.title(f'{LANG.get("title")}: {self.master.brain.project_path}')

        self.brain = self.master.brain

        self.columnconfigure(0, weight=1, minsize=500)
        self.columnconfigure(1, weight=1, minsize=800)

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # self.menu_bar = MenuBar(master=self)
        self.brain.enable_menubar_btns()

        self.tree_pan = TreePan(master=self)
        self.tree_pan.grid(row=0, column=0)

        self.detail_pan = MyLabel(master=self, text="Detail Pan")
        self.detail_pan.grid(row=1, column=0)

        self.zoom_pan = MyLabel(master=self, text="Zoom Pan")
        self.zoom_pan.grid(row=0, column=1)

        self.general_pan = MyLabel(master=self, text="General Pan")
        self.general_pan.grid(row=1, column=1)



class MainWindow(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title(LANG.get("title"))
        width = self.winfo_screenwidth()
        height = self.winfo_screenheight()
        self.geometry(f"{width}x{height}")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        ctk.set_appearance_mode("dark")
        gc.disable()

        self.brain = TheBrain(self)

        self.menu_bar = MenuBar(master=self)
        self.config(menu=self.menu_bar)

        self.main_frame = MainMenuView(master=self)

    # def clear_main_frame(self):
    #     self.main_frame.destroy()


class OpenProjectView(MyFrame):
    @log_it
    def __init__(self, projects_list=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.projects_list = projects_list
        # self.projects_list = []

        self.project_path = tk.StringVar()

        self.grid()
        self.columnconfigure((0, 2), weight=1)
        self.columnconfigure((1), weight=0, minsize=550)
        self.rowconfigure((0, 3), weight=1)
        self.rowconfigure((1), weight=0, minsize=200)
        self.rowconfigure((2), weight=0, minsize=50)

        MyLabel(master=self, text="Open project").grid(column=0, row=0, columnspan=3, sticky=tk.S)

        self.list_of_projects = MyListbox(master=self)
        self.list_of_projects.grid(column=1, row=1)

        self.list_of_projects.insert(tk.END, *projects_list)
        self.list_of_projects.bind("<<ListboxSelect>>", self.listbox_select)

        MyLabel(master=self, text="Selected project:").grid(column=0, row=2, sticky=tk.E)

        self.ent_selected_project = MyEntry(master=self, textvariable=self.project_path, width=500)
        self.ent_selected_project.grid(column=1, row=2)

        MyButton(master=self, text="Browse", command=self.browse).grid(column=2, row=2, sticky=tk.W)
        MyButton(master=self, text="Go back", command=self.go_back).grid(column=0, row=3, sticky=tk.NE)
        MyButton(master=self, text="Open project", command=self.go_to_base_project_view).grid(column=2, row=3, sticky=tk.NW)

    @log_it
    def listbox_select(self, event):
        index = self.list_of_projects.curselection()
        if index:
            self.project_path.set(self.list_of_projects.get(index[0]))

    @log_it
    def browse(self):
        MyDialogWindow_AskDir(self.project_path, title="Select a directory with a project")

    @log_it
    def go_back(self):
        self.master.brain.go_back_to_main_menu_or_base_pro_view() # change in the brain: if self.project is set ->
                                            # go back to base pro view (keep the same view -> load from Temp_layer?

    @log_it
    def go_to_base_project_view(self):

        project_path = pathlib.Path(self.project_path.get())

        if project_path.joinpath("base.json").exists():
            self.master.brain.go_to_base_project_view(project_path)
        else:
            messagebox.showerror(title="Wrong directory", message="A directory must contain base.json file to be 'a project'. Selected folder does not include base.json file.")


class NewProjectView(MyFrame):
    @log_it
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.grid()
        self.columnconfigure((0, 2), weight=1)
        self.columnconfigure((1), weight=0, minsize=550)
        self.rowconfigure((0, 2), weight=1)
        self.rowconfigure((1), weight=0, minsize=50)

        self.d_path = tk.StringVar(master=self)
        self.d_path.set(os.getcwd())

        MyLabel(master=self, text="Create project").grid(column=0, row=0, columnspan=3, sticky=tk.S)
        MyLabel(master=self, text="Select location:").grid(column=0, row=1, sticky=tk.E)

        self.ent_project_path = MyEntry(master=self, textvariable=self.d_path, width=500)
        self.ent_project_path.grid(column=1, row=1)

        MyButton(master=self, text="Change location", command=self.change_location).grid(column=2, row=1, sticky=tk.W)
        MyButton(master=self, text="Go back", command=self.go_back).grid(column=0, row=2, sticky=tk.NE)
        MyButton(master=self, text="Create Project", command=self.create_project).grid(column=2, row=2, sticky=tk.NW)

    @log_it
    def change_location(self):
        MyDialogWindow_AskDir_CreateDir(string_var_to_set_path=self.d_path, title="Select a directory to set a project")
        # ask_dir = filedialog.askdirectory(initialdir=self.d_path.get(), mustexist=False, title="Select a directory to set a project")
        # if ask_dir:
        #     self.d_path.set(ask_dir)

    @log_it
    def create_project(self):
        temp_path = pathlib.Path(self.d_path.get())
        if temp_path.is_absolute():
            self.master.brain.create_project(temp_path)
        else:
            messagebox.showerror(title="Wrong path", message="Pass an absolute path, eg. C:\\My documents\\Files...")

    @log_it
    def go_back(self):
        self.master.brain.go_back_to_main_menu_or_base_pro_view() # change in the brain: if self.project is set ->
                                            # go back to base pro view (keep the same view -> load from Temp_layer?


class MainMenuView(MyFrame):
    @log_it
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.grid()

        self.menu = MyFrame(master=self)
        self.menu.grid()

        self.menu.rowconfigure((0, 1, 2, 3), weight=0, minsize=40)
        self.menu.columnconfigure(0, weight=1)

        MyButton(master=self.menu, text=LANG.get("new_pro"), command=self.new_project).grid()
        MyButton(master=self.menu, text=LANG.get("open_pro"), command=self.open_project).grid()
        MyButton(master=self.menu, text="Settings", command=self.settings).grid()
        MyButton(master=self.menu, text=LANG.get("quit"), command=self.close).grid()

    @log_it
    def new_project(self):
        self.master.brain.new_project_view()

    @log_it
    def open_project(self):
        self.master.brain.open_project_view()

    @log_it
    def settings(self):
        self.master.brain.settings_view()

    @log_it
    def close(self):
        self.destroy()
        self.master.destroy()


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()