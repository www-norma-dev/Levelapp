import { NavItem } from "@/types";

export type User = {
  id: number;
  name: string;
  company: string;
  role: string;
  verified: boolean;
  status: string;
};

export const navItems: NavItem[] = [
  {
    title: "Dashboard",
    url: "/dashboard/overview",
    icon: "dashboard",
    isActive: true,
    items: [
      {
        title: "Overview",
        url: "/dashboard/overview",
        icon: "dashboard",
      },
      {
        title: "Projects",
        url: "/dashboard/projects",
        icon: "product",
      },
    ],
  },
  {
    title: "API Config",
    url: "/dashboard/api-config",
    icon: "webhook",
    isActive: true,
    items: [
      {
        title: "Manage api's",
        url: "/dashboard/api-config",
        icon: "product",
      },
    ],
  },
  {
    title: "Datasets",
    url: "/dashboard/datasets",
    icon: "database",
    isActive: true,
    items: [
      {
        title: "Manage datasets",
        url: "/dashboard/datasets",
        icon: "product",
      },
    ],
  },
  {
    title: "Evaluate",
    url: "/dashboard/evaluate",
    icon: "database",
    isActive: true,
    items: [
      {
        title: "Run Evaluation",
        url: "/dashboard/evaluate",
        icon: "database",
      },
    ],
  },
  {
    title: "Settings",
    url: "/dashboard/settings",
    icon: "settings",
    isActive: true,
    items: [],
  },
];
