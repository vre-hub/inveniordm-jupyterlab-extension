import { useZenodoRecordPermission, ZenodoRecordData } from '../api_calls';

export function useHasEditingRights(record: ZenodoRecordData): boolean {
  const isDraft = record.is_draft;
  const userPermission = useZenodoRecordPermission(
    record.id,
    isDraft ? 'draft' : 'published'
  );
  return userPermission === 'edit' || userPermission === 'manage';
}
