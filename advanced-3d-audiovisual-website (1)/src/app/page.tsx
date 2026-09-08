import { MarketingNav } from "@/components/marketing/MarketingNav";
import { Hero } from "@/components/marketing/Hero";
import { Philosophy } from "@/components/marketing/Philosophy";
import { CouncilGrid } from "@/components/marketing/CouncilGrid";
import { Pipeline } from "@/components/marketing/Pipeline";
import { LiveStats } from "@/components/marketing/LiveStats";
import { FeatureGrid } from "@/components/marketing/FeatureGrid";
import { Roadmap } from "@/components/marketing/Roadmap";
import { CTAFooter } from "@/components/marketing/CTAFooter";

export const dynamic = "force-dynamic";

export default function HomePage() {
  return (
    <main className="relative">
      <MarketingNav />
      <Hero />
      <Philosophy />
      <CouncilGrid />
      <Pipeline />
      <LiveStats />
      <FeatureGrid />
      <Roadmap />
      <CTAFooter />
    </main>
  );
}
