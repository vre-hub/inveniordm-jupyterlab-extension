import { ZenodoRecordVersion } from '../api_calls';
import { selectVersionAfterDraftDiscard } from '.';

describe('selectVersionAfterDraftDiscard', () => {
  const sameRecordPublished: ZenodoRecordVersion = {
    id: 'record-1',
    status: 'published',
    is_draft: false,
    versions: { index: 1 }
  };
  const latestPublished: ZenodoRecordVersion = {
    id: 'record-2',
    status: 'published',
    is_draft: false,
    versions: { index: 2 }
  };

  it('prefers the published representation with the discarded draft ID', () => {
    expect(
      selectVersionAfterDraftDiscard(
        [sameRecordPublished, latestPublished],
        'record-1'
      )
    ).toBe(sameRecordPublished);
  });

  it('falls back to the latest remaining version', () => {
    expect(
      selectVersionAfterDraftDiscard(
        [sameRecordPublished, latestPublished],
        'missing'
      )
    ).toBe(latestPublished);
  });
});
