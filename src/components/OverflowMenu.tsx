import React, { useEffect, useId, useRef, useState } from 'react';
import { MoreVertical } from 'lucide-react';

/** Describes an action shown in an overflow menu. */
export type OverflowMenuItem = {
  label: string;
  hint?: string;
  icon?: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  destructive?: boolean;
};

/** Displays a compact menu of secondary actions. */
export const OverflowMenu: React.FC<{
  items: OverflowMenuItem[];
  label?: string;
}> = ({ items, label = 'More actions' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const menuId = useId();
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const closeOnOutsideClick = (event: MouseEvent): void => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    const closeOnEscape = (event: KeyboardEvent): void => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', closeOnOutsideClick);
    document.addEventListener('keydown', closeOnEscape);
    return () => {
      document.removeEventListener('mousedown', closeOnOutsideClick);
      document.removeEventListener('keydown', closeOnEscape);
    };
  }, [isOpen]);

  return (
    <div className="relative" ref={containerRef}>
      <button
        aria-controls={isOpen ? menuId : undefined}
        aria-expanded={isOpen}
        aria-haspopup="menu"
        aria-label={label}
        className="flex size-8 items-center justify-center rounded-md border-0 bg-transparent text-muted transition-colors hover:bg-surface-subtle hover:text-foreground-secondary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
        onClick={() => setIsOpen(open => !open)}
        title={label}
        type="button"
      >
        <MoreVertical aria-hidden="true" size={18} />
      </button>

      {isOpen && (
        <div
          aria-label={label}
          className="absolute right-0 z-20 mt-1 w-64 overflow-hidden rounded-lg border border-border bg-surface py-1 shadow-lg"
          id={menuId}
          role="menu"
        >
          {items.map(item => (
            <button
              className={`flex w-full items-start gap-3 border-0 bg-transparent px-3 py-2 text-left transition-colors hover:bg-surface-muted focus:bg-surface-muted focus:outline-none disabled:cursor-not-allowed disabled:opacity-50 ${
                item.destructive ? 'text-danger' : 'text-foreground-secondary'
              }`}
              disabled={item.disabled}
              key={item.label}
              onClick={() => {
                item.onClick();
                setIsOpen(false);
              }}
              role="menuitem"
              title={item.hint}
              type="button"
            >
              {item.icon && (
                <span className="mt-0.5 shrink-0" aria-hidden="true">
                  {item.icon}
                </span>
              )}
              <span className="min-w-0">
                <span className="block text-sm font-medium">{item.label}</span>
                {item.hint && (
                  <span className="mt-0.5 block text-xs leading-4 text-muted">
                    {item.hint}
                  </span>
                )}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
