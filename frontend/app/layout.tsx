import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Churn Intelligence Platform",
  description: "Explainable customer churn prediction dashboard",
};

const NAV_LINKS = [
  { href: "/", label: "Overview" },
  { href: "/predict", label: "Predict Churn" },
  { href: "/analytics", label: "Analytics" },
  { href: "/model", label: "Model Info" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
            <Link href="/" className="text-lg font-semibold text-slate-900">
              Churn Intelligence
            </Link>
            <nav className="flex gap-6 text-sm font-medium text-slate-600">
              {NAV_LINKS.map((link) => (
                <Link key={link.href} href={link.href} className="hover:text-brand-600">
                  {link.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-10">{children}</main>
        <footer className="mx-auto max-w-6xl px-6 py-10 text-xs text-slate-400">
          Predictions reflect statistical associations learned from historical data, not
          guaranteed or causal outcomes for any individual customer.
        </footer>
      </body>
    </html>
  );
}
