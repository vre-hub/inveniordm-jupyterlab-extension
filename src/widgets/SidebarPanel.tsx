import React from 'react';
import { VDomRenderer } from '@jupyterlab/apputils';

const PANEL_CLASS = 'jp-ZenodoExtensionPanel';

const Panel: React.FC = () => (
  <div className={PANEL_CLASS}>
    <h2>Zenodo</h2>
    <p>Zenodo extension</p>
  </div>
);

export class SidebarPanel extends VDomRenderer {
  constructor() {
    super();
    super.addClass(PANEL_CLASS);
    super.title.label = 'Zenodo';
    super.title.caption = 'Zenodo Integration';
    super.title.closable = true;
  }

  render(): React.ReactElement {
    return <Panel />;
  }
}
