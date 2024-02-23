import copy
import tkinter as tk
import os
import re
import pathlib
import time
import shutil
import json
import datetime as dt
from tkinter import ttk
from tkinter import filedialog, scrolledtext, messagebox
from __zoomed_canvas import ZoomAdvanced
from __sekretarz_lang import LANG
from __sekretarz_subclass import (NewProWindow,
                                  BaseProjectView)

# files = {"id": "", "source": "link/app/whatever", "f_name": "nazwa pliku", "path": "file location", "labels": [], "comment": "", "extra_fields": {}, "c_time": ""}
#
# files_ = {"id + f_name": {"id": "", "source": "link/app/whatever", "f_name": "nazwa pliku", "path": "file location", "labels": [], "comment": "", "extra_fields": {}, "c_time": ""}}
#
#
base_proj = {
    "name": "",
    "main_dir": "",
    "files": {},
    "labels": [],
    "last_id": 0,
    "links": []
    }




class MainWindow(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)

        self.title(LANG.get("title"))
        self.geometry("400x300")

        self.main_frame = ttk.Frame(master=self, )
        self.main_frame.grid()

        self.menu = ttk.Frame(master=self.main_frame)
        self.menu.grid()

        self.btn_create_pro = ttk.Button(master=self.menu, text=LANG.get("new_pro"), command=self.new_pro)
        self.btn_create_pro.grid()

        self.btn_open_pro = ttk.Button(master=self.menu, text=LANG.get("open_pro"), command=self.open_pro)
        self.btn_open_pro.grid()

        # self.btn_list_files = ttk.Button(master=self.menu, text=LANG.get("list_files"), command=self.list_files)
        # self.btn_list_files.grid()

        self.btn_quit = ttk.Button(master=self.menu, text=LANG.get("quit"), command=self.destroy)
        self.btn_quit.quit()

        self.pat_formats = re.compile(r"(.png$|.jpg$|.jpeg$)")

        self.project = None

        self.temp_window_new_project = None

    def new_pro(self):
        """NewProWindow sets MainWindow.project and executes MainWindow.base_project_view()"""
        self.temp_window_new_project = NewProWindow(master=self)

    def base_project_view(self):
        for c in self.main_frame.winfo_children():
            c.destroy()

        self.main_frame = BaseProjectView(master=self)
        self.main_frame.grid(sticky=tk.NSEW)

    def open_pro(self):
        d_path = filedialog.askdirectory(initialdir=os.getcwd(), title=LANG.get("sel_dir"))

        if not d_path:
            return

        if "base.json" not in os.listdir(d_path):
            messagebox.showerror(f'{LANG.get("error")}', f'{LANG.get("lack_of_base_file")}')
            return

        with open(pathlib.Path(d_path, "base.json"), mode="r") as f:
            self.project = json.load(f)

        self.base_project_view()

    def save_project(self):
        with open(pathlib.Path(self.project["main_dir"], "base.json"), mode="w") as file:
            json.dump(self.project, file, indent=4)

    def load_project(self):
        with open(pathlib.Path(self.project["main_dir"], "base.json"), mode="r") as f:
            self.project = json.load(f)
        return self.project

if __name__ == "__main__":
    App = MainWindow()
    App.mainloop()
