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
    title: "Settings",
    url: "/dashboard/settings",
    icon: "settings",
    isActive: true,
    items: [],
  },
];
