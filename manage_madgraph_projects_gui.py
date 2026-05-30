#!/usr/bin/env python3
"""Tkinter-based project manager for reproducible MadGraph workflows."""

from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText

APP_TITLE = "MadGraph Project Manager"
APP_ROOT = Path(__file__).resolve().parent
SETTINGS_PATH = APP_ROOT / ".madgraph_project_manager_settings.json"
DEFAULT_PROJECTS_DIR = APP_ROOT / "madgraph_projects"
DEFAULT_RUNS_DIR = APP_ROOT / "madgraph_runs"
PROJECT_FILENAME = "project.json"
RUN_HISTORY_FILENAME = "run_history.jsonl"
DEFAULT_TEMPLATE = """# This card is rendered and executed by the GUI.
# Use placeholders to keep projects reproducible:
#   ${PROJECT_DIR} ${PROJECT_RUNS_ROOT} ${RUN_TAG} ${RUN_OUTPUT} ${RUN_OUTPUT_Q}

import model sm
define p = g u c d s u~ c~ d~ s~
define j = p

# Example process (edit freely):
generate p p > t t~

# Keep output and launch attached to the selected run directory:
output ${RUN_OUTPUT_Q} -f
launch ${RUN_OUTPUT_Q} -f
"""
PLACEHOLDER_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")
COMMENT_PATTERN = re.compile(r"^\s*#")


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def default_run_tag() -> str:
    return datetime.now().strftime("run_%Y%m%d_%H%M%S")


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower()).strip("_")
    return slug or "project"


def quote_for_madgraph(path: Path) -> str:
    text = str(path)
    if any(char.isspace() for char in text):
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return text


def find_default_mg5() -> str:
    env = os.environ.get("MADGRAPH_EXECUTABLE", "").strip()
    if env and Path(env).exists():
        return env

    binary = shutil.which("mg5_aMC")
    if binary:
        return str(Path(binary).resolve())

    local_candidates = sorted((APP_ROOT / "HERWIG" / "opt").glob("MG5_aMC_*/bin/mg5_aMC"), reverse=True)
    for candidate in local_candidates:
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate.resolve())
    return ""


def normalize_dir(text: str, fallback: Path) -> Path:
    candidate = Path(text.strip()).expanduser() if text.strip() else fallback
    return candidate.resolve()


def has_madgraph_command(text: str, command: str) -> bool:
    token = command.strip().lower()
    for raw_line in text.splitlines():
        if COMMENT_PATTERN.match(raw_line):
            continue
        line = raw_line.strip()
        if not line:
            continue
        pieces = line.split(maxsplit=1)
        if pieces and pieces[0].lower() == token:
            return True
    return False


def expand_placeholders(template: str, variables: Dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return variables.get(key, match.group(0))

    return PLACEHOLDER_PATTERN.sub(replace, template)


@dataclass
class ProjectRecord:
    name: str
    slug: str
    description: str
    madgraph_exec: str
    runs_root: str
    command_template: str
    created_at: str
    updated_at: str
    last_run_at: str = ""
    last_run_output: str = ""

    @classmethod
    def new(cls, name: str, slug: str, madgraph_exec: str, runs_root: str) -> "ProjectRecord":
        now = now_iso()
        return cls(
            name=name,
            slug=slug,
            description="",
            madgraph_exec=madgraph_exec,
            runs_root=runs_root,
            command_template=DEFAULT_TEMPLATE,
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def from_dict(cls, payload: Dict[str, str]) -> "ProjectRecord":
        return cls(
            name=payload.get("name", "").strip(),
            slug=payload.get("slug", "").strip(),
            description=payload.get("description", ""),
            madgraph_exec=payload.get("madgraph_exec", ""),
            runs_root=payload.get("runs_root", ""),
            command_template=payload.get("command_template", DEFAULT_TEMPLATE),
            created_at=payload.get("created_at", now_iso()),
            updated_at=payload.get("updated_at", now_iso()),
            last_run_at=payload.get("last_run_at", ""),
            last_run_output=payload.get("last_run_output", ""),
        )

    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "madgraph_exec": self.madgraph_exec,
            "runs_root": self.runs_root,
            "command_template": self.command_template,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_run_at": self.last_run_at,
            "last_run_output": self.last_run_output,
        }


class ProjectStore:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def set_base_dir(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _project_dir(self, slug: str) -> Path:
        return self.base_dir / slug

    def _project_manifest(self, slug: str) -> Path:
        return self._project_dir(slug) / PROJECT_FILENAME

    def list_projects(self) -> List[ProjectRecord]:
        projects: List[ProjectRecord] = []
        for manifest in sorted(self.base_dir.glob(f"*/{PROJECT_FILENAME}")):
            try:
                payload = json.loads(manifest.read_text())
                project = ProjectRecord.from_dict(payload)
            except Exception:
                continue
            if project.slug and project.name:
                projects.append(project)
        projects.sort(key=lambda item: item.name.lower())
        return projects

    def load_project(self, slug: str) -> ProjectRecord:
        manifest = self._project_manifest(slug)
        payload = json.loads(manifest.read_text())
        return ProjectRecord.from_dict(payload)

    def save_project(self, project: ProjectRecord) -> None:
        project_dir = self._project_dir(project.slug)
        project_dir.mkdir(parents=True, exist_ok=True)
        manifest = project_dir / PROJECT_FILENAME
        manifest.write_text(json.dumps(project.to_dict(), indent=2, sort_keys=True) + "\n")

    def delete_project(self, slug: str) -> None:
        target = self._project_dir(slug)
        if target.exists():
            shutil.rmtree(target)

    def next_available_slug(self, base_slug: str) -> str:
        base = base_slug or "project"
        if not self._project_dir(base).exists():
            return base
        idx = 2
        while True:
            candidate = f"{base}_{idx}"
            if not self._project_dir(candidate).exists():
                return candidate
            idx += 1

    def append_run_history(self, slug: str, entry: Dict[str, str]) -> None:
        history_path = self._project_dir(slug) / RUN_HISTORY_FILENAME
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")

    def load_run_history(self, slug: str, limit: int = 200) -> List[Dict[str, str]]:
        history_path = self._project_dir(slug) / RUN_HISTORY_FILENAME
        if not history_path.exists():
            return []
        entries: List[Dict[str, str]] = []
        for raw_line in history_path.read_text().splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(entry, dict):
                entries.append(entry)
        return entries[-limit:]

    def project_dir(self, slug: str) -> Path:
        return self._project_dir(slug)


class MadGraphProjectManagerGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1200x820")

        self.log_queue: queue.Queue[str] = queue.Queue()
        self.store = ProjectStore(DEFAULT_PROJECTS_DIR)
        self.projects: List[ProjectRecord] = []
        self.current_project: Optional[ProjectRecord] = None
        self.process: Optional[subprocess.Popen[str]] = None
        self.runner_thread: Optional[threading.Thread] = None
        self.current_output_dir = ""
        self.history_index: List[Dict[str, str]] = []

        settings = self._load_settings()
        projects_dir = settings.get("projects_dir", str(DEFAULT_PROJECTS_DIR))
        self.projects_dir_var = tk.StringVar(value=projects_dir)

        self._build_ui()
        self._apply_projects_dir(refresh=False)
        self._refresh_projects()
        self._start_log_pump()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self._build_settings_panel()

        main = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left = ttk.Frame(main, padding=6)
        right = ttk.Frame(main, padding=6)
        main.add(left, weight=1)
        main.add(right, weight=4)

        self._build_project_list(left)
        self._build_project_editor(right)
        self._build_log_panel()

    def _build_settings_panel(self) -> None:
        frame = ttk.Frame(self.root, padding=(10, 10, 10, 0))
        frame.pack(fill=tk.X)

        ttk.Label(frame, text="Projects directory:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.projects_dir_var).grid(row=0, column=1, sticky="ew", padx=(6, 6))
        ttk.Button(frame, text="Browse", command=self._browse_projects_dir).grid(row=0, column=2, padx=(0, 6))
        ttk.Button(frame, text="Apply", command=self._apply_projects_dir).grid(row=0, column=3, padx=(0, 6))
        ttk.Button(frame, text="Reload", command=self._refresh_projects).grid(row=0, column=4)
        frame.columnconfigure(1, weight=1)

    def _build_project_list(self, frame: ttk.Frame) -> None:
        ttk.Label(frame, text="Projects").pack(anchor="w")

        self.project_list = tk.Listbox(frame, height=20, exportselection=False)
        self.project_list.pack(fill=tk.BOTH, expand=True, pady=(4, 8))
        self.project_list.bind("<<ListboxSelect>>", self._on_project_selected)

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X)
        ttk.Button(button_frame, text="New", command=self._new_project).grid(row=0, column=0, sticky="ew")
        ttk.Button(button_frame, text="Duplicate", command=self._duplicate_project).grid(
            row=0, column=1, sticky="ew", padx=(4, 0)
        )
        ttk.Button(button_frame, text="Delete", command=self._delete_project).grid(
            row=0, column=2, sticky="ew", padx=(4, 0)
        )
        ttk.Button(button_frame, text="Open Folder", command=self._open_project_folder).grid(
            row=0, column=3, sticky="ew", padx=(4, 0)
        )
        for col in (0, 1, 2, 3):
            button_frame.columnconfigure(col, weight=1)

    def _build_project_editor(self, frame: ttk.Frame) -> None:
        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        self.project_tab = ttk.Frame(notebook, padding=8)
        self.run_tab = ttk.Frame(notebook, padding=8)
        notebook.add(self.project_tab, text="Project")
        notebook.add(self.run_tab, text="Run")

        self._build_project_tab()
        self._build_run_tab()

    def _build_project_tab(self) -> None:
        frame = self.project_tab

        row = 0
        ttk.Label(frame, text="Name:").grid(row=row, column=0, sticky="w")
        self.name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.name_var).grid(row=row, column=1, sticky="ew", padx=(6, 4))
        ttk.Label(frame, text="Slug:").grid(row=row, column=2, sticky="w")
        self.slug_var = tk.StringVar()
        ttk.Label(frame, textvariable=self.slug_var).grid(row=row, column=3, sticky="w")

        row += 1
        ttk.Label(frame, text="Description:").grid(row=row, column=0, sticky="w")
        self.description_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.description_var).grid(
            row=row, column=1, columnspan=3, sticky="ew", padx=(6, 0)
        )

        row += 1
        ttk.Label(frame, text="MadGraph executable:").grid(row=row, column=0, sticky="w")
        self.mg_exec_var = tk.StringVar(value=find_default_mg5())
        ttk.Entry(frame, textvariable=self.mg_exec_var).grid(row=row, column=1, columnspan=2, sticky="ew", padx=(6, 6))
        ttk.Button(frame, text="Browse", command=self._browse_mg_exec).grid(row=row, column=3, sticky="ew")

        row += 1
        ttk.Label(frame, text="Default runs root:").grid(row=row, column=0, sticky="w")
        self.runs_root_var = tk.StringVar(value=str(DEFAULT_RUNS_DIR))
        ttk.Entry(frame, textvariable=self.runs_root_var).grid(
            row=row, column=1, columnspan=2, sticky="ew", padx=(6, 6)
        )
        ttk.Button(frame, text="Browse", command=self._browse_runs_root).grid(row=row, column=3, sticky="ew")

        row += 1
        ttk.Label(frame, text="MadGraph command template:").grid(row=row, column=0, sticky="nw", pady=(8, 2))
        self.command_text = ScrolledText(frame, height=20, wrap=tk.WORD)
        self.command_text.grid(row=row, column=1, columnspan=3, sticky="nsew", padx=(6, 0), pady=(8, 2))

        row += 1
        placeholder_help = (
            "Placeholders: ${PROJECT_DIR} ${PROJECT_RUNS_ROOT} ${RUN_TAG} ${RUN_OUTPUT} ${RUN_OUTPUT_Q}"
        )
        ttk.Label(frame, text=placeholder_help).grid(row=row, column=0, columnspan=4, sticky="w", pady=(2, 6))

        row += 1
        self.last_run_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.last_run_var).grid(row=row, column=0, columnspan=3, sticky="w")
        ttk.Button(frame, text="Save Project", command=self._save_project_from_ui).grid(row=row, column=3, sticky="ew")

        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.rowconfigure(4, weight=1)

    def _build_run_tab(self) -> None:
        frame = self.run_tab

        row = 0
        ttk.Label(frame, text="Run tag:").grid(row=row, column=0, sticky="w")
        self.run_tag_var = tk.StringVar(value=default_run_tag())
        run_tag_entry = ttk.Entry(frame, textvariable=self.run_tag_var)
        run_tag_entry.grid(row=row, column=1, sticky="ew", padx=(6, 6))
        run_tag_entry.bind("<KeyRelease>", self._on_run_path_inputs_changed)
        ttk.Button(frame, text="New Tag", command=self._reset_run_tag).grid(row=row, column=2, sticky="ew")

        row += 1
        ttk.Label(frame, text="Run output directory (optional):").grid(row=row, column=0, sticky="w")
        self.output_dir_var = tk.StringVar(value="")
        output_entry = ttk.Entry(frame, textvariable=self.output_dir_var)
        output_entry.grid(row=row, column=1, sticky="ew", padx=(6, 6))
        output_entry.bind("<KeyRelease>", self._on_run_path_inputs_changed)
        ttk.Button(frame, text="Browse", command=self._browse_output_dir).grid(row=row, column=2, sticky="ew")

        row += 1
        ttk.Label(frame, text="Resolved output:").grid(row=row, column=0, sticky="w")
        self.output_preview_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.output_preview_var).grid(row=row, column=1, columnspan=2, sticky="w")

        row += 1
        options_frame = ttk.Frame(frame)
        options_frame.grid(row=row, column=0, columnspan=3, sticky="w", pady=(4, 0))
        self.inject_output_var = tk.BooleanVar(value=False)
        self.inject_launch_var = tk.BooleanVar(value=False)
        self.save_rendered_card_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame, text="Inject output command if missing", variable=self.inject_output_var
        ).pack(side=tk.LEFT)
        ttk.Checkbutton(
            options_frame, text="Inject launch command if missing", variable=self.inject_launch_var
        ).pack(side=tk.LEFT, padx=(12, 0))
        ttk.Checkbutton(
            options_frame, text="Store rendered card in run directory", variable=self.save_rendered_card_var
        ).pack(side=tk.LEFT, padx=(12, 0))

        row += 1
        action_frame = ttk.Frame(frame)
        action_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(8, 8))
        self.preview_btn = ttk.Button(action_frame, text="Preview Rendered Card", command=self._preview_rendered_card)
        self.preview_btn.grid(row=0, column=0, sticky="ew")
        self.run_btn = ttk.Button(action_frame, text="Run MadGraph", command=self._start_run)
        self.run_btn.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self.stop_btn = ttk.Button(action_frame, text="Stop", command=self._stop_run, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=2, sticky="ew", padx=(6, 0))
        self.open_output_btn = ttk.Button(action_frame, text="Open Output Folder", command=self._open_output_folder)
        self.open_output_btn.grid(row=0, column=3, sticky="ew", padx=(6, 0))
        for col in (0, 1, 2, 3):
            action_frame.columnconfigure(col, weight=1)

        row += 1
        ttk.Label(frame, text="Run history (latest first):").grid(row=row, column=0, sticky="w")
        self.history_list = tk.Listbox(frame, height=10, exportselection=False)
        self.history_list.grid(row=row + 1, column=0, columnspan=3, sticky="nsew", pady=(4, 0))
        self.history_list.bind("<Double-1>", self._apply_history_selection)

        row += 2
        ttk.Label(
            frame,
            text="Double-click history item to reuse its output directory in the run form.",
        ).grid(row=row, column=0, columnspan=3, sticky="w", pady=(6, 0))

        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(row - 1, weight=1)

    def _build_log_panel(self) -> None:
        container = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        container.pack(fill=tk.BOTH, expand=False)
        ttk.Label(container, text="Activity log:").pack(anchor="w")
        self.log_text = ScrolledText(container, height=12, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load_settings(self) -> Dict[str, str]:
        if not SETTINGS_PATH.exists():
            return {}
        try:
            payload = json.loads(SETTINGS_PATH.read_text())
        except Exception:
            return {}
        if not isinstance(payload, dict):
            return {}
        return {str(k): str(v) for k, v in payload.items()}

    def _save_settings(self) -> None:
        payload = {"projects_dir": self.projects_dir_var.get().strip() or str(DEFAULT_PROJECTS_DIR)}
        SETTINGS_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        self.log_queue.put(message.rstrip("\n"))

    def _start_log_pump(self) -> None:
        def pump() -> None:
            while True:
                try:
                    msg = self.log_queue.get_nowait()
                except queue.Empty:
                    break
                self.log_text.configure(state=tk.NORMAL)
                self.log_text.insert(tk.END, msg + "\n")
                self.log_text.configure(state=tk.DISABLED)
                self.log_text.see(tk.END)
            self.root.after(120, pump)

        pump()

    # ------------------------------------------------------------------
    # Project list actions
    # ------------------------------------------------------------------

    def _apply_projects_dir(self, refresh: bool = True) -> None:
        chosen = normalize_dir(self.projects_dir_var.get(), DEFAULT_PROJECTS_DIR)
        self.projects_dir_var.set(str(chosen))
        self.store.set_base_dir(chosen)
        self._save_settings()
        self._log(f"[info] Using projects directory: {chosen}")
        if refresh:
            self._refresh_projects()

    def _browse_projects_dir(self) -> None:
        selected = filedialog.askdirectory(
            title="Select projects directory", initialdir=self.projects_dir_var.get() or str(DEFAULT_PROJECTS_DIR)
        )
        if selected:
            self.projects_dir_var.set(selected)

    def _refresh_projects(self) -> None:
        selected_slug = self.current_project.slug if self.current_project else ""
        self.projects = self.store.list_projects()
        self.project_list.delete(0, tk.END)
        for item in self.projects:
            label = f"{item.name} [{item.slug}]"
            self.project_list.insert(tk.END, label)
        if not self.projects:
            self.current_project = None
            self._clear_project_form()
            self._refresh_history()
            return

        target_idx = 0
        for idx, project in enumerate(self.projects):
            if project.slug == selected_slug:
                target_idx = idx
                break
        self.project_list.selection_set(target_idx)
        self.project_list.event_generate("<<ListboxSelect>>")

    def _clear_project_form(self) -> None:
        self.name_var.set("")
        self.slug_var.set("")
        self.description_var.set("")
        self.mg_exec_var.set(find_default_mg5())
        self.runs_root_var.set(str(DEFAULT_RUNS_DIR))
        self.command_text.delete("1.0", tk.END)
        self.command_text.insert("1.0", DEFAULT_TEMPLATE)
        self.last_run_var.set("No project selected.")
        self._reset_run_tag()
        self.output_dir_var.set("")
        self._refresh_output_preview()

    def _on_project_selected(self, event: tk.Event | None = None) -> None:
        selection = self.project_list.curselection()
        if not selection:
            return
        index = int(selection[0])
        if index < 0 or index >= len(self.projects):
            return
        self.current_project = self.projects[index]
        self._load_project_into_form(self.current_project)

    def _load_project_into_form(self, project: ProjectRecord) -> None:
        self.name_var.set(project.name)
        self.slug_var.set(project.slug)
        self.description_var.set(project.description)
        self.mg_exec_var.set(project.madgraph_exec or find_default_mg5())
        self.runs_root_var.set(project.runs_root or str(DEFAULT_RUNS_DIR))
        self.command_text.delete("1.0", tk.END)
        self.command_text.insert("1.0", project.command_template or DEFAULT_TEMPLATE)
        if project.last_run_at:
            self.last_run_var.set(f"Last run: {project.last_run_at} -> {project.last_run_output}")
        else:
            self.last_run_var.set("Last run: n/a")
        self._reset_run_tag()
        self.output_dir_var.set("")
        self._refresh_output_preview()
        self._refresh_history()

    def _new_project(self) -> None:
        name = simpledialog.askstring("New project", "Project name:")
        if not name:
            return
        base_slug = slugify(name)
        slug = self.store.next_available_slug(base_slug)
        mg_exec = self.mg_exec_var.get().strip() or find_default_mg5()
        runs_root = self.runs_root_var.get().strip() or str(DEFAULT_RUNS_DIR)
        project = ProjectRecord.new(name=name.strip(), slug=slug, madgraph_exec=mg_exec, runs_root=runs_root)
        self.current_project = project
        self._load_project_into_form(project)
        self._log(f"[info] Created unsaved project '{project.name}' ({project.slug}). Save to persist it.")

    def _duplicate_project(self) -> None:
        source = self.current_project
        if source is None:
            messagebox.showerror("No project", "Select a project first.")
            return
        name = simpledialog.askstring("Duplicate project", "New project name:", initialvalue=f"{source.name} Copy")
        if not name:
            return
        base_slug = slugify(name)
        slug = self.store.next_available_slug(base_slug)
        duplicated = ProjectRecord(
            name=name.strip(),
            slug=slug,
            description=source.description,
            madgraph_exec=source.madgraph_exec,
            runs_root=source.runs_root,
            command_template=source.command_template,
            created_at=now_iso(),
            updated_at=now_iso(),
        )
        self.store.save_project(duplicated)
        self._log(f"[success] Duplicated '{source.name}' as '{duplicated.name}' ({duplicated.slug}).")
        self.current_project = duplicated
        self._refresh_projects()

    def _delete_project(self) -> None:
        project = self.current_project
        if project is None:
            messagebox.showerror("No project", "Select a project first.")
            return
        answer = messagebox.askyesno(
            "Delete project",
            f"Delete project '{project.name}'?\nThis removes its saved template and run history.",
            icon="warning",
        )
        if not answer:
            return
        self.store.delete_project(project.slug)
        self._log(f"[success] Deleted project '{project.name}' ({project.slug}).")
        self.current_project = None
        self._refresh_projects()

    def _open_project_folder(self) -> None:
        project = self.current_project
        if project is None:
            messagebox.showerror("No project", "Select a project first.")
            return
        target = self.store.project_dir(project.slug)
        target.mkdir(parents=True, exist_ok=True)
        self._open_directory(target)

    def _save_project_from_ui(self) -> None:
        project = self._collect_project_from_form(require_existing=False)
        if project is None:
            return
        self.store.save_project(project)
        self.current_project = project
        self._log(f"[success] Saved project '{project.name}' ({project.slug}).")
        self._refresh_projects()

    def _collect_project_from_form(self, require_existing: bool) -> Optional[ProjectRecord]:
        current_slug = self.current_project.slug if self.current_project else ""

        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Invalid project", "Project name is required.")
            return None

        mg_exec = self.mg_exec_var.get().strip()
        if not mg_exec:
            messagebox.showerror("Invalid project", "MadGraph executable path is required.")
            return None
        mg_exec_path = Path(mg_exec).expanduser()
        if not mg_exec_path.exists():
            messagebox.showerror("Invalid project", f"MadGraph executable does not exist:\n{mg_exec_path}")
            return None
        if not os.access(mg_exec_path, os.X_OK):
            messagebox.showerror("Invalid project", f"MadGraph executable is not executable:\n{mg_exec_path}")
            return None

        runs_root = self.runs_root_var.get().strip()
        if not runs_root:
            messagebox.showerror("Invalid project", "Default runs root is required.")
            return None
        runs_root_path = Path(runs_root).expanduser().resolve()

        command_template = self.command_text.get("1.0", tk.END).strip()
        if not command_template:
            messagebox.showerror("Invalid project", "MadGraph command template cannot be empty.")
            return None

        if require_existing and self.current_project is None:
            messagebox.showerror("No project", "Select or save a project first.")
            return None

        if current_slug:
            slug = current_slug
        else:
            slug = self.store.next_available_slug(slugify(name))

        now = now_iso()
        created_at = self.current_project.created_at if self.current_project else now
        last_run_at = self.current_project.last_run_at if self.current_project else ""
        last_run_output = self.current_project.last_run_output if self.current_project else ""
        project = ProjectRecord(
            name=name,
            slug=slug,
            description=self.description_var.get().strip(),
            madgraph_exec=str(mg_exec_path),
            runs_root=str(runs_root_path),
            command_template=command_template + "\n",
            created_at=created_at,
            updated_at=now,
            last_run_at=last_run_at,
            last_run_output=last_run_output,
        )
        return project

    # ------------------------------------------------------------------
    # Run actions
    # ------------------------------------------------------------------

    def _reset_run_tag(self) -> None:
        self.run_tag_var.set(default_run_tag())
        self._refresh_output_preview()

    def _on_run_path_inputs_changed(self, event: tk.Event | None = None) -> None:
        self._refresh_output_preview()

    def _resolve_output_dir(
        self,
        project: ProjectRecord,
        run_tag: Optional[str] = None,
        explicit_output: Optional[str] = None,
    ) -> Path:
        explicit = (explicit_output if explicit_output is not None else self.output_dir_var.get()).strip()
        if explicit:
            return Path(explicit).expanduser().resolve()
        chosen_run_tag = (run_tag if run_tag is not None else self.run_tag_var.get()).strip() or default_run_tag()
        root_dir = Path(project.runs_root).expanduser().resolve()
        return root_dir / project.slug / chosen_run_tag

    def _refresh_output_preview(self) -> None:
        project = self.current_project
        if project is None:
            self.current_output_dir = ""
            self.output_preview_var.set("")
            return
        output_dir = self._resolve_output_dir(project)
        self.current_output_dir = str(output_dir)
        self.output_preview_var.set(self.current_output_dir)

    def _build_rendered_commands(self, project: ProjectRecord, run_tag: str, output_dir: Path) -> str:
        project_dir = self.store.project_dir(project.slug).resolve()
        runs_root = Path(project.runs_root).expanduser().resolve()

        variables = {
            "PROJECT_DIR": str(project_dir),
            "PROJECT_RUNS_ROOT": str(runs_root),
            "RUN_TAG": run_tag,
            "RUN_OUTPUT": str(output_dir),
            "RUN_OUTPUT_Q": quote_for_madgraph(output_dir),
        }
        rendered = expand_placeholders(project.command_template, variables).strip() + "\n"

        if self.inject_output_var.get() and not has_madgraph_command(rendered, "output"):
            rendered += f"output {quote_for_madgraph(output_dir)} -f\n"
        if self.inject_launch_var.get() and not has_madgraph_command(rendered, "launch"):
            rendered += f"launch {quote_for_madgraph(output_dir)} -f\n"

        return rendered

    def _preview_rendered_card(self) -> None:
        project = self._collect_project_from_form(require_existing=False)
        if project is None:
            return
        run_tag = self.run_tag_var.get().strip() or default_run_tag()
        output_dir = self._resolve_output_dir(
            project,
            run_tag=run_tag,
            explicit_output=self.output_dir_var.get(),
        )
        rendered = self._build_rendered_commands(project, run_tag, output_dir)
        self._show_text_window("Rendered MadGraph Card", rendered)

    def _start_run(self) -> None:
        if self.process is not None:
            messagebox.showerror("Busy", "A MadGraph process is already running.")
            return

        project = self._collect_project_from_form(require_existing=False)
        if project is None:
            return

        run_tag = self.run_tag_var.get().strip() or default_run_tag()
        explicit_output = self.output_dir_var.get()
        output_dir = self._resolve_output_dir(project, run_tag=run_tag, explicit_output=explicit_output)
        rendered = self._build_rendered_commands(project, run_tag, output_dir)

        self.store.save_project(project)
        self.current_project = project
        output_dir.parent.mkdir(parents=True, exist_ok=True)
        project_dir = self.store.project_dir(project.slug)
        cards_dir = project_dir / "cards"
        cards_dir.mkdir(parents=True, exist_ok=True)
        card_path = cards_dir / f"{run_tag}.mg5"
        card_path.write_text(rendered)
        self.current_output_dir = str(output_dir)
        self.output_preview_var.set(self.current_output_dir)

        self._log(f"[info] Running {project.madgraph_exec} with card {card_path}")
        self._log(f"[info] Target output directory: {output_dir}")

        self.run_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        thread = threading.Thread(
            target=self._run_worker,
            args=(project, run_tag, output_dir, card_path, rendered),
            daemon=True,
        )
        self.runner_thread = thread
        thread.start()

    def _run_worker(
        self,
        project: ProjectRecord,
        run_tag: str,
        output_dir: Path,
        card_path: Path,
        rendered_card: str,
    ) -> None:
        rc = -1
        try:
            proc = subprocess.Popen(
                [project.madgraph_exec, str(card_path)],
                cwd=str(self.store.project_dir(project.slug)),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            self.process = proc
            assert proc.stdout is not None
            for line in proc.stdout:
                self._log(f"[mg5] {line.rstrip()}")
            rc = proc.wait()
        except Exception as exc:
            self._log(f"[error] Failed to run MadGraph: {exc}")
        finally:
            if self.save_rendered_card_var.get():
                try:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    rendered_copy = output_dir / "rendered_commands.mg5"
                    rendered_copy.write_text(rendered_card)
                except Exception as exc:
                    self._log(f"[warning] Could not store rendered card in run directory: {exc}")

            history_entry = {
                "timestamp": now_iso(),
                "run_tag": run_tag,
                "output_dir": str(output_dir),
                "card_path": str(card_path),
                "return_code": str(rc),
            }
            self.store.append_run_history(project.slug, history_entry)

            project.last_run_at = history_entry["timestamp"]
            project.last_run_output = str(output_dir)
            project.updated_at = now_iso()
            self.store.save_project(project)

            if rc == 0:
                self._log("[success] MadGraph run completed.")
            elif rc == -15:
                self._log("[warning] MadGraph run terminated by user.")
            else:
                self._log(f"[error] MadGraph run finished with return code {rc}.")

            self.process = None
            self.root.after(0, self._on_run_finished)

    def _on_run_finished(self) -> None:
        self.run_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self._refresh_projects()
        self._refresh_history()
        if self.current_project and self.current_project.last_run_at:
            self.last_run_var.set(
                f"Last run: {self.current_project.last_run_at} -> {self.current_project.last_run_output}"
            )

    def _stop_run(self) -> None:
        proc = self.process
        if proc is None:
            return
        self._log("[info] Terminating MadGraph process...")
        try:
            proc.terminate()
        except Exception as exc:
            self._log(f"[warning] Failed to terminate process cleanly: {exc}")

    def _open_output_folder(self) -> None:
        target = self.current_output_dir.strip() or self.output_preview_var.get().strip()
        if not target:
            messagebox.showerror("No output", "No output directory is resolved yet.")
            return
        path = Path(target).expanduser()
        if not path.exists():
            messagebox.showerror("Missing directory", f"Output directory does not exist:\n{path}")
            return
        self._open_directory(path)

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def _refresh_history(self) -> None:
        self.history_index = []
        self.history_list.delete(0, tk.END)
        if self.current_project is None:
            return
        entries = list(reversed(self.store.load_run_history(self.current_project.slug)))
        self.history_index = entries
        for entry in entries:
            stamp = entry.get("timestamp", "?")
            code = entry.get("return_code", "?")
            tag = entry.get("run_tag", "?")
            out_dir = entry.get("output_dir", "")
            label = f"{stamp} | rc={code} | {tag} | {out_dir}"
            self.history_list.insert(tk.END, label)

    def _apply_history_selection(self, event: tk.Event | None = None) -> None:
        selection = self.history_list.curselection()
        if not selection:
            return
        idx = int(selection[0])
        if idx < 0 or idx >= len(self.history_index):
            return
        item = self.history_index[idx]
        output_dir = item.get("output_dir", "").strip()
        run_tag = item.get("run_tag", "").strip()
        if output_dir:
            self.output_dir_var.set(output_dir)
        if run_tag:
            self.run_tag_var.set(run_tag)
        self._refresh_output_preview()

    # ------------------------------------------------------------------
    # Browsers and dialogs
    # ------------------------------------------------------------------

    def _browse_mg_exec(self) -> None:
        selected = filedialog.askopenfilename(
            title="Select MadGraph executable",
            initialdir=str(Path(self.mg_exec_var.get() or APP_ROOT).expanduser()),
        )
        if selected:
            self.mg_exec_var.set(selected)

    def _browse_runs_root(self) -> None:
        selected = filedialog.askdirectory(
            title="Select default runs root",
            initialdir=self.runs_root_var.get() or str(DEFAULT_RUNS_DIR),
        )
        if selected:
            self.runs_root_var.set(selected)
            self._refresh_output_preview()

    def _browse_output_dir(self) -> None:
        initial = self.output_dir_var.get().strip() or self.output_preview_var.get().strip() or str(DEFAULT_RUNS_DIR)
        selected = filedialog.askdirectory(title="Select run output directory", initialdir=initial)
        if selected:
            self.output_dir_var.set(selected)
            self._refresh_output_preview()

    def _show_text_window(self, title: str, text: str) -> None:
        top = tk.Toplevel(self.root)
        top.title(title)
        top.geometry("900x650")
        widget = ScrolledText(top, wrap=tk.WORD)
        widget.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        widget.insert("1.0", text)
        widget.configure(state=tk.DISABLED)
        ttk.Button(top, text="Close", command=top.destroy).pack(pady=(0, 8))

    def _open_directory(self, path: Path) -> None:
        try:
            subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            messagebox.showerror("Open folder failed", f"Could not open folder:\n{path}\n\n{exc}")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _on_close(self) -> None:
        if self.process is not None:
            if not messagebox.askyesno("Quit", "A MadGraph process is still running. Quit anyway?"):
                return
            try:
                self.process.terminate()
            except Exception:
                pass
        self._save_settings()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    app = MadGraphProjectManagerGUI(root)
    app._log("[info] Ready. Create or select a project, then run MadGraph cards.")
    root.mainloop()


if __name__ == "__main__":
    main()
