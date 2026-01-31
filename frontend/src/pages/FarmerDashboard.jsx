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
import ChatInterface from '../components/dashboard/ChatInterface';
import MarketPricePredictor from '../components/dashboard/MarketPricePredictor';
import PestRiskAssessment from '../components/dashboard/PestRiskAssessment';

export default function FarmerDashboard() {
  const [variable, setVariable] = useState(null);
  const [calendar, setCalendar] = useState(null);
  const [loadingVar, setLoadingVar] = useState(false);
  const [loadingCal, setLoadingCal] = useState(false);
  const [error, setError] = useState('');
  const [activeSection, setActiveSection] = useState('variable');
  const [showChat, setShowChat] = useState(false);

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
      if (variable?.location?.state && variable?.location?.city && variable?.crop?.crop_name && variable?.crop?.season) {
        await generateVariable({
          state: variable.location.state,
          city: variable.location.city,
          crop_name: variable.crop.crop_name,
          season: variable.crop.season,
        });
      }
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

  const tabs = [
    { id: 'variable', label: 'Crop plan setup', icon: '🌱' },
    { id: 'calendar-gen', label: 'Generate calendar', icon: '📅' },
    { id: 'daily', label: "Today's tasks", icon: '✅' },
    { id: 'full', label: 'Full calendar', icon: '📋' },
    { id: 'market-price', label: 'Market prices', icon: '💰' },
    { id: 'pest-risk', label: 'Pest & disease risk', icon: '🐛' },
    { id: 'crop', label: 'Crop recommendations', icon: '🌾' },
    { id: 'chat', label: 'Ask Assistant', icon: '💬' },
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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Section with Animation */}
      <div className="flex flex-wrap items-end justify-between gap-4 animate-fade-in">
        <div className="space-y-2">
          <h1 className="font-display text-4xl lg:text-5xl font-bold text-gradient flex items-center gap-3">
            <span className="animate-float">🌾</span>
            Farmer Dashboard
          </h1>
          <p className="text-earth-600 text-lg max-w-2xl">
            Set up your crop plan, generate the calendar, then view today's tasks or the full schedule.
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-earth-600 bg-white/80 backdrop-blur-sm px-4 py-2 rounded-full shadow-elevation-1 border border-farm-200">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-farm-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-farm-500"></span>
          </span>
          <span className="font-medium">Live farm insights</span>
        </div>
      </div>

      {/* Overview Cards with Staggered Animation */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card p-5 animate-rise-in hover:scale-105 transition-transform duration-300" style={{ animationDelay: '0.1s' }}>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-farm-400 to-farm-600 flex items-center justify-center text-2xl shadow-glow">
              📍
            </div>
            <div>
              <p className="text-xs uppercase tracking-wider text-earth-500 font-semibold">Location</p>
              <p className="font-display text-lg font-bold text-earth-800">{overview.location}</p>
            </div>
          </div>
        </div>
        <div className="card p-5 animate-rise-in hover:scale-105 transition-transform duration-300" style={{ animationDelay: '0.2s' }}>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-harvest-400 to-harvest-600 flex items-center justify-center text-2xl shadow-glow-harvest">
              🌱
            </div>
            <div>
              <p className="text-xs uppercase tracking-wider text-earth-500 font-semibold">Crop & Season</p>
              <p className="font-display text-lg font-bold text-earth-800">{overview.crop}</p>
            </div>
          </div>
        </div>
        <div className="card p-5 animate-rise-in hover:scale-105 transition-transform duration-300" style={{ animationDelay: '0.3s' }}>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-farm-500 to-farm-700 flex items-center justify-center text-2xl shadow-glow">
              📆
            </div>
            <div>
              <p className="text-xs uppercase tracking-wider text-earth-500 font-semibold">Cycle Day</p>
              <p className="font-display text-lg font-bold text-earth-800">Day {overview.day}</p>
            </div>
          </div>
        </div>
        <div className="card p-5 animate-rise-in hover:scale-105 transition-transform duration-300" style={{ animationDelay: '0.4s' }}>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-soil-400 to-soil-600 flex items-center justify-center text-2xl shadow-elevation-2">
              ✅
            </div>
            <div>
              <p className="text-xs uppercase tracking-wider text-earth-500 font-semibold">Today's Tasks</p>
              <p className="font-display text-lg font-bold text-earth-800">{overview.stage}</p>
              <p className="text-sm text-farm-600 font-medium">{overview.tasks} tasks</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-[280px_1fr] gap-6">
        {/* Enhanced Sidebar Navigation */}
        <aside className="card p-6 h-fit lg:sticky lg:top-6 animate-slide-in-left">
          <h2 className="font-display text-base font-bold text-earth-700 mb-4 flex items-center gap-2">
            <span className="w-1 h-6 bg-gradient-to-b from-farm-500 to-farm-700 rounded-full"></span>
            Dashboard Sections
          </h2>
          <div className="space-y-2">
            {tabs.map((t, index) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setActiveSection(t.id)}
                className={`w-full flex items-center gap-3 rounded-xl px-4 py-3.5 text-sm font-semibold transition-all duration-300 transform ${
                  activeSection === t.id
                    ? 'bg-gradient-to-r from-farm-600 to-farm-700 text-white shadow-glow scale-105'
                    : 'bg-gradient-to-r from-white to-earth-50 text-earth-700 hover:from-farm-50 hover:to-farm-100 border-2 border-earth-200/80 hover:border-farm-300 hover:scale-102'
                }`}
                aria-current={activeSection === t.id ? 'page' : undefined}
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                <span className={`text-2xl ${activeSection === t.id ? 'animate-bounce-slow' : ''}`}>{t.icon}</span>
                <span className="truncate text-left">{t.label}</span>
              </button>
            ))}
          </div>
          <div className="mt-6 rounded-xl bg-gradient-to-br from-farm-50 to-harvest-50 border-2 border-farm-200 p-4 text-sm animate-pulse-slow">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg">⏱️</span>
              <span className="font-semibold text-earth-700">Cycle Duration</span>
            </div>
            <p className="text-2xl font-display font-bold text-gradient">{overview.cycle} days</p>
          </div>
        </aside>

        <section className="space-y-6 animate-slide-in-right">
          {/* Error Alert with Animation */}
          {error && (
            <div className="rounded-xl bg-gradient-to-r from-red-50 to-red-100 border-2 border-red-200 text-red-700 px-5 py-4 flex items-center justify-between animate-scale-in shadow-elevation-2">
              <div className="flex items-center gap-3">
                <span className="text-2xl">⚠️</span>
                <span className="font-medium">{error}</span>
              </div>
              <button onClick={() => setError('')} className="text-red-500 hover:text-red-700 text-2xl font-bold hover:rotate-90 transition-transform duration-300">
                ×
              </button>
            </div>
          )}

          {/* Loading Indicator with Animation */}
          {(loadingVar || loadingCal) && (
            <div className="card p-5 flex items-center gap-4 text-sm text-earth-600 animate-pulse">
              <div className="relative">
                <div className="h-6 w-6 rounded-full border-3 border-farm-200"></div>
                <div className="absolute top-0 left-0 h-6 w-6 rounded-full border-3 border-farm-500 border-t-transparent animate-spin"></div>
              </div>
              <span className="font-medium">Syncing latest farm data…</span>
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
          {activeSection === 'market-price' && (
            <MarketPricePredictor
              variable={variable}
              loading={loadingVar}
            />
          )}
          {activeSection === 'pest-risk' && (
            <PestRiskAssessment
              variable={variable}
              calendar={calendar}
              loading={loadingVar || loadingCal}
            />
          )}
          {activeSection === 'chat' && (
            <div className="h-[600px]">
              <ChatInterface sessionId="farmer-dashboard" />
            </div>
          )}
          {!loadingVar && !loadingCal && !variable && activeSection !== 'crop' && activeSection !== 'chat' && (
            <SectionLoader title="Getting farm insights" subtitle="Set up your crop plan to start." />
          )}
        </section>
      </div>

      {/* Floating Chat Button */}
      {!showChat && activeSection !== 'chat' && (
        <button
          onClick={() => setShowChat(true)}
          className="fixed bottom-6 right-6 w-16 h-16 bg-gradient-to-br from-farm-500 to-farm-600 text-white rounded-full shadow-elevation-3 hover:shadow-elevation-4 hover:scale-110 transition-all duration-300 flex items-center justify-center group z-50"
          title="Chat with Farming Assistant"
        >
          <span className="text-2xl group-hover:animate-bounce">💬</span>
          {variable && calendar && (
            <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full border-2 border-white animate-pulse"></span>
          )}
        </button>
      )}

      {/* Chat Modal */}
      {showChat && activeSection !== 'chat' && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-2xl h-[80vh] animate-scale-in">
            <ChatInterface 
              sessionId="farmer-dashboard" 
              onClose={() => setShowChat(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
