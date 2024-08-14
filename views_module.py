import pathlib
import os
import re
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
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
                          MyRadiobutton,
                          MyText)
from lang_module import LANG
from panels import (DetailPan,
                    ZoomPan,
                    TreePan,
                    RotatingPan)


@log_exception_decorator(log_exception)
class ManageSourcesView(MyFrame):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.grid()

        self.columnconfigure((0, 1, 2), weight=1)
        self.rowconfigure((0, 1), weight=1)

        self.add_sources_pan = MyFrame(master=self)
        self.add_sources_pan.grid(row=0, column=0)

        self.add_sources_pan.columnconfigure(0, weight=1)
        self.add_sources_pan.rowconfigure((0, 2), weight=0)
        self.add_sources_pan.rowconfigure(1, weight=1)

        MyLabel(master=self.add_sources_pan, text=LANG.get("Pass_sources")).grid(row=0, column=0)

        self.add_sources_textbox = MyText(master=self.add_sources_pan)
        self.add_sources_textbox.grid(row=1, column=0, sticky=tk.NSEW)
        self.add_sources_textbox.insert("1.0", text=LANG.get("insert_sources"))

        self.add_sources_pan_bottom = MyFrame(master=self.add_sources_pan)
        self.add_sources_pan_bottom.grid(row=2, column=0)

        self.add_sources_pan_bottom.columnconfigure((0, 1), weight=1)
        self.add_sources_pan_bottom.rowconfigure(0, weight=0)

        MyButton(master=self.add_sources_pan_bottom, text=LANG.get("add_sources"), command=self.add_sources_to_project).grid(row=0, column=0)
        MyButton(master=self.add_sources_pan_bottom, text=LANG.get("del_source_pro"), command=self.del_sources_from_project).grid(row=0, column=1)

        self.zoom_pan = MyFrame(master=self)
        self.zoom_pan.grid(row=0, column=1, columnspan=2)

        self.bottom_pan = MyFrame(master=self)
        self.bottom_pan.grid(row=1, column=0, columnspan=3)

        self.bottom_pan.columnconfigure((0, 2), weight=1)
        self.bottom_pan.columnconfigure(1, weight=0)
        self.bottom_pan.rowconfigure(0, weight=1)

        self.sources_listbox = MyListbox(master=self.bottom_pan)
        self.sources_listbox.grid(row=0, column=0, sticky=tk.NSEW)

        self.vertical_menu = MyFrame(master=self.bottom_pan)
        self.vertical_menu.grid(row=0, column=1)
        self.vertical_menu.columnconfigure(0, weight=0)
        self.vertical_menu.rowconfigure((0, 1, 2, 3, 4), weight=0)

        MyButton(master=self.vertical_menu, text=LANG.get("add_source"), command=self.add_sources).grid(row=0, column=0)
        MyButton(master=self.vertical_menu, text=LANG.get("del_source"), command=self.del_sources).grid(row=1, column=0)
        MyButton(master=self.vertical_menu, text=LANG.get("go_back"), command=self.go_back).grid(row=2, column=0)

        self.files_tree = ttk.Treeview(master=self.bottom_pan, show="headings")
        self.files_tree.grid(row=0, column=2, sticky=tk.NSEW)

        columns = ("f_name", "source")
        self.files_tree.configure(columns=columns)

        self.files_tree.heading("f_name", text=LANG.get("f_name"))
        self.files_tree.heading("source", text=LANG.get("source"))

        self.files_tree.bind('<<TreeviewSelect>>', self.tree_selecting_item)

        for _uuid, data in self.master.brain.project["files"].items():
            self.files_tree.insert(
                "",
                tk.END,
                iid=_uuid,
                values=(
                    data.get("f_name"),
                    data.get("source"),
                )
            )

        self.file_pat_formats = re.compile(r"(.png$|.jpg$|.jpeg$)", flags=re.IGNORECASE)

        self.sources_listbox.insert(tk.END, *self.master.brain.project["sources"])

    def tree_selecting_item(self, event):
        _uuid = self.files_tree.focus()
        if _uuid:
            try:
                path_to_img = self.master.brain.project["files"][_uuid]["path"]
            except KeyError as key_error:
                my_logger.debug(f"ManageSourcesView.tree_selecting_item: zoom_pan error: {key_error}")
                return

            path_to_img = self.master.brain.project_path.joinpath(path_to_img)

            my_logger.debug(f"ManageSourcesView.tree_selecting_item: path to img {path_to_img}")
            self.zoom_pan.destroy()

            if self.file_pat_formats.search(path_to_img.suffix):
                try:
                    self.zoom_pan = ZoomPan(master=self, path_to_img=path_to_img)
                    self.zoom_pan.grid(row=0, column=1, columnspan=2)
                except tk.TclError as tk_error:
                    my_logger.debug(f"ManageSourcesView.tree_selecting_item: zoom_pan error: {tk_error}")
                    return
                except KeyError as key_error:
                    my_logger.debug(f"ManageSourcesView.tree_selecting_item: zoom_pan error: {key_error}")
                    return
            else:
                self.zoom_pan = MyLabel(master=self, text=LANG.get("Available_formats"))
                self.zoom_pan.grid(row=0, column=1, columnspan=2)
                my_logger.debug(f"TheBrain.mount_detail_and_zoom_pan: unavailable format: {path_to_img}")

            self.master.brain.collect_garbage()

    def add_sources_to_project(self):
        new_sources = self.add_sources_textbox.get("1.0", tk.END).split("\n")
        new_sources = dict.fromkeys(new_sources, None)

        self.master.brain.project["sources"] += new_sources.keys()
        no_duplicates = dict.fromkeys(self.master.brain.project["sources"], None)
        self.master.brain.project["sources"] = list(no_duplicates.keys())
        self.master.brain.save_project()

        self.sources_listbox.delete(0, tk.END)
        self.sources_listbox.insert(tk.END, *self.master.brain.project["sources"])

    def del_sources_from_project(self):
        index = self.sources_listbox.curselection()
        if index:
            index = index[0]
            source = self.sources_listbox.get(index)

            self.master.brain.project["sources"].remove(source)
            self.master.brain.save_project()

            self.sources_listbox.delete(index)

    def add_sources(self):
        source_index = self.sources_listbox.curselection()
        _uuid = self.files_tree.focus()

        if source_index and _uuid:
            new_source = self.sources_listbox.get(source_index[0])

            self.master.brain.project["files"][_uuid]["source"] = new_source
            self.master.brain.save_project()

            self.files_tree.item(
                _uuid,
                values=(
                    (
                        self.master.brain.project["files"][_uuid]["f_name"],
                        self.master.brain.project["files"][_uuid]["source"],
                    )
                )
            )

    def del_sources(self):
        _uuid = self.files_tree.focus()

        if _uuid:
            self.master.brain.project["files"][_uuid]["source"] = ""
            self.master.brain.save_project()

            self.files_tree.item(
                _uuid,
                values=(
                    (
                        self.master.brain.project["files"][_uuid]["f_name"],
                        self.master.brain.project["files"][_uuid]["source"],
                    )
                )
            )

    def go_back(self):
        self.master.brain.go_to_base_project_view(self.master.brain.project_path)


@log_exception_decorator(log_exception)
class AddFilesView(MyFrame):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.grid()
        # self.file_pat_formats = self.master.brain.file_pat_formats
        # self.file_pat_formats = re.compile(r"(.png$|.jpg$|.jpeg$|.pdf$)", flags=re.IGNORECASE)
        # self.project = None
        # self.project_path = None
        self.f_paths = tuple()

        self.columnconfigure((0, 2), weight=1)
        self.columnconfigure(1, weight=0, minsize=750)
        self.rowconfigure((0, 5), weight=1)
        self.rowconfigure((1, 2, 3, 4), weight=0)

        MyLabel(master=self, text=LANG.get("add_selected_files")).grid(column=0, row=0, columnspan=3, sticky=tk.S)
        MyLabel(master=self, text=LANG.get("sel_dir")).grid(column=0, row=1, sticky=tk.E)

        self.listbox_selected_files = MyListbox(master=self)
        self.listbox_selected_files.grid(column=1, row=1, sticky=tk.NSEW)

        MyButton(master=self, text=LANG.get("browse"), command=self.browse).grid(column=2, row=1, sticky=tk.W)

        MyButton(master=self, text=LANG.get("go_back"), command=self.go_back).grid(column=0, row=4, sticky=tk.E)
        MyButton(master=self, text=LANG.get("add_files"), command=self.add_files).grid(column=2, row=4, sticky=tk.W)

        my_logger.debug("AddFilesView initiated successfully")

    def browse(self):
        my_logger.debug("AddFilesView.browse: waiting for a dir to select")
        # dialog = MyDialogWindow_AskDir(self.d_path, title="Select a directory with files to add")
        # self.master.brain.main_window.wait_window(dialog)

        # ask_dir = filedialog.askdirectory(initialdir=os.getcwd(), title=LANG.get("sel_dir_with_files"))
        ask_dir = filedialog.askopenfilenames(initialdir=os.getcwd(), title="Select a directory with files to add", multiple=True)
        if ask_dir:
            self.listbox_selected_files.delete("0", tk.END)
            self.listbox_selected_files.insert(tk.END, *ask_dir)
            my_logger.debug(f"AddFilesView.browse: selected: {'\n'.join(ask_dir)}")
            self.f_paths = ask_dir

    def go_back(self):
        my_logger.debug("AddFilesView.go_back: go back to self.master.brain.go_to_base_project_view(self.master.brain.project_path)")
        self.master.brain.go_to_base_project_view(self.master.brain.project_path)

    def add_files(self):
        my_logger.debug(f"AddFilesView.add_files: self.master.brain.add_files({'\n'.join(self.f_paths)}")
        self.master.brain.add_files(self.f_paths)


@log_exception_decorator(log_exception)
class AddDirView(MyFrame):
    """Allows adding dirs with files to a project
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

        MyLabel(master=self, text=LANG.get("add_files_from_dir")).grid(column=0, row=0, columnspan=3, sticky=tk.S)
        MyLabel(master=self, text=LANG.get("sel_dir")).grid(column=0, row=1, sticky=tk.E)

        self.ent_selected_directory = MyEntry(master=self, textvariable=self.d_path, width=500)
        self.ent_selected_directory.grid(column=1, row=1)

        MyButton(master=self, text=LANG.get("browse"), command=self.browse).grid(column=2, row=1, sticky=tk.W)

        MyLabel(master=self, text=LANG.get("options")).grid(column=1, row=2)

        self.all_or_some_files_var = tk.IntVar()

        self.copy_all_files = MyRadiobutton(master=self,
                                            text=LANG.get("copy_all_files"),
                                            variable=self.all_or_some_files_var,
                                            value=1)
        self.copy_all_files.grid(column=1, row=3)
        self.copy_all_files.select()

        self.copy_some_files = MyRadiobutton(master=self,
                                             text=LANG.get("copy_only"),
                                             variable=self.all_or_some_files_var,
                                             value=0)
        self.copy_some_files.grid(column=1, row=4)

        MyButton(master=self, text=LANG.get("go_back"), command=self.go_back).grid(column=0, row=4, sticky=tk.E)
        MyButton(master=self, text=LANG.get("add_files"), command=self.add_dir).grid(column=2, row=4, sticky=tk.W)

        my_logger.debug("AddDirView initiated successfully")

    def browse(self):
        my_logger.debug("AddDirView.browse: waiting for a dir to select")
        # dialog = MyDialogWindow_AskDir(self.d_path, title="Select a directory with files to add")
        # self.master.brain.main_window.wait_window(dialog)

        ask_dir = filedialog.askdirectory(initialdir=os.getcwd(), title=LANG.get("sel_dir_with_files"))
        # ask_dir = filedialog.askopenfilenames(initialdir=os.getcwd(), title="Select a directory with files to add", multiple=True)
        if ask_dir:
            self.d_path.set(ask_dir)
            my_logger.debug(f"AddDirView.browse: selected: {self.d_path.get()}")

    def go_back(self):
        my_logger.debug("AddDirView.go_back: go back to self.master.brain.go_to_base_project_view(self.master.brain.project_path)")
        self.master.brain.go_to_base_project_view(self.master.brain.project_path)

    def add_dir(self):
        my_logger.debug(f"AddDirView.add_dir: self.master.brain.add_dir({self.d_path.get()}, {self.all_or_some_files_var.get()}")
        self.master.brain.add_dir(self.d_path.get(), self.all_or_some_files_var.get())


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

        self.project_path = tk.StringVar()

        self.grid()
        self.columnconfigure((0, 2), weight=1)
        self.columnconfigure(1, weight=0, minsize=550)
        self.rowconfigure((0, 3), weight=1)
        self.rowconfigure(1, weight=0, minsize=200)
        self.rowconfigure(2, weight=0, minsize=50)

        MyLabel(master=self, text=LANG.get("open_pro")).grid(column=0, row=0, columnspan=3, sticky=tk.S)

        self.list_of_projects = MyListbox(master=self)
        self.list_of_projects.grid(column=1, row=1)

        self.list_of_projects.insert(tk.END, *projects_list)
        self.list_of_projects.bind("<<ListboxSelect>>", self.listbox_select)

        MyLabel(master=self, text=LANG.get("sel_project")).grid(column=0, row=2, sticky=tk.E)

        self.ent_selected_project = MyEntry(master=self, textvariable=self.project_path, width=500)
        self.ent_selected_project.grid(column=1, row=2)

        MyButton(master=self, text=LANG.get("browse"), command=self.browse).grid(column=2, row=2, sticky=tk.W)
        MyButton(master=self, text=LANG.get("go_back"), command=self.go_back).grid(column=0, row=3, sticky=tk.NE)
        MyButton(master=self, text=LANG.get("open_pro"), command=self.go_to_base_project_view).grid(column=2, row=3, sticky=tk.NW)

    def listbox_select(self, event) -> None:
        index = self.list_of_projects.curselection()
        if index:
            self.project_path.set(self.list_of_projects.get(index[0]))

    def browse(self) -> None:
        # MyDialogWindow_AskDir(self.project_path, title="Select a directory with a project")
        ask_dir = filedialog.askdirectory(initialdir=os.getcwd(), title=LANG.get("sel_dir_proj"))
        if ask_dir:
            self.project_path.set(ask_dir)
            my_logger.debug(f"AddFilesFromDirView.browse: selected: {self.project_path.get()}")

    def go_back(self) -> None:
        self.master.brain.go_back_to_main_menu_or_base_pro_view()

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

        MyLabel(master=self, text=LANG.get("new_pro_info")).grid(column=0, row=0, columnspan=3, sticky=tk.S)
        MyLabel(master=self, text=LANG.get("sel_location")).grid(column=0, row=1, sticky=tk.E)

        self.ent_project_path = MyEntry(master=self, textvariable=self.d_path, width=500)
        self.ent_project_path.grid(column=1, row=1)

        MyButton(master=self, text=LANG.get("chang_location"), command=self.change_location).grid(column=2, row=1, sticky=tk.W)
        MyButton(master=self, text=LANG.get("go_back"), command=self.go_back).grid(column=0, row=2, sticky=tk.NE)
        MyButton(master=self, text=LANG.get("new_pro"), command=self.create_project).grid(column=2, row=2, sticky=tk.NW)

        my_logger.debug("NewProjectView created successfully")

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

        MyButton(master=self.menu, text=LANG.get("new_pro"), command=self.new_project).grid(padx=10, pady=10)
        MyButton(master=self.menu, text=LANG.get("open_pro"), command=self.open_project).grid(padx=10, pady=10)
        MyButton(master=self.menu, text=LANG.get("quit"), command=self.close).grid(padx=10, pady=10)

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
