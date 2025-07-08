// @ts-nocheck
"use client";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Separator } from "@/components/ui/separator";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarProvider,
  SidebarRail,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { navItems } from "@/constants/data";
import { ChevronRight, GalleryVerticalEnd } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import * as React from "react";
import { Breadcrumbs } from "../breadcrumbs";
import { Icons } from "../icons";
import { UserNav } from "./user-nav";
import { useSession } from "next-auth/react";

export const company = {
  name: "Norma",
  logo: GalleryVerticalEnd,
  plan: "Eval",
};

export default function AppSidebar({
  children,
}: {
  children: React.ReactNode;
}) {
  const [mounted, setMounted] = React.useState(false);
  const { data: session } = useSession();
  const pathname = usePathname();

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null; // or a loading skeleton
  }

  console.log(session);

  return (
    <SidebarProvider>
      {/* Add a subtle shadow and border for a modern look */}
      <Sidebar
        collapsible="icon"
        className="shadow-lg border-r border-gray-200"
      >
        {/* Enhanced header with border and padding */}
        <SidebarHeader className=" border-b border-gray-200">
          <div className="flex gap-2 py-2 text-sidebar-accent-foreground items-center">
            <div className="font-bold flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
              N
            </div>
            <div className="grid flex-1 text-left text-sm leading-tight">
              <span className="truncate font-semibold">{company.name}</span>
              <span className="truncate text-xs text-gray-500">
                {company.plan}
              </span>
            </div>
          </div>
        </SidebarHeader>

        {/* Slight spacing on the sidebar content */}
        <SidebarContent className="overflow-x-hidden mt-2">
          <SidebarGroup>
            <SidebarGroupLabel className="text-xs font-semibold uppercase tracking-wider text-gray-500 px-4 mb-2">
              Overview
            </SidebarGroupLabel>
            <SidebarMenu>
              {navItems.map((item: any) => {
                //@ts-ignore
                const Icon = item.icon ? Icons[item.icon] : Icons.logo;
                return item?.items && item?.items?.length > 0 ? (
                  <Collapsible
                    key={item.title}
                    asChild
                    defaultOpen={item.isActive}
                    className="group/collapsible"
                  >
                    <SidebarMenuItem>
                      <CollapsibleTrigger asChild>
                        <SidebarMenuButton
                          tooltip={item.title}
                          isActive={pathname === item.url}
                          className="transition-colors duration-200 hover:bg-gray-100 px-3 rounded-md"
                        >
                          {item.icon && <Icon className="text-teal-600" />}
                          <span className="font-semibold">{item.title}</span>
                          <ChevronRight className="ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90" />
                        </SidebarMenuButton>
                      </CollapsibleTrigger>
                      <CollapsibleContent>
                        <SidebarMenuSub>
                          {item.items?.map((subItem: any) => (
                            <SidebarMenuSubItem key={subItem.title}>
                              <SidebarMenuSubButton
                                asChild
                                isActive={pathname === subItem.url}
                                className="transition-colors duration-200 hover:bg-gray-50 pl-6 rounded-md"
                              >
                                <Link href={subItem.url}>
                                  <span>{subItem.title}</span>
                                </Link>
                              </SidebarMenuSubButton>
                            </SidebarMenuSubItem>
                          ))}
                        </SidebarMenuSub>
                      </CollapsibleContent>
                    </SidebarMenuItem>
                  </Collapsible>
                ) : (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      asChild
                      tooltip={item.title}
                      isActive={pathname === item.url}
                      className="transition-colors duration-200 hover:bg-gray-100 px-3 rounded-md"
                    >
                      <Link href={item.url}>
                        <Icon />
                        <span>{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroup>
        </SidebarContent>

        <SidebarRail />
      </Sidebar>

      <SidebarInset>
        {/* Stick header at the top and give it a light shadow */}
        <header className="flex h-16 shrink-0 items-center justify-between gap-2 transition-[width,height] ease-linear group-has-[[data-collapsible=icon]]/sidebar-wrapper:h-12 px-4 shadow-sm border-b border-gray-200 bg-white">
          <div className="flex items-center gap-2">
            {/* Slight scale on hover for the trigger */}
            <SidebarTrigger className="transition-transform duration-200 hover:scale-105" />
            <Separator
              orientation="vertical"
              className="mr-2 h-6 border-gray-300"
            />
            <Breadcrumbs />
          </div>

          <div className="flex items-center gap-2">
            <UserNav />
          </div>
        </header>

        {/* Main content area with subtle background and padding */}
        <div className="min-h-screen bg-slate-50 p-4">{children}</div>
      </SidebarInset>
    </SidebarProvider>
  );
}
