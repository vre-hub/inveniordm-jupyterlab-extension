import React from 'react';
import { ZenodoFileIdentifier } from '../api_calls';
import { useInsertImportCell } from '../core/useInsertImportCell';

export const ZenodoFileImportCellButton: React.FC<{
  fileId: ZenodoFileIdentifier;
}> = ({ fileId }) => {
  const { insertImportCell } = useInsertImportCell(fileId);

  return (
    <button onClick={insertImportCell} type="button">
      Insert import cell
    </button>
  );
};
