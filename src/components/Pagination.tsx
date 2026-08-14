import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

type PaginationProps = {
  page: number;
  pageSize: number;
  total: number;
  disabled?: boolean;
  onPageChange: (page: number) => void;
};

/** Displays controls for navigating a paginated collection. */
export const Pagination: React.FC<PaginationProps> = ({
  page,
  pageSize,
  total,
  disabled = false,
  onPageChange
}) => {
  const pageCount = Math.ceil(total / pageSize);

  if (pageCount <= 1) {
    return null;
  }

  return (
    <nav
      aria-label="Records pagination"
      className="mt-3 flex items-center justify-between gap-2"
    >
      <button
        aria-label="Previous page"
        className="inline-flex items-center gap-1 rounded-md border border-border-strong bg-surface px-2.5 py-1.5 text-xs font-medium text-muted-strong shadow-sm transition-colors hover:border-primary hover:bg-primary-subtle hover:text-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-50"
        disabled={disabled || page <= 1}
        onClick={() => onPageChange(page - 1)}
        type="button"
      >
        <ChevronLeft aria-hidden="true" className="size-3.5" />
      </button>
      <span className="text-xs text-muted-strong">
        Page {page} of {pageCount}
      </span>
      <button
        aria-label="Next page"
        className="inline-flex items-center gap-1 rounded-md border border-border-strong bg-surface px-2.5 py-1.5 text-xs font-medium text-muted-strong shadow-sm transition-colors hover:border-primary hover:bg-primary-subtle hover:text-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-50"
        disabled={disabled || page >= pageCount}
        onClick={() => onPageChange(page + 1)}
        type="button"
      >
        <ChevronRight aria-hidden="true" className="size-3.5" />
      </button>
    </nav>
  );
};
