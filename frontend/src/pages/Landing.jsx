import { Link } from 'react-router-dom';

export default function Landing() {
  return (
    <div className="bg-gradient-to-b from-farm-50 via-white to-earth-100">
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg width=\'60\' height=\'60\' viewBox=\'0 0 60 60\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'none\' fill-rule=\'evenodd\'%3E%3Cg fill=\'%2322c55e\' fill-opacity=\'0.06\'%3E%3Cpath d=\'M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E')] opacity-60" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-28">
          <div className="text-center max-w-3xl mx-auto">
            <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold text-earth-800 tracking-tight">
              Smart crop planning for
              <span className="text-farm-600"> Indian farmers</span>
            </h1>
            <p className="mt-6 text-lg text-earth-600">
              Generate location-aware variable data, soil & weather insights, and a day-by-day crop calendar—all in one place.
            </p>
            <div className="mt-10 flex flex-wrap justify-center gap-4">
              <Link to="/register" className="btn-primary text-lg px-8 py-3 rounded-2xl">
                Get started
              </Link>
              <Link to="/login" className="btn-secondary text-lg px-8 py-3 rounded-2xl">
                Sign in
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* System info */}
      <section className="py-16 sm:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="font-display text-3xl font-bold text-earth-800 text-center mb-12">
            How the system works
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                title: 'Variable generation',
                desc: 'Enter state, city, crop, and season. We fetch soil (SoilGrids), weather (Open-Meteo), and geocode your location to build variable.json.',
                icon: '🌱',
              },
              {
                title: 'Crop & persistent data',
                desc: 'Crop timeline and stages come from persistent.json (state-wise). Missing crops are enriched via trusted government sources.',
                icon: '📋',
              },
              {
                title: 'Calendar agent',
                desc: 'An AI agent generates a full day-by-day crop calendar with tasks, stages, and a 16-day weather window. Regenerates when conditions cross thresholds.',
                icon: '📅',
              },
              {
                title: 'Daily & full view',
                desc: 'View today’s tasks or browse the entire calendar. Plan from day 1; no real dates—just cycle days and weather-aware recommendations.',
                icon: '✅',
              },
            ].map((item, i) => (
              <div key={i} className="card p-6 hover:shadow-glow transition-shadow">
                <span className="text-3xl mb-3 block">{item.icon}</span>
                <h3 className="font-display font-semibold text-earth-800 text-lg">{item.title}</h3>
                <p className="mt-2 text-earth-600 text-sm leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-farm-600">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <h2 className="font-display text-2xl sm:text-3xl font-bold text-white">
            Ready to plan your crop cycle?
          </h2>
          <p className="mt-4 text-farm-100">
            Register, log in, and use the farmer dashboard to generate variables and your calendar.
          </p>
          <Link
            to="/register"
            className="mt-6 inline-flex items-center rounded-xl px-6 py-3 font-medium text-farm-600 bg-white hover:bg-farm-50 transition"
          >
            Create account
          </Link>
        </div>
      </section>

      <footer className="py-8 text-center text-earth-500 text-sm">
        Crop Calendar · Smart Farming · No current dates stored
      </footer>
    </div>
  );
}
