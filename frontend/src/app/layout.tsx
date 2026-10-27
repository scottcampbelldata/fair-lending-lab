import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider, themeInitScript } from "@/components/ThemeProvider";

// Type follows scottcampbell.io: Source Serif 4 for text, Libertinus Serif
// Display for headings, Plex Mono for estimates and intervals. All self hosted.

export const metadata: Metadata = {
  metadataBase: new URL("https://fair-lending.scottcampbell.io"),
  title: "Fair Lending Lab: HMDA mortgage disparity analysis",
  description:
    "HMDA data analysis tool for fair lending: disparity screening, hypothesis tests and family wise error correction on CFPB HMDA mortgage application records.",
  applicationName: "Fair Lending Lab",
  authors: [{ name: "Scott Campbell", url: "https://scottcampbell.io/" }],
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    url: "/",
    siteName: "Fair Lending Lab",
    title: "Fair Lending Lab: HMDA mortgage disparity analysis",
    description: "HMDA data analysis tool for fair lending: disparity screening, hypothesis tests and family wise error correction on CFPB HMDA mortgage application records.",
    images: [{ url: "/og-image.png", width: 1200, height: 630, alt: "Fair Lending Lab HMDA disparity screening dashboard" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Fair Lending Lab: HMDA mortgage disparity analysis",
    description: "HMDA data analysis tool for fair lending: disparity screening, hypothesis tests and family wise error correction on CFPB HMDA mortgage application records.",
    images: ["/og-image.png"],
  },
};

// Structured data for search engines.
const JSON_LD = {
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "Fair Lending Lab",
  "url": "https://fair-lending.scottcampbell.io/",
  "description": "HMDA data analysis tool for fair lending: disparity screening, hypothesis tests and family wise error correction on CFPB HMDA mortgage application records.",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Any (web browser)",
  "isAccessibleForFree": true,
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  },
  "author": {
    "@type": "Person",
    "name": "Scott Campbell",
    "url": "https://scottcampbell.io/"
  },
  "subjectOf": {
    "@type": "CreativeWork",
    "name": "Fair Lending Lab case study",
    "url": "https://scottcampbell.io/projects/fair-lending-lab/"
  },
  "sameAs": [
    "https://github.com/scottcampbelldata/fair-lending-lab"
  ]
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preload" href="/fonts/source-serif-4-text.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />
        <link rel="preload" href="/fonts/libertinus-serif-display-latin.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(JSON_LD) }} />
      </head>
      <body>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
