import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { ThemeProvider, themeInitScript } from "@/components/ThemeProvider";

// Deliberate trio: Space Grotesk (display, technical character),
// IBM Plex Sans (humanist body that coheres with the mono),
// IBM Plex Mono (the data face for estimates, p-values, and intervals).
const display = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-display",
  display: "swap",
});

const sans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-sans",
  display: "swap",
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
  display: "swap",
});

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
    <html
      lang="en"
      className={`${display.variable} ${sans.variable} ${mono.variable}`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(JSON_LD) }} />
      </head>
      <body>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
