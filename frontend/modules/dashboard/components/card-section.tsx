import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import { ButtonClient } from "@/app/dashboard/components/button-client";
import React from "react";

interface SectionCardProps {
  title: string;
  children: React.ReactNode;
  buttonLabel: string;
  buttonAction: string;
  onBulletsClick?: () => void;
  className?: string;
}

export function SectionCard({
  title,
  children,
  buttonLabel,
  buttonAction,
  onBulletsClick,
  className = "",
}: SectionCardProps) {
  return (
    <Card className={`h-full flex flex-col ${className}`}>
      <CardHeader className="pb-0 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <CardTitle className="text-2xl font-extrabold text-lintblauw">
            {title}
          </CardTitle>
          {/* Bullets button, optioneel */}
          {onBulletsClick && (
            <button
              onClick={onBulletsClick}
              className="ml-2 p-2 rounded-full hover:bg-gray-100 transition-colors"
              aria-label="Toon lijst"
            >
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full block mb-0.5"></span>
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full block mb-0.5"></span>
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full block"></span>
            </button>
          )}
        </div>
      </CardHeader>
      <CardContent className="p-0 flex-1 overflow-y-auto">
        {children}
      </CardContent>
      <CardFooter className="pt-0 mt-auto">
        <ButtonClient className="w-full" action={buttonAction}>
          {buttonLabel}
        </ButtonClient>
      </CardFooter>
    </Card>
  );
}
