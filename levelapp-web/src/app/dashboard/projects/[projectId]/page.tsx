// File: src/app/dashboard/projects/[projectId]/page.tsx
"use client";

import { useEffect, useMemo, useState } from "react";
import {
  useParams,
  useRouter,
  useSearchParams,
  usePathname,
} from "next/navigation";
import { useSession } from "next-auth/react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Calendar, Brain, ClipboardList } from "lucide-react";

type Project = {
  id: string;
  name: string;
  description?: string;
  status?: "active" | "completed" | "archived";
  createdAt?: string | null;
  updatedAt?: string | null;
};
type ProviderEval = {
  match_level?: number | null;
  justification?: string | null;
} | null;

type EvaluationItem = {
  id: string;
  updatedAt: string | null;
  test_name: string | null; // evaluation name
  modelId: string | null; // model used
  scenariosCount: number;
  attemptsCount: number;
  sample?: {
    user_message?: string | null;
    agent_reply?: string | null;
    reference_reply?: string | null;
    openai?: ProviderEval;
    ionos?: ProviderEval;
    execution_time?: string | number | null;
  } | null;
};

type EvalListResponse = {
  items: EvaluationItem[];
  nextCursor: string | null;
  count: number;
};

export default function ProjectDetailPage() {
  const router = useRouter();
  const params = useParams<{ projectId: string }>();
  const { status: authStatus, data: session } = useSession();
  const search = useSearchParams();
  const pathname = usePathname();

  const projectId = decodeURIComponent(search.get("id") || params.projectId);

  const [project, setProject] = useState<Project | null>(null);
  const [loadingProject, setLoadingProject] = useState<boolean>(false);

  const [evals, setEvals] = useState<EvaluationItem[]>([]);
  const [evalsLoading, setEvalsLoading] = useState<boolean>(false);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);

  const formattedCreated = useMemo(() => {
    if (!project?.createdAt) return "—";
    try {
      return new Date(project.createdAt).toLocaleString();
    } catch {
      return "—";
    }
  }, [project?.createdAt]);

  const goEvaluate = () => {
    router.push(
      `/dashboard/projects/${encodeURIComponent(projectId)}/evaluate`
    );
  };

  useEffect(() => {
    if (authStatus !== "authenticated") return;
    let aborted = false;
    (async () => {
      setLoadingProject(true);
      try {
        const res = await fetch(
          `/api/projects/${encodeURIComponent(projectId)}`,
          { method: "GET" }
        );
        if (!res.ok) throw new Error(`Fetch project failed: ${res.status}`);
        const data: Project = await res.json();
        if (!aborted) setProject(data);
      } catch (e) {
        console.error(e);
        if (!aborted) setProject(null);
      } finally {
        if (!aborted) setLoadingProject(false);
      }
    })();
    return () => {
      aborted = true;
    };
  }, [authStatus, projectId]);

  useEffect(() => {
    if (authStatus !== "authenticated") return;
    let aborted = false;

    (async () => {
      setEvalsLoading(true);
      try {
        const url = `/api/projects/${encodeURIComponent(
          projectId
        )}/evaluations?limit=10`;
        const res = await fetch(url, {
          method: "GET",
          cache: "no-store",
          credentials: "same-origin",
        });

        if (!res.ok) {
          const text = await res.text();
          throw new Error(
            `GET ${url} -> ${res.status} ${res.statusText}: ${text}`
          );
        }

        const data: EvalListResponse = await res.json();
        if (!aborted) {
          setEvals(data.items ?? []);
          setNextCursor(data.nextCursor ?? null);
        }
      } catch (e) {
        console.error("[ProjectDetailPage] evals fetch error:", e);
        if (!aborted) {
          setEvals([]);
          setNextCursor(null);
        }
      } finally {
        if (!aborted) setEvalsLoading(false);
      }
    })();

    return () => {
      aborted = true;
    };
  }, [authStatus, projectId]);

  const loadMore = async () => {
    if (!nextCursor) return;
    setLoadingMore(true);
    try {
      const url = new URL(
        `/api/projects/${encodeURIComponent(projectId)}/evaluations`,
        window.location.origin
      );
      url.searchParams.set("limit", "10");
      url.searchParams.set("cursor", nextCursor);
      const res = await fetch(url.toString(), { method: "GET" });
      if (!res.ok)
        throw new Error(`Fetch more evaluations failed: ${res.status}`);
      const data: EvalListResponse = await res.json();
      setEvals((prev) => [...prev, ...(data.items || [])]);
      setNextCursor(data.nextCursor);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingMore(false);
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <Card className="border border-gray-200 rounded-2xl shadow-sm">
        <CardHeader className="bg-gray-50 rounded-t-2xl">
          <CardTitle className="text-2xl">Project</CardTitle>
        </CardHeader>
        <CardContent className="py-6">
          {loadingProject ? (
            <div>Loading project…</div>
          ) : project ? (
            <>
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <h1 className="text-xl font-semibold text-gray-900">
                    {project.name}
                  </h1>
                  <p className="text-gray-700 mt-1">
                    {project.description || "—"}
                  </p>
                  <div className="flex gap-4 mt-2 text-sm text-gray-600">
                    <span className="inline-flex items-center gap-1">
                      <Brain className="w-4 h-4" />
                      <span className="capitalize">
                        {project.status || "active"}
                      </span>
                    </span>
                    <span className="inline-flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      <span>Created: {formattedCreated}</span>
                    </span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button onClick={goEvaluate}>Run Evaluation</Button>
                </div>
              </div>
            </>
          ) : (
            <div>Project not found.</div>
          )}
        </CardContent>
      </Card>

      <Card className="border border-gray-200 rounded-2xl shadow-sm">
        <CardHeader className="bg-gray-50 rounded-t-2xl">
          <CardTitle className="text-xl inline-flex items-center gap-2">
            <ClipboardList className="w-5 h-5" /> Evaluations
          </CardTitle>
        </CardHeader>
        <CardContent className="py-6">
          {evalsLoading ? (
            <div>Loading evaluations…</div>
          ) : evals.length ? (
            <div className="space-y-4">
              {evals.map((ev) => {
                const updatedLabel = ev.updatedAt
                  ? (() => {
                      try {
                        return new Date(ev.updatedAt).toLocaleString();
                      } catch {
                        return "—";
                      }
                    })()
                  : "—";

                const sample = ev.sample || {};
                const userMsg = sample.user_message ?? "—";
                const agentReply = sample.agent_reply ?? "—";
                const refReply = sample.reference_reply ?? "—";
                const openai = sample.openai ?? {};
                const ionos = sample.ionos ?? {};
                const execTime = sample.execution_time
                  ? `${sample.execution_time}s`
                  : "—";

                return (
                  <div
                    key={ev.id}
                    className="border rounded-xl p-4 hover:shadow-sm transition"
                  >
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                      <div>
                        <div className="text-base font-semibold text-gray-900">
                          {ev.test_name || "Unnamed evaluation"}
                        </div>
                        <div className="text-xs text-gray-500">
                          Batch: {ev.id}
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-6 text-sm text-gray-700">
                        <div>
                          <b>Scenarios:</b> {ev.scenariosCount ?? "—"}
                        </div>
                        <div>
                          <b>Attempts:</b> {ev.attemptsCount ?? "—"}
                        </div>
                        <div>
                          <b>Updated:</b> {updatedLabel}
                        </div>
                        <div>
                          <b>Model:</b> {ev.modelId ?? "—"}
                        </div>
                        <div>
                          <b>Exec:</b> {execTime}
                        </div>
                      </div>
                    </div>

                    <Separator className="my-3" />
                    <div className="grid md:grid-cols-3 gap-4">
                      <div className="bg-gray-50 p-3 rounded border">
                        <div className="text-xs font-semibold text-gray-700 mb-1">
                          User Message
                        </div>
                        <div className="text-sm text-gray-800">
                          {typeof userMsg === "string" && userMsg.length > 240
                            ? userMsg.slice(0, 240) + "…"
                            : userMsg}
                        </div>
                      </div>
                      <div className="bg-green-50 p-3 rounded border border-green-100">
                        <div className="text-xs font-semibold text-green-800 mb-1">
                          Agent Reply
                        </div>
                        <div className="text-sm text-gray-800">
                          {typeof agentReply === "string" &&
                          agentReply.length > 240
                            ? agentReply.slice(0, 240) + "…"
                            : agentReply}
                        </div>
                      </div>
                      <div className="bg-blue-50 p-3 rounded border border-blue-100">
                        <div className="text-xs font-semibold text-blue-800 mb-1">
                          Reference Reply
                        </div>
                        <div className="text-sm text-gray-800">
                          {typeof refReply === "string" && refReply.length > 240
                            ? refReply.slice(0, 240) + "…"
                            : refReply}
                        </div>
                      </div>
                    </div>

                    {(openai || ionos) && (
                      <>
                        <Separator className="my-3" />
                        <div className="grid md:grid-cols-2 gap-4">
                          <div className="bg-white p-3 rounded border">
                            <div className="text-xs font-semibold text-gray-900 mb-1">
                              OpenAI Evaluation
                            </div>
                            <div className="text-xs text-gray-700">
                              <b>Match level:</b> {openai?.match_level ?? "N/A"}
                            </div>
                            <div className="text-xs text-gray-700 mt-1">
                              <b>Justification:</b>{" "}
                              {openai?.justification || "N/A"}
                            </div>
                          </div>
                          <div className="bg-white p-3 rounded border">
                            <div className="text-xs font-semibold text-gray-900 mb-1">
                              IONOS Evaluation
                            </div>
                            <div className="text-xs text-gray-700">
                              <b>Match level:</b> {ionos?.match_level ?? "N/A"}
                            </div>
                            <div className="text-xs text-gray-700 mt-1">
                              <b>Justification:</b>{" "}
                              {ionos?.justification || "N/A"}
                            </div>
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                );
              })}

              {nextCursor && (
                <div className="flex justify-center">
                  <Button onClick={loadMore} disabled={loadingMore}>
                    {loadingMore ? "Loading…" : "Load more"}
                  </Button>
                </div>
              )}
            </div>
          ) : (
            <div className="text-gray-500">No evaluations yet.</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
