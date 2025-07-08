"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Plus, Copy } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils"; // (If you have a classNames utility)

interface NewProjectData {
  name: string;
  description: string;
  createdBy?: string;
  status: "active" | "completed" | "archived";
}

interface Props {
  onAddProject: (project: NewProjectData) => void;
  userId?: string;
}

export function NewProjectDialog({ onAddProject, userId }: Props) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [keysGenerated, setKeysGenerated] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);

  const [formData, setFormData] = useState<NewProjectData>({
    name: "",
    description: "",
    status: "active",
    createdBy: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name) {
      alert("Project name is required.");
      return;
    }

    setLoading(true);

    // Simulate an async call
    setTimeout(() => {
      onAddProject({
        ...formData,
        createdBy: userId,
      });
      setLoading(false);
      setOpen(false);
    }, 1000);
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(text);
    setTimeout(() => setCopied(null), 1500);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="default"
          size="sm"
          className="flex items-center gap-2 transition-colors hover:bg-primary hover:text-primary-foreground"
        >
          <Plus className="w-4 h-4" />
          New Project
        </Button>
      </DialogTrigger>

      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="text-xl">Add New Project</DialogTitle>
          {!keysGenerated && (
            <DialogDescription className="text-muted-foreground">
              Create a new project and generate associated keys for integration.
            </DialogDescription>
          )}
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6 mt-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Project Name</label>
            <Input
              placeholder="Enter your project name..."
              value={formData.name}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, name: e.target.value }))
              }
            />
          </div>
          <Button
            type="submit"
            className="w-full flex justify-center"
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="animate-spin w-5 h-5" />
            ) : (
              "Add Project"
            )}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
