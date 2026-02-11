import React from 'react';
import { Card } from '@/components/ui';

interface MetricCardProps {
  title: string;
  value: number | string;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  loading?: boolean;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  icon,
  trend,
  loading = false,
}) => {
  if (loading) {
    return (
      <Card className="animate-pulse">
        <div className="flex items-center justify-between mb-2">
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          {icon && <div className="h-8 w-8 bg-gray-200 rounded"></div>}
        </div>
        <div className="h-8 bg-gray-200 rounded w-3/4 mt-2"></div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value.toLocaleString()}</p>
          {trend && (
            <div className="flex items-center mt-2">
              <span
                className={`text-sm font-medium ${
                  trend.isPositive ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
              </span>
              <span className="text-sm text-gray-500 ml-2">vs last period</span>
            </div>
          )}
        </div>
        {icon && <div className="text-gray-400 ml-4">{icon}</div>}
      </div>
    </Card>
  );
};
