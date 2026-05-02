import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from pathlib import Path
import queue
import core

CONFIG_FILE = Path(__file__).parent / "config.json"

class App:
    def __init__(self, root):
        self.root = root
        self.root.title(core.t("title"))
        self.root.geometry("800x650")
        self.root.resizable(True, True)

        self.config = self.load_config()
        self.apply_language()

        self.create_menu()
        self.create_widgets()

        self.processing_thread = None
        self.cancel_event = threading.Event()
        self.msg_queue = queue.Queue()

        self.after_id = None

    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"min": 512, "max": 2048, "step": 64, "lang": "zh"}

    def save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    def apply_language(self):
        lang = self.config.get("lang", "zh")
        core.LANG = lang

    def switch_language(self, lang_code):
        if self.config.get("lang") == lang_code:
            return
        self.config["lang"] = lang_code
        self.save_config()
        self.apply_language()
        self.rebuild_ui()

    def get_sort_key(self):
        text = self.sort_order_combo.get()
        if text == core.t("sort_desc"):
            return "desc"
        return "asc"

    def rebuild_ui(self):
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        state = {
            "mode": self.mode_var.get(),
            "rename": self.rename_enabled.get(),
            "sort_key": self.get_sort_key(),
            "single_path": self.folder_path.get(),
            "batch_parent": self.batch_parent_path.get(),
            "min": self.min_var.get(),
            "max": self.max_var.get(),
            "step": self.step_var.get(),
            "selected_indices": list(self.batch_listbox.curselection()),
        }

        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Menu):
                continue
            widget.destroy()

        self.create_widgets()
        self.root.title(core.t("title"))

        self.mode_var.set(state["mode"])
        self.rename_enabled.set(state["rename"])
        new_sort_display = core.t("sort_asc") if state["sort_key"] == "asc" else core.t("sort_desc")
        self.sort_order_combo.set(new_sort_display)
        self.on_rename_toggle()
        self.folder_path.set(state["single_path"])
        self.batch_parent_path.set(state["batch_parent"])
        self.min_var.set(state["min"])
        self.max_var.set(state["max"])
        self.step_var.set(state["step"])

        if state["selected_indices"]:
            for i in state["selected_indices"]:
                try:
                    self.batch_listbox.selection_set(i)
                except Exception:
                    pass
        self.on_mode_change()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        lang_menu = tk.Menu(menubar, tearoff=0)
        lang_menu.add_command(label="中文", command=lambda: self.switch_language("zh"))
        lang_menu.add_command(label="English", command=lambda: self.switch_language("en"))
        menubar.add_cascade(label="语言 Language" if core.LANG == "zh" else "Language", menu=lang_menu)

    def create_widgets(self):
        mode_frame = ttk.LabelFrame(self.root, text=core.t("mode_selection"))
        mode_frame.pack(fill=tk.X, padx=8, pady=4)

        left_frame = ttk.Frame(mode_frame)
        left_frame.pack(side=tk.LEFT, padx=8, pady=3)
        self.mode_var = tk.StringVar(value="single")
        ttk.Radiobutton(left_frame, text=core.t("single_folder"), variable=self.mode_var, value="single",
                        command=self.on_mode_change).pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(left_frame, text=core.t("batch_folder"), variable=self.mode_var, value="batch",
                        command=self.on_mode_change).pack(side=tk.LEFT, padx=4)

        rename_frame = ttk.Frame(mode_frame)
        rename_frame.pack(side=tk.RIGHT, padx=8, pady=3)
        self.rename_enabled = tk.BooleanVar(value=False)
        self.rename_check = ttk.Checkbutton(rename_frame, text=core.t("auto_rename"),
                                            variable=self.rename_enabled,
                                            command=self.on_rename_toggle)
        self.rename_check.pack(side=tk.LEFT, padx=4)
        ttk.Label(rename_frame, text=core.t("sort_order_label")).pack(side=tk.LEFT, padx=4)
        self.sort_order_var = tk.StringVar(value=core.t("sort_asc"))
        self.sort_order_combo = ttk.Combobox(rename_frame, textvariable=self.sort_order_var,
                                             values=[core.t("sort_asc"), core.t("sort_desc")],
                                             state='readonly', width=20)
        self.sort_order_combo.pack(side=tk.LEFT, padx=4)
        self.on_rename_toggle()

        rule_frame = ttk.LabelFrame(self.root, text=core.t("current_rule"))
        rule_frame.pack(fill=tk.X, padx=8, pady=4)

        ttk.Label(rule_frame, text=core.t("min_resolution")).grid(row=0, column=0, padx=4, pady=4, sticky=tk.W)
        self.min_var = tk.IntVar(value=self.config["min"])
        ttk.Entry(rule_frame, textvariable=self.min_var, width=7).grid(row=0, column=1, padx=4, pady=4)

        ttk.Label(rule_frame, text=core.t("max_resolution")).grid(row=0, column=2, padx=4, pady=4, sticky=tk.W)
        self.max_var = tk.IntVar(value=self.config["max"])
        ttk.Entry(rule_frame, textvariable=self.max_var, width=7).grid(row=0, column=3, padx=4, pady=4)

        ttk.Label(rule_frame, text=core.t("step_size")).grid(row=0, column=4, padx=4, pady=4, sticky=tk.W)
        self.step_var = tk.IntVar(value=self.config["step"])
        ttk.Entry(rule_frame, textvariable=self.step_var, width=7).grid(row=0, column=5, padx=4, pady=4)

        ttk.Button(rule_frame, text=core.t("save_rule"), command=self.save_rules).grid(row=0, column=6, padx=8)

        self.path_frame = ttk.Frame(self.root)
        self.path_frame.pack(fill=tk.X, padx=8, pady=4)

        self.single_frame = ttk.Frame(self.path_frame)
        self.create_single_widgets()

        self.batch_frame = ttk.Frame(self.path_frame)
        self.create_batch_widgets()

        self.on_mode_change()

        self.batch_list_frame = ttk.LabelFrame(self.root, text=core.t("batch_list_label"))
        self.batch_list_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        batch_inner = ttk.Frame(self.batch_list_frame)
        batch_inner.pack(fill=tk.BOTH, expand=True)

        self.batch_listbox = tk.Listbox(batch_inner, selectmode=tk.MULTIPLE, exportselection=False)
        self.batch_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll = ttk.Scrollbar(batch_inner, orient=tk.VERTICAL, command=self.batch_listbox.yview)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.batch_listbox.config(yscrollcommand=list_scroll.set)

        btn_panel = ttk.Frame(batch_inner)
        btn_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=4, pady=4)
        ttk.Button(btn_panel, text=core.t("select_all"),
                   command=lambda: self.batch_listbox.selection_set(0, tk.END)).pack(pady=2, fill=tk.X)
        ttk.Button(btn_panel, text=core.t("invert_selection"),
                   command=self.invert_selection).pack(pady=2, fill=tk.X)
        ttk.Button(btn_panel, text=core.t("clear_selection"),
                   command=lambda: self.batch_listbox.selection_clear(0, tk.END)).pack(pady=2, fill=tk.X)

        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=8, pady=4)

        log_frame = ttk.LabelFrame(self.root, text=core.t("log_label"))
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scroll.set)

        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=8, pady=6)
        self.cancel_btn = ttk.Button(control_frame, text=core.t("cancel"), command=self.cancel_processing,
                                     state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.RIGHT, padx=4)
        self.start_btn = ttk.Button(control_frame, text=core.t("start_process"), command=self.start_processing)
        self.start_btn.pack(side=tk.RIGHT, padx=4)

    def create_single_widgets(self):
        row0 = ttk.Frame(self.single_frame)
        row0.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        ttk.Label(row0, text=core.t("single_path_label")).pack(side=tk.LEFT, padx=4)
        self.folder_path = tk.StringVar()
        # Entry 设为可伸缩，填充剩余空间
        ttk.Entry(row0, textvariable=self.folder_path, width=60).pack(
            side=tk.LEFT, padx=4, fill=tk.X, expand=True
        )
        # 按钮固定在最右侧
        ttk.Button(row0, text=core.t("browse"), command=self.browse_single).pack(
            side=tk.RIGHT, padx=4
        )

    def create_batch_widgets(self):
        row0 = ttk.Frame(self.batch_frame)
        row0.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        ttk.Label(row0, text=core.t("batch_parent_label")).pack(side=tk.LEFT, padx=4)
        self.batch_parent_path = tk.StringVar()
        ttk.Entry(row0, textvariable=self.batch_parent_path, width=60).pack(
            side=tk.LEFT, padx=4, fill=tk.X, expand=True
        )
        # 按钮框架固定在右侧
        btn_row = ttk.Frame(row0)
        btn_row.pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_row, text=core.t("browse"), command=self.browse_batch_parent).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(btn_row, text=core.t("scan_subdirs"), command=self.scan_subdirs).pack(
            side=tk.LEFT, padx=2
        )

    def on_mode_change(self):
        mode = self.mode_var.get()
        if mode == "single":
            self.batch_frame.grid_remove()
            self.single_frame.grid(row=0, column=0, sticky="ew")
        else:
            self.single_frame.grid_remove()
            self.batch_frame.grid(row=0, column=0, sticky="ew")

    def on_rename_toggle(self):
        if self.rename_enabled.get():
            self.sort_order_combo.state(['!disabled'])
        else:
            self.sort_order_combo.state(['disabled'])

    def save_rules(self):
        try:
            min_val = self.min_var.get()
            max_val = self.max_var.get()
            step_val = self.step_var.get()
            if min_val > max_val:
                messagebox.showerror(core.t("error"), core.t("min_max_error"))
                return
            if step_val <= 0:
                messagebox.showerror(core.t("error"), core.t("step_error"))
                return
            self.config.update({"min": min_val, "max": max_val, "step": step_val})
            self.save_config()
            messagebox.showinfo(core.t("info"), core.t("rule_saved_ok"))
        except tk.TclError:
            messagebox.showerror(core.t("error"), core.t("invalid_integer"))

    def browse_single(self):
        path = filedialog.askdirectory()
        if path:
            self.folder_path.set(path)

    def browse_batch_parent(self):
        path = filedialog.askdirectory()
        if path:
            self.batch_parent_path.set(path)

    def scan_subdirs(self):
        parent = self.batch_parent_path.get().strip()
        if not parent or not Path(parent).is_dir():
            messagebox.showwarning(core.t("warning"), core.t("invalid_parent_dir"))
            return
        self.batch_listbox.delete(0, tk.END)
        subdirs = sorted([d for d in Path(parent).iterdir() if d.is_dir()])
        for d in subdirs:
            self.batch_listbox.insert(tk.END, d.name)
        if not subdirs:
            messagebox.showinfo(core.t("info"), core.t("no_subdirs"))

    def invert_selection(self):
        all_items = self.batch_listbox.size()
        selected = set(self.batch_listbox.curselection())
        new_selection = set(range(all_items)) - selected
        self.batch_listbox.selection_clear(0, tk.END)
        for idx in new_selection:
            self.batch_listbox.selection_set(idx)

    def log(self, msg: str):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def safe_progress_callback(self, msg: str, pct: float = None):
        """线程安全：将消息放入队列，由主线程轮询更新"""
        self.msg_queue.put(("log", msg))
        if pct is not None:
            self.msg_queue.put(("progress", pct))

    def process_queue(self):
        """定期从队列取出消息并更新 UI"""
        try:
            while True:
                msg_type, value = self.msg_queue.get_nowait()
                if msg_type == "log":
                    self.log(value)
                elif msg_type == "progress":
                    self.progress_var.set(value * 100)
        except queue.Empty:
            pass
        if self.processing_thread and self.processing_thread.is_alive():
            self.after_id = self.root.after(100, self.process_queue)
        else:
            self.on_processing_done()

    def start_processing(self):
        mode = self.mode_var.get()
        if self.processing_thread and self.processing_thread.is_alive():
            messagebox.showwarning(core.t("warning"), core.t("task_running"))
            return

        # 重置取消事件
        self.cancel_event.clear()
        # 清空队列
        while not self.msg_queue.empty():
            self.msg_queue.get()

        self.start_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)

        sort_key = self.get_sort_key()
        enable_rename = self.rename_enabled.get()

        if mode == "single":
            folder = self.folder_path.get().strip()
            if not folder or not Path(folder).is_dir():
                messagebox.showerror(core.t("error"), core.t("invalid_single_folder"))
                self.reset_buttons()
                return
            self.processing_thread = threading.Thread(
                target=self.process_single,
                args=(folder, enable_rename, sort_key),
                daemon=True
            )
        else:
            parent = self.batch_parent_path.get().strip()
            if not parent or not Path(parent).is_dir():
                messagebox.showerror(core.t("error"), core.t("invalid_parent_dir"))
                self.reset_buttons()
                return
            selected = self.batch_listbox.curselection()
            if not selected:
                messagebox.showwarning(core.t("warning"), core.t("no_selection"))
                self.reset_buttons()
                return
            folders = [Path(parent) / self.batch_listbox.get(i) for i in selected]
            self.processing_thread = threading.Thread(
                target=self.process_batch,
                args=(folders, enable_rename, sort_key),
                daemon=True
            )

        self.processing_thread.start()
        self.after_id = self.root.after(100, self.process_queue)

    def process_single(self, folder, enable_rename, sort_order):
        try:
            core.process_images(
                input_folder=folder,
                min_size=self.config["min"],
                max_size=self.config["max"],
                step=self.config["step"],
                rename=enable_rename,
                sort_order=sort_order,
                progress_callback=self.safe_progress_callback,
                cancel_event=self.cancel_event
            )
        except Exception as e:
            self.safe_progress_callback(f"发生异常: {e}")
        # 不再直接调用 on_processing_done，留给 process_queue 检测线程结束

    def process_batch(self, folders, enable_rename, sort_order):
        total = len(folders)
        for i, folder in enumerate(folders):
            if self.cancel_event.is_set():
                self.safe_progress_callback(core.t("batch_cancelled"))
                break
            self.safe_progress_callback(f"\n========== {core.t('batch_start')} [{i+1}/{total}]: {folder.name} ==========")
            try:
                core.process_images(
                    input_folder=str(folder),
                    min_size=self.config["min"],
                    max_size=self.config["max"],
                    step=self.config["step"],
                    rename=False,
                    sort_order=sort_order,
                    progress_callback=self.safe_progress_callback,
                    cancel_event=self.cancel_event
                )
            except Exception as e:
                self.safe_progress_callback(f"{folder.name} {core.t('batch_error')}: {e}")
            self.safe_progress_callback(f"========== {folder.name} {core.t('batch_done')} ==========\n")

    def cancel_processing(self):
        self.cancel_event.set()
        self.cancel_btn.config(state=tk.DISABLED)

    def on_processing_done(self):
        self.start_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        messagebox.showinfo(core.t("info"), core.t("task_completed"))

    def reset_buttons(self):
        self.start_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()