// File: src/app/dashboard/projects/page.tsx
"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
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
  description: string;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  status: "active" | "completed" | "archived";
};

export default function ProjectsPage() {
  const router = useRouter();
  const { toast } = useToast();

  // No Firestore: empty placeholders
  // const [projects] = useState<Project[]>([]);
  const [projects, setProjects] = useState<Project[]>([
    {
      id: "proj-1",
      name: "Llama Chatbot",
      description: "Evaluation of Llama responses",
      createdBy: "bedra",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      status: "active",
    },
    {
      id: "proj-2",
      name: "BERT QA",
      description: "Question Answering project",
      createdBy: "bedra",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      status: "active",
    },
  ]);

  const [loading] = useState(false);
  const [deleteProjectId, setDeleteProjectId] = useState<string | null>(null);

  const handleAddProject = (newProject: any) => {
    toast({ description: "Created" });
  };

  const confirmDelete = () => {
    toast({ description: `Deleted` });
    setDeleteProjectId(null);
  };

  const handleCopyProjectId = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(id);
    toast({ description: "Project ID Copied!" });
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Projects</h1>
        <NewProjectDialog onAddProject={handleAddProject} userId={undefined} />
      </div>

      {loading ? (
        <p>Loading projects...</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <Card
              key={project.id}
              className="border border-gray-200 shadow-sm rounded-2xl hover:shadow-md hover:-translate-y-1 transition cursor-pointer"
              onClick={() => router.push(`/dashboard/projects/${project.name}`)}
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
                    >
                      <Trash2 className="w-5 h-5" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-6">
                <p className="text-sm text-gray-600 mb-4">llm-project</p>
                <div className="flex justify-between text-sm text-gray-500">
                  <div className="flex items-center gap-2">
                    <Brain className="w-4 h-4 text-gray-500" />
                    <span className="capitalize">{project.status}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-gray-500" />
                    <span>
                      {new Date(project.createdAt).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}

          {!projects.length && (
            <h1 className="col-span-full text-center text-gray-500">
              No projects yet
            </h1>
          )}
        </div>
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
