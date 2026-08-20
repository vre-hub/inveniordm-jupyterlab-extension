import React, { useEffect, useId, useRef, useState } from 'react';
import { ChevronDown, LoaderCircle } from 'lucide-react';

/** Properties shared by the accessible dropdown control. */
export type DropdownProps = {
  ariaLabel: string;
  children: React.ReactNode;
  emptyLabel: string;
  isLoading?: boolean;
  listboxLabel?: string;
  loadingLabel?: string;
  onChange: (value: string) => void;
  value: string;
};

/** Describes a selectable option in a dropdown. */
export type DropdownOptionProps = {
  children: React.ReactNode;
  value: string;
};

type DropdownOptionElement = React.ReactElement<DropdownOptionProps>;

/** Displays a button-driven single-selection dropdown. */
export function Dropdown({
  ariaLabel,
  children,
  emptyLabel,
  isLoading = false,
  listboxLabel = ariaLabel,
  loadingLabel = 'Loading…',
  onChange,
  value
}: DropdownProps): JSX.Element {
  const [isOpen, setIsOpen] = useState(false);
  const listboxId = useId();
  const containerRef = useRef<HTMLDivElement>(null);
  const options = React.Children.toArray(children).filter(
    (child): child is DropdownOptionElement =>
      React.isValidElement<DropdownOptionProps>(child) &&
      child.type === DropdownOption
  );
  const selectedOption =
    options.find(option => option.props.value === value) ?? options[0];

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
    <div className="relative inline-block max-w-full" ref={containerRef}>
      <button
        aria-busy={isLoading}
        aria-controls={isOpen ? listboxId : undefined}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-label={ariaLabel}
        className="box-border flex max-w-full items-center gap-2 rounded-md border border-border-strong bg-surface py-2 pl-3 pr-9 text-sm text-foreground-secondary shadow-sm transition-colors hover:border-border-hover focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-50"
        disabled={isLoading}
        onClick={() => setIsOpen(open => !open)}
        type="button"
      >
        {isLoading ? (
          <>
            <LoaderCircle
              aria-hidden="true"
              className="animate-spin text-primary"
              size={16}
            />
            <span className="font-semibold text-foreground">
              {loadingLabel}
            </span>
          </>
        ) : selectedOption ? (
          selectedOption.props.children
        ) : (
          <span className="font-semibold text-foreground">{emptyLabel}</span>
        )}
      </button>
      <ChevronDown
        aria-hidden="true"
        className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-muted"
        size={16}
      />
      {isOpen && (
        <div
          aria-label={listboxLabel}
          className="absolute left-0 z-20 mt-1 min-w-full overflow-hidden rounded-lg border border-border bg-surface py-1 shadow-lg"
          id={listboxId}
          role="listbox"
        >
          {options.map(option => {
            const optionValue = option.props.value;
            const isSelected = optionValue === value;

            return (
              <button
                aria-selected={isSelected}
                className={`flex w-full items-center gap-2 whitespace-nowrap border-0 bg-transparent px-3 py-2 text-left transition-colors hover:bg-surface-muted focus:bg-surface-muted focus:outline-none ${
                  isSelected ? 'text-foreground' : 'text-foreground-secondary'
                }`}
                key={optionValue}
                onClick={() => {
                  onChange(optionValue);
                  setIsOpen(false);
                }}
                role="option"
                type="button"
              >
                {option.props.children}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

/** Declares an option consumed and rendered by {@link Dropdown}. */
export function DropdownOption(_: DropdownOptionProps): null {
  return null;
}
