"use client";

import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = decodeURIComponent(params.projectId as string);

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Project: {projectId}</h1>

      <Button
        onClick={() =>
          router.push(`/dashboard/projects/${params.projectId}/evaluate`)
        }
      >
        Run Evaluation
      </Button>
    </div>
  );
}
