import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/api/dashboard';
import { MetricCard } from './components/MetricCard';
import { RecentImports } from './components/RecentImports';
import {
  UserGroupIcon,
  ShoppingBagIcon,
  MegaphoneIcon,
  EnvelopeIcon,
  CloudArrowUpIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  ChevronRightIcon,
} from '@/components/icons';

export const Dashboard: React.FC = () => {
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: dashboardApi.getMetrics,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Welcome to your AI-powered marketing platform</p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard
          title="Total Customers"
          value={metrics?.total_customers ?? 0}
          icon={<UserGroupIcon className="w-8 h-8" />}
          loading={isLoading}
        />
        <MetricCard
          title="Orders (30d)"
          value={metrics?.total_orders_30d ?? 0}
          icon={<ShoppingBagIcon className="w-8 h-8" />}
          loading={isLoading}
        />
        <MetricCard
          title="Active Campaigns"
          value={metrics?.active_campaigns ?? 0}
          icon={<MegaphoneIcon className="w-8 h-8" />}
          loading={isLoading}
        />
        <MetricCard
          title="Messages Generated"
          value={metrics?.messages_generated ?? 0}
          icon={<EnvelopeIcon className="w-8 h-8" />}
          loading={isLoading}
        />
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecentImports />

        {/* Quick Actions */}
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <a
              href="/import"
              className="flex items-center justify-between p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-colors group"
            >
              <div className="flex items-center">
                <CloudArrowUpIcon className="w-5 h-5 text-gray-400 group-hover:text-primary-600" />
                <span className="ml-3 font-medium text-gray-900 group-hover:text-primary-700">
                  Import Customer Data
                </span>
              </div>
              <ChevronRightIcon className="w-5 h-5 text-gray-400" />
            </a>

            <a
              href="/campaigns/new"
              className="flex items-center justify-between p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-colors group"
            >
              <div className="flex items-center">
                <PlusIcon className="w-5 h-5 text-gray-400 group-hover:text-primary-600" />
                <span className="ml-3 font-medium text-gray-900 group-hover:text-primary-700">
                  Create New Campaign
                </span>
              </div>
              <ChevronRightIcon className="w-5 h-5 text-gray-400" />
            </a>

            <a
              href="/customers"
              className="flex items-center justify-between p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-colors group"
            >
              <div className="flex items-center">
                <MagnifyingGlassIcon className="w-5 h-5 text-gray-400 group-hover:text-primary-600" />
                <span className="ml-3 font-medium text-gray-900 group-hover:text-primary-700">
                  Browse Customers
                </span>
              </div>
              <ChevronRightIcon className="w-5 h-5 text-gray-400" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
