import React from 'react';
import { useServerSettings } from '../store';
import { ZenodoFileIdentifier, deleteZenodoRecordFile } from '../api_calls';

export function useDeleteZenodoFile(fileId: ZenodoFileIdentifier) {
  const serverSettings = useServerSettings();
  const [isDeleting, setIsDeleting] = React.useState(false);

  const deleteFile = async (): Promise<void> => {
    setIsDeleting(true);
    try {
      await deleteZenodoRecordFile(serverSettings, fileId);
    } finally {
      setIsDeleting(false);
    }
  };
  return { deleteFile, isDeleting };
}
