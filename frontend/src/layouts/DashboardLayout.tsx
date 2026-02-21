import React from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import {
  HomeIcon,
  UserGroupIcon,
  BookOpenIcon,
  CloudArrowUpIcon,
  MegaphoneIcon,
  SettingsIcon,
} from '@/components/icons';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarProvider,
  SidebarRail,
  SidebarTrigger,
} from '@/components/ui/sidebar';

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
      { name: 'PDF Import', path: '/menu/pdf-import', icon: null },
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

const AppSidebar: React.FC = () => {
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <div className="px-2 py-1">
          <h1 className="text-lg font-bold group-data-[collapsible=icon]:hidden">
            AI Marketing
          </h1>
          <h1 className="text-lg font-bold hidden group-data-[collapsible=icon]:block">
            AI
          </h1>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.path}>
                  <SidebarMenuButton asChild isActive={isActive(item.path)}>
                    <Link to={item.path}>
                      {item.icon}
                      <span>{item.name}</span>
                    </Link>
                  </SidebarMenuButton>
                  {item.children && (
                    <SidebarMenuSub>
                      {item.children.map((child) => (
                        <SidebarMenuSubItem key={child.path}>
                          <SidebarMenuSubButton asChild isActive={location.pathname === child.path}>
                            <Link to={child.path}>
                              <span>{child.name}</span>
                            </Link>
                          </SidebarMenuSubButton>
                        </SidebarMenuSubItem>
                      ))}
                    </SidebarMenuSub>
                  )}
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <div className="px-2 py-1 text-xs text-muted-foreground group-data-[collapsible=icon]:hidden">
          © {new Date().getFullYear()} AI Marketing
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
};

const Header: React.FC = () => {
  return (
    <header className="sticky top-0 z-10 bg-white border-b border-gray-200 h-16 flex items-center px-6 gap-2">
      <SidebarTrigger />
      <div className="ml-auto flex items-center gap-4">
        <div className="text-sm text-gray-600">Welcome back!</div>
      </div>
    </header>
  );
};

export const DashboardLayout: React.FC = () => {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <Header />
        <main className="p-4 sm:p-6">
          <Outlet />
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
};
