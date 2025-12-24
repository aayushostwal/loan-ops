import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import { RefreshCw, Trash2, Eye, TrendingUp } from 'lucide-react';
import { loanApplicationApi, handleApiError } from '../services/api';
import { FileUpload } from '../components/FileUpload';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import type { LoanApplication } from '../types';

export const LoanApplications: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [applicantName, setApplicantName] = useState('');
  const [applicantEmail, setApplicantEmail] = useState('');
  const [applicantPhone, setApplicantPhone] = useState('');
  const [createdBy, setCreatedBy] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [selectedApplication, setSelectedApplication] = useState<LoanApplication | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Fetch loan applications
  const {
    data: applicationsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['loanApplications', statusFilter],
    queryFn: () =>
      loanApplicationApi.list({
        status_filter: statusFilter || undefined,
        limit: 100,
      }),
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: loanApplicationApi.upload,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loanApplications'] });
      setSelectedFile(null);
      setApplicantName('');
      setApplicantEmail('');
      setApplicantPhone('');
      setCreatedBy('');
      setUploadError(null);
    },
    onError: (error) => {
      setUploadError(handleApiError(error));
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: loanApplicationApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loanApplications'] });
    },
  });

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    setUploadError(null);

    if (!selectedFile || !applicantName.trim()) {
      setUploadError('Please select a file and enter an applicant name');
      return;
    }

    uploadMutation.mutate({
      file: selectedFile,
      applicant_name: applicantName.trim(),
      applicant_email: applicantEmail.trim() || undefined,
      applicant_phone: applicantPhone.trim() || undefined,
      created_by: createdBy.trim() || undefined,
    });
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this loan application?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleViewDetails = async (application: LoanApplication) => {
    // Fetch full details with matches
    try {
      const fullData = await loanApplicationApi.get(application.id, true);
      setSelectedApplication(fullData);
    } catch (error) {
      console.error('Failed to fetch application details:', error);
      setSelectedApplication(application);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MMM dd, yyyy HH:mm');
    } catch {
      return dateString;
    }
  };

  const getProcessingTime = (application: LoanApplication) => {
    if (application.status === 'completed' || application.status === 'failed') {
      const start = new Date(application.created_at);
      const end = new Date(application.updated_at);
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
        <h1 className="text-3xl font-bold text-gray-900">Loan Application Management</h1>
        <p className="mt-2 text-gray-600">
          Upload and manage loan applications
        </p>
      </div>

      {/* Upload Form */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Upload Loan Application
        </h2>
        <form onSubmit={handleUpload} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Applicant Name *</label>
              <input
                type="text"
                value={applicantName}
                onChange={(e) => setApplicantName(e.target.value)}
                className="input"
                placeholder="Enter applicant name"
                disabled={uploadMutation.isPending}
                required
              />
            </div>

            <div>
              <label className="label">Email (Optional)</label>
              <input
                type="email"
                value={applicantEmail}
                onChange={(e) => setApplicantEmail(e.target.value)}
                className="input"
                placeholder="applicant@example.com"
                disabled={uploadMutation.isPending}
              />
            </div>

            <div>
              <label className="label">Phone (Optional)</label>
              <input
                type="tel"
                value={applicantPhone}
                onChange={(e) => setApplicantPhone(e.target.value)}
                className="input"
                placeholder="+1 (555) 123-4567"
                disabled={uploadMutation.isPending}
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
            disabled={uploadMutation.isPending || !selectedFile || !applicantName.trim()}
            className="btn-primary w-full"
          >
            {uploadMutation.isPending ? (
              <span className="flex items-center justify-center">
                <LoadingSpinner size="sm" className="mr-2" />
                Uploading...
              </span>
            ) : (
              'Upload Application'
            )}
          </button>
        </form>
      </div>

      {/* Applications List */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">
            Loan Applications ({applicationsData?.total || 0})
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
        ) : applicationsData && applicationsData.applications.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Applicant
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
                {applicationsData.applications.map((application) => (
                  <tr key={application.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {application.applicant_name}
                      </div>
                      {application.applicant_email && (
                        <div className="text-xs text-gray-500">{application.applicant_email}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {application.original_filename || 'N/A'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={application.status} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {getProcessingTime(application)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(application.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      <button
                        onClick={() => handleViewDetails(application)}
                        className="text-primary-600 hover:text-primary-900"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(application.id)}
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
            <p className="text-gray-500">No applications found. Upload your first application above.</p>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedApplication && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedApplication(null)}
        >
          <div
            className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-semibold text-gray-900">
                {selectedApplication.applicant_name}
              </h3>
              <button
                onClick={() => setSelectedApplication(null)}
                className="text-gray-400 hover:text-gray-600 text-2xl"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-6">
              {/* Application Info */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Status</h4>
                <StatusBadge status={selectedApplication.status} />
              </div>

              {/* Contact Info */}
              {(selectedApplication.applicant_email || selectedApplication.applicant_phone) && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Contact Information</h4>
                  <div className="bg-gray-50 p-4 rounded-lg space-y-1">
                    {selectedApplication.applicant_email && (
                      <p className="text-sm text-gray-900">Email: {selectedApplication.applicant_email}</p>
                    )}
                    {selectedApplication.applicant_phone && (
                      <p className="text-sm text-gray-900">Phone: {selectedApplication.applicant_phone}</p>
                    )}
                  </div>
                </div>
              )}

              {/* Matches */}
              {selectedApplication.matches && selectedApplication.matches.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                    <TrendingUp className="w-4 h-4 mr-2" />
                    Lender Matches ({selectedApplication.matches.length})
                  </h4>
                  <div className="space-y-2">
                    {selectedApplication.matches
                      .sort((a, b) => (b.match_score || 0) - (a.match_score || 0))
                      .map((match) => (
                        <div
                          key={match.id}
                          className="bg-gray-50 p-4 rounded-lg flex justify-between items-center"
                        >
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <span className="text-sm font-medium text-gray-900">
                                ID: {match.lender_id} | Name: {match.lender_name}
                              </span>
                              <StatusBadge status={match.status} />
                            </div>
                            {match.error_message && (
                              <p className="text-xs text-red-600 mt-1">{match.error_message}</p>
                            )}
                          </div>
                          {match.match_score !== null && (
                            <div className="text-right">
                              <div className="text-2xl font-bold text-primary-600">
                                {match.match_score.toFixed(1)}
                              </div>
                              <div className="text-xs text-gray-500">Match Score</div>
                            </div>
                          )}
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {/* Processed Data */}
              {selectedApplication.processed_data && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    Processing Result
                  </h4>
                  <pre className="bg-gray-50 p-4 rounded-lg text-xs overflow-x-auto">
                    {JSON.stringify(selectedApplication.processed_data, null, 2)}
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

