export default function SectionLoader({ title = 'Loading', subtitle = 'Fetching latest data…' }) {
  return (
    <div className="card p-10 flex flex-col items-center justify-center text-center animate-fade-in">
      <div className="relative">
        <div className="h-12 w-12 rounded-full border-2 border-farm-500 border-t-transparent animate-spin" />
        <div className="absolute -inset-3 rounded-full bg-farm-100/60 blur-xl" />
      </div>
      <h3 className="mt-4 font-display text-lg font-semibold text-earth-800">{title}</h3>
      <p className="text-earth-500 text-sm mt-1">{subtitle}</p>
    </div>
  );
}
