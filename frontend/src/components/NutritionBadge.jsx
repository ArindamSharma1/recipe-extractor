/**
 * NutritionBadge — Displays per-serving nutrition data as a compact card.
 */

import { Flame, Beef, Wheat, Droplets, Leaf } from 'lucide-react';

const MACRO_ITEMS = [
  { key: 'calories', label: 'Calories', icon: Flame, color: 'text-orange-400', unit: '' },
  { key: 'protein', label: 'Protein', icon: Beef, color: 'text-red-400', unit: '' },
  { key: 'carbs', label: 'Carbs', icon: Wheat, color: 'text-amber-400', unit: '' },
  { key: 'fat', label: 'Fat', icon: Droplets, color: 'text-blue-400', unit: '' },
  { key: 'fiber', label: 'Fiber', icon: Leaf, color: 'text-emerald-400', unit: '' },
];

export default function NutritionBadge({ nutrition }) {
  if (!nutrition) return null;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {MACRO_ITEMS.map(({ key, label, icon: Icon, color }) => {
          const value = nutrition[key];
          if (value == null) return null;
          return (
            <div
              key={key}
              className="flex flex-col items-center p-3 bg-slate-800/50 rounded-xl border border-slate-700/50"
            >
              <Icon className={`w-5 h-5 ${color} mb-1`} />
              <span className="text-lg font-bold text-slate-100">
                {typeof value === 'number' ? value.toLocaleString() : value}
              </span>
              <span className="text-xs text-slate-400">{label}</span>
            </div>
          );
        })}
      </div>
      {nutrition.note && (
        <p className="text-xs text-slate-500 italic px-1">⚠ {nutrition.note}</p>
      )}
    </div>
  );
}
