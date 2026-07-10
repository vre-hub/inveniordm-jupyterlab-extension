import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { FileDialog } from '@jupyterlab/filebrowser';
import { INotebookTracker } from '@jupyterlab/notebook';
import { IDocumentManager } from '@jupyterlab/docmanager';

import { insertZenodoCell } from './insertCell';
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
      pickDownloadDirectory: async () => {
        const result = await FileDialog.getExistingDirectory({
          manager: docManager,
          title: 'Select download directory',
          label: 'Choose a directory for Zenodo downloads'
        });

        if (
          !result.button.accept ||
          !result.value ||
          result.value.length === 0
        ) {
          return null;
        }

        return result.value[0].path;
      },
      pickUploadFiles: async () => {
        const result = await FileDialog.getOpenFiles({
          manager: docManager,
          title: 'Select files',
          label: 'Choose files to upload to Zenodo',
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
      },
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
