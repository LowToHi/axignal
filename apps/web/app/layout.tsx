import type {Metadata} from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AXIGNAL — Investigation Shell v0.2',
  description: 'Global Opportunity Intelligence prototype'
};

export default function RootLayout({children}: Readonly<{children: React.ReactNode}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
