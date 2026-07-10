import { IDocumentManager } from '@jupyterlab/docmanager';
import { FileDialog } from '@jupyterlab/filebrowser';

export async function pickDownloadDirectory(
  docManager: IDocumentManager
): Promise<string | null> {
  const result = await FileDialog.getExistingDirectory({
    manager: docManager,
    title: 'Select download directory',
    label: 'Choose a directory for Zenodo downloads'
  });

  if (!result.button.accept || !result.value || result.value.length === 0) {
    return null;
  }

  return result.value[0].path;
}
