import os
import pathlib
import webbrowser
import tkinter as tk
import datetime as dt
import customtkinter as ctk
from tkinter import ttk
from tkinter import (scrolledtext,
                     messagebox)
from __base_classes import (MyFrame,
                            MyScrollableFrame,
                            MyLabel,
                            MyEntry,
                            MyButton,
                            ExtraField,
                            MyListbox,
                            MyInputDialog)
from __sekretarz_lang import LANG
from __zoomed_canvas import ZoomAdvanced

class TreePan(MyFrame):
    def __init__(self, *args, **kwargs):
        super(TreePan, self).__init__(*args, **kwargs)

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        self.tree = ttk.Treeview(master=self, show="headings")

        columns = ("index", "source", "path", "labels", "c_time")
        self.tree.configure(columns=columns)

        self.tree.heading("index", text=LANG.get("index"))
        self.tree.heading("source", text=LANG.get("source"))
        self.tree.heading("path", text=LANG.get("path"))
        self.tree.heading("labels", text=LANG.get("labels"))
        self.tree.heading("c_time", text=LANG.get("c_time"))

        self.tree.grid(row=0, column=0, sticky=tk.NSEW)

        scroll_y = ctk.CTkScrollbar(master=self, orientation=tk.VERTICAL, command=self.tree.yview)
        scroll_y.grid(row=0, column=1, sticky=tk.NS)
        self.tree.configure(yscrollcommand=scroll_y.set)

        scroll_x = ctk.CTkScrollbar(master=self, orientation=tk.HORIZONTAL, command=self.tree.xview)
        scroll_x.grid(row=1, column=0, sticky=tk.EW)
        self.tree.configure(xscrollcommand=scroll_x.set)

        self.tree.bind('<<TreeviewSelect>>', self.selecting_item)

        # self.project = self.nametowidget(".").project
        self.populate()

    def populate(self):
        """Important note: tree iids = file_ids"""
        self.tree.delete(*self.tree.get_children())

        for file_id, i in self.master.brain.project["files"].items():
            self.tree.insert(
                "",
                tk.END,
                iid=file_id,
                values=(
                    file_id,
                    i.get("source"),
                    i.get("path"),
                    i.get("labels"),
                    f"{dt.datetime.fromtimestamp(int(i.get('c_time'))): %Y-%m-%d %H:%M:%S}"
                )
            )

    def selecting_item(self, event):
        """Important note: tree iids = file_ids"""
        self.master.brain.clear_detail_and_zoom_pan()

        # item index == file_id
        item_index = self.tree.focus()

        self.master.brain.mount_detail_and_zoom_pan(file_id=item_index)


class ZoomPan(MyFrame):
    def __init__(self, path_to_img=None, *args, **kwargs):
        super(ZoomPan, self).__init__(*args, **kwargs)

        if not path_to_img:
            return

        self.zoom = ZoomAdvanced(master=self, path=path_to_img)
        self.zoom.grid(sticky=tk.NSEW)


class DetailPan(MyFrame):
    def __init__(self, file_id, *args, **kwargs):

        super(DetailPan, self).__init__(*args, **kwargs)

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=0)

        for row in range(8):
            self.rowconfigure(row, weight=0)

        self.file_id = file_id
        self.file_data = self.master.brain.project["files"][self.file_id]

        self.uuid = self.file_data["uuid"]

        self.source = self.file_data["source"]
        self.source_var = tk.StringVar(master=self)
        self.source_var.set(self.source)

        self.path = self.file_data["path"]
        self.labels = self.file_data["labels"]
        self.comment = self.file_data["comment"]
        self.extra_fields = self.file_data["extra_fields"]
        self.c_time = self.file_data["c_time"]
        c_time = f"{dt.datetime.fromtimestamp(int(self.c_time)):%Y-%m-%d %H:%M:%S}"
        if self.file_data.get("binds"):
            self.binds = self.file_data.get("binds")
        else:
            self.binds = []
        # c_time =

        self.main_options_pan = MyFrame(master=self)
        self.main_options_pan.grid(row=0, column=0, columnspan=3)
        self.main_options_pan.rowconfigure(0, weight=0)
        self.main_options_pan.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        MyButton(master=self.main_options_pan, text=LANG.get("del_file"), command=self.del_file).grid(row=0, column=0)  # todo command
        MyButton(master=self.main_options_pan, text="Show history", command=self.show_history).grid(row=0, column=1)  # todo command
        MyButton(master=self.main_options_pan, text="Open in default viewer", command=self.open_in_default_viewer).grid(row=0, column=2)
        MyButton(master=self.main_options_pan, text="Open in new detail pan", command=self.open_in_new_window_pan).grid(row=0, column=3)
        MyButton(master=self.main_options_pan, text="Move up", command=self.move_up).grid(row=0, column=4)
        MyButton(master=self.main_options_pan, text="Move down", command=self.move_down).grid(row=0, column=5)

        MyLabel(master=self, text=LANG.get("id")).grid(row=1, column=0)

        self.id_pan = MyFrame(master=self)
        self.id_pan.grid(row=1, column=1)
        self.id_pan.rowconfigure(0)
        self.id_pan.columnconfigure(0, weight=0)
        self.id_pan.columnconfigure(1, weight=1)

        self.id, self.f_name = self.file_id.split(" - ", 1)

        self.f_name_var = tk.StringVar(master=self)
        self.f_name_var.set(self.f_name)

        MyLabel(master=self.id_pan, text=f"{self.id} - ").grid(row=1, column=0)

        self.ent_name = MyEntry(master=self.id_pan, textvariable=self.f_name_var)
        self.ent_name.grid(row=1, column=1, sticky=tk.EW)

        MyButton(master=self, text=LANG.get("f_rename"), command=self.rename_file).grid(row=1, column=2)

        MyLabel(master=self, text=LANG.get("source")).grid(row=2, column=0)

        self.ent_src = MyEntry(master=self, textvariable=self.source_var)
        # self.ent_src.insert(tk.END, self.source)
        self.ent_src.grid(row=2, column=1, sticky=tk.EW)

        self.source_pan = MyFrame(master=self)
        self.source_pan.grid(row=2, column=2)
        self.source_pan.rowconfigure((0, 1), weight=0)
        self.source_pan.columnconfigure(0, weight=0)

        MyButton(master=self.source_pan, text=LANG.get("s_rename"), command=self.rename_source).grid(row=0, column=0)
        MyButton(master=self.source_pan, text="Open Src in Browser", command=self.open_source_in_browser).grid(row=1, column=0)

        MyLabel(master=self, text=LANG.get("path")).grid(row=3, column=0)
        path_broken = self.path
        if len(self.path) > 100:
            path_broken = path_broken[:99] + "\n    " + path_broken[99:]
        self.lbl_path = MyLabel(master=self, text=path_broken, width=100)
        self.lbl_path.grid(row=3, column=1)

        MyButton(master=self, text="Open File in Browser", command=self.open_in_new_browser).grid(row=3, column=2)

        MyLabel(master=self, text=LANG.get("labels")).grid(row=4, column=0)

        self.lbls_listbox = MyListbox(master=self)
        self.lbls_listbox.grid(row=4, column=1)

        self.lbls_listbox.insert(tk.END, *self.labels)

        self.frame_lbls_btns = MyFrame(master=self)
        self.frame_lbls_btns.grid(row=4, column=2)
        self.frame_lbls_btns.rowconfigure((0, 4), weight=1)
        self.frame_lbls_btns.rowconfigure((1, 2, 3,), weight=0)
        self.frame_lbls_btns.columnconfigure(0, weight=0)
        MyLabel(master=self.frame_lbls_btns, text=LANG.get("manage_labels")).grid(row=0, column=0)
        # todo: combine the above
        MyButton(master=self.frame_lbls_btns, text="Add Label(s)", command=self.add_labels).grid(row=1, column=0, sticky=tk.S)
        MyButton(master=self.frame_lbls_btns, text="Remove Label(s)", command=self.remove_labels).grid(row=2, column=0)
        MyButton(master=self.frame_lbls_btns, text="Move up", command=self.remove_labels).grid(row=3, column=0)
        MyButton(master=self.frame_lbls_btns, text="Move down", command=self.remove_labels).grid(row=4, column=0, sticky=tk.N)


        MyLabel(master=self, text=LANG.get("comment")).grid(row=5, column=0)

        self.tbox_com = scrolledtext.ScrolledText(master=self, height=4)
        self.tbox_com.insert("1.0", self.comment)
        self.tbox_com.grid(row=5, column=1, sticky=tk.EW)

        MyButton(master=self, text=LANG.get("alter_comment"), command=self.alter_comment).grid(row=5, column=2)

        MyLabel(master=self, text=LANG.get("extra_fields")).grid(row=6, column=0)
        self.frame_extra = MyFrame(master=self)
        self.frame_extra.grid(row=6, column=1)

        self.frame_extra.columnconfigure(0)
        self.frame_extra.columnconfigure(1)
        self.frame_extra.columnconfigure(2)

        num_fields = len(self.extra_fields)

        for r in range(num_fields):
            if r % 3 == 0:
                self.frame_extra.rowconfigure(r // 3)

        for index, (field_name, field_val) in enumerate(self.extra_fields.items()):
            ExtraField(master=self.frame_extra, field_name=field_name, field_val=field_val, file_id=self.file_id
                       ).grid(row=index // 3, column=index % 3)

        MyButton(master=self, text=LANG.get("manage_fields"),
                   command=self.manage_fields).grid(row=6, column=2)

        MyLabel(master=self, text=LANG.get("c_time")).grid(row=7, column=0)
        lbl_ctime = MyLabel(master=self, text=c_time, width=100)
        lbl_ctime.grid(row=7, column=1)

        self.fields_manager = None

    def show_history(self):
        self.master.brain.show_history(self.file_id)

    def move_down(self):
        self.master.brain.move_down()

    def move_up(self):
        self.master.brain.move_up()

    def open_in_new_window_pan(self):
        self.master.brain.open_in_new_window_pan

    def open_in_default_viewer(self):
        self.master.brain.open_in_default_viewer(self.path)
        # sh: 1: / home / tomasz / PycharmProjects / sekretarz / 2 / foto / skierowanie: not found
        # sh: 1: / home / tomasz / PycharmProjects / sekretarz / 2 / foto / 62662726 as.png: Permission
        # denied
        # sh: 1: / home / tomasz / PycharmProjects / sekretarz / 2 / foto / Nikon - D750 - Image - Samples - 2.j
        # pg: Permission
        # denied
        # path = self.master.brain.project_path.joinpath(self.path) # moved to th brain
        # os.system(path)

    def open_source_in_browser(self): # moved to th brain
        self.master.brain.open_source_in_browser(self.source_var.get())

    def open_in_new_browser(self): # moved to th brain
        self.master.brain.open_in_new_browser(self.path)

        # path = self.master.brain.project_path.joinpath(self.path) # moved to th brain
        # webbrowser.open(str(path), new=2)
    # todo: add "open in new window option"
    # todo: send all those functions to the BRAIN
    def del_file(self):
        self.master.brain.del_file(self.file_id)

    def manage_fields(self):
        ...
        # self.fields_manager = FieldsManager(driver=self, file_id=self.file_id)

    def rename_file(self):
        n_name = self.f_name_var.get()

        if not n_name.endswith(pathlib.Path(self.path).suffix):
            messagebox.showerror(master=self, title=LANG.get("f_rename"), message=LANG.get("f_name_wrong_suffix"))
            return

        print(n_name, self.f_name)

        if n_name != self.f_name:
            res = messagebox.askyesno(master=self, title=LANG.get("f_rename"), message=LANG.get("f_rename"))
            if res:
                old_path = pathlib.Path(self.path)
                old_path_abs = self.master.brain.project_path.joinpath(old_path)
                new_path = pathlib.Path(old_path.parent, n_name)
                new_path_abs = pathlib.Path(old_path_abs.parent, n_name)

                old_path_abs.rename(new_path_abs)
                self.path = str(new_path)

                path_broken = self.path
                if len(self.path) > 100:
                    path_broken = path_broken[:99] + "\n    " + path_broken[99:]
                self.lbl_path.configure(text=path_broken)

                self.f_name = n_name
                self.f_name_var.set(self.f_name)

                new_name_with_data = f"{self.id} - {self.f_name}"

                old_name, self.file_id = self.file_id, new_name_with_data

                self.master.brain.rename_file(
                    old_name,
                    self.file_id,
                    {
                        "uuid": self.uuid,
                        "index": int(self.id),
                        "source": self.source,
                        "path": self.path,
                        "labels": self.labels,
                        "comment": self.comment,
                        "extra_fields": self.extra_fields,
                        "c_time": self.c_time,
                        "binds": self.binds
                    }
                )

        else:
            messagebox.showerror(master=self, title=LANG.get("f_rename"), message=LANG.get("same_f_name"))

    def rename_source(self):
        src = self.source_var.get()
        if src != self.source:
            res = messagebox.askyesno(master=self, title=LANG.get("s_rename"), message=LANG.get("s_rename"))
            if res:
                self.master.brain.rename_source(
                    self.file_id,
                    self.source,
                    self.path,
                    self.labels,
                    f"{dt.datetime.fromtimestamp(int(self.c_time)):%Y-%m-%d %H:%M:%S}",
                    src
                )
                self.source = src
                self.source_var.set(src)
                # self.master.brain.history_manager.save_previous_state(self.uuid, "path", self.path)
        else:
            messagebox.showerror(master=self, title=LANG.get("s_rename"), message=LANG.get("same_source"))

    def go_to_source(self):
        ...

    def remove_labels(self):
        ...
    def add_labels(self):

        self.lbl_manager = tk.Toplevel(master=self)
        self.lbl_manager.title(f"{LANG.get('label_man')}{self.file_id}")

        self.lbl_manager.grab_set()

        self.frame_lbl = MyFrame(master=self.lbl_manager)
        self.frame_lbl.grid()

        self.frame_lbl.columnconfigure(0)
        self.frame_lbl.columnconfigure(1)
        self.frame_lbl.columnconfigure(2)

        self.frame_lbl.rowconfigure(0)
        self.frame_lbl.rowconfigure(1)

        self.btn_menu = MyFrame(master=self.frame_lbl)
        self.btn_menu.grid(row=1, column=2, )

        ttk.Label(master=self.frame_lbl, text=LANG.get("all_lbls")).grid(row=0, column=0)
        ttk.Label(master=self.frame_lbl, text=LANG.get("file_lbls")).grid(row=0, column=1)

        self.lst_box_all = tk.Listbox(master=self.frame_lbl, width=60)
        self.lst_box_all.grid(row=1, column=0, sticky=tk.NSEW)

        all_labels = self.project["labels"]
        for l in all_labels:
            self.lst_box_all.insert(tk.END, l)

        self.lst_box_file = tk.Listbox(master=self.frame_lbl, width=60)
        self.lst_box_file.grid(row=1, column=1, sticky=tk.NSEW)

        self.project = self.nametowidget(".").load_project()

        file_labels = self.project["files"][self.file_id]["labels"]
        for l in file_labels:
            self.lst_box_file.insert(tk.END, l)

        ttk.Button(master=self.btn_menu, text=LANG.get("sel_lbl"), command=self._select_lbl).grid(row=0)
        ttk.Button(master=self.btn_menu, text=LANG.get("remove_lbl"), command=self._remove_lbl).grid(row=1)
        ttk.Button(master=self.btn_menu, text=LANG.get("confirm_sel"),
                   command=self._confirm_sel).grid(row=2)
        ttk.Button(master=self.btn_menu, text=LANG.get("go_back"), command=self.lbl_manager.destroy).grid(row=3)
        ttk.Button(master=self.btn_menu, text=LANG.get("go_to_labels"),
                   command=self._go_to_label_manager).grid(row=4)

    def _go_to_label_manager(self):
        self.lbl_manager.destroy()
        self.nametowidget(".!myframe.!baseprojectview").label_manager()

    def _select_lbl(self):
        sel_lbl = self.lst_box_all.curselection()
        if sel_lbl and not self.lst_box_all.get(sel_lbl[0]) in self.lst_box_file.get(0, tk.END):
            self.lst_box_file.insert(tk.END, self.lst_box_all.get(sel_lbl[0]))

    def _remove_lbl(self):
        rem_lbl = self.lst_box_file.curselection()
        if rem_lbl:
            self.lst_box_file.delete(rem_lbl[0])

    def _confirm_sel(self):
        selected_labels = self.lst_box_file.get(0, tk.END)
        print(selected_labels)
        self.project["files"][self.file_id]["labels"] = list(selected_labels)
        print(self.project["files"][self.file_id]["labels"])

        self.nametowidget(".").save_project()
        self.project = self.nametowidget(".").load_project()

        self.labels = self.project["files"][self.file_id]["labels"]

        for child in self.frame_lbls.winfo_children():
            child.destroy()

        for lbl in self.labels:
            ttk.Label(master=self.frame_lbls, text=lbl).pack(side=tk.LEFT, padx=5, pady=2)

        self.nametowidget(".!myframe.!baseprojectview.!myframe2.!treepan").project = self.project

        selected_labels = " ".join(selected_labels)
        tree_pan = self.nametowidget(".!myframe.!baseprojectview.!myframe2.!treepan")
        tree_pan.project = self.project
        tree_pan.tree.item(
            self.file_id,
            values=(
                (self.file_id,
                 self.source,
                 self.path,
                 selected_labels,
                 dt.datetime.fromtimestamp(self.c_time).strftime("%Y-%m-%d %H:%M:%S"))
            )
        )

    def alter_comment(self):
        comment = self.tbox_com.get("1.0", tk.END)[:-1]

        if comment != self.comment:
            res = messagebox.askyesno(master=self, title=LANG.get("alter_comment"), message=LANG.get("alter_comment"))
            if res:
                self.master.brain.alter_comment(self.file_id, comment)
                self.comment = comment
        else:
            messagebox.showerror(master=self, title=LANG.get("alter_comment"), message=LANG.get("same_comment"))


class RotatingPan(MyFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)

        self.columnconfigure(0, weight=1)

        self.menu_bar = MyFrame(master=self)
        self.menu_bar.grid(row=0, column=0)

        self.menu_bar.rowconfigure(0, weight=0)
        self.menu_bar.columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.pan = MyFrame(master=self)
        self.pan.grid(row=1, column=0)

        MyButton(master=self.menu_bar, text="General Pan", command=self.general_pan).grid(row=0, column=0)
        MyButton(master=self.menu_bar, text="Label Pan", command=self.label_pan).grid(row=0, column=1)

    def general_pan(self):
        self.pan.destroy()
        self.pan = GeneralPan(master=self)
        self.pan.grid(row=1, column=0)

    def label_pan(self):
        self.pan.destroy()
        self.pan = LabelPan(master=self)
        self.pan.grid(row=1, column=0)

class LabelPan(MyFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        # self.rowconfigure(2, weight=1)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)

        MyLabel(master=self, text="Labels in the project").grid(row=0, column=0)

        self.all_lbls_listbox = MyListbox(master=self)
        self.all_lbls_listbox.grid(row=1, column=0)

        self.all_lbls_listbox.insert(tk.END, *self.master.master.brain.project["labels"])

        self.button_pan = MyFrame(master=self)
        self.button_pan.grid(row=1, column=1)
        self.button_pan.columnconfigure(0, weight=0)
        self.button_pan.rowconfigure((0, 4), weight=1)
        self.button_pan.rowconfigure((1, 2, 3, ), weight=0)

        MyButton(master=self.button_pan, text="Move up", command=self.move_up).grid(row=0, column=0, sticky=tk.S)
        MyButton(master=self.button_pan, text="Move down", command=self.move_down).grid(row=1, column=0)
        MyButton(master=self.button_pan, text="Add Label to\nthe Project", command=self.add_label_to_project).grid(row=2, column=0)
        MyButton(master=self.button_pan, text="Rename Label", command=self.rename_label).grid(row=3, column=0)
        MyButton(master=self.button_pan, text="Delete Label").grid(row=4, column=0, sticky=tk.N)

    def move_up(self):
        index = self.all_lbls_listbox.curselection()
        if not index:
            return
        index = index[0]
        selected = self.all_lbls_listbox.get(index)
        if index - 1 < 0:
            return

        all_labels = list(self.all_lbls_listbox.get(0, tk.END))
        all_labels.remove(selected)
        all_labels.insert(index - 1, selected)

        self.all_lbls_listbox.delete(0, tk.END)
        self.all_lbls_listbox.insert(tk.END, *all_labels)

        self.master.master.brain.save_new_order_all_labels(all_labels)

    def move_down(self):
        index = self.all_lbls_listbox.curselection()
        if not index:
            return
        index = index[0]
        selected = self.all_lbls_listbox.get(index)
        all_labels = list(self.all_lbls_listbox.get(0, tk.END))
        if index + 1 > len(all_labels):
            return

        all_labels.remove(selected)
        all_labels.insert(index + 1, selected)

        self.all_lbls_listbox.delete(0, tk.END)
        self.all_lbls_listbox.insert(tk.END, *all_labels)

        self.master.master.brain.save_new_order_all_labels(all_labels)

    def rename_label(self):
        # todo
        ...
    def delete_label(self):
        # todo
        ...

    def add_label_to_project(self):
        dialog = MyInputDialog(text="Type in a new label name:", title="Add Label to the Project")
        new_label = dialog.get_input()
        if not new_label:
            return
        if new_label in self.all_lbls_listbox.get(0, tk.END):
            return

        self.all_lbls_listbox.insert(tk.END, new_label)
        self.master.master.brain.add_label_to_project(new_label)



class GeneralPan(MyFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.rowconfigure(0, weight=0)
