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
import webbrowser
from tkinter import ttk
import datetime as dt
from tkinter import filedialog, messagebox
from __sekretarz_lang import LANG
from base_classes import (MyFrame,
                          MyLabel,
                          MyButton,
                          MyEntry,
                          MyListbox,
                          MyTopLevel,
                          MyMenu,
                          MyScrollableFrame,
                          MyRadiobutton,
                          MyDialogWindow_AskDir,
                          MyDialogWindow_AskDir_CreateDir,
                          MyInputDialog)
from panels import (TreePan,
                    ZoomPan,
                    DetailPan,
                    RotatingPan,
                    FileHistoryPan,
                    ProjectHistoryPan)
from typing import (List,
                    Dict,)
from my_logging_module import (log_exception_decorator,
                               log_exception,
                               my_logger)
from the_brain_module import TheBrain
from menu_bar_module import MenuBar
from views_module import MainMenuView

class TempLayer:
    def __init__(self, *args, **kwargs):
        ... # todo: maybe it might work as a variable storage for the whole base view eg:
        # temp_layer.curr_widget = base pro view which is not displayed in main window?
        # class TempLayer(MyFrame)


class LangVariables:
    def __init__(self, *args, **kwargs):
        ...


@log_exception_decorator(log_exception)
class MainWindow(ctk.CTk):
    """Root for all windows and widgets.
    Keeps reference to TheBrain and MenuBar (menu bar is always visible at the top of the window).
    Garbage collection is disabled here as well
    """
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.title(LANG.get("title"))
        width = self.winfo_screenwidth()
        height = self.winfo_screenheight()
        self.geometry(f"{width}x{height}")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        ctk.set_appearance_mode("dark")
        gc.disable()

        self.brain = TheBrain(main_window=self)

        self.menu_bar = MenuBar(master=self)
        self.config(menu=self.menu_bar)

        self.main_frame = MainMenuView(master=self)

        my_logger.debug("Main window initiated successfully")


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
