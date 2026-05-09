import Link from "next/link";
import { LayoutOrchestrator } from "@/components/layouts/LayoutOrchestrator";

export default function NotFound() {
  return (
    <LayoutOrchestrator mode="cinematic">
      <p className="font-mono text-sm font-medium text-rose/95">404</p>
      <h1 className="mt-2 text-h1 font-semibold tracking-tight text-chalk">
        Signal lost in the void
      </h1>
      <p className="mt-4 max-w-2xl text-body text-chalk/[0.9]">
        That route does not exist. You mistyped the URL, or something shipped
        without a smoke test. Either way: not your finest moment, but fixable.
      </p>
      <Link
        href="/"
        className="mt-10 inline-block font-mono text-cyan underline decoration-cyan/55 underline-offset-4 transition hover:decoration-cyan"
      >
        ← Return to dashboard
      </Link>
    </LayoutOrchestrator>
  );
}
