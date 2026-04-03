from __future__ import annotations

import json
import threading
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from core.config.loader import load_config
from core.runner.analyze import run_analysis


class CodevizGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Codeviz Local Analyzer")
        self.geometry("980x700")
        self.minsize(900, 620)

        self.workspace_root = Path(__file__).resolve().parents[2]

        self.project_var = tk.StringVar(value=str(self.workspace_root))
        self.config_var = tk.StringVar(value=str(self.workspace_root / "configs" / "default.yaml"))
        self.engine_var = tk.StringVar(value="emerge")
        self.locale_var = tk.StringVar(value="ko")

        self._build_ui()

    def _build_ui(self) -> None:
        top = ttk.Frame(self, padding=10)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Project Path").grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=6)
        ttk.Entry(top, textvariable=self.project_var, width=90).grid(row=0, column=1, sticky=tk.EW, pady=6)
        ttk.Button(top, text="Browse", command=self._pick_project).grid(row=0, column=2, padx=(8, 0), pady=6)

        ttk.Label(top, text="Config File").grid(row=1, column=0, sticky=tk.W, padx=(0, 8), pady=6)
        ttk.Entry(top, textvariable=self.config_var, width=90).grid(row=1, column=1, sticky=tk.EW, pady=6)
        ttk.Button(top, text="Browse", command=self._pick_config).grid(row=1, column=2, padx=(8, 0), pady=6)

        controls = ttk.Frame(top)
        controls.grid(row=2, column=1, sticky=tk.W, pady=6)
        ttk.Label(controls, text="Engine").pack(side=tk.LEFT)
        ttk.Combobox(controls, textvariable=self.engine_var, values=["emerge", "madge", "codecharta"], width=14, state="readonly").pack(side=tk.LEFT, padx=(8, 16))
        ttk.Label(controls, text="Locale").pack(side=tk.LEFT)
        ttk.Combobox(controls, textvariable=self.locale_var, values=["ko", "en"], width=8, state="readonly").pack(side=tk.LEFT, padx=(8, 16))

        self.run_btn = ttk.Button(top, text="Run Analysis", command=self._run_async)
        self.run_btn.grid(row=2, column=2, sticky=tk.E)

        top.columnconfigure(1, weight=1)

        splitter = ttk.Panedwindow(self, orient=tk.VERTICAL)
        splitter.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        log_frame = ttk.Labelframe(splitter, text="Execution Log", padding=8)
        self.log_box = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=16)
        self.log_box.pack(fill=tk.BOTH, expand=True)
        splitter.add(log_frame, weight=1)

        warn_frame = ttk.Labelframe(splitter, text="Warnings", padding=8)
        self.warn_box = scrolledtext.ScrolledText(warn_frame, wrap=tk.WORD, height=10)
        self.warn_box.pack(fill=tk.BOTH, expand=True)
        splitter.add(warn_frame, weight=1)

        summary_frame = ttk.Labelframe(splitter, text="Summary JSON", padding=8)
        self.summary_box = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD, height=12)
        self.summary_box.pack(fill=tk.BOTH, expand=True)
        splitter.add(summary_frame, weight=1)

        self.status_var = tk.StringVar(value="Ready")
        status = ttk.Label(self, textvariable=self.status_var, anchor=tk.W, padding=8)
        status.pack(fill=tk.X)

        self._build_menu()

    def _build_menu(self) -> None:
        menu = tk.Menu(self)
        help_menu = tk.Menu(menu, tearoff=0)
        help_menu.add_command(command=self._show_help, label="About")
        menu.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menu)

    def _show_help(self) -> None:
        messagebox.showinfo(
            "Help",
            "Codeviz Local Analyzer\nContact: swh@speefox.com\n제작자: 신우혁",
        )

    def _pick_project(self) -> None:
        selected = filedialog.askdirectory(title="Select project root folder")
        if selected:
            self.project_var.set(selected)

    def _pick_config(self) -> None:
        selected = filedialog.askopenfilename(
            title="Select config file",
            filetypes=[("YAML or JSON", "*.yaml *.yml *.json"), ("All", "*.*")],
        )
        if selected:
            self.config_var.set(selected)

    def _run_async(self) -> None:
        self.run_btn.configure(state=tk.DISABLED)
        self.status_var.set("Running analysis...")
        self._append_log("Analysis started from GUI.")

        worker = threading.Thread(target=self._run_sync, daemon=True)
        worker.start()

    def _run_sync(self) -> None:
        try:
            config = load_config(Path(self.config_var.get()))
            config.project_path = self.project_var.get()
            config.engine = self.engine_var.get()
            config.locale = self.locale_var.get()

            run_dir = run_analysis(config=config, workspace_root=self.workspace_root)
            summary_path = run_dir / "summary.json"
            payload = json.loads(summary_path.read_text(encoding="utf-8"))

            self.after(0, lambda: self._render_result(run_dir, payload))
        except Exception as exc:
            self.after(0, lambda: self._render_error(exc))

    def _render_result(self, run_dir: Path, payload: dict) -> None:
        self._append_log(f"Completed: {run_dir}")
        self.warn_box.delete("1.0", tk.END)
        warnings = payload.get("warnings", [])
        if warnings:
            for idx, item in enumerate(warnings, start=1):
                self.warn_box.insert(tk.END, f"{idx}. {item}\n")
        else:
            self.warn_box.insert(tk.END, "No warnings detected.\n")

        self.summary_box.delete("1.0", tk.END)
        self.summary_box.insert(tk.END, json.dumps(payload, indent=2, ensure_ascii=False))

        self.status_var.set(f"Done: {run_dir}")
        self.run_btn.configure(state=tk.NORMAL)

    def _render_error(self, exc: Exception) -> None:
        self._append_log(f"ERROR: {exc}")
        self._append_log(traceback.format_exc())
        self.status_var.set("Failed")
        self.run_btn.configure(state=tk.NORMAL)
        messagebox.showerror("Analysis Failed", str(exc))

    def _append_log(self, message: str) -> None:
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)


def main() -> int:
    app = CodevizGui()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
