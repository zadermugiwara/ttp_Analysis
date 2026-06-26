#!/usr/bin/env python3
"""Interactive helper to run MadGraph workflows and ASE analyses.

This script orchestrates:
  * Collecting simulation parameters from the user
  * Preparing/maintaining MadGraph process directories
  * Launching MadGraph event generation
  * Organising resulting HEPMC files for downstream analyses
  * Updating `list_all_files_*` manifests used by existing analysis code
  * Running any `Analysis.sh` helper shipped with the repository

The goal is to provide a single friendly entry-point for the common
tasks described in the Codex request.
"""

from __future__ import annotations

import gzip
import csv
import os
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, List, Optional, Tuple

try:
    import curses
except Exception:  # noqa: BLE001 - Optional dependency for nicer UI
    curses = None

USE_CURSES = (
    curses is not None
    and sys.stdin.isatty()
    and sys.stdout.isatty()
    and os.environ.get("TERM") not in {None, "", "dumb"}
)


def _first_existing_path(*candidates: str | Path | None) -> Path:
    valid_candidates = [c for c in candidates if c]
    if not valid_candidates:
        raise ValueError("No path candidates provided.")
    for candidate in valid_candidates:
        path = Path(candidate).expanduser()
        if path.exists():
            return path
    return Path(valid_candidates[0]).expanduser()


def _resolve_env_script(
    env: dict[str, str],
    key: str,
    candidates: Iterable[str | Path | None],
    logger: Callable[[str], None] = print,
) -> Optional[Path]:
    tried: List[Path] = []

    raw = env.get(key)
    if raw:
        candidate = Path(raw).expanduser()
        tried.append(candidate)
        if candidate.exists():
            return candidate
        logger(f"[warn] {key} points to missing path: {candidate}")

    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        tried.append(path)
        if path.exists():
            return path

    if tried:
        logger(f"[warn] No valid {key} found. Tried: {', '.join(str(p) for p in tried)}")
    else:
        logger(f"[warn] {key} not provided and no fallback candidates supplied.")
    return None


def _python_for_root(root_setup: Path | None, logger: Callable[[str], None] = print) -> Optional[Path]:
    """Pick the Python interpreter matching the ROOT build, if available."""
    if not root_setup:
        return None
    root_setup = root_setup.expanduser()
    root_sys = root_setup.parent.parent  # .../root-xyz/bin/thisroot.sh -> root-xyz

    cfg = root_sys / "share" / "root" / "cmake" / "ROOTConfig.cmake"
    version: Optional[str] = None
    if cfg.exists():
        try:
            text = cfg.read_text()
            for line in text.splitlines():
                if "ROOT_PYTHON_VERSION" in line:
                    parts = line.replace("(", " ").replace(")", " ").split()
                    for token in parts:
                        if token.count(".") == 2 and token.replace(".", "").isdigit():
                            version = token
                            break
                    if version:
                        break
        except Exception:
            pass

    if version:
        py_name = f"python{version.rsplit('.', 1)[0]}"
        py_path = shutil.which(py_name)
        if py_path:
            return Path(py_path)
        logger(f"[warn] ROOT expects Python {version}, but {py_name} not found in PATH.")

    candidate = root_sys / "bin" / "python"
    if candidate.exists():
        return candidate
    return None


_STORAGE_ROOT_HINT = os.environ.get("ASE_STORAGE_ROOT")
_MADGRAPH_ROOT_HINT = os.environ.get("ASE_MADGRAPH_ROOT")
_HEPMC_ROOT_HINT = os.environ.get("ASE_HEPMC_ROOT")

REPO_ROOT = Path(__file__).resolve().parent
MADGRAPH_ROOT = _first_existing_path(
    _MADGRAPH_ROOT_HINT,
    Path(_STORAGE_ROOT_HINT) / "Madgraph" if _STORAGE_ROOT_HINT else None,
    "/media/higinio/Expansion/Madgraph",
    "/media/higinio/Expansion1/Madgraph",
)
HEPMC_ROOT = _first_existing_path(
    _HEPMC_ROOT_HINT,
    Path(_STORAGE_ROOT_HINT) / "Hepmcs" if _STORAGE_ROOT_HINT else None,
    "/media/higinio/Expansion/Hepmcs",
    "/media/higinio/Expansion1/Hepmcs",
)
_NEW_ROOT_ENV = REPO_ROOT / "Analysis/root/root-new/bin/thisroot.sh"
_OLD_ROOT_ENV = REPO_ROOT / "Analysis/root/root/bin/thisroot.sh"
ROOT_ENV_SCRIPT = _NEW_ROOT_ENV if _NEW_ROOT_ENV.exists() else _OLD_ROOT_ENV
WIDTH_TABLE_PATH = REPO_ROOT / "generation/widths.csv"
SMART_ANALYSIS_FILENAMES = ("smart_Analysis.sh", "smart_analysis.sh")
SMART_HISTOGRAM_FILENAMES = ("smart_Histograms.sh", "smart_histograms.sh")
DEFAULT_CONFIG_PRESETS = [
    "ideal",
    "ISR",
    "+80",
    "-80",
    "ISR+80",
    "ISR-80",
    "kappa010",
    "kappa015",
    "kappa020",
    "kappa025",
    "kappa030",
    "kappa035",
    "kappa040",
    "kappa045",
    "kappa050",
    "kappa055",
    "kappa060",
    "kappa065",
]


def gather_config_presets() -> List[str]:
    tokens = list(DEFAULT_CONFIG_PRESETS)
    seen = set(tokens)

    for path in sorted(REPO_ROOT.glob("ttp_Analysis*")):
        if not path.is_dir():
            continue
        name = path.name
        if name == "ttp_Analysis":
            token = "ideal"
        elif name.startswith("ttp_Analysis_"):
            token = name[len("ttp_Analysis_") :]
        else:
            token = name[len("ttp_Analysis") :]
        token = token.strip()
        if not token:
            continue
        if token not in seen:
            tokens.append(token)
            seen.add(token)
    return tokens


CONFIG_PRESETS = gather_config_presets()
DATASET_NAMES: List[str] = []


def discover_dataset_names(root: Path) -> List[str]:
    names: set[str] = set()
    for files_dir in root.glob("**/files/list_all_files_*"):
        if ".git" in files_dir.parts:
            continue
        suffix = files_dir.name.split("list_all_files_", 1)[-1]
        name = suffix.split(".", 1)[0]
        if name:
            names.add(name)
    return sorted(names)


DATASET_NAMES = discover_dataset_names(REPO_ROOT)

ANALYSIS_J_PRESETS = [f"-j {i}" for i in range(1, 11)]
ANALYSIS_INCLUDE_PRESETS = [f"--include '^{re.escape(name)}$'" for name in DATASET_NAMES]
ANALYSIS_EXCLUDE_PRESETS = [f"--exclude '^{re.escape(name)}$'" for name in DATASET_NAMES]
ANALYSIS_MISC_PRESETS = ["--histos"]
HISTOGRAM_OPTION_PRESETS: List[str] = []


def locate_heptools_paths() -> Tuple[Optional[Path], Optional[Path]]:
    heptools_lib = None
    pythia_lib = None
    opt_dir = REPO_ROOT / "HERWIG" / "opt"
    if opt_dir.exists():
        for candidate in sorted(opt_dir.glob("MG5_aMC_*"), reverse=True):
            lib_dir = candidate / "HEPTools" / "lib"
            py8_dir = candidate / "HEPTools" / "pythia8" / "lib"
            if lib_dir.exists() and heptools_lib is None:
                heptools_lib = lib_dir
            if py8_dir.exists() and pythia_lib is None:
                pythia_lib = py8_dir
            if heptools_lib and pythia_lib:
                break
    return heptools_lib, pythia_lib


HEPTOOLS_LIB_PATH, PYTHIA8_LIB_PATH = locate_heptools_paths()
# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class SimulationConfig:
    mass: int  # target TP mass (GeV)
    template_mass: int  # base template mass to copy from
    kappa: Optional[float]
    polarization: Optional[str]  # "+80", "-80", or None
    isr: bool
    nevents: int
    run_name: Optional[str]

    @property
    def kappa_code(self) -> Optional[str]:
        if self.kappa is None:
            return None
        return f"{int(round(self.kappa * 100)):03d}"

    @property
    def mass_label(self) -> str:
        return f"Tt1M{self.mass}"

    @property
    def process_dir_name(self) -> str:
        parts: List[str] = [f"Tt{self.mass}"]
        if self.kappa_code:
            parts.append(f"kappa{self.kappa_code}")
        if self.polarization:
            parts.append(self.polarization)
        if self.isr:
            parts.append("ISR")
        return "".join(parts)

    @property
    def analysis_dir_name(self) -> str:
        suffix = ""
        if self.kappa_code:
            suffix += f"_kappa{self.kappa_code}"
        if self.polarization:
            suffix += self.polarization
        if self.isr:
            suffix += "ISR"
        return f"ttp_Analysis{suffix}"

    @property
    def hepmc_directory_name(self) -> str:
        if self.kappa_code:
            subname = f"kappa{self.kappa_code}"
            if self.polarization:
                subname += self.polarization
            if self.isr:
                subname += "ISR"
            return subname
        # Non-kappa runs follow the existing directory structure
        if self.isr and self.polarization:
            return f"ISR{self.polarization}"
        if self.isr:
            return "ISR"
        if self.polarization:
            return self.polarization
        return "Ideal"

    @property
    def hepmc_filename(self) -> str:
        return f"{self.mass_label}.hepmc"


# ---------------------------------------------------------------------------
# Entry point & menus
# ---------------------------------------------------------------------------


def main() -> None:
    ensure_environment()
    while True:
        print("\n=== ASE workflow helper ===")
        choice = prompt_menu(
            "Select an action",
            [
                "Run MadGraph simulation",
                "Run analysis script",
                "Exit",
            ],
        )
        if choice == 0:
            run_simulation_flow()
        elif choice == 1:
            run_analysis_flow()
        else:
            print("Bye!")
            break


# ---------------------------------------------------------------------------
# Simulation flow
# ---------------------------------------------------------------------------


def run_simulation_flow() -> None:
    if not MADGRAPH_ROOT.exists():
        print(f"[error] MadGraph root not found: {MADGRAPH_ROOT}")
        return

    config = collect_simulation_config()
    if config is None:
        return

    if not confirm("\nReady to launch MadGraph. Proceed?", default=True):
        print("[info] Aborting at user request.")
        return

    try:
        hepmc_path = perform_simulation(config)
    except RuntimeError as exc:
        print(f"[error] {exc}")
        return
    except KeyboardInterrupt:
        print("\n[warn] Simulation interrupted by user.")
        return

    update_analysis_files(config, hepmc_path)
    print("\n[success] Workflow completed.")


def collect_simulation_config() -> Optional[SimulationConfig]:
    masses = discover_masses()
    if not masses:
        print(f"[error] No TtXXXX templates found in {MADGRAPH_ROOT}")
        return None

    print("\n--- Simulation parameters ---")
    mass_labels = [str(m) for m in masses] + ["Custom mass..."]
    mass_index = prompt_menu("Select TP mass (GeV)", mass_labels)
    custom_mass = mass_index == len(masses)

    if custom_mass:
        mass = prompt_positive_int("Enter desired TP mass (GeV)")
        template_idx = prompt_menu(
            "Select base template directory",
            [f"Tt{m}" for m in masses],
        )
        template_mass = masses[template_idx]
    else:
        mass = masses[mass_index]
        template_mass = mass

    kappa_value = prompt_float(
        "Enter kappa value (e.g. 0.20). Leave blank for none",
        allow_empty=True,
        min_value=0.0,
    )
    kappa = None if kappa_value == "" else float(kappa_value)

    pol_options = ["None", "+80", "-80"]
    pol_choice = prompt_menu("Select beam polarization", pol_options)
    polarization = None if pol_choice == 0 else pol_options[pol_choice]

    isr = confirm("Enable ISR?", default=False)

    while True:
        nevents_str = input("Number of simulations (events) [positive integer]: ").strip()
        if not nevents_str:
            print("  -> Please enter a positive integer.")
            continue
        if not nevents_str.isdigit():
            print("  -> Invalid number. Please use digits only.")
            continue
        nevents = int(nevents_str)
        if nevents <= 0:
            print("  -> Number must be greater than zero.")
            continue
        break

    run_name = input(
        "Optional MadGraph run name (leave blank for default run_0X): "
    ).strip() or None

    return SimulationConfig(
        mass=mass,
        template_mass=template_mass,
        kappa=kappa,
        polarization=polarization,
        isr=isr,
        nevents=nevents,
        run_name=run_name,
    )


def perform_simulation(
    config: SimulationConfig, logger: Callable[[str], None] = print
) -> Path:
    process_path = MADGRAPH_ROOT / config.process_dir_name
    template_dir = MADGRAPH_ROOT / f"Tt{config.template_mass}"

    logger(f"[info] Using process directory: {process_path}")
    if not process_path.exists():
        if not template_dir.exists():
            raise RuntimeError(f"Base template {template_dir} not found. Cannot continue.")
        logger(f"[info] Creating process directory from base template Tt{config.template_mass}...")
        copy_process_template(template_dir, process_path)
        clean_generated_outputs(process_path)
    else:
        logger("[info] Reusing existing process directory (parameters will be refreshed).")

    try:
        update_run_card(process_path, config)
        update_param_card(process_path, config)
        ensure_pythia8_settings(process_path, config)
        update_pythia8_cmd_files(process_path, config)
    except RuntimeError as exc:
        raise RuntimeError(f"Failed to update MadGraph cards: {exc}") from exc

    if not launch_madgraph(process_path, config, logger=logger):
        raise RuntimeError("MadGraph run failed or was interrupted.")

    # MadGraph rewrites the Pythia cards during generation, so enforce again.
    update_pythia8_cmd_files(process_path, config)

    run_pythia_shower(process_path, logger=logger)

    hepmc_path = handle_hepmc_output(process_path, config, logger=logger)
    return hepmc_path


def discover_masses() -> List[int]:
    masses = set()
    pattern = re.compile(r"^Tt(\d+)\b")
    try:
        for item in MADGRAPH_ROOT.iterdir():
            match = pattern.match(item.name)
            if match and item.is_dir():
                masses.add(int(match.group(1)))
    except OSError as exc:
        print(f"[warn] Could not scan {MADGRAPH_ROOT} ({exc}). Continuing with empty mass list.")
    return sorted(masses)


def copy_process_template(template_dir: Path, target_dir: Path) -> None:
    try:
        shutil.copytree(template_dir, target_dir)
    except Exception as exc:  # noqa: BLE001 - surfaced to caller
        raise RuntimeError(f"Failed to copy template: {exc}") from exc


def clean_generated_outputs(process_dir: Path) -> None:
    """Remove leftover run artefacts from freshly copied templates."""
    for relative in ("Events", "HTML"):
        target = process_dir / relative
        if not target.exists():
            continue
        for item in target.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            except Exception:  # noqa: BLE001 - best effort cleanup
                pass


def update_run_card(process_dir: Path, config: SimulationConfig) -> None:
    run_card = process_dir / "Cards" / "run_card.dat"
    if not run_card.exists():
        raise RuntimeError(f"run_card not found: {run_card}")

    content = run_card.read_text()

    # Update numeric settings
    replacements = {
        "nevents": str(config.nevents),
        "polbeam1": "0.0",
        "polbeam2": config.polarization.replace("+", "") if config.polarization else "0.0",
    }

    if config.isr:
        replacements.update(
            {
                "lpp1": "-3",
                "lpp2": "3",
                "lhaid": "0",
            }
        )
        pdf_value = "clic3000ll"
        pdf_keys = ["pdlabel", "pdlabel1", "pdlabel2"]
    else:
        replacements.update(
            {
                "lpp1": "0",
                "lpp2": "0",
                "lhaid": "230000",
            }
        )
        pdf_value = "nn23lo1"
        pdf_keys = ["pdlabel"]

    for key in pdf_keys:
        replacements[key] = pdf_value

    for key, value in replacements.items():
        content = replace_setting_line(content, key, value)

    run_card.write_text(content)


def replace_setting_line(content: str, key: str, value: str) -> str:
    pattern = re.compile(
        rf"(?m)^(?P<prefix>\s*)(?P<oldval>[^#=\n]+?)\s*=\s*{re.escape(key)}\b(?P<suffix>.*)$"
    )
    if pattern.search(content):
        return pattern.sub(
            lambda m: f"{m.group('prefix')}{value} = {key}{m.group('suffix')}", content, count=1
        )

    # If the key is missing, append a new line near the section header.
    insertion_line = f"  {value} = {key}\n"
    section_match = re.search(r"(?m)^#\*+.*PDF.*$", content)
    if section_match:
        idx = section_match.end()
        return content[:idx] + "\n" + insertion_line + content[idx:]

    return content + "\n" + insertion_line


def update_param_card(process_dir: Path, config: SimulationConfig) -> None:
    param_card = process_dir / "Cards" / "param_card.dat"
    if not param_card.exists():
        raise RuntimeError(f"param_card not found: {param_card}")

    content = param_card.read_text()
    # Update mass of TP
    mass_pattern = re.compile(
        r"(?m)^(?P<prefix>\s*6000006\s+)(?P<value>[-+0-9.eEdD]+)(?P<suffix>\s+#\s*MTP.*)$"
    )
    new_mass = f"{config.mass:.6e}"
    if mass_pattern.search(content):
        content = mass_pattern.sub(
            lambda m: f"{m.group('prefix')}{new_mass}{m.group('suffix')}", content, count=1
        )
    else:
        raise RuntimeError("Could not locate MTP entry (PDG 6000006) in param_card.")

    if config.kappa is not None:
        kappa_pattern = re.compile(
            r"(?m)^(?P<prefix>\s*2\s+)(?P<value>[-+0-9.eEdD]+)(?P<suffix>\s+#\s*KT.*)$"
        )
        new_kappa = f"{config.kappa:.6e}"
        if kappa_pattern.search(content):
            content = kappa_pattern.sub(
                lambda m: f"{m.group('prefix')}{new_kappa}{m.group('suffix')}",
                content,
                count=1,
            )
        else:
            raise RuntimeError("Could not locate KT entry in kappa block.")

    width = lookup_width(config.mass, config.kappa if config.kappa is not None else 0.20)
    if width is not None:
        width_pattern = re.compile(
            r"(?m)^(?P<prefix>\s*DECAY\s+6000006\s+)(?P<value>[-+0-9.eEdD]+)(?P<suffix>.*)$"
        )
        new_width = f"{width:.6e}"
        if width_pattern.search(content):
            content = width_pattern.sub(
                lambda m: f"{m.group('prefix')}{new_width}{m.group('suffix')}",
                content,
                count=1,
            )

    param_card.write_text(content)


def lookup_width(mass: int, kappa: float) -> Optional[float]:
    """Return the simulated width for an exact mass/kappa benchmark."""
    if not WIDTH_TABLE_PATH.exists():
        return None
    with WIDTH_TABLE_PATH.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            try:
                row_mass = int(row["mass_GeV"])
                row_kappa = float(row["kappa"])
                row_width = float(row["width_GeV"])
            except (KeyError, TypeError, ValueError):
                continue
            if row_mass == mass and abs(row_kappa - kappa) < 1e-9:
                return row_width
    return None


def ensure_pythia8_settings(process_dir: Path, config: SimulationConfig) -> None:
    """Make sure ISR-dependent settings are present in the Pythia8 card."""
    if not config.isr:
        return

    card_path = process_dir / "Cards" / "pythia8_card.dat"
    if not card_path.exists():
        raise RuntimeError(f"pythia8_card not found: {card_path}")

    desired = {
        "SpaceShower:QEDshowerByL": "on",
        "TimeShower:QEDshowerByL": "on",
        "SpaceShower:pTminChgL": "0.1",
        "PDF:lepton": "on",
    }

    lines = card_path.read_text().splitlines()
    patterns = {key: re.compile(rf"^\s*{re.escape(key)}\s*=") for key in desired}
    seen = set()
    updated_lines: List[str] = []

    for line in lines:
        stripped = line.lstrip()
        replaced = False
        for key, pattern in patterns.items():
            if pattern.match(stripped):
                updated_lines.append(f"{key} = {desired[key]}")
                seen.add(key)
                replaced = True
                break
        if not replaced:
            updated_lines.append(line)

    for key, value in desired.items():
        if key not in seen:
            updated_lines.append(f"{key} = {value}")

    card_path.write_text("\n".join(updated_lines) + "\n")


def update_pythia8_cmd_files(process_dir: Path, config: SimulationConfig) -> None:
    desired_events = max(config.nevents, 1)
    pattern = re.compile(r"(?m)(^\s*Main:numberOfEvents\s*=\s*)(-?\d+)(\s*$)")

    for cmd_path in process_dir.glob("Events/**/tag_1_pythia8.cmd"):
        try:
            text = cmd_path.read_text()
        except FileNotFoundError:
            continue

        # Drop legacy shell instructions that recent Pythia versions reject.
        filtered_lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("unset ") or "MG5aMC_PY8_interface" in stripped:
                continue
            filtered_lines.append(line)
        text = "\n".join(filtered_lines)

        if not pattern.search(text):
            continue

        replaced = pattern.sub(
            lambda m: f"{m.group(1)}{desired_events}{m.group(3)}",
            text,
            count=1,
        )

        if replaced != text:
            cmd_path.write_text(replaced + "\n")


def launch_madgraph(
    process_dir: Path, config: SimulationConfig, logger: Callable[[str], None] = print
) -> bool:
    cmd = ["./bin/generate_events", "-f"]
    if config.run_name:
        cmd.insert(1, config.run_name)
    logger(f"[info] Launching {' '.join(cmd)} in {process_dir}")
    try:
        completed = subprocess.run(
            cmd,
            cwd=process_dir,
            check=False,
        )
    except KeyboardInterrupt:
        return False

    if completed.returncode != 0:
        logger(f"[error] MadGraph exited with code {completed.returncode}")
        return False
    logger("[info] MadGraph event generation finished.")
    return True


def run_pythia_shower(process_dir: Path, logger: Callable[[str], None] = print) -> None:
    scripts = sorted(process_dir.glob("Events/**/run_shower.sh"))
    if not scripts:
        raise RuntimeError("No run_shower.sh scripts found; cannot produce HEPMC output.")

    executed_any = False
    for script in scripts:
        cmd_card = script.parent / "tag_1_pythia8.cmd"
        targets = expected_hepmc_paths(cmd_card)
        already_present = targets and all(target.exists() for target in targets)

        if already_present:
            logger(
                f"[info] Skipping Pythia8 shower {script.relative_to(process_dir)} (HEPMC already present)."
            )
            continue

        logger(f"[info] Running Pythia8 shower via {script.relative_to(process_dir)}")
        command = f"cd {shlex.quote(str(script.parent))} && ./run_shower.sh"
        env = os.environ.copy()
        ld_paths = []
        if HEPTOOLS_LIB_PATH:
            ld_paths.append(str(HEPTOOLS_LIB_PATH))
        if PYTHIA8_LIB_PATH:
            ld_paths.append(str(PYTHIA8_LIB_PATH))
        existing = env.get("LD_LIBRARY_PATH")
        if existing:
            ld_paths.append(existing)
        if ld_paths:
            env["LD_LIBRARY_PATH"] = ":".join(filter(None, ld_paths))
        try:
            subprocess.run(
                ["bash", "-lc", command],
                cwd=process_dir,
                check=True,
                env=env,
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                f"Pythia8 shower failed (exit code {exc.returncode}) for {script}"
            ) from exc
        executed_any = True

    if not executed_any:
        logger("[info] Pythia8 showers already up to date.")


def expected_hepmc_paths(cmd_path: Path) -> List[Path]:
    default = [cmd_path.parent / "tag_1_pythia8_events.hepmc"]
    try:
        text = cmd_path.read_text()
    except FileNotFoundError:
        return default

    match = re.search(r"HEPMCoutput:file\s*=\s*([^\s]+)", text)
    if not match:
        return default

    raw = match.group(1).strip().strip('"').strip("'")
    if not raw:
        return default

    base_dir = cmd_path.parent

    if raw in {"hepmc", "hepmc.gz"}:
        suffix = ".hepmc.gz" if raw.endswith(".gz") else ".hepmc"
        return [base_dir / f"tag_1_pythia8_events{suffix}"]

    if raw.startswith("hepmc@"):
        dest = raw.split("@", 1)[1]
        if not dest:
            return default
        path = Path(dest)
        return [path if path.is_absolute() else base_dir / path]

    if raw in {"hepmcremove", "/dev/null"} or raw.startswith("fifo"):
        return []

    path = Path(raw)
    if not path.is_absolute():
        path = base_dir / path
    return [path]


def handle_hepmc_output(
    process_dir: Path, config: SimulationConfig, logger: Callable[[str], None] = print
) -> Path:
    hepmc_candidates = sorted(
        process_dir.glob("Events/**/*.hepmc*"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not hepmc_candidates:
        raise RuntimeError("No HEPMC file produced by MadGraph.")

    src = hepmc_candidates[0]
    target_dir = HEPMC_ROOT / config.hepmc_directory_name
    target_dir.mkdir(parents=True, exist_ok=True)
    dest = target_dir / config.hepmc_filename

    if dest.exists():
        logger(f"[warn] Existing HEPMC file will be replaced: {dest}")

    if src.suffix == ".gz":
        with gzip.open(src, "rb") as src_file, open(dest, "wb") as dest_file:
            shutil.copyfileobj(src_file, dest_file)
    else:
        shutil.move(src, dest)

    logger(f"[info] HEPMC stored at {dest}")
    return dest


def update_analysis_files(
    config: SimulationConfig,
    hepmc_path: Path,
    logger: Callable[[str], None] = print,
) -> None:
    analysis_dir = REPO_ROOT / config.analysis_dir_name
    files_dir = analysis_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    list_file = files_dir / f"list_all_files_{config.mass_label}"
    list_file.write_text(str(hepmc_path) + "\n")
    logger(f"[info] Updated analysis list: {list_file}")


# ---------------------------------------------------------------------------
# Analysis flow
# ---------------------------------------------------------------------------


def run_analysis_flow() -> None:
    while True:
        action = prompt_menu(
            "Analysis options",
            [
                "Run smart_Histograms.sh + smart_Analysis.sh pipeline",
                "Run smart_Analysis.sh directly",
                "Back",
            ],
        )
        if action == 0:
            run_combined_analysis()
        elif action == 1:
            run_analysis_sh_script()
        else:
            return


def run_analysis_sh_script() -> None:
    scripts = find_analysis_scripts(REPO_ROOT)
    if not scripts:
        print("[error] No smart_Analysis.sh scripts found.")
        return

    print("\n--- Available analysis scripts ---")
    labels = [str(script.relative_to(REPO_ROOT)) for script in scripts]
    index = prompt_menu("Select script to run", labels)
    script_path = scripts[index]

    positional_presets = CONFIG_PRESETS.copy()
    configs: List[str] = []
    for entry in prompt_presets("smart_Analysis positional", positional_presets):
        configs.extend(token for token in shlex.split(entry) if not token.startswith("-"))

    arg_tokens: List[str] = []
    if configs:
        arg_tokens.extend(["-c", ",".join(configs)])
    for entry in prompt_presets("smart_Analysis -j", ANALYSIS_J_PRESETS):
        arg_tokens.extend(shlex.split(entry))
    for entry in prompt_presets("smart_Analysis --include", ANALYSIS_INCLUDE_PRESETS):
        arg_tokens.extend(shlex.split(entry))
    for entry in prompt_presets("smart_Analysis --exclude", ANALYSIS_EXCLUDE_PRESETS):
        arg_tokens.extend(shlex.split(entry))
    for entry in prompt_presets("smart_Analysis misc", ANALYSIS_MISC_PRESETS):
        arg_tokens.extend(shlex.split(entry))

    try:
        run_shell_script(script_path, arg_tokens, logger=print)
        print("[success] Analysis script completed.")
    except subprocess.CalledProcessError as exc:
        print(f"[error] Analysis script failed with exit code {exc.returncode}")
    except RuntimeError as exc:
        print(f"[error] {exc}")


def run_shell_script(
    script_path: Path,
    args: List[str],
    logger: Callable[[str], None] = print,
) -> None:
    script_path = script_path.resolve()
    if not script_path.exists():
        raise RuntimeError(f"Script not found: {script_path}")

    env = os.environ.copy()

    base_repo = REPO_ROOT
    # If the script lives under a nested tool directory (e.g. Analysis_Programs),
    # prefer that location as the ASE_DIR root.
    try:
        if script_path.parent.name == "Analysis_Programs":
            base_repo = script_path.parent.parent
    except Exception:
        pass

    env.setdefault("ASE_DIR", str(base_repo))
    env.setdefault("PROG_DIR", str(base_repo / "Analysis_Programs"))
    env.setdefault("ANALYZER", str(Path(env["PROG_DIR"]) / "ttp_Analysis"))
    env.setdefault("PY_HISTO", str(Path(env["PROG_DIR"]) / "Histograms.py"))

    herwig_env = _resolve_env_script(
        env,
        "HERWIG_ENV",
        [
            base_repo / "HERWIG/bin/activate",
            script_path.parent.parent / "HERWIG/bin/activate",
            Path(_STORAGE_ROOT_HINT) / "HERWIG/bin/activate" if _STORAGE_ROOT_HINT else None,
        ],
        logger=logger,
    )
    root_setup = _resolve_env_script(
        env,
        "ROOT_SETUP",
        [
            ROOT_ENV_SCRIPT,
            base_repo / "Analysis/root/root/bin/thisroot.sh",
            script_path.parent.parent / "Analysis/root/root/bin/thisroot.sh",
            Path(_STORAGE_ROOT_HINT) / "Analysis/root/root/bin/thisroot.sh" if _STORAGE_ROOT_HINT else None,
        ],
        logger=logger,
    )

    if herwig_env:
        env["HERWIG_ENV"] = str(herwig_env)
    else:
        env.pop("HERWIG_ENV", None)
    if root_setup:
        env["ROOT_SETUP"] = str(root_setup)
    else:
        env.pop("ROOT_SETUP", None)

    # Prefer the ROOT-provided python binary when available to avoid ABI mismatches.
    if not env.get("PYTHON_BIN"):
        root_python = _python_for_root(root_setup, logger=logger)
        if root_python:
            env["PYTHON_BIN"] = str(root_python)

    prolog: List[str] = []
    if herwig_env:
        prolog.append(f"source {shlex.quote(str(herwig_env))}")
    if root_setup:
        prolog.append(f"source {shlex.quote(str(root_setup))}")

    script_call = " ".join(shlex.quote(part) for part in [f"./{script_path.name}", *args])
    shell_cmd = " && ".join([*prolog, f"exec {script_call}"]) if prolog else f"exec {script_call}"
    cmd = ["bash", "-lc", shell_cmd]
    logger(f"[info] Running {' '.join(shlex.quote(part) for part in cmd)} in {script_path.parent}")
    subprocess.run(cmd, cwd=script_path.parent, check=True, env=env)


def prompt_presets(label: str, presets: List[str]) -> List[str]:
    if not presets:
        return []
    print(f"\nAvailable {label} presets:")
    for idx, option in enumerate(presets, 1):
        print(f"  {idx}) {option}")
    raw = input(f"Select {label} preset indices (space/comma separated, blank for none): ").strip()
    if not raw:
        return []
    selections = re.split(r"[\s,]+", raw.strip())
    entries: List[str] = []
    for sel in selections:
        if not sel:
            continue
        if not sel.isdigit():
            print(f"  -> Ignoring invalid selection '{sel}'")
            continue
        idx = int(sel) - 1
        if 0 <= idx < len(presets):
            entries.append(presets[idx])
        else:
            print(f"  -> Index {sel} out of range")
    return entries


def run_combined_analysis() -> None:
    targets = find_combined_targets(REPO_ROOT)
    if not targets:
        print("[error] No directories containing smart_Histograms.sh and smart_Analysis.sh were found.")
        return

    labels = [str(path.relative_to(REPO_ROOT)) for path, *_ in targets]
    idx = prompt_menu("Select analysis directory", labels)
    (
        base_dir,
        hist_script,
        analysis_script,
        hist_pos,
        hist_opts,
        analysis_pos,
        analysis_j,
        analysis_include,
        analysis_exclude,
        analysis_misc,
    ) = targets[idx]

    hist_args: List[str] = []
    for entry in prompt_presets("smart_Histograms positional", hist_pos):
        hist_args.extend(shlex.split(entry))
    for entry in prompt_presets("smart_Histograms options", hist_opts):
        hist_args.extend(shlex.split(entry))

    try:
        run_shell_script(hist_script, hist_args)
    except subprocess.CalledProcessError as exc:
        print(f"[error] smart_Histograms.sh failed with exit code {exc.returncode}")
        return
    except RuntimeError as exc:
        print(f"[error] {exc}")
        return

    configs: List[str] = []
    for entry in prompt_presets("smart_Analysis positional", analysis_pos):
        configs.extend(token for token in shlex.split(entry) if not token.startswith("-"))

    analysis_args: List[str] = []
    if configs:
        analysis_args.extend(["-c", ",".join(configs)])

    for entry in prompt_presets("smart_Analysis -j", analysis_j):
        analysis_args.extend(shlex.split(entry))
    for entry in prompt_presets("smart_Analysis --include", analysis_include):
        analysis_args.extend(shlex.split(entry))
    for entry in prompt_presets("smart_Analysis --exclude", analysis_exclude):
        analysis_args.extend(shlex.split(entry))
    for entry in prompt_presets("smart_Analysis misc", analysis_misc):
        analysis_args.extend(shlex.split(entry))

    try:
        run_shell_script(analysis_script, analysis_args)
    except subprocess.CalledProcessError as exc:
        print(f"[error] smart_Analysis.sh failed with exit code {exc.returncode}")
        return
    except RuntimeError as exc:
        print(f"[error] {exc}")
        return

    print("[success] Combined analysis finished.")


def find_analysis_scripts(root: Path) -> List[Path]:
    scripts = set()
    for name in SMART_ANALYSIS_FILENAMES:
        for path in root.glob(f"**/{name}"):
            if path.is_file() and ".git" not in path.parts:
                scripts.add(path)
    return sorted(scripts, key=lambda p: str(p))


def find_combined_targets(
    root: Path,
) -> List[Tuple[Path, Path, Path, List[str], List[str], List[str], List[str], List[str], List[str]]]:
    combos: dict[Path, List[Optional[Path]]] = {}

    for name in SMART_HISTOGRAM_FILENAMES:
        for hist_path in root.glob(f"**/{name}"):
            base_dir = hist_path.parent
            if ".git" in base_dir.parts or not hist_path.is_file():
                continue
            entry = combos.setdefault(base_dir, [None, None])
            if entry[0] is None:
                entry[0] = hist_path

    for name in SMART_ANALYSIS_FILENAMES:
        for analysis_path in root.glob(f"**/{name}"):
            base_dir = analysis_path.parent
            if ".git" in base_dir.parts or not analysis_path.is_file():
                continue
            entry = combos.setdefault(base_dir, [None, None])
            if entry[1] is None:
                entry[1] = analysis_path

    targets: List[
        Tuple[
            Path,
            Path,
            Path,
            List[str],
            List[str],
            List[str],
            List[str],
            List[str],
            List[str],
        ]
    ] = []
    for base_dir, (hist_path, analysis_path) in combos.items():
        if hist_path and analysis_path:
            hist_pos = CONFIG_PRESETS.copy()
            hist_opts: List[str] = []
            analysis_pos = CONFIG_PRESETS.copy()
            targets.append(
                (
                    base_dir,
                    hist_path,
            analysis_path,
            hist_pos,
            hist_opts,
            CONFIG_PRESETS.copy(),
            ANALYSIS_J_PRESETS,
            ANALYSIS_INCLUDE_PRESETS,
            ANALYSIS_EXCLUDE_PRESETS,
            ANALYSIS_MISC_PRESETS,
                )
            )

    return sorted(targets, key=lambda tup: str(tup[0]))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def ensure_environment() -> None:
    missing = []
    for path in (MADGRAPH_ROOT, HEPMC_ROOT):
        if not path.exists():
            missing.append(str(path))
    if missing:
        print("[warning] The following paths do not currently exist:")
        for item in missing:
            print(f"  - {item}")
        print("The script will attempt to create directories when required.\n")


def prompt_menu(title: str, options: Iterable[str], initial: int = 0) -> int:
    global USE_CURSES
    opts = list(options)
    if not opts:
        raise ValueError("Options must not be empty")
    initial = max(0, min(initial, len(opts) - 1))
    if USE_CURSES:
        try:
            return _curses_menu(title, opts, initial)
        except Exception:
            # If curses fails mid-run, disable it and fall back to textual menu.
            USE_CURSES = False

    while True:
        print(f"\n{title}:")
        for idx, opt in enumerate(opts, start=1):
            default_marker = " [default]" if idx - 1 == initial else ""
            print(f"  {idx}) {opt}{default_marker}")
        choice = input("Enter choice number: ").strip()
        if not choice:
            return initial
        if not choice.isdigit():
            print("  -> Please enter a number.")
            continue
        index = int(choice) - 1
        if not 0 <= index < len(opts):
            print("  -> Choice out of range.")
            continue
        return index


def _curses_menu(title: str, options: List[str], initial: int) -> int:
    result = {"index": initial}

    def draw_menu(stdscr: Any) -> None:
        curses.curs_set(0)
        stdscr.keypad(True)
        selected = initial
        while True:
            stdscr.clear()
            try:
                stdscr.addstr(0, 0, title, curses.A_BOLD)
            except curses.error:
                pass
            for idx, option in enumerate(options):
                attr = curses.A_REVERSE if idx == selected else curses.A_NORMAL
                label = f"[ {option} ]"
                try:
                    stdscr.addstr(idx + 2, 2, label, attr)
                except curses.error:
                    pass
            stdscr.refresh()
            key = stdscr.getch()
            if key in (curses.KEY_UP, ord("k")):
                selected = (selected - 1) % len(options)
            elif key in (curses.KEY_DOWN, ord("j")):
                selected = (selected + 1) % len(options)
            elif key in (curses.KEY_ENTER, 10, 13):
                result["index"] = selected
                break
            elif key in (27,):  # ESC key
                result["index"] = initial
                break

    curses.wrapper(draw_menu)
    print()
    return result["index"]


def confirm(prompt: str, default: bool = False) -> bool:
    if USE_CURSES:
        options = ["Yes", "No"]
        initial = 0 if default else 1
        choice = prompt_menu(prompt, options, initial=initial)
        return choice == 0

    suffix = " [Y/n]: " if default else " [y/N]: "
    while True:
        answer = input(prompt + suffix).strip().lower()
        if not answer:
            return default
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("  -> Please answer with y or n.")


def prompt_float(
    prompt: str, allow_empty: bool = False, min_value: Optional[float] = None
) -> str:
    while True:
        raw = input(prompt + ": ").strip()
        if not raw:
            if allow_empty:
                return ""
            print("  -> Value required.")
            continue
        try:
            value = float(raw)
        except ValueError:
            print("  -> Invalid float.")
            continue
        if min_value is not None and value < min_value:
            print(f"  -> Value must be at least {min_value}.")
            continue
        return raw


def prompt_positive_int(prompt: str) -> int:
    while True:
        raw = input(prompt + ": ").strip()
        if not raw:
            print("  -> Value required.")
            continue
        if not raw.isdigit():
            print("  -> Enter a positive integer.")
            continue
        value = int(raw)
        if value <= 0:
            print("  -> Value must be greater than zero.")
            continue
        return value


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(1)
