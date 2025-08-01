"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
} from "@/components/ui/form";
import { useForm } from "react-hook-form";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";

type EvaluationFormValues = {
  userMessage: string;
  referenceReply: string;
  interactionType: string;
  modelId: string;
};

export default function EvaluatePage() {
  const { projectId } = useParams();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const form = useForm<EvaluationFormValues>({
    defaultValues: {
      userMessage: "",
      referenceReply: "",
      interactionType: "opening",
      modelId: "meta-llama/Llama-3.3-70B-Instruct",
    },
  });

  const handleSubmit = async (values: EvaluationFormValues) => {
    setLoading(true);
    setResult(null);

    const payload = {
      test_batch: {
        id: crypto.randomUUID(),
        interactions: [
          {
            id: crypto.randomUUID(),
            user_message: values.userMessage,
            agent_reply: "",
            reference_reply: values.referenceReply,
            interaction_type: values.interactionType,
            reference_metadata: { intent: "greeting", sentiment: "positive" },
            generated_metadata: { intent: "greeting", sentiment: "positive" },
          },
        ],
        description: "Quick evaluation from UI",
        details: { name: "Manual Test", version: "1.0" },
      },
      endpoint: "http://localhost:8000",
      model_id: values.modelId,
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

  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const toggleReadMore = (key: string) => {
    setExpanded((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const truncate = (text: string, max = 150, key = "") =>
    text && !expanded[key] && text.length > max
      ? text.slice(0, max) + "…"
      : text || "N/A";

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-start">
        {/*  Form Column */}
        <div className="flex-1 max-w-sm bg-white rounded-xl shadow-md p-6 border border-gray-200 min-h-[500px]">
          <h1 className="text-xl font-bold mb-4 text-gray-900">Evaluation</h1>
          <p className="text-sm text-gray-600 mb-4">
            Enter the scenario details below and run the evaluation.
          </p>

          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(handleSubmit)}
              className="space-y-4"
            >
              <FormField
                control={form.control}
                name="userMessage"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>User Message</FormLabel>
                    <FormControl>
                      <Input placeholder="Enter user message" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="referenceReply"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Reference Reply</FormLabel>
                    <FormControl>
                      <Input placeholder="Enter reference reply" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="interactionType"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Interaction Type</FormLabel>
                    <FormControl>
                      <Select
                        onValueChange={field.onChange}
                        value={field.value}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select interaction type..." />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="opening">Opening</SelectItem>
                          <SelectItem value="followup">Follow-up</SelectItem>
                          <SelectItem value="closing">Closing</SelectItem>
                        </SelectContent>
                      </Select>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="modelId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Model ID</FormLabel>
                    <FormControl>
                      <Select
                        onValueChange={field.onChange}
                        value={field.value}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select a model..." />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="meta-llama/Meta-Llama-3.1-8B-Instruct">
                            meta-llama/Meta-Llama-3.1-8B-Instruct
                          </SelectItem>
                          <SelectItem value="meta-llama/Llama-3.3-70B-Instruct">
                            meta-llama/Llama-3.3-70B-Instruct
                          </SelectItem>
                          <SelectItem value="meta-llama/Meta-Llama-3.1-405B-Instruct-FP8">
                            meta-llama/Meta-Llama-3.1-405B-Instruct-FP8
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <Button type="submit" disabled={loading} className="w-full">
                {loading ? "Evaluating..." : "Run Evaluation"}
              </Button>
            </form>
          </Form>
        </div>

        {/*  Results Column */}
        <div className="flex-[2] bg-gray-50 rounded-xl shadow-lg p-6 border border-gray-300 overflow-y-auto">
          <h1 className="text-xl font-bold mb-4 text-gray-900">Results</h1>
          {result ? (
            (() => {
              const parsed = JSON.parse(result);
              const scenarios = parsed?.results?.scenarios || [];

              return (
                <div className="space-y-6">
                  {scenarios.map((scenario: any, i: number) => (
                    <div
                      key={i}
                      className="bg-white p-6 rounded-lg border shadow-sm hover:shadow-md transition-shadow duration-200"
                    >
                      {scenario.attempts?.map((attempt: any, j: number) => {
                        const interaction = attempt.interactions?.[0] || {};
                        const evalResults =
                          interaction.evaluation_results || {};
                        const openai = evalResults.openai || {};
                        const ionos = evalResults.ionos || {};

                        return (
                          <div key={j} className="space-y-6">
                            <div className="bg-gray-50 p-4 rounded-md border border-gray-200">
                              <h2 className="font-semibold text-gray-900 text-lg mb-1">
                                User Message
                              </h2>
                              <p className="text-gray-800 text-sm leading-relaxed">
                                {truncate(
                                  interaction.user_message,
                                  150,
                                  `um-${i}-${j}`
                                )}
                              </p>
                              {interaction.user_message?.length > 150 && (
                                <button
                                  className="text-blue-600 text-xs mt-1 hover:underline"
                                  onClick={() => toggleReadMore(`um-${i}-${j}`)}
                                >
                                  {expanded[`um-${i}-${j}`]
                                    ? "Read Less"
                                    : "Read More"}
                                </button>
                              )}
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                              <div className="bg-blue-50 p-4 rounded-md border border-blue-100">
                                <h3 className="font-medium text-blue-800 text-sm mb-1">
                                  Reference Reply
                                </h3>
                                <p className="text-gray-700 text-sm leading-relaxed">
                                  {truncate(
                                    interaction.reference_reply,
                                    150,
                                    `ref-${i}-${j}`
                                  )}
                                </p>
                                {interaction.reference_reply?.length > 150 && (
                                  <button
                                    className="text-blue-600 text-xs mt-1 hover:underline"
                                    onClick={() =>
                                      toggleReadMore(`ref-${i}-${j}`)
                                    }
                                  >
                                    {expanded[`ref-${i}-${j}`]
                                      ? "Read Less"
                                      : "Read More"}
                                  </button>
                                )}
                              </div>
                              <div className="bg-green-50 p-4 rounded-md border border-green-100">
                                <h3 className="font-medium text-green-800 text-sm mb-1">
                                  Agent Reply
                                </h3>
                                <p className="text-gray-700 text-sm leading-relaxed">
                                  {truncate(
                                    interaction.agent_reply,
                                    150,
                                    `agent-${i}-${j}`
                                  )}
                                </p>
                                {interaction.agent_reply?.length > 150 && (
                                  <button
                                    className="text-blue-600 text-xs mt-1 hover:underline"
                                    onClick={() =>
                                      toggleReadMore(`agent-${i}-${j}`)
                                    }
                                  >
                                    {expanded[`agent-${i}-${j}`]
                                      ? "Read Less"
                                      : "Read More"}
                                  </button>
                                )}
                              </div>
                            </div>

                            <Accordion
                              type="single"
                              collapsible
                              className="w-full mt-4"
                            >
                              <AccordionItem value="openai">
                                <AccordionTrigger className="text-gray-900 font-semibold">
                                  OpenAI Evaluation
                                </AccordionTrigger>
                                <AccordionContent>
                                  <p className="text-xs text-gray-700">
                                    <b>Match Level:</b>{" "}
                                    {openai.match_level ?? "N/A"}
                                  </p>
                                  <p className="text-xs text-gray-700 mt-1">
                                    <b>Justification:</b>{" "}
                                    {openai.justification || "N/A"}
                                  </p>
                                </AccordionContent>
                              </AccordionItem>

                              <AccordionItem value="ionos">
                                <AccordionTrigger className="text-gray-900 font-semibold">
                                  IONOS Evaluation
                                </AccordionTrigger>
                                <AccordionContent>
                                  <p className="text-xs text-gray-700">
                                    <b>Match Level:</b>{" "}
                                    {ionos.match_level ?? "N/A"}
                                  </p>
                                  <p className="text-xs text-gray-700 mt-1">
                                    <b>Justification:</b>{" "}
                                    {ionos.justification || "N/A"}
                                  </p>
                                </AccordionContent>
                              </AccordionItem>
                            </Accordion>

                            <div className="flex justify-end text-xs text-gray-500 mt-2">
                              Execution Time:{" "}
                              {attempt.execution_time
                                ? attempt.execution_time + "s"
                                : "N/A"}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ))}
                </div>
              );
            })()
          ) : (
            <div className="flex items-center justify-center  w-full h-full text-gray-400 text-sm italic">
              No results yet. Run an evaluation to see results here.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
