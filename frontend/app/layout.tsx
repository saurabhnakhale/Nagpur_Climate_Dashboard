import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "Nagpur Climate Intelligence",
  description: "Live climate impact and public health monitoring dashboard for Nagpur."
};
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}