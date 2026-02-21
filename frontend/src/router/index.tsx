import { createBrowserRouter, Navigate } from 'react-router-dom';
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
import { PdfImportPage } from '@/pages/menu/pdf-import';
import { NotFound } from '@/pages/NotFound';
import { RouteErrorBoundary } from '@/components/RouteErrorBoundary';
import SettingsPage from '@/pages/settings';
import WelcomePage from '@/pages/welcome/WelcomePage';
import OnboardingLayout from '@/pages/onboarding/OnboardingLayout';
import BrandDetailsStep from '@/pages/onboarding/steps/BrandDetailsStep';
import MenuDataStep from '@/pages/onboarding/steps/MenuDataStep';
import OrderDataStep from '@/pages/onboarding/steps/OrderDataStep';
import ConfirmationStep from '@/pages/onboarding/steps/ConfirmationStep';
import { useSettingsStore } from '@/stores/settings';

// Root redirect component
function RootRedirect() {
  const hasCompletedOnboarding = useSettingsStore(
    (state) => state.hasCompletedOnboarding
  );

  return hasCompletedOnboarding ? <Dashboard /> : <Navigate to="/welcome" replace />;
}

export const router = createBrowserRouter([
  {
    path: '/welcome',
    element: <WelcomePage />,
  },
  {
    path: '/onboarding',
    element: <OnboardingLayout />,
    children: [
      {
        path: 'brand',
        element: <BrandDetailsStep />,
      },
      {
        path: 'menu',
        element: <MenuDataStep />,
      },
      {
        path: 'orders',
        element: <OrderDataStep />,
      },
      {
        path: 'confirm',
        element: <ConfirmationStep />,
      },
    ],
  },
  {
    path: '/',
    element: <DashboardLayout />,
    errorElement: <RouteErrorBoundary />,
    children: [
      {
        index: true,
        element: <RootRedirect />,
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
        path: 'menu/pdf-import',
        element: <PdfImportPage />,
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
      {
        path: 'settings',
        element: <SettingsPage />,
      },
    ],
  },
  {
    path: '*',
    element: <NotFound />,
  },
]);
