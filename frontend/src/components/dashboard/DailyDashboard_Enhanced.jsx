import SectionLoader from './SectionLoader';

export default function DailyDashboard({ variable, calendar, loading }) {
  const currentDay = variable?.day_of_cycle ?? 1;
  const days = calendar?.days || [];
  const startDay = calendar?.start_day ?? 1;
  const dayIndex = currentDay - startDay;
  const todayEntry = dayIndex >= 0 && dayIndex < days.length ? days[dayIndex] : null;

  if (loading) {
    return (
      <SectionLoader title="Loading today's tasks" subtitle="Syncing the latest calendar data…" />
    );
  }

  if (!variable) {
    return (
      <div className="card p-8 text-center rounded-2xl bg-gradient-to-br from-amber-50 to-harvest-50 border-2 border-amber-200 animate-scale-in">
        <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-amber-400 to-harvest-600 flex items-center justify-center text-4xl shadow-glow-harvest">
          ⚠️
        </div>
        <p className="text-amber-800 font-semibold text-lg">Set up your crop plan and generate the calendar to see today's tasks.</p>
      </div>
    );
  }

  if (!todayEntry) {
    return (
      <div className="card p-8 animate-fade-in">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-farm-400 to-farm-600 flex items-center justify-center text-3xl shadow-glow">
            ✅
          </div>
          <h2 className="font-display text-2xl font-bold text-gradient">Today's Tasks (Day {currentDay})</h2>
        </div>
        <div className="rounded-xl bg-gradient-to-br from-earth-50 to-farm-50 p-8 text-earth-600 border-2 border-earth-200">
          <p className="font-medium text-lg">No calendar entry for day {currentDay}.</p>
          <p className="mt-2">Generate or remake the calendar. If your calendar starts after day {currentDay}, complete crop plan setup first.</p>
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
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-farm-400 to-farm-600 flex items-center justify-center text-3xl shadow-glow animate-pulse-slow">
              ✅
            </div>
            <div>
              <h2 className="font-display text-2xl font-bold text-gradient">Today's Tasks</h2>
              <p className="text-earth-600 text-sm font-medium mt-1">
                Day {todayEntry.day_index} · <span className="text-farm-600">{todayEntry.stage_name}</span>
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <span className="badge-farm text-sm px-4 py-2">
              <span className="text-base mr-1">🌱</span>
              {todayEntry.stage_name}
            </span>
            <span className="badge-harvest text-sm px-4 py-2">
              <span className="text-base mr-1">✓</span>
              {tasks.length} Tasks
            </span>
          </div>
        </div>

        {/* Weather Cards with Gradient */}
        <div className="grid sm:grid-cols-3 gap-4 mb-6">
          <div className="rounded-2xl bg-gradient-to-br from-farm-50 to-farm-100 border-2 border-farm-200 p-5 hover:scale-105 transition-transform duration-300">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">🌡️</span>
              <p className="text-sm text-earth-600 font-semibold">Temperature</p>
            </div>
            <p className="text-2xl font-display font-bold text-gradient">{weather.temperature_c ?? '—'}°C</p>
          </div>
          <div className="rounded-2xl bg-gradient-to-br from-farm-50 to-farm-100 border-2 border-farm-200 p-5 hover:scale-105 transition-transform duration-300">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">💧</span>
              <p className="text-sm text-earth-600 font-semibold">Humidity</p>
            </div>
            <p className="text-2xl font-display font-bold text-gradient">{weather.humidity_percent ?? '—'}%</p>
          </div>
          <div className="rounded-2xl bg-gradient-to-br from-farm-50 to-farm-100 border-2 border-farm-200 p-5 hover:scale-105 transition-transform duration-300">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">🌧️</span>
              <p className="text-sm text-earth-600 font-semibold">Rainfall</p>
            </div>
            <p className="text-2xl font-display font-bold text-gradient">{weather.rainfall_mm ?? '—'} mm</p>
          </div>
        </div>

        {/* Task List with Modern Styling */}
        <div>
          <h3 className="font-display font-bold text-earth-800 mb-4 flex items-center gap-2">
            <span className="w-1 h-6 bg-gradient-to-b from-farm-500 to-farm-700 rounded-full"></span>
            Tasks for Today
          </h3>
          <ul className="space-y-3">
            {tasks.length === 0 ? (
              <li className="text-earth-500 text-center py-8 rounded-xl bg-earth-50 border-2 border-earth-200">
                🎉 No tasks scheduled for today
              </li>
            ) : (
              tasks.map((task, i) => (
                <li
                  key={i}
                  className="group flex items-start gap-4 rounded-2xl bg-gradient-to-r from-white to-earth-50 hover:from-farm-50 hover:to-harvest-50 border-2 border-earth-200 hover:border-farm-300 p-5 transition-all duration-300 hover:scale-102 hover:shadow-elevation-2 animate-rise-in"
                  style={{ animationDelay: `${i * 0.1}s` }}
                >
                  <span className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-farm-500 to-farm-700 text-white text-sm font-bold flex items-center justify-center shadow-glow group-hover:scale-110 transition-transform duration-300">
                    {i + 1}
                  </span>
                  <span className="text-earth-800 font-medium text-lg leading-relaxed flex-1">{task}</span>
                  <span className="text-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300">✓</span>
                </li>
              ))
            )}
          </ul>
        </div>
      </div>

      {/* Summary Card */}
      <div className="card p-6 grid sm:grid-cols-2 gap-6 animate-fade-in" style={{ animationDelay: '0.2s' }}>
        <div className="rounded-xl bg-gradient-to-br from-farm-50 to-harvest-50 border-2 border-farm-200 p-5">
          <h3 className="font-display font-bold text-earth-800 mb-3 flex items-center gap-2">
            <span className="text-2xl">📍</span>
            Current Plan
          </h3>
          <p className="text-earth-700 font-medium leading-relaxed">
            {variable.location?.city}, {variable.location?.state} · <span className="text-farm-600 font-bold">{variable.crop?.crop_name}</span> ({variable.crop?.season}) · <span className="text-harvest-600 font-bold">Day {variable.day_of_cycle}</span>
          </p>
        </div>
        <div className="rounded-xl bg-gradient-to-br from-soil-50 to-earth-100 border-2 border-soil-200 p-5">
          <h3 className="font-display font-bold text-earth-800 mb-3 flex items-center gap-2">
            <span className="text-2xl">🌱</span>
            Growth Stage
          </h3>
          <p className="text-xl font-display font-bold text-gradient">{todayEntry.stage_name}</p>
        </div>
      </div>
    </div>
  );
}
