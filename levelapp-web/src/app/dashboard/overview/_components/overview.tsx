// File: src/app/dashboard/overview/page.tsx
"use client";

import { useState } from "react";
import PageContainer from "@/components/layout/page-container";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import Image from "next/image";
import { ArrowRight, ChevronRight } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface LatestBatch {
  projectId: string;
  projectName: string;
  batchId: string;
  testName: string;
  type: "extract" | "multiAgent";
  createdAt: Date;
}

export default function OverViewPage() {
  const [metrics] = useState({
    totalProjects: 0,
    activeProjects: 0,
  });

  const [latestBatches] = useState<LatestBatch[]>([]);
  const [activeProjects] = useState<{ id: string; name: string }[]>([]);
  const [showModal, setShowModal] = useState(false);

  return (
    <PageContainer scrollable>
      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>No Projects Yet</DialogTitle>
            <DialogDescription>
              You don’t have any projects at the moment. Create one to get
              started!
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Link href="/dashboard/projects">
              <Button>Create Your First Project</Button>
            </Link>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="space-y-8">
        {/* Header */}
        <div className="space-y-4">
          <h2 className="text-3xl font-bold tracking-tight">Welcome 👋</h2>
          <p className="text-muted-foreground text-lg">Projects Overview</p>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle>Total Projects</CardTitle>
            </CardHeader>
            <CardContent>
              <h3 className="text-4xl font-bold">{metrics.totalProjects}</h3>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Active Projects</CardTitle>
            </CardHeader>
            <CardContent>
              <h3 className="text-4xl font-bold">{metrics.activeProjects}</h3>
            </CardContent>
          </Card>

          <Card
            className="p-4 flex items-center justify-between bg-cover bg-center relative"
            style={{ backgroundImage: "url('/assets/norma.png')" }}
          >
            <Image
              width={100}
              height={70}
              src="/assets/logo_pub.png"
              alt="Logo"
            />
            <div className="absolute bottom-2 right-2 z-10">
              <Link
                href="https://norma.dev"
                className="text-xs text-white underline inline-flex items-center space-x-1"
              >
                <span>Visit Website</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </Card>
        </div>

        {/* Latest Batch Tests & Active Projects */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Latest Batches */}
          <Card>
            <CardHeader>
              <CardTitle>Latest Batch Tests</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-4">
                {activeProjects.map((project) => {
                  const batch = latestBatches.find(
                    (b) => b.projectId === project.id
                  );
                  return (
                    <li
                      key={project.id}
                      className="flex flex-col space-y-1 p-3 border rounded-lg"
                    >
                      <Badge variant="outline" className="w-fit">
                        {project.name}
                      </Badge>
                      {batch ? (
                        <>
                          <p className="text-sm">
                            <strong>Test Name:</strong> {batch.testName}
                          </p>
                          <p className="text-sm">
                            <strong>Type:</strong> {batch.type}
                          </p>
                          <p className="text-sm">
                            <strong>Created:</strong>{" "}
                            {batch.createdAt.toLocaleString()}
                          </p>
                          <Link
                            href={`/dashboard/projects/${batch.projectId}/batch/${batch.batchId}/${batch.type}`}
                            className="text-teal-700 text-sm"
                          >
                            View details &rarr;
                          </Link>
                        </>
                      ) : (
                        <p className="text-sm text-muted-foreground">
                          No batches yet.
                        </p>
                      )}
                    </li>
                  );
                })}
              </ul>
            </CardContent>
          </Card>

          {/* Active Projects */}
          <Card>
            <CardHeader>
              <CardTitle>Active Projects</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 flex flex-col">
              {activeProjects.map((project) => (
                <Link
                  href={`/dashboard/projects/${project.id}`}
                  key={project.id}
                >
                  <div className="p-3 border rounded-lg flex justify-between items-center hover:bg-gray-50 transition">
                    <div>
                      <h4 className="text-lg font-semibold">{project.name}</h4>
                      <p className="text-sm text-muted-foreground">
                        View project details
                      </p>
                    </div>
                    <ChevronRight className="h-5 w-5 text-muted-foreground" />
                  </div>
                </Link>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </PageContainer>
  );
}
