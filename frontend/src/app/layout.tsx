import type { Metadata } from "next"
import "./globals.css"
import { Providers } from "./providers"
import { Inter } from "next/font/google"

const inter = Inter({ subsets: ["latin"] })
export const metadata: Metadata = {
  title: "SignalHire AI",
  description: "AI‑Native Recruiting Intelligence",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.className}>
      <body className="antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}