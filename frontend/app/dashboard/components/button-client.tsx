"use client";
import { Button } from "@/components/ui/button";
import React from "react";

interface ButtonClientProps {
  children: React.ReactNode;
  className?: string;
  action: string;
  kleur?: string;
}

export function ButtonClient({
  children,
  className = "",
  action,
  kleur,
}: ButtonClientProps) {
  const base =
    "bg-white border border-lintblauw text-lintblauw rounded-full h-12 text-lg font-medium mt-6 hover:bg-lichtblauw/10";
  return (
    <Button
      className={`${base} ${className} ${kleur ? kleur : ""}`.trim()}
      // onClick={() => alert(action)}
      type="button"
    >
      {children}
    </Button>
  );
}
