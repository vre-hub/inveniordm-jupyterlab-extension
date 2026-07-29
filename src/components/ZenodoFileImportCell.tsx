import React from 'react';
import { getZenodoFileImportCell, ZenodoFileIdentifier } from '../api_calls';
import { useServerSettings, useInsertZenodoCell } from '../store';

export const ZenodoFileImportCellButton: React.FC<{
  fileId: ZenodoFileIdentifier;
}> = ({ fileId }) => {
  const serverSettings = useServerSettings();
  const insertZenodoCell = useInsertZenodoCell();

  const insertImportCell = async (): Promise<void> => {
    insertZenodoCell(await getZenodoFileImportCell(serverSettings, fileId));
  };

  return (
    <button onClick={insertImportCell} type="button">
      Insert import cell
    </button>
  );
};
