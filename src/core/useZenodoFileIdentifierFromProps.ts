import React from 'react';
import { ZenodoFile, ZenodoFileIdentifier } from '../api_calls';

export function useZenodoFileIdentifierFromProps(
  file: ZenodoFile,
  recordId: string,
  isDraft: boolean
): ZenodoFileIdentifier {
  return React.useMemo<ZenodoFileIdentifier>(
    () => ({
      file_key: file.key,
      record_id: recordId,
      record_status: isDraft ? 'draft' : 'published'
    }),
    [file.key, isDraft, recordId]
  );
}
