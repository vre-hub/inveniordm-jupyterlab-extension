import {
  useInvenioRDMRecordPermission,
  InvenioRDMRecordData
} from '../api_calls';

/** Reports whether the current user may edit a record draft. */
export function useHasEditingRights(record: InvenioRDMRecordData): boolean {
  const isDraft = record.is_draft;
  const userPermission = useInvenioRDMRecordPermission(
    record.id,
    isDraft ? 'draft' : 'published'
  );
  return userPermission === 'edit' || userPermission === 'manage';
}
