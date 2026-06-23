import { INotebookTracker } from '@jupyterlab/notebook';
import { JSONExt, PartialJSONObject } from '@lumino/coreutils';

type InsertZenodoCellAction = {
  cell_type: 'code' | 'markdown';
  source: string;
  metadata_zenodo_jupyterlab?: PartialJSONObject;
};

export function insertZenodoCell(
  action: InsertZenodoCellAction,
  notebooks: INotebookTracker
): void {
  const model = notebooks.currentWidget?.model;

  // If a cell with the same metadata already exists, do not insert a new cell.
  const existingCell = model?.sharedModel.cells.find(cell => {
    const metadata = cell.getMetadata('zenodo_jupyterlab');
    return (
      metadata &&
      action.metadata_zenodo_jupyterlab &&
      JSONExt.deepEqual(metadata, action.metadata_zenodo_jupyterlab)
    );
  });
  if (existingCell) {
    console.log(
      'A cell with the same Zenodo metadata already exists. Not inserting a new cell.'
    );
    return;
  }

  const indexAboveCurrentCell =
    notebooks.currentWidget?.content.activeCellIndex ?? 0;
  model?.sharedModel.insertCell(indexAboveCurrentCell, {
    cell_type: action.cell_type,
    source: action.source,
    metadata: {
      zenodo_jupyterlab: action.metadata_zenodo_jupyterlab
    }
  });
}

export type { InsertZenodoCellAction };
