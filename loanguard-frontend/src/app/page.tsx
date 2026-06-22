import { Hero } from "@/components/landing/Hero";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { RiskCategoryPreview } from "@/components/landing/RiskCategoryPreview";
import { StatsBar } from "@/components/landing/StatsBar";
import { Footer } from "@/components/landing/Footer";

export default function LandingPage() {
  return (
    <main>
      <Hero />
      <StatsBar />
      <HowItWorks />
      <RiskCategoryPreview />
      <Footer />
    </main>
  );
}
