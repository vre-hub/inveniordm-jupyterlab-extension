import React from 'react';
import type { LucideIcon } from 'lucide-react';

/** Describes a selectable tab and its label. */
export type TabItem<T extends string> = {
  id: T;
  label?: string;
  icon?: LucideIcon;
};

type TabsProps<T extends string> = {
  currentTab: T;
  onChange: (tab: T) => void;
  panelId: string;
  tabs: TabItem<T>[];
};

/** Displays an accessible tab list for switching between views. */
export function Tabs<T extends string>({
  currentTab,
  onChange,
  panelId,
  tabs
}: TabsProps<T>): React.ReactElement {
  return (
    <div
      aria-label={tabs.map(tab => tab.label ?? tab.id).join(', ')}
      className="flex w-full flex-wrap gap-x-0.5 border-b border-border px-1 pt-2"
      role="tablist"
    >
      {tabs.map(tab => (
        <button
          aria-label={tab.label ?? tab.id}
          aria-controls={panelId}
          aria-selected={tab.id === currentTab}
          className={`-mb-px inline-flex shrink-0 items-center gap-1 border-x-0 border-b-2 border-t-0 bg-transparent px-2 py-2 text-sm font-semibold transition-colors focus-visible:z-10 focus-visible:rounded-sm focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-primary ${
            tab.id === currentTab
              ? 'border-primary text-primary-hover'
              : 'border-transparent text-muted hover:border-border-strong hover:text-foreground-secondary'
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
          {tab.label && <span>{tab.label}</span>}
        </button>
      ))}
    </div>
  );
}
