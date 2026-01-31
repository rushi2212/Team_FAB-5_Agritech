import { useState, useEffect, useMemo } from 'react';
import {
  generateVariable,
  getVariable,
  getCalendar,
  generateCalendar,
  updateDayOfCycle,
} from '../api';
import CropSelection from '../components/dashboard/CropSelection';
import VariableGeneration from '../components/dashboard/VariableGeneration';
import CalendarGeneration from '../components/dashboard/CalendarGeneration';
import DailyDashboard from '../components/dashboard/DailyDashboard';
import FullCalendar from '../components/dashboard/FullCalendar';
import SectionLoader from '../components/dashboard/SectionLoader';

export default function FarmerDashboard() {
  const [variable, setVariable] = useState(null);
  const [calendar, setCalendar] = useState(null);
  const [loadingVar, setLoadingVar] = useState(false);
  const [loadingCal, setLoadingCal] = useState(false);
  const [error, setError] = useState('');
  const [activeSection, setActiveSection] = useState('variable');

  const loadVariable = () => {
    setLoadingVar(true);
    setError('');
    getVariable()
      .then(setVariable)
      .catch((e) => setError(e.message))
      .finally(() => setLoadingVar(false));
  };

  const loadCalendar = () => {
    setLoadingCal(true);
    setError('');
    getCalendar()
      .then(setCalendar)
      .catch((e) => setError(e.message))
      .finally(() => setLoadingCal(false));
  };

  useEffect(() => {
    loadVariable();
    loadCalendar();
  }, []);

  const handleGenerateVariable = async (body) => {
    setError('');
    try {
      await generateVariable(body);
      loadVariable();
    } catch (e) {
      setError(e.message);
    }
  };

  const handleGenerateCalendar = async () => {
    setError('');
    try {
      const data = await generateCalendar();
      setCalendar(data);
    } catch (e) {
      setError(e.message);
    }
  };

  const handleMarkAsDone = async (cycleDay) => {
    setError('');
    try {
      // 1) Refresh variable.json (weather, soil, etc.) via generate-variable
      if (variable?.location?.state && variable?.location?.city && variable?.crop?.crop_name && variable?.crop?.season) {
        await generateVariable({
          state: variable.location.state,
          city: variable.location.city,
          crop_name: variable.crop.crop_name,
          season: variable.crop.season,
        });
      }
      // 2) Set day_of_cycle to the calendar day the user clicked (e.g. 11)
      await updateDayOfCycle(cycleDay);
      loadVariable();
      loadCalendar();
    } catch (e) {
      setError(e.message);
      throw e;
    }
  };

  const handleCheckThreshold = async () => {
    setError('');
    try {
      const data = await generateCalendar();
      setCalendar(data);
      loadCalendar();
    } catch (e) {
      setError(e.message);
      throw e;
    }
  };

  // MVP flow: Plan → Calendar → Today → Full view → Recommendations
  const tabs = [
    { id: 'variable', label: 'Crop plan setup', icon: '🌱' },
    { id: 'calendar-gen', label: 'Generate calendar', icon: '📅' },
    { id: 'daily', label: "Today's tasks", icon: '✅' },
    { id: 'full', label: 'Full calendar', icon: '📋' },
    { id: 'crop', label: 'Crop recommendations', icon: '🌾' },
  ];

  const overview = useMemo(() => {
    const currentDay = variable?.day_of_cycle ?? null;
    const startDay = calendar?.start_day ?? 1;
    const days = calendar?.days || [];
    const dayIndex = currentDay != null ? currentDay - startDay : null;
    const todayEntry = dayIndex != null && dayIndex >= 0 && dayIndex < days.length ? days[dayIndex] : null;
    return {
      location: variable?.location?.city && variable?.location?.state ? `${variable.location.city}, ${variable.location.state}` : '—',
      crop: variable?.crop?.crop_name ? `${variable.crop.crop_name} · ${variable.crop.season}` : '—',
      day: currentDay ?? '—',
      tasks: todayEntry?.tasks?.length ?? 0,
      stage: todayEntry?.stage_name ?? '—',
      cycle: calendar?.cycle_duration_days ?? '—',
    };
  }, [variable, calendar]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-wrap items-end justify-between gap-4 mb-6">
        <div>
          <h1 className="font-display text-3xl font-bold text-earth-800">Farmer dashboard</h1>
          <p className="text-earth-600 mt-2">
            Set up your crop plan, generate the calendar, then view today’s tasks or the full schedule.
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-earth-500">
          <span className="inline-flex h-2 w-2 rounded-full bg-farm-500 animate-pulse" />
          Live farm insights
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        <div className="card p-4 animate-rise-in">
          <p className="text-xs uppercase tracking-wide text-earth-500">Location</p>
          <p className="mt-2 font-semibold text-earth-800">{overview.location}</p>
        </div>
        <div className="card p-4 animate-rise-in">
          <p className="text-xs uppercase tracking-wide text-earth-500">Crop & Season</p>
          <p className="mt-2 font-semibold text-earth-800">{overview.crop}</p>
        </div>
        <div className="card p-4 animate-rise-in">
          <p className="text-xs uppercase tracking-wide text-earth-500">Cycle day</p>
          <p className="mt-2 font-semibold text-earth-800">Day {overview.day}</p>
        </div>
        <div className="card p-4 animate-rise-in">
          <p className="text-xs uppercase tracking-wide text-earth-500">Today</p>
          <p className="mt-2 font-semibold text-earth-800">{overview.stage} · {overview.tasks} tasks</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-[250px_1fr] gap-6">
        <aside className="card p-4 h-fit lg:sticky lg:top-6">
          <h2 className="font-display text-sm font-semibold text-earth-600 mb-3">Dashboard sections</h2>
          <div className="space-y-2">
            {tabs.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setActiveSection(t.id)}
                className={`w-full flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${activeSection === t.id
                  ? 'bg-farm-600 text-white shadow-glow'
                  : 'bg-white text-earth-700 hover:bg-farm-100 border border-earth-200/80'
                  }`}
                aria-current={activeSection === t.id ? 'page' : undefined}
              >
                <span className="text-lg">{t.icon}</span>
                <span className="truncate">{t.label}</span>
              </button>
            ))}
          </div>
          <div className="mt-6 rounded-xl bg-farm-50 border border-farm-200 p-3 text-xs text-earth-600">
            Cycle length: <span className="font-semibold text-earth-800">{overview.cycle} days</span>
          </div>
        </aside>

        <section className="space-y-6">
          {error && (
            <div className="rounded-xl bg-red-50 border border-red-200 text-red-700 px-4 py-3 flex items-center justify-between animate-fade-in">
              <span>{error}</span>
              <button onClick={() => setError('')} className="text-red-500 hover:text-red-700">
                ×
              </button>
            </div>
          )}

          {(loadingVar || loadingCal) && (
            <div className="card p-4 flex items-center gap-3 text-sm text-earth-600">
              <div className="h-5 w-5 rounded-full border-2 border-farm-500 border-t-transparent animate-spin" />
              Syncing latest farm data…
            </div>
          )}

          {activeSection === 'crop' && (
            <CropSelection onSelect={() => { }} />
          )}
          {activeSection === 'variable' && (
            <VariableGeneration
              variable={variable}
              loading={loadingVar}
              onGenerate={handleGenerateVariable}
              onRefresh={loadVariable}
            />
          )}
          {activeSection === 'calendar-gen' && (
            <CalendarGeneration
              calendar={calendar}
              variable={variable}
              onGenerate={handleGenerateCalendar}
              onRefresh={loadCalendar}
            />
          )}
          {activeSection === 'daily' && (
            <DailyDashboard variable={variable} calendar={calendar} loading={loadingVar || loadingCal} />
          )}
          {activeSection === 'full' && (
            <FullCalendar
              calendar={calendar}
              loading={loadingCal}
              onRefresh={loadCalendar}
              onMarkAsDone={handleMarkAsDone}
              onCheckThreshold={handleCheckThreshold}
            />
          )}
          {!loadingVar && !loadingCal && !variable && activeSection !== 'crop' && (
            <SectionLoader title="Getting farm insights" subtitle="Set up your crop plan to start." />
          )}
        </section>
      </div>
    </div>
  );
}
