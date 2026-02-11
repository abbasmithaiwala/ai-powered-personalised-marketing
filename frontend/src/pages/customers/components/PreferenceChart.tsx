import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { formatPercentage, capitalize } from '@/utils/formatting';

interface PreferenceChartProps {
  preferences: Record<string, number>;
  title: string;
}

export const PreferenceChart = ({ preferences, title }: PreferenceChartProps) => {
  // Transform preferences object into array for recharts
  const data = Object.entries(preferences)
    .sort(([, a], [, b]) => b - a) // Sort by score descending
    .slice(0, 5) // Top 5
    .map(([name, score]) => ({
      name: capitalize(name),
      score: score * 100, // Convert to percentage
    }));

  if (data.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-6 text-center">
        <p className="text-gray-500">No {title.toLowerCase()} data available</p>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-sm font-medium text-gray-700 mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} layout="vertical" margin={{ left: 60, right: 20 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" domain={[0, 100]} tickFormatter={(value) => `${value}%`} />
          <YAxis type="category" dataKey="name" width={80} />
          <Tooltip
            formatter={(value: number | undefined) => formatPercentage((value ?? 0) / 100, 1)}
            labelStyle={{ color: '#374151' }}
          />
          <Bar dataKey="score" fill="#3b82f6" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
