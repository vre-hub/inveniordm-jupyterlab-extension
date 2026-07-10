import React from 'react';

import {
  MinimalDepositionDraftResponse,
  createMinimalDepositionDraft
} from '../api_calls';
import { useServerSettings } from '../store';
import { PickFilesButton } from './FilePicker';

export const Upload: React.FC = () => {
  const serverSettings = useServerSettings();
  const [filePaths, setFilePaths] = React.useState<string[]>([]);
  const [isCreatingDraft, setIsCreatingDraft] = React.useState(false);
  const [result, setResult] =
    React.useState<MinimalDepositionDraftResponse | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const canCreateDraft = filePaths.length > 0 && !isCreatingDraft;

  const onSubmit = async (event: React.FormEvent): Promise<void> => {
    event.preventDefault();
    if (!canCreateDraft) {
      return;
    }

    const draftTab = window.open('', '_blank');
    setIsCreatingDraft(true);
    setResult(null);
    setError(null);

    try {
      const deposition = await createMinimalDepositionDraft(
        serverSettings,
        filePaths
      );
      setResult(deposition);
      const draftUrl = `https://sandbox.zenodo.org/uploads/${deposition.id}`;
      if (draftTab) {
        draftTab.location.href = draftUrl;
      } else {
        window.open(draftUrl, '_blank');
      }
    } catch (reason) {
      draftTab?.close();
      setError(String(reason));
    } finally {
      setIsCreatingDraft(false);
    }
  };

  return (
    <form onSubmit={onSubmit}>
      <h2>Upload</h2>
      <PickFilesButton
        buttonText="Select files"
        onFilesSelected={files => setFilePaths(files)}
      />
      {filePaths.length > 0 && (
        <ul>
          {filePaths.map(filePath => (
            <li key={filePath}>{filePath}</li>
          ))}
        </ul>
      )}
      <button disabled={!canCreateDraft} type="submit">
        {isCreatingDraft ? 'Creating draft...' : 'Upload to Zenodo Draft'}
      </button>
      {error && <p>{error}</p>}
      {result && <p>Created draft {result.id}</p>}
    </form>
  );
};
