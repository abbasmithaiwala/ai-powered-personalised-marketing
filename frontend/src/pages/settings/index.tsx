import React from 'react';
import type { LLMProvider } from '@/stores/settings';
import { useSettingsStore } from '@/stores/settings';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { SettingsIcon } from '@/components/icons';

export default function SettingsPage() {
    const { llm, setLLMProvider, setLLMModel } = useSettingsStore();

    const handleProviderChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const newProvider = e.target.value as LLMProvider;
        // Update provider and reset model to its default in the store logic
        setLLMProvider(newProvider);
        // Specifically set the model if the store doesn't automatically do it perfectly, 
        // but our store logic handles defaults.
    };

    const handleModelChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setLLMModel(e.target.value);
    };

    const currentProviderDefault = llm.provider === 'openrouter'
        ? 'anthropic/claude-3.5-sonnet'
        : 'llama3-70b-8192';

    return (
        <div className="space-y-6 max-w-4xl mx-auto">
            <div className="flex items-center space-x-3 mb-8">
                <SettingsIcon className="w-8 h-8 text-gray-700" />
                <h1 className="text-3xl font-bold text-gray-900">Application Settings</h1>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>AI Configuration</CardTitle>
                    <CardDescription>
                        Configure the Large Language Model (LLM) provider and model used for message generation.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Provider Selection */}
                        <div className="space-y-2">
                            <label htmlFor="provider" className="block text-sm font-medium text-gray-700">
                                LLM Provider
                            </label>
                            <div className="relative">
                                <select
                                    id="provider"
                                    value={llm.provider}
                                    onChange={handleProviderChange}
                                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm py-2 pl-3 pr-10 border"
                                >
                                    <option value="openrouter">OpenRouter (Default)</option>
                                    <option value="groq">Groq</option>
                                </select>
                            </div>
                            <p className="text-xs text-gray-500">
                                Select the backend service for AI generation. Ensure API keys are configured in backend .env.
                            </p>
                        </div>

                        {/* Model Selection */}
                        <div className="space-y-2">
                            <label htmlFor="model" className="block text-sm font-medium text-gray-700">
                                Model ID
                            </label>
                            <input
                                type="text"
                                id="model"
                                value={llm.model}
                                onChange={handleModelChange}
                                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm py-2 px-3 border"
                                placeholder={currentProviderDefault}
                            />
                            <p className="text-xs text-gray-500">
                                Enter the specific model identifier (e.g., {currentProviderDefault}).
                            </p>
                        </div>
                    </div>

                    <div className="pt-4 border-t border-gray-100">
                        <div className="bg-blue-50 rounded-md p-4 flex items-start">
                            <div className="flex-shrink-0">
                                <SettingsIcon className="h-5 w-5 text-blue-400" aria-hidden="true" />
                            </div>
                            <div className="ml-3 flex-1 md:flex md:justify-between">
                                <p className="text-sm text-blue-700">
                                    Settings are automatically saved to your browser.
                                </p>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
