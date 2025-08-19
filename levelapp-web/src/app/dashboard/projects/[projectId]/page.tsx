"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Calendar, Brain } from "lucide-react";

type Project = {
  id: string;
  name: string;
  description?: string;
  status?: "active" | "completed" | "archived";
  createdAt?: string | null;
  updatedAt?: string | null;
};

export default function ProjectDetailPage() {
  const router = useRouter();
  const params = useParams<{ projectId: string }>();
  const { status: authStatus, data: session } = useSession();

  const projectId = decodeURIComponent(params.projectId);
  const [project, setProject] = useState<Project | null>(null);
  const [loadingProject, setLoadingProject] = useState<boolean>(false);

  const formattedCreated = useMemo(() => {
    if (!project?.createdAt) return "—";
    try {
      return new Date(project.createdAt).toLocaleString();
    } catch {
      return "—";
    }
  }, [project?.createdAt]);

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
                <Button
                  onClick={() =>
                    router.push(
                      `/dashboard/projects/${encodeURIComponent(
                        projectId
                      )}/evaluate`
                    )
                  }
                >
                  Run Evaluation
                </Button>
              </div>
            </div>
          ) : (
            <div>Project not found.</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
