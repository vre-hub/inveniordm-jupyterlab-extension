import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { requestAPI } from './request';
import { SidebarPanel } from './widgets/SidebarPanel';

/**
 * Initialization data for the zenodo_jupyterlab extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'zenodo_jupyterlab:plugin',
  description: 'Integrates Zenodo into JupyterLab.',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension zenodo_jupyterlab is activated!');

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
