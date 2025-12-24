import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import { RefreshCw, Trash2, Eye } from 'lucide-react';
import { lenderApi, handleApiError } from '../services/api';
import { FileUpload } from '../components/FileUpload';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import type { Lender } from '../types';

export const Lenders: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [lenderName, setLenderName] = useState('');
  const [createdBy, setCreatedBy] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [selectedLender, setSelectedLender] = useState<Lender | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Fetch lenders
  const {
    data: lendersData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['lenders', statusFilter],
    queryFn: () =>
      lenderApi.list({
        status_filter: statusFilter || undefined,
        limit: 100,
      }),
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: lenderApi.upload,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lenders'] });
      setSelectedFile(null);
      setLenderName('');
      setCreatedBy('');
      setUploadError(null);
    },
    onError: (error) => {
      setUploadError(handleApiError(error));
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: lenderApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lenders'] });
    },
  });

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    setUploadError(null);

    if (!selectedFile || !lenderName.trim()) {
      setUploadError('Please select a file and enter a lender name');
      return;
    }

    uploadMutation.mutate({
      file: selectedFile,
      lender_name: lenderName.trim(),
      created_by: createdBy.trim() || undefined,
    });
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this lender?')) {
      deleteMutation.mutate(id);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MMM dd, yyyy HH:mm');
    } catch {
      return dateString;
    }
  };

  const getProcessingTime = (lender: Lender) => {
    if (lender.status === 'completed' || lender.status === 'failed') {
      const start = new Date(lender.created_at);
      const end = new Date(lender.updated_at);
      const diff = Math.abs(end.getTime() - start.getTime());
      const seconds = Math.floor(diff / 1000);
      return `${seconds}s`;
    }
    return '-';
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Lender Policy Management</h1>
        <p className="mt-2 text-gray-600">
          Upload and manage lending policy documents
        </p>
      </div>

      {/* Upload Form */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Upload Lending Policy Document
        </h2>
        <form onSubmit={handleUpload} className="space-y-4">
          <div>
            <label className="label">Lender Name *</label>
            <input
              type="text"
              value={lenderName}
              onChange={(e) => setLenderName(e.target.value)}
              className="input"
              placeholder="Enter lender name"
              disabled={uploadMutation.isPending}
              required
            />
          </div>

          <div>
            <label className="label">Created By (Optional)</label>
            <input
              type="text"
              value={createdBy}
              onChange={(e) => setCreatedBy(e.target.value)}
              className="input"
              placeholder="Your name"
              disabled={uploadMutation.isPending}
            />
          </div>

          <div>
            <label className="label">PDF Document *</label>
            <FileUpload
              selectedFile={selectedFile}
              onFileSelect={setSelectedFile}
              onClear={() => setSelectedFile(null)}
              disabled={uploadMutation.isPending}
            />
          </div>

          {uploadError && (
            <ErrorMessage
              message={uploadError}
              onRetry={() => setUploadError(null)}
            />
          )}

          <button
            type="submit"
            disabled={uploadMutation.isPending || !selectedFile || !lenderName.trim()}
            className="btn-primary w-full"
          >
            {uploadMutation.isPending ? (
              <span className="flex items-center justify-center">
                <LoadingSpinner size="sm" className="mr-2" />
                Uploading...
              </span>
            ) : (
              'Upload Document'
            )}
          </button>
        </form>
      </div>

      {/* Lenders List */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">
            Uploaded Lenders ({lendersData?.total || 0})
          </h2>
          <div className="flex items-center space-x-4">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input w-auto"
            >
              <option value="">All Statuses</option>
              <option value="uploaded">Uploaded</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
            <button
              onClick={() => refetch()}
              className="btn-secondary flex items-center"
              disabled={isLoading}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        {error && (
          <ErrorMessage message={handleApiError(error)} onRetry={() => refetch()} />
        )}

        {isLoading ? (
          <LoadingSpinner className="py-12" />
        ) : lendersData && lendersData.lenders.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Lender Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Document
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Processing Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created At
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {lendersData.lenders.map((lender) => (
                  <tr key={lender.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {lender.lender_name}
                      </div>
                      {lender.created_by && (
                        <div className="text-xs text-gray-500">by {lender.created_by}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {lender.original_filename || 'N/A'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={lender.status} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {getProcessingTime(lender)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(lender.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      <button
                        onClick={() => setSelectedLender(lender)}
                        className="text-primary-600 hover:text-primary-900"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(lender.id)}
                        disabled={deleteMutation.isPending}
                        className="text-red-600 hover:text-red-900 disabled:opacity-50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-500">No lenders found. Upload your first document above.</p>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedLender && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedLender(null)}
        >
          <div
            className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-semibold text-gray-900">
                {selectedLender.lender_name}
              </h3>
              <button
                onClick={() => setSelectedLender(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Status</h4>
                <StatusBadge status={selectedLender.status} />
              </div>
              {selectedLender.processed_data && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    Processing Result
                  </h4>
                  <pre className="bg-gray-50 p-4 rounded-lg text-xs overflow-x-auto">
                    {JSON.stringify(selectedLender.processed_data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

