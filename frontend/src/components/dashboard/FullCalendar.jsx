import { useState, useMemo } from 'react';

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
  const [cycleStartDate, setCycleStartDate] = useState(() => {
    const d = new Date();
    d.setDate(1);
    return dateToKey(d);
  });
  const [selectedDay, setSelectedDay] = useState(null);

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

  const handleMarkAsDone = async () => {
    if (!selectedInfo?.cycleDay || !onMarkAsDone) return;
    setPanelError('');
    setMarkAsDoneLoading(true);
    try {
      await onMarkAsDone(selectedInfo.cycleDay);
      await onRefresh();
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

  if (loading) {
    return (
      <div className="card p-12 flex justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-2 border-farm-500 border-t-transparent" />
      </div>
    );
  }

  if (!calendar || days.length === 0) {
    return (
      <div className="card p-8 text-center rounded-2xl bg-amber-50 border border-amber-200">
        <p className="text-amber-800">No calendar yet. Set up your crop plan (step 1) and generate the calendar (step 2).</p>
        <button onClick={onRefresh} className="btn-secondary mt-4 rounded-xl">Refresh</button>
      </div>
    );
  }

  const selectedInfo = selectedDay ? getDayDataForDate(selectedDay) : null;
  const selectedData = selectedInfo?.data;

  return (
    <div className="space-y-6">
      <div className="card p-6 sm:p-8">
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
          <button onClick={onRefresh} className="btn-secondary rounded-xl px-4 py-2 text-sm">Refresh</button>
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
        <div className="border border-earth-200 rounded-2xl overflow-hidden">
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
                  className={`min-h-[80px] sm:min-h-[100px] p-2 border-b border-r border-earth-100 text-left transition ${!cell.isCurrentMonth ? 'bg-earth-50/50 text-earth-400' : 'bg-white hover:bg-farm-50/50'
                    } ${isSelected ? 'ring-2 ring-farm-500 ring-inset bg-farm-50' : ''} ${isToday ? 'border-l-2 border-l-farm-500' : ''}`}
                >
                  {cell.dayOfGrid != null && (
                    <>
                      <span className={`text-sm font-medium ${!cell.isCurrentMonth ? 'text-earth-400' : isToday ? 'text-farm-600' : 'text-earth-800'}`}>
                        {cell.dayOfGrid}
                      </span>
                      {dayData?.data && (
                        <div className="mt-1 space-y-0.5 overflow-hidden">
                          <span className="block text-[10px] sm:text-xs font-medium text-farm-700 truncate" title={dayData.data.stage_name}>
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

        {/* Selected day detail panel */}
        {selectedDay && (
          <div className="mt-6 rounded-2xl border-2 border-farm-200 bg-farm-50/80 p-6">
            <div className="flex items-center justify-between flex-wrap gap-2 mb-4">
              <h3 className="font-display font-semibold text-earth-800">
                {selectedDay.toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' })}
                {selectedInfo && ` · Cycle Day ${selectedInfo.cycleDay}`}
              </h3>
              <div className="flex items-center gap-2 flex-wrap">
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
                    disabled={checkThresholdLoading}
                    className="btn-secondary rounded-xl px-4 py-2 text-sm disabled:opacity-50"
                  >
                    {checkThresholdLoading ? 'Checking…' : 'Check threshold'}
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setSelectedDay(null)}
                  className="text-earth-500 hover:text-earth-700 text-sm"
                >
                  Close
                </button>
              </div>
            </div>
            {panelError && (
              <div className="mb-3 rounded-xl bg-red-50 text-red-700 px-3 py-2 text-sm">{panelError}</div>
            )}
            {selectedData ? (
              <>
                <p className="font-medium text-farm-700 mb-2">{selectedData.stage_name}</p>
                {selectedData.weather && (
                  <div className="flex flex-wrap gap-3 text-sm text-earth-600 mb-3">
                    {selectedData.weather.temperature_c != null && (
                      <span>{selectedData.weather.temperature_c}°C</span>
                    )}
                    {selectedData.weather.humidity_percent != null && (
                      <span>{selectedData.weather.humidity_percent}% humidity</span>
                    )}
                    {selectedData.weather.rainfall_mm != null && (
                      <span>{selectedData.weather.rainfall_mm} mm rain</span>
                    )}
                  </div>
                )}
                <ul className="list-disc list-inside space-y-1 text-earth-700 text-sm">
                  {(selectedData.tasks || []).map((t, i) => (
                    <li key={i}>{t}</li>
                  ))}
                </ul>
                {selectedData.weather_note && (
                  <p className="mt-2 text-earth-500 text-sm italic">{selectedData.weather_note}</p>
                )}
              </>
            ) : (
              <p className="text-earth-500 text-sm">No crop plan data for this date. Adjust cycle start date or check if this day is within your cycle.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
