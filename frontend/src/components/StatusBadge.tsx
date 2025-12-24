import React from 'react';

interface StatusBadgeProps {
  status: 'uploaded' | 'processing' | 'completed' | 'failed' | 'pending';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const getBadgeClass = () => {
    switch (status) {
      case 'uploaded':
        return 'badge badge-uploaded';
      case 'processing':
        return 'badge badge-processing';
      case 'completed':
        return 'badge badge-completed';
      case 'failed':
        return 'badge badge-failed';
      case 'pending':
        return 'badge badge-uploaded';
      default:
        return 'badge bg-gray-100 text-gray-800';
    }
  };

  return (
    <span className={getBadgeClass()}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
};

