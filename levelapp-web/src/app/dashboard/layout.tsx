import AppSidebar from "@/components/layout/app-sidebar";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Eval Norma - AI Agent Evaluation Platform",
  description:
    "Eval Norma provides advanced tools to evaluate AI agents with detailed performance metrics, correctness, and efficiency insights. Optimize AI development with actionable evaluations.",
  keywords: [
    "Eval Norma",
    "AI agent evaluation",
    "performance metrics",
    "AI correctness analysis",
    "AI performance insights",
    "AI model evaluation",
    "AI assessment tools",
  ],
  openGraph: {
    title: "Eval Norma - AI Agent Evaluation Platform",
    description:
      "Discover Eval Norma, the platform for evaluating AI agents with in-depth performance metrics and correctness analysis. Enhance your AI development process with precision tools.",
    url: "https://eval-norma--norma-dev.europe-west4.hosted.app",
    type: "website",
    images: [
      {
        url: "",
        width: 1200,
        height: 630,
        alt: "Eval Norma - AI Agent Evaluation",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Eval Norma - AI Agent Evaluation Platform",
    description:
      "Evaluate AI agents with precision using Eval Norma. Get detailed performance metrics, correctness analysis, and actionable insights to optimize AI models.",
    images: [],
  },
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <AppSidebar>
        {children}
      </AppSidebar>
    </>
  );
}
