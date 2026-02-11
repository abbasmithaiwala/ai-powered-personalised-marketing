import { Link } from 'react-router-dom';
import type { Customer } from '@/types/api';
import { formatCurrency, formatDate, formatNumber } from '@/utils/formatting';
import { Badge } from '@/components/ui';

interface CustomerTableProps {
  customers: Customer[];
  isLoading?: boolean;
}

export const CustomerTable = ({ customers, isLoading }: CustomerTableProps) => {
  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="h-12 bg-gray-200"></div>
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 bg-gray-100 border-t border-gray-200"></div>
          ))}
        </div>
      </div>
    );
  }

  if (customers.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <p className="text-gray-500">No customers found</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Customer
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Contact
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Location
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Orders
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Total Spend
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Last Order
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {customers.map((customer) => (
              <tr key={customer.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap">
                  <Link
                    to={`/customers/${customer.id}`}
                    className="text-sm font-medium text-blue-600 hover:text-blue-800"
                  >
                    {customer.first_name && customer.last_name
                      ? `${customer.first_name} ${customer.last_name}`
                      : customer.email || customer.external_id || 'Unknown'}
                  </Link>
                  {customer.external_id && (
                    <div className="text-xs text-gray-500">ID: {customer.external_id}</div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">{customer.email || '—'}</div>
                  {customer.phone && (
                    <div className="text-xs text-gray-500">{customer.phone}</div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {customer.city || '—'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <Badge variant={customer.total_orders > 10 ? 'success' : 'gray'}>
                    {formatNumber(customer.total_orders)}
                  </Badge>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {formatCurrency(customer.total_spend)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {customer.last_order_at ? formatDate(customer.last_order_at) : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
