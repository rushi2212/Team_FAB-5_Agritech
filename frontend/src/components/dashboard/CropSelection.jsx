import { useEffect, useState } from 'react';
import { recommendCrops } from '../../api';

export default function CropSelection({ onSelect }) {
  const [crops, setCrops] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    recommendCrops()
      .then((d) => setCrops(d.crops || []))
      .catch(() => setCrops([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="card p-6 sm:p-8">
      <div className="flex items-center gap-3 mb-6">
        <span className="text-3xl">🌾</span>
        <div>
          <h2 className="font-display text-xl font-bold text-earth-800">Crop recommendations</h2>
          <p className="text-earth-600 text-sm">Suggested crops based on prediction (/recommend-crops — coming soon)</p>
        </div>
      </div>
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-10 w-10 border-2 border-farm-500 border-t-transparent" />
        </div>
      ) : crops.length === 0 ? (
        <div className="rounded-2xl bg-farm-50 border border-farm-200 p-8 text-center">
          <p className="text-earth-600">
            Recommendation endpoint is not available yet. Use <strong>Crop plan setup</strong> to enter your crop, state, city, and season.
          </p>
          <p className="mt-3 text-earth-500 text-sm">When /recommend-crops is added, suggested crops will appear here.</p>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {crops.map((c, i) => (
            <button
              key={i}
              onClick={() => {
                setSelected(c);
                onSelect(c);
              }}
              className={`rounded-xl border-2 p-4 text-left transition ${selected?.name === c.name
                ? 'border-farm-500 bg-farm-50'
                : 'border-earth-200 hover:border-farm-300 bg-white'
                }`}
            >
              <span className="font-medium text-earth-800">{c.name || c}</span>
              {c.reason && <p className="mt-1 text-earth-600 text-sm">{c.reason}</p>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
