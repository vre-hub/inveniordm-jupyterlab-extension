import React from "react";
import { getZenodoUserRecord } from "../api_calls";
import { useServerSettings } from "../store";

/**
 * A button that opens a Zenodo record editor in a new tab.
 */
export function EditRecordButton({ id }: { id: string }): JSX.Element {
  const serverSettings = useServerSettings();
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const openRecord = async (): Promise<void> => {
    setIsLoading(true);
    setError(null);

    // Open the tab before awaiting the request so browsers do not treat it as
    // an unsolicited popup.
    const recordWindow = window.open('', '_blank');

    try {
      const record = await getZenodoUserRecord(serverSettings, id);
      const url = record.links?.self_html;
      if (!url) {
        throw new Error('Zenodo did not provide a link for this record');
      }

      if (recordWindow) {
        recordWindow.location.href = url;
      } else {
        window.open(url, '_blank');
      }
    } catch (reason) {
      recordWindow?.close();
      setError(String(reason));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <button
        disabled={isLoading}
        onClick={() => void openRecord()}
        type="button"
      >
        {isLoading ? 'Opening...' : 'Edit Record'}
      </button>
      {error ? <span>{error}</span> : null}
    </>
  );
}
