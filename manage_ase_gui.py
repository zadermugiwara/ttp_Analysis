#!/usr/bin/env python3
"""PySide6 GUI wrapper around manage_ase workflows."""

from __future__ import annotations

import json
from collections import deque
import queue
import shlex
import subprocess
import threading
from pathlib import Path
from typing import Any, Callable, List, Optional

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

SIMULATION_SEMAPHORE = threading.Semaphore(3)
SCENARIO_OPTIONS = ["default", "plus80", "minus80", "ISR", "plus80ISR", "minus80ISR"]
SCENARIO_BASE_HINTS = {
    "default": "ttp_Analysis",
    "plus80": "ttp_Analysis+80",
    "minus80": "ttp_Analysis-80",
    "ISR": "ttp_AnalysisISR",
    "plus80ISR": "ttp_Analysis+80ISR",
    "minus80ISR": "ttp_Analysis-80ISR",
}
AGGREGATE_BASE_LABELS = {".", "", "Analysis_Programs"}
DEFAULT_DISCOVERY_MASSES = [1200, 1600, 2000, 2400]
ROOT_LOG_HEAD = 60
ROOT_LOG_TAIL = 60

from manage_ase import (
    SimulationConfig,
    discover_masses,
    find_combined_targets,
    perform_simulation,
    run_shell_script,
    update_analysis_files,
)


class ManageASEGUI(QMainWindow):
    ui_call_requested = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ASE Manager")
        self.resize(1220, 860)

        self.log_queue: queue.Queue[str] = queue.Queue()
        self.masses = discover_masses()
        self.targets = []

        self._build_ui()
        self._apply_theme()
        self.ui_call_requested.connect(self._execute_ui_call)
        self._refresh_targets()
        self._start_log_timer()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        self.notebook = QTabWidget()
        self.sim_frame = QWidget()
        self.analysis_frame = QWidget()
        self.notebook.addTab(self.sim_frame, "Simulation")
        self.notebook.addTab(self.analysis_frame, "Analysis")

        self._build_simulation_tab()
        self._build_analysis_tab()

        log_panel = self._build_log_panel()

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.notebook)
        splitter.addWidget(log_panel)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([620, 220])
        root_layout.addWidget(splitter)

        status = QStatusBar(self)
        status.showMessage("Ready")
        self.setStatusBar(status)

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                font-size: 12px;
            }
            QMainWindow, QWidget#centralWidget {
                background: #f4f6f8;
            }
            QTabWidget::pane {
                border: 1px solid #d7dbe0;
                background: #ffffff;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #e8edf2;
                border: 1px solid #d7dbe0;
                padding: 8px 14px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom-color: #ffffff;
                font-weight: 600;
            }
            QGroupBox {
                border: 1px solid #d8dee6;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                background: #ffffff;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }
            QLineEdit, QComboBox, QListWidget, QTextEdit {
                border: 1px solid #c8d0da;
                border-radius: 8px;
                background: #ffffff;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
                width: 22px;
            }
            QPushButton {
                border: 1px solid #c8d0da;
                background: #ffffff;
                border-radius: 8px;
                padding: 7px 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #eef4ff;
                border-color: #8cb3ff;
            }
            QPushButton:disabled {
                color: #8f98a3;
                background: #f1f3f5;
            }
            QPushButton#primaryButton {
                background: #1463ff;
                color: white;
                border-color: #1463ff;
            }
            QPushButton#primaryButton:hover {
                background: #0f56e0;
                border-color: #0f56e0;
            }
            QPushButton#successButton {
                background: #117a43;
                color: white;
                border-color: #117a43;
            }
            QPushButton#successButton:hover {
                background: #0d6738;
                border-color: #0d6738;
            }
            QLabel[muted='true'] {
                color: #607080;
            }
            """
        )

    def _build_simulation_tab(self) -> None:
        layout = QVBoxLayout(self.sim_frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        card = QGroupBox("Simulation Setup")
        form = QFormLayout(card)
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(10)

        self.template_mass_combo = QComboBox()
        template_values = [str(m) for m in self.masses] or ["N/A"]
        self.template_mass_combo.addItems(template_values)
        self.template_mass_var = self.template_mass_combo
        form.addRow("Template mass (GeV):", self.template_mass_combo)

        self.custom_mass_entry = QLineEdit()
        self.custom_mass_entry.setPlaceholderText("Optional, e.g. 1800")
        form.addRow("Custom TP mass (optional):", self.custom_mass_entry)

        self.kappa_entry = QLineEdit()
        self.kappa_entry.setPlaceholderText("Optional, e.g. 0.03")
        form.addRow("Kappa (optional):", self.kappa_entry)

        pol_row = QWidget()
        pol_layout = QHBoxLayout(pol_row)
        pol_layout.setContentsMargins(0, 0, 0, 0)
        pol_layout.setSpacing(12)
        self.pol_group = QButtonGroup(self)
        self.pol_none_radio = QRadioButton("None")
        self.pol_plus_radio = QRadioButton("+80")
        self.pol_minus_radio = QRadioButton("-80")
        for i, radio in enumerate((self.pol_none_radio, self.pol_plus_radio, self.pol_minus_radio)):
            self.pol_group.addButton(radio, i)
            pol_layout.addWidget(radio)
        self.pol_none_radio.setChecked(True)
        pol_layout.addStretch(1)
        form.addRow("Polarization:", pol_row)

        self.isr_check = QCheckBox("Enable ISR")
        self.isr_var = self.isr_check
        form.addRow("ISR:", self.isr_check)

        self.nevents_entry = QLineEdit("100")
        form.addRow("Number of events:", self.nevents_entry)

        self.run_name_entry = QLineEdit()
        self.run_name_entry.setPlaceholderText("Optional run label")
        form.addRow("Run name (optional):", self.run_name_entry)

        layout.addWidget(card)

        actions = QFrame()
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)
        self.sim_btn = QPushButton("Run Simulation")
        self.sim_btn.setObjectName("primaryButton")
        self.sim_btn.clicked.connect(self._start_simulation)
        actions_layout.addWidget(self.sim_btn)
        actions_layout.addStretch(1)
        layout.addWidget(actions)
        layout.addStretch(1)

    def _build_analysis_tab(self) -> None:
        outer = QVBoxLayout(self.analysis_frame)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(10)

        top_group = QGroupBox("Analysis Target")
        top_grid = QGridLayout(top_group)
        top_grid.setHorizontalSpacing(10)
        top_grid.setVerticalSpacing(8)

        top_grid.addWidget(QLabel("Analysis directory:"), 0, 0)
        self.target_combo = QComboBox()
        self.target_combo.setEditable(False)
        self.target_combo.currentTextChanged.connect(self._on_target_change)
        top_grid.addWidget(self.target_combo, 0, 1)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_targets)
        top_grid.addWidget(refresh_btn, 0, 2)
        top_grid.setColumnStretch(1, 1)
        outer.addWidget(top_group)

        presets_group = QGroupBox("smart_* Presets")
        presets_grid = QGridLayout(presets_group)
        presets_grid.setHorizontalSpacing(10)
        presets_grid.setVerticalSpacing(8)

        self.hist_pos_list = self._make_multi_list()
        self.hist_opt_list = self._make_multi_list()
        self.analysis_pos_list = self._make_multi_list()
        self.analysis_j_list = self._make_multi_list()
        self.analysis_include_list = self._make_multi_list()
        self.analysis_exclude_list = self._make_multi_list()
        self.analysis_misc_list = self._make_multi_list()
        self.analysis_misc_list.setMinimumHeight(90)

        presets_grid.addWidget(QLabel("smart_Histograms positional presets:"), 0, 0)
        presets_grid.addWidget(self.hist_pos_list, 0, 1)
        presets_grid.addWidget(QLabel("smart_Histograms option presets:"), 0, 2)
        presets_grid.addWidget(self.hist_opt_list, 0, 3)

        presets_grid.addWidget(QLabel("smart_Analysis positional presets:"), 1, 0)
        presets_grid.addWidget(self.analysis_pos_list, 1, 1)
        presets_grid.addWidget(QLabel("-j presets:"), 1, 2)
        presets_grid.addWidget(self.analysis_j_list, 1, 3)

        presets_grid.addWidget(QLabel("--include presets:"), 2, 0)
        presets_grid.addWidget(self.analysis_include_list, 2, 1)
        presets_grid.addWidget(QLabel("--exclude presets:"), 2, 2)
        presets_grid.addWidget(self.analysis_exclude_list, 2, 3)

        presets_grid.addWidget(QLabel("Misc options:"), 3, 0)
        presets_grid.addWidget(self.analysis_misc_list, 3, 1)

        self.run_hist_btn = QPushButton("Run smart_Histograms.sh")
        self.run_hist_btn.clicked.connect(self._run_histograms_only)
        self.run_analysis_btn = QPushButton("Run smart_Analysis.sh")
        self.run_analysis_btn.clicked.connect(self._run_analysis_only)
        self.run_pipeline_btn = QPushButton("Run Both")
        self.run_pipeline_btn.setObjectName("successButton")
        self.run_pipeline_btn.clicked.connect(self._run_combined_analysis)
        self.launch_tbrowser_btn = QPushButton("Launch TBrowser")
        self.launch_tbrowser_btn.clicked.connect(self._launch_tbrowser)

        action_bar = QWidget()
        action_bar_layout = QHBoxLayout(action_bar)
        action_bar_layout.setContentsMargins(0, 0, 0, 0)
        action_bar_layout.setSpacing(8)
        action_bar_layout.addWidget(self.launch_tbrowser_btn)
        action_bar_layout.addWidget(self.run_hist_btn)
        action_bar_layout.addWidget(self.run_analysis_btn)
        action_bar_layout.addWidget(self.run_pipeline_btn)
        presets_grid.addWidget(action_bar, 4, 0, 1, 4)

        for col in (1, 3):
            presets_grid.setColumnStretch(col, 1)
        for row in (0, 1, 2, 3):
            presets_grid.setRowStretch(row, 1)

        outer.addWidget(presets_group, stretch=2)

        discovery_group = QGroupBox("ROOT Discovery / Plot Analysis")
        disc_grid = QGridLayout(discovery_group)
        disc_grid.setHorizontalSpacing(10)
        disc_grid.setVerticalSpacing(8)

        mass_choices = [str(m) for m in (self.masses or DEFAULT_DISCOVERY_MASSES)]
        default_mass = mass_choices[0] if mass_choices else ""
        self.fa_mass_combo = QComboBox()
        self.fa_mass_combo.setEditable(True)
        self.fa_mass_combo.addItems(mass_choices)
        self.fa_mass_combo.setCurrentText(default_mass)
        self.fa_mass_var = self.fa_mass_combo

        self.fa_scenario_combo = QComboBox()
        self.fa_scenario_combo.setEditable(True)
        self.fa_scenario_combo.addItems(SCENARIO_OPTIONS)
        self.fa_scenario_combo.setCurrentText(SCENARIO_OPTIONS[0] if SCENARIO_OPTIONS else "")
        self.fa_scenario_combo.currentTextChanged.connect(self._on_scenario_change)
        self.fa_scenario_var = self.fa_scenario_combo

        self.fa_basedir_combo = QComboBox()
        self.fa_basedir_combo.setEditable(True)
        self.fa_basedir_combo.setCurrentText(".")
        self.fa_basedir_combo.currentTextChanged.connect(self._on_basedir_change)
        if self.fa_basedir_combo.lineEdit() is not None:
            self.fa_basedir_combo.lineEdit().editingFinished.connect(self._on_basedir_change)
        self.fa_basedir_var = self.fa_basedir_combo

        self.fa_xsec_entry = QLineEdit()
        self.fa_xsec_entry.setPlaceholderText("Optional")
        self.fa_extra_args_entry = QLineEdit()
        self.fa_extra_args_entry.setPlaceholderText('["tag", true]')

        disc_grid.addWidget(QLabel("Discovery mass (GeV):"), 0, 0)
        disc_grid.addWidget(self.fa_mass_combo, 0, 1)
        disc_grid.addWidget(QLabel("Scenario:"), 0, 2)
        disc_grid.addWidget(self.fa_scenario_combo, 0, 3)

        disc_grid.addWidget(QLabel("Base directory:"), 1, 0)
        disc_grid.addWidget(self.fa_basedir_combo, 1, 1)
        disc_grid.addWidget(QLabel("Override xsec (pb):"), 1, 2)
        disc_grid.addWidget(self.fa_xsec_entry, 1, 3)

        disc_grid.addWidget(QLabel("Extra arguments (JSON list, optional):"), 2, 0)
        disc_grid.addWidget(self.fa_extra_args_entry, 2, 1, 1, 3)

        self.run_general_btn = QPushButton("Run full_analysis_with_plot_general.C")
        self.run_general_btn.setObjectName("primaryButton")
        self.run_general_btn.clicked.connect(self._run_full_analysis_general)
        disc_grid.addWidget(self.run_general_btn, 3, 0, 1, 4)

        for col in (1, 3):
            disc_grid.setColumnStretch(col, 1)

        outer.addWidget(discovery_group)

        resonance_group = QGroupBox("Resonance Finder")
        res_grid = QGridLayout(resonance_group)
        res_grid.setHorizontalSpacing(10)
        res_grid.setVerticalSpacing(8)

        self.res_workspace_combo = QComboBox()
        self.res_workspace_combo.setEditable(True)
        self.res_workspace_var = self.res_workspace_combo
        self.rescan_ws_btn = QPushButton("Rescan")
        self.rescan_ws_btn.clicked.connect(self._update_res_workspace_choices)

        self.res_wsname_entry = QLineEdit("myWS")
        self.res_pdf_entry = QLineEdit("model")
        self.res_data_entry = QLineEdit("data")
        self.res_obs_entry = QLineEdit("invMass")
        self.res_binwidth_entry = QLineEdit("5.0")
        self.res_step_entry = QLineEdit("5.0")
        self.res_min_entry = QLineEdit("30.0")
        self.res_max_entry = QLineEdit("150.0")
        self.res_save_plots_check = QCheckBox("Save diagnostic plots")
        self.res_save_plots_check.setChecked(True)
        self.res_save_plots_var = self.res_save_plots_check

        res_grid.addWidget(QLabel("Workspace (myWS*.root):"), 0, 0)
        res_grid.addWidget(self.res_workspace_combo, 0, 1, 1, 2)
        res_grid.addWidget(self.rescan_ws_btn, 0, 3)

        res_grid.addWidget(QLabel("Workspace name:"), 1, 0)
        res_grid.addWidget(self.res_wsname_entry, 1, 1)
        res_grid.addWidget(QLabel("PDF name:"), 1, 2)
        res_grid.addWidget(self.res_pdf_entry, 1, 3)

        res_grid.addWidget(QLabel("Dataset name:"), 2, 0)
        res_grid.addWidget(self.res_data_entry, 2, 1)
        res_grid.addWidget(QLabel("Observable:"), 2, 2)
        res_grid.addWidget(self.res_obs_entry, 2, 3)

        res_grid.addWidget(QLabel("Bin width (GeV):"), 3, 0)
        res_grid.addWidget(self.res_binwidth_entry, 3, 1)
        res_grid.addWidget(QLabel("Step width (GeV):"), 3, 2)
        res_grid.addWidget(self.res_step_entry, 3, 3)

        res_grid.addWidget(QLabel("Min window (GeV):"), 4, 0)
        res_grid.addWidget(self.res_min_entry, 4, 1)
        res_grid.addWidget(QLabel("Max window (GeV):"), 4, 2)
        res_grid.addWidget(self.res_max_entry, 4, 3)

        res_grid.addWidget(self.res_save_plots_check, 5, 0, 1, 2)

        self.run_resonance_btn = QPushButton("Run find_resonance_agnostic.C")
        self.run_resonance_btn.clicked.connect(self._run_resonance_finder)
        res_grid.addWidget(self.run_resonance_btn, 6, 0, 1, 4)

        for col in (1, 3):
            res_grid.setColumnStretch(col, 1)

        outer.addWidget(resonance_group)

    def _build_log_panel(self) -> QWidget:
        group = QGroupBox("Activity Log")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 10, 10, 10)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        mono = QFont("Monospace")
        mono.setStyleHint(QFont.Monospace)
        self.log_text.setFont(mono)
        layout.addWidget(self.log_text)
        return group

    def _make_multi_list(self) -> QListWidget:
        widget = QListWidget()
        widget.setSelectionMode(QListWidget.MultiSelection)
        widget.setAlternatingRowColors(True)
        return widget

    def _start_log_timer(self) -> None:
        self._log_timer = QTimer(self)
        self._log_timer.timeout.connect(self._process_log_queue)
        self._log_timer.start(150)

    def _call_in_main(self, fn: Callable[[], None]) -> None:
        self.ui_call_requested.emit(fn)

    def _execute_ui_call(self, fn: Callable[[], None]) -> None:
        fn()

    def _set_button_enabled(self, button: QPushButton, enabled: bool) -> None:
        self._call_in_main(lambda: button.setEnabled(enabled))

    def _show_error(self, title: str, message: str) -> None:
        self._call_in_main(lambda: QMessageBox.critical(self, title, message))

    def _show_warning(self, title: str, message: str) -> None:
        self._call_in_main(lambda: QMessageBox.warning(self, title, message))

    def _combo_text(self, combo: QComboBox) -> str:
        return combo.currentText().strip()

    def _set_combo_values(self, combo: QComboBox, values: List[str]) -> None:
        current = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(values)
        if current:
            combo.setCurrentText(current)
        combo.blockSignals(False)

    def _selected_entries(self, listbox: QListWidget) -> List[str]:
        return [item.text() for item in listbox.selectedItems()]

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        self.log_queue.put(message.rstrip("\n"))

    def _process_log_queue(self) -> None:
        while True:
            try:
                msg = self.log_queue.get_nowait()
            except queue.Empty:
                break
            self.log_text.append(msg)
        sb = self.statusBar()
        if sb is not None:
            sb.showMessage("Running" if not self.log_queue.empty() else "Ready", 1200)

    # ------------------------------------------------------------------
    # Simulation handling
    # ------------------------------------------------------------------

    def _start_simulation(self) -> None:
        if not self.masses:
            self._show_error("Error", "No template masses were found.")
            return

        try:
            template_mass = int(self._combo_text(self.template_mass_combo))
        except ValueError:
            self._show_error("Invalid input", "Template mass must be an integer value.")
            return

        custom_mass_text = self.custom_mass_entry.text().strip()
        if custom_mass_text:
            try:
                mass = int(custom_mass_text)
            except ValueError:
                self._show_error("Invalid input", "Custom mass must be an integer value.")
                return
        else:
            mass = template_mass

        kappa_text = self.kappa_entry.text().strip()
        try:
            kappa_value = float(kappa_text) if kappa_text else None
        except ValueError:
            self._show_error("Invalid input", "Kappa must be a numeric value.")
            return

        pol = self._selected_polarization_label()
        polarization = None if pol == "None" else pol
        isr = self.isr_check.isChecked()

        try:
            nevents = int(self.nevents_entry.text())
            if nevents <= 0:
                raise ValueError
        except ValueError:
            self._show_error("Invalid input", "Number of events must be a positive integer.")
            return

        run_name = self.run_name_entry.text().strip() or None

        config = SimulationConfig(
            mass=mass,
            template_mass=template_mass,
            kappa=kappa_value,
            polarization=polarization,
            isr=isr,
            nevents=nevents,
            run_name=run_name,
        )

        self._log(f"[info] Starting simulation with config: {config}")
        threading.Thread(target=self._simulation_worker, args=(config,), daemon=True).start()

    def _selected_polarization_label(self) -> str:
        if self.pol_plus_radio.isChecked():
            return "+80"
        if self.pol_minus_radio.isChecked():
            return "-80"
        return "None"

    def _simulation_worker(self, config: SimulationConfig) -> None:
        acquired = SIMULATION_SEMAPHORE.acquire(blocking=False)
        if not acquired:
            self._log("[info] All simulation slots busy; queuing request.")
            SIMULATION_SEMAPHORE.acquire()
        try:
            hepmc_path = perform_simulation(config, logger=self._log)
            update_analysis_files(config, hepmc_path, logger=self._log)
            self._log("[success] Simulation completed.")
            self._call_in_main(self._refresh_targets)
        except Exception as exc:  # noqa: BLE001 - surfaced to user log
            self._log(f"[error] {exc}")
            self._show_error("Simulation error", str(exc))
        finally:
            SIMULATION_SEMAPHORE.release()

    # ------------------------------------------------------------------
    # Analysis handling
    # ------------------------------------------------------------------

    def _refresh_targets(self) -> None:
        discover_root = self._get_repo_root()
        self.targets = find_combined_targets(discover_root)

        labels: List[str] = []
        base_dirs: List[str] = []
        for target in self.targets:
            base_dir = target[0]
            rel_label = str(base_dir.relative_to(discover_root))
            labels.append(rel_label)
            base_dirs.append(rel_label)

        self._set_combo_values(self.target_combo, labels)
        unique_base_dirs = sorted(dict.fromkeys(base_dirs))
        self._set_combo_values(self.fa_basedir_combo, unique_base_dirs)

        current_base = self._combo_text(self.fa_basedir_combo)
        if unique_base_dirs and current_base in ("", "."):
            self.fa_basedir_combo.setCurrentText(unique_base_dirs[0])
            self._on_basedir_change()

        if labels:
            if not self._combo_text(self.target_combo):
                self.target_combo.setCurrentText(labels[0])
            selected_label = self._combo_text(self.target_combo) or labels[0]
            for item in self.targets:
                rel = str(item[0].relative_to(discover_root))
                if rel == selected_label:
                    self._populate_argument_lists(item)
                    break
            else:
                self.target_combo.setCurrentText(labels[0])
                self._populate_argument_lists(self.targets[0])
        else:
            for listbox in (
                self.hist_pos_list,
                self.hist_opt_list,
                self.analysis_pos_list,
                self.analysis_j_list,
                self.analysis_include_list,
                self.analysis_exclude_list,
                self.analysis_misc_list,
            ):
                listbox.clear()
            hinted = self._default_base_for_scenario(self._combo_text(self.fa_scenario_combo))
            if hinted:
                self._set_combo_values(self.fa_basedir_combo, [hinted])
                self.fa_basedir_combo.setCurrentText(hinted)
            else:
                self._set_combo_values(self.fa_basedir_combo, [])
                self.fa_basedir_combo.setCurrentText(".")
        self._update_res_workspace_choices()

    def _get_repo_root(self):
        from manage_ase import REPO_ROOT

        return REPO_ROOT

    def _on_target_change(self, _event: object | None = None) -> None:
        label = self._combo_text(self.target_combo)
        if not label:
            return
        repo_root = self._get_repo_root()
        for item in self.targets:
            base_dir = item[0]
            rel = str(base_dir.relative_to(repo_root))
            if rel == label:
                self._populate_argument_lists(item)
                break

    def _on_basedir_change(self, _event: object | None = None) -> None:
        base_value = self._combo_text(self.fa_basedir_combo)
        if not base_value:
            return
        suggestion = self._suggest_scenario(base_value)
        current = self._combo_text(self.fa_scenario_combo)
        if not current or current in SCENARIO_OPTIONS:
            self.fa_scenario_combo.setCurrentText(suggestion)
        self._resolve_base_dir(self._combo_text(self.fa_scenario_combo), base_value, allow_update=True)
        self._update_res_workspace_choices()

    def _on_scenario_change(self, _event: object | None = None) -> None:
        scenario = self._combo_text(self.fa_scenario_combo)
        current_base = self._combo_text(self.fa_basedir_combo)
        _path, label = self._resolve_base_dir(scenario, current_base, allow_update=True)
        self.fa_basedir_combo.setCurrentText(label)
        self._update_res_workspace_choices()

    def _suggest_scenario(self, base_dir_label: str) -> str:
        label = base_dir_label.lower()
        if "plus80isr" in label:
            return "plus80ISR"
        if "minus80isr" in label:
            return "minus80ISR"
        if "plus80" in label:
            return "plus80"
        if "minus80" in label:
            return "minus80"
        if "isr" in label:
            return "ISR"
        return "default"

    def _default_base_for_scenario(self, scenario: str) -> Optional[str]:
        scenario_key = scenario.strip()
        base = SCENARIO_BASE_HINTS.get(scenario_key)
        if not base:
            return None
        repo_root = self._get_repo_root()
        if (repo_root / base).exists():
            return base
        return None

    def _resolve_base_dir(self, scenario: str, base_input: str, allow_update: bool = False) -> tuple[Path, str]:
        repo_root = self._get_repo_root()
        candidate = base_input.strip()
        label = candidate

        def normalize(path: Path) -> Path:
            return path.resolve()

        if candidate and candidate != ".":
            path = Path(candidate)
            if not path.is_absolute():
                path = repo_root / path
            path = normalize(path)
            if path.exists():
                return path, label or str(path.relative_to(repo_root))

        hinted = self._default_base_for_scenario(scenario)
        if hinted:
            path = normalize(repo_root / hinted)
            if path.exists():
                if allow_update:
                    self.fa_basedir_combo.setCurrentText(hinted)
                return path, hinted

        if candidate:
            fallback = Path(candidate)
            if not fallback.is_absolute():
                fallback = repo_root / fallback
            fallback = normalize(fallback)
        else:
            fallback = repo_root

        if allow_update and not candidate:
            self.fa_basedir_combo.setCurrentText(".")
        try:
            rel_label = str(fallback.relative_to(repo_root)) if fallback != repo_root else "."
        except ValueError:
            rel_label = str(fallback)
        return fallback, rel_label

    def _select_analysis_dir(self, scenario: str, base_input: str, mass: int) -> tuple[Path, str]:
        base_path, label = self._resolve_base_dir(scenario, base_input, allow_update=True)
        repo_root = self._get_repo_root()
        expected_name = f"Tt1M{mass}.root" if mass else ""
        expected_path = base_path / "root" / expected_name if expected_name else None

        if expected_path is None or expected_path.exists():
            return base_path, label

        hinted = self._default_base_for_scenario(scenario)
        if hinted:
            hinted_path = (repo_root / hinted).resolve()
            if (hinted_path / "root" / expected_name).exists():
                if label != hinted:
                    self._log(
                        f"[info] Switching analysis directory to '{hinted}' "
                        f"(found required {expected_name})."
                    )
                self.fa_basedir_combo.setCurrentText(hinted)
                return hinted_path, hinted

        if not expected_path.exists():
            self._log(
                f"[warning] Expected {expected_name} not found under '{label}'. "
                "Proceeding with the current directory; ROOT may fail if inputs are missing."
            )
        return base_path, label

    def _all_analysis_dirs(self) -> List[str]:
        repo_root = self._get_repo_root()
        dirs: set[str] = set()
        for target, *_ in self.targets:
            try:
                rel = str(target.relative_to(repo_root))
            except ValueError:
                rel = str(target)
            if rel.startswith("ttp_Analysis"):
                dirs.add(rel)
        for path in repo_root.glob("ttp_Analysis*"):
            if path.is_dir():
                dirs.add(str(path.relative_to(repo_root)))
        if (repo_root / "ttp_Analysis").exists():
            dirs.add("ttp_Analysis")
        return sorted(dirs)

    def _expand_run_directories(self, scenario: str, base_label: str) -> List[tuple[str, str]]:
        scenario = scenario.strip() or SCENARIO_OPTIONS[0]
        label = base_label.strip()
        repo_root = self._get_repo_root()

        def normalize(rel: str) -> Optional[str]:
            path = (repo_root / rel).resolve()
            if path.exists():
                try:
                    return str(path.relative_to(repo_root))
                except ValueError:
                    return str(path)
            return None

        if label and label not in AGGREGATE_BASE_LABELS:
            rel = normalize(label) or label
            scen = scenario or self._suggest_scenario(rel)
            return [(scen, rel)]

        dirs = self._all_analysis_dirs()
        plan: List[tuple[str, str]] = []
        for rel in dirs:
            scen = self._suggest_scenario(rel)
            if label not in AGGREGATE_BASE_LABELS and scenario and scenario in SCENARIO_OPTIONS and scenario != scen:
                continue
            if label in AGGREGATE_BASE_LABELS:
                plan.append((scen, rel))
            else:
                chosen = scenario or scen
                plan.append((chosen, rel))
        return plan

    def _discover_masses(self, base_path: Path) -> List[int]:
        masses: set[int] = set()
        root_dir = base_path / "root"
        if root_dir.exists():
            for file in root_dir.glob("Tt1M*.root"):
                stem = file.stem
                digits = "".join(ch for ch in stem if ch.isdigit())
                if digits:
                    try:
                        masses.add(int(digits))
                    except ValueError:
                        continue
        return sorted(masses)

    def _update_res_workspace_choices(self) -> None:
        scenario = self._combo_text(self.fa_scenario_combo)
        base_input = self._combo_text(self.fa_basedir_combo)
        mass_text = self._combo_text(self.fa_mass_combo)
        try:
            mass_value = int(mass_text)
        except ValueError:
            mass_value = 0
        base_path, label = self._select_analysis_dir(scenario, base_input, mass_value)
        repo_root = self._get_repo_root()

        candidates: List[str] = []
        if base_path.exists():
            for ws_file in sorted(base_path.glob("myWS*.root")):
                try:
                    path_str = str(ws_file.relative_to(repo_root))
                except ValueError:
                    path_str = str(ws_file)
                if path_str not in candidates:
                    candidates.append(path_str)

        current = self._combo_text(self.res_workspace_combo)
        if current and current not in candidates:
            candidates.append(current)

        self._set_combo_values(self.res_workspace_combo, candidates)

        existing = [self.fa_basedir_combo.itemText(i) for i in range(self.fa_basedir_combo.count())]
        if label and label not in existing:
            self.fa_basedir_combo.addItem(label)
        self.fa_basedir_combo.setCurrentText(label)

        if candidates:
            if not current or current not in candidates:
                self.res_workspace_combo.setCurrentText(candidates[0])
        else:
            self.res_workspace_combo.setCurrentText("")

    def _run_histograms_only(self) -> None:
        target = self._selected_target()
        if not target:
            return
        base_dir = target[0]
        hist_script = target[1]
        hist_args: List[str] = []
        for entry in self._selected_entries(self.hist_pos_list):
            hist_args.extend(shlex.split(entry))
        for entry in self._selected_entries(self.hist_opt_list):
            hist_args.extend(shlex.split(entry))

        self.run_hist_btn.setEnabled(False)
        threading.Thread(
            target=self._analysis_worker,
            args=(hist_script, base_dir, hist_args, self.run_hist_btn),
            daemon=True,
        ).start()

    def _run_analysis_only(self) -> None:
        target = self._selected_target()
        if not target:
            return
        base_dir = target[0]
        analysis_script = target[2]
        configs: List[str] = []
        for entry in self._selected_entries(self.analysis_pos_list):
            configs.extend(token for token in shlex.split(entry) if not token.startswith("-"))

        analysis_args: List[str] = []
        if configs:
            analysis_args.extend(["-c", ",".join(configs)])
        for entry in self._selected_entries(self.analysis_j_list):
            analysis_args.extend(shlex.split(entry))
        for entry in self._selected_entries(self.analysis_include_list):
            analysis_args.extend(shlex.split(entry))
        for entry in self._selected_entries(self.analysis_exclude_list):
            analysis_args.extend(shlex.split(entry))
        for entry in self._selected_entries(self.analysis_misc_list):
            analysis_args.extend(shlex.split(entry))

        self.run_analysis_btn.setEnabled(False)
        threading.Thread(
            target=self._analysis_worker,
            args=(analysis_script, base_dir, analysis_args, self.run_analysis_btn),
            daemon=True,
        ).start()

    def _run_combined_analysis(self) -> None:
        target = self._selected_target()
        if not target:
            return
        _base_dir = target[0]
        hist_script = target[1]
        analysis_script = target[2]

        hist_args: List[str] = []
        for entry in self._selected_entries(self.hist_pos_list):
            hist_args.extend(shlex.split(entry))
        for entry in self._selected_entries(self.hist_opt_list):
            hist_args.extend(shlex.split(entry))

        configs: List[str] = []
        for entry in self._selected_entries(self.analysis_pos_list):
            configs.extend(token for token in shlex.split(entry) if not token.startswith("-"))
        analysis_args: List[str] = []
        if configs:
            analysis_args.extend(["-c", ",".join(configs)])
        for entry in self._selected_entries(self.analysis_j_list):
            analysis_args.extend(shlex.split(entry))
        for entry in self._selected_entries(self.analysis_include_list):
            analysis_args.extend(shlex.split(entry))
        for entry in self._selected_entries(self.analysis_exclude_list):
            analysis_args.extend(shlex.split(entry))
        for entry in self._selected_entries(self.analysis_misc_list):
            analysis_args.extend(shlex.split(entry))

        self.run_pipeline_btn.setEnabled(False)

        def worker() -> None:
            try:
                run_shell_script(hist_script, hist_args, logger=self._log)
                run_shell_script(analysis_script, analysis_args, logger=self._log)
                self._log("[success] Analysis pipeline completed.")
            except Exception as exc:  # noqa: BLE001
                self._log(f"[error] {exc}")
                self._show_error("Analysis error", str(exc))
            finally:
                self._set_button_enabled(self.run_pipeline_btn, True)

        threading.Thread(target=worker, daemon=True).start()

    def _parse_float_entry(self, entry: QLineEdit, label: str, default: float) -> float:
        text = entry.text().strip()
        if not text:
            return default
        try:
            return float(text)
        except ValueError:
            self._show_error("Invalid input", f"{label} must be a numeric value.")
            raise

    def _run_resonance_finder(self) -> None:
        scenario = self._combo_text(self.fa_scenario_combo)
        mass_text = self._combo_text(self.fa_mass_combo)
        try:
            mass_value = int(mass_text)
        except ValueError:
            mass_value = 0

        base_path, _base_label = self._select_analysis_dir(scenario, self._combo_text(self.fa_basedir_combo), mass_value)
        repo_root = self._get_repo_root()
        ws_value = self._combo_text(self.res_workspace_combo)
        if not ws_value:
            self._show_error("Missing workspace", "Please select a workspace file to analyse.")
            return

        ws_path = Path(ws_value)
        if not ws_path.is_absolute():
            ws_path = (repo_root / ws_path).resolve()
        if not ws_path.exists() and base_path.exists():
            candidate = base_path / ws_value
            if candidate.exists():
                ws_path = candidate.resolve()
        if not ws_path.exists():
            self._show_error("Invalid workspace", f"Workspace file not found:\n{ws_path}")
            return

        try:
            ws_rel = str(ws_path.relative_to(repo_root))
        except ValueError:
            ws_rel = str(ws_path)

        ws_name = self.res_wsname_entry.text().strip() or "myWS"
        pdf_name = self.res_pdf_entry.text().strip() or "model"
        data_name = self.res_data_entry.text().strip() or "data"
        observable = self.res_obs_entry.text().strip() or "invMass"

        try:
            bin_width = self._parse_float_entry(self.res_binwidth_entry, "Bin width", 5.0)
            step_width = self._parse_float_entry(self.res_step_entry, "Step width", 5.0)
            min_width = self._parse_float_entry(self.res_min_entry, "Min window", 30.0)
            max_width = self._parse_float_entry(self.res_max_entry, "Max window", 150.0)
        except ValueError:
            return

        if bin_width <= 0.0:
            self._show_error("Invalid input", "Bin width must be positive.")
            return
        if step_width <= 0.0:
            self._show_error("Invalid input", "Step width must be positive.")
            return
        if max_width <= min_width:
            self._show_error("Invalid input", "Max window must be greater than min window.")
            return

        save_plots = bool(self.res_save_plots_check.isChecked())

        from manage_ase import ROOT_ENV_SCRIPT

        serialized_args = [
            json.dumps(ws_rel),
            json.dumps(ws_name),
            json.dumps(pdf_name),
            json.dumps(data_name),
            json.dumps(observable),
            json.dumps(bin_width),
            json.dumps(min_width),
            json.dumps(max_width),
            json.dumps(step_width),
            json.dumps(save_plots),
        ]
        macro_call = f"Analysis_Programs/find_resonance_agnostic.C+({','.join(serialized_args)})"
        command = f"source {shlex.quote(str(ROOT_ENV_SCRIPT))} >/dev/null 2>&1 && root -l -b -q '{macro_call}'"

        window_desc = f"[{min_width}, {max_width}] GeV @ bin={bin_width} GeV, step={step_width} GeV"
        self._log(f"[info] Running resonance finder for {ws_rel} ({window_desc})")
        self._run_root_process(command, self.run_resonance_btn, "Resonance finder", "Resonance error")

    def _launch_tbrowser(self) -> None:
        from manage_ase import ROOT_ENV_SCRIPT

        command = f"source {shlex.quote(str(ROOT_ENV_SCRIPT))} >/dev/null 2>&1 && root -l -e 'new TBrowser();'"
        self._log("[info] Launching ROOT TBrowser...")
        try:
            subprocess.Popen(["bash", "-lc", command])
        except Exception as exc:  # noqa: BLE001
            self._log(f"[error] Unable to launch TBrowser: {exc}")
            self._show_error("TBrowser error", str(exc))

    def _run_full_analysis_general(self) -> None:
        mass_text = self._combo_text(self.fa_mass_combo)
        if not mass_text:
            mass_input = None
        else:
            lowered = mass_text.lower()
            if lowered in {"*", "all"}:
                mass_input = None
            else:
                masses: List[int] = []
                parts = [part.strip() for part in mass_text.replace(";", ",").split(",") if part.strip()]
                if not parts:
                    mass_input = None
                else:
                    try:
                        for part in parts:
                            value = int(part)
                            if value <= 0:
                                raise ValueError
                            masses.append(value)
                    except ValueError:
                        self._show_error(
                            "Invalid mass",
                            "Mass must be an integer (or comma-separated list, or '*' for all available masses).",
                        )
                        return
                    mass_input = masses

        fallback_scenario = SCENARIO_OPTIONS[0] if SCENARIO_OPTIONS else "default"
        scenario = self._combo_text(self.fa_scenario_combo) or fallback_scenario

        override_text = self.fa_xsec_entry.text().strip()
        if override_text:
            try:
                override = float(override_text)
            except ValueError:
                self._show_error("Invalid cross section", "Override cross section must be numeric.")
                return
        else:
            override = -1.0

        extra_args_text = self.fa_extra_args_entry.text().strip()
        extra_args: List[Any] = []
        if extra_args_text:
            try:
                parsed = json.loads(extra_args_text)
            except json.JSONDecodeError as exc:
                self._show_error(
                    "Invalid extra arguments",
                    f"Could not parse extra arguments as JSON list:\n{exc}",
                )
                return
            if not isinstance(parsed, list):
                self._show_error(
                    "Invalid extra arguments",
                    "Extra arguments must be provided as a JSON list, for example: [\"tag\", true].",
                )
                return
            extra_args = parsed

        from manage_ase import ROOT_ENV_SCRIPT

        base_label_input = self._combo_text(self.fa_basedir_combo)
        expanded_dirs = self._expand_run_directories(scenario, base_label_input)
        if not expanded_dirs:
            self._show_error("No directories", "No analysis directories matched the current selection.")
            return

        repo_root = self._get_repo_root()
        run_plan: List[dict[str, str]] = []
        for scen_label, base_label in expanded_dirs:
            base_path, resolved_label = self._select_analysis_dir(scen_label, base_label, 0)
            if not base_path.exists():
                continue
            masses_to_run = mass_input if mass_input is not None else self._discover_masses(base_path)
            if not masses_to_run:
                self._log(
                    f"[warning] No signal masses found in {resolved_label}/root; skipping discovery for this directory."
                )
                continue
            for mass in masses_to_run:
                base_path_mass, resolved_label_mass = self._select_analysis_dir(scen_label, base_label, mass)
                if not (base_path_mass / "root" / f"Tt1M{mass}.root").exists():
                    self._log(
                        f"[warning] Missing root/Tt1M{mass}.root in {resolved_label_mass}; skipping this mass."
                    )
                    continue
                try:
                    base_dir_arg = str(base_path_mass.relative_to(repo_root))
                except ValueError:
                    base_dir_arg = str(base_path_mass)

                serialized_args = [
                    json.dumps(mass),
                    json.dumps(scen_label),
                    json.dumps(base_dir_arg),
                    json.dumps(override),
                ]
                serialized_args.extend(json.dumps(arg) for arg in extra_args)
                macro_call = f"Analysis_Programs/full_analysis_with_plot_general.C+({','.join(serialized_args)})"
                command = f"source {shlex.quote(str(ROOT_ENV_SCRIPT))} >/dev/null 2>&1 && root -l -b -q '{macro_call}'"
                extra_label = f", extra={extra_args}" if extra_args else ""
                context = f"Discovery macro [{resolved_label_mass}] (mass {mass})"
                self._log(
                    f"[info] Running discovery macro: mass={mass}, scenario={scen_label}, base={resolved_label_mass}{extra_label}"
                )
                run_plan.append(
                    {
                        "command": command,
                        "context": context,
                        "title": f"Discovery error ({resolved_label_mass}, mass {mass})",
                    }
                )

        if not run_plan:
            self._show_error(
                "No valid directories",
                "No analysis directories contained the expected ROOT files for the requested masses.",
            )
            return

        self._run_root_commands(run_plan, self.run_general_btn)

    def _run_root_process(
        self,
        command: str,
        button: QPushButton,
        context: str,
        error_title: Optional[str] = None,
    ) -> None:
        job = {"command": command, "context": context, "title": error_title or context}
        self._run_root_commands([job], button)

    def _run_root_commands(self, jobs: List[dict[str, str]], button: QPushButton) -> None:
        if not jobs:
            return
        button.setEnabled(False)

        def worker() -> None:
            for job in jobs:
                success = self._execute_root_command(job["command"], job["context"], job.get("title", job["context"]))
                if not success:
                    break
            self._set_button_enabled(button, True)

        threading.Thread(target=worker, daemon=True).start()

    def _execute_root_command(self, command: str, context: str, title: str) -> bool:
        from manage_ase import REPO_ROOT

        try:
            proc = subprocess.Popen(
                ["bash", "-lc", command],
                cwd=str(REPO_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            assert proc.stdout is not None
            line_count = 0
            tail_buffer: deque[str] = deque(maxlen=ROOT_LOG_TAIL)
            for line in proc.stdout:
                stripped = line.rstrip()
                if not stripped:
                    continue
                line_count += 1
                if line_count <= ROOT_LOG_HEAD:
                    self._log(f"[root] {stripped}")
                else:
                    tail_buffer.append(stripped)
            proc.stdout.close()
            returncode = proc.wait()

            if line_count > ROOT_LOG_HEAD:
                extra_lines = line_count - ROOT_LOG_HEAD
                tail_len = len(tail_buffer)
                skipped = max(0, extra_lines - tail_len)
                if skipped > 0:
                    self._log(
                        f"[info] ROOT output truncated; showing last {tail_len} lines ({skipped} additional lines omitted)."
                    )
                else:
                    self._log(
                        f"[info] ROOT output truncated; showing all {tail_len} lines beyond the first {ROOT_LOG_HEAD}."
                    )
                for entry in tail_buffer:
                    self._log(f"[root] {entry}")

            if returncode != 0:
                msg = f"{context} failed (exit {returncode})."
                self._log(f"[error] {msg}")
                self._show_error(title, msg)
                return False

            self._log(f"[success] {context} completed.")
            return True
        except Exception as exc:  # noqa: BLE001
            self._log(f"[error] {exc}")
            self._show_error(title, str(exc))
            return False

    def _selected_target(self):
        label = self._combo_text(self.target_combo)
        if not label:
            self._show_warning("Missing selection", "Please choose an analysis directory.")
            return None
        repo_root = self._get_repo_root()
        for item in self.targets:
            base_dir = item[0]
            rel = str(base_dir.relative_to(repo_root))
            if rel == label:
                return item
        self._show_warning(
            "Invalid selection",
            "Selected analysis directory is no longer available. Refresh targets.",
        )
        return None

    def _populate_argument_lists(self, target_tuple) -> None:
        (
            base_dir,
            _hist_script,
            _analysis_script,
            hist_pos,
            hist_opts,
            analysis_pos,
            analysis_j,
            analysis_include,
            analysis_exclude,
            analysis_misc,
        ) = target_tuple
        base_label = str(base_dir.relative_to(self._get_repo_root()))
        self.fa_basedir_combo.setCurrentText(base_label)
        self._on_basedir_change()
        self._fill_listbox(self.hist_pos_list, hist_pos)
        self._fill_listbox(self.hist_opt_list, hist_opts)
        self._fill_listbox(self.analysis_pos_list, analysis_pos)
        self._fill_listbox(self.analysis_j_list, analysis_j)
        self._fill_listbox(self.analysis_include_list, analysis_include)
        self._fill_listbox(self.analysis_exclude_list, analysis_exclude)
        self._fill_listbox(self.analysis_misc_list, analysis_misc)

    def _fill_listbox(self, listbox: QListWidget, values: List[str]) -> None:
        listbox.clear()
        for arg in dict.fromkeys(values):
            QListWidgetItem(arg, listbox)

    def _analysis_worker(self, script, base_dir, args, control_button: QPushButton):
        try:
            run_shell_script(script, args, logger=self._log)
            self._log(f"[success] {script.name} completed.")
        except Exception as exc:  # noqa: BLE001
            self._log(f"[error] {exc}")
            self._show_error("Analysis error", str(exc))
        finally:
            self._set_button_enabled(control_button, True)


def main() -> None:
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("ASE Manager")
    window = ManageASEGUI()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
