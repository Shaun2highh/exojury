"""Central configuration: leakage policy, feature groups, paths, seeds.

The KOI cumulative table mixes genuine observables with columns that are
*outputs of the human/robotic vetting process* — i.e. the answer key.
Every column in this dataset is assigned to exactly one tier below, so the
leakage policy is auditable rather than implicit.
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_dotenv() -> None:
    """Load KEY=value lines from .env into os.environ (no dependency)."""
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()
DATA_RAW = PROJECT_ROOT / "data_raw" / "KOI_Cumulative_clean.csv"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

SEED = 42
TARGET = "koi_disposition"

# ---------------------------------------------------------------------------
# Leakage tiers
# ---------------------------------------------------------------------------

# Row identifiers and documentation links. Useless as features.
IDENTIFIER_COLS = [
    "rowid",
    "kepid",
    "kepoi_name",
    "koi_datalink_dvr",
    "koi_datalink_dvs",
]

# Direct leakage: these columns *are* the disposition, restated.
#   - kepler_name exists only for CONFIRMED planets (99.9% separation)
#   - koi_pdisposition is the pipeline's own verdict (99.9% separation)
#   - koi_comment contains the vetting rationale codes in plain text
DIRECT_LEAKAGE_COLS = [
    "kepler_name",
    "koi_pdisposition",
    "koi_disp_prov",
    "koi_comment",
    "koi_vet_stat",
    "koi_vet_date",
]

# Vetting-derived flags: set by the Kepler Robovetter AFTER classification.
# Any flag set => FALSE POSITIVE with 99.6% precision. Most published
# student models include these and report inflated accuracy.
VETTING_FLAG_COLS = [
    "koi_fpflag_nt",
    "koi_fpflag_ss",
    "koi_fpflag_co",
    "koi_fpflag_ec",
]

# Columns that are 100% empty in this extract.
ALL_EMPTY_COLS = [
    "koi_eccen_err1", "koi_eccen_err2",
    "koi_longp", "koi_longp_err1", "koi_longp_err2",
    "koi_ingress", "koi_ingress_err1", "koi_ingress_err2",
    "koi_sma_err1", "koi_sma_err2",
    "koi_incl_err1", "koi_incl_err2",
    "koi_teq_err1", "koi_teq_err2",
    "koi_model_dof", "koi_model_chisq",
    "koi_sage", "koi_sage_err1", "koi_sage_err2",
]

# Low-information provenance/metadata strings (single value or fit bookkeeping).
METADATA_COLS = [
    "koi_limbdark_mod",
    "koi_trans_mod",
    "koi_parm_prov",
    "koi_sparprov",
    "koi_tce_delivname",
    "koi_fittype",
    "koi_quarters",  # replaced by engineered n_quarters
]

DROP_ALWAYS = IDENTIFIER_COLS + DIRECT_LEAKAGE_COLS + ALL_EMPTY_COLS + METADATA_COLS

LABEL_MAP_BINARY = {"FALSE POSITIVE": 0, "CONFIRMED": 1}
LABEL_MAP_3CLASS = {"FALSE POSITIVE": 0, "CANDIDATE": 1, "CONFIRMED": 2}
