import {
  InvenioRDMFileIdentifier,
  deleteInvenioRDMFileDownload
} from '../api_calls';
import { useServerSettings } from '../store';

/** Provides state and an action for removing a downloaded file. */
export function useDeleteDownload(fileId: InvenioRDMFileIdentifier) {
  const serverSettings = useServerSettings();
  const deleteDownload = async (): Promise<void> => {
    await deleteInvenioRDMFileDownload(serverSettings, fileId);
  };
  return { deleteDownload };
}
