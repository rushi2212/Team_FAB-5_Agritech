import { useState, useEffect } from 'react';
import { assessPestRisk } from '../../api';
import SectionLoader from './SectionLoader';

const RISK_COLORS = {
  low: {
    bg: 'bg-farm-50',
    border: 'border-farm-300',
    text: 'text-farm-800',
    badge: 'bg-farm-100 text-farm-700 border-farm-300',
    icon: '✅'
  },
  medium: {
    bg: 'bg-amber-50',
    border: 'border-amber-300',
    text: 'text-amber-900',
    badge: 'bg-amber-100 text-amber-800 border-amber-300',
    icon: '⚠️'
  },
  high: {
    bg: 'bg-orange-50',
    border: 'border-orange-300',
    text: 'text-orange-900',
    badge: 'bg-orange-100 text-orange-800 border-orange-300',
    icon: '🔴'
  },
  critical: {
    bg: 'bg-red-50',
    border: 'border-red-300',
    text: 'text-red-900',
    badge: 'bg-red-100 text-red-800 border-red-300',
    icon: '🚨'
  }
};

const SEVERITY_COLORS = {
  low: 'bg-farm-100 text-farm-800 border-farm-300',
  medium: 'bg-amber-100 text-amber-800 border-amber-300',
  high: 'bg-orange-100 text-orange-800 border-orange-300',
  critical: 'bg-red-100 text-red-800 border-red-300'
};

export default function PestRiskAssessment({ variable, calendar, loading }) {
  const [riskData, setRiskData] = useState(null);
  const [loadingRisk, setLoadingRisk] = useState(false);
  const [error, setError] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [emailSent, setEmailSent] = useState(false);
  const [autoFetched, setAutoFetched] = useState(false);

  // Auto-fetch risk assessment when component mounts
  useEffect(() => {
    if (variable && !autoFetched) {
      setAutoFetched(true);
      fetchRiskAssessment();
    }
  }, [variable, autoFetched]);

  const fetchRiskAssessment = async (email = '') => {
    setLoadingRisk(true);
    setError('');
    setEmailSent(false);

    try {
      const data = await assessPestRisk({
        user_email: email
      });

      setRiskData(data);
      if (email && data.email_sent) {
        setEmailSent(true);
      }
    } catch (err) {
      setError(err.message || 'Failed to assess pest/disease risk');
      setRiskData(null);
    } finally {
      setLoadingRisk(false);
    }
  };

  const handleAssessWithEmail = () => {
    if (userEmail) {
      fetchRiskAssessment(userEmail);
    }
  };

  const getRiskColor = (level) => {
    return RISK_COLORS[level?.toLowerCase()] || RISK_COLORS.low;
  };

  const getRiskScoreColor = (score) => {
    if (score >= 85) return 'text-red-600';
    if (score >= 60) return 'text-orange-600';
    if (score >= 30) return 'text-amber-600';
    return 'text-farm-600';
  };

  if (loading) {
    return <SectionLoader title="Loading risk data" subtitle="Analyzing pest and disease threats..." />;
  }

  if (!variable) {
    return (
      <div className="card p-6 sm:p-8">
        <div className="text-center text-earth-600">
          <p className="mb-2">🐛 Pest & disease risk assessment not available</p>
          <p className="text-sm">Please set up your crop plan first in the "Crop plan setup" tab</p>
        </div>
      </div>
    );
  }

  const riskColor = riskData ? getRiskColor(riskData.risk_level) : RISK_COLORS.low;

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="card p-6 sm:p-8 animate-fade-in">
        <div className="flex items-center gap-3 mb-6">
          <span className="text-3xl">🐛</span>
          <div className="flex-1">
            <h2 className="font-display text-xl font-bold text-earth-800">Pest & Disease Risk Assessment</h2>
            <p className="text-earth-600 text-sm">Early warning system for crop health threats</p>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-800 text-sm">
            <p className="font-medium">⚠️ {error}</p>
          </div>
        )}

        {/* Email Alert Success */}
        {emailSent && (
          <div className="mb-6 p-4 bg-farm-50 border border-farm-200 rounded-xl text-farm-800 text-sm animate-fade-in">
            <p className="font-medium">✅ Alert email sent successfully!</p>
          </div>
        )}

        {/* Loading State */}
        {loadingRisk && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-farm-600"></div>
            <p className="text-earth-600 mt-3">Analyzing crop health risks...</p>
          </div>
        )}

        {/* Risk Assessment Display */}
        {!loadingRisk && riskData && (
          <div className="space-y-6 animate-fade-in">
            {/* Overall Risk Banner */}
            <div className={`rounded-2xl ${riskColor.bg} border-2 ${riskColor.border} p-6`}>
              <div className="flex items-center justify-between gap-4 mb-4">
                <div className="flex items-center gap-3">
                  <span className="text-4xl">{riskColor.icon}</span>
                  <div>
                    <p className="text-sm text-earth-600 mb-1">Overall Risk Level</p>
                    <p className={`text-2xl font-bold capitalize ${riskColor.text}`}>
                      {riskData.risk_level}
                    </p>
                  </div>
                </div>
                <div className="text-center">
                  <p className="text-sm text-earth-600 mb-1">Risk Score</p>
                  <p className={`text-3xl font-bold ${getRiskScoreColor(riskData.risk_score)}`}>
                    {riskData.risk_score}
                  </p>
                  <p className="text-xs text-earth-500">/100</p>
                </div>
              </div>

              {/* Crop Info */}
              <div className="grid sm:grid-cols-2 gap-3 text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-earth-600">🌾 Crop:</span>
                  <span className="font-semibold text-earth-800">{riskData.crop_name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-earth-600">📅 Stage:</span>
                  <span className="font-semibold text-earth-800">{riskData.crop_stage}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-earth-600">⏱️ Day:</span>
                  <span className="font-semibold text-earth-800">Day {riskData.day_of_cycle}</span>
                </div>
              </div>
            </div>

            {/* Weather Factors */}
            {riskData.weather_factors && (
              <div className="card p-6 bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200">
                <p className="font-medium text-earth-800 mb-4 flex items-center gap-2">
                  <span className="text-xl">🌤️</span>
                  Current Weather Conditions
                </p>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div className="text-center">
                    <p className="text-earth-600 mb-1">🌡️ Temperature</p>
                    <p className="text-2xl font-bold text-earth-800">{riskData.weather_factors.temperature_c}°C</p>
                  </div>
                  <div className="text-center">
                    <p className="text-earth-600 mb-1">💧 Humidity</p>
                    <p className="text-2xl font-bold text-earth-800">{riskData.weather_factors.humidity_percent}%</p>
                  </div>
                  <div className="text-center">
                    <p className="text-earth-600 mb-1">🌧️ Rainfall</p>
                    <p className="text-2xl font-bold text-earth-800">{riskData.weather_factors.rainfall_mm}mm</p>
                  </div>
                </div>
              </div>
            )}

            {/* Pest Risks */}
            {riskData.pest_risks && riskData.pest_risks.length > 0 && (
              <div className="card p-6">
                <h3 className="font-medium text-earth-800 mb-4 flex items-center gap-2">
                  <span className="text-xl">🦗</span>
                  Identified Pest Risks ({riskData.pest_risks.length})
                </h3>
                <div className="space-y-3">
                  {riskData.pest_risks.map((pest, idx) => (
                    <div key={idx} className="rounded-xl bg-earth-50 border border-earth-200 p-4">
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <p className="font-semibold text-earth-800">{pest.name}</p>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium border capitalize ${SEVERITY_COLORS[pest.severity] || SEVERITY_COLORS.low}`}>
                          {pest.severity}
                        </span>
                      </div>
                      <p className="text-sm text-earth-700 mb-2">{pest.description}</p>
                      <p className="text-xs text-earth-600">
                        <span className="font-medium">Reason:</span> {pest.reason}
                      </p>
                      {pest.score && (
                        <p className="text-xs text-earth-500 mt-1">Score: {pest.score}/100</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Disease Risks */}
            {riskData.disease_risks && riskData.disease_risks.length > 0 && (
              <div className="card p-6">
                <h3 className="font-medium text-earth-800 mb-4 flex items-center gap-2">
                  <span className="text-xl">🦠</span>
                  Identified Disease Risks ({riskData.disease_risks.length})
                </h3>
                <div className="space-y-3">
                  {riskData.disease_risks.map((disease, idx) => (
                    <div key={idx} className="rounded-xl bg-earth-50 border border-earth-200 p-4">
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <p className="font-semibold text-earth-800">{disease.name}</p>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium border capitalize ${SEVERITY_COLORS[disease.severity] || SEVERITY_COLORS.low}`}>
                          {disease.severity}
                        </span>
                      </div>
                      <p className="text-sm text-earth-700 mb-2">{disease.description}</p>
                      <p className="text-xs text-earth-600">
                        <span className="font-medium">Reason:</span> {disease.reason}
                      </p>
                      {disease.score && (
                        <p className="text-xs text-earth-500 mt-1">Score: {disease.score}/100</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* No Risks Found */}
            {(!riskData.pest_risks || riskData.pest_risks.length === 0) &&
              (!riskData.disease_risks || riskData.disease_risks.length === 0) && (
                <div className="card p-6 bg-farm-50 border border-farm-200">
                  <div className="text-center py-4">
                    <span className="text-4xl mb-3 block">✅</span>
                    <p className="font-medium text-farm-800 mb-1">No Immediate Threats Detected</p>
                    <p className="text-sm text-earth-600">Current conditions are favorable for your crop</p>
                  </div>
                </div>
              )}

            {/* Preventive Actions */}
            {riskData.preventive_actions && riskData.preventive_actions.length > 0 && (
              <div className="card p-6 bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200">
                <h3 className="font-medium text-earth-800 mb-4 flex items-center gap-2">
                  <span className="text-xl">🛡️</span>
                  Recommended Preventive Actions
                </h3>
                <ul className="space-y-3">
                  {riskData.preventive_actions.map((action, idx) => (
                    <li key={idx} className="flex items-start gap-3 rounded-xl bg-white hover:bg-purple-50 p-4 transition border border-purple-100">
                      <span className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-500 text-white text-xs font-medium flex items-center justify-center mt-0.5">
                        {idx + 1}
                      </span>
                      <span className="text-earth-800 text-sm flex-1">{action}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Calendar hazard alerts: LLM-flagged hazardous content in calendar */}
            {riskData.calendar_hazard_alerts && riskData.calendar_hazard_alerts.length > 0 && (
              <div className="card p-6 bg-red-50 border-2 border-red-200">
                <h3 className="font-medium text-red-900 mb-2 flex items-center gap-2">
                  <span className="text-xl">⚠️</span>
                  Hazardous content detected in calendar
                </h3>
                <p className="text-sm text-red-800 mb-4">
                  The following task(s) were flagged by our safety review as hazardous or unsafe. They have been removed from your calendar view. Do not follow them.
                </p>
                <ul className="space-y-3">
                  {riskData.calendar_hazard_alerts.map((alert, idx) => (
                    <li key={idx} className="rounded-xl bg-white border border-red-200 p-4">
                      <p className="text-sm font-semibold text-red-900 mb-2">Day {alert.day_index}</p>
                      <ul className="space-y-2">
                        {(alert.flagged_tasks || alert.tasks_removed || []).map((item, i) => {
                          const taskText = typeof item === 'string' ? item : (item?.task || item);
                          const reason = typeof item === 'object' && item?.hazard_reason ? item.hazard_reason : null;
                          return (
                            <li key={i} className="text-sm text-red-800">
                              <span className="font-medium">"{taskText}"</span>
                              {reason && (
                                <p className="text-red-700 mt-1 ml-2 text-xs">Reason: {reason}</p>
                              )}
                            </li>
                          );
                        })}
                      </ul>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Email Alert Section */}
            <div className="card p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200">
              <h3 className="font-medium text-earth-800 mb-3 flex items-center gap-2">
                <span className="text-xl">📧</span>
                Email Alerts
              </h3>
              <p className="text-sm text-earth-600 mb-4">
                Get alerts via email when risk level is medium or higher
              </p>
              <div className="flex gap-3">
                <input
                  type="email"
                  value={userEmail}
                  onChange={(e) => setUserEmail(e.target.value)}
                  placeholder="your.email@example.com"
                  className="input-field flex-1"
                />
                <button
                  onClick={handleAssessWithEmail}
                  disabled={!userEmail || loadingRisk}
                  className="btn-primary whitespace-nowrap"
                >
                  📧 Send Alert
                </button>
              </div>
              {riskData.email_sent && (
                <p className="text-xs text-farm-700 mt-2">
                  ✓ Email alert was sent during the last assessment
                </p>
              )}
            </div>

            {/* Last Updated */}
            <div className="text-center text-xs text-earth-500">
              Last assessed: {riskData.last_updated ? new Date(riskData.last_updated).toLocaleDateString('en-IN', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              }) : 'N/A'}
            </div>

            {/* Refresh Button */}
            <div className="text-center">
              <button
                onClick={() => fetchRiskAssessment()}
                className="btn-secondary text-sm"
                disabled={loadingRisk}
              >
                🔄 Refresh Assessment
              </button>
            </div>
          </div>
        )}

        {/* No Data State */}
        {!loadingRisk && !riskData && !error && (
          <div className="text-center py-8 text-earth-600">
            <p className="text-lg mb-2">🐛</p>
            <p>Click refresh to assess pest and disease risks</p>
          </div>
        )}
      </div>

      {/* Info Card */}
      <div className="card p-6 bg-amber-50 border border-amber-200">
        <div className="flex gap-3">
          <span className="text-2xl flex-shrink-0">💡</span>
          <div className="text-sm text-earth-700">
            <p className="font-medium mb-2">About Risk Assessment</p>
            <ul className="space-y-1 text-earth-600">
              <li>• Risk levels are calculated based on weather conditions and crop stage</li>
              <li>• Follow preventive actions even at low risk levels for best crop health</li>
              <li>• Contact agricultural extension officers for critical risk situations</li>
              <li>• Regular monitoring is essential for early pest/disease detection</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
