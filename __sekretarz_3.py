import tkinter as tk
import customtkinter as ctk
import os
import re
import pathlib
import json
import gc
import shutil
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



class ProjectHandler:
    def __init__(self, *args, **kwargs):
        ...


class TempLayer:
    def __init__(self, *args, **kwargs):
        ...

class LangVariables:
    def __init__(self, *args, **kwargs):
        ...


class TheBrain:
    def __init__(self, main_window, *args, **kwargs):
        self.main_window = main_window
        self.project_path = None
        self.project = None
        self.d_path = tk.StringVar() # (maybe unnsecesary) variable for different dir_paths - is cleared to "" every time when a particular func is called
        self.list_of_uncopied_files = []

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
            "last_id": 0,
            "links": [],
            "binds": {},
            "last_id_binds": 0,
            "dist_schemas": {}
        }

        self.project = base_proj_data
        self.save_project()
        self.add_project_to_list_of_projects()
        self.go_to_base_project_view(self.project_path)

    def go_to_base_project_view(self, project_path: pathlib.Path):
        self.project_path = project_path

        self.project = self.load_project()

        self.main_window.main_frame.destroy()
        self.main_window.main_frame = BaseProjectView(master=self.main_window) # todo

    def load_project(self):
        with open(self.project_path.joinpath("base.json"), mode="r") as f:
            self.project = json.load(f)
        return self.project

    def save_project(self):
        with open(self.project_path.joinpath("base.json"), mode="w") as file:
            json.dump(self.project, file, indent=4)

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

    def load_list_of_projects(self):
        cwd_path = pathlib.Path(os.getcwd())
        check_if_project_list_exists = cwd_path.joinpath("projects_list.json").exists()
        if check_if_project_list_exists:
            with open(cwd_path.joinpath("projects_list.json"), mode="r") as file:
                projects_list = json.load(file)
            return projects_list["projects"]
        return []

    def settings_view(self):
        # lang, dark - light view mode
        ...

    def open_project_view(self):
        self.main_window.main_frame.destroy()
        projects_list = self.load_list_of_projects()
        self.main_window.main_frame = OpenProjectView(master=self.main_window, projects_list=projects_list)

    def new_project_view(self):
        self.main_window.main_frame.destroy()
        self.main_window.main_frame = NewProjectView(master=self.main_window)

    def main_menu_view(self):
        self.main_window.main_frame.destroy()
        self.main_window.main_frame = MainMenuView(master=self.main_window)

    def collect_garbage(self):
        gc.collect()


    def enable_menubar_btns(self):
        self.main_window.menu_bar.enable_buttons()

    def add_files_from_dir_initial_stage(self):
        self.main_window.main_frame.destroy()
        self.main_window.main_frame = AddFilesFromDirView(master=self.main_window)

    def add_files_from_dir_last_stage(self):
        self.project = self.main_window.main_frame.project
        self.save_project()
        self.main_window.main_frame.destroy()
        self.go_to_base_project_view(self.project_path)  # todo: simplify this func to omit loading part? - procejt just has been saved

        self.collect_garbage()


class AddFilesFromDirView(MyFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.grid()
        self.file_pat_formats = re.compile(r"(.png$|.jpg$|.jpeg$)", flags=re.IGNORECASE)
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

    def _add_files_from_dir__ignore_patterns(self, path, names):
        return [f for f in names if pathlib.Path(path, f).is_file() and not self.file_pat_formats.search(f)]

    def browse(self):
        dialog = MyDialogWindow_AskDir(self.d_path, title="Select a directory with files to add")
        self.master.brain.main_window.wait_window(dialog)

    def go_back(self):
        self.master.brain.go_to_base_project_view(self.master.brain.project_path)

    def add_files_from_dir(self):
        _d_path = pathlib.Path(self.d_path.get())

        if not _d_path.is_absolute():
            messagebox.showerror(title="Wrong path", message="Pass an absolute path, eg. C:\\My documents\\Files...")
            return

        if not _d_path.is_dir():
            _d_path = _d_path.parent
            res = messagebox.askyesno(title="Wrong path", message=f"It's not a directory. Do you want to add files from {_d_path}")
            if not res:
                return

        if self.check_circular_reference(_d_path):
            return

        self.project = self.master.brain.project
        self.project_path = self.master.brain.project_path

        target_dir = pathlib.Path(self.project_path, _d_path.stem)

        res = messagebox.askyesno(title="Confirm", message="Copying ready to start. It may last a few minutes depending on the scale.")
        if not res:
            return

        if target_dir.exists():
            target_dir = pathlib.Path(self.project_path, _d_path.stem + str(int(dt.datetime.today().timestamp())))

        if self.all_or_some_files_var.get():
            shutil.copytree(_d_path, target_dir)
        else:
            shutil.copytree(_d_path, target_dir, ignore=self._add_files_from_dir__ignore_patterns)

        pro_counter = int(self.project["last_id"])

        project_path_parts = self.project_path.parts

        for (dpath, dirs, files) in os.walk(target_dir):
            for file in files:
                path = pathlib.Path(dpath, file)

                path_parts = path.parts

                relative_path = path_parts[len(project_path_parts) - len(path_parts):]
                relative_path = "/".join(relative_path)

                pro_counter += 1
                self.project["files"][f"{pro_counter} - {path.name}"] = {
                    "id": pro_counter,
                    "source": "",
                    "f_name": path.name,
                    "path": relative_path,  # paths are cut so that user can move whole dir with project (dir with base.json and files)
                    "labels": [],
                    "comment": "",
                    "extra_fields": {},
                    "c_time": path.stat().st_mtime,
                    "binds": [],
                }

            files_added = pro_counter - self.project["last_id"]

            messagebox.showinfo(title="Files added", message=f"{files_added} file(s) added to the project.")

            self.project["last_id"] = pro_counter

            self.master.brain.add_files_from_dir_last_stage()  # and save it!

    def check_circular_reference(self, d_path):
        for (_dpath, dirs, files) in os.walk(d_path):
            if _dpath == d_path:
                messagebox.showerror(title="Circular reference", message="A circular reference spotted: You tried to add to the project a directory that contains this project")
                return True


class MenuBar(MyMenu):
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

        self.add_command(label="Add files to project", command=self.add_files_from_dir_initial_stage, state=tk.DISABLED)  # todo : del or activate/deactivate

    def enable_buttons(self):
        self.entryconfigure("Add files to project", state=tk.NORMAL)


    def new_project(self):
        self.master.brain.new_project_view()

    def open_project(self):
        self.master.brain.open_project_view()

    def settings(self):
        self.master.brain.settings_view()

    def add_files_from_dir_initial_stage(self):
        self.master.brain.add_files_from_dir_initial_stage()

    def close(self):
        self.destroy()
        self.master.destroy()

class BaseProjectView(MyFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grid()
        self.master.title(f'{LANG.get("title")}: {self.master.brain.project_path}')

        MyLabel(master=self, text="Base Pro View").grid()

        self.brain = self.master.brain

        self.columnconfigure(0, weight=1, minsize=500)
        self.columnconfigure(1, weight=1, minsize=800)

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        # self.menu_bar = MenuBar(master=self)
        self.brain.enable_menubar_btns()

        self.tree_pan = "tree"
        self.detail_pan = "detail pan"

        self.zoom_pan = "zoom_pan"
        self.general_pan = "general_pan"



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

        self.project_handler = ProjectHandler()
        self.temp_layer = TempLayer()
        self.brain = TheBrain(self)

        self.menu_bar = MenuBar(master=self)
        self.config(menu=self.menu_bar)

        self.main_frame = MainMenuView(master=self)

    # def clear_main_frame(self):
    #     self.main_frame.destroy()


class OpenProjectView(MyFrame):
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

    def listbox_select(self, event):
        index = self.list_of_projects.curselection()
        if index:
            self.project_path.set(self.list_of_projects.get(index[0]))

    def browse(self):
        MyDialogWindow_AskDir(self.project_path, title="Select a directory with a project")
        # ask_dir = filedialog.askdirectory(initialdir=os.getcwd(), mustexist=True,
        #                                   title="Select a directory with base.json file") #
        # ask_dir = filedialog.askdirectory(initialdir=os.getcwd(), mustexist=True, filetypes=[("all files", "*.*")], cannot view files
        #                                   title="Select a directory with base.json file")
        # ask_dir = filedialog.askopenfilename(initialdir=os.getcwd(), filetypes=[("all files", "*.*")], cannot select dir
        #                                   title="Select a directory with base.json file")
        # if ask_dir:
        #     self.project_path.set(ask_dir)

    def go_back(self):
        self.master.brain.main_menu_view()

    def go_to_base_project_view(self):

        project_path = pathlib.Path(self.project_path.get())

        if project_path.joinpath("base.json").exists():
            self.master.brain.go_to_base_project_view(project_path)
        else:
            messagebox.showerror(title="Wrong directory", message="A directory must contain base.json file to be 'a project'. Selected folder does not include base.json file.")


class NewProjectView(MyFrame):
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

    def change_location(self):
        MyDialogWindow_AskDir_CreateDir(string_var_to_set_path=self.d_path, title="Select a directory to set a project")
        # ask_dir = filedialog.askdirectory(initialdir=self.d_path.get(), mustexist=False, title="Select a directory to set a project")
        # if ask_dir:
        #     self.d_path.set(ask_dir)

    def create_project(self):
        temp_path = pathlib.Path(self.d_path.get())
        if temp_path.is_absolute():
            self.master.brain.create_project(temp_path)
        else:
            messagebox.showerror(title="Wrong path", message="Pass an absolute path, eg. C:\\My documents\\Files...")

    def go_back(self):
        self.master.brain.main_menu_view()
        # pro structure: separate files?


class MainMenuView(MyFrame):
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

    def new_project(self):
        self.master.brain.new_project_view()

    def open_project(self):
        self.master.brain.open_project_view()

    def settings(self):
        self.master.brain.settings_view()

    def close(self):
        self.destroy()
        self.master.destroy()


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()