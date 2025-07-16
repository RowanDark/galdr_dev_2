// galdr/interceptor/frontend/src/renderer/components/recon/ReconResults.tsx
import React, { useState } from 'react';
import { 
  Download, 
  Search, 
  Globe, 
  Shield, 
  Eye, 
  Server,
  TrendingUp,
  Copy,
  ExternalLink,
  Filter,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';
import { ReconResult } from '../../services/ReconManager';

interface ReconResultsProps {
  results: ReconResult | null;
  onExport: (format: 'json' | 'csv' | 'txt') => void;
  onNewScan: () => void;
}

export const ReconResults: React.FC<ReconResultsProps> = ({
  results,
  onExport,
  onNewScan
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'subdomains' | 'urls' | 'ips' | 'analysis'>('overview');
  const [searchTerm, setSearchTerm] = useState('');
  const [showInteresting, setShowInteresting] = useState(false);

  if (!results) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <p className="text-gray-600">No results available</p>
        </div>
      </div>
    );
  }

  const filterItems = (items: string[]) => {
    if (!searchTerm) return items;
    return items.filter(item => 
      item.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  const getInterestingSubdomains = () => {
    return results.analysis.interesting_subdomains || [];
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      // Show success notification
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-blue-50 p-6 rounded-lg">
          <div className="flex items-center space-x-3">
            <Globe className="w-8 h-8 text-blue-600" />
            <div>
              <p className="text-sm text-gray-600">Subdomains</p>
              <p className="text-2xl font-bold text-blue-900">
                {results.statistics.total_subdomains_found}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-green-50 p-6 rounded-lg">
          <div className="flex items-center space-x-3">
            <Eye className="w-8 h-8 text-green-600" />
            <div>
              <p className="text-sm text-gray-600">URLs</p>
              <p className="text-2xl font-bold text-green-900">
                {results.statistics.total_urls_found}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-purple-50 p-6 rounded-lg">
          <div className="flex items-center space-x-3">
            <Server className="w-8 h-8 text-purple-600" />
            <div>
              <p className="text-sm text-gray-600">IP Addresses</p>
              <p className="text-2xl font-bold text-purple-900">
                {results.statistics.total_ips_found}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-yellow-50 p-6 rounded-lg">
          <div className="flex items-center space-x-3">
            <TrendingUp className="w-8 h-8 text-yellow-600" />
            <div>
              <p className="text-sm text-gray-600">Technologies</p>
              <p className="text-2xl font-bold text-yellow-900">
                {results.statistics.unique_technologies}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Scan Information */}
      <div className="bg-white rounded-lg p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Scan Information</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Target:</span>
            <p className="font-medium">{results.target.primary_target}</p>
          </div>
          <div>
            <span className="text-gray-600">Scan ID:</span>
            <p className="font-medium">{results.scan_id}</p>
          </div>
          <div>
            <span className="text-gray-600">Duration:</span>
            <p className="font-medium">{Math.round(results.duration_seconds)}s</p>
          </div>
          <div>
            <span className="text-gray-600">Sources:</span>
            <p className="font-medium">{results.statistics.successful_sources}/{results.statistics.sources_queried}</p>
          </div>
        </div>
      </div>

      {/* Source Status */}
      <div className="bg-white rounded-lg p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Source Results</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(results.sources).map(([sourceName, sourceData]) => (
            <div key={sourceName} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                {sourceData.success ? (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-red-600" />
                )}
                <span className="font-medium">{sourceName}</span>
              </div>
              <span className="text-sm text-gray-600">
                {sourceData.success ? `${sourceData.count} results` : 'Failed'}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderSubdomains = () => {
    const subdomains = showInteresting 
      ? getInterestingSubdomains() 
      : results.deduplicated_data.subdomains;
    const filteredSubdomains = filterItems(subdomains);

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h3 className="text-lg font-semibold text-gray-900">
              {showInteresting ? 'Interesting Subdomains' : 'All Subdomains'}
            </h3>
            <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
              {filteredSubdomains.length} results
            </span>
          </div>
          <button
            onClick={() => setShowInteresting(!showInteresting)}
            className={`px-3 py-1 rounded text-sm ${
              showInteresting 
                ? 'bg-yellow-100 text-yellow-800' 
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            {showInteresting ? 'Show All' : 'Show Interesting'}
          </button>
        </div>

        <div className="grid gap-2">
          {filteredSubdomains.map((subdomain) => (
            <div key={subdomain} className="flex items-center justify-between p-3 bg-white rounded-lg border hover:bg-gray-50">
              <div className="flex items-center space-x-3">
                <Globe className="w-4 h-4 text-gray-500" />
                <span className="font-mono text-sm">{subdomain}</span>
                {getInterestingSubdomains().includes(subdomain) && (
                  <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs">
                    Interesting
                  </span>
                )}
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => copyToClipboard(subdomain)}
                  className="p-1 text-gray-500 hover:text-gray-700"
                  title="Copy to clipboard"
                >
                  <Copy className="w-4 h-4" />
                </button>
                <button
                  onClick={() => window.open(`https://${subdomain}`, '_blank')}
                  className="p-1 text-gray-500 hover:text-gray-700"
                  title="Open in browser"
                >
                  <ExternalLink className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderUrls = () => {
    const filteredUrls = filterItems(results.deduplicated_data.urls);

    return (
      <div className="space-y-4">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-semibold text-gray-900">Discovered URLs</h3>
          <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-sm">
            {filteredUrls.length} results
          </span>
        </div>

        <div className="grid gap-2">
          {filteredUrls.map((url) => (
            <div key={url} className="flex items-center justify-between p-3 bg-white rounded-lg border hover:bg-gray-50">
              <div className="flex items-center space-x-3">
                <Eye className="w-4 h-4 text-gray-500" />
                <span className="font-mono text-sm break-all">{url}</span>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => copyToClipboard(url)}
                  className="p-1 text-gray-500 hover:text-gray-700"
                  title="Copy to clipboard"
                >
                  <Copy className="w-4 h-4" />
                </button>
                <button
                  onClick={() => window.open(url, '_blank')}
                  className="p-1 text-gray-500 hover:text-gray-700"
                  title="Open in browser"
                >
                  <ExternalLink className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderIps = () => {
    const filteredIps = filterItems(results.deduplicated_data.ips);

    return (
      <div className="space-y-4">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-semibold text-gray-900">IP Addresses</h3>
          <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded text-sm">
            {filteredIps.length} results
          </span>
        </div>

        <div className="grid gap-2">
          {filteredIps.map((ip) => (
            <div key={ip} className="flex items-center justify-between p-3 bg-white rounded-lg border hover:bg-gray-50">
              <div className="flex items-center space-x-3">
                <Server className="w-4 h-4 text-gray-500" />
                <span className="font-mono text-sm">{ip}</span>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => copyToClipboard(ip)}
                  className="p-1 text-gray-500 hover:text-gray-700"
                  title="Copy to clipboard"
                >
                  <Copy className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderAnalysis = () => (
    <div className="space-y-6">
      {/* Subdomain Patterns */}
      <div className="bg-white rounded-lg p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Subdomain Patterns</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(results.analysis.subdomain_patterns).map(([pattern, count]) => (
            <div key={pattern} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="font-mono text-sm">{pattern}</span>
              <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
                {count}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Technology Stack */}
      <div className="bg-white rounded-lg p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Technology Stack</h3>
        <div className="space-y-4">
          {Object.entries(results.analysis.technology_stack).map(([category, technologies]) => (
            <div key={category}>
              <h4 className="font-medium text-gray-700 mb-2 capitalize">
                {category.replace('_', ' ')}
              </h4>
              <div className="flex flex-wrap gap-2">
                {technologies.map((tech) => (
                  <span key={tech} className="bg-green-100 text-green-800 px-2 py-1 rounded text-sm">
                    {tech}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* IP Ranges */}
      <div className="bg-white rounded-lg p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">IP Ranges</h3>
        <div className="space-y-2">
          {Object.entries(results.analysis.ip_ranges).map(([range, ips]) => (
            <div key={range} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="font-mono text-sm">{range}</span>
              <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded text-sm">
                {ips.length} IPs
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Reconnaissance Results</h2>
            <p className="text-gray-600">{results.target.primary_target}</p>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={() => onExport('json')}
              className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
            >
              <Download className="w-4 h-4" />
              <span>Export JSON</span>
            </button>
            <button
              onClick={() => onExport('csv')}
              className="flex items-center space-x-2 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
            >
              <Download className="w-4 h-4" />
              <span>Export CSV</span>
            </button>
            <button
              onClick={onNewScan}
              className="px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm"
            >
              New Scan
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'subdomains', label: 'Subdomains' },
            { id: 'urls', label: 'URLs' },
            { id: 'ips', label: 'IPs' },
            { id: 'analysis', label: 'Analysis' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2 text-sm font-medium rounded ${
                activeTab === tab.id
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search Bar (for non-overview tabs) */}
        {activeTab !== 'overview' && activeTab !== 'analysis' && (
          <div className="mt-4">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
              <input
                type="text"
                placeholder={`Search ${activeTab}...`}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'subdomains' && renderSubdomains()}
        {activeTab === 'urls' && renderUrls()}
        {activeTab === 'ips' && renderIps()}
        {activeTab === 'analysis' && renderAnalysis()}
      </div>
    </div>
  );
};
