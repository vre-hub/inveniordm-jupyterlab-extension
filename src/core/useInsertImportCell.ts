import React from 'react';
import {
  InvenioRDMFileIdentifier,
  getInvenioRDMFileImportCell
} from '../api_calls';
import { useServerSettings, useInsertInvenioRDMCell } from '../store';

/** Provides an action for inserting a notebook cell that imports a file. */
export function useInsertImportCell(fileId: InvenioRDMFileIdentifier) {
  const serverSettings = useServerSettings();
  const insertInvenioRDMCell = useInsertInvenioRDMCell();

  const insertImportCell = React.useCallback(async (): Promise<void> => {
    insertInvenioRDMCell(
      await getInvenioRDMFileImportCell(serverSettings, fileId)
    );
  }, [fileId, insertInvenioRDMCell, serverSettings]);

  return { insertImportCell };
}
