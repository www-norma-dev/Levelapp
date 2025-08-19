// File: src/app/dashboard/projects/page.tsx
"use client";

import React, { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { NewProjectDialog } from "./_components/NewProjectModal";
import { Brain, Calendar, Trash2, Copy } from "lucide-react";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction,
} from "@/components/ui/alert-dialog";
import { useToast } from "@/hooks/use-toast";

type Project = {
  id: string;
  name: string;
  description?: string;
  createdAt?: string | null;
  updatedAt?: string | null;
  status: "active" | "completed" | "archived";
};

type ListResponse = {
  items: Project[];
  nextCursor: string | null;
  count: number;
};

export default function ProjectsPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { data: session, status } = useSession();

  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  const [nextCursor, setNextCursor] = useState<string | null>(null);

  const [deleteProjectId, setDeleteProjectId] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (status !== "authenticated") return;

    const controller = new AbortController();
    abortRef.current?.abort();
    abortRef.current = controller;

    (async () => {
      setLoading(true);
      try {
        const url = new URL("/api/projects", window.location.origin);
        url.searchParams.set("limit", "20");

        const res = await fetch(url.toString(), {
          method: "GET",
          signal: controller.signal,
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.error || `Fetch failed: ${res.status}`);
        }
        const data: ListResponse = await res.json();
        console.log("Fetched projects:", data);
        setProjects(data.items || []);
        setNextCursor(data.nextCursor);
      } catch (e) {
        if ((e as any)?.name !== "AbortError") {
          console.error(e);
          toast({ description: "Failed to load projects" });
        }
      } finally {
        setLoading(false);
      }
    })();

    return () => controller.abort();
  }, [status, toast]);

  const loadMore = async () => {
    if (!nextCursor) return;
    setLoadingMore(true);
    try {
      const url = new URL("/api/projects", window.location.origin);
      url.searchParams.set("limit", "20");
      url.searchParams.set("cursor", nextCursor);

      const res = await fetch(url.toString(), { method: "GET" });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Fetch failed: ${res.status}`);
      }
      const data: ListResponse = await res.json();
      setProjects((prev) => [...prev, ...(data.items || [])]);
      setNextCursor(data.nextCursor);
    } catch (e) {
      console.error(e);
      toast({ description: "Failed to load more projects" });
    } finally {
      setLoadingMore(false);
    }
  };

  const handleAddProject = async (newProject: {
    name: string;
    description?: string;
  }) => {
    try {
      const res = await fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newProject),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Create failed: ${res.status}`);
      }
      const created: Project = await res.json();
      setProjects((prev) => [created, ...prev]); // optimistic prepend
      toast({ description: "Project created successfully!" });
    } catch (e) {
      console.error(e);
      toast({ description: "Failed to create project" });
    }
  };

  const confirmDelete = () => {
    toast({ description: `Deleted` });
    setProjects((prev) => prev.filter((p) => p.id !== deleteProjectId));
    setDeleteProjectId(null);
  };

  const handleCopyProjectId = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(id);
    toast({ description: "Project ID Copied!" });
  };

  if (status === "loading") return <div className="p-8">Checking session…</div>;
  if (!session?.user)
    return <div className="p-8">Please sign in to manage projects.</div>;

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Projects</h1>
        <NewProjectDialog onAddProject={handleAddProject} />
      </div>

      {loading ? (
        <p>Loading projects...</p>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => {
              const createdAt = project.createdAt
                ? new Date(project.createdAt)
                : null;
              const createdAtLabel = createdAt
                ? createdAt.toLocaleDateString()
                : "—";

              return (
                <Card
                  key={project.id}
                  className="border border-gray-200 shadow-sm rounded-2xl hover:shadow-md hover:-translate-y-1 transition cursor-pointer"
                  onClick={() =>
                    router.push(`/dashboard/projects/${project.id}`)
                  } // consider using id for uniqueness
                >
                  <CardHeader className="p-6 bg-gray-50 rounded-t-2xl">
                    <div className="flex justify-between items-start">
                      <CardTitle className="text-lg font-semibold text-gray-800">
                        {project.name}
                      </CardTitle>
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-gray-600 hover:bg-gray-100 rounded-full"
                          onClick={(e) => handleCopyProjectId(project.id, e)}
                          title="Copy Project ID"
                        >
                          <Copy className="w-5 h-5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-red-600 rounded-full hover:bg-red-50"
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeleteProjectId(project.id);
                          }}
                          title="Delete Project"
                        >
                          <Trash2 className="w-5 h-5" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="p-6">
                    <p className="text-sm text-gray-600 mb-4">
                      {project.description || "—"}
                    </p>
                    <div className="flex justify-between text-sm text-gray-500">
                      <div className="flex items-center gap-2">
                        <Brain className="w-4 h-4 text-gray-500" />
                        <span className="capitalize">{project.status}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-gray-500" />
                        <span>{createdAtLabel}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}

            {!projects.length && (
              <h1 className="col-span-full text-center text-gray-500">
                No projects yet
              </h1>
            )}
          </div>

          {nextCursor && (
            <div className="flex justify-center mt-8">
              <Button onClick={loadMore} disabled={loadingMore}>
                {loadingMore ? "Loading…" : "Load more"}
              </Button>
            </div>
          )}
        </>
      )}

      {/* Delete Confirmation */}
      {deleteProjectId && (
        <AlertDialog open onOpenChange={() => setDeleteProjectId(null)}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Are you sure?</AlertDialogTitle>
              <AlertDialogDescription>
                This action cannot be undone. This will permanently delete the
                project.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={() => setDeleteProjectId(null)}>
                Cancel
              </AlertDialogCancel>
              <AlertDialogAction
                onClick={confirmDelete}
                className="bg-red-600 hover:bg-red-700"
              >
                Confirm Delete
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
    </div>
  );
}
