import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { customersApi } from '@/api/customers';
import { formatCurrency, formatDate } from '@/utils/formatting';
import { Button } from '@/components/ui';
import type { Order } from '@/types/api';

interface OrderHistoryProps {
  customerId: string;
}

export const OrderHistory = ({ customerId }: OrderHistoryProps) => {
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data, isLoading, error } = useQuery({
    queryKey: ['customer-orders', customerId, page],
    queryFn: () => customersApi.getOrders(customerId, page, pageSize),
  });

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-16 bg-gray-100 rounded"></div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Failed to load order history</p>
      </div>
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-8 text-center">
        <p className="text-gray-500">No orders found</p>
      </div>
    );
  }

  return (
    <div>
      <div className="space-y-3">
        {data.items.map((order: Order) => (
          <div
            key={order.id}
            className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex justify-between items-start">
              <div>
                <div className="text-sm font-medium text-gray-900">
                  {formatDate(order.order_date)}
                </div>
                {order.external_id && (
                  <div className="text-xs text-gray-500">Order #{order.external_id}</div>
                )}
                {order.channel && (
                  <div className="text-xs text-gray-500 mt-1">
                    Channel: {order.channel}
                  </div>
                )}
              </div>
              <div className="text-right">
                <div className="text-lg font-semibold text-gray-900">
                  {formatCurrency(order.total_amount)}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {data.pages > 1 && (
        <div className="mt-6 flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Page {data.page} of {data.pages}
          </div>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              Previous
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
              disabled={page === data.pages}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
