import React from 'react';
import { VDomRenderer } from '@jupyterlab/apputils';
import { Library, LogIn, Search, Settings, Upload } from 'lucide-react';

import { Tabs, TabItem } from '../components/Tabs';
import { ZenodoUserRecordList } from '../components/ZenodoUserRecordList';
import { ZenodoLoginForm } from '../components/ZenodoLoginForm';
import { ZenodoRecordSearch } from '../components/ZenodoRecordSearch';
import { setCurrentTabID, useCurrentTabID } from '../store';
import { DeveloperSettings } from '../components/DeveloperSettings';
import { ZenodoRecordDraftUpload } from '../components/ZenodoRecordDraftUpload';

const PANEL_CLASS = 'jp-ZenodoExtensionPanel';
const TAB_PANEL_ID = 'zenodo-tab-panel';

type SidebarTab = TabItem<string> & {
  Component: React.FC;
};

const TABS: SidebarTab[] = [
  { id: 'login', label: 'Login', icon: LogIn, Component: ZenodoLoginForm },
  {
    id: 'search',
    label: 'Search',
    icon: Search,
    Component: ZenodoRecordSearch
  },
  {
    id: 'upload',
    label: 'Upload',
    icon: Upload,
    Component: ZenodoRecordDraftUpload
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: Settings,
    Component: DeveloperSettings
  },
  {
    id: 'account',
    label: 'My Records',
    icon: Library,
    Component: ZenodoUserRecordList
  }
];

const Panel: React.FC = () => {
  const currentTabID = useCurrentTabID();
  const selectedTab = TABS.find(tab => tab.id === currentTabID) ?? TABS[0];
  const SelectedTabComponent = selectedTab.Component;

  return (
    <div className={`${PANEL_CLASS} flex h-full min-h-0 flex-col`}>
      <Tabs
        currentTab={currentTabID}
        onChange={setCurrentTabID}
        panelId={TAB_PANEL_ID}
        tabs={TABS}
      />
      <div
        aria-labelledby={`tab-${selectedTab.id}`}
        className="min-h-0 flex-1 overflow-auto p-3"
        id={TAB_PANEL_ID}
        role="tabpanel"
        tabIndex={0}
      >
        <SelectedTabComponent />
      </div>
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
