/**
 * O-Negative Frontend - Root Layout
 * This is the main layout for all pages in the Next.js app
 */

import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'O-Negative - AI Blood Coordination',
  description: 'Urgent blood request coordination across India with AI agent',
  keywords: 'blood donation, blood banks, urgent blood request, India',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
