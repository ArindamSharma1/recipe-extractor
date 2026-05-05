/**
 * RecipeHistory — Tab 2: Paginated table, detail modal, meal plan generation.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  History, Eye, Trash2, ChevronLeft, ChevronRight,
  Loader2, AlertCircle, ShoppingCart, X, RefreshCw,
} from 'lucide-react';
import { useRecipes } from '../hooks/useRecipes';
import RecipeModal from './RecipeModal';
import ShoppingList from './ShoppingList';

/** Difficulty pill */
function DifficultyPill({ difficulty }) {
  if (!difficulty) return <span className="text-slate-600">—</span>;
  const cls =
    difficulty === 'easy' ? 'badge-green' :
    difficulty === 'medium' ? 'badge-yellow' : 'badge-red';
  return <span className={cls}>{difficulty}</span>;
}

/** Confidence bar */
function ConfidenceBar({ score }) {
  if (score == null) return <span className="text-slate-600">—</span>;
  const pct = Math.round(score * 100);
  const color =
    score >= 0.8 ? 'bg-emerald-500' :
    score >= 0.5 ? 'bg-amber-500' : 'bg-red-500';
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-500">{pct}%</span>
    </div>
  );
}

export default function RecipeHistory() {
  const [data, setData] = useState(null);
  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [selected, setSelected] = useState(new Set());
  const [mealPlan, setMealPlan] = useState(null);
  const [mealPlanLoading, setMealPlanLoading] = useState(false);

  const { fetchRecipes, deleteRecipe, generateMealPlan, loading, error } = useRecipes();

  const loadData = useCallback(async () => {
    try {
      const result = await fetchRecipes(page);
      setData(result);
    } catch {}
  }, [fetchRecipes, page]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleDelete = async (id) => {
    try {
      await deleteRecipe(id);
      setDeleteConfirm(null);
      selected.delete(id);
      setSelected(new Set(selected));
      loadData();
    } catch {}
  };

  const toggleSelect = (id) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelected(next);
  };

  const handleMealPlan = async () => {
    if (selected.size < 2) return;
    setMealPlanLoading(true);
    try {
      const plan = await generateMealPlan([...selected]);
      setMealPlan(plan);
    } catch {}
    setMealPlanLoading(false);
  };

  const items = data?.items || [];
  const totalPages = data?.pages || 1;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <History className="w-5 h-5 text-brand-400" />
          <h2 className="text-lg font-semibold text-slate-100">History</h2>
          {data && (
            <span className="text-xs text-slate-500">({data.total} recipes)</span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {selected.size >= 2 && (
            <button
              id="meal-plan-btn"
              onClick={handleMealPlan}
              disabled={mealPlanLoading}
              className="btn-primary text-sm flex items-center gap-2"
            >
              {mealPlanLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <ShoppingCart className="w-4 h-4" />
              )}
              Meal Plan ({selected.size})
            </button>
          )}
          <button onClick={loadData} className="btn-secondary text-sm flex items-center gap-2" id="refresh-btn">
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>
      </div>

      {/* Meal plan result */}
      {mealPlan && (
        <div className="glass-card p-5 animate-slide-up" id="meal-plan-result">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-slate-200 flex items-center gap-2">
              <ShoppingCart className="w-5 h-5 text-brand-400" />
              Meal Plan — {mealPlan.recipe_count} recipes
            </h3>
            <button onClick={() => setMealPlan(null)} className="text-slate-500 hover:text-slate-300">
              <X className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs text-slate-500 mb-3">
            Combined: {mealPlan.recipes.join(' • ')}
          </p>
          <ShoppingList shoppingList={mealPlan.shopping_list} />
        </div>
      )}

      {/* Loading */}
      {loading && !data && (
        <div className="glass-card p-12 flex justify-center">
          <Loader2 className="w-7 h-7 text-brand-400 animate-spin" />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="glass-card p-5 border-red-500/30">
          <div className="flex items-center gap-2 text-red-400 text-sm">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        </div>
      )}

      {/* Empty state */}
      {data && items.length === 0 && (
        <div className="glass-card p-12 text-center" id="empty-state">
          <History className="w-12 h-12 text-slate-700 mx-auto mb-3" />
          <p className="text-slate-500">No recipes yet. Extract one to get started!</p>
        </div>
      )}

      {/* Table */}
      {items.length > 0 && (
        <div className="glass-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm" id="recipe-table">
              <thead>
                <tr className="border-b border-slate-700/50">
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider w-10">
                    <input
                      type="checkbox"
                      className="rounded bg-slate-800 border-slate-600"
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelected(new Set(items.map((i) => i.id)));
                        } else {
                          setSelected(new Set());
                        }
                      }}
                      checked={items.length > 0 && items.every((i) => selected.has(i.id))}
                    />
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Title</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider hidden sm:table-cell">Cuisine</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider hidden md:table-cell">Difficulty</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider hidden lg:table-cell">Confidence</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider hidden md:table-cell">Date</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {items.map((recipe) => (
                  <tr
                    key={recipe.id}
                    className="hover:bg-slate-800/30 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        className="rounded bg-slate-800 border-slate-600"
                        checked={selected.has(recipe.id)}
                        onChange={() => toggleSelect(recipe.id)}
                      />
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-slate-200 font-medium">
                        {recipe.title || 'Untitled'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-400 hidden sm:table-cell">
                      {recipe.cuisine || '—'}
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell">
                      <DifficultyPill difficulty={recipe.difficulty} />
                    </td>
                    <td className="px-4 py-3 hidden lg:table-cell">
                      <ConfidenceBar score={recipe.extraction_confidence} />
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs hidden md:table-cell">
                      {new Date(recipe.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => setSelectedId(recipe.id)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-brand-400 hover:bg-slate-800 transition-colors"
                          title="View details"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        {deleteConfirm === recipe.id ? (
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => handleDelete(recipe.id)}
                              className="text-xs text-red-400 hover:text-red-300 px-2 py-1 rounded bg-red-500/10"
                            >
                              Confirm
                            </button>
                            <button
                              onClick={() => setDeleteConfirm(null)}
                              className="text-xs text-slate-500 hover:text-slate-300 px-2 py-1"
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => setDeleteConfirm(recipe.id)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-slate-800 transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-slate-800/50">
              <span className="text-xs text-slate-500">
                Page {data.page} of {totalPages}
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="btn-secondary text-xs flex items-center gap-1 !px-3 !py-1.5"
                  id="prev-page"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                  Prev
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="btn-secondary text-xs flex items-center gap-1 !px-3 !py-1.5"
                  id="next-page"
                >
                  Next
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Detail modal */}
      {selectedId && (
        <RecipeModal
          recipeId={selectedId}
          onClose={() => setSelectedId(null)}
        />
      )}

      {/* Delete confirmation overlay is inline in the table */}
    </div>
  );
}
