import { useState } from 'react';

export default function CalendarGeneration({ calendar, variable, onGenerate, onRefresh }) {
  const [generating, setGenerating] = useState(false);

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
            Set up your crop plan first (step 1) so the calendar has location, crop, and climate.
          </div>
        )}
        <div className="flex gap-3">
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
        <div className="card p-6">
          <h3 className="font-display font-semibold text-earth-800 mb-4">Calendar summary</h3>
          <div className="flex flex-wrap gap-4 text-sm">
            <span className="rounded-full bg-farm-100 text-farm-800 px-3 py-1">
              Days: {calendar.start_day ?? 1} – {calendar.days?.[calendar.days?.length - 1]?.day_index ?? calendar.cycle_duration_days}
            </span>
            <span className="rounded-full bg-earth-100 text-earth-700 px-3 py-1">
              Cycle: {calendar.cycle_duration_days} days
            </span>
            <span className="rounded-full bg-earth-100 text-earth-700 px-3 py-1">
              Crop: {calendar.crop?.crop_name} · {calendar.season}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
