import React, { createContext, useContext, useState } from 'react';
import { LoaderCircle } from 'lucide-react';

type RecordAction = {
  description: string;
  icon?: React.ReactNode;
};

type RecordActionContextValue = {
  currentAction: RecordAction | null;
  setRecordAction: (action: RecordAction | null) => void;
};

const RecordActionContext = createContext<RecordActionContextValue | null>(
  null
);

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

export const useRecordAction = (): RecordActionContextValue => {
  const context = useContext(RecordActionContext);
  if (!context) {
    throw new Error('useRecordAction must be used within RecordActionProvider');
  }
  return context;
};

export const RecordActionStatus: React.FC = () => {
  const { currentAction } = useRecordAction();

  if (!currentAction) {
    return null;
  }

  return (
    <div
      className="mt-3 flex items-center gap-2 rounded-lg bg-blue-50 px-3 py-2 text-sm text-slate-700"
      role="status"
    >
      {currentAction.icon ? (
        <span aria-hidden="true">{currentAction.icon}</span>
      ) : null}
      <span>{currentAction.description}</span>
      <LoaderCircle
        aria-hidden="true"
        className="ml-auto animate-spin text-blue-600"
        size={16}
      />
    </div>
  );
};
