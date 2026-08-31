"""Central configuration for the ML pipeline."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = ROOT_DIR / "data" / "raw" / "telco_churn_partial_ibm_source.csv"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
ARTIFACT_DIR = ROOT_DIR / "ml" / "artifacts"
REPORTS_DIR = ROOT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
RESULTS_DIR = REPORTS_DIR / "results"

RANDOM_STATE = 42
TEST_SIZE = 0.2
CV_FOLDS = 5

MODEL_ARTIFACT_PATH = ARTIFACT_DIR / "churn_pipeline.joblib"
METADATA_PATH = ARTIFACT_DIR / "metadata.json"

# NOTE ON DATASET PROVENANCE:
# The working file (telco_churn_partial_ibm_source.csv) is a 253-row
# subset of the full 7,043-row IBM Telco Customer Churn dataset
# (https://github.com/IBM/telco-customer-churn-on-icp4d), retrieved
# via automated fetch. The full file could not be retrieved in this
# environment (fixed response-size ceiling on the fetch tool). All
# metrics produced by this pipeline are real, computed values on that
# 253-row subset -- not fabricated -- but should be treated as a
# small-sample proof-of-concept, not a publication-grade result.
# Re-running with the full file (drop-in replacement, same schema) at
# RAW_DATA_PATH will make numbers immediately representative.

for _dir in (PROCESSED_DIR, ARTIFACT_DIR, FIGURES_DIR, RESULTS_DIR):
    _dir.mkdir(parents=True, exist_ok=True)
