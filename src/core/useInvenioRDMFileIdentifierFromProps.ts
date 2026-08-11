import React from 'react';
import { InvenioRDMFile, InvenioRDMFileIdentifier } from '../api_calls';

export function useInvenioRDMFileIdentifierFromProps(
  file: InvenioRDMFile,
  recordId: string,
  isDraft: boolean
): InvenioRDMFileIdentifier {
  return React.useMemo<InvenioRDMFileIdentifier>(
    () => ({
      file_key: file.key,
      record_id: recordId,
      record_status: isDraft ? 'draft' : 'published'
    }),
    [file.key, isDraft, recordId]
  );
}
