/**
 * RecipeExtractor — Tab 1: URL input, multi-step progress, result display.
 */

import { useState } from 'react';
import { Link2, Loader2, CheckCircle2, AlertCircle, Sparkles } from 'lucide-react';
import { useRecipes } from '../hooks/useRecipes';
import RecipeCard from './RecipeCard';

const PROGRESS_STEPS = [
  { key: 'scraping', label: 'Scraping page...', duration: 2000 },
  { key: 'extracting', label: 'Extracting recipe with AI...', duration: 4000 },
  { key: 'insights', label: 'Generating insights...', duration: 3000 },
];

export default function RecipeExtractor() {
  const [url, setUrl] = useState('');
  const [result, setResult] = useState(null);
  const [activeStep, setActiveStep] = useState(-1);
  const { extractRecipe, loading, error, setError } = useRecipes();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;

    setResult(null);
    setError(null);

    // Animate progress steps
    for (let i = 0; i < PROGRESS_STEPS.length; i++) {
      setActiveStep(i);
      await new Promise((r) => setTimeout(r, PROGRESS_STEPS[i].duration));
    }

    try {
      const data = await extractRecipe(url.trim());
      setResult(data);
      setActiveStep(-1);
    } catch {
      setActiveStep(-1);
    }
  };

  return (
    <div className="space-y-6">
      {/* Input form */}
      <form onSubmit={handleSubmit} className="glass-card p-6" id="extract-form">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-5 h-5 text-brand-400" />
          <h2 className="text-lg font-semibold text-slate-100">Extract Recipe</h2>
        </div>
        <p className="text-sm text-slate-400 mb-4">
          Paste a recipe URL from any website. Our AI will extract ingredients, instructions,
          nutrition data, and more.
        </p>
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Link2 className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              id="url-input"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.example.com/recipe/..."
              className="input-field pl-10"
              required
              disabled={loading}
            />
          </div>
          <button
            id="extract-btn"
            type="submit"
            disabled={loading || !url.trim()}
            className="btn-primary flex items-center gap-2 whitespace-nowrap"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Extracting...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Extract
              </>
            )}
          </button>
        </div>
      </form>

      {/* Progress indicator */}
      {activeStep >= 0 && (
        <div className="glass-card p-6 animate-fade-in">
          <div className="space-y-3">
            {PROGRESS_STEPS.map((step, idx) => (
              <div key={step.key} className="flex items-center gap-3">
                {idx < activeStep ? (
                  <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0" />
                ) : idx === activeStep ? (
                  <Loader2 className="w-5 h-5 text-brand-400 animate-spin flex-shrink-0" />
                ) : (
                  <div className="w-5 h-5 rounded-full border-2 border-slate-700 flex-shrink-0" />
                )}
                <span
                  className={`text-sm ${
                    idx <= activeStep ? 'text-slate-200' : 'text-slate-600'
                  }`}
                >
                  {step.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="glass-card p-5 border-red-500/30 animate-fade-in" id="extract-error">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-400">Extraction Failed</p>
              <p className="text-sm text-slate-400 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Result */}
      {result && !loading && (
        <RecipeCard recipe={result} showCacheBadge />
      )}
    </div>
  );
}
