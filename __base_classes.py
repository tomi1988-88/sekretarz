import time
import tkinter as tk
import customtkinter as ctk
import os
import re
import pathlib
import json
from tkinter import ttk
from tkinter import filedialog, messagebox
from __sekretarz_lang import LANG


class MyButton(ctk.CTkButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.configure(pady=5, padx=10)


class MyLabel(ctk.CTkLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(pady=5, padx=10)


class MyEntry(ctk.CTkEntry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.configure(pady=5, padx=10)

class MyListbox(tk.Listbox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def grid(self, **kwargs):
        if kwargs.get("sticky"):
            super(MyListbox, self).grid(**kwargs)
        else:
            super(MyListbox, self).grid(sticky=tk.NSEW, **kwargs)


class MyFrame(ctk.CTkFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def grid(self, **kwargs):
        if kwargs.get("sticky"):
            super(MyFrame, self).grid(**kwargs)
        else:
            super(MyFrame, self).grid(sticky=tk.NSEW, **kwargs)


class MyScrollableFrame(ctk.CTkScrollableFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MyOptionMenu(ctk.CTkOptionMenu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MyTopLevel(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MyMenu(tk.Menu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MyRadiobutton(ctk.CTkRadioButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MyDialogWindow_AskDir(ctk.CTkToplevel):
    def __init__(self, string_var_to_set_path, title, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.string_var_to_set_path = string_var_to_set_path
        self.title(title)

        self.columnconfigure((0, 2), weight=1)
        self.columnconfigure((1), weight=1, minsize=550)

        self.rowconfigure((1, 3), weight=0)
        self.rowconfigure((2), weight=1, minsize=200)
        self.rowconfigure((0, 4), weight=1)

        self.upper_row = MyFrame(master=self)
        self.upper_row.grid(column=1, row=1)

        self.upper_row.rowconfigure(0)
        self.upper_row.columnconfigure(0, weight=0)
        self.upper_row.columnconfigure(1, weight=1)
        self.upper_row.columnconfigure(2, weight=0)

        MyLabel(master=self.upper_row, text="Directory: ").grid(column=0, row=0)

        cwd_path = pathlib.Path(os.getcwd())
        paths_for_dir_option_menu = [str(p) for p in [cwd_path] + list(cwd_path.parents)]
        filepaths_in_current_dir = self.get_filepaths(cwd_path)

        self.dir_option_menu = MyOptionMenu(master=self.upper_row, values=paths_for_dir_option_menu, command=self.dir_option_change)
        self.dir_option_menu.grid(column=1, row=0, sticky=tk.EW)

        MyButton(master=self.upper_row, text="Go up", command=self.go_dir_up).grid(row=0, column=2)

        self.central_row = MyFrame(master=self)
        self.central_row.grid(column=1, row=2)
        self.central_row.rowconfigure(0)
        self.central_row.columnconfigure(0, weight=1)
        self.central_row.columnconfigure(1, weight=0)
        self.tree = ttk.Treeview(master=self.central_row, show="headings")
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)

        scroll_y = ttk.Scrollbar(master=self.central_row, orient=tk.VERTICAL, command=self.tree.yview)
        scroll_y.grid(row=0, column=1, sticky=tk.NS)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.bind('<Button-1>', self.tree_select)
        self.tree.bind("<Double-1>", self.tree_double_click)

        columns = ("File name", )
        self.tree.configure(columns=columns)
        self.tree.heading("File name", text="File name")

        for f_path in filepaths_in_current_dir:
            self.tree.insert("", index=tk.END, iid=f_path, values=(f_path.name, ))

        self.bottom_row = MyFrame(master=self)
        self.bottom_row.grid(column=1, row=3)

        self.bottom_row.rowconfigure(0, weight=0)
        self.bottom_row.columnconfigure((0, 2, 3), weight=0)
        self.bottom_row.columnconfigure((1), weight=1)

        MyLabel(master=self.bottom_row, text="Selected: ").grid(row=0, column=0)

        self.var_selected_dir = tk.StringVar(master=self.bottom_row)
        self.ent_selected_dir = MyEntry(master=self.bottom_row, textvariable=self.var_selected_dir, width=500)
        self.ent_selected_dir.grid(row=0, column=1)

        self.var_selected_dir.set(cwd_path)

        MyButton(master=self.bottom_row, text="Select", command=self.select_dir).grid(row=0, column=2)
        MyButton(master=self.bottom_row, text="Go back", command=self.destroy).grid(row=0, column=3)

        self.grab_set()

    def go_dir_up(self):
        dir_up = pathlib.Path(self.dir_option_menu.get()).parent

        paths_for_dir_option_menu = [str(p) for p in [dir_up] + list(dir_up.parents)]
        filepaths_in_current_dir = self.get_filepaths(dir_up)

        self.dir_option_menu.configure(values=paths_for_dir_option_menu)
        self.dir_option_menu.set(paths_for_dir_option_menu[0])
        self.tree.delete(*self.tree.get_children())

        for f_path in filepaths_in_current_dir:
            self.tree.insert("", index=tk.END, iid=f_path, values=(f_path.name,))
        self.var_selected_dir.set("")

    def dir_option_change(self, event):
        curr_dir = pathlib.Path(self.dir_option_menu.get())

        paths_for_dir_option_menu = [str(p) for p in [curr_dir] + list(curr_dir.parents)]
        filepaths_in_current_dir = self.get_filepaths(curr_dir)

        self.dir_option_menu.configure(values=paths_for_dir_option_menu)
        self.tree.delete(*self.tree.get_children())

        for f_path in filepaths_in_current_dir:
            self.tree.insert("", index=tk.END, iid=f_path, values=(f_path.name,))
        self.var_selected_dir.set(curr_dir)

    def tree_select(self, event):
        # self.var_selected_dir.set(self.tree.selection()[0])
        self.var_selected_dir.set(self.tree.focus())

    def tree_double_click(self, event):
        # dst_path = pathlib.Path(self.var_selected_dir.get())
        # dst_path = pathlib.Path(self.tree.selection()[0])
        dst_path = pathlib.Path(self.tree.focus())
        if dst_path.is_dir():
            paths_for_dir_option_menu = [str(p) for p in [dst_path] + list(dst_path.parents)]
            filepaths_in_current_dir = self.get_filepaths(dst_path)

            self.dir_option_menu.configure(values=paths_for_dir_option_menu)
            self.dir_option_menu.set(dst_path)
            self.tree.delete(*self.tree.get_children())

            for f_path in filepaths_in_current_dir:
                self.tree.insert("", index=tk.END, iid=f_path, values=(f_path.name,))

            self.var_selected_dir.set(dst_path)

    def select_dir(self):
        self.string_var_to_set_path.set(self.var_selected_dir.get())
        self.destroy()

    def get_filepaths(self, path):
        filepaths = list(path.iterdir())
        filepaths.sort(key=lambda x: x.name)
        filepaths.sort(key=lambda x: x.is_dir())
        return filepaths


class MyDialogWindow_AskDir_CreateDir(MyDialogWindow_AskDir):
    def __init__(self, string_var_to_set_path, title, *args, **kwargs):
        super().__init__(string_var_to_set_path, title,*args, **kwargs)

        self.upper_row.columnconfigure(3, weight=0)
        MyButton(master=self.upper_row, text="Create dir", command=self.create_dir).grid(row=0, column=3)

    def create_dir(self):
        dialog = MyDialog(text="Pass a name for new directory", title="Create a new directory")
        new_dir = dialog.get_input()
        if new_dir:
            new_dir_path = pathlib.Path(self.dir_option_menu.get()).joinpath(new_dir)
            try:
                new_dir_path.mkdir()
            except FileExistsError:
                messagebox.showerror(title="A directory already exists.", message="A directory already exists. Try a different name")
                return
            except OSError:
                messagebox.showerror(title="Wrong path.", message="Wrong path name. Some characters might be not allowed (check: < > : \" / \\ | ? *).")
                return
            self.tree.insert("",index=tk.END, iid=new_dir_path, values=(new_dir, ))


class MyDialog(ctk.CTkInputDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grab_set()


class ExtraField(ttk.Frame):
    def __init__(self, field_name=None, field_val=None, file_id=None, *args, **kwargs):
        ...
        super().__init__(**kwargs)

        self.field_name = field_name
        self.field_val = field_val
        self.file_id = file_id

        self.columnconfigure(0)
        self.columnconfigure(1)
        self.columnconfigure(2)

        self.lbl_field = ttk.Label(master=self, text=self.field_name)
        self.lbl_field.grid(column=0, row=0)
        self.ent_field = ttk.Entry(master=self, width=10)
        self.ent_field.grid(column=1, row=0)
        self.ent_field.insert(tk.END, self.field_val)
        self.btn_field = ttk.Button(master=self, text=LANG.get("update"), command=self.update)
        self.btn_field.grid(column=2, row=0)

        self.project = self.nametowidget(".").load_project()

    def update(self):
        self.field_val = self.ent_field.get()

        self.project["files"][self.file_id]["extra_fields"][self.lbl_field["text"]] = self.field_val

        self.nametowidget(".").project = self.project
        self.nametowidget(".").save_project()

    def get_values(self):
        return self.file_id, self.field_name, self.field_val
