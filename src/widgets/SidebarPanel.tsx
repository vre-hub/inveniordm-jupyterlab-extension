import React from 'react';
import { VDomRenderer } from '@jupyterlab/apputils';

import { Tabs, TabItem } from '../components/Tabs';
import { ZenodoDepositions } from '../components/ZenodoDepositions';
import { ZenodoLoginForm } from '../components/ZenodoLoginForm';
import { ZenodoSearch } from '../components/ZenodoSearch';
import { setCurrentTabID, useCurrentTabID } from '../store';
import { DeveloperSettings } from '../components/DeveloperSettings';

const PANEL_CLASS = 'jp-ZenodoExtensionPanel';

type SidebarTab = TabItem<string> & {
  Component: React.FC;
};

const TABS: SidebarTab[] = [
  { id: 'login', label: 'Login', Component: ZenodoLoginForm },
  { id: 'search', label: 'Search', Component: ZenodoSearch },
  {
    id: 'settings',
    label: 'Settings',
    Component: DeveloperSettings,
  },
  { id: 'account', label: 'My Account', Component: ZenodoDepositions }
];


const Panel: React.FC = () => {
  const currentTabID = useCurrentTabID();
  const SelectedTabComponent = (TABS.find(tab => tab.id === currentTabID) ?? TABS[0]).Component;

  return (
    <div className={PANEL_CLASS}>
      <Tabs currentTab={currentTabID} onChange={setCurrentTabID} tabs={TABS} />
      <hr />
      <SelectedTabComponent />
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
