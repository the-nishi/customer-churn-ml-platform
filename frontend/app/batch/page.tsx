"use client";

import { useState } from "react";

const REQUIRED_COLUMNS = [
  "customer_reference",
  "tenure",
  "gender",
  "senior_citizen",
  "partner",
  "dependents",
  "phone_service",
  "multiple_lines",
  "internet_service",
  "online_security",
  "online_backup",
  "device_protection",
  "tech_support",
  "streaming_tv",
  "streaming_movies",
  "contract",
  "paperless_billing",
  "payment_method",
  "monthly_charges",
  "total_charges",
];

type CustomerRow = {
  customer_reference: string;
  tenure: number;
  gender: string;
  senior_citizen: string;
  partner: string;
  dependents: string;
  phone_service: string;
  multiple_lines: string;
  internet_service: string;
  online_security: string;
  online_backup: string;
  device_protection: string;
  tech_support: string;
  streaming_tv: string;
  streaming_movies: string;
  contract: string;
  paperless_billing: string;
  payment_method: string;
  monthly_charges: number;
  total_charges: number;
};

function parseCSVLine(line: string): string[] {
  const values: string[] = [];
  let current = "";
  let insideQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];

    if (char === '"') {
      if (insideQuotes && line[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        insideQuotes = !insideQuotes;
      }
    } else if (char === "," && !insideQuotes) {
      values.push(current.trim());
      current = "";
    } else {
      current += char;
    }
  }

  values.push(current.trim());
  return values;
}

function chunkArray<T>(array: T[], size: number): T[][] {
  const chunks: T[][] = [];

  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }

  return chunks;
}

export default function BatchPredictionPage() {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select a CSV file first.");
      return;
    }

    const apiUrl = process.env.NEXT_PUBLIC_API_URL;

    if (!apiUrl) {
      setMessage("API URL is not configured.");
      return;
    }

    setUploading(true);
    setProgress(0);
    setMessage("Reading CSV file...");

    try {
      const text = await file.text();

      const lines = text
        .replace(/^\uFEFF/, "")
        .split(/\r?\n/)
        .filter((line) => line.trim() !== "");

      if (lines.length < 2) {
        throw new Error("CSV file does not contain customer data.");
      }

      const headers = parseCSVLine(lines[0]).map((h) => h.trim());

      const missingColumns = REQUIRED_COLUMNS.filter(
        (column) => !headers.includes(column)
      );

      if (missingColumns.length > 0) {
        throw new Error(
          `Missing columns: ${missingColumns.join(", ")}`
        );
      }

      const customers: CustomerRow[] = lines.slice(1).map((line, index) => {
        const values = parseCSVLine(line);

        if (values.length !== headers.length) {
          throw new Error(
            `Invalid CSV format at data row ${index + 2}.`
          );
        }

        const row: Record<string, string> = {};

        headers.forEach((header, i) => {
          row[header] = values[i];
        });

        const tenure = Number(row.tenure);
        const monthlyCharges = Number(row.monthly_charges);
        const totalCharges = Number(row.total_charges);

        if (
          Number.isNaN(tenure) ||
          Number.isNaN(monthlyCharges) ||
          Number.isNaN(totalCharges)
        ) {
          throw new Error(
            `Invalid numeric value at data row ${index + 2}.`
          );
        }

        return {
          customer_reference: row.customer_reference,
          tenure,
          gender: row.gender,
          senior_citizen: row.senior_citizen,
          partner: row.partner,
          dependents: row.dependents,
          phone_service: row.phone_service,
          multiple_lines: row.multiple_lines,
          internet_service: row.internet_service,
          online_security: row.online_security,
          online_backup: row.online_backup,
          device_protection: row.device_protection,
          tech_support: row.tech_support,
          streaming_tv: row.streaming_tv,
          streaming_movies: row.streaming_movies,
          contract: row.contract,
          paperless_billing: row.paperless_billing,
          payment_method: row.payment_method,
          monthly_charges: monthlyCharges,
          total_charges: totalCharges,
        };
      });

      if (customers.length === 0) {
        throw new Error("No customer records found.");
      }

      if (customers.length > 500) {
        throw new Error("Maximum 500 customers are allowed.");
      }

      setMessage(
        `${customers.length} customers found. Starting predictions...`
      );

      const batches = chunkArray(customers, 20);

      let completed = 0;
      let successCount = 0;
      let errorCount = 0;

      for (const batch of batches) {
        const response = await fetch(
          `${apiUrl.replace(/\/$/, "")}/predict-batch`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(batch),
          }
        );

        if (!response.ok) {
          const errorText = await response.text();

          throw new Error(
            `Backend error (${response.status}): ${errorText}`
          );
        }

        const data = await response.json();

        if (Array.isArray(data.results)) {
          data.results.forEach(
            (result: { error?: string }) => {
              if (result.error) {
                errorCount++;
              } else {
                successCount++;
              }
            }
          );
        } else {
          successCount += batch.length;
        }

        completed += batch.length;

        setProgress(
          Math.round((completed / customers.length) * 100)
        );

        setMessage(
          `Processing: ${completed} / ${customers.length} customers`
        );
      }

      setProgress(100);

      setMessage(
        `Completed! ${successCount} predictions successful` +
          (errorCount > 0
            ? `, ${errorCount} failed.`
            : ". Analytics can now be refreshed.")
      );
    } catch (error) {
      console.error(error);

      setMessage(
        error instanceof Error
          ? `Error: ${error.message}`
          : "Something went wrong."
      );
    } finally {
      setUploading(false);
    }
  };

  return (
    <main
      style={{
        maxWidth: "900px",
        margin: "50px auto",
        padding: "20px",
      }}
    >
      <h1>Batch Churn Prediction</h1>

      <p>
        Upload a CSV file containing multiple customer records for batch
        prediction.
      </p>

      <div
        style={{
          marginTop: "30px",
          padding: "30px",
          border: "2px dashed #999",
          borderRadius: "12px",
        }}
      >
        <h2>Upload Customer CSV</h2>

        <input
          type="file"
          accept=".csv,text/csv"
          disabled={uploading}
          onChange={(e) => {
            const selectedFile = e.target.files?.[0] ?? null;

            setFile(selectedFile);
            setMessage("");
            setProgress(0);
          }}
        />

        <div style={{ marginTop: "20px" }}>
          <button
            type="button"
            onClick={handleUpload}
            disabled={uploading}
            style={{
              padding: "10px 20px",
              cursor: uploading ? "not-allowed" : "pointer",
              fontWeight: "bold",
            }}
          >
            {uploading ? "Processing..." : "Upload CSV"}
          </button>
        </div>

        {file && (
          <p style={{ marginTop: "20px" }}>
            Selected file: <strong>{file.name}</strong>
          </p>
        )}

        {uploading && (
          <div style={{ marginTop: "20px" }}>
            <progress
              value={progress}
              max="100"
              style={{ width: "100%" }}
            />

            <p>{progress}% completed</p>
          </div>
        )}

        {message && (
          <p style={{ marginTop: "15px" }}>
            {message}
          </p>
        )}
      </div>
    </main>
  );
}
