import React from 'react';

export type TabItem<T extends string> = {
  id: T;
  label: string;
};

type TabsProps<T extends string> = {
  currentTab: T;
  onChange: (tab: T) => void;
  tabs: TabItem<T>[];
};

export function Tabs<T extends string>({
  currentTab,
  onChange,
  tabs
}: TabsProps<T>): React.ReactElement {
  return (
    <div style={{ display: 'flex', gap: 4 }}>
      {tabs.map(tab => (
        <button
          aria-pressed={tab.id === currentTab}
          key={tab.id}
          onClick={() => onChange(tab.id)}
          style={{ fontWeight: tab.id === currentTab ? 'bold' : 'normal' }}
          type="button"
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
