import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ruata AI Software Engineering Team",
  description: "Hybrid cloud + local AI software development control plane",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
