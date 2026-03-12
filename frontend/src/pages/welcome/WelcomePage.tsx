import { TopBanner } from '@/components/landing/TopBanner'
import { Hero } from '@/components/landing/Hero'
import { TrustSection } from '@/components/landing/TrustSection'
import { HowItWorksSection } from '@/components/landing/HowItWorksSection'
import { FeaturesGrid } from '@/components/landing/FeaturesGrid'
import { StatsSection } from '@/components/landing/StatsSection'
import { ComparisonSection } from '@/components/landing/ComparisonSection'
import { ResourcesSection } from '@/components/landing/ResourcesSection'
import { CTASection } from '@/components/landing/CTASection'
import { Footer } from '@/components/landing/Footer'

export default function WelcomePage() {
  return (
    <div className="min-h-screen bg-white">
      <TopBanner text="FlavorFlow partners with top POS providers for seamless integration. Learn more →" />
      {/* <Header /> */}
      <Hero />
      <TrustSection />
      <HowItWorksSection />
      <FeaturesGrid />
      <StatsSection />
      <ComparisonSection />
      <ResourcesSection />
      <CTASection />
      <Footer />
    </div>
  )
}
