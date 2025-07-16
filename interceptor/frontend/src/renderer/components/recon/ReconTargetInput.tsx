f// galdr/interceptor/frontend/src/renderer/components/recon/ReconTargetInput.tsx
import React, { useState } from 'react';
import { 
  Search, 
  Play, 
  Globe, 
  Server, 
  Settings, 
  AlertTriangle,
  Info
} from 'lucide-react';
import { ReconConfig } from '../../services/ReconManager';

interface ReconTargetInputProps {
  onStartScan: (target: string) => void;
  isScanning: boolean;
  config: Partial<ReconConfig>;
}

export const ReconTargetInput: React.FC<ReconTargetInputProps> = ({
  onStartScan,
  isScanning,
  config
}) => {
  const [target, setTarget] = useState('');
  const [targetType, setTargetType] = useState<'auto' | 'domain' | 'ip'>('auto');
  const [validationError, setValidationError] = useState<string | null>(null);

  const validateTarget = (input: string): boolean => {
    if (!input.trim()) {
      setValidationError('Please enter a target domain or IP address');
      return false;
    }

    const trimmed = input.trim();
    
    // Basic domain validation
    const domainRegex = /^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$/;
    
    // Basic IP validation
    const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    
    if (!domainRegex.test(trimmed) && !ipRegex.test(trimmed)) {
      setValidationError('Please enter a valid domain name or IP address');
      return false;
    }

    setValidationError(null);
    return true;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validateTarget(target)) {
      onStartScan(target.trim());
    }
  };

  const handleTargetChange = (value: string) => {
    setTarget(value);
    if (validationError && value.trim()) {
      validateTarget(value);
    }
  };

  const getEnabledSources = () => {
    const sources = [];
    if (config.enable_passive_sources) {
      sources.push('Wayback Machine', 'crt.sh', 'DNSDumpster', 'ThreatCrowd', 'HackerTarget', 'URLScan.io');
    }
    if (config.enable_api_sources) {
      sources.push('Shodan', 'Censys', 'SecurityTrails', 'VirusTotal', 'PassiveTotal');
    }
    return sources;
  };

  return (
    <div className="h-full flex items-center justify-center bg-gray-50">
      <div className="max-w-2xl w-full p-8">
        <div className="bg-white rounded-lg shadow-sm p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Search className="w-8 h-8 text-blue-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900">OSINT Reconnaissance</h2>
            <p className="text-gray-600 mt-2">
              Discover subdomains, URLs, IPs, and technologies for your target
            </p>
          </div>

          {/* Target Input Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target Domain or IP Address
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={target}
                  onChange={(e) => handleTargetChange(e.target.value)}
                  placeholder="example.com or 192.168.1.1"
                  className={`w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    validationError ? 'border-red-300' : 'border-gray-300'
                  }`}
                  disabled={isScanning}
                />
                <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                  {targetType === 'domain' ? (
                    <Globe className="w-5 h-5 text-gray-400" />
                  ) : (
                    <Server className="w-5 h-5 text-gray-400" />
                  )}
                </div>
              </div>
              {validationError && (
                <div className="mt-2 flex items-center space-x-2 text-red-600">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="text-sm">{validationError}</span>
                </div>
              )}
            </div>

            {/* Target Type Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target Type
              </label>
              <div className="grid grid-cols-3 gap-3">
                <button
                  type="button"
                  onClick={() => setTargetType('auto')}
                  className={`p-3 border rounded-lg text-sm font-medium ${
                    targetType === 'auto'
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  Auto Detect
                </button>
                <button
                  type="button"
                  onClick={() => setTargetType('domain')}
                  className={`p-3 border rounded-lg text-sm font-medium ${
                    targetType === 'domain'
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  Domain
                </button>
                <button
                  type="button"
                  onClick={() => setTargetType('ip')}
                  className={`p-3 border rounded-lg text-sm font-medium ${
                    targetType === 'ip'
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  IP Address
                </button>
              </div>
            </div>

            {/* Configuration Summary */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-3">
                <Settings className="w-4 h-4 text-gray-600" />
                <span className="text-sm font-medium text-gray-700">Scan Configuration</span>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Passive Sources:</span>
                  <span className={`ml-2 ${config.enable_passive_sources ? 'text-green-600' : 'text-red-600'}`}>
                    {config.enable_passive_sources ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">API Sources:</span>
                  <span className={`ml-2 ${config.enable_api_sources ? 'text-green-600' : 'text-red-600'}`}>
                    {config.enable_api_sources ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Include Subdomains:</span>
                  <span className={`ml-2 ${config.include_subdomains ? 'text-green-600' : 'text-red-600'}`}>
                    {config.include_subdomains ? 'Yes' : 'No'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Historical Data:</span>
                  <span className={`ml-2 ${config.include_historical ? 'text-green-600' : 'text-red-600'}`}>
                    {config.include_historical ? 'Yes' : 'No'}
                  </span>
                </div>
              </div>
            </div>

            {/* Active Sources */}
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-3">
                <Info className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-700">Active Sources</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {getEnabledSources().map((source) => (
                  <span key={source} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                    {source}
                  </span>
                ))}
              </div>
              {getEnabledSources().length === 0 && (
                <p className="text-sm text-blue-700">No sources enabled. Please configure sources in the Configuration tab.</p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isScanning || !target.trim() || getEnabledSources().length === 0}
              className={`w-full flex items-center justify-center space-x-2 py-3 px-4 rounded-lg font-medium ${
                isScanning || !target.trim() || getEnabledSources().length === 0
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              <Play className="w-4 h-4" />
              <span>{isScanning ? 'Starting Reconnaissance...' : 'Start Reconnaissance'}</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
