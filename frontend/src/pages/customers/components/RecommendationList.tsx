import { useQuery } from '@tanstack/react-query';
import { customersApi } from '@/api/customers';
import { formatCurrency } from '@/utils/formatting';
import { Badge } from '@/components/ui';

interface RecommendationListProps {
  customerId: string;
}

export const RecommendationList = ({ customerId }: RecommendationListProps) => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['customer-recommendations', customerId],
    queryFn: () => customersApi.getRecommendations(customerId, 5),
  });

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-24 bg-gray-100 rounded"></div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Failed to load recommendations</p>
      </div>
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-8 text-center">
        <p className="text-gray-500">No recommendations available</p>
        <p className="text-sm text-gray-400 mt-2">
          Recommendations will appear once the customer has sufficient order history
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {data.items.map((item, index) => (
        <div
          key={item.menu_item_id}
          className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <Badge variant="blue">{index + 1}</Badge>
                <h4 className="text-base font-semibold text-gray-900">{item.name}</h4>
              </div>
              <div className="mt-1 text-sm text-gray-600">{item.brand_name}</div>
              {item.category && (
                <div className="mt-1 text-xs text-gray-500">
                  {item.category}
                </div>
              )}
              <div className="mt-2 text-sm text-gray-700 italic">
                "{item.reason}"
              </div>
            </div>
            <div className="ml-4 flex flex-col items-end">
              {item.price && (
                <div className="text-lg font-semibold text-gray-900">
                  {formatCurrency(item.price)}
                </div>
              )}
              <div className="mt-1 text-xs text-gray-500">
                Match: {Math.round(item.score * 100)}%
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
