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
        self.geometry("1100x860")
        self.minsize(980, 720)

        self.workspace_root = Path(__file__).resolve().parents[2]

        self.project_var = tk.StringVar(value=str(self.workspace_root))
        self.config_var = tk.StringVar(value=str(self.workspace_root / "configs" / "default.yaml"))
        self.engine_var = tk.StringVar(value="emerge")
        self.locale_var = tk.StringVar(value="ko")
        self.status_var = tk.StringVar(value="Ready")

        self._build_ui()

    def _build_ui(self) -> None:
        top = ttk.Frame(self, padding=10)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Project Path").grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=6)
        ttk.Entry(top, textvariable=self.project_var, width=100).grid(row=0, column=1, sticky=tk.EW, pady=6)
        ttk.Button(top, text="Browse", command=self._pick_project).grid(row=0, column=2, padx=(8, 0), pady=6)

        ttk.Label(top, text="Config File").grid(row=1, column=0, sticky=tk.W, padx=(0, 8), pady=6)
        ttk.Entry(top, textvariable=self.config_var, width=100).grid(row=1, column=1, sticky=tk.EW, pady=6)
        ttk.Button(top, text="Browse", command=self._pick_config).grid(row=1, column=2, padx=(8, 0), pady=6)

        controls = ttk.Frame(top)
        controls.grid(row=2, column=1, sticky=tk.W, pady=6)
        ttk.Label(controls, text="Engine").pack(side=tk.LEFT)
        self.engine_combo = ttk.Combobox(
            controls,
            textvariable=self.engine_var,
            values=["emerge", "madge", "codecharta"],
            width=14,
            state="readonly",
        )
        self.engine_combo.pack(side=tk.LEFT, padx=(8, 16))
        ttk.Label(controls, text="Locale").pack(side=tk.LEFT)
        self.locale_combo = ttk.Combobox(
            controls,
            textvariable=self.locale_var,
            values=["ko", "en"],
            width=8,
            state="readonly",
        )
        self.locale_combo.pack(side=tk.LEFT, padx=(8, 16))

        self.run_btn = ttk.Button(top, text="Run Analysis", command=self._run_async)
        self.run_btn.grid(row=2, column=2, sticky=tk.E)

        top.columnconfigure(1, weight=1)

        progress_row = ttk.Frame(self, padding=(10, 0, 10, 8))
        progress_row.pack(fill=tk.X)
        ttk.Label(progress_row, text="Progress").pack(side=tk.LEFT, padx=(0, 10))
        self.progress = ttk.Progressbar(progress_row, mode="determinate", length=420, maximum=100)
        self.progress.pack(side=tk.LEFT)

        tabs = ttk.Notebook(self)
        tabs.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        exec_tab = ttk.Frame(tabs)
        risk_tab = ttk.Frame(tabs)
        summary_tab = ttk.Frame(tabs)
        tabs.add(exec_tab, text="Execution")
        tabs.add(risk_tab, text="Risk Visualization")
        tabs.add(summary_tab, text="Summary")

        self.log_box = scrolledtext.ScrolledText(ttk.Labelframe(exec_tab, text="Execution Log", padding=8), wrap=tk.WORD, height=16)
        self.log_box.master.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.log_box.pack(fill=tk.BOTH, expand=True)

        self.warn_box = scrolledtext.ScrolledText(ttk.Labelframe(exec_tab, text="Warnings", padding=8), wrap=tk.WORD, height=12)
        self.warn_box.master.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.warn_box.pack(fill=tk.BOTH, expand=True)

        self.heatmap_box = scrolledtext.ScrolledText(ttk.Labelframe(risk_tab, text="Risk Heatmap (By File)", padding=8), wrap=tk.NONE, height=12)
        self.heatmap_box.master.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.heatmap_box.pack(fill=tk.BOTH, expand=True)

        self.findings_box = scrolledtext.ScrolledText(ttk.Labelframe(risk_tab, text="Risk Findings (Line-level)", padding=8), wrap=tk.NONE, height=12)
        self.findings_box.master.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.findings_box.pack(fill=tk.BOTH, expand=True)

        self.flowchart_box = scrolledtext.ScrolledText(ttk.Labelframe(risk_tab, text="Error Flowchart (Mermaid)", padding=8), wrap=tk.NONE, height=10)
        self.flowchart_box.master.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.flowchart_box.pack(fill=tk.BOTH, expand=True)

        self.summary_box = scrolledtext.ScrolledText(ttk.Labelframe(summary_tab, text="Summary JSON", padding=8), wrap=tk.WORD, height=30)
        self.summary_box.master.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.summary_box.pack(fill=tk.BOTH, expand=True)

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

    def _normalize_path_text(self, raw: str) -> Path:
        cleaned = raw.strip().strip('"').strip("'")
        return Path(cleaned)

    def _set_busy(self, busy: bool) -> None:
        if busy:
            self.run_btn.configure(state=tk.DISABLED)
            self.progress.configure(value=0)
        else:
            self.run_btn.configure(state=tk.NORMAL)

    def _reset_view(self) -> None:
        self.warn_box.delete("1.0", tk.END)
        self.heatmap_box.delete("1.0", tk.END)
        self.findings_box.delete("1.0", tk.END)
        self.flowchart_box.delete("1.0", tk.END)
        self.summary_box.delete("1.0", tk.END)
        self.progress.configure(value=0)

    def _run_async(self) -> None:
        config_path = self._normalize_path_text(self.config_var.get())
        project_path = self._normalize_path_text(self.project_var.get())

        if not config_path.exists() or not config_path.is_file():
            messagebox.showerror("Invalid Config", f"Config file not found:\n{config_path}")
            self.status_var.set("Failed: invalid config path")
            self._reset_view()
            return

        if config_path.suffix.lower() not in {".yaml", ".yml", ".json"}:
            messagebox.showerror("Invalid Config", "Config file must be .yaml/.yml/.json")
            self.status_var.set("Failed: invalid config extension")
            self._reset_view()
            return

        if not project_path.exists() or not project_path.is_dir():
            messagebox.showerror("Invalid Project", f"Project folder not found:\n{project_path}")
            self.status_var.set("Failed: invalid project path")
            self._reset_view()
            return

        try:
            preloaded_config = load_config(config_path)
        except Exception as exc:
            messagebox.showerror("Config Parse Error", f"Cannot parse config:\n{config_path}\n\n{exc}")
            self.status_var.set("Failed: config parse error")
            self._reset_view()
            return

        self._set_busy(True)
        self.status_var.set("Running analysis...")
        self._append_log(f"Analysis started from GUI. Config={config_path}")

        worker = threading.Thread(
            target=lambda: self._run_sync(preloaded_config, project_path),
            daemon=True,
        )
        worker.start()

    def _progress_update(self, message: str, percent: float) -> None:
        self.after(0, lambda: self._on_progress_message(message, percent))

    def _on_progress_message(self, message: str, percent: float) -> None:
        self.status_var.set(f"{message} ({percent:.0f}%)")
        self.progress.configure(value=percent)

    def _run_sync(self, config, project_path: Path) -> None:
        try:
            config.project_path = str(project_path)
            config.engine = self.engine_var.get()
            config.locale = self.locale_var.get()

            run_dir = run_analysis(
                config=config,
                workspace_root=self.workspace_root,
                progress_callback=self._progress_update,
            )
            summary_path = run_dir / "summary.json"
            payload = json.loads(summary_path.read_text(encoding="utf-8"))

            findings = json.loads((run_dir / "risk_findings.json").read_text(encoding="utf-8")).get("findings", [])
            heatmap = json.loads((run_dir / "risk_heatmap.json").read_text(encoding="utf-8")).get("heatmap", [])
            flowchart_text = (run_dir / "risk_flowchart.mmd").read_text(encoding="utf-8")

            self.after(0, lambda: self._render_result(run_dir, payload, findings, heatmap, flowchart_text))
        except Exception as exc:
            self.after(0, lambda: self._render_error(exc))

    def _render_result(
        self,
        run_dir: Path,
        payload: dict,
        findings: list[dict],
        heatmap: list[dict],
        flowchart_text: str,
    ) -> None:
        self._append_log(f"Completed: {run_dir}")

        self.warn_box.delete("1.0", tk.END)
        warnings = payload.get("warnings", [])
        if warnings:
            for idx, item in enumerate(warnings, start=1):
                self.warn_box.insert(tk.END, f"{idx}. {item}\n")
        else:
            self.warn_box.insert(tk.END, "No warnings detected.\n")

        self._render_heatmap(heatmap)
        self._render_findings(findings)

        self.flowchart_box.delete("1.0", tk.END)
        self.flowchart_box.insert(tk.END, flowchart_text)

        self.summary_box.delete("1.0", tk.END)
        self.summary_box.insert(tk.END, json.dumps(payload, indent=2, ensure_ascii=False))

        self.progress.configure(value=100)
        self.status_var.set(f"Done: {run_dir}")
        self._set_busy(False)

    def _render_heatmap(self, heatmap: list[dict]) -> None:
        self.heatmap_box.delete("1.0", tk.END)
        if not heatmap:
            self.heatmap_box.insert(tk.END, "No risk heatmap data.\n")
            return

        max_score = max(item.get("risk_score", 0) for item in heatmap) or 1
        self.heatmap_box.insert(tk.END, "score | level    | bar                             | file\n")
        self.heatmap_box.insert(tk.END, "-" * 100 + "\n")

        for item in heatmap[:200]:
            score = int(item.get("risk_score", 0))
            level = str(item.get("risk_level", "low"))
            bar_len = max(1, int((score / max_score) * 30))
            bar = "#" * bar_len
            file = str(item.get("file", ""))
            self.heatmap_box.insert(tk.END, f"{score:5d} | {level:8s} | {bar:30s} | {file}\n")

    def _render_findings(self, findings: list[dict]) -> None:
        self.findings_box.delete("1.0", tk.END)
        if not findings:
            self.findings_box.insert(tk.END, "No risk findings.\n")
            return

        self.findings_box.insert(tk.END, "severity | category          | rule_id            | file:line | code\n")
        self.findings_box.insert(tk.END, "-" * 160 + "\n")
        for row in findings[:1500]:
            sev = str(row.get("severity", ""))
            cat = str(row.get("category", ""))
            rule = str(row.get("rule_id", ""))
            file_line = f"{row.get('file', '')}:{row.get('line', '')}"
            code = str(row.get("code", "")).replace("\t", " ")
            self.findings_box.insert(
                tk.END,
                f"{sev:8s} | {cat:17s} | {rule:18s} | {file_line:40s} | {code}\n",
            )

    def _render_error(self, exc: Exception) -> None:
        self._append_log(f"ERROR: {exc}")
        self._append_log(traceback.format_exc())
        self._reset_view()
        self.status_var.set("Failed (reset complete)")
        self._set_busy(False)
        messagebox.showerror("Analysis Failed", f"처리를 완료할 수 없어 초기화했습니다.\n\n{exc}")

    def _append_log(self, message: str) -> None:
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)


def main() -> int:
    app = CodevizGui()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
