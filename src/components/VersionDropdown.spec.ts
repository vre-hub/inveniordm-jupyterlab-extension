import { ZenodoRecordVersion } from '../api_calls';
import { findRecordIdentifier, recordIdentifierKey } from './VersionDropdown';

describe('VersionDropdown identifiers', () => {
  const versions: ZenodoRecordVersion[] = [
    {
      id: 'record-1',
      status: 'published',
      is_draft: false,
      versions: { index: 1 }
    },
    {
      id: 'record-1',
      status: 'draft',
      is_draft: true,
      versions: { index: 1 }
    }
  ];

  it('distinguishes draft and published variants with the same record ID', () => {
    expect(
      versions.map(version =>
        recordIdentifierKey({
          record_id: version.id,
          record_status: version.is_draft ? 'draft' : 'published'
        })
      )
    ).toEqual(['published:record-1', 'draft:record-1']);

    expect(findRecordIdentifier(versions, 'draft:record-1')).toEqual({
      record_id: 'record-1',
      record_status: 'draft'
    });
  });
});
