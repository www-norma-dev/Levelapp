"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function EvaluatePage() {
  const [userMessage, setUserMessage] = useState("");
  const [agentReply, setAgentReply] = useState("");
  const [referenceReply, setReferenceReply] = useState("");
  const [interactionType, setInteractionType] = useState("opening");
  const [description, setDescription] = useState("Quick evaluation from UI");
  const [modelId, setModelId] = useState("meta-llama/Llama-3.3-70B-Instruct");

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    const payload = {
      test_batch: {
        id: crypto.randomUUID(),
        interactions: [
          {
            id: crypto.randomUUID(),
            user_message: userMessage,
            agent_reply: agentReply,
            reference_reply: referenceReply,
            interaction_type: interactionType,
            reference_metadata: {
              intent: "greeting",
              sentiment: "positive",
            },
            generated_metadata: {
              intent: "greeting",
              sentiment: "positive",
            },
          },
        ],
        description: description,
        details: {
          name: "Manual Test",
          version: "1.0",
        },
      },
      endpoint: "http://localhost:8000",
      model_id: modelId,
      attempts: 1,
      test_name: "manual_test",
    };

    try {
      const res = await fetch("http://localhost:8080/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      setResult(JSON.stringify(data, null, 2));
    } catch (error) {
      console.error(error);
      setResult("Error calling evaluation API");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-lg mx-auto">
      <h1 className="text-2xl font-bold mb-4">Manual Evaluation</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* User Message */}
        <div>
          <label className="block font-medium mb-1">User Message</label>
          <Input
            type="text"
            value={userMessage}
            onChange={(e) => setUserMessage(e.target.value)}
            required
          />
        </div>

        <div>
          <label className="block font-medium mb-1">Agent Reply</label>
          <Input
            type="text"
            value={agentReply}
            onChange={(e) => setAgentReply(e.target.value)}
            required
          />
        </div>

        <div>
          <label className="block font-medium mb-1">Reference Reply</label>
          <Input
            type="text"
            value={referenceReply}
            onChange={(e) => setReferenceReply(e.target.value)}
            required
          />
        </div>

        <div>
          <label className="block font-medium mb-1">Interaction Type</label>
          <select
            className="border rounded w-full p-2"
            value={interactionType}
            onChange={(e) => setInteractionType(e.target.value)}
          >
            <option value="opening">Opening</option>
            <option value="followup">Follow-up</option>
            <option value="closing">Closing</option>
          </select>
        </div>

        <div>
          <label className="block font-medium mb-1">Description</label>
          <Input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>

        <div>
          <label className="block font-medium mb-1">Model ID</label>
          <Input
            type="text"
            value={modelId}
            onChange={(e) => setModelId(e.target.value)}
          />
        </div>

        <Button type="submit" disabled={loading}>
          {loading ? "Evaluating..." : "Run Evaluation"}
        </Button>
      </form>

      {result && (
        <pre className="mt-6 bg-gray-100 p-4 rounded text-sm overflow-x-auto">
          {result}
        </pre>
      )}
    </div>
  );
}
