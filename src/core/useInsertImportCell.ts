import React from 'react';
import { ZenodoFileIdentifier, getZenodoFileImportCell } from '../api_calls';
import { useServerSettings, useInsertZenodoCell } from '../store';

export function useInsertImportCell(fileId: ZenodoFileIdentifier) {
  const serverSettings = useServerSettings();
  const insertZenodoCell = useInsertZenodoCell();

  const insertImportCell = React.useCallback(async (): Promise<void> => {
    insertZenodoCell(await getZenodoFileImportCell(serverSettings, fileId));
  }, [fileId, insertZenodoCell, serverSettings]);

  return { insertImportCell };
}
