import React from 'react'

const brands = [
  { name: "FRESH & CO", font: "font-bold" },
  { name: "Tasty Treats", font: "font-serif font-bold italic" },
  { name: "ORGANIC", font: "font-light tracking-widest" },
  { name: "GOURMET KITCHEN", font: "font-extrabold text-sm" },
  { name: "artisan", font: "font-bold lowercase" },
]

export const TrustSection: React.FC = () => {
  return (
    <section
      className="w-full py-16 px-4 relative"
      style={{
        background: `
          linear-gradient(to bottom,
            rgba(250, 250, 250, 1) 0%,
            rgba(250, 250, 250, 0.5) 15%,
            rgba(250, 250, 250, 0) 40%,
            rgba(255, 255, 255, 0) 60%,
            rgba(255, 255, 255, 0.5) 85%,
            rgba(255, 255, 255, 1) 100%
          ),
          url('/pixels_bg_rotated.png')
        `,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }}
    >
      <div className="max-w-6xl mx-auto space-y-8">
        <p className="text-center text-base font-medium text-gray-500">
          Trusted by innovative food brands worldwide
        </p>
        <div className="flex flex-wrap items-center justify-center gap-12 opacity-60">
          {brands.map((brand, idx) => (
            <div key={idx} className={`text-2xl text-gray-900 ${brand.font}`}>
              {brand.name}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
