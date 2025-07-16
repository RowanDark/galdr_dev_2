// galdr/interceptor/frontend/src/renderer/components/crawler/SecurityFindings.tsx
import React, { useState } from 'react';
import { 
  Shield, 
  Key, 
  AlertTriangle, 
  Info, 
  Download, 
  RefreshCw,
  Eye,
  EyeOff,
  Copy,
  Filter
} from 'lucide-react';
import { VulnerabilityFinding, SecretFinding } from '../../services/CrawlerManager';

interface SecurityFindingsProps {
  vulnerabilities: VulnerabilityFinding[];
  secrets: SecretFinding[];
  onRefresh: () => void;
  onExport: (format: 'json' | 'csv' | 'xlsx', dataType: string) => void;
}

export const SecurityFindings: React.FC<SecurityFindingsProps> = ({
  vulnerabilities,
  secrets,
  onRefresh,
  onExport
}) => {
  const [activeTab, setActiveTab] = useState<'vulnerabilities' | 'secrets'>('vulnerabilities');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [showSecretValues, setShowSecretValues] = useState(false);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'Critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'High': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'Medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'Low': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'Critical':
      case 'High':
        return <AlertTriangle className="w-4 h-4" />;
      case 'Medium':
        return <Info className="w-4 h-4" />;
      case 'Low':
        return <Shield className="w-4 h-4" />;
      default:
        return <Info className="w-4 h-4" />;
    }
  };

  const filterBySeverity = <T extends { severity: string }>(items: T[]) => {
    if (severityFilter === 'all') return items;
    return items.filter(item => item.severity === severityFilter);
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const renderVulnerabilities = () => {
    const filteredVulns = filterBySeverity(vulnerabilities);

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Vulnerability Findings</h3>
          <div className="flex items-center space-x-2">
            <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-sm">
              {filteredVulns.length} vulnerabilities
            </span>
            <button
              onClick={() => onExport('json', 'vulnerabilities')}
              className="flex items-center space-x-1 px-3 py-1 bg-yellow-600 text-white rounded hover:bg-yellow-700 text-sm"
            >
              <Download className="w-4 h-4" />
              <span>Export</span>
            </button>
          </div>
        </div>

        <div className="space-y-3">
          {filteredVulns.map((vuln, index) => (
            <div key={index} className="bg-white rounded-lg border p-4 hover:shadow-sm transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-full border ${getSeverityColor(vuln.severity)}`}>
                    {getSeverityIcon(vuln.severity)}
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">{vuln.type}</h4>
                    <p className="text-sm text-gray-600">{vuln.location.url}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getSeverityColor(vuln.severity)}`}>
                    {vuln.severity}
                  </span>
                  <span className="text-xs text-gray-500">
                    {Math.round(vuln.confidence * 100)}% confidence
                  </span>
                </div>
              </div>

              <p className="text-gray-700 mb-3">{vuln.description}</p>

              {vuln.evidence && (
                <div className="bg-gray-50 rounded p-3 mb-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Evidence</span>
                    <button
                      onClick={() => copyToClipboard(vuln.evidence)}
                      className="p-1 text-gray-500 hover:text-gray-700"
                      title="Copy evidence"
                    >
                      <Copy className="w-4 h-4" />
                    </button>
                  </div>
                  <code className="text-sm text-gray-800 font-mono break-all">
                    {vuln.evidence}
                  </code>
                </div>
              )}

              <div className="bg-blue-50 rounded p-3">
                <span className="text-sm font-medium text-blue-700">Remediation:</span>
                <p className="text-sm text-blue-800 mt-1">{vuln.remediation}</p>
              </div>

              <div className="mt-3 text-xs text-gray-500">
                Found at {new Date(vuln.timestamp).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderSecrets = () => {
    const filteredSecrets = filterBySeverity(secrets);

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Exposed Secrets</h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowSecretValues(!showSecretValues)}
              className="flex items-center space-x-1 px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700 text-sm"
            >
              {showSecretValues ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              <span>{showSecretValues ? 'Hide' : 'Show'} Values</span>
            </button>
            <span className="bg-red-100 text-red-800 px-2 py-1 rounded text-sm">
              {filteredSecrets.length} secrets
            </span>
            <button
              onClick={() => onExport('json', 'secrets')}
              className="flex items-center space-x-1 px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
            >
              <Download className="w-4 h-4" />
              <span>Export</span>
            </button>
          </div>
        </div>

        <div className="space-y-3">
          {filteredSecrets.map((secret, index) => (
            <div key={index} className="bg-white rounded-lg border p-4 hover:shadow-sm transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-full border ${getSeverityColor(secret.severity)}`}>
                    <Key className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">{secret.type}</h4>
                    <p className="text-sm text-gray-600">{secret.location.url}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getSeverityColor(secret.severity)}`}>
                    {secret.severity}
                  </span>
                  <span className="text-xs text-gray-500">
                    {Math.round(secret.confidence * 100)}% confidence
                  </span>
                </div>
              </div>

              <div className="bg-gray-50 rounded p-3 mb-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Secret Value</span>
                  <button
                    onClick={() => copyToClipboard(showSecretValues ? secret.value : secret.masked_value)}
                    className="p-1 text-gray-500 hover:text-gray-700"
                    title="Copy secret"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                </div>
                <code className="text-sm text-gray-800 font-mono break-all">
                  {showSecretValues ? secret.value : secret.masked_value}
                </code>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Location Type:</span>
                  <span className="ml-2 text-gray-600">{secret.location.type}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Entropy:</span>
                  <span className="ml-2 text-gray-600">{secret.entropy.toFixed(2)}</span>
                </div>
              </div>

              {(secret.location.header_name || secret.location.parameter_name) && (
                <div className="mt-2 text-sm">
                  <span className="font-medium text-gray-700">
                    {secret.location.header_name ? 'Header' : 'Parameter'}:
                  </span>
                  <span className="ml-2 text-gray-600 font-mono">
                    {secret.location.header_name || secret.location.parameter_name}
                  </span>
                </div>
              )}

              <div className="mt-3 text-xs text-gray-500">
                Found at {new Date(secret.timestamp).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const getSeverityStats = () => {
    const currentItems = activeTab === 'vulnerabilities' ? vulnerabilities : secrets;
    const stats = { Critical: 0, High: 0, Medium: 0, Low: 0 };
    
    currentItems.forEach(item => {
      if (stats.hasOwnProperty(item.severity)) {
        stats[item.severity]++;
      }
    });
    
    return stats;
  };

  const severityStats = getSeverityStats();

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">Security Findings</h2>
          <button
            onClick={onRefresh}
            className="flex items-center space-x-2 px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg mb-4">
          <button
            onClick={() => setActiveTab('vulnerabilities')}
            className={`px-4 py-2 text-sm font-medium rounded ${
              activeTab === 'vulnerabilities'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Vulnerabilities ({vulnerabilities.length})
          </button>
          <button
            onClick={() => setActiveTab('secrets')}
            className={`px-4 py-2 text-sm font-medium rounded ${
              activeTab === 'secrets'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Secrets ({secrets.length})
          </button>
        </div>

        {/* Severity Filter */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded text-sm"
            >
              <option value="all">All Severities</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>

          {/* Severity Stats */}
          <div className="flex space-x-2">
            {Object.entries(severityStats).map(([severity, count]) => (
              <span
                key={severity}
                className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(severity)}`}
              >
                {severity}: {count}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'vulnerabilities' && renderVulnerabilities()}
        {activeTab === 'secrets' && renderSecrets()}
      </div>
    </div>
  );
};
