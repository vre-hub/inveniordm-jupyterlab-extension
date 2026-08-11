import { InvenioRDMFileIdentifier, deleteInvenioRDMFileDownload } from '../api_calls';
import { useServerSettings } from '../store';

export function useDeleteDownload(fileId: InvenioRDMFileIdentifier) {
  const serverSettings = useServerSettings();
  const deleteDownload = async (): Promise<void> => {
    await deleteInvenioRDMFileDownload(serverSettings, fileId);
  };
  return { deleteDownload };
}
