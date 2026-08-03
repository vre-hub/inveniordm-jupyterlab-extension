import { ZenodoFileIdentifier, deleteZenodoFileDownload } from '../api_calls';
import { useServerSettings } from '../store';

export function useDeleteDownload(fileId: ZenodoFileIdentifier) {
  const serverSettings = useServerSettings();
  const deleteDownload = async (): Promise<void> => {
    await deleteZenodoFileDownload(serverSettings, fileId);
  };
  return { deleteDownload };
}
