/**
 * RecipeModal — Full-screen overlay modal for recipe details.
 */

import { useEffect, useState } from 'react';
import { X, Loader2 } from 'lucide-react';
import { useRecipes } from '../hooks/useRecipes';
import RecipeCard from './RecipeCard';

export default function RecipeModal({ recipeId, onClose }) {
  const [recipe, setRecipe] = useState(null);
  const { fetchRecipe, loading, error } = useRecipes();

  useEffect(() => {
    if (!recipeId) return;
    fetchRecipe(recipeId)
      .then(setRecipe)
      .catch(() => {});
  }, [recipeId, fetchRecipe]);

  if (!recipeId) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center p-4 pt-10 overflow-y-auto bg-black/60 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div
        className="w-full max-w-3xl mb-10"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <div className="flex justify-end mb-2">
          <button
            onClick={onClose}
            className="p-2 rounded-full bg-slate-800/80 text-slate-400 hover:text-slate-100 hover:bg-slate-700 transition-colors"
            id="modal-close-btn"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        {loading && (
          <div className="glass-card p-16 flex flex-col items-center gap-3">
            <Loader2 className="w-8 h-8 text-brand-400 animate-spin" />
            <p className="text-slate-400">Loading recipe details...</p>
          </div>
        )}

        {error && !loading && (
          <div className="glass-card p-8 text-center">
            <p className="text-red-400">Failed to load recipe: {error}</p>
          </div>
        )}

        {recipe && !loading && <RecipeCard recipe={recipe} />}
      </div>
    </div>
  );
}
