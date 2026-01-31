import { useEffect, useMemo, useState } from 'react';
import SectionLoader from './SectionLoader';

const SEASONS = ['Kharif', 'Rabi', 'Summer'];

export default function VariableGeneration({ variable, loading, onGenerate, onRefresh }) {
  const [state, setState] = useState(variable?.location?.state || '');
  const [city, setCity] = useState(variable?.location?.city || '');
  const [cropName, setCropName] = useState(variable?.crop?.crop_name || '');
  const [season, setSeason] = useState(variable?.crop?.season || 'Kharif');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!variable) return;
    setState(variable?.location?.state || '');
    setCity(variable?.location?.city || '');
    setCropName(variable?.crop?.crop_name || '');
    setSeason(variable?.crop?.season || 'Kharif');
  }, [variable]);

  const soilRows = useMemo(() => {
    const props = variable?.soil_properties || {};
    const units = variable?.soil_properties_units || {};
    return Object.entries(props).map(([depth, values]) => ({
      depth,
      values,
      units,
    }));
  }, [variable]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await onGenerate({ state, city, crop_name: cropName, season });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {loading && !variable && (
        <SectionLoader title="Loading crop plan" subtitle="Fetching location, soil, and climate data…" />
      )}
      <div className="card p-6 sm:p-8">
        <div className="flex items-center gap-3 mb-6">
          <span className="text-3xl">🌱</span>
          <div>
            <h2 className="font-display text-xl font-bold text-earth-800">Set up your crop plan</h2>
            <p className="text-earth-600 text-sm">Location, crop & season → we fetch soil & weather for your plan</p>
          </div>
        </div>
        <form onSubmit={handleSubmit} className="grid sm:grid-cols-2 gap-4 max-w-3xl">
          <div>
            <label className="block text-sm font-medium text-earth-700 mb-1.5">State</label>
            <input
              type="text"
              value={state}
              onChange={(e) => setState(e.target.value)}
              className="input-field"
              placeholder="e.g. Maharashtra"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-earth-700 mb-1.5">City</label>
            <input
              type="text"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              className="input-field"
              placeholder="e.g. Pune"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-earth-700 mb-1.5">Crop name</label>
            <input
              type="text"
              value={cropName}
              onChange={(e) => setCropName(e.target.value)}
              className="input-field"
              placeholder="e.g. rice"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-earth-700 mb-1.5">Season</label>
            <select
              value={season}
              onChange={(e) => setSeason(e.target.value)}
              className="input-field"
            >
              {SEASONS.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div className="sm:col-span-2 flex gap-3">
            <button type="submit" disabled={submitting} className="btn-primary rounded-xl px-6 py-3">
              {submitting ? 'Saving plan…' : 'Save crop plan'}
            </button>
            <button type="button" onClick={onRefresh} disabled={loading} className="btn-secondary rounded-xl px-6 py-3">
              Refresh
            </button>
          </div>
        </form>
      </div>

      {variable && (
        <div className="card p-6 sm:p-8 space-y-6 animate-fade-in">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <h3 className="font-display font-semibold text-earth-800">Current plan insights</h3>
              <p className="text-earth-500 text-sm">Live snapshot of soil and climate inputs used for the calendar.</p>
            </div>
            <button type="button" onClick={onRefresh} className="btn-secondary rounded-xl px-4 py-2 text-sm">Refresh</button>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            <div className="rounded-2xl bg-earth-50 p-4">
              <span className="text-earth-500">Location</span>
              <p className="font-semibold text-earth-800">{variable.location?.city}, {variable.location?.state}</p>
              <p className="text-earth-600">Lat {variable.location?.coordinates?.lat}, Lon {variable.location?.coordinates?.lon}</p>
            </div>
            <div className="rounded-2xl bg-earth-50 p-4">
              <span className="text-earth-500">Crop</span>
              <p className="font-semibold text-earth-800">{variable.crop?.crop_name} · {variable.crop?.season}</p>
              <p className="text-earth-600">Day of cycle: {variable.day_of_cycle}</p>
            </div>
            <div className="rounded-2xl bg-earth-50 p-4">
              <span className="text-earth-500">Climate</span>
              <p className="font-semibold text-earth-800">{variable.climate?.temperature_c}°C</p>
              <p className="text-earth-600">Humidity {variable.climate?.humidity_percent}% · Rain {variable.climate?.rainfall_mm} mm</p>
            </div>
            <div className="rounded-2xl bg-farm-50 p-4">
              <span className="text-earth-500">Soil type</span>
              <p className="font-semibold text-earth-800">{variable.soil_type}</p>
              {variable.soil_map?.texture_class_usda && (
                <p className="text-earth-600">Texture: {variable.soil_map.texture_class_usda}</p>
              )}
            </div>
          </div>

          {variable.soil_map && (
            <div className="grid lg:grid-cols-2 gap-4">
              <div className="rounded-2xl border border-earth-200 p-4">
                <h4 className="font-semibold text-earth-800 mb-2">Soil classification</h4>
                <div className="text-sm text-earth-600 space-y-1">
                  {variable.soil_map.wrb_class_name && (
                    <p>WRB class: <span className="font-medium text-earth-800">{variable.soil_map.wrb_class_name}</span></p>
                  )}
                  {Array.isArray(variable.soil_map.wrb_class_probability) && (
                    <div className="mt-2 space-y-1">
                      {variable.soil_map.wrb_class_probability.slice(0, 4).map(([name, value]) => (
                        <div key={name} className="flex items-center justify-between text-xs">
                          <span>{name}</span>
                          <span className="font-medium text-earth-700">{value}%</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {variable.soil_map.properties_note && (
                    <p className="text-xs text-earth-500 italic">{variable.soil_map.properties_note}</p>
                  )}
                </div>
              </div>
              <div className="rounded-2xl border border-earth-200 p-4">
                <h4 className="font-semibold text-earth-800 mb-2">Soil profile depths</h4>
                <div className="flex flex-wrap gap-2 text-xs">
                  {(variable.soil_map.depths_available || []).map((d) => (
                    <span key={d} className="rounded-full bg-farm-100 text-farm-700 px-3 py-1">{d}</span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {soilRows.length > 0 && (
            <div className="rounded-2xl border border-earth-200 overflow-hidden">
              <div className="bg-earth-50 px-4 py-3 text-sm font-semibold text-earth-700">Soil properties by depth</div>
              <div className="overflow-auto">
                <table className="min-w-full text-sm">
                  <thead className="bg-white text-earth-500">
                    <tr>
                      <th className="text-left px-4 py-3 font-medium">Depth</th>
                      {Object.keys(soilRows[0]?.values || {}).map((key) => (
                        <th key={key} className="text-left px-4 py-3 font-medium">{key} {soilRows[0].units?.[key] ? `(${soilRows[0].units[key]})` : ''}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {soilRows.map((row) => (
                      <tr key={row.depth} className="border-t border-earth-100">
                        <td className="px-4 py-3 font-medium text-earth-800">{row.depth}</td>
                        {Object.entries(row.values).map(([key, value]) => (
                          <td key={key} className="px-4 py-3 text-earth-700">{value}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
