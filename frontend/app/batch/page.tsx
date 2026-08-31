"use client";

import { useState } from "react";

export default function BatchPredictionPage() {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select a CSV file first.");
      return;
    }

    setMessage(`Selected: ${file.name}`);
  };

  return (
    <main style={{ maxWidth: "900px", margin: "50px auto", padding: "20px" }}>
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
          onChange={(e) => {
            const selectedFile = e.target.files?.[0] ?? null;
            setFile(selectedFile);
            setMessage("");
          }}
        />

        <div style={{ marginTop: "20px" }}>
          <button
            type="button"
            onClick={handleUpload}
            style={{
              padding: "10px 20px",
              cursor: "pointer",
              fontWeight: "bold",
            }}
          >
            Upload CSV
          </button>
        </div>

        {file && (
          <p style={{ marginTop: "20px" }}>
            Selected file: <strong>{file.name}</strong>
          </p>
        )}

        {message && <p style={{ marginTop: "15px" }}>{message}</p>}
      </div>
    </main>
  );
}
