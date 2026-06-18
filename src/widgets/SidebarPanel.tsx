import React from 'react';
import { VDomRenderer } from '@jupyterlab/apputils';
import { ServerConnection } from '@jupyterlab/services';

import { ZenodoLoginForm } from '../components/ZenodoLoginForm';
import { ZenodoSearch } from '../components/ZenodoSearch';

const PANEL_CLASS = 'jp-ZenodoExtensionPanel';

interface IPanelProps {
  serverSettings: ServerConnection.ISettings;
}

const Panel: React.FC<IPanelProps> = ({ serverSettings }) => {
  return (
    <div className={PANEL_CLASS}>
      <ZenodoLoginForm serverSettings={serverSettings} />
      <hr />
      <ZenodoSearch serverSettings={serverSettings} />
    </div>
  );
};

export class SidebarPanel extends VDomRenderer {
  constructor(private serverSettings: ServerConnection.ISettings) {
    super();
    super.addClass(PANEL_CLASS);
    super.title.label = 'Zenodo';
    super.title.caption = 'Zenodo Integration';
    super.title.closable = true;
  }

  render(): React.ReactElement {
    return <Panel serverSettings={this.serverSettings} />;
  }
}
