"use client";
import { Grid, Bell, User, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { SidebarIcon } from "./icon-text";
import { Wrench, RotateCcw } from "lucide-react";

import { useState, useEffect } from "react";
import ProfileSidebar from "./profile-sidebar-content";
import documentsData from "@/dummydata/data_last_docs.json";
import { useNotificationsStore } from "@/store/notification-store";
import { DocumentItem } from "@/lib/types";

export function Header() {
  const [profileOpen, setProfileOpen] = useState(false);
  const { latestDoc, hasNew, markAsRead, setLatestDoc } =
    useNotificationsStore();

  useEffect(() => {
    setLatestDoc((documentsData as DocumentItem[])[0]);
  }, [setLatestDoc]);

  return (
    <header className="bg-white border-b border-gray-200 py-2 px-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <div className="flex items-center py-3">
            <h1 className="!text-black text-3xl font-bold">
              Goedemorgen <span className="text-hemelblauw">Marieke</span>
            </h1>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            className="text-[#027BC7] flex items-center"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#027BC7"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="lucide lucide-pencil"
            >
              <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />
              <path d="m15 5 4 4" />
            </svg>
            <span className="ml-1">Bewerk indeling</span>
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                className="rounded-md px-4 py-4 text-[#027BC7] flex items-center gap-2 border-[#027BC7] border"
              >
                <Grid className="h-5 w-5 text-[#027BC7]" />
                WOO overzicht
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-64">
              <DropdownMenuItem className="bg-[#F2F7FA] text-black font-semibold cursor-default">
                Woo overzicht
              </DropdownMenuItem>
              <DropdownMenuItem>Samenwerkingsruimte</DropdownMenuItem>
              <DropdownMenuItem>
                <SidebarIcon bgColor="bg-gray-100 rounded-lg w-6 h-6 mr-2">
                  <Wrench className="h-4 w-4 text-[#027BC7]" />
                </SidebarIcon>
                Indelingen verkennen
              </DropdownMenuItem>
              <DropdownMenuItem>
                <SidebarIcon bgColor="bg-gray-100 rounded-lg w-6 h-6 mr-2">
                  <RotateCcw className="h-4 w-4 text-[#027BC7]" />
                </SidebarIcon>
                Terug naar standaard
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <DropdownMenu onOpenChange={(open) => open && markAsRead()}>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="relative">
                <Bell className="h-6 w-6 text-[#027BC7]" />
                {hasNew && (
                  <span className="absolute -top-1 -right-1 bg-red-600 text-white text-xs rounded-full px-1.5 py-0.5 font-bold">
                    1
                  </span>
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-72">
              {latestDoc && (
                <DropdownMenuItem asChild>
                  <a
                    href={latestDoc.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-start gap-2 w-full"
                    onClick={markAsRead}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-sm text-black leading-tight">
                        {latestDoc.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {latestDoc.filetype}
                      </p>
                    </div>
                    {hasNew && (
                      <span className="h-2 w-2 bg-lintblauw rounded-full mt-2" />
                    )}
                  </a>
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="flex items-center gap-2 px-2"
              >
                <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-gray-200 overflow-hidden">
                  {/* Hier zou een profielfoto kunnen komen, nu fallback */}
                  <User className="h-6 w-6 text-gray-500" />
                </span>
                <ChevronDown className="h-4 w-4 text-gray-500" />
              </Button>
            </DropdownMenuTrigger>
            {/* style every child with tailwind cursor pointer */}
            <DropdownMenuContent className="[&>*]:cursor-pointer" align="end">
              <DropdownMenuItem onClick={() => setProfileOpen(true)}>
                Mijn profiel
              </DropdownMenuItem>
              <DropdownMenuItem>Instellingen</DropdownMenuItem>
              <DropdownMenuItem>Uitloggen</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
      <ProfileSidebar open={profileOpen} onOpenChange={setProfileOpen} />
    </header>
  );
}
