import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { Providers } from "@/lib/providers";

const geist = Geist({ subsets: ["latin"], variable: "--font-geist-sans" });

export const metadata: Metadata = {
  title: "TGS Metrics",
  description: "The Good Spots — internal metrics dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" className={`${geist.variable} h-full antialiased`}>
      <body className="h-full flex">
        <Providers>
          <Sidebar />
          <main className="flex-1 overflow-y-auto bg-muted/30 p-8">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  );
}
