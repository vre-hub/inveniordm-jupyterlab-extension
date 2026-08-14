import { IDocumentManager } from '@jupyterlab/docmanager';
import { FileDialog } from '@jupyterlab/filebrowser';

/** Opens JupyterLab's file picker and returns selected file paths. */
export async function pickUploadFiles(
  docManager: IDocumentManager
): Promise<string[] | null> {
  const result = await FileDialog.getOpenFiles({
    manager: docManager,
    title: 'Select files',
    label: `Choose files to upload`,
    filter: model => {
      return model.type === 'file' ? {} : null;
    }
  });

  if (!result.button.accept || !result.value) {
    return null;
  }

  const files = result.value.filter(model => model.type === 'file');
  if (files.length === 0) {
    return null;
  }

  return files.map(file => file.path);
}
