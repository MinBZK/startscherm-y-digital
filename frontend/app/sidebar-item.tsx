import React from "react";
import Link from "next/link";

interface SidebarItemProps {
  icon: React.ReactNode;
  text: string;
  href?: string;
  bgColor?: string; // Tailwind class, e.g. 'bg-lintblauw'
  textColor?: string; // Tailwind class, e.g. 'text-lintblauw'
  iconBg?: string; // Tailwind class for icon background
  active?: boolean;
  className?: string;
  onClick?: () => void; // Add onClick prop for button functionality
}

export function SidebarItem({
  icon,
  text,
  href = "#",
  bgColor = "",
  textColor = "text-gray-700",
  iconBg = "",
  active = false,
  className = "",
  onClick,
}: SidebarItemProps) {
  const base = `flex items-center px-2 py-2 text-sm rounded-md transition-colors ${bgColor} ${textColor} ${
    active ? "font-semibold" : "font-normal"
  } ${active ? "bg-[#F2F7FA]" : "hover:bg-gray-100"} ${className}`;

  const iconElement = (
    <span
      className={`mr-3 flex items-center justify-center ${iconBg} ${
        iconBg ? "rounded-md w-9 h-9" : ""
      }`}
    >
      {icon}
    </span>
  );

  const textElement = <span>{text}</span>;

  // If onClick is provided, render as a button instead of a Link
  if (onClick) {
    return (
      <button onClick={onClick} className={base}>
        {iconElement}
        {textElement}
      </button>
    );
  }

  return (
    <Link href={href} className={base}>
      {iconElement}
      {textElement}
    </Link>
  );
}
