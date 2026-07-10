import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { INotebookTracker } from '@jupyterlab/notebook';
import { IDocumentManager } from '@jupyterlab/docmanager';

import {
  insertZenodoCell,
  pickDownloadDirectory,
  pickUploadFiles
} from './jupyterlab_interactions';
import { requestAPI } from './request';
import { initializeZenodoStore } from './store';
import { SidebarPanel } from './widgets/SidebarPanel';

/**
 * Initialization data for the zenodo_jupyterlab extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'zenodo_jupyterlab:plugin',
  description: 'Integrates Zenodo into JupyterLab.',
  autoStart: true,
  requires: [INotebookTracker, IDocumentManager],
  activate: (
    app: JupyterFrontEnd,
    notebooks: INotebookTracker,
    docManager: IDocumentManager
  ) => {
    console.log('JupyterLab extension zenodo_jupyterlab is activated!');

    initializeZenodoStore({
      insertZenodoCell: action => insertZenodoCell(action, notebooks),
      pickDownloadDirectory: () => pickDownloadDirectory(docManager),
      pickUploadFiles: () => pickUploadFiles(docManager),
      serverSettings: app.serviceManager.serverSettings
    });

    const sidebarPanel = new SidebarPanel();
    sidebarPanel.id = 'zenodo_jupyterlab:panel';
    app.shell.add(sidebarPanel, 'left', { rank: 900 });
    app.shell.activateById(sidebarPanel.id);

    requestAPI<any>('hello', app.serviceManager.serverSettings)
      .then(data => {
        console.log(data);
      })
      .catch(reason => {
        console.error(
          `The zenodo_jupyterlab server extension appears to be missing.\n${reason}`
        );
      });
  }
};

export default plugin;
