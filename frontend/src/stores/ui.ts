import { create } from 'zustand';

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
}

interface UIState {
  // Sidebar state
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;

  // Notifications
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;

  // Loading states
  loadingStates: Record<string, boolean>;
  setLoading: (key: string, loading: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  // Sidebar
  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

  // Notifications
  notifications: [],
  addNotification: (notification) =>
    set((state) => {
      const id = Math.random().toString(36).substr(2, 9);
      const newNotification = { ...notification, id };

      // Auto-remove after duration (default 5s)
      if (notification.duration !== 0) {
        setTimeout(() => {
          set((state) => ({
            notifications: state.notifications.filter((n) => n.id !== id),
          }));
        }, notification.duration || 5000);
      }

      return {
        notifications: [...state.notifications, newNotification],
      };
    }),
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),

  // Loading states
  loadingStates: {},
  setLoading: (key, loading) =>
    set((state) => ({
      loadingStates: { ...state.loadingStates, [key]: loading },
    })),
}));

// Helper hooks
export const useNotification = () => {
  const addNotification = useUIStore((state) => state.addNotification);

  return {
    success: (message: string, duration?: number) =>
      addNotification({ type: 'success', message, duration }),
    error: (message: string, duration?: number) =>
      addNotification({ type: 'error', message, duration }),
    warning: (message: string, duration?: number) =>
      addNotification({ type: 'warning', message, duration }),
    info: (message: string, duration?: number) =>
      addNotification({ type: 'info', message, duration }),
  };
};
