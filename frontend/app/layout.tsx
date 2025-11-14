import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";
import Providers from "./providers";

const rijksOverheidFont = localFont({
  src: "./fonts/RijksSansWeb-Regular.woff2",
  variable: "--font-rijksoverheid",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Wet Open Overheid",
  description: "Wet Open Overheid",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html className={`${rijksOverheidFont.variable}`} lang="nl">
      <body className="antialiased">
        <Providers>
          {children}
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}
