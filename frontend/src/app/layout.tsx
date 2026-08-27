import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";

export const metadata: Metadata = {
  title: "Kestrel — AI Trading Intelligence",
  description: "See every market. Miss nothing. Cross-platform AI trading intelligence by CapeChain Labs.",
  keywords: ["trading", "AI", "forex", "crypto", "indices", "signals", "analysis"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/kestrel-logo.jpg" />
        <script dangerouslySetInnerHTML={{ __html: `
          (function() {
            document.documentElement.style.backgroundColor = '#060a14';
            document.documentElement.style.colorScheme = 'dark';
          })();
        `}} />
      </head>
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
