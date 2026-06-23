import React from 'react';
import { VDomRenderer } from '@jupyterlab/apputils';

import { ZenodoDepositions } from '../components/ZenodoDepositions';
import { ZenodoLoginForm } from '../components/ZenodoLoginForm';
import { ZenodoSandboxOverrideSetting } from '../components/ZenodoSandboxOverrideSetting';
import { ZenodoSearch } from '../components/ZenodoSearch';
import { ZenodoUserProfile } from '../components/ZenodoUserProfile';

const PANEL_CLASS = 'jp-ZenodoExtensionPanel';

const Panel: React.FC = () => {
  return (
    <div className={PANEL_CLASS}>
      <ZenodoLoginForm />
      <hr />
      <ZenodoUserProfile />
      <hr />
      <ZenodoSandboxOverrideSetting />
      <hr />
      <ZenodoDepositions />
      <hr />
      <ZenodoSearch />
    </div>
  );
};

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
