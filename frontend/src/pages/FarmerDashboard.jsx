import { useState, useEffect } from 'react';
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

  // MVP flow: 1 Plan → 2 Calendar → 3 Today → 4 Full view → 5 Recommendations
  const tabs = [
    { id: 'variable', label: '1. Crop plan setup', icon: '🌱', step: 1 },
    { id: 'calendar-gen', label: '2. Generate calendar', icon: '📅', step: 2 },
    { id: 'daily', label: "3. Today's tasks", icon: '✅', step: 3 },
    { id: 'full', label: '4. Full calendar', icon: '📋', step: 4 },
    { id: 'crop', label: '5. Crop recommendations', icon: '🌾', step: 5 },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="font-display text-3xl font-bold text-earth-800 mb-2">Farmer dashboard</h1>
      <p className="text-earth-600 mb-6">
        Set up your crop plan, generate the calendar, then view today’s tasks or the full schedule.
      </p>

      {/* MVP steps overview */}
      <div className="grid grid-cols-2 sm:flex sm:flex-wrap gap-2 sm:gap-3 mb-6 p-4 rounded-2xl bg-farm-50/80 border border-farm-200/80">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setActiveSection(t.id)}
            className={`flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition ${activeSection === t.id
              ? 'bg-farm-600 text-white shadow-glow'
              : 'bg-white text-earth-700 hover:bg-farm-100 border border-earth-200/80'
              }`}
          >
            <span>{t.step}</span>
            <span className="truncate">{t.label.replace(/^\d\.\s/, '')}</span>
          </button>
        ))}
      </div>

      {error && (
        <div className="mb-6 rounded-xl bg-red-50 border border-red-200 text-red-700 px-4 py-3 flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError('')} className="text-red-500 hover:text-red-700">
            ×
          </button>
        </div>
      )}

      {/* Sections */}
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
    </div>
  );
}
