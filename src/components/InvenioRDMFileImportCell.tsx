import React from 'react';
import { InvenioRDMFileIdentifier } from '../api_calls';
import { useInsertImportCell } from '../core';

export const InvenioRDMFileImportCellButton: React.FC<{
  fileId: InvenioRDMFileIdentifier;
}> = ({ fileId }) => {
  const { insertImportCell } = useInsertImportCell(fileId);

  return (
    <button onClick={insertImportCell} type="button">
      Insert import cell
    </button>
  );
};
