import React from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { useUIStore } from '@/stores/ui';
import {
  HomeIcon,
  UserGroupIcon,
  BookOpenIcon,
  CloudArrowUpIcon,
  MegaphoneIcon,
  Bars3Icon,
  SettingsIcon,
} from '@/components/icons';

interface NavItem {
  name: string;
  path: string;
  icon: React.ReactNode;
  children?: NavItem[];
}

const navItems: NavItem[] = [
  {
    name: 'Dashboard',
    path: '/',
    icon: <HomeIcon className="w-5 h-5" />,
  },
  {
    name: 'Customers',
    path: '/customers',
    icon: <UserGroupIcon className="w-5 h-5" />,
  },
  {
    name: 'Menu Catalog',
    path: '/menu',
    icon: <BookOpenIcon className="w-5 h-5" />,
    children: [
      { name: 'Brands', path: '/menu/brands', icon: null },
      { name: 'Items', path: '/menu/items', icon: null },
    ],
  },
  {
    name: 'Data Import',
    path: '/import',
    icon: <CloudArrowUpIcon className="w-5 h-5" />,
  },
  {
    name: 'Campaigns',
    path: '/campaigns',
    icon: <MegaphoneIcon className="w-5 h-5" />,
  },
  {
    name: 'Settings',
    path: '/settings',
    icon: <SettingsIcon className="w-5 h-5" />,
  },
];

const Sidebar: React.FC<{ open: boolean }> = ({ open }) => {
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <aside
      className={`fixed left-0 top-0 h-full bg-gray-900 text-white transition-all duration-300 ${open ? 'w-64' : 'w-0'
        } overflow-hidden`}
    >
      <div className="p-6">
        <h1 className="text-xl font-bold">AI Marketing</h1>
      </div>
      <nav className="mt-6">
        {navItems.map((item) => (
          <div key={item.path}>
            <Link
              to={item.path}
              className={`flex items-center px-6 py-3 hover:bg-gray-800 transition-colors ${isActive(item.path) ? 'bg-gray-800 border-l-4 border-primary-500' : ''
                }`}
            >
              {item.icon}
              <span className="ml-3">{item.name}</span>
            </Link>
            {item.children && isActive(item.path) && (
              <div className="ml-8">
                {item.children.map((child) => (
                  <Link
                    key={child.path}
                    to={child.path}
                    className={`flex items-center px-6 py-2 text-sm hover:bg-gray-800 transition-colors ${location.pathname === child.path ? 'text-primary-400' : 'text-gray-400'
                      }`}
                  >
                    {child.name}
                  </Link>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>
    </aside>
  );
};

const Header: React.FC = () => {
  const { toggleSidebar } = useUIStore();

  return (
    <header className="bg-white border-b border-gray-200 h-16 flex items-center px-6">
      <button
        onClick={toggleSidebar}
        className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
      >
        <Bars3Icon className="w-6 h-6" />
      </button>
      <div className="ml-auto flex items-center gap-4">
        <div className="text-sm text-gray-600">Welcome back!</div>
      </div>
    </header>
  );
};

export const DashboardLayout: React.FC = () => {
  const { sidebarOpen } = useUIStore();

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar open={sidebarOpen} />
      <div
        className={`transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-0'}`}
      >
        <Header />
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
