import CodingAgentInterface from "@/components/coding/CodingAgentInterface";

export default function ProxyBackendPage() {
  return (
    <main className="min-h-dvh bg-slate-950">
      <CodingAgentInterface layoutMode="backend-console" />
    </main>
  );
}
