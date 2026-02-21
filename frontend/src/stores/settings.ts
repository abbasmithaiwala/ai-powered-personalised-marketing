import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type LLMProvider = 'openrouter' | 'groq';

export interface LLMSettings {
    provider: LLMProvider;
    model: string;
}

interface SettingsState {
    llm: LLMSettings;
    hasCompletedOnboarding: boolean;
    isFirstVisit: boolean;
    setLLMProvider: (provider: LLMProvider) => void;
    setLLMModel: (model: string) => void;
    completeOnboarding: () => void;
    dismissWelcomeBanner: () => void;
}

export const useSettingsStore = create<SettingsState>()(
    persist(
        (set) => ({
            llm: {
                provider: 'openrouter',
                model: 'anthropic/claude-3.5-sonnet',
            },
            hasCompletedOnboarding: false,
            isFirstVisit: true,
            setLLMProvider: (provider) =>
                set((state) => ({
                    llm: {
                        ...state.llm,
                        provider,
                        // Reset model to default when provider changes
                        model: provider === 'groq' ? 'llama3-70b-8192' : 'anthropic/claude-3.5-sonnet'
                    },
                })),
            setLLMModel: (model) =>
                set((state) => ({
                    llm: { ...state.llm, model },
                })),
            completeOnboarding: () =>
                set({ hasCompletedOnboarding: true }),
            dismissWelcomeBanner: () =>
                set({ isFirstVisit: false }),
        }),
        {
            name: 'app-settings',
        }
    )
);
