/**
 * App — Root component with tabbed navigation.
 */

import { useState } from 'react';
import { ChefHat, Sparkles, History } from 'lucide-react';
import RecipeExtractor from './components/RecipeExtractor';
import RecipeHistory from './components/RecipeHistory';

const TABS = [
  { key: 'extract', label: 'Extract Recipe', icon: Sparkles },
  { key: 'history', label: 'History', icon: History },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('extract');

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Ambient glow effect */}
      <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-brand-500/5 rounded-full blur-[120px] pointer-events-none" />

      {/* Header */}
      <header className="relative border-b border-slate-800/50 bg-slate-950/80 backdrop-blur-xl sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-lg shadow-brand-500/20">
                <ChefHat className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-slate-100 leading-tight">
                  Recipe Extractor
                </h1>
                <p className="text-[10px] text-slate-500 -mt-0.5 tracking-widest uppercase">
                  AI-Powered Meal Planner
                </p>
              </div>
            </div>

            {/* Tab navigation */}
            <nav className="flex items-center gap-1" id="main-nav">
              {TABS.map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  id={`tab-${key}`}
                  onClick={() => setActiveTab(key)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    activeTab === key
                      ? 'bg-brand-500/10 text-brand-400 shadow-inner'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden sm:inline">{label}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="relative max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {activeTab === 'extract' && <RecipeExtractor />}
        {activeTab === 'history' && <RecipeHistory />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/30 py-6 mt-auto">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <p className="text-center text-xs text-slate-600">
            Built with FastAPI + LangChain + React • Powered by Google Gemini AI
          </p>
        </div>
      </footer>
    </div>
  );
}
