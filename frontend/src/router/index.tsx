import { createBrowserRouter } from 'react-router-dom';
import { DashboardLayout } from '@/layouts/DashboardLayout';
import { Dashboard } from '@/pages/dashboard';
import { Import } from '@/pages/import';
import { Customers } from '@/pages/customers';
import { CustomerDetail } from '@/pages/customers/[id]';
import { Campaigns } from '@/pages/campaigns';
import { NewCampaign } from '@/pages/campaigns/new';
import { CampaignDetail } from '@/pages/campaigns/[id]';
import { MenuOverview } from '@/pages/menu';
import { BrandsList } from '@/pages/menu/brands';
import { BrandDetail } from '@/pages/menu/brands/[id]';
import { MenuItems } from '@/pages/menu/items';
import { NotFound } from '@/pages/NotFound';
import { RouteErrorBoundary } from '@/components/RouteErrorBoundary';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <DashboardLayout />,
    errorElement: <RouteErrorBoundary />,
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: 'customers',
        element: <Customers />,
      },
      {
        path: 'customers/:id',
        element: <CustomerDetail />,
      },
      {
        path: 'menu',
        element: <MenuOverview />,
      },
      {
        path: 'menu/brands',
        element: <BrandsList />,
      },
      {
        path: 'menu/brands/:id',
        element: <BrandDetail />,
      },
      {
        path: 'menu/items',
        element: <MenuItems />,
      },
      {
        path: 'import',
        element: <Import />,
      },
      {
        path: 'campaigns',
        element: <Campaigns />,
      },
      {
        path: 'campaigns/new',
        element: <NewCampaign />,
      },
      {
        path: 'campaigns/:id',
        element: <CampaignDetail />,
      },
    ],
  },
  {
    path: '*',
    element: <NotFound />,
  },
]);
