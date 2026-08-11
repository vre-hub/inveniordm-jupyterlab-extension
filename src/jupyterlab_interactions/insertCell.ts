import { INotebookTracker } from '@jupyterlab/notebook';
import { JSONExt, PartialJSONObject } from '@lumino/coreutils';

type InsertInvenioRDMCellAction = {
  cell_type: 'code' | 'markdown';
  source: string;
  metadata_inveniordm_jupyterlab?: PartialJSONObject;
};

export function insertInvenioRDMCell(
  action: InsertInvenioRDMCellAction,
  notebooks: INotebookTracker
): void {
  const model = notebooks.currentWidget?.model;

  // If a cell with the same metadata already exists, do not insert a new cell.
  const existingCell = model?.sharedModel.cells.find(cell => {
    const metadata = cell.getMetadata('inveniordm_jupyterlab');
    return (
      metadata &&
      action.metadata_inveniordm_jupyterlab &&
      JSONExt.deepEqual(metadata, action.metadata_inveniordm_jupyterlab)
    );
  });
  if (existingCell) {
    console.log(
      'A cell with the same InvenioRDM metadata already exists. Not inserting a new cell.'
    );
    return;
  }

  const indexAboveCurrentCell =
    notebooks.currentWidget?.content.activeCellIndex ?? 0;
  model?.sharedModel.insertCell(indexAboveCurrentCell, {
    cell_type: action.cell_type,
    source: action.source,
    metadata: {
      inveniordm_jupyterlab: action.metadata_inveniordm_jupyterlab
    }
  });
}

export type { InsertInvenioRDMCellAction };
