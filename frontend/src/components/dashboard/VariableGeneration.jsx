import { useState } from 'react';

const SEASONS = ['Kharif', 'Rabi', 'Summer'];

export default function VariableGeneration({ variable, loading, onGenerate, onRefresh }) {
  const [state, setState] = useState(variable?.location?.state || '');
  const [city, setCity] = useState(variable?.location?.city || '');
  const [cropName, setCropName] = useState(variable?.crop?.crop_name || '');
  const [season, setSeason] = useState(variable?.crop?.season || 'Kharif');
  const [submitting, setSubmitting] = useState(false);

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
      <div className="card p-6 sm:p-8">
        <div className="flex items-center gap-3 mb-6">
          <span className="text-3xl">🌱</span>
          <div>
            <h2 className="font-display text-xl font-bold text-earth-800">Set up your crop plan</h2>
            <p className="text-earth-600 text-sm">Location, crop & season → we fetch soil & weather for your plan</p>
          </div>
        </div>
        <form onSubmit={handleSubmit} className="grid sm:grid-cols-2 gap-4 max-w-2xl">
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
        <div className="card p-6 overflow-hidden">
          <h3 className="font-display font-semibold text-earth-800 mb-4">Current plan</h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
            <div className="rounded-xl bg-earth-50 p-4">
              <span className="text-earth-500">Location</span>
              <p className="font-medium text-earth-800">{variable.location?.city}, {variable.location?.state}</p>
              <p className="text-earth-600">lat {variable.location?.coordinates?.lat}, lon {variable.location?.coordinates?.lon}</p>
            </div>
            <div className="rounded-xl bg-earth-50 p-4">
              <span className="text-earth-500">Crop</span>
              <p className="font-medium text-earth-800">{variable.crop?.crop_name} · {variable.crop?.season}</p>
              <p className="text-earth-600">Day of cycle: {variable.day_of_cycle}</p>
            </div>
            <div className="rounded-xl bg-earth-50 p-4">
              <span className="text-earth-500">Climate</span>
              <p className="font-medium text-earth-800">{variable.climate?.temperature_c}°C, {variable.climate?.humidity_percent}% humidity</p>
              <p className="text-earth-600">Rainfall: {variable.climate?.rainfall_mm} mm</p>
            </div>
            <div className="rounded-xl bg-farm-50 p-4 sm:col-span-2 lg:col-span-3">
              <span className="text-earth-500">Soil</span>
              <p className="font-medium text-earth-800">{variable.soil_type}</p>
              {variable.soil_map?.texture_class_usda && (
                <p className="text-earth-600">Texture: {variable.soil_map.texture_class_usda}</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
