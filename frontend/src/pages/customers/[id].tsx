import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { customersApi } from '@/api/customers';
import { formatCurrency, formatDate, formatNumber, formatRelativeTime } from '@/utils/formatting';
import { Badge, Card, CardHeader, CardTitle, Button } from '@/components/ui';
import { PreferenceChart } from './components/PreferenceChart';
import { OrderHistory } from './components/OrderHistory';
import { RecommendationList } from './components/RecommendationList';

export const CustomerDetail = () => {
  const { id } = useParams<{ id: string }>();

  const { data: customer, isLoading: isLoadingCustomer } = useQuery({
    queryKey: ['customer', id],
    queryFn: () => customersApi.get(id!),
    enabled: !!id,
  });

  const { data: preferences, isLoading: isLoadingPreferences } = useQuery({
    queryKey: ['customer-preferences', id],
    queryFn: () => customersApi.getPreferences(id!),
    enabled: !!id,
  });

  if (isLoadingCustomer) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-32 bg-gray-200 rounded-lg"></div>
          <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="h-96 bg-gray-200 rounded-lg"></div>
            <div className="h-96 bg-gray-200 rounded-lg"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!customer) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-red-800">Customer not found</h2>
        <p className="mt-2 text-red-700">
          The customer you're looking for doesn't exist or has been removed.
        </p>
        <Link to="/customers" className="mt-4 inline-block">
          <Button variant="secondary">Back to Customers</Button>
        </Link>
      </div>
    );
  }

  const customerName =
    customer.first_name && customer.last_name
      ? `${customer.first_name} ${customer.last_name}`
      : customer.email || customer.external_id || 'Unknown Customer';

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Link to="/customers" className="inline-flex items-center text-blue-600 hover:text-blue-800">
        <svg
          className="w-5 h-5 mr-1"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 19l-7-7 7-7"
          />
        </svg>
        Back to Customers
      </Link>

      {/* Header */}
      <Card>
        <div className="p-6">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{customerName}</h1>
              {customer.external_id && (
                <p className="mt-1 text-sm text-gray-500">ID: {customer.external_id}</p>
              )}
            </div>
            <Badge variant={customer.total_orders > 10 ? 'success' : 'gray'} className="text-lg">
              {customer.total_orders > 20
                ? 'VIP Customer'
                : customer.total_orders > 10
                ? 'Regular Customer'
                : 'New Customer'}
            </Badge>
          </div>

          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Email & Phone */}
            <div>
              <h3 className="text-sm font-medium text-gray-500">Contact</h3>
              <p className="mt-1 text-sm text-gray-900">{customer.email || '—'}</p>
              {customer.phone && <p className="text-sm text-gray-900">{customer.phone}</p>}
            </div>

            {/* City */}
            <div>
              <h3 className="text-sm font-medium text-gray-500">Location</h3>
              <p className="mt-1 text-sm text-gray-900">{customer.city || '—'}</p>
            </div>

            {/* Stats */}
            <div>
              <h3 className="text-sm font-medium text-gray-500">Total Orders</h3>
              <p className="mt-1 text-2xl font-semibold text-gray-900">
                {formatNumber(customer.total_orders)}
              </p>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-500">Total Spend</h3>
              <p className="mt-1 text-2xl font-semibold text-gray-900">
                {formatCurrency(customer.total_spend)}
              </p>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-200 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Member since:</span>{' '}
              <span className="font-medium text-gray-900">
                {customer.first_order_at ? formatDate(customer.first_order_at) : '—'}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Last order:</span>{' '}
              <span className="font-medium text-gray-900">
                {customer.last_order_at ? formatRelativeTime(customer.last_order_at) : '—'}
              </span>
            </div>
          </div>
        </div>
      </Card>

      {/* Preferences Section */}
      <Card>
        <CardHeader>
          <CardTitle>Customer Preferences</CardTitle>
        </CardHeader>
        <div className="p-6">
          {isLoadingPreferences ? (
            <div className="animate-pulse space-y-4">
              <div className="h-48 bg-gray-100 rounded"></div>
              <div className="h-48 bg-gray-100 rounded"></div>
            </div>
          ) : preferences ? (
            <div className="space-y-8">
              {/* Dietary Flags & Frequency */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Dietary Preferences</h3>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(preferences.dietary_flags || {})
                      .filter(([, value]) => value)
                      .map(([key]) => (
                        <Badge key={key} variant="success">
                          {key.replace('_', ' ')}
                        </Badge>
                      ))}
                    {Object.keys(preferences.dietary_flags || {}).length === 0 && (
                      <span className="text-sm text-gray-500">No dietary restrictions</span>
                    )}
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Order Frequency</h3>
                  <Badge variant="blue" className="text-base">
                    {preferences.order_frequency || 'Unknown'}
                  </Badge>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Price Sensitivity</h3>
                  <Badge
                    variant={
                      preferences.price_sensitivity === 'high'
                        ? 'success'
                        : preferences.price_sensitivity === 'medium'
                        ? 'warning'
                        : 'gray'
                    }
                    className="text-base"
                  >
                    {preferences.price_sensitivity || 'Unknown'}
                  </Badge>
                </div>
              </div>

              {/* Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {preferences.favorite_cuisines &&
                  Object.keys(preferences.favorite_cuisines).length > 0 && (
                    <PreferenceChart
                      preferences={preferences.favorite_cuisines}
                      title="Favorite Cuisines"
                    />
                  )}
                {preferences.favorite_categories &&
                  Object.keys(preferences.favorite_categories).length > 0 && (
                    <PreferenceChart
                      preferences={preferences.favorite_categories}
                      title="Favorite Categories"
                    />
                  )}
              </div>

              {/* Last Computed */}
              <div className="text-xs text-gray-500">
                Preferences last updated:{' '}
                {preferences.last_computed_at
                  ? formatRelativeTime(preferences.last_computed_at)
                  : 'Never'}
              </div>
            </div>
          ) : (
            <div className="bg-gray-50 rounded-lg p-8 text-center">
              <p className="text-gray-500">No preference data available</p>
              <p className="text-sm text-gray-400 mt-2">
                Preferences will be computed after the customer places orders
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* Recommendations & Order History */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AI Recommendations */}
        <Card>
          <CardHeader>
            <CardTitle>AI Recommendations</CardTitle>
          </CardHeader>
          <div className="p-6">
            <RecommendationList customerId={id!} />
          </div>
        </Card>

        {/* Order History */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Orders</CardTitle>
          </CardHeader>
          <div className="p-6">
            <OrderHistory customerId={id!} />
          </div>
        </Card>
      </div>
    </div>
  );
};
