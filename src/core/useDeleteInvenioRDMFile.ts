import React from 'react';
import { useServerSettings } from '../store';
import {
  InvenioRDMFileIdentifier,
  deleteInvenioRDMRecordFile
} from '../api_calls';

/** Provides state and an action for deleting a file from a record draft. */
export function useDeleteInvenioRDMFile(fileId: InvenioRDMFileIdentifier) {
  const serverSettings = useServerSettings();
  const [isDeleting, setIsDeleting] = React.useState(false);

  const deleteFile = async (): Promise<void> => {
    setIsDeleting(true);
    try {
      await deleteInvenioRDMRecordFile(serverSettings, fileId);
    } finally {
      setIsDeleting(false);
    }
  };
  return { deleteFile, isDeleting };
}
