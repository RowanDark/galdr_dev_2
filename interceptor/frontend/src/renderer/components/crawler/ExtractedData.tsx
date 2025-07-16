// galdr/interceptor/frontend/src/renderer/components/crawler/ExtractedData.tsx
import React, { useState, useEffect } from 'react';
import { 
  Download, 
  Search, 
  Filter, 
  Globe, 
  Mail, 
  FileText, 
  Copy,
  ExternalLink,
  RefreshCw
} from 'lucide-react';
import { CrawlerManager } from '../../services/CrawlerManager';

interface ExtractedDataProps {
  crawlerManager: CrawlerManager;
  onExport: (format: 'json' | 'csv' | 'xlsx', dataType: string) => void;
}

export const ExtractedData: React.FC<ExtractedDataProps> = ({
  crawlerManager,
  onExport
}) => {
  const [activeTab, setActiveTab] = useState<'links' | 'emails' | 'files'>('links');
  const [searchTerm, setSearchTerm] = useState('');
  const [links, setLinks] = useState<string[]>([]);
  const [emails, setEmails] = useState<string[]>([]);
  const [files, setFiles] = useState<Record<string, string[]>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [linksData, emailsData, filesData] = await Promise.all([
        crawlerManager.getExtractedLinks(),
        crawlerManager.getExtractedEmails(),
        crawlerManager.getExtractedFiles()
      ]);
      
      setLinks(linksData);
      setEmails(emailsData);
      setFiles(filesData);
    } catch (error) {
      console.error('Failed to load extracted data:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterItems = (items: string[]) => {
    if (!searchTerm) return items;
    return items.filter(item => 
      item.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      // Show success notification
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const renderLinks = () => {
    const filteredLinks = filterItems(links);
    
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Extracted Links</h3>
          <div className="flex items-center space-x-2">
            <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
              {filteredLinks.length} links
            </span>
            <button
              onClick={() => onExport('csv', 'links')}
              className="flex items-center space-x-1 px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
            >
              <Download className="w-4 h-4" />
              <span>Export</span>
            </button>
          </div>
        </div>

        <div className="grid gap-2">
          {filteredLinks.map((link, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-white rounded-lg border hover:bg-gray-50">
              <div className="flex items-center space-x-3">
                <Globe className="w-4 h-4 text-gray-500" />
                <span className="font-mono text-sm break-all">{link}</span>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => copyToClipboard(link)}
                  className="p-1 text-gray-500 hover:text-gray-700"
                  title="Copy to clipboard"
                >
                  <Copy className="w-4 h-4" />
                </button>
                <button
                  onClick={() => window.open(link, '_blank')}
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

  const renderEmails = () => {
    const filteredEmails = filterItems(emails);
    
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Extracted Email Addresses</h3>
          <div className="flex items-center space-x-2">
            <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-sm">
              {filteredEmails.length} emails
            </span>
            <button
              onClick={() => onExport('csv', 'emails')}
              className="flex items-center space-x-1 px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
            >
              <Download className="w-4 h-4" />
              <span>Export</span>
            </button>
          </div>
        </div>

        <div className="grid gap-2">
          {filteredEmails.map((email, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-white rounded-lg border hover:bg-gray-50">
              <div className="flex items-center space-x-3">
                <Mail className="w-4 h-4 text-gray-500" />
                <span className="font-mono text-sm">{email}</span>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => copyToClipboard(email)}
                  className="p-1 text-gray-500 hover:text-gray-700"
                  title="Copy to clipboard"
                >
                  <Copy className="w-4 h-4" />
                </button>
                <button
                  onClick={() => window.open(`mailto:${email}`, '_blank')}
                  className="p-1 text-gray-500 hover:text-gray-700"
                  title="Send email"
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

  const renderFiles = () => {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Extracted Files</h3>
          <button
            onClick={() => onExport('json', 'files')}
            className="flex items-center space-x-1 px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700 text-sm"
          >
            <Download className="w-4 h-4" />
            <span>Export</span>
          </button>
        </div>

        {Object.entries(files).map(([fileType, fileList]) => {
          const filteredFiles = filterItems(fileList);
          
          return (
            <div key={fileType} className="bg-white rounded-lg p-4 border">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-gray-900 capitalize">
                  {fileType.replace('_', ' ')} Files
                </h4>
                <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded text-sm">
                  {filteredFiles.length} files
                </span>
              </div>
              
              <div className="space-y-2">
                {filteredFiles.map((file, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div className="flex items-center space-x-2">
                      <FileText className="w-4 h-4 text-gray-500" />
                      <span className="font-mono text-sm break-all">{file}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => copyToClipboard(file)}
                        className="p-1 text-gray-500 hover:text-gray-700"
                        title="Copy to clipboard"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => window.open(file, '_blank')}
                        className="p-1 text-gray-500 hover:text-gray-700"
                        title="Open file"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">Extracted Data</h2>
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center space-x-2 px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab('links')}
            className={`px-4 py-2 text-sm font-medium rounded ${
              activeTab === 'links'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Links ({links.length})
          </button>
          <button
            onClick={() => setActiveTab('emails')}
            className={`px-4 py-2 text-sm font-medium rounded ${
              activeTab === 'emails'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Emails ({emails.length})
          </button>
          <button
            onClick={() => setActiveTab('files')}
            className={`px-4 py-2 text-sm font-medium rounded ${
              activeTab === 'files'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Files ({Object.values(files).flat().length})
          </button>
        </div>

        {/* Search */}
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
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <RefreshCw className="w-8 h-8 animate-spin text-gray-400" />
          </div>
        ) : (
          <>
            {activeTab === 'links' && renderLinks()}
            {activeTab === 'emails' && renderEmails()}
            {activeTab === 'files' && renderFiles()}
          </>
        )}
      </div>
    </div>
  );
};
