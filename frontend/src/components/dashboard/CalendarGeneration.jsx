import { useMemo, useState } from 'react';
import SectionLoader from './SectionLoader';

export default function CalendarGeneration({ calendar, variable, onGenerate, onRefresh }) {
  const [generating, setGenerating] = useState(false);

  const previewDays = useMemo(() => {
    return (calendar?.days || []).slice(0, 5);
  }, [calendar]);

  const forecastSnapshot = useMemo(() => {
    return (calendar?.forecast_snapshot || []).slice(0, 16);
  }, [calendar]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await onGenerate();
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {generating && (
        <SectionLoader title="Building calendar" subtitle="Generating day-by-day schedule…" />
      )}
      <div className="card p-6 sm:p-8">
        <div className="flex items-center gap-3 mb-6">
          <span className="text-3xl">📅</span>
          <div>
            <h2 className="font-display text-xl font-bold text-earth-800">Calendar generation</h2>
            <p className="text-earth-600 text-sm">Uses your crop plan + persistent data; creates or remakes the day-by-day calendar</p>
          </div>
        </div>
        {!variable && (
          <div className="rounded-xl bg-amber-50 border border-amber-200 p-4 mb-6 text-amber-800 text-sm">
            Set up your crop plan first so the calendar has location, crop, and climate.
          </div>
        )}
        <div className="flex flex-wrap gap-3">
          <button
            onClick={handleGenerate}
            disabled={generating || !variable}
            className="btn-primary rounded-xl px-6 py-3 disabled:opacity-50"
          >
            {generating ? 'Generating calendar…' : 'Generate / remake calendar'}
          </button>
          <button onClick={onRefresh} className="btn-secondary rounded-xl px-6 py-3">
            Refresh
          </button>
        </div>
      </div>

      {calendar && (
        <div className="card p-6 sm:p-8 space-y-6 animate-fade-in">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <h3 className="font-display font-semibold text-earth-800">Calendar summary</h3>
              <p className="text-earth-500 text-sm">Overview of cycle length, location, and baseline weather.</p>
            </div>
            <button onClick={onRefresh} className="btn-secondary rounded-xl px-4 py-2 text-sm">Refresh</button>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            <div className="rounded-2xl bg-farm-50 p-4">
              <span className="text-earth-500">Cycle range</span>
              <p className="font-semibold text-earth-800">Days {calendar.start_day ?? 1} – {calendar.days?.[calendar.days?.length - 1]?.day_index ?? calendar.cycle_duration_days}</p>
            </div>
            <div className="rounded-2xl bg-earth-50 p-4">
              <span className="text-earth-500">Duration</span>
              <p className="font-semibold text-earth-800">{calendar.cycle_duration_days} days</p>
            </div>
            <div className="rounded-2xl bg-earth-50 p-4">
              <span className="text-earth-500">Crop</span>
              <p className="font-semibold text-earth-800">{calendar.crop?.crop_name} · {calendar.season}</p>
            </div>
            <div className="rounded-2xl bg-earth-50 p-4">
              <span className="text-earth-500">Location</span>
              <p className="font-semibold text-earth-800">{calendar.location?.city}, {calendar.location?.state}</p>
            </div>
          </div>

          {calendar.weather_baseline && (
            <div className="rounded-2xl border border-earth-200 p-4 text-sm">
              <p className="font-semibold text-earth-800 mb-2">Weather baseline</p>
              <div className="flex flex-wrap gap-3 text-earth-600">
                {calendar.weather_baseline.temperature_c != null && (
                  <span>{calendar.weather_baseline.temperature_c}°C</span>
                )}
                {calendar.weather_baseline.humidity_percent != null && (
                  <span>{calendar.weather_baseline.humidity_percent}% humidity</span>
                )}
                {calendar.weather_baseline.rainfall_mm != null && (
                  <span>{calendar.weather_baseline.rainfall_mm} mm rain</span>
                )}
              </div>
            </div>
          )}

          {forecastSnapshot.length > 0 && (
            <div className="rounded-2xl border border-earth-200 p-4">
              <div className="flex items-center justify-between gap-3 mb-3">
                <h4 className="font-semibold text-earth-800">Forecast snapshot (next {forecastSnapshot.length} days)</h4>
                <span className="text-xs text-earth-500">Based on forecast window</span>
              </div>
              <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                {forecastSnapshot.map((f, i) => (
                  <div key={i} className="rounded-xl bg-earth-50 p-3">
                    <p className="font-semibold text-earth-800">Day {i + 1}</p>
                    <p className="text-earth-600">Temp: {f.temperature_c ?? '—'}°C</p>
                    <p className="text-earth-600">Humidity: {f.humidity_percent ?? '—'}%</p>
                    <p className="text-earth-600">Rain: {f.rainfall_mm ?? '—'} mm</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {previewDays.length > 0 && (
            <div className="rounded-2xl border border-earth-200 p-4">
              <h4 className="font-semibold text-earth-800 mb-3">First 5 days preview</h4>
              <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-3 text-xs">
                {previewDays.map((d) => (
                  <div key={d.day_index} className="rounded-xl bg-earth-50 p-3">
                    <p className="font-semibold text-earth-800">Day {d.day_index}</p>
                    <p className="text-earth-600">{d.stage_name}</p>
                    <p className="text-earth-500 mt-1">{(d.tasks || []).length} tasks</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <details className="rounded-2xl border border-earth-200 p-4 text-sm">
            <summary className="cursor-pointer font-semibold text-earth-800">Raw calendar response</summary>
            <pre className="mt-3 whitespace-pre-wrap text-xs text-earth-600 bg-earth-50 rounded-xl p-3 overflow-auto">
              {JSON.stringify(calendar, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </div>
  );
}
