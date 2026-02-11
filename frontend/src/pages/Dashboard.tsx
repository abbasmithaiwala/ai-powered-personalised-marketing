import React from 'react';
import { Card, CardTitle } from '@/components/ui';

export const Dashboard: React.FC = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardTitle>Total Customers</CardTitle>
          <p className="text-3xl font-bold mt-2">-</p>
        </Card>
        <Card>
          <CardTitle>Orders (30d)</CardTitle>
          <p className="text-3xl font-bold mt-2">-</p>
        </Card>
        <Card>
          <CardTitle>Active Campaigns</CardTitle>
          <p className="text-3xl font-bold mt-2">-</p>
        </Card>
        <Card>
          <CardTitle>Messages Generated</CardTitle>
          <p className="text-3xl font-bold mt-2">-</p>
        </Card>
      </div>
    </div>
  );
};
