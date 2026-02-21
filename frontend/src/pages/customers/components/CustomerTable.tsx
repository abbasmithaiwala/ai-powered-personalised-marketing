import { Link } from 'react-router-dom';
import type { ColumnDef } from '@tanstack/react-table';
import type { Customer } from '@/types/api';
import { formatCurrency, formatDate, formatNumber } from '@/utils/formatting';
import { Badge } from '@/components/ui';
import { DataTable } from '@/components/ui/data-table';

interface CustomerTableProps {
  customers: Customer[];
  isLoading?: boolean;
}

export const CustomerTable = ({ customers, isLoading }: CustomerTableProps) => {
  const columns: ColumnDef<Customer>[] = [
    {
      id: 'name',
      accessorFn: (row) => `${row.first_name || ''} ${row.last_name || ''}`.trim(),
      header: 'Customer',
      enableSorting: true,
      sortingFn: (rowA, rowB) => {
        const nameA = `${rowA.original.first_name || ''} ${rowA.original.last_name || ''}`.trim().toLowerCase();
        const nameB = `${rowB.original.first_name || ''} ${rowB.original.last_name || ''}`.trim().toLowerCase();
        return nameA.localeCompare(nameB);
      },
      cell: ({ row }) => {
        const customer = row.original;
        return (
          <div>
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
          </div>
        );
      },
      filterFn: (row, _columnId, filterValue: string) => {
        const customer = row.original;
        const fullName = `${customer.first_name || ''} ${customer.last_name || ''}`.trim().toLowerCase();
        const email = (customer.email || '').toLowerCase();
        const externalId = (customer.external_id || '').toLowerCase();
        const searchLower = filterValue.toLowerCase();
        return fullName.includes(searchLower) || email.includes(searchLower) || externalId.includes(searchLower);
      },
    },
    {
      accessorKey: 'external_id',
      header: 'External ID',
      enableSorting: true,
      enableColumnFilter: true,
      cell: ({ row }) => {
        return (
          <div className="text-sm text-gray-600">{row.original.external_id || '—'}</div>
        );
      },
      filterFn: (row, _columnId, filterValue: string) => {
        const externalId = (row.original.external_id || '').toLowerCase();
        return externalId.includes(filterValue.toLowerCase());
      },
    },
    {
      accessorKey: 'email',
      header: 'Contact',
      enableSorting: true,
      enableColumnFilter: true,
      cell: ({ row }) => {
        const customer = row.original;
        return (
          <div>
            <div className="text-sm text-gray-900">{customer.email || '—'}</div>
            {customer.phone && (
              <div className="text-xs text-gray-500">{customer.phone}</div>
            )}
          </div>
        );
      },
      filterFn: (row, _columnId, filterValue: string) => {
        const email = (row.original.email || '').toLowerCase();
        return email.includes(filterValue.toLowerCase());
      },
    },
    {
      accessorKey: 'phone',
      header: 'Phone',
      enableSorting: true,
      enableColumnFilter: true,
      cell: ({ row }) => {
        return (
          <div className="text-sm text-gray-600">{row.original.phone || '—'}</div>
        );
      },
      filterFn: (row, _columnId, filterValue: string) => {
        const phone = (row.original.phone || '').toLowerCase();
        return phone.includes(filterValue.toLowerCase());
      },
    },
    {
      accessorKey: 'city',
      header: 'Location',
      enableSorting: true,
      enableColumnFilter: true,
      cell: ({ row }) => {
        return (
          <div className="text-sm text-gray-900">{row.original.city || '—'}</div>
        );
      },
      filterFn: (row, _columnId, filterValue: string) => {
        const city = (row.original.city || '').toLowerCase();
        return city.includes(filterValue.toLowerCase());
      },
    },
    {
      accessorKey: 'total_orders',
      header: 'Orders',
      enableSorting: true,
      cell: ({ row }) => {
        const customer = row.original;
        return (
          <Badge variant={customer.total_orders > 10 ? 'success' : 'gray'}>
            {formatNumber(customer.total_orders)}
          </Badge>
        );
      },
    },
    {
      accessorKey: 'total_spend',
      header: 'Total Spend',
      enableSorting: true,
      cell: ({ row }) => {
        return (
          <div className="text-sm font-medium text-gray-900">
            {formatCurrency(row.original.total_spend)}
          </div>
        );
      },
    },
    {
      accessorKey: 'last_order_at',
      header: 'Last Order',
      enableSorting: true,
      cell: ({ row }) => {
        const customer = row.original;
        return (
          <div className="text-sm text-gray-500">
            {customer.last_order_at ? formatDate(customer.last_order_at) : '—'}
          </div>
        );
      },
    },
  ];

  if (customers.length === 0 && !isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <p className="text-gray-500">No customers found</p>
      </div>
    );
  }

  const searchOptions = [
    { key: 'name', label: 'Name', placeholder: 'Search by name...' },
    { key: 'email', label: 'Email', placeholder: 'Search by email...' },
    { key: 'phone', label: 'Phone', placeholder: 'Search by phone...' },
    { key: 'external_id', label: 'External ID', placeholder: 'Search by ID...' },
    { key: 'city', label: 'City', placeholder: 'Search by city...' },
  ];

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden p-6">
      <DataTable
        columns={columns}
        data={customers}
        searchOptions={searchOptions}
        isLoading={isLoading}
        emptyMessage="No customers found"
        pageSize={25}
        showPagination={false}
      />
    </div>
  );
};
