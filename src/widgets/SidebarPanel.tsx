import React from 'react';
import { VDomRenderer } from '@jupyterlab/apputils';
import {
  CircleUser,
  Library,
  Search,
  Settings as SettingsIcon,
  Upload
} from 'lucide-react';

import { Tabs, TabItem } from '../components/Tabs';
import { ZenodoUserRecordList } from '../components/ZenodoUserRecordList';
import { ZenodoLoginForm } from '../components/ZenodoLoginForm';
import { ZenodoRecordSearch } from '../components/ZenodoRecordSearch';
import { setCurrentTabID, useCurrentTabID } from '../store';
import { Settings } from '../components/Settings';
import { ZenodoRecordDraftUpload } from '../components/ZenodoRecordDraftUpload';
import { useCurrentRemoteServer } from '../core';

const PANEL_CLASS = 'jp-ZenodoExtensionPanel';
const TAB_PANEL_ID = 'zenodo-tab-panel';

type SidebarTab = TabItem<string> & {
  Component: React.FC;
};

const TABS: SidebarTab[] = [
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
    id: 'user-records',
    label: 'My Records',
    icon: Library,
    Component: ZenodoUserRecordList
  },
  {
    id: 'account',
    label: 'Account',
    icon: CircleUser,
    Component: ZenodoLoginForm
  },
  {
    id: 'settings',
    icon: SettingsIcon,
    Component: Settings
  }
];
const DEFAULT_TAB_ID = 'account';

const Panel: React.FC<{
  onRemoteNameChanged: (displayName: string | undefined) => void;
}> = ({ onRemoteNameChanged }) => {
  const currentTabID = useCurrentTabID();
  const { remoteServer } = useCurrentRemoteServer();

  React.useEffect(() => {
    onRemoteNameChanged(remoteServer?.display_name);
  }, [onRemoteNameChanged, remoteServer?.display_name]);
  const selectedTab =
    TABS.find(tab => tab.id === currentTabID) ??
    TABS.find(tab => tab.id === DEFAULT_TAB_ID)!;
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
        className="min-h-0 flex-1 overflow-y-auto px-2 py-3"
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
    super.title.label = 'Repository';
    super.title.caption = 'Remote repository integration';
    super.title.closable = true;
  }

  render(): React.ReactElement {
    return (
      <Panel
        onRemoteNameChanged={displayName => {
          this.title.label = displayName ?? 'InvenioRDM';
          this.title.caption = displayName
            ? `${displayName} integration`
            : 'InvenioRDM integration';
        }}
      />
    );
  }
}
