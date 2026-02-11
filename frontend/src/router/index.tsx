import { createBrowserRouter } from 'react-router-dom';
import { DashboardLayout } from '@/layouts/DashboardLayout';
import { Dashboard } from '@/pages/dashboard';
import { Import } from '@/pages/import';
import { NotFound } from '@/pages/NotFound';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <DashboardLayout />,
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      // Placeholder routes - will be implemented in subsequent tasks
      {
        path: 'customers',
        element: <div className="text-2xl">Customers (Coming in TASK-020)</div>,
      },
      {
        path: 'customers/:id',
        element: <div className="text-2xl">Customer Detail (Coming in TASK-020)</div>,
      },
      {
        path: 'menu',
        element: <div className="text-2xl">Menu Catalog (Coming in TASK-022)</div>,
      },
      {
        path: 'menu/brands',
        element: <div className="text-2xl">Brands (Coming in TASK-022)</div>,
      },
      {
        path: 'menu/brands/:id',
        element: <div className="text-2xl">Brand Detail (Coming in TASK-022)</div>,
      },
      {
        path: 'menu/items',
        element: <div className="text-2xl">Menu Items (Coming in TASK-022)</div>,
      },
      {
        path: 'import',
        element: <Import />,
      },
      {
        path: 'campaigns',
        element: <div className="text-2xl">Campaigns (Coming in TASK-021)</div>,
      },
      {
        path: 'campaigns/new',
        element: <div className="text-2xl">New Campaign (Coming in TASK-021)</div>,
      },
      {
        path: 'campaigns/:id',
        element: <div className="text-2xl">Campaign Detail (Coming in TASK-021)</div>,
      },
    ],
  },
  {
    path: '*',
    element: <NotFound />,
  },
]);
