import { useState, useEffect } from 'react';
import { predictMarketPrice } from '../../api';
import SectionLoader from './SectionLoader';

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

const TREND_ICONS = {
  rising: '📈',
  falling: '📉',
  stable: '↔️',
  volatile: '🔄'
};

const CONFIDENCE_COLORS = {
  high: 'bg-farm-100 text-farm-800 border-farm-300',
  medium: 'bg-amber-100 text-amber-800 border-amber-300',
  low: 'bg-gray-100 text-gray-800 border-gray-300'
};

export default function MarketPricePredictor({ variable, loading }) {
  const [prediction, setPrediction] = useState(null);
  const [loadingPrediction, setLoadingPrediction] = useState(false);
  const [error, setError] = useState('');
  const [harvestMonth, setHarvestMonth] = useState('');
  const [autoFetched, setAutoFetched] = useState(false);

  // Auto-fetch prediction when component mounts (if variable exists)
  useEffect(() => {
    if (variable && !autoFetched) {
      // Determine default harvest month based on season
      const season = variable?.crop?.season?.toLowerCase() || '';
      let defaultMonth = '';
      
      if (season.includes('kharif')) {
        defaultMonth = 'October'; // Kharif harvest
      } else if (season.includes('rabi')) {
        defaultMonth = 'March'; // Rabi harvest
      } else if (season.includes('summer') || season.includes('zaid')) {
        defaultMonth = 'June'; // Summer harvest
      } else {
        // Default to 3 months from now
        const futureDate = new Date();
        futureDate.setMonth(futureDate.getMonth() + 3);
        defaultMonth = MONTHS[futureDate.getMonth()];
      }
      
      setHarvestMonth(defaultMonth);
      setAutoFetched(true);
      fetchPrediction(defaultMonth);
    }
  }, [variable, autoFetched]);

  const fetchPrediction = async (month) => {
    if (!variable || !month) return;

    setLoadingPrediction(true);
    setError('');
    
    try {
      const cropName = variable.crop?.crop_name || variable.crop?.name || '';
      const state = variable.location?.state || '';
      const season = variable.crop?.season || '';

      if (!cropName || !state || !season) {
        throw new Error('Missing crop information. Please set up your farm profile first.');
      }

      const data = await predictMarketPrice({
        crop_name: cropName,
        state: state,
        season: season,
        harvest_month: month
      });

      setPrediction(data);
    } catch (err) {
      setError(err.message || 'Failed to fetch market price prediction');
      setPrediction(null);
    } finally {
      setLoadingPrediction(false);
    }
  };

  const handleMonthChange = (e) => {
    const month = e.target.value;
    setHarvestMonth(month);
    if (month) {
      fetchPrediction(month);
    }
  };

  if (loading) {
    return <SectionLoader title="Loading market data" subtitle="Analyzing price trends..." />;
  }

  if (!variable) {
    return (
      <div className="card p-6 sm:p-8">
        <div className="text-center text-earth-600">
          <p className="mb-2">📊 Market price prediction not available</p>
          <p className="text-sm">Please set up your crop plan first in the "Crop plan setup" tab</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="card p-6 sm:p-8 animate-fade-in">
        <div className="flex items-center gap-3 mb-6">
          <span className="text-3xl">📊</span>
          <div className="flex-1">
            <h2 className="font-display text-xl font-bold text-earth-800">Market Price Prediction</h2>
            <p className="text-earth-600 text-sm">Harvest-time price forecast based on historical data</p>
          </div>
        </div>

        {/* Harvest Month Selector */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-earth-700 mb-2">
            Expected Harvest Month
          </label>
          <select
            value={harvestMonth}
            onChange={handleMonthChange}
            className="input-field w-full sm:w-64"
          >
            <option value="">Select month...</option>
            {MONTHS.map(month => (
              <option key={month} value={month}>{month}</option>
            ))}
          </select>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-800 text-sm">
            <p className="font-medium">⚠️ {error}</p>
          </div>
        )}

        {/* Loading State */}
        {loadingPrediction && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-farm-600"></div>
            <p className="text-earth-600 mt-3">Analyzing market trends...</p>
          </div>
        )}

        {/* Prediction Display */}
        {!loadingPrediction && prediction && (
          <div className="space-y-6 animate-fade-in">
            {/* Crop Info Banner */}
            <div className="rounded-2xl bg-gradient-to-r from-farm-50 to-farm-100 p-4 border border-farm-200">
              <div className="flex items-center gap-3 text-sm">
                <span className="text-2xl">🌾</span>
                <div>
                  <p className="font-semibold text-earth-800">{prediction.crop_name}</p>
                  <p className="text-earth-600">{prediction.season} Season • {prediction.state}</p>
                </div>
              </div>
            </div>

            {/* Main Price Display */}
            <div className="grid sm:grid-cols-2 gap-4">
              {/* Average Price */}
              <div className="rounded-2xl bg-gradient-to-br from-farm-500 to-farm-600 p-6 text-white">
                <p className="text-sm opacity-90 mb-1">Average Expected Price</p>
                <p className="text-3xl font-bold">₹{prediction.average_price?.toLocaleString()}</p>
                <p className="text-sm opacity-75 mt-1">per quintal</p>
              </div>

              {/* Price Range */}
              <div className="rounded-2xl bg-earth-50 p-6 border border-earth-200">
                <p className="text-sm text-earth-600 mb-3">Price Range</p>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-earth-500">Minimum</span>
                    <span className="font-semibold text-earth-800">₹{prediction.predicted_price_range?.min?.toLocaleString()}</span>
                  </div>
                  <div className="h-2 bg-gradient-to-r from-amber-300 via-farm-400 to-farm-600 rounded-full"></div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-earth-500">Maximum</span>
                    <span className="font-semibold text-earth-800">₹{prediction.predicted_price_range?.max?.toLocaleString()}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Trend */}
              <div className="rounded-2xl bg-earth-50 p-4 border border-earth-200">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">{TREND_ICONS[prediction.trend] || '📊'}</span>
                  <span className="text-earth-500 text-sm">Market Trend</span>
                </div>
                <p className="font-semibold text-earth-800 capitalize text-lg">{prediction.trend}</p>
                {prediction.trend === 'rising' && (
                  <p className="text-xs text-earth-600 mt-1">Prices expected to increase</p>
                )}
                {prediction.trend === 'falling' && (
                  <p className="text-xs text-earth-600 mt-1">Prices expected to decrease</p>
                )}
                {prediction.trend === 'stable' && (
                  <p className="text-xs text-earth-600 mt-1">Prices expected to remain steady</p>
                )}
                {prediction.trend === 'volatile' && (
                  <p className="text-xs text-earth-600 mt-1">Prices may fluctuate significantly</p>
                )}
              </div>

              {/* Confidence */}
              <div className="rounded-2xl bg-earth-50 p-4 border border-earth-200">
                <span className="text-earth-500 text-sm block mb-2">Confidence Level</span>
                <div className="inline-flex items-center gap-2">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium border capitalize ${CONFIDENCE_COLORS[prediction.confidence] || CONFIDENCE_COLORS.low}`}>
                    {prediction.confidence}
                  </span>
                </div>
                <p className="text-xs text-earth-600 mt-2">
                  {prediction.confidence === 'high' && 'Based on consistent historical data'}
                  {prediction.confidence === 'medium' && 'Based on moderate data availability'}
                  {prediction.confidence === 'low' && 'Limited historical data available'}
                </p>
              </div>

              {/* Harvest Month */}
              <div className="rounded-2xl bg-earth-50 p-4 border border-earth-200">
                <span className="text-earth-500 text-sm block mb-2">Harvest Period</span>
                <p className="font-semibold text-earth-800 text-lg">{prediction.harvest_month}</p>
                <p className="text-xs text-earth-600 mt-1">Expected harvest time</p>
              </div>
            </div>

            {/* Data Sources */}
            {prediction.data_sources && prediction.data_sources.length > 0 && (
              <div className="rounded-xl bg-blue-50 border border-blue-200 p-4">
                <p className="text-sm font-medium text-blue-900 mb-2">📚 Data Sources</p>
                <div className="flex flex-wrap gap-2">
                  {prediction.data_sources.map((source, idx) => (
                    <span key={idx} className="text-xs bg-white px-3 py-1 rounded-full text-blue-800 border border-blue-200">
                      {source}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Last Updated */}
            <div className="text-center text-xs text-earth-500">
              Last updated: {prediction.last_updated ? new Date(prediction.last_updated).toLocaleDateString('en-IN', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              }) : 'N/A'}
            </div>

            {/* Refresh Button */}
            <div className="text-center">
              <button
                onClick={() => fetchPrediction(harvestMonth)}
                className="btn-secondary text-sm"
                disabled={loadingPrediction}
              >
                🔄 Refresh Prediction
              </button>
            </div>
          </div>
        )}

        {/* No Data State */}
        {!loadingPrediction && !prediction && !error && harvestMonth && (
          <div className="text-center py-8 text-earth-600">
            <p className="text-lg mb-2">📊</p>
            <p>Select a harvest month to see price predictions</p>
          </div>
        )}
      </div>

      {/* Info Card */}
      <div className="card p-6 bg-amber-50 border border-amber-200">
        <div className="flex gap-3">
          <span className="text-2xl flex-shrink-0">💡</span>
          <div className="text-sm text-earth-700">
            <p className="font-medium mb-2">About Market Price Predictions</p>
            <ul className="space-y-1 text-earth-600">
              <li>• Prices are based on historical Agmarknet data and seasonal patterns</li>
              <li>• Predictions are estimates and actual prices may vary</li>
              <li>• Consider market trends when planning harvest timing</li>
              <li>• Higher confidence indicates more reliable historical data</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
