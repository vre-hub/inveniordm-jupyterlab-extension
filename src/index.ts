import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { INotebookTracker } from '@jupyterlab/notebook';
import { IDocumentManager } from '@jupyterlab/docmanager';

import {
  insertInvenioRDMCell,
  pickDownloadDirectory,
  pickUploadFiles
} from './jupyterlab_interactions';
import { requestAPI } from './request';
import { initializeInvenioRDMStore } from './store';
import { SidebarPanel } from './widgets/SidebarPanel';

/**
 * Initialization data for the inveniordm_jupyterlab extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'inveniordm_jupyterlab:plugin',
  description: 'Integrates InvenioRDM into JupyterLab.',
  autoStart: true,
  requires: [INotebookTracker, IDocumentManager],
  activate: (
    app: JupyterFrontEnd,
    notebooks: INotebookTracker,
    docManager: IDocumentManager
  ) => {
    console.log('JupyterLab extension inveniordm_jupyterlab is activated!');

    initializeInvenioRDMStore({
      insertInvenioRDMCell: action => insertInvenioRDMCell(action, notebooks),
      pickDownloadDirectory: () => pickDownloadDirectory(docManager),
      pickUploadFiles: () => pickUploadFiles(docManager),
      serverSettings: app.serviceManager.serverSettings
    });

    const sidebarPanel = new SidebarPanel();
    sidebarPanel.id = 'inveniordm_jupyterlab:panel';
    app.shell.add(sidebarPanel, 'left', { rank: 900 });
    app.shell.activateById(sidebarPanel.id);

    requestAPI<any>('hello', app.serviceManager.serverSettings)
      .then(data => {
        console.log(data);
      })
      .catch(reason => {
        console.error(
          `The inveniordm_jupyterlab server extension appears to be missing.\n${reason}`
        );
      });
  }
};

export default plugin;
