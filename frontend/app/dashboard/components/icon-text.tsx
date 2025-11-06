import React from "react"

interface SidebarIconProps {
  children: React.ReactNode
  bgColor?: string // e.g. 'bg-gray-100', 'bg-blue-100'
  className?: string
}

export function SidebarIcon({ children, bgColor = '', className = '' }: SidebarIconProps) {
  return (
    <span
      className={`inline-flex items-center justify-center rounded-md ${bgColor} ${className}`}
    >
      {children}
    </span>
  )
}
