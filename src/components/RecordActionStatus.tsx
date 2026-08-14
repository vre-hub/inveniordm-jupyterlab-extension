import React, { createContext, useContext, useState } from 'react';
import { LoaderCircle } from 'lucide-react';

type RecordAction = {
  description: string;
  icon?: React.ReactNode;
  isLoading?: boolean;
};

type RecordActionContextValue = {
  currentAction: RecordAction | null;
  setRecordAction: (action: RecordAction | null) => void;
};

const RecordActionContext = createContext<RecordActionContextValue | null>(
  null
);

/** Provides record-action status to descendant components. */
export const RecordActionProvider: React.FC<React.PropsWithChildren> = ({
  children
}) => {
  const [currentAction, setRecordAction] = useState<RecordAction | null>(null);

  return (
    <RecordActionContext.Provider value={{ currentAction, setRecordAction }}>
      {children}
    </RecordActionContext.Provider>
  );
};

/** Returns the current record-action status and its updater. */
export const useRecordAction = (): RecordActionContextValue => {
  const context = useContext(RecordActionContext);
  if (!context) {
    throw new Error('useRecordAction must be used within RecordActionProvider');
  }
  return context;
};

/** Displays feedback for the latest record action. */
export const RecordActionStatus: React.FC = () => {
  const { currentAction } = useRecordAction();

  if (!currentAction) {
    return null;
  }

  return (
    <div
      className={`mt-3 flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-foreground-secondary ${
        currentAction.isLoading === false
          ? 'bg-danger-subtle'
          : 'bg-primary-subtle'
      }`}
      role={currentAction.isLoading === false ? 'alert' : 'status'}
    >
      {currentAction.icon ? (
        <span aria-hidden="true">{currentAction.icon}</span>
      ) : null}
      <span>{currentAction.description}</span>
      {currentAction.isLoading !== false ? (
        <LoaderCircle
          aria-hidden="true"
          className="ml-auto animate-spin text-primary"
          size={16}
        />
      ) : null}
    </div>
  );
};
