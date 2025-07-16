// galdr/interceptor/frontend/src/renderer/components/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import { 
  Play, 
  Square, 
  Activity, 
  Globe, 
  Clock, 
  TrendingUp, 
  Shield, 
  Wifi,
  AlertCircle,
  CheckCircle,
  Users
} from 'lucide-react';
import { InterceptedTraffic, ProxyStats, SSLConnectionInfo } from '../types/traffic';

interface DashboardProps {
  traffic: InterceptedTraffic[];
  proxyStatus: 'stopped' | 'starting' | 'running' | 'error';
  proxyStats: ProxyStats;
  sslConnections: SSLConnectionInfo[];
  websocketConnected: boolean;
  onStartProxy: () => void;
  onStopProxy: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  traffic,
  proxyStatus,
  proxyStats,
  sslConnections,
  websocketConnected,
  onStartProxy,
  onStopProxy
}) => {
  const [realtimeTraffic, setRealtimeTraffic] = useState<InterceptedTraffic[]>([]);

  useEffect(() => {
    // Update realtime traffic display (last 10 requests)
    setRealtimeTraffic(traffic.slice(0, 10));
  }, [traffic]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'text-green-500';
      case 'starting': return 'text-yellow-500';
      case 'error': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <CheckCircle className="w-5 h-5" />;
      case 'starting': return <Activity className="w-5 h-5 animate-spin" />;
      case 'error': return <AlertCircle className="w-5 h-5" />;
      default: return <Square className="w-5 h-5" />;
    }
  };

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      <div className="p-6">
        {/* Header with Real-time Status */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <div className="flex items-center space-x-4 mt-1">
              <div className={`flex items-center space-x-2 ${getStatusColor(proxyStatus)}`}>
                {getStatusIcon(proxyStatus)}
                <span className="text-sm font-medium capitalize">{proxyStatus}</span>
              </div>
              <div className={`flex items-center space-x-2 ${websocketConnected ? 'text-green-500' : 'text-red-500'}`}>
                <Wifi className="w-4 h-4" />
                <span className="text-sm">WebSocket {websocketConnected ? 'Connected' : 'Disconnected'}</span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            {proxyStatus === 'running' ? (
              <button
                onClick={onStopProxy}
                className="flex items-center space-x-2 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
              >
                <Square className="w-4 h-4" />
                <span>Stop Proxy</span>
              </button>
            ) : (
              <button
                onClick={onStartProxy}
                className="flex items-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                disabled={proxyStatus === 'starting'}
              >
                <Play className="w-4 h-4" />
                <span>{proxyStatus === 'starting' ? 'Starting...' : 'Start Proxy'}</span>
              </button>
            )}
          </div>
        </div>

        {/* Enhanced Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Requests</p>
                <p className="text-2xl font-bold text-gray-900">{proxyStats.total_requests}</p>
                <p className="text-xs text-gray-500 mt-1">Real-time count</p>
              </div>
              <Activity className="w-8 h-8 text-blue-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Unique Hosts</p>
                <p className="text-2xl font-bold text-gray-900">{proxyStats.unique_hosts}</p>
                <p className="text-xs text-gray-500 mt-1">Active targets</p>
              </div>
              <Globe className="w-8 h-8 text-green-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">SSL Connections</p>
                <p className="text-2xl font-bold text-gray-900">{proxyStats.ssl_connections}</p>
                <p className="text-xs text-gray-500 mt-1">HTTPS bumping</p>
              </div>
              <Shield className="w-8 h-8 text-purple-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">WebSocket Clients</p>
                <p className="text-2xl font-bold text-gray-900">{proxyStats.websocket_clients}</p>
                <p className="text-xs text-gray-500 mt-1">Connected GUIs</p>
              </div>
              <Users className="w-8 h-8 text-indigo-500" />
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Performance</h3>
              <Clock className="w-5 h-5 text-gray-400" />
            </div>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Avg Response Time</span>
                <span className="text-sm font-medium">{proxyStats.average_response_time.toFixed(0)}ms</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Error Rate</span>
                <span className="text-sm font-medium">{proxyStats.error_rate.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Uptime</span>
                <span className="text-sm font-medium">{Math.floor(proxyStats.uptime_seconds / 3600)}h {Math.floor((proxyStats.uptime_seconds % 3600) / 60)}m</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">SSL Connections</h3>
              <Shield className="w-5 h-5 text-gray-400" />
            </div>
            <div className="space-y-2">
              {sslConnections.slice(0, 3).map((conn, index) => (
                <div key={index} className="flex justify-between items-center">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{conn.hostname}</p>
                    <p className="text-xs text-gray-500">{conn.duration_seconds.toFixed(1)}s active</p>
                  </div>
                  <div className="text-xs text-gray-500">
                    {Math.round(conn.bytes_sent / 1024)}KB ↑
                  </div>
                </div>
              ))}
              {sslConnections.length === 0 && (
                <p className="text-sm text-gray-500">No active SSL connections</p>
              )}
            </div>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Certificate Status</h3>
              <CheckCircle className="w-5 h-5 text-green-500" />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">CA Certificate</span>
                <span className="text-sm font-medium text-green-600">Valid</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Generated Certs</span>
                <span className="text-sm font-medium">{proxyStats.unique_hosts}</span>
              </div>
              <button className="w-full mt-2 text-xs text-blue-600 hover:text-blue-700">
                View Certificate Installation Guide
              </button>
            </div>
          </div>
        </div>

        {/* Real-time Traffic Stream */}
        <div className="bg-white rounded-lg shadow-sm">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Live Traffic Stream</h2>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-600">Real-time</span>
              </div>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Method
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    URL
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {realtimeTraffic.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(item.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                        item.method === 'GET' ? 'bg-green-100 text-green-800' :
                        item.method === 'POST' ? 'bg-blue-100 text-blue-800' :
                        item.method === 'PUT' ? 'bg-yellow-100 text-yellow-800' :
                        item.method === 'DELETE' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {item.method}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 truncate max-w-xs">
                      {item.url}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`text-sm font-medium ${
                        !item.response ? 'text-gray-500' :
                        item.response.status_code < 300 ? 'text-green-600' :
                        item.response.status_code < 400 ? 'text-blue-600' :
                        item.response.status_code < 500 ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {item.response?.status_code || 'Pending'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        {item.is_https && <Shield className="w-4 h-4 text-purple-500" />}
                        <span className="text-sm text-gray-600">
                          {item.is_https ? 'HTTPS' : 'HTTP'}
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
