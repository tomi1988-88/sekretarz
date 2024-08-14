import tkinter as tk
from my_logging_module import (log_exception_decorator,
                               log_exception,
                               my_logger)
from base_classes import MyMenu
from lang_module import LANG
from panels import DistributeMan


@log_exception_decorator(log_exception)
class MenuBar(MyMenu):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.file_menu = MyMenu(master=self, tearoff=0, font=(None, 18))
        self.add_cascade(label=LANG.get("file"), menu=self.file_menu)

        self.file_menu.add_command(label=LANG.get("new_pro"), command=self.new_project)
        self.file_menu.add_command(label=LANG.get("open_pro"), command=self.open_project)
        # self.file_menu.add_command(label=LANG.get("settings"), command=self.settings)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=LANG.get("quit"), command=self.close)

        self.add_command(label=LANG.get("add_folder"), command=self.add_dir_view, state=tk.DISABLED)
        self.add_command(label=LANG.get("add_files"), command=self.add_files_view, state=tk.DISABLED)
        self.add_command(label=LANG.get("manage_sources"), command=self.manage_sources_view, state=tk.DISABLED)
        self.add_command(label=LANG.get("distr_man"), command=self.distribute, state=tk.DISABLED)

        my_logger.debug("MenuBar initiated successfully")

    def enable_buttons(self) -> None:
        self.entryconfigure(LANG.get("add_folder"), state=tk.NORMAL)
        self.entryconfigure(LANG.get("add_files"), state=tk.NORMAL)
        self.entryconfigure(LANG.get("manage_sources"), state=tk.NORMAL)
        self.entryconfigure(LANG.get("distr_man"), state=tk.NORMAL)
        my_logger.debug("MenuBar.enable_buttons: buttons enabled")

    def new_project(self) -> None:
        my_logger.debug("MenuBar.new_project: self.master.brain.new_project_view()")
        self.master.brain.new_project_view()

    def open_project(self) -> None:
        my_logger.debug("MenuBar.open_project: self.master.brain.open_project_view()")
        self.master.brain.open_project_view()

    # def settings(self):
    #     my_logger.debug("MenuBar.settings: self.master.brain.settings_view()")
    #     self.master.brain.settings_view()

    def add_dir_view(self) -> None:
        my_logger.debug("MenuBar.add_files_from_dir_view: self.master.brain.add_dir_view()")
        self.master.brain.add_dir_view()

    def add_files_view(self) -> None:
        self.master.brain.add_files_view()

    def manage_sources_view(self) -> None:
        self.master.brain.manage_sources_view()

    def distribute(self) -> None:
        DistributeMan(master=self)

    def close(self) -> None:
        self.destroy()
        self.master.destroy()
        my_logger.debug("MenuBar.close: Closed")
