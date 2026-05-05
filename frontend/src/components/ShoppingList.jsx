/**
 * ShoppingList — Categorized shopping list display.
 */

import { ShoppingCart, Apple, Milk, Drumstick, Archive, Croissant, Package } from 'lucide-react';

const CATEGORY_CONFIG = {
  produce:      { label: 'Produce',      icon: Apple,     color: 'text-green-400' },
  dairy:        { label: 'Dairy',        icon: Milk,      color: 'text-blue-300' },
  meat_seafood: { label: 'Meat & Seafood', icon: Drumstick, color: 'text-red-400' },
  pantry:       { label: 'Pantry',       icon: Archive,   color: 'text-amber-400' },
  bakery:       { label: 'Bakery',       icon: Croissant, color: 'text-yellow-300' },
  other:        { label: 'Other',        icon: Package,   color: 'text-slate-400' },
};

export default function ShoppingList({ shoppingList, title }) {
  if (!shoppingList) return null;

  const nonEmptyCategories = Object.entries(CATEGORY_CONFIG).filter(
    ([key]) => shoppingList[key]?.length > 0
  );

  if (nonEmptyCategories.length === 0) return null;

  return (
    <div className="space-y-3">
      {title && (
        <div className="flex items-center gap-2 mb-2">
          <ShoppingCart className="w-5 h-5 text-brand-400" />
          <h4 className="font-semibold text-slate-200">{title}</h4>
        </div>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {nonEmptyCategories.map(([key, { label, icon: Icon, color }]) => (
          <div
            key={key}
            className="bg-slate-800/40 rounded-xl p-3 border border-slate-700/30"
          >
            <div className="flex items-center gap-2 mb-2">
              <Icon className={`w-4 h-4 ${color}`} />
              <span className="text-sm font-medium text-slate-300">{label}</span>
              <span className="ml-auto text-xs text-slate-500">
                {shoppingList[key].length}
              </span>
            </div>
            <ul className="space-y-1">
              {shoppingList[key].map((item, idx) => (
                <li key={idx} className="text-sm text-slate-400 flex items-start gap-2">
                  <span className="text-slate-600 mt-1">•</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
