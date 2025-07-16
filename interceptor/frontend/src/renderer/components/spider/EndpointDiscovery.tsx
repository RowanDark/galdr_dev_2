// galdr/interceptor/frontend/src/renderer/components/spider/EndpointDiscovery.tsx
import React, { useState } from 'react';
import { 
  Database, 
  Search, 
  Filter, 
  Download, 
  RefreshCw,
  Copy,
  ExternalLink,
  Code,
  Globe,
  Activity
} from 'lucide-react';
import { DiscoveredEndpoint } from '../../services/SpiderManager';

interface EndpointDiscoveryProps {
  endpoints: DiscoveredEndpoint[];
  onRefresh: () => void;
  onExport: (format: 'json' | 'csv' | 'xlsx', dataType: string) => void;
}

export const EndpointDiscovery: React.FC<EndpointDiscoveryProps> = ({
  endpoints,
  onRefresh,
  onExport
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [methodFilter, setMethodFilter] = useState<string>('all');
  const [discoveryFilter, setDiscoveryFilter] = useState<string>('all');

  const filteredEndpoints = endpoints.filter(endpoint => {
    const matchesSearch = searchTerm === '' || 
      endpoint.url.toLowerCase().includes(searchTerm.toLowerCase()) ||
      endpoint.method.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesMethod = methodFilter === 'all' || endpoint.method === methodFilter;
    const matchesDiscovery = discoveryFilter === 'all' || endpoint.discovery_method === discoveryFilter;
    
    return matchesSearch && matchesMethod && matchesDiscovery;
  });

  const getMethodColor = (method: string) => {
    switch (method) {
      case 'GET': return 'bg-green-100 text-green-800';
      case 'POST': return 'bg-blue-100 text-blue-800';
      case 'PUT': return 'bg-yellow-100 text-yellow-800';
      case 'DELETE': return 'bg-red-100 text-red-800';
      case 'PATCH': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getDiscoveryMethodIcon = (method: string) => {
    switch (method) {
      case 'network_monitoring': return <Activity className="w-4 h-4" />;
      case 'javascript_analysis': return <Code className="w-4 h-4" />;
      case 'swagger_documentation': return <Database className="w-4 h-4" />;
      case 'html_documentation': return <Globe className="w-4 h-4" />;
      default: return <Search className="w-4 h-4" />;
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const groupEndpointsByDomain = () => {
    const grouped: Record<string, DiscoveredEndpoint[]> = {};
    
    filteredEndpoints.forEach(endpoint => {
      try {
        const domain = new URL(endpoint.url).hostname;
        if (!grouped[domain]) {
          grouped[domain] = [];
        }
        grouped[domain].push(endpoint);
      } catch {
        // Invalid URL, add to 'unknown' group
        if (!grouped['unknown']) {
          grouped['unknown'] = [];
        }
        grouped['unknown'].push(endpoint);
      }
    });
    
    return grouped;
  };

  const groupedEndpoints = groupEndpointsByDomain();

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">Discovered Endpoints</h2>
          <div className="flex items-center space-x-2">
            <button
              onClick={onRefresh}
              className="flex items-center space-x-2 px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Refresh</span>
            </button>
            <button
              onClick={() => onExport('json', 'endpoints')}
              className="flex items-center space-x-2 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              <Download className="w-4 h-4" />
              <span>Export JSON</span>
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center space-x-4 mb-4">
          <div className="flex-1 relative">
            <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
            <input
              type="text"
              placeholder="Search endpoints..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <select
              value={methodFilter}
              onChange={(e) => setMethodFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded text-sm"
            >
              <option value="all">All Methods</option>
              <option value="GET">GET</option>
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
              <option value="DELETE">DELETE</option>
              <option value="PATCH">PATCH</option>
            </select>
            <select
              value={discoveryFilter}
              onChange={(e) => setDiscoveryFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded text-sm"
            >
              <option value="all">All Discovery Methods</option>
              <option value="network_monitoring">Network Monitoring</option>
              <option value="javascript_analysis">JavaScript Analysis</option>
              <option value="swagger_documentation">Swagger Docs</option>
              <option value="html_documentation">HTML Docs</option>
            </select>
          </div>
        </div>

        {/* Stats */}
        <div className="flex items-center space-x-4 text-sm">
          <span className="bg-green-100 text-green-800 px-2 py-1 rounded">
            {filteredEndpoints.length} endpoints
          </span>
          <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
            {Object.keys(groupedEndpoints).length} domains
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="space-y-6">
          {Object.entries(groupedEndpoints).map(([domain, domainEndpoints]) => (
            <div key={domain} className="bg-white rounded-lg shadow-sm">
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">{domain}</h3>
                  <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-sm">
                    {domainEndpoints.length} endpoints
                  </span>
                </div>
              </div>

              <div className="divide-y divide-gray-100">
                {domainEndpoints.map((endpoint, index) => (
                  <div key={index} className="p-4 hover:bg-gray-50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${getMethodColor(endpoint.method)}`}>
                            {endpoint.method}
                          </span>
                          <div className="flex items-center space-x-1 text-gray-500">
                            {getDiscoveryMethodIcon(endpoint.discovery_method)}
                            <span className="text-xs">{endpoint.discovery_method.replace('_', ' ')}</span>
                          </div>
                          {endpoint.response_status && (
                            <span className={`text-xs px-2 py-1 rounded ${
                              endpoint.response_status < 300 ? 'bg-green-100 text-green-800' :
                              endpoint.response_status < 400 ? 'bg-blue-100 text-blue-800' :
                              endpoint.response_status < 500 ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {endpoint.response_status}
                            </span>
                          )}
                        </div>

                        <div className="font-mono text-sm text-gray-900 break-all mb-2">
                          {endpoint.url}
                        </div>

                        {endpoint.post_data && (
                          <div className="bg-gray-50 rounded p-2 mb-2">
                            <span className="text-xs font-medium text-gray-700">POST Data:</span>
                            <pre className="text-xs text-gray-800 mt-1 overflow-x-auto">
                              {endpoint.post_data.substring(0, 200)}
                              {endpoint.post_data.length > 200 ? '...' : ''}
                            </pre>
                          </div>
                        )}

                        <div className="text-xs text-gray-500">
                          Discovered: {new Date(endpoint.timestamp).toLocaleString()}
                        </div>
                      </div>

                      <div className="flex items-center space-x-2 ml-4">
                        <button
                          onClick={() => copyToClipboard(endpoint.url)}
                          className="p-1 text-gray-500 hover:text-gray-700"
                          title="Copy URL"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => window.open(endpoint.url, '_blank')}
                          className="p-1 text-gray-500 hover:text-gray-700"
                          title="Open in browser"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {filteredEndpoints.length === 0 && (
            <div className="text-center py-12">
              <Database className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Endpoints Found</h3>
              <p className="text-gray-600">
                {endpoints.length === 0 
                  ? 'Start a spider session to discover API endpoints and AJAX calls'
                  : 'Try adjusting your search criteria'
                }
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
