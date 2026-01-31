import SectionLoader from './SectionLoader';

export default function DailyDashboard({ variable, calendar, loading }) {
  const currentDay = variable?.day_of_cycle ?? 1;
  const days = calendar?.days || [];
  const startDay = calendar?.start_day ?? 1;
  const dayIndex = currentDay - startDay;
  const todayEntry = dayIndex >= 0 && dayIndex < days.length ? days[dayIndex] : null;

  if (loading) {
    return (
      <SectionLoader title="Loading today’s tasks" subtitle="Syncing the latest calendar data…" />
    );
  }

  if (!variable) {
    return (
      <div className="card p-8 text-center rounded-2xl bg-amber-50 border border-amber-200">
        <p className="text-amber-800">Set up your crop plan and generate the calendar to see today’s tasks.</p>
      </div>
    );
  }

  if (!todayEntry) {
    return (
      <div className="card p-8">
        <div className="flex items-center gap-3 mb-4">
          <span className="text-3xl">✅</span>
          <h2 className="font-display text-xl font-bold text-earth-800">Today’s tasks (Day {currentDay})</h2>
        </div>
        <div className="rounded-xl bg-earth-50 p-6 text-earth-600">
          No calendar entry for day {currentDay}. Generate or remake the calendar. If your calendar starts after day {currentDay}, complete crop plan setup first.
        </div>
      </div>
    );
  }

  const weather = todayEntry.weather || {};
  const tasks = todayEntry.tasks || [];

  return (
    <div className="space-y-6">
      <div className="card p-6 sm:p-8 animate-fade-in">
        <div className="flex items-center justify-between flex-wrap gap-4 mb-6">
          <div className="flex items-center gap-3">
            <span className="text-3xl">✅</span>
            <div>
              <h2 className="font-display text-xl font-bold text-earth-800">Today’s tasks</h2>
              <p className="text-earth-600 text-sm">Day {todayEntry.day_index} · {todayEntry.stage_name}</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <span className="rounded-full bg-farm-100 text-farm-800 px-3 py-1 text-sm">Stage: {todayEntry.stage_name}</span>
            <span className="rounded-full bg-earth-100 text-earth-700 px-3 py-1 text-sm">Tasks: {tasks.length}</span>
          </div>
        </div>

        <div className="grid sm:grid-cols-3 gap-4 mb-6 text-sm">
          <div className="rounded-2xl bg-earth-50 p-4">
            <p className="text-earth-500">Temperature</p>
            <p className="font-semibold text-earth-800">{weather.temperature_c ?? '—'}°C</p>
          </div>
          <div className="rounded-2xl bg-earth-50 p-4">
            <p className="text-earth-500">Humidity</p>
            <p className="font-semibold text-earth-800">{weather.humidity_percent ?? '—'}%</p>
          </div>
          <div className="rounded-2xl bg-earth-50 p-4">
            <p className="text-earth-500">Rainfall</p>
            <p className="font-semibold text-earth-800">{weather.rainfall_mm ?? '—'} mm</p>
          </div>
        </div>

        <ul className="space-y-3">
          {tasks.length === 0 ? (
            <li className="text-earth-500">No tasks for this day.</li>
          ) : (
            tasks.map((task, i) => (
              <li
                key={i}
                className="flex items-start gap-3 rounded-xl bg-earth-50 hover:bg-farm-50/50 p-4 transition"
              >
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-farm-500 text-white text-xs font-medium flex items-center justify-center">
                  {i + 1}
                </span>
                <span className="text-earth-800">{task}</span>
              </li>
            ))
          )}
        </ul>
      </div>

      <div className="card p-6 grid sm:grid-cols-2 gap-4">
        <div>
          <h3 className="font-display font-semibold text-earth-800 mb-2">Current plan</h3>
          <p className="text-earth-600 text-sm">
            {variable.location?.city}, {variable.location?.state} · {variable.crop?.crop_name} ({variable.crop?.season}) · Day {variable.day_of_cycle}
          </p>
        </div>
        <div>
          <h3 className="font-display font-semibold text-earth-800 mb-2">Stage</h3>
          <p className="text-earth-600 text-sm">{todayEntry.stage_name}</p>
        </div>
      </div>
    </div>
  );
}
