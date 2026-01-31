import { useState, useMemo, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { analyzeImage, generateCalendarWithDiseaseAnalysis } from '../../api';
import SectionLoader from './SectionLoader';

/** Normalize analysis text so unicode bullets (• ●) become markdown list items for proper rendering */
function normalizeAnalysisMarkdown(text) {
  if (!text || typeof text !== 'string') return text;
  return text.replace(/(^|\n)([•●])\s+/g, '$1- ');
}

const analysisMarkdownComponents = {
  h1: ({ children, ...props }) => <h1 className="text-lg font-bold text-earth-800 mt-3 mb-1" {...props}>{children}</h1>,
  h2: ({ children, ...props }) => <h2 className="text-base font-bold text-earth-800 mt-3 mb-1" {...props}>{children}</h2>,
  h3: ({ children, ...props }) => <h3 className="text-sm font-semibold text-earth-800 mt-3 mb-1" {...props}>{children}</h3>,
  h4: ({ children, ...props }) => <h4 className="text-sm font-semibold text-earth-800 mt-2 mb-1" {...props}>{children}</h4>,
  p: ({ children, ...props }) => <p className="text-earth-700 mb-2 text-sm leading-relaxed" {...props}>{children}</p>,
  strong: ({ children, ...props }) => <strong className="font-semibold text-earth-800" {...props}>{children}</strong>,
  em: ({ children, ...props }) => <em className="italic" {...props}>{children}</em>,
  ul: ({ children, ...props }) => <ul className="list-disc pl-5 mb-3 space-y-1.5 text-earth-700 text-sm" {...props}>{children}</ul>,
  ol: ({ children, ...props }) => <ol className="list-decimal pl-5 mb-3 space-y-1.5 text-earth-700 text-sm" {...props}>{children}</ol>,
  li: ({ children, ...props }) => <li className="text-earth-700 pl-1 leading-relaxed" {...props}>{children}</li>,
};

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

function getDaysInMonth(year, month) {
  const first = new Date(year, month, 1);
  const last = new Date(year, month + 1, 0);
  const startPad = first.getDay();
  const daysInMonth = last.getDate();
  const totalCells = Math.ceil((startPad + daysInMonth) / 7) * 7;
  const cells = [];
  for (let i = 0; i < totalCells; i++) {
    const dayOfGrid = i - startPad + 1;
    const isCurrentMonth = dayOfGrid >= 1 && dayOfGrid <= daysInMonth;
    const date = isCurrentMonth ? new Date(year, month, dayOfGrid) : null;
    cells.push({ dayOfGrid: isCurrentMonth ? dayOfGrid : null, date, isCurrentMonth, key: i });
  }
  return cells;
}

function dateToKey(d) {
  if (!d) return '';
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function diffDays(a, b) {
  const start = new Date(a.getFullYear(), a.getMonth(), a.getDate());
  const end = new Date(b.getFullYear(), b.getMonth(), b.getDate());
  return Math.round((end - start) / (1000 * 60 * 60 * 24));
}

export default function FullCalendar({ calendar, loading, onRefresh, onMarkAsDone, onCheckThreshold }) {
  const [viewDate, setViewDate] = useState(() => new Date());
  const [markAsDoneLoading, setMarkAsDoneLoading] = useState(false);
  const [checkThresholdLoading, setCheckThresholdLoading] = useState(false);
  const [panelError, setPanelError] = useState('');
  const [markedDays, setMarkedDays] = useState(() => new Set());
  const [cycleStartDate, setCycleStartDate] = useState(() => {
    const d = new Date();
    d.setDate(1);
    return dateToKey(d);
  });
  const [selectedDay, setSelectedDay] = useState(null);
  const [diseaseAnalysis, setDiseaseAnalysis] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [regenerateLoading, setRegenerateLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState('');
  const [recalibrateSuccess, setRecalibrateSuccess] = useState(false);
  const fileInputRef = useRef(null);

  const days = calendar?.days || [];
  const startDay = calendar?.start_day ?? 1;
  const cycleDuration = calendar?.cycle_duration_days ?? 120;
  const dayByIndex = useMemo(() => {
    const map = {};
    days.forEach((d) => { map[d.day_index] = d; });
    return map;
  }, [days]);

  const cycleStart = useMemo(() => {
    if (!cycleStartDate) return null;
    const [y, m, d] = cycleStartDate.split('-').map(Number);
    return new Date(y, m - 1, d);
  }, [cycleStartDate]);

  const grid = useMemo(() => {
    return getDaysInMonth(viewDate.getFullYear(), viewDate.getMonth());
  }, [viewDate]);

  const getDayDataForDate = (date) => {
    if (!date || !cycleStart) return null;
    const dayOffset = diffDays(cycleStart, date);
    const cycleDay = dayOffset + 1;
    if (cycleDay < startDay || cycleDay > startDay + days.length - 1) return null;
    return { cycleDay, data: dayByIndex[cycleDay] };
  };

  const goPrevMonth = () => {
    setViewDate((d) => new Date(d.getFullYear(), d.getMonth() - 1));
  };
  const goNextMonth = () => {
    setViewDate((d) => new Date(d.getFullYear(), d.getMonth() + 1));
  };
  const goToday = () => {
    setViewDate(new Date());
  };

  const closeModal = () => {
    setSelectedDay(null);
    setPanelError('');
  };

  const handleMarkAsDone = async () => {
    if (!selectedInfo?.cycleDay || !onMarkAsDone) return;
    setPanelError('');
    setMarkAsDoneLoading(true);
    try {
      await onMarkAsDone(selectedInfo.cycleDay);
      await onRefresh();
      setMarkedDays((prev) => {
        const next = new Set(prev);
        next.add(selectedInfo.cycleDay);
        return next;
      });
    } catch (e) {
      setPanelError(e.message || 'Mark as done failed');
    } finally {
      setMarkAsDoneLoading(false);
    }
  };

  const handleCheckThreshold = async () => {
    if (!onCheckThreshold) return;
    setPanelError('');
    setCheckThresholdLoading(true);
    try {
      await onCheckThreshold();
      await onRefresh();
    } catch (e) {
      setPanelError(e.message || 'Check threshold failed');
    } finally {
      setCheckThresholdLoading(false);
    }
  };

  const handleImageSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAnalysisError('');
    setDiseaseAnalysis(null);
    setAnalysisLoading(true);
    try {
      const { analysis } = await analyzeImage(file);
      setDiseaseAnalysis(analysis);
    } catch (err) {
      setAnalysisError(err.message || 'Analysis failed');
    } finally {
      setAnalysisLoading(false);
      e.target.value = '';
    }
  };

  const handleRecalibrateCalendar = async () => {
    if (!diseaseAnalysis?.trim()) return;
    setAnalysisError('');
    setRecalibrateSuccess(false);
    setRegenerateLoading(true);
    try {
      await generateCalendarWithDiseaseAnalysis(diseaseAnalysis);
      if (onRefresh) await onRefresh();
      setRecalibrateSuccess(true);
      setTimeout(() => setRecalibrateSuccess(false), 5000);
    } catch (err) {
      setAnalysisError(err.message || 'Recalibration failed');
    } finally {
      setRegenerateLoading(false);
    }
  };

  if (loading) {
    return (
      <SectionLoader title="Loading full calendar" subtitle="Preparing your cycle overview…" />
    );
  }

  if (!calendar || days.length === 0) {
    return (
      <div className="card p-8 text-center rounded-2xl bg-amber-50 border border-amber-200">
        <p className="text-amber-800">No calendar yet. Set up your crop plan and generate the calendar.</p>
        <button onClick={onRefresh} className="btn-secondary mt-4 rounded-xl">Refresh</button>
      </div>
    );
  }

  const selectedInfo = selectedDay ? getDayDataForDate(selectedDay) : null;
  const selectedData = selectedInfo?.data;

  return (
    <div className="space-y-6">
      <div className="card p-6 sm:p-8 animate-fade-in">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <span className="text-3xl">📋</span>
            <div>
              <h2 className="font-display text-xl font-bold text-earth-800">Full calendar</h2>
              <p className="text-earth-600 text-sm">
                {calendar.crop?.crop_name} · {calendar.season} · Cycle days {calendar.start_day ?? 1}–{days[days.length - 1]?.day_index}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/gif,image/webp"
              onChange={handleImageSelect}
              className="hidden"
              aria-label="Upload image for disease analysis"
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={analysisLoading}
              className="btn-secondary rounded-xl px-4 py-2 text-sm disabled:opacity-50 flex items-center gap-2"
            >
              {analysisLoading ? (
                <>Analyzing…</>
              ) : (
                <>🖼️ Upload image</>
              )}
            </button>
            <button onClick={onRefresh} className="btn-secondary rounded-xl px-4 py-2 text-sm">Refresh</button>
          </div>
        </div>

        {analysisError && (
          <div className="mb-4 rounded-xl bg-red-50 text-red-700 px-3 py-2 text-sm">{analysisError}</div>
        )}

        {recalibrateSuccess && (
          <div className="mb-4 rounded-xl bg-green-50 text-green-800 px-3 py-2 text-sm font-medium">
            Calendar recalibrated successfully. The new calendar has replaced the previous one.
          </div>
        )}

        {diseaseAnalysis && (
          <div className="mb-6 rounded-2xl border border-amber-200 bg-amber-50/50 p-4">
            <h4 className="font-semibold text-earth-800 mb-2">Disease / field analysis</h4>
            <p className="text-earth-600 text-xs mb-2">Full analysis from uploaded image (Tavily + government sources). Use the button below to re-run the pipeline and replace the calendar with disease-weighted tasks.</p>
            <div className="text-sm text-earth-700 max-h-64 overflow-y-auto mb-4 pr-2 rounded-lg bg-white/60 p-3 border border-amber-100 max-w-none">
              <ReactMarkdown components={analysisMarkdownComponents}>{normalizeAnalysisMarkdown(diseaseAnalysis)}</ReactMarkdown>
            </div>
            <button
              type="button"
              onClick={handleRecalibrateCalendar}
              disabled={regenerateLoading}
              className="btn-primary rounded-xl px-4 py-2 text-sm disabled:opacity-50"
            >
              {regenerateLoading ? 'Recalibrating…' : 'Recalibrate calendar'}
            </button>
            <p className="text-earth-500 text-xs mt-2">Re-evaluates the full pipeline (variable + persistent + past days + this analysis) and replaces the calendar with disease management given more weight.</p>
          </div>
        )}

        <div className="grid sm:grid-cols-3 gap-4 mb-6 text-sm">
          <div className="rounded-2xl bg-earth-50 p-4">
            <p className="text-earth-500">Cycle duration</p>
            <p className="font-semibold text-earth-800">{cycleDuration} days</p>
          </div>
          <div className="rounded-2xl bg-earth-50 p-4">
            <p className="text-earth-500">Forecast window</p>
            <p className="font-semibold text-earth-800">{calendar.forecast_days ?? '—'} days</p>
          </div>
          <div className="rounded-2xl bg-earth-50 p-4">
            <p className="text-earth-500">Location</p>
            <p className="font-semibold text-earth-800">{calendar.location?.city}, {calendar.location?.state}</p>
          </div>
        </div>

        {/* Cycle start date: map cycle day 1 to this date */}
        <div className="mb-6 flex flex-wrap items-center gap-3">
          <label className="text-sm font-medium text-earth-700">Cycle start date (Day 1 = this date):</label>
          <input
            type="date"
            value={cycleStartDate}
            onChange={(e) => setCycleStartDate(e.target.value)}
            className="input-field w-auto max-w-[180px] py-2"
          />
        </div>

        {/* Month navigation */}
        <div className="flex items-center justify-between mb-4">
          <button
            type="button"
            onClick={goPrevMonth}
            className="rounded-xl p-2 text-earth-600 hover:bg-earth-100 font-medium transition"
            aria-label="Previous month"
          >
            ← Prev
          </button>
          <h3 className="font-display text-lg font-semibold text-earth-800">
            {MONTHS[viewDate.getMonth()]} {viewDate.getFullYear()}
          </h3>
          <button
            type="button"
            onClick={goNextMonth}
            className="rounded-xl p-2 text-earth-600 hover:bg-earth-100 font-medium transition"
            aria-label="Next month"
          >
            Next →
          </button>
        </div>
        <button
          type="button"
          onClick={goToday}
          className="text-sm text-farm-600 hover:underline mb-4 block"
        >
          Go to today
        </button>

        {/* Calendar grid */}
        <div className="border border-earth-200 rounded-2xl overflow-hidden shadow-sm">
          <div className="grid grid-cols-7 bg-earth-100 border-b border-earth-200">
            {WEEKDAYS.map((wd) => (
              <div
                key={wd}
                className="py-2 text-center text-xs font-semibold text-earth-600 uppercase tracking-wider"
              >
                {wd}
              </div>
            ))}
          </div>
          <div className="grid grid-cols-7 bg-white">
            {grid.map((cell) => {
              const dayData = cell.date ? getDayDataForDate(cell.date) : null;
              const isSelected = selectedDay && cell.date && dateToKey(selectedDay) === dateToKey(cell.date);
              const isToday = cell.date && dateToKey(cell.date) === dateToKey(new Date());
              return (
                <button
                  key={cell.key}
                  type="button"
                  onClick={() => cell.date && setSelectedDay(cell.date)}
                  className={`min-h-[80px] sm:min-h-[110px] p-2 border-b border-r border-earth-100 text-left transition duration-200 ${!cell.isCurrentMonth ? 'bg-earth-50/50 text-earth-400' : 'bg-white hover:bg-farm-50/60'} ${isSelected ? 'ring-2 ring-farm-500 ring-inset bg-farm-50' : ''} ${isToday ? 'border-l-2 border-l-farm-500 bg-farm-50/30' : ''}`}
                >
                  {cell.dayOfGrid != null && (
                    <>
                      <span className={`text-sm font-semibold ${!cell.isCurrentMonth ? 'text-earth-400' : isToday ? 'text-farm-600' : 'text-earth-800'}`}>
                        {cell.dayOfGrid}
                      </span>
                      {dayData?.data && (
                        <div className="mt-1 space-y-1 overflow-hidden">
                          <span className="inline-flex items-center gap-1 rounded-full bg-farm-100 text-farm-700 px-2 py-0.5 text-[10px] sm:text-xs font-semibold truncate" title={dayData.data.stage_name}>
                            {dayData.data.stage_name}
                          </span>
                          <span className="block text-[10px] text-earth-500">
                            Day {dayData.cycleDay} · {(dayData.data.tasks || []).length} tasks
                          </span>
                        </div>
                      )}
                    </>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {selectedDay && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm p-4"
          onClick={(e) => e.currentTarget === e.target && closeModal()}
        >
          <div className="w-full max-w-6xl max-h-[90vh] flex flex-col rounded-3xl bg-white shadow-2xl border border-earth-200 animate-rise-in">
            <div className="px-6 pt-6 pb-4 border-b border-earth-100 shrink-0">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="font-display text-lg font-semibold text-earth-800">
                    {selectedDay.toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' })}
                    {selectedInfo && ` · Cycle Day ${selectedInfo.cycleDay}`}
                  </h3>
                  <p className="text-earth-500 text-sm">Tap outside to close</p>
                </div>
                <button
                  type="button"
                  onClick={closeModal}
                  className="text-earth-400 hover:text-earth-700 text-xl"
                  aria-label="Close"
                >
                  ×
                </button>
              </div>
            </div>

            <div className="px-6 py-5 flex-1 flex flex-col min-h-0 overflow-hidden">
              {panelError && (
                <div className="mb-3 shrink-0 rounded-xl bg-red-50 text-red-700 px-3 py-2 text-sm">{panelError}</div>
              )}

              {/* Day details: fixed height / shrink-0 so analysis can take remaining space */}
              <div className="shrink-0">
                {selectedData ? (
                  <>
                    <div className="flex flex-wrap items-center gap-3 mb-4">
                      <span className="rounded-full bg-farm-100 text-farm-700 px-3 py-1 text-sm font-semibold">
                        {selectedData.stage_name}
                      </span>
                      <span className="rounded-full bg-earth-100 text-earth-700 px-3 py-1 text-sm">
                        {(selectedData.tasks || []).length} tasks
                      </span>
                    </div>

                    {selectedData.weather && (
                      <div className="grid sm:grid-cols-3 gap-3 text-sm mb-4">
                        <div className="rounded-xl bg-earth-50 p-3">
                          <p className="text-earth-500">Temperature</p>
                          <p className="font-semibold text-earth-800">{selectedData.weather.temperature_c ?? '—'}°C</p>
                        </div>
                        <div className="rounded-xl bg-earth-50 p-3">
                          <p className="text-earth-500">Humidity</p>
                          <p className="font-semibold text-earth-800">{selectedData.weather.humidity_percent ?? '—'}%</p>
                        </div>
                        <div className="rounded-xl bg-earth-50 p-3">
                          <p className="text-earth-500">Rainfall</p>
                          <p className="font-semibold text-earth-800">{selectedData.weather.rainfall_mm ?? '—'} mm</p>
                        </div>
                      </div>
                    )}

                    <div className="rounded-2xl border border-earth-200 p-4">
                      <h4 className="font-semibold text-earth-800 mb-2">Tasks</h4>
                      <ul className="space-y-2 text-sm text-earth-700">
                        {(selectedData.tasks || []).map((t, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <span className="mt-1 h-2 w-2 rounded-full bg-farm-500" />
                            <span>{t}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {selectedData.weather_note && (
                      <p className="mt-3 text-earth-500 text-sm italic">{selectedData.weather_note}</p>
                    )}
                  </>
                ) : (
                  <p className="text-earth-500 text-sm">No crop plan data for this date. Adjust cycle start date or check if this day is within your cycle.</p>
                )}
              </div>

              {/* Analysis: takes remaining space, single scroll area for consistent rendering */}
              {analysisLoading && (
                <div className="mt-4 shrink-0 rounded-xl bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800">
                  Analyzing image… (Tavily + government sources)
                </div>
              )}
              {analysisError && (
                <div className="mt-4 shrink-0 rounded-xl bg-red-50 text-red-700 px-4 py-3 text-sm">{analysisError}</div>
              )}
              {diseaseAnalysis && (
                <div className="mt-4 flex-1 flex flex-col min-h-0 rounded-2xl border border-amber-200 bg-amber-50/50 overflow-hidden">
                  <h4 className="font-semibold text-earth-800 mb-2 px-4 pt-4 shrink-0">Disease / field analysis</h4>
                  <div className="flex-1 min-h-0 overflow-y-auto px-4 pb-4 text-sm text-earth-700 rounded-lg bg-white/60 mx-4 mb-4 border border-amber-100 max-w-none">
                    <div className="p-3">
                      <ReactMarkdown components={analysisMarkdownComponents}>{normalizeAnalysisMarkdown(diseaseAnalysis)}</ReactMarkdown>
                    </div>
                  </div>
                  <div className="px-4 pb-4 shrink-0">
                    <button
                      type="button"
                      onClick={handleRecalibrateCalendar}
                      disabled={regenerateLoading}
                      className="btn-primary rounded-xl px-4 py-2 text-sm disabled:opacity-50 w-full sm:w-auto"
                    >
                      {regenerateLoading ? 'Recalibrating…' : 'Recalibrate calendar'}
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div className="px-6 pb-6 flex flex-wrap gap-2 shrink-0 border-t border-earth-100 pt-4">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={analysisLoading}
                className="btn-secondary rounded-xl px-4 py-2 text-sm disabled:opacity-50 flex items-center gap-2"
              >
                {analysisLoading ? 'Analyzing…' : '🖼️ Upload image'}
              </button>
              {selectedInfo?.cycleDay != null && onMarkAsDone && (
                <button
                  type="button"
                  onClick={handleMarkAsDone}
                  disabled={markAsDoneLoading}
                  className="btn-primary rounded-xl px-4 py-2 text-sm disabled:opacity-50"
                >
                  {markAsDoneLoading ? 'Updating…' : 'Mark as done'}
                </button>
              )}
              {onCheckThreshold && (
                <button
                  type="button"
                  onClick={handleCheckThreshold}
                  disabled={checkThresholdLoading || !selectedInfo?.cycleDay || !markedDays.has(selectedInfo.cycleDay)}
                  className="btn-secondary rounded-xl px-4 py-2 text-sm disabled:opacity-50"
                >
                  {checkThresholdLoading ? 'Checking…' : 'Check threshold'}
                </button>
              )}
              <button
                type="button"
                onClick={closeModal}
                className="text-earth-500 hover:text-earth-700 text-sm"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
