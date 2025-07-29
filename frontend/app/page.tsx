"use client";

import { useState } from "react";
import styles from "./page.module.css";

export default function Home() {
  const [testBatch, setTestBatch] = useState("");
  const [endpoint, setEndpoint] = useState("http://localhost:8000");
  const [modelId, setModelId] = useState("meta-llama/Llama-3.3-70B-Instruct");
  const [attempts, setAttempts] = useState(1);
  const [testName, setTestName] = useState("main_evaluate_test");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  async function sendTest() {
    setLoading(true);
    setResponse("");

    try {
      const parsedTestBatch = JSON.parse(testBatch);

      const payload = {
        test_batch: parsedTestBatch,
        endpoint,
        model_id: modelId,
        attempts,
        test_name: testName,
      };

      const res = await fetch("/api/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        setResponse("Erreur : " + (data.detail || JSON.stringify(data)));
      } else {
        setResponse(JSON.stringify(data, null, 2));
      }
    } catch (err: any) {
      setResponse("Erreur : " + err.message);
    }

    setLoading(false);
  }

  return (
    <main className={styles.container}>
      <div className={styles.formWrapper}>
        <h1 className={styles.heading}> Évaluer un test</h1>

        <label className={styles.label}>Test Batch (JSON)</label>
        <textarea
          className={styles.textarea}
          placeholder="{ ... }"
          value={testBatch}
          onChange={(e) => setTestBatch(e.target.value)}
        />

        <label className={styles.label}>Endpoint</label>
        <input
          className={styles.input}
          type="text"
          value={endpoint}
          onChange={(e) => setEndpoint(e.target.value)}
        />

        <label className={styles.label}>Model ID</label>
        <input
          className={styles.input}
          type="text"
          value={modelId}
          onChange={(e) => setModelId(e.target.value)}
        />

        <label className={styles.label}>Attempts</label>
        <input
          className={styles.input}
          type="number"
          value={attempts}
          onChange={(e) => setAttempts(Number(e.target.value))}
        />

        <label className={styles.label}>Test Name</label>
        <input
          className={styles.input}
          type="text"
          value={testName}
          onChange={(e) => setTestName(e.target.value)}
        />

        <div style={{ textAlign: "center", margin: "1.5rem 0" }}>
          <button
            className={styles.button}
            onClick={sendTest}
            disabled={loading}
          >
            {loading ? "Chargement..." : " Envoyer le test"}
          </button>
        </div>

        <label className={styles.label}>Réponse</label>
        <pre className={styles.responseBox}>
          {response || "Aucune réponse encore..."}
        </pre>
      </div>
    </main>
  );
}
