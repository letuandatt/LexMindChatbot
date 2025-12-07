import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Law Chatbot",
  description: "Hệ thống Chatbot tra cứu văn bản pháp luật",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <body suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
