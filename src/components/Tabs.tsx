import React from 'react';
import type { LucideIcon } from 'lucide-react';

export type TabItem<T extends string> = {
  id: T;
  label: string;
  icon?: LucideIcon;
};

type TabsProps<T extends string> = {
  currentTab: T;
  onChange: (tab: T) => void;
  panelId: string;
  tabs: TabItem<T>[];
};

export function Tabs<T extends string>({
  currentTab,
  onChange,
  panelId,
  tabs
}: TabsProps<T>): React.ReactElement {
  return (
    <div
      aria-label={tabs.map(tab => tab.label).join(', ')}
      className="flex w-full flex-wrap gap-x-1 border-b border-slate-200 px-2 pt-2"
      role="tablist"
    >
      {tabs.map(tab => (
        <button
          aria-controls={panelId}
          aria-selected={tab.id === currentTab}
          className={`-mb-px inline-flex shrink-0 items-center gap-1.5 border-x-0 border-b-2 border-t-0 bg-transparent px-2.5 py-2 text-sm font-semibold transition-colors focus-visible:z-10 focus-visible:rounded-sm focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-blue-600 ${
            tab.id === currentTab
              ? 'border-blue-600 text-blue-700'
              : 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-800'
          }`}
          id={`tab-${tab.id}`}
          key={tab.id}
          onClick={() => onChange(tab.id)}
          role="tab"
          tabIndex={tab.id === currentTab ? 0 : -1}
          type="button"
        >
          {tab.icon && (
            <tab.icon aria-hidden="true" className="size-4 shrink-0" />
          )}
          <span>{tab.label}</span>
        </button>
      ))}
    </div>
  );
}
