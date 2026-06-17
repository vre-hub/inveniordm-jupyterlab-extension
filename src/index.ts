import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { requestAPI } from './request';

/**
 * Initialization data for the zenodo_jupyterlab extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'zenodo_jupyterlab:plugin',
  description: 'Integrates Zenodo into JupyterLab.',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension zenodo_jupyterlab is activated!');

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
