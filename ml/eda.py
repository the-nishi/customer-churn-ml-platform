"""
eda.py
Exploratory data analysis for the Customer Churn dataset.
Produces summary statistics (printed + saved as JSON) and figures under
reports/figures/.
"""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from ml import config
from ml.preprocessing import clean_raw, load_raw

sns.set_theme(style="whitegrid")


def run_eda() -> dict:
    df = load_raw(str(config.RAW_DATA_PATH))
    findings: dict = {}

    findings["n_rows"] = int(len(df))
    findings["n_columns"] = int(df.shape[1])
    findings["duplicate_rows"] = int(df.duplicated().sum())
    findings["duplicate_customer_ids"] = int(df["customerID"].duplicated().sum())
    findings["missing_values_raw"] = df.isna().sum().to_dict()

    df = clean_raw(df)
    findings["missing_total_charges_after_coercion"] = int(df["TotalCharges"].isna().sum())

    churn_counts = df["Churn"].value_counts().to_dict()
    findings["churn_counts"] = {int(k): int(v) for k, v in churn_counts.items()}
    findings["churn_rate"] = round(float(df["Churn"].mean()), 4)

    # --- Figure 1: churn distribution ---
    fig, ax = plt.subplots(figsize=(5, 4))
    sns.countplot(x=df["Churn"].map({0: "No", 1: "Yes"}), ax=ax, hue=df["Churn"].map({0: "No", 1: "Yes"}), legend=False, palette=["#4C72B0", "#C44E52"])
    ax.set_title("Churn Distribution")
    ax.set_xlabel("Churn")
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / "01_churn_distribution.png", dpi=150)
    plt.close(fig)

    # --- Figure 2: tenure vs churn ---
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.histplot(data=df, x="tenure", hue=df["Churn"].map({0: "No", 1: "Yes"}), multiple="stack", bins=20, ax=ax)
    ax.set_title("Tenure Distribution by Churn")
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / "02_tenure_by_churn.png", dpi=150)
    plt.close(fig)

    # --- Figure 3: contract type vs churn rate ---
    contract_churn = df.groupby("Contract")["Churn"].mean().sort_values(ascending=False)
    findings["churn_rate_by_contract"] = contract_churn.round(4).to_dict()
    fig, ax = plt.subplots(figsize=(6, 4))
    contract_churn.plot(kind="bar", ax=ax, color="#DD8452")
    ax.set_ylabel("Churn Rate")
    ax.set_title("Churn Rate by Contract Type")
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / "03_churn_rate_by_contract.png", dpi=150)
    plt.close(fig)

    # --- Figure 4: monthly charges by churn ---
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.boxplot(data=df, x=df["Churn"].map({0: "No", 1: "Yes"}), y="MonthlyCharges", ax=ax)
    ax.set_title("Monthly Charges by Churn")
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / "04_monthly_charges_by_churn.png", dpi=150)
    plt.close(fig)

    # --- Figure 5: internet service vs churn rate ---
    internet_churn = df.groupby("InternetService")["Churn"].mean().sort_values(ascending=False)
    findings["churn_rate_by_internet_service"] = internet_churn.round(4).to_dict()
    fig, ax = plt.subplots(figsize=(6, 4))
    internet_churn.plot(kind="bar", ax=ax, color="#55A868")
    ax.set_ylabel("Churn Rate")
    ax.set_title("Churn Rate by Internet Service")
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / "05_churn_rate_by_internet.png", dpi=150)
    plt.close(fig)

    # --- Figure 6: payment method vs churn rate ---
    payment_churn = df.groupby("PaymentMethod")["Churn"].mean().sort_values(ascending=False)
    findings["churn_rate_by_payment_method"] = payment_churn.round(4).to_dict()
    fig, ax = plt.subplots(figsize=(7, 4))
    payment_churn.plot(kind="bar", ax=ax, color="#8172B2")
    ax.set_ylabel("Churn Rate")
    ax.set_title("Churn Rate by Payment Method")
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / "06_churn_rate_by_payment.png", dpi=150)
    plt.close(fig)

    with open(config.RESULTS_DIR / "eda_findings.json", "w") as f:
        json.dump(findings, f, indent=2, default=str)

    return findings


if __name__ == "__main__":
    results = run_eda()
    print(json.dumps(results, indent=2, default=str))
