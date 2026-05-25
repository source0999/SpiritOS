import Link from "next/link";
import { DashboardDemoV4FloatingNav } from "@/components/dashboard/demo-v4/DashboardDemoV4FloatingNav";
import "@/styles/dashboard-demo-v4.css";

export default function NotFound() {
  return (
    <div className="dashboard-demo-v4-route-shell">
      <main className="dashboard-demo-v4-route-main min-h-dvh bg-slate-950 text-slate-100">
        <section className="mx-auto flex min-h-dvh w-full max-w-4xl flex-col justify-center px-4 pb-[var(--shell-mobile-bottom-reserved-height)] pt-8 sm:px-6 lg:px-8 lg:pb-8">
          <p className="font-mono text-sm font-medium text-rose-300">404</p>
          <h1 className="mt-2 text-4xl font-semibold tracking-normal text-white sm:text-5xl">
            Signal lost in the void
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-300">
            That route does not exist. You mistyped the URL, or something shipped
            without a smoke test. Either way: not your finest moment, but fixable.
          </p>
          <Link
            className="mt-10 inline-block font-mono text-sm text-cyan-300 underline decoration-cyan-300/55 underline-offset-4 transition hover:decoration-cyan-300"
            href="/"
          >
            Return to dashboard
          </Link>
        </section>
      </main>
      <DashboardDemoV4FloatingNav />
    </div>
  );
}
