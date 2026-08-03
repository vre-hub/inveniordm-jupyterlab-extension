import React from 'react';
import { getZenodoFileImportCell, ZenodoFileIdentifier } from '../api_calls';
import { useServerSettings, useInsertZenodoCell } from '../store';

function useInsertImportCell(fileId: ZenodoFileIdentifier) {
  const serverSettings = useServerSettings();
  const insertZenodoCell = useInsertZenodoCell();

  const insertImportCell = React.useCallback(async (): Promise<void> => {
    insertZenodoCell(await getZenodoFileImportCell(serverSettings, fileId));
  }, [fileId, insertZenodoCell, serverSettings]);

  return { insertImportCell };
}

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
