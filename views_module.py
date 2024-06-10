import pathlib
import os
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from my_logging_module import (log_exception_decorator,
                               log_exception,
                               my_logger)
from base_classes import (MyButton,
                          MyDialogWindow_AskDir,
                          MyDialogWindow_AskDir_CreateDir,
                          MyEntry,
                          MyFrame,
                          MyLabel,
                          MyListbox,
                          MyRadiobutton,)
from lang_module import LANG
from panels import (DetailPan,
                    ZoomPan,
                    TreePan,
                    RotatingPan)


@log_exception_decorator(log_exception)
class AddFilesFromDirView(MyFrame):
    """Allowes adding dirs with files to a project
    """
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.grid()
        self.file_pat_formats = self.master.brain.file_pat_formats
        # self.file_pat_formats = re.compile(r"(.png$|.jpg$|.jpeg$|.pdf$)", flags=re.IGNORECASE)
        self.project = None
        self.project_path = None
        self.d_path = tk.StringVar()

        self.columnconfigure((0, 2), weight=1)
        self.columnconfigure(1, weight=0, minsize=550)
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

        my_logger.debug("AddFilesFromDirView initiated successfully")

    def browse(self):
        my_logger.debug("AddFilesFromDirView.browse: waiting for a dir to select")
        # dialog = MyDialogWindow_AskDir(self.d_path, title="Select a directory with files to add")
        # self.master.brain.main_window.wait_window(dialog)

        ask_dir = filedialog.askdirectory(initialdir=os.getcwd(), title="Select a directory with files to add")
        if ask_dir:
            self.d_path.set(ask_dir)
            my_logger.debug(f"AddFilesFromDirView.browse: selected: {self.d_path.get()}")

    def go_back(self):
        my_logger.debug("AddFilesFromDirView.go_back: go back to self.master.brain.go_to_base_project_view(self.master.brain.project_path)")
        self.master.brain.go_to_base_project_view(self.master.brain.project_path)

    def add_files_from_dir(self):
        my_logger.debug(f"AddFilesFromDirView.add_files_from_dir: self.master.brain.add_files_from_dir({self.d_path.get()}, {self.all_or_some_files_var.get()}")
        self.master.brain.add_files_from_dir(self.d_path.get(), self.all_or_some_files_var.get())


@log_exception_decorator(log_exception)
class BaseProjectView(MyFrame):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.grid()
        self.master.title(f'{LANG.get("title")}: {self.master.brain.project_path}')

        self.brain = self.master.brain

        # self.columnconfigure(0, weight=1, minsize=500)
        # self.columnconfigure(1, weight=1, minsize=800)
        #
        # self.rowconfigure(0, weight=1, minsize=1000)
        # self.rowconfigure(1, weight=1)

        self.columnconfigure(0, weight=1, )
        self.columnconfigure(1, weight=1, )

        self.rowconfigure(0, weight=1, )
        self.rowconfigure(1, weight=0, )

        # self.menu_bar = MenuBar(master=self)
        self.brain.enable_menubar_btns()

        self.tree_pan = TreePan(master=self)
        self.tree_pan.grid(row=0, column=0)

        self.detail_pan = DetailPan(master=self)
        self.detail_pan.grid(row=1, column=0)

        self.zoom_pan = MyLabel(master=self, text="Zoom Pan")
        self.zoom_pan.grid(row=0, column=1)

        self.rotating_pan = RotatingPan(master=self)
        self.rotating_pan.grid(row=1, column=1)

        my_logger.debug("BaseProjectView initiated successfully")


@log_exception_decorator(log_exception)
class OpenProjectView(MyFrame):
    def __init__(self, projects_list=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.projects_list = projects_list
        # self.projects_list = []

        self.project_path = tk.StringVar()

        self.grid()
        self.columnconfigure((0, 2), weight=1)
        self.columnconfigure(1, weight=0, minsize=550)
        self.rowconfigure((0, 3), weight=1)
        self.rowconfigure(1, weight=0, minsize=200)
        self.rowconfigure(2, weight=0, minsize=50)

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

    def listbox_select(self, event) -> None:
        index = self.list_of_projects.curselection()
        if index:
            self.project_path.set(self.list_of_projects.get(index[0]))

    def browse(self) -> None:
        MyDialogWindow_AskDir(self.project_path, title="Select a directory with a project")

    def go_back(self) -> None:
        self.master.brain.go_back_to_main_menu_or_base_pro_view() # change in the brain: if self.project is set ->
                                            # go back to base pro view (keep the same view -> load from Temp_layer?

    def go_to_base_project_view(self) -> None:

        project_path = pathlib.Path(self.project_path.get())

        if project_path.joinpath("base.json").exists():
            self.master.brain.go_to_base_project_view(project_path)
        else:
            messagebox.showerror(title="Wrong directory", message="A directory must contain base.json file to be 'a project'. Selected folder does not include base.json file.")


@log_exception_decorator(log_exception)
class NewProjectView(MyFrame):
    """A new project menu.
    """
    def __init__(self, *args, **kwargs) -> None:
        """Called by TheBrain.new_project_view()"""
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

        my_logger.debug("NewProjectView created sucessfully")

    def change_location(self) -> None:
        """Opens a new dialog window.
        """
        # MyDialogWindow_AskDir_CreateDir(string_var_to_set_path=self.d_path, title="Select a directory to set a project")
        ask_dir = filedialog.askdirectory(initialdir=self.d_path.get(), mustexist=False, title="Select a directory to set a project")
        if ask_dir:
            self.d_path.set(ask_dir)

    def create_project(self) -> None:
        """Go to self.master.brain.create_project(temp_path)
        """
        temp_path = pathlib.Path(self.d_path.get())
        if temp_path.is_absolute():
            my_logger.debug(f"Go to self.master.brain.create_project({temp_path})")
            self.master.brain.create_project(temp_path)
        else:
            my_logger.debug(f"Wrong path : {temp_path}")
            messagebox.showerror(title="Wrong path", message="Pass an absolute path, eg. C:\\My documents\\Files...")

    def go_back(self) -> None:
        self.master.brain.go_back_to_main_menu_or_base_pro_view() # change in the brain: if self.project is set ->
                                            # go back to base pro view (keep the same view -> load from Temp_layer?


@log_exception_decorator(log_exception)
class MainMenuView(MyFrame):
    """Main menu window - here we start our journey.
    This is the first object placed in root window (MainWindow).
    It's just a standard menu. All functions refer to TheBrain which directs traffic between windows, panels and project files.
    You can go back to the MainMenuView any time - use menu bar.
    """
    def __init__(self, *args, **kwargs) -> None:
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

        my_logger.debug("MainMenuView initiated successfully")

    def new_project(self) -> None:
        """goes to self.master.brain.new_project_view()"""
        my_logger.debug("MainMenuView - goes to self.master.brain.new_project_view()")
        self.master.brain.new_project_view()

    def open_project(self) -> None:
        """goes to self.master.brain.open_project_view()"""
        my_logger.debug("MainMenuView - goes to self.master.brain.open_project_view()")
        self.master.brain.open_project_view()

    def settings(self) -> None:
        """goes to self.master.brain.settings_view()"""
        my_logger.debug("MainMenuView - goes to self.master.brain.settings_view()")
        self.master.brain.settings_view()

    def close(self) -> None:
        """goes to self.destroy(); self.master.destroy()"""
        my_logger.debug("MainMenuView - goes to self.destroy(); self.master.destroy()")
        self.destroy()
        self.master.destroy()
