/**
 * RecipeCard — Full recipe display with all sections.
 * Used after extraction and in the detail modal.
 */

import {
  ChefHat, Clock, Users, Gauge, Globe, Sparkles,
  ListOrdered, Shuffle, BookOpen, ArrowRight,
} from 'lucide-react';
import NutritionBadge from './NutritionBadge';
import ShoppingList from './ShoppingList';

/** Confidence score badge with color coding */
function ConfidenceBadge({ score }) {
  if (score == null) return null;
  const pct = Math.round(score * 100);
  const cls =
    score >= 0.8 ? 'badge-green' :
    score >= 0.5 ? 'badge-yellow' : 'badge-red';
  return <span className={cls}>{pct}% confidence</span>;
}

/** Difficulty pill */
function DifficultyBadge({ difficulty }) {
  if (!difficulty) return null;
  const cls =
    difficulty === 'easy'   ? 'badge-green' :
    difficulty === 'medium' ? 'badge-yellow' : 'badge-red';
  return <span className={cls}>{difficulty}</span>;
}

/** A collapsible section card */
function Section({ icon: Icon, title, children, color = 'text-brand-400' }) {
  return (
    <div className="glass-card p-5 animate-fade-in">
      <div className="flex items-center gap-2 mb-4">
        <Icon className={`w-5 h-5 ${color}`} />
        <h3 className="text-lg font-semibold text-slate-100">{title}</h3>
      </div>
      {children}
    </div>
  );
}

export default function RecipeCard({ recipe, showCacheBadge = false }) {
  if (!recipe) return null;

  return (
    <div className="space-y-4 animate-slide-up">
      {/* Header */}
      <div className="glass-card p-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-2xl font-bold text-slate-50 mb-2">
              {recipe.title || 'Untitled Recipe'}
            </h2>
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <ConfidenceBadge score={recipe.extraction_confidence} />
              <DifficultyBadge difficulty={recipe.difficulty} />
              {showCacheBadge && recipe.cached && (
                <span className="badge-blue">⚡ Loaded from cache</span>
              )}
            </div>
          </div>
          <ChefHat className="w-10 h-10 text-brand-400 opacity-40" />
        </div>

        {/* Meta row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-5">
          {recipe.cuisine && (
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Globe className="w-4 h-4 text-brand-400" />
              <span>{recipe.cuisine}</span>
            </div>
          )}
          {recipe.prep_time && (
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Clock className="w-4 h-4 text-blue-400" />
              <span>Prep: {recipe.prep_time}</span>
            </div>
          )}
          {recipe.cook_time && (
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Clock className="w-4 h-4 text-orange-400" />
              <span>Cook: {recipe.cook_time}</span>
            </div>
          )}
          {recipe.servings && (
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Users className="w-4 h-4 text-green-400" />
              <span>{recipe.servings} servings</span>
            </div>
          )}
        </div>
      </div>

      {/* Ingredients */}
      {recipe.ingredients?.length > 0 && (
        <Section icon={ListOrdered} title="Ingredients" color="text-green-400">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {recipe.ingredients.map((ing, idx) => (
              <div
                key={ing.id || idx}
                className="flex items-start gap-2 text-sm text-slate-300 py-1"
              >
                <span className="text-brand-400 font-mono text-xs mt-0.5 min-w-[60px] text-right">
                  {ing.quantity} {ing.unit || ''}
                </span>
                <span>{ing.item}</span>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Instructions */}
      {recipe.instructions?.length > 0 && (
        <Section icon={BookOpen} title="Instructions" color="text-blue-400">
          <ol className="space-y-3">
            {recipe.instructions.map((step, idx) => (
              <li key={step.id || idx} className="flex gap-3">
                <span className="flex-shrink-0 w-7 h-7 rounded-full bg-brand-500/10 text-brand-400 flex items-center justify-center text-sm font-bold">
                  {step.step_number || idx + 1}
                </span>
                <p className="text-sm text-slate-300 leading-relaxed pt-0.5">
                  {step.instruction_text}
                </p>
              </li>
            ))}
          </ol>
        </Section>
      )}

      {/* Nutrition */}
      {recipe.nutrition && (
        <Section icon={Gauge} title="Nutrition (per serving)" color="text-orange-400">
          <NutritionBadge nutrition={recipe.nutrition} />
        </Section>
      )}

      {/* Substitutions */}
      {recipe.substitutions?.length > 0 && (
        <Section icon={Shuffle} title="Substitutions" color="text-purple-400">
          <div className="space-y-3">
            {recipe.substitutions.map((sub, idx) => (
              <div key={idx} className="bg-slate-800/40 rounded-xl p-3 border border-slate-700/30">
                <div className="flex items-center gap-2 text-sm mb-1">
                  <span className="text-red-400 line-through">{sub.original}</span>
                  <ArrowRight className="w-3 h-3 text-slate-500" />
                  <span className="text-green-400 font-medium">{sub.substitute}</span>
                  {sub.dietary_benefit && (
                    <span className="badge-blue ml-auto">{sub.dietary_benefit}</span>
                  )}
                </div>
                <p className="text-xs text-slate-500">{sub.reason}</p>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Shopping List */}
      {recipe.shopping_list && (
        <Section icon={Sparkles} title="Shopping List" color="text-emerald-400">
          <ShoppingList shoppingList={recipe.shopping_list} />
        </Section>
      )}

      {/* Related Recipes */}
      {recipe.related_recipes?.length > 0 && (
        <Section icon={BookOpen} title="Related Recipes" color="text-amber-400">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {recipe.related_recipes.map((rel, idx) => (
              <div
                key={idx}
                className="bg-slate-800/40 rounded-xl p-3 border border-slate-700/30"
              >
                <p className="text-sm font-medium text-slate-200 mb-1">{rel.name}</p>
                <p className="text-xs text-slate-500">{rel.reason}</p>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}
