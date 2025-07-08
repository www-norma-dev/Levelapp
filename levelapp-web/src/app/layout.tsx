import type { Metadata } from "next";
import { Lato } from "next/font/google";
import NextTopLoader from "nextjs-toploader";
import "./globals.css";
import { auth } from "../../auth";
import Providers from "@/components/layout/Providers";
import { Toaster } from "@/components/ui/toaster";

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
        url: "https://norma-backend--norma-website-716ae.us-central1.hosted.app/assets/preview.png",
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
    images: [
      "https://norma-backend--norma-website-716ae.us-central1.hosted.app/assets/preview.png",
    ],
  },
};
const lato = Lato({
  subsets: ["latin"],
  weight: ["400", "700", "900"],
  display: "swap",
});



export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();

  return (
    <html
      lang="en"
      className={`${lato.className}`}
      suppressHydrationWarning={true}
    >
      <body>
        <NextTopLoader color="#736EFF" showSpinner={false} />
        <Providers session={session}>
          <Toaster />
          {children}
        </Providers>
      </body>
    </html>
  );
}
