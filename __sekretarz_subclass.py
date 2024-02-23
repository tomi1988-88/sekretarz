import os
import json
import re
import pathlib
import shutil
import time
import tkinter as tk
import datetime as dt
from tkinter import (ttk,
                     messagebox,
                     filedialog,
                     scrolledtext)
from __sekretarz_lang import LANG
from __zoomed_canvas import ZoomAdvanced


class ExtraField(ttk.Frame):
    def __init__(self, field_name=None, field_val=None, file_id=None, project=None, **kwargs):
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
        self.btn_field = ttk.Button(master=self, text=LANG.get("update"), command=lambda x=project, y=self.file_id: self.update(x, y)) #todo
        self.btn_field.grid(column=2, row=0)

    def update(self, project, file_id):
        self.field_val = self.ent_field.get()

        project["files"][file_id]["extra_fields"][self.lbl_field["text"]] = self.field_val

        with open(pathlib.Path(project["main_dir"], "base.json"), mode="w") as file:
            json.dump(project, file, indent=4)

    def get_values(self):
        return self.file_id, self.field_name, self.field_val




class NewProWindow(tk.Toplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.geometry("600x200")
        self.title(f'{LANG.get("new_pro")}')

        self.main_frame = ttk.Frame(master=self)
        self.main_frame.grid()
        self.main_frame.columnconfigure(0)
        self.main_frame.columnconfigure(1)
        self.main_frame.rowconfigure(0)
        self.main_frame.rowconfigure(1)
        self.main_frame.rowconfigure(2)

        ttk.Label(master=self.main_frame, text=LANG.get("proj_name")).grid(row=0, column=0)

        self.ent_pro_name = ttk.Entry(master=self.main_frame)
        self.ent_pro_name.grid(row=0, column=1, sticky=tk.EW, padx=10)

        ttk.Label(master=self.main_frame, text=LANG.get("proj_local")).grid(row=1, column=0)

        self.curr_dir = os.getcwd()
        ttk.Label(master=self.main_frame, text=self.curr_dir).grid(row=1, column=1)

        ttk.Button(master=self.main_frame, text=LANG.get("go_back"), command=self.destroy).grid(row=2, column=0)

        ttk.Button(
            master=self.main_frame,
            text=LANG.get("new_pro"),
            command=lambda x=self.ent_pro_name.get: self.create_project(x())
        ).grid(row=2, column=1)

        self.pat_format = re.compile(r"[<>:\"/\\|?*]")

    def create_project(self, project_name):
        if self.pat_format.search(project_name) or project_name == "":
            messagebox.showerror(f'{LANG.get("error")}', f'{LANG.get("wrong_dir_name")}')
            return

        path = pathlib.Path(self.curr_dir, project_name)

        if path.exists():
            messagebox.showerror(f'{LANG.get("error")}', f'{LANG.get("dir_exists")}')
            return

        path.mkdir()

        base_proj = {
            "name": project_name,
            "main_dir": str(path),
            "files": {},
            "labels": [],
            "last_id": 0,
            "links": []
        }

        with open(pathlib.Path(path, "base.json"), mode="w") as file:
            json.dump(base_proj, file, indent=4)

        self.master.project = base_proj
        self.master.base_project_view()
        self.destroy() # może będzie trzeba przesunąć do MainWindow.base_pro_view()


class BaseProjectView(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super(BaseProjectView, self).__init__(*args, **kwargs)

        self.master.title(f'{LANG.get("title")}: {self.master.project["main_dir"]}')

        self.columnconfigure(0, weight=1, minsize=700)
        self.columnconfigure(1, weight=1, minsize=1000)

        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        self.menu_bar = ttk.Frame(master=self)
        self.menu_bar.grid(row=0, column=0, sticky=tk.W)

        self.project = self.master.load_project()

        ttk.Button(master=self.menu_bar, text=LANG.get("add_folder"),
                                    command=self.add_folder).pack(side=tk.LEFT, padx=5, pady=2)
        #
        # ttk.Button(master=self.menu_bar, text=LANG.get("manage_links"),
        #                               command=lambda x=project: self.manage_links(x)).pack(side=tk.LEFT, padx=5, pady=2)
        #
        # ttk.Button(master=self.menu_bar, text=LANG.get("list_files"), command=self.list_files).pack(side=tk.LEFT)
        #
        # ttk.Button(master=self.menu_bar, text=LANG.get("labels"), command=lambda x=project: self.labels(x)).pack(side=tk.LEFT)
        #
        # ttk.Button(master=self.menu_bar, text=LANG.get("del_pro"), ).pack(side=tk.LEFT)
        #
        # ttk.Button(master=self.menu_bar, text=LANG.get("filter_labels"),
        #                                command=lambda x=project: self.filter_labels(x)).pack(side=tk.LEFT)

        ttk.Label(master=self.menu_bar, text=f'{LANG.get("proj_name")} {self.project.get("name")}').pack(padx=15, pady=10)

        self.left_pan = ttk.Frame(master=self)
        self.left_pan.grid(row=1, column=0, sticky=tk.NSEW)
        self.tree_view = TreePan(master=self.left_pan)
        self.tree_view.grid()

        self.right_pan = ttk.Frame(master=self)
        self.right_pan.grid(row=0, column=1, rowspan=3, sticky=tk.NSEW)

        self.down_pan = ttk.Frame(master=self)
        self.down_pan.grid(row=2, column=0, sticky=tk.NSEW)

        self.pat_formats = re.compile(r"(.png$|.jpg$|.jpeg$)")

        if self.project["files"]:
            self.tree_view.populate()
        else:
            ttk.Label(master=self.down_pan, text=LANG.get("no_files")).grid()

    def __ignore_patterns(self, path, names):
        return [f for f in names if pathlib.Path(path, f).is_file() and not self.pat_formats.search(f)]

    def add_folder(self):
        d_path = filedialog.askdirectory(initialdir=os.getcwd(), title=LANG.get("add_folder"))
        if not d_path:
            return

        d_path = pathlib.Path(d_path)
        main_dir = self.project["main_dir"]

        target_dir = pathlib.Path(main_dir, d_path.stem)

        if target_dir.exists():
            target_dir = pathlib.Path(main_dir, d_path.stem + str(int(time.time())))

        shutil.copytree(d_path, target_dir, ignore=self.__ignore_patterns)

        pro_counter = int(self.project["last_id"])

        for (dpath, dirs, files) in os.walk(target_dir):
            for file in files:
                path = pathlib.Path(dpath, file)
                pro_counter += 1
                self.project["files"][f"{pro_counter} - {path.name}"] = {
                    "id": pro_counter,
                    "source": "",
                    "f_name": path.name,
                    "path": str(path),
                    "labels": [],
                    "comment": "",
                    "extra_fields": {},
                    "c_time": path.stat().st_mtime
                }

        files_added = pro_counter - self.project["last_id"]

        self.project["last_id"] = pro_counter

        self.master.save_project()

        if files_added > 0:
            messagebox.showinfo(LANG.get("add_folder"), f'{LANG.get("update_copy_finish")}{files_added}')
            self.reset_tree()
        else:
            messagebox.showerror(LANG.get("add_folder"), LANG.get("no_files_added"))

    def reset_tree(self):
        self.tree_view.populate()


class TreePan(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super(TreePan, self).__init__(*args, **kwargs)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        self.tree = ttk.Treeview(master=self, show="headings")

        columns = ("id", "source", "path", "labels", "c_time")
        self.tree.configure(columns=columns)

        self.tree.heading("id", text=LANG.get("id"))
        self.tree.heading("source", text=LANG.get("source"))
        self.tree.heading("path", text=LANG.get("path"))
        self.tree.heading("labels", text=LANG.get("labels"))
        self.tree.heading("c_time", text=LANG.get("c_time"))

        self.tree.grid(row=0, column=0, sticky=tk.NSEW)

        scroll_y = ttk.Scrollbar(master=self, orient=tk.VERTICAL, command=self.tree.yview)
        scroll_y.grid(row=0, column=1, sticky=tk.NS)
        self.tree.configure(yscrollcommand=scroll_y.set)

        scroll_x = ttk.Scrollbar(master=self, orient=tk.HORIZONTAL, command=self.tree.xview)
        scroll_x.grid(row=1, column=0, sticky=tk.EW)
        self.tree.configure(xscrollcommand=scroll_x.set)

        self.tree.bind('<<TreeviewSelect>>', self.selecting_item)

        self.project = self.master.master.project

    def populate(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for file_id, i in self.project["files"].items():
            self.tree.insert("", tk.END, values=(file_id, i.get("source"), i.get("path"), i.get("labels"),
                                                 dt.datetime.fromtimestamp(i.get("c_time")).strftime(
                                                     "%Y-%m-%d %H-%M-%S ")))

    def selecting_item(self, event):
        for child in self.master.master.right_pan.winfo_children():
            child.destroy()

        for child in self.master.master.down_pan.winfo_children():
            child.destroy()

        self.project = self.master.master.master.load_project()

        files = self.project["files"]

        curr_item = self.tree.focus()

        item = self.tree.item(curr_item)

        self.master.master.down_pan.columnconfigure(0)
        self.master.master.down_pan.columnconfigure(1)
        self.master.master.down_pan.columnconfigure(2)

        for row in range(8):
            self.master.master.down_pan.rowconfigure(row)

        # item_vals = item.get("values")
        #
        # ttk.Label(master=self.master.down_pan, text=LANG.get("id")).grid(row=0, column=0)
        # ent_name = ttk.Entry(master=self.master.down_pan, width=100)
        # ent_name.insert(tk.END, item_vals[0])
        # ent_name.grid(row=0, column=1)
        #
        # ttk.Button(master=self.master.down_pan, text=LANG.get("f_rename")).grid(row=0, column=2)
        #
        # ttk.Label(master=self.master.down_pan, text=LANG.get("source")).grid(row=1, column=0)
        # ent_src = ttk.Entry(master=self.master.down_pan, width=100)
        # ent_src.insert(tk.END, item_vals[1])
        # ent_src.grid(row=1, column=1)
        #
        # ttk.Button(master=self.master.down_pan, text=LANG.get("s_rename")).grid(row=1, column=2)
        #
        # ttk.Label(master=self.master.down_pan, text=LANG.get("path")).grid(row=2, column=0)
        # path_broken = item_vals[2]
        # if len(item_vals[2]) > 100:
        #     path_broken = path_broken[:99] + "\n    " + path_broken[99:]
        # lbl_path = ttk.Label(master=self.master.down_pan, text=path_broken, width=100)
        # lbl_path.grid(row=2, column=1)
        #
        # ttk.Label(master=self.master.down_pan, text=LANG.get("labels")).grid(row=3, column=0)
        # frame_lbls = ttk.Frame(master=self.master.down_pan)
        # frame_lbls.grid(row=3, column=1)
        #
        # ttk.Button(master=self.master.down_pan, text=LANG.get("manage_labels"),
        #            command=lambda x=project, y=item_vals, z=curr_item: self.manage_labels(x, y, z)).grid(row=3,
        #                                                                                                  column=2)
        #
        # for lbl in files[item_vals[0]]["labels"]:
        #     ttk.Label(master=frame_lbls, text=lbl).pack(side=tk.LEFT, padx=5, pady=2)
        #
        # ttk.Label(master=self.master.down_pan, text=LANG.get("comment")).grid(row=4, column=0)
        #
        # comment_temp = files.get(item_vals[0]).get("comment")
        # tbox_com = scrolledtext.ScrolledText(master=self.master.down_pan, height=4)
        # tbox_com.insert("1.0", comment_temp)
        # tbox_com.grid(row=4, column=1)
        #
        # ttk.Button(master=self.master.down_pan, text=LANG.get("alter_comment")).grid(row=4, column=2)
        #
        # ttk.Label(master=self.master.down_pan, text=LANG.get("extra_fields")).grid(row=5, column=0)
        # self.frame_extra = ttk.Frame(master=self.master.down_pan)
        # self.frame_extra.grid(row=5, column=1)
        #
        # self.frame_extra.columnconfigure(0)
        # self.frame_extra.columnconfigure(1)
        # self.frame_extra.columnconfigure(2)
        #
        # fields_temp = files.get(item_vals[0]).get("extra_fields")
        #
        # num_fields = len(fields_temp)
        #
        # for r in range(num_fields):
        #     if r % 3 == 0:
        #         self.frame_extra.rowconfigure(r // 3)
        #
        # for index, (f, val) in enumerate(fields_temp.items()):
        #     ExtraField(master=self.frame_extra, field_name=f, field_val=val, file_id=item_vals[0],
        #                project=project).grid(row=index // 3, column=index % 3)
        #
        # ttk.Button(master=self.master.down_pan, text=LANG.get("manage_fields"),
        #            command=lambda x=project, y=item_vals[0]: self.manage_fields(x, y)).grid(row=5, column=2)
        #
        # ttk.Label(master=self.master.down_pan, text=LANG.get("c_time")).grid(row=6, column=0)
        # lbl_ctime = ttk.Label(master=self.master.down_pan, text=str(item_vals[4]), width=100)
        # lbl_ctime.grid(row=6, column=1)
        #
        # ttk.Button(master=self.master.down_pan, text=LANG.get("del_file")).grid(row=7, column=1)
        #
        # ZoomAdvanced(mainframe=self.master.right_pan, path=pathlib.Path(item.get("values")[2])).grid(sticky=tk.NSEW)
