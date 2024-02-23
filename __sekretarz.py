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

LANG_pl = {"title": "Twój sekretarz / Urzędnik 2.0",}

LANG_eng = {
    "title": "Personal assistant / Clerk 2.0",
    "new_pro": "Create New Project",
    "open_pro": "Open Project",
    "add_folder": "Add Folder",
    "add_files": "Add Files",
    "add_links": "Add Sources",
    "manage_links": "Manage Sources (URLs/Info)",
    "assign_sources": "Assign Sources",
    "input_links": "Paste Links or Descriptions for Screenshots\nNew Line (Enter) Separates Successive Links/Desc",
    "list_files": "List Files",
    "labels": "Labels",
    "del_pro": "Delete Project",
    "filter_labels": "Filter Labels",
    "sel_dir": "Select Directory",
    "proj_name": "Project Name:",
    "proj_local": "Project will be saved in:",
    "go_back": "Go Back",
    "quit": "Quit",
    "error": "Error!",
    "wrong_dir_name": "Wrong directory name! No < > : \" / \\ | ? * allowed.",
    "dir_exists": "Dir or file with that name already exists! Try different name.",
    "lack_of_base_file": "It's not a project directory! A directory must include base.json file.",
    "no_files": "No files or directories added to the project.",
    "id": "ID + File name",
    "f_name": "File name",
    "source": "Source",
    "path": "Path",
    "c_time": "Creation time",
    "add_f_copy_files": "Updating project and copying files. I'll let you kon when I'm finished :)",
    "update_copy_finish": "Updating project and copying files finished. Total files added: ",
    "no_files_added": "Something went wrong: No files added.",
    "submit": "Submit",
    "no_links_or_wrong": "Wrong links or no links!",
    'source_added': "Total number of sources has been added: ",
    "show_all_links": "Show all sources in the project",
    "show_unassigned_links": "Show only unassigned sources",
    "assign": "Assign Source to Image",
    "mark_sources_and_img": "Mark Source and Image to Assign",
    "ask_assign": "Do you want to assign Source to Image?",
    "ask_save_changes": "Do you want to save changes?",
    "no_changes_applied": "No changes applied. Nothing to save.",
    "save_changes": "Save Changes",
    "del_source": "Delete Source",
    "no_source_sel": "No Source Selected",
    "save_to_confirm_del": "Save to confirm deletion",
    "f_rename": "Rename File",
    "s_rename": "Rename Source",
    "manage_labels": "Manage Labels",
    "comment": "Comment",
    "extra_fields": "Extra Fields",
    "alter_comment": "Alter Comment",
    "del_file": "Delete File",
    "manage_fields": "Manage Fields",
    "input_new_label": "Input new Label:",
    "add_label": "Add Label",
    "del_label": "Delete Label",
    "edit_label": "Edit Label",
    "no_labels": "Empty string or Label already added",
    "no_label_selected": "No Label selected",
    "ask_del_conf_1": "This operation will affect: ",
    "ask_del_conf_2": " file(s).\nAre you sure you want to delete the Label:\n",
    "rename_label": "Rename Label: ",
    "ask_edit_conf_1": "This operation will affect: ",
    "ask_edit_conf_2": " file(s).\nAre you sure you want to edit the Label:\n",
    "no_new_label_name": "Input a new Label name",
    "label_man": "Label management for: ",
    "sel_lbl": "Select Label",
    "remove_lbl": "Remove Label",
    "confirm_sel": "Save Changes",
    "go_to_labels": "Go to Label Manager",
    "all_lbls": "All Labels in the Project",
    "file_lbls": "Labels related to th File",
    "sel_lbls_incl": "Select Labels to Include",
    "sel_lbls_excl": "Select Labels to Exclude",
    "show_all": "Show all",
    "update": "Update",
    "filter": "Filter",
    "add_field": "Add Field",
    "edit_field": "Edit Field",
    "del_field": "Delete Field",
    "curr_fields": "Current Fields",
    "field_name": "Field name",
    "field_val": "Field value",
}
LANG = LANG_eng


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


class MainWindow(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)

        self.title(LANG.get("title"))
        self.geometry("400x300")

        self.main_frame = ttk.Frame(master=self, )
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.menu = ttk.Frame(master=self.main_frame)
        self.menu.pack(fill=tk.BOTH, expand=True)

        self.btn_create_pro = ttk.Button(master=self.menu, text=LANG.get("new_pro"), command=self.new_pro)
        self.btn_create_pro.pack(padx=5, pady=2)
        # btn_create_pro.grid(row=1, column=0, padx=5, pady=2)

        self.btn_open_pro = ttk.Button(master=self.menu, text=LANG.get("open_pro"), command=self.open_pro)
        self.btn_open_pro.pack(padx=5, pady=2)
        # btn_open_pro.grid(row=1, column=0, padx=5, pady=2)

        self.btn_list_files = ttk.Button(master=self.menu, text=LANG.get("list_files"), command=self.list_files)
        self.btn_list_files.pack(padx=5, pady=2)
        # btn_list_files.grid(row=1, column=0, padx=5, pady=2)

        self.btn_quit = ttk.Button(master=self.menu, text=LANG.get("quit"), command=self.destroy)
        self.btn_quit.pack(padx=5, pady=2)

        self.pat_formats = re.compile(r"(.png$|.jpg$|.jpeg$)")

    def new_pro(self):
        temp_window = tk.Toplevel(master=self)
        temp_window.geometry("600x200")
        temp_window.title(f'{LANG.get("new_pro")}')

        _frm = ttk.Frame(master=temp_window)
        _frm.pack(fill=tk.BOTH, expand=True)

        _frm.columnconfigure([0, 1], weight=1)
        _frm.rowconfigure([0, 1, 2], weight=1)

        lbl_proj_name = ttk.Label(master=_frm, text=LANG.get("proj_name"))
        lbl_proj_name.grid(row=0, column=0)

        ent_name = ttk.Entry(master=_frm)
        ent_name.grid(row=0, column=1, sticky=tk.EW, padx=10)

        lbl_local = ttk.Label(master=_frm, text=LANG.get("proj_local"))
        lbl_local.grid(row=1, column=0)

        _curr_dir = os.getcwd()
        lbl_local_dir = ttk.Label(master=_frm, text=_curr_dir)
        lbl_local_dir.grid(row=1, column=1)

        btn_go_back = ttk.Button(master=_frm, text=LANG.get("go_back"), command=temp_window.destroy)
        btn_go_back.grid(row=2, column=0)

        btn_create = ttk.Button(master=_frm, text=LANG.get("new_pro"),
                                command=lambda x=_curr_dir, y=ent_name.get, z=temp_window: self._create_base_pro(x, y(), z))
        btn_create.grid(row=2, column=1)

    def _create_base_pro(self, curr_dir: str, name: str, w_temp):

        if re.search(r"[<>:\"/\\|?*]", name) or name == "":
            messagebox.showerror(f'{LANG.get("error")}', f'{LANG.get("wrong_dir_name")}')
        else:
            path = pathlib.Path(curr_dir, name)

            if path.exists():
                messagebox.showerror(f'{LANG.get("error")}', f'{LANG.get("dir_exists")}')
                return

            path.mkdir()

            base_proj["name"] = name
            base_proj["main_dir"] = str(path)
            with open(pathlib.Path(path, "base.json"), mode="w") as file:
                json.dump(base_proj, file, indent=4)

            w_temp.destroy()

            self._base_pro_view(path)

    def labels(self, project):
        def add_label(project):
            temp_lbl = ent_add.get()
            if temp_lbl and temp_lbl not in project["labels"]:
                project["labels"].append(temp_lbl)
                lst_box.insert(tk.END, temp_lbl)

                with open(pathlib.Path(project["main_dir"], "base.json"), mode="w") as file:
                    json.dump(project, file, indent=4)

            else:
                messagebox.showerror(LANG.get("labels"), LANG.get("no_labels"))

        def del_label(project):
            temp_lbl = lst_box.curselection()
            if temp_lbl:
                temp_lbl = lst_box.get(temp_lbl[0])
                counter = 0
                for file, val in project["files"].items():
                    if temp_lbl in val.get("labels"):
                        counter += 1

                res = messagebox.askyesno(LANG.get("labels"), f'{LANG.get("ask_del_conf_1")}{counter}{LANG.get("ask_del_conf_2")}{temp_lbl}')

                if res:
                    lst_box.delete(tk.ACTIVE)

                    for file, val in project["files"].items():
                        if temp_lbl in val.get("labels"):
                            val.get("labels").remove(temp_lbl)

                    project["labels"].remove(temp_lbl)

                    with open(pathlib.Path(project["main_dir"], "base.json"), mode="w") as file:
                        json.dump(project, file, indent=4)
                else:
                    return

            else:
                messagebox.showerror(LANG.get("labels"), LANG.get("no_label_selected"))

        def edit_label(project):
            def _edit(project):
                new_lbl = ent_edit.get()

                if not new_lbl:
                    messagebox.showerror(LANG.get("labels"), LANG.get("no_new_label_name"))
                    edit_frame.destroy()
                    return

                counter = 0
                for file, val in project["files"].items():
                    if temp_lbl in val.get("labels"):
                        counter += 1

                res = messagebox.askyesno(LANG.get("labels"), f'{LANG.get("ask_edit_conf_1")}{counter}{LANG.get("ask_edit_conf_2")}{temp_lbl}')

                if res:
                    lst_box.delete(tk.ACTIVE)
                    lst_box.insert(num_of_lbl, new_lbl)

                    for file, val in project["files"].items():
                        if temp_lbl in val.get("labels"):
                            index = val.get("labels").index(temp_lbl)
                            val.get("labels")[index] = new_lbl

                    index = project["labels"].index(temp_lbl)
                    project["labels"][index] = new_lbl

                    with open(pathlib.Path(project["main_dir"], "base.json"), mode="w") as file:
                        json.dump(project, file, indent=4)

                    edit_frame.destroy()
                else:
                    return

            temp_lbl = lst_box.curselection()
            if temp_lbl:
                num_of_lbl = temp_lbl[0]
                temp_lbl = lst_box.get(temp_lbl[0])

                edit_frame = ttk.Frame(master=right_pan)
                edit_frame.grid()

                ttk.Label(master=edit_frame, text=f'{LANG.get("rename_label")}{temp_lbl}').grid()

                ent_edit = ttk.Entry(master=edit_frame, width=60)
                ent_edit.grid()

                ttk.Button(master=edit_frame, text=LANG.get("submit"), command=lambda x=project: _edit(x)).grid()
                ttk.Button(master=edit_frame, text=LANG.get("go_back"), command=edit_frame.destroy).grid()
            else:
                messagebox.showerror(LANG.get("labels"), LANG.get("no_label_selected"))

        self.labels_window = tk.Toplevel(master=self)
        self.labels_window.title(LANG.get("labels"))

        self.frame_labels = ttk.Frame(master=self.labels_window)
        self.frame_labels.grid()
        self.frame_labels.columnconfigure(0)
        self.frame_labels.columnconfigure(1)

        self.frame_labels.rowconfigure(0)

        lst_box = tk.Listbox(master=self.frame_labels, width=60)
        lst_box.grid(row=0, column=0)

        labels = project["labels"]
        for l in labels:
            lst_box.insert(tk.END, l)

        right_pan = ttk.Frame(master=self.frame_labels)
        right_pan.grid(row=0, column=1)

        ttk.Label(master=right_pan, text=LANG.get("input_new_label")).grid()

        ent_add = ttk.Entry(master=right_pan, width=60)
        ent_add.grid()

        ttk.Button(master=right_pan, text=LANG.get("add_label"), command=lambda x=project: add_label(x)).grid()
        ttk.Button(master=right_pan, text=LANG.get("del_label"), command=lambda x=project: del_label(x)).grid()
        ttk.Button(master=right_pan, text=LANG.get("edit_label"), command=lambda x=project: edit_label(x)).grid()
        ttk.Button(master=right_pan, text=LANG.get("go_back"), command=self.labels_window.destroy).grid()

    def manage_labels(self, project, item_vals, curr_item):
        def go_to_label_manager(project):
            self.lbl_manager.destroy()
            self.labels(project)

        def select_lbl():
            sel_lbl = lst_box_all.curselection()
            if sel_lbl and not lst_box_all.get(sel_lbl[0]) in lst_box_file.get(0, tk.END):
                    lst_box_file.insert(tk.END, lst_box_all.get(sel_lbl[0]))

        def remove_lbl():
            rem_lbl = lst_box_file.curselection()
            if rem_lbl:
                lst_box_file.delete(rem_lbl[0])

        def confirm_sel(project, item_vals, curr_item):
            nonlocal file_id
            selected_labels = lst_box_file.get(0, tk.END)
            print(selected_labels)
            project["files"][file_id]["labels"] = list(selected_labels)
            print(project["files"][file_id]["labels"])

            with open(pathlib.Path(project["main_dir"], "base.json"), mode="w") as file:
                json.dump(project, file, indent=4)

            item_vals[3] = " ".join(selected_labels)
            self.tree.item(curr_item, values=tuple(item_vals))

        file_id = item_vals[0]

        self.lbl_manager = tk.Toplevel(master=self)
        self.lbl_manager.title(f"{LANG.get('label_man')}{file_id}")

        self.frame_lbl = ttk.Frame(master=self.lbl_manager)
        self.frame_lbl.grid()

        self.frame_lbl.columnconfigure(0)
        self.frame_lbl.columnconfigure(1)
        self.frame_lbl.columnconfigure(2)

        self.frame_lbl.rowconfigure(0)
        self.frame_lbl.rowconfigure(1)

        self.btn_menu = ttk.Frame(master=self.frame_lbl)
        self.btn_menu.grid(row=1, column=2)

        ttk.Label(master=self.frame_lbl, text=LANG.get("all_lbls")).grid(row=0, column=0)
        ttk.Label(master=self.frame_lbl, text=LANG.get("file_lbls")).grid(row=0, column=1)

        lst_box_all = tk.Listbox(master=self.frame_lbl, width=60)
        lst_box_all.grid(row=1, column=0)

        all_labels = project["labels"]
        for l in all_labels:
            lst_box_all.insert(tk.END, l)

        lst_box_file = tk.Listbox(master=self.frame_lbl, width=60)
        lst_box_file.grid(row=1, column=1)

        file_labels = project["files"][file_id]["labels"]
        for l in file_labels:
            lst_box_file.insert(tk.END, l)

        ttk.Button(master=self.btn_menu, text=LANG.get("sel_lbl"), command=select_lbl).grid(row=0)
        ttk.Button(master=self.btn_menu, text=LANG.get("remove_lbl"), command=remove_lbl).grid(row=1)
        ttk.Button(master=self.btn_menu, text=LANG.get("confirm_sel"), command=lambda x=project, y=item_vals, z=curr_item: confirm_sel(x, y, z)).grid(row=2)
        ttk.Button(master=self.btn_menu, text=LANG.get("go_back"), command=self.lbl_manager.destroy).grid(row=3)
        ttk.Button(master=self.btn_menu, text=LANG.get("go_to_labels"), command=lambda x=project: go_to_label_manager(x)).grid(row=4)

    def filter_labels(self, project):
        def show_all(project):
            for item in self.tree.get_children():
                self.tree.delete(item)

            for file_id, i in project["files"].items():
                self.tree.insert("", tk.END, values=(file_id, i.get("source"), i.get("path"), i.get("labels"),
                                                     dt.datetime.fromtimestamp(i.get("c_time")).strftime(
                                                         "%Y-%m-%d %H-%M-%S ")))

        def filter_lbls(project):
            positive = lst_box_include.curselection()
            negative = lst_box_exclude.curselection()

            positive = [lst_box_include.get(p) for p in positive]
            negative = [lst_box_exclude.get(n) for n in negative]
            print(positive, negative)

            for item in self.tree.get_children():
                self.tree.delete(item)

            if positive and negative:
                for file_id, i in project["files"].items():
                    lbls = i["labels"]
                    p = [l for l in lbls if l in positive]
                    n = [l for l in lbls if l in negative]
                    if p and not n:
                        self.tree.insert("", tk.END, values=(file_id, i.get("source"), i.get("path"), i.get("labels"),
                                                         dt.datetime.fromtimestamp(i.get("c_time")).strftime(
                                                             "%Y-%m-%d %H-%M-%S ")))

            elif positive:
                for file_id, i in project["files"].items():
                    lbls = i["labels"]
                    p = [l for l in lbls if l in positive]
                    if p:
                        self.tree.insert("", tk.END, values=(file_id, i.get("source"), i.get("path"), i.get("labels"),
                                                         dt.datetime.fromtimestamp(i.get("c_time")).strftime(
                                                             "%Y-%m-%d %H-%M-%S ")))
            elif negative:
                for file_id, i in project["files"].items():
                    lbls = i["labels"]
                    n = [l for l in lbls if l in negative]
                    if not n:
                        self.tree.insert("", tk.END, values=(file_id, i.get("source"), i.get("path"), i.get("labels"),
                                                         dt.datetime.fromtimestamp(i.get("c_time")).strftime(
                                                             "%Y-%m-%d %H-%M-%S ")))

        self.temp_filter = tk.Toplevel(master=self)

        self.filter_frame = ttk.Frame(master=self.temp_filter)
        self.filter_frame.grid()

        self.filter_frame.columnconfigure(0)
        self.filter_frame.columnconfigure(1)
        self.filter_frame.columnconfigure(2)

        self.filter_frame.rowconfigure(0)
        self.filter_frame.rowconfigure(1)

        ttk.Label(master=self.filter_frame, text=LANG.get("sel_lbls_incl")).grid(row=0, column=0)
        ttk.Label(master=self.filter_frame, text=LANG.get("sel_lbls_excl")).grid(row=0, column=1)

        menu_frm = ttk.Frame(master=self.filter_frame)
        menu_frm.grid(row=1, column=2)

        labels = project["labels"]

        lst_box_include = tk.Listbox(master=self.filter_frame, selectmode=tk.MULTIPLE, width=60, exportselection=False)
        lst_box_include.grid(row=1, column=0)
        for l in labels:
            lst_box_include.insert(tk.END, l)

        lst_box_exclude = tk.Listbox(master=self.filter_frame, selectmode=tk.MULTIPLE, width=60, exportselection=False)
        lst_box_exclude.grid(row=1, column=1)
        for l in labels:
            lst_box_exclude.insert(tk.END, l)

        ttk.Button(master=menu_frm, text=LANG.get("filter"), command=lambda x=project: filter_lbls(x)).grid()
        ttk.Button(master=menu_frm, text=LANG.get("show_all"), command=lambda x=project: show_all(x)).grid()
        ttk.Button(master=menu_frm, text=LANG.get("go_back"), command=self.temp_filter.destroy).grid()

    def manage_fields(self, project, file_id):

        def add_field(project, file_id):
            def accept_add(project, file_id):
                f_name = field_name.get()
                if f_name:
                    extra_fields = project["files"][file_id]["extra_fields"]

                    if f_name in extra_fields:
                        messagebox.showerror(LANG.get("field_name_exists"), LANG.get("field_name_exists"))
                        return

                    extra_fields[f_name] = field_val.get()

                    with open(pathlib.Path(project["main_dir"], "base.json"), mode="w") as file:
                        json.dump(project, file, indent=4)

                    lst_box_fields.insert(tk.END, f"{f_name} - {field_val.get()}")

            for c in right_pan.winfo_children():
                c.destroy()

            ttk.Label(master=right_pan, text=LANG.get("add_field")).grid()

            ttk.Label(master=right_pan, text=LANG.get("field_name")).grid()
            field_name = ttk.Entry(master=right_pan)
            field_name.grid()

            ttk.Label(master=right_pan, text=LANG.get("field_val")).grid()
            field_val = ttk.Entry(master=right_pan)
            field_val.grid()

            ttk.Button(master=right_pan, text=LANG.get("submit"), command=lambda x=project, y=file_id: accept_add(x, y)).grid()

        def edit_field(project, file_id):
            def accept_edit(project, file_id):

                if not new_val_ent.get():
                    return

                if new_val_ent.get() != f_edit_name:
                    project["files"][file_id]["extra_fields"][new_fname_ent.get()] = new_val_ent.get()

                    del project["files"][file_id]["extra_fields"][f_edit_name]

                    lst_box_fields.delete(f_index)
                    lst_box_fields.insert(f_index, f"{new_fname_ent.get()} /// {new_val_ent.get()}")

                else:
                    project["files"][file_id]["extra_fields"][f_edit_name] = new_val_ent.get()

                with open(pathlib.Path(project["main_dir"], "base.json"), mode="w") as file:
                    json.dump(project, file, indent=4)

            f_index = lst_box_fields.curselection()
            if f_index:
                for c in right_pan.winfo_children():
                    c.destroy()

                f_index = f_index[0]
                f_edit_name, f_edit_val = lst_box_fields.get(f_index).split(" /// ")


                ttk.Label(master=right_pan, text=LANG.get("rename_field")).grid()
                new_fname_ent = ttk.Entry(master=right_pan)
                new_fname_ent.insert(tk.END, f_edit_name)
                new_fname_ent.grid()

                ttk.Label(master=right_pan, text=LANG.get("change_val_field")).grid()
                new_val_ent = ttk.Entry(master=right_pan)
                new_val_ent.insert(tk.END, f_edit_val)
                new_val_ent.grid()

                ttk.Button(master=right_pan, text=LANG.get("submit"), command=lambda x=project, y=file_id: accept_edit(x, y)).grid()

        def del_field(project, file_id):
            ...

        self.temp_manage_fields = tk.Toplevel(master=self)
        self.manage_fields_frame = ttk.Frame(master=self.temp_manage_fields)
        self.manage_fields_frame.grid()

        self.manage_fields_frame.columnconfigure(0)
        self.manage_fields_frame.columnconfigure(1)
        self.manage_fields_frame.columnconfigure(2)

        self.manage_fields_frame.rowconfigure(0)

        left_pan = ttk.Frame(master=self.manage_fields_frame)
        left_pan.grid(column=0, row=0)

        centr_pan = ttk.Frame(master=self.manage_fields_frame)
        centr_pan.grid(column=1, row=0)

        right_pan = ttk.Frame(master=self.manage_fields_frame)
        right_pan.grid(column=2, row=0)

        ttk.Label(master=centr_pan, text=f'{LANG.get("curr_fields")}{file_id}').grid()

        lst_box_fields = tk.Listbox(master=centr_pan, width=60)
        lst_box_fields.grid()

        for f, val in project["files"][file_id]["extra_fields"].items():
            lst_box_fields.insert(tk.END, f"{f} /// {val}")

        ttk.Button(master=left_pan, text=LANG.get("add_field"), command=lambda x=project, y=file_id: add_field(x, y)).grid()
        ttk.Button(master=left_pan, text=LANG.get("edit_field"), command=lambda x=project, y=file_id: edit_field(x, y)).grid()
        ttk.Button(master=left_pan, text=LANG.get("del_field"), command=lambda x=project, y=file_id: del_field(x, y)).grid()
        ttk.Button(master=left_pan, text=LANG.get("go_back"), command=self.temp_manage_fields.destroy).grid()

    def manage_all_fields(self):
        ...

    def _base_pro_view(self, path: pathlib.Path):
        def selecting_item(event):
            nonlocal project

            for child in right_pan.winfo_children():
                child.destroy()

            for child in down_pan.winfo_children():
                child.destroy()

            with open(pathlib.Path(project["main_dir"], "base.json"), mode="r") as f:
                project = json.load(f)

            files = project["files"]

            curr_item = self.tree.focus()

            item = self.tree.item(curr_item)

            down_pan.columnconfigure(0)
            down_pan.columnconfigure(1)
            down_pan.columnconfigure(2)

            down_pan.rowconfigure(0)
            down_pan.rowconfigure(1)
            down_pan.rowconfigure(2)
            down_pan.rowconfigure(3)
            down_pan.rowconfigure(4)
            down_pan.rowconfigure(5)
            down_pan.rowconfigure(6)
            down_pan.rowconfigure(7)

            item_vals = item.get("values")

            ttk.Label(master=down_pan, text=LANG.get("id")).grid(row=0, column=0)
            ent_name = ttk.Entry(master=down_pan, width=100)
            ent_name.insert(tk.END, item_vals[0])
            ent_name.grid(row=0, column=1)

            ttk.Button(master=down_pan, text=LANG.get("f_rename")).grid(row=0, column=2)

            ttk.Label(master=down_pan, text=LANG.get("source")).grid(row=1, column=0)
            ent_src = ttk.Entry(master=down_pan, width=100)
            ent_src.insert(tk.END, item_vals[1])
            ent_src.grid(row=1, column=1)

            ttk.Button(master=down_pan, text=LANG.get("s_rename")).grid(row=1, column=2)

            ttk.Label(master=down_pan, text=LANG.get("path")).grid(row=2, column=0)
            path_broken = item_vals[2]
            if len(item_vals[2]) > 100:
                path_broken = path_broken[:99] + "\n    " + path_broken[99:]
            lbl_path = ttk.Label(master=down_pan, text=path_broken, width=100)
            lbl_path.grid(row=2, column=1)

            ttk.Label(master=down_pan, text=LANG.get("labels")).grid(row=3, column=0)
            frame_lbls = ttk.Frame(master=down_pan)
            frame_lbls.grid(row=3, column=1)

            ttk.Button(master=down_pan, text=LANG.get("manage_labels"), command=lambda x=project, y=item_vals, z=curr_item: self.manage_labels(x, y, z)).grid(row=3, column=2)

            for lbl in files[item_vals[0]]["labels"]:
                ttk.Label(master=frame_lbls, text=lbl).pack(side=tk.LEFT, padx=5, pady=2)

            ttk.Label(master=down_pan, text=LANG.get("comment")).grid(row=4, column=0)

            comment_temp = files.get(item_vals[0]).get("comment")
            tbox_com = scrolledtext.ScrolledText(master=down_pan, height=4)
            tbox_com.insert("1.0", comment_temp)
            tbox_com.grid(row=4, column=1)

            ttk.Button(master=down_pan, text=LANG.get("alter_comment")).grid(row=4, column=2)

            ttk.Label(master=down_pan, text=LANG.get("extra_fields")).grid(row=5, column=0)
            self.frame_extra = ttk.Frame(master=down_pan)
            self.frame_extra.grid(row=5, column=1)

            self.frame_extra.columnconfigure(0)
            self.frame_extra.columnconfigure(1)
            self.frame_extra.columnconfigure(2)

            fields_temp = files.get(item_vals[0]).get("extra_fields")

            num_fields = len(fields_temp)

            for r in range(num_fields):
                if r % 3 == 0:
                    self.frame_extra.rowconfigure(r//3)

            for index, (f, val) in enumerate(fields_temp.items()):
                ExtraField(master=self.frame_extra, field_name=f, field_val=val, file_id=item_vals[0], project=project).grid(row=index // 3, column=index % 3)

            ttk.Button(master=down_pan, text=LANG.get("manage_fields"), command=lambda x=project, y=item_vals[0]: self.manage_fields(x, y)).grid(row=5, column=2)

            ttk.Label(master=down_pan, text=LANG.get("c_time")).grid(row=6, column=0)
            lbl_ctime = ttk.Label(master=down_pan, text=str(item_vals[4]), width=100)
            lbl_ctime.grid(row=6, column=1)

            ttk.Button(master=down_pan, text=LANG.get("del_file")).grid(row=7, column=1)

            ZoomAdvanced(mainframe=right_pan, path=pathlib.Path(item.get("values")[2])).grid(sticky=tk.NSEW)

        self.title(f'{LANG.get("title")}: {path}')

        self.menu.destroy()

        self.main_frame.columnconfigure(0, weight=1, minsize=700)
        self.main_frame.columnconfigure(1, weight=1, minsize=1000)

        self.main_frame.rowconfigure(0, weight=0)
        self.main_frame.rowconfigure(1, weight=1)
        self.main_frame.rowconfigure(2, weight=1)

        self.menu_bar = ttk.Frame(master=self.main_frame)
        self.menu_bar.grid(row=0, column=0, sticky=tk.W)

        with open(pathlib.Path(path, "base.json"), mode="r") as f:
            project = json.load(f)

        btn_add_folder = ttk.Button(master=self.menu_bar, text=LANG.get("add_folder"),
                                    command=lambda x=project: self.add_folder(x))
        btn_add_folder.pack(side=tk.LEFT, padx=5, pady=2)

        btn_manage_links = ttk.Button(master=self.menu_bar, text=LANG.get("manage_links"), command=lambda x=project: self.manage_links(x))
        btn_manage_links.pack(side=tk.LEFT, padx=5, pady=2)

        btn_list_files = ttk.Button(master=self.menu_bar, text=LANG.get("list_files"), command=self.list_files)
        btn_list_files.pack(side=tk.LEFT)

        btn_labels = ttk.Button(master=self.menu_bar, text=LANG.get("labels"), command=lambda x=project: self.labels(x))
        btn_labels.pack(side=tk.LEFT)

        btn_del_pro = ttk.Button(master=self.menu_bar, text=LANG.get("del_pro"), )
        btn_del_pro.pack(side=tk.LEFT)

        btn_filter_labels = ttk.Button(master=self.menu_bar, text=LANG.get("filter_labels"), command=lambda x=project: self.filter_labels(x))
        btn_filter_labels.pack(side=tk.LEFT)

        lbl_name = ttk.Label(master=self.menu_bar, text=f'{LANG.get("proj_name")} {project.get("name")}')
        lbl_name.pack(padx=15, pady=10)

        left_pan = ttk.Frame(master=self.main_frame)
        left_pan.grid(row=1, column=0, sticky=tk.NSEW)
        left_pan.rowconfigure(0, weight=1)
        left_pan.rowconfigure(1, weight=0)
        left_pan.columnconfigure(0, weight=1)
        left_pan.columnconfigure(1, weight=0)

        right_pan = ttk.Frame(master=self.main_frame)
        right_pan.grid(row=0, column=1, rowspan=3, sticky=tk.NSEW)

        down_pan = ttk.Frame(master=self.main_frame)
        down_pan.grid(row=2, column=0, sticky=tk.NSEW)

        files = project.get("files")

        if files:
            self.tree = ttk.Treeview(master=left_pan, show="headings")

            columns = ("id", "source", "path", "labels", "c_time")
            self.tree.configure(columns=columns)

            self.tree.heading("id", text=LANG.get("id"))
            self.tree.heading("source", text=LANG.get("source"))
            self.tree.heading("path", text=LANG.get("path"))
            self.tree.heading("labels", text=LANG.get("labels"))
            self.tree.heading("c_time", text=LANG.get("c_time"))

            self.tree.grid(row=0, column=0, sticky=tk.NSEW)

            scroll_y = ttk.Scrollbar(master=left_pan, orient=tk.VERTICAL, command=self.tree.yview)
            scroll_y.grid(row=0, column=1, sticky=tk.NS)
            self.tree.configure(yscrollcommand=scroll_y.set)

            scroll_x = ttk.Scrollbar(master=left_pan, orient=tk.HORIZONTAL, command=self.tree.xview)
            scroll_x.grid(row=1, column=0, sticky=tk.EW)
            self.tree.configure(xscrollcommand=scroll_x.set)

            self.tree.bind('<<TreeviewSelect>>', selecting_item)
            # tree.bind("<Button-2>", selecting_item_double)

            for file_id, i in files.items():
                self.tree.insert("", tk.END, values=(file_id, i.get("source"), i.get("path"), i.get("labels"), dt.datetime.fromtimestamp(i.get("c_time")).strftime("%Y-%m-%d %H-%M-%S ")))

            # selection = info poniżej + ładuje obrazek obok
            # double click = new window
        else:
            ttk.Label(master=left_pan, text=LANG.get("no_files")).grid()

    def open_pro(self):
        d_path = filedialog.askdirectory(initialdir=os.getcwd(), title=LANG.get("sel_dir"))

        if not d_path:
            return

        if "base.json" not in os.listdir(d_path):
            messagebox.showerror(f'{LANG.get("error")}', f'{LANG.get("lack_of_base_file")}')
            return

        self._base_pro_view(d_path)

    def list_files(self):
        d_path = filedialog.askdirectory(initialdir=os.getcwd(), title=LANG.get("sel_dir"))

        if not d_path:
            return

        temp_window = tk.Toplevel(master=self)
        temp_window.title(f'{LANG.get("list_files")}: {d_path}')

        _tbox = scrolledtext.ScrolledText(master=temp_window)
        _tbox.pack()

        _files = "\n".join(os.listdir(d_path))
        _tbox.insert(tk.END, _files)

        temp_window.mainloop()

    def manage_links(self, project):

        self.temp_window = tk.Toplevel(master=self)
        self.temp_window.title(f'{LANG.get("manage_links")}')
        self.temp_window.columnconfigure(0, weight=0, minsize=300)
        self.temp_window.columnconfigure(1, minsize=500)
        self.temp_window.columnconfigure(2, minsize=500)
        self.temp_window.rowconfigure(0)
        self.temp_window.rowconfigure(1)
        self.temp_window.rowconfigure(2)


        self.temp_menu = ttk.Frame(master=self.temp_window)
        self.temp_menu.grid(column=0, row=0)

        btn_add_links = ttk.Button(master=self.temp_menu, text=LANG.get("add_links"), command=lambda x=project: self.add_links(x))
        btn_add_links.grid(column=0, sticky=tk.EW, padx=5, pady=2)

        btn_assign_links = ttk.Button(master=self.temp_menu, text=LANG.get("assign_sources"), command=lambda x=project: self.assign_s(x))
        btn_assign_links.grid(column=0, sticky=tk.EW, padx=5, pady=2)

        btn_go_back = ttk.Button(master=self.temp_menu, text=LANG.get("go_back"), command=self.temp_window.destroy)
        btn_go_back.grid(column=0, sticky=tk.EW, padx=5, pady=2)

        self.temp_upper_pan = ttk.Frame(master=self.temp_window)
        self.temp_upper_pan.grid(column=1, row=0, columnspan=2, sticky=tk.NSEW)


        self.temp_left_pan = ttk.Frame(master=self.temp_window)
        self.temp_left_pan.grid(column=1, row=1)
        self.temp_left_pan.columnconfigure(0)
        self.temp_left_pan.columnconfigure(1, weight=0)
        self.temp_left_pan.rowconfigure(0)
        self.temp_left_pan.rowconfigure(1, weight=0)

        self.temp_right_pan = ttk.Frame(master=self.temp_window)
        self.temp_right_pan.grid(column=2, row=1)
        self.temp_right_pan.columnconfigure(0)
        self.temp_right_pan.columnconfigure(1, weight=0)
        self.temp_right_pan.rowconfigure(0)
        self.temp_right_pan.rowconfigure(1, weight=0)

        self.temp_bottom_pan = ttk.Frame(master=self.temp_window)
        self.temp_bottom_pan.grid(row=2, column=1, columnspan=2)


    def add_links(self, project):
        for child in self.temp_left_pan.winfo_children():
            child.destroy()

        for child in self.temp_right_pan.winfo_children():
            child.destroy()

        def accept_links(project):
            pat_w_space = re.compile("^\s+$")

            links = [x for x in tbox.get("1.0", tk.END).split("\n") if bool(x) and not pat_w_space.match(x)]
            # links = [x for x in _tbox.get("1.0", tk.END).split("\n") if bool(x) is True and not pat_w_space.match(x)]

            if not links:
                messagebox.showerror(LANG.get("manage_links"), LANG.get("no_links_or_wrong"))
                return

            if "links" in project:
                project["links"] += links
            else:
                project["links"] = links

            main_dir = project["main_dir"]

            with open(pathlib.Path(main_dir, "base.json"), mode="w") as file:
                json.dump(project, file, indent=4)

            messagebox.showinfo(LANG.get("manage_links"), f"{LANG.get('source_added')}{len(links)}")

            for child in self.temp_left_pan.winfo_children():
                child.destroy()

        tbox = scrolledtext.ScrolledText(master=self.temp_left_pan)
        tbox.grid()

        tbox.insert(tk.END, LANG.get("input_links"))

        btn_submit = ttk.Button(master=self.temp_left_pan, text=LANG.get("submit"), command=lambda x=project: accept_links(x))
        btn_submit.grid(padx=5, pady=2)

    def assign_s(self, project):
        for child in self.temp_left_pan.winfo_children():
            child.destroy()

        for child in self.temp_right_pan.winfo_children():
            child.destroy()

        all_assigned_links = list(set(v.get("source") for k, v in project["files"].items()))

        copy_project_files = copy.deepcopy(project["files"])

        def show_all_links(project):
            nonlocal all_assigned_links
            # all_assigned_links = list(set(v.get("source") for k, v in project["files"].items()))
            unassigned_links = [tree_sources.item(i).get("values")[0] for i in tree_sources.get_children()]

            for link in all_assigned_links:
                if link not in unassigned_links:
                    tree_sources.insert("", tk.END, value=(link, ))

        def show_unassigned_links(project):
            for i in tree_sources.get_children():
                if tree_sources.item(i).get("values")[0] not in project["links"]:
                    tree_sources.delete(i)

        def selecting_sources(event):
            nonlocal selected_source
            curr_item = tree_sources.focus()
            item = tree_sources.item(curr_item)
            selected_source = (curr_item, item.get("values")[0])

            print(selected_source)

        def selecting_base(event):
            nonlocal selected_base
            for child in self.temp_upper_pan.winfo_children():
                child.destroy()

            curr_item = tree_base.focus()
            item = tree_base.item(curr_item)

            ZoomAdvanced(mainframe=self.temp_upper_pan, path=pathlib.Path(item.get("values")[2])).grid(sticky=tk.NSEW)

            selected_base = (curr_item, item.get("values")[0])

            print(selected_base)

        def assign():
            nonlocal changes_applied, selected_base, selected_source, selected_sources_to_delete
            if selected_source and selected_base:
                res = messagebox.askyesno(LANG.get("assign_sources"), LANG.get("ask_assign"))

                if res:
                    key_temp = selected_base[1]
                    copy_project_files[key_temp]["source"] = selected_source[1]

                    tree_base.item(selected_base[0], values=(key_temp,
                                                      copy_project_files[key_temp].get("source"),
                                                      copy_project_files[key_temp].get("path"),
                                                      copy_project_files[key_temp].get("labels"),
                                                      dt.datetime.fromtimestamp(copy_project_files[key_temp].get("c_time")).strftime("%Y-%m-%d %H-%M-%S ")))

                    changes_applied = True
                    selected_sources_to_delete.append(selected_source[1])
                else:
                    return

            else:
                messagebox.showinfo(LANG.get("assign_sources"), LANG.get("mark_sources_and_img"))

        def save_changes(project):
            nonlocal changes_applied, selected_sources_to_delete
            if not changes_applied:
                messagebox.showinfo(LANG.get("assign_sources"), LANG.get("no_changes_applied"))
                return

            res = messagebox.askyesno(LANG.get("assign_sources"), LANG.get("ask_save_changes"))
            if res:
                project["files"] = copy_project_files

                for scr_to_del in selected_sources_to_delete:
                    try:
                        project["links"].remove(scr_to_del)
                    except:
                        pass

                with open(pathlib.Path(project["main_dir"], "base.json"), mode="w") as file:
                    json.dump(project, file, indent=4)

                changes_applied = False
                selected_sources_to_delete = []

                self.temp_window.destroy()
                for child in self.main_frame.winfo_children():
                    child.destroy()

                self._base_pro_view(project["main_dir"])

                self.manage_links(project)
                self.assign_s(project)

        def delete_source():
            nonlocal selected_source, selected_sources_to_delete, changes_applied
            if not selected_source:
                messagebox.showinfo(LANG.get("del_source"), LANG.get("no_source_sel"))
                return

            selected_sources_to_delete.append(selected_source[1])
            changes_applied = True
            messagebox.showinfo(LANG.get("del_source"), LANG.get("save_to_confirm_del"))

        selected_source = None
        selected_base = None
        changes_applied = None
        selected_sources_to_delete = []

        tree_sources = ttk.Treeview(master=self.temp_left_pan, show="headings")
        columns_scr = ("source", )
        tree_sources.configure(columns=columns_scr)
        tree_sources.column("source", width=500)
        tree_sources.heading("source", text=LANG.get("source"))
        tree_sources.grid(row=0, column=0, sticky=tk.NSEW)

        scroll_y_scr = ttk.Scrollbar(master=self.temp_left_pan, orient=tk.VERTICAL, command=tree_sources.yview)
        scroll_y_scr.grid(row=0, column=1, sticky=tk.NS)
        tree_sources.configure(yscrollcommand=scroll_y_scr.set)

        scroll_x_src = ttk.Scrollbar(master=self.temp_left_pan, orient=tk.HORIZONTAL, command=tree_sources.xview)
        scroll_x_src.grid(row=1, column=0, sticky=tk.EW)
        tree_sources.configure(xscrollcommand=scroll_x_src.set)

        tree_sources.bind('<<TreeviewSelect>>', selecting_sources)

        for link in project["links"]:
            tree_sources.insert("", tk.END, value=(link, ))

        tree_base = ttk.Treeview(master=self.temp_right_pan, show="headings")
        columns_base = ("id", "source", "path", "labels", "c_time")

        tree_base.configure(columns=columns_base)

        tree_base.heading("id", text=LANG.get("id"))
        tree_base.heading("source", text=LANG.get("source"))
        tree_base.heading("path", text=LANG.get("path"))
        tree_base.heading("labels", text=LANG.get("labels"))
        tree_base.heading("c_time", text=LANG.get("c_time"))

        tree_base.grid(row=0, column=0, sticky=tk.NSEW)

        scroll_y = ttk.Scrollbar(master=self.temp_right_pan, orient=tk.VERTICAL, command=tree_base.yview)
        scroll_y.grid(row=0, column=1, sticky=tk.NS)
        tree_base.configure(yscrollcommand=scroll_y.set)

        scroll_x = ttk.Scrollbar(master=self.temp_right_pan, orient=tk.HORIZONTAL, command=tree_base.xview)
        scroll_x.grid(row=1, column=0, sticky=tk.EW)
        tree_base.configure(xscrollcommand=scroll_x.set)

        tree_base.bind('<<TreeviewSelect>>', selecting_base)

        for file_id, i in copy_project_files.items():
            if i.get("source") == "":
                tree_base.insert("", tk.END, values=(file_id, i.get("source"), i.get("path"), i.get("labels"), dt.datetime.fromtimestamp(i.get("c_time")).strftime("%Y-%m-%d %H-%M-%S ")))

        btn_show_all_links = ttk.Button(master=self.temp_bottom_pan, text=LANG.get("show_all_links"), command=lambda x=project: show_all_links(x))
        btn_show_all_links.pack(padx=5, pady=2, side=tk.LEFT)

        btn_show_all_links = ttk.Button(master=self.temp_bottom_pan, text=LANG.get("show_unassigned_links"), command=lambda x=project: show_unassigned_links(x))
        btn_show_all_links.pack(padx=5, pady=2, side=tk.LEFT)

        btn_assign = ttk.Button(master=self.temp_bottom_pan, text=LANG.get("assign"), command=assign)
        btn_assign.pack(padx=5, pady=2, side=tk.LEFT)

        btn_save = ttk.Button(master=self.temp_bottom_pan, text=LANG.get("save_changes"), command=lambda x=project: save_changes(x))
        btn_save.pack(padx=5, pady=2, side=tk.LEFT)

        btn_delete_source = ttk.Button(master=self.temp_bottom_pan, text=LANG.get("del_source"), command=delete_source)
        btn_delete_source.pack(padx=5, pady=2, side=tk.LEFT)

    def add_folder(self, project):
        d_path = filedialog.askdirectory(initialdir=os.getcwd(), title=LANG.get("add_folder"))
        if not d_path:
            return

        d_path = pathlib.Path(d_path)
        main_dir = project["main_dir"]

        target_dir = pathlib.Path(main_dir, d_path.stem)

        if target_dir.exists():
            target_dir = pathlib.Path(main_dir, d_path.stem + str(int(time.time())))

        def __ignore_patterns(path, names):
            return [f for f in names if pathlib.Path(path, f).is_file() and not self.pat_formats.search(f)]

        shutil.copytree(d_path, target_dir, ignore=__ignore_patterns)

        pro_counter = int(project["last_id"])

        for (dpath, dirs, files) in os.walk(target_dir):
            for file in files:
                # print(pathlib.Path(dpath, file))
                # list_of_files.append(pathlib.Path(dpath, file))
                path = pathlib.Path(dpath, file)
                pro_counter += 1
                project["files"][f"{pro_counter} - {path.name}"] = {"id": pro_counter,
                                                                    "source": "",
                                                                    "f_name": path.name,
                                                                    "path": str(path),
                                                                    "labels": [],
                                                                    "comment": "",
                                                                    "extra_fields": {},
                                                                    "c_time": path.stat().st_mtime}

        files_added = pro_counter - project["last_id"]

        project["last_id"] = pro_counter

        with open(pathlib.Path(main_dir, "base.json"), mode="w") as file:
            json.dump(project, file, indent=4)

        if files_added > 0:
            messagebox.showinfo(LANG.get("add_folder"), f'{LANG.get("update_copy_finish")}{files_added}')
        else:
            messagebox.showerror(LANG.get("add_folder"), LANG.get("no_files_added"))

        self._base_pro_view(main_dir)

    def add_files(self):
        ...

    def delete_project(self):
        ...



if __name__ == "__main__":
    App = MainWindow()
    App.mainloop()
