import { useEffect, useState } from "react";
import { recommendCrops } from "../../api";

export default function CropSelection({ onSelect }) {
  const [crops, setCrops] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(null);
  const [city, setCity] = useState("");
  const [soilType, setSoilType] = useState("");
  const [error, setError] = useState("");
  const [rationale, setRationale] = useState("");

  useEffect(() => {}, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setRationale("");
    setSelected(null);
    setLoading(true);
    try {
      const data = await recommendCrops({
        city: city.trim(),
        soil_type: soilType.trim(),
      });
      setCrops(data.crops || []);
      setRationale(data.rationale || "");
    } catch (err) {
      setCrops([]);
      setError(err?.message || "Failed to fetch recommendations");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card p-6 sm:p-8">
      <div className="flex items-center gap-3 mb-6">
        <span className="text-3xl">🌾</span>
        <div>
          <h2 className="font-display text-xl font-bold text-earth-800">
            Crop recommendations
          </h2>
          <p className="text-earth-600 text-sm">
            Suggested crops based on location and soil type
          </p>
        </div>
      </div>
      <form onSubmit={handleSubmit} className="grid gap-4 sm:grid-cols-3 mb-6">
        <div className="sm:col-span-1">
          <label className="block text-sm text-earth-600 mb-1">City</label>
          <input
            value={city}
            onChange={(e) => setCity(e.target.value)}
            placeholder="e.g. Pune"
            className="w-full rounded-xl border border-earth-200 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-farm-300"
          />
        </div>
        <div className="sm:col-span-1">
          <label className="block text-sm text-earth-600 mb-1">Soil type</label>
          <input
            value={soilType}
            onChange={(e) => setSoilType(e.target.value)}
            placeholder="e.g. loamy"
            className="w-full rounded-xl border border-earth-200 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-farm-300"
          />
        </div>
        <div className="sm:col-span-1 flex items-end">
          <button
            type="submit"
            disabled={loading || !city.trim() || !soilType.trim()}
            className="w-full rounded-xl bg-farm-500 text-white px-4 py-2 font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-farm-600 transition"
          >
            {loading ? "Loading..." : "Get recommendations"}
          </button>
        </div>
      </form>
      {error && (
        <div className="mb-4 rounded-xl border border-red-200 bg-red-50 p-3 text-red-700 text-sm">
          {error}
        </div>
      )}
      {rationale && (
        <div className="mb-4 rounded-xl border border-farm-200 bg-farm-50 p-3 text-earth-700 text-sm">
          {rationale}
        </div>
      )}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-10 w-10 border-2 border-farm-500 border-t-transparent" />
        </div>
      ) : crops.length === 0 ? (
        <div className="rounded-2xl bg-farm-50 border border-farm-200 p-8 text-center">
          <p className="text-earth-600">
            Enter your city and soil type to get crop recommendations.
          </p>
          <p className="mt-3 text-earth-500 text-sm">
            Recommendations will appear here after submission.
          </p>
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
              className={`rounded-xl border-2 p-4 text-left transition ${
                selected?.name === c.name
                  ? "border-farm-500 bg-farm-50"
                  : "border-earth-200 hover:border-farm-300 bg-white"
              }`}
            >
              <span className="font-medium text-earth-800">{c.name || c}</span>
              {c.reason && (
                <p className="mt-1 text-earth-600 text-sm">{c.reason}</p>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
