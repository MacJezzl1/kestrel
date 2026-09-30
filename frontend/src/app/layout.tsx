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
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#060a14" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5, viewport-fit=cover" />
        <script dangerouslySetInnerHTML={{ __html: `
          (function() {
            document.documentElement.style.backgroundColor = '#060a14';
            document.documentElement.style.colorScheme = 'dark';
            if ('serviceWorker' in navigator && window.location.protocol === 'https:') {
              window.addEventListener('load', function() {
                navigator.serviceWorker.register('/sw.js').catch(function(){});
              });
            }
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
