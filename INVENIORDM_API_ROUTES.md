# InvenioRDM API calls made by the JupyterLab extension

This document describes the Jupyter Server routes registered below
`<jupyter-base-url>/inveniordm-jupyterlab`, the requests they make to the configured
InvenioRDM instance, and why those requests are needed. The configured instance can be e.g. `https://zenodo.org` or `https://sandbox.zenodo.org`.

All extension routes require an authenticated Jupyter user. That is separate
from InvenioRDM authentication: calls to public InvenioRDM APIs can be made without a
InvenioRDM access token, while user records, drafts, grants, and write operations
normally require one. When a token is available, the extension sends it as a
Bearer token even when calling a public endpoint.

## The record distinctions used by the extension

### General records and user records

- **General records** come from `/api/records`. Search, record details, and the
  versions endpoint represent the generally visible, published record space.
  These calls are also used when the user is not logged in to InvenioRDM.
- **User records** come from `/api/user/records`. This is the authenticated
  user's working view and can contain both their published records and their
  unpublished drafts. The extension uses this view when ownership, draft state,
  or editability matters.
  Record refetching uses `GET /record-variants/:id` with an explicit
  `record_status`. The user-record API remains a collection operation used to
  list accessible drafts and published records.

### Drafts and published records

The extension uses `is_published` to choose a file-editing target:

- If `is_published` is false, the record is already a draft and is edited in
  place.
- If `is_published` is true, the published record is immutable. The extension
  rejects the file-editing request. A new-version draft must be created
  explicitly before its files can be changed.

InvenioRDM's published versions endpoint does not include an unpublished next
version. Consequently, the versions route combines the general versions API
with the user's record list to add accessible drafts. It uses the boolean
`is_draft` field, rather than `status`, to identify drafts in that list.

File operations include a `record_status` of either `draft` or `published` in
their file identifier. Downloads use only the matching draft or published file
endpoint. Local paths include the status as well as the record ID and file key,
so the two variants can be downloaded without overwriting one another.

## Naming convention

Every InvenioRDM-facing operation uses the same verb, domain, resource, and
qualifier vocabulary across layers. Python uses `snake_case`, TypeScript uses
`camelCase`, and route handlers describe the REST resource and cardinality.
For example, `get_inveniordm_record_variant`, `getInvenioRDMRecordVariant`, and
`InvenioRDMRecordVariantItemHandler` all describe the same operation.

The fixed verbs are `get`, `list`, `search`, `create`, `upload`, `delete`,
`open`, and `check`.

## Route summary

| Extension route                                  | Frontend call                          | InvenioRDM traffic                                                                                   |
| ------------------------------------------------ | -------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `GET /hello`                                     | —                                      | None                                                                                                 |
| `GET /access-token`                              | `useAccessTokenStatus`                 | `GET /api/me` only when a stored token is present                                                    |
| `GET /auth/login`                                | `constructInvenioRDMAuthUrl`           | Browser redirect to `/oauth/authorize`; no server-to-server API call                                 |
| `GET /auth/callback`                             | —                                      | `POST /oauth/token`                                                                                  |
| `GET /auth/logout`                               | `constructInvenioRDMAuthUrl`           | None; removes the locally stored token                                                               |
| `GET /records`                                   | `searchInvenioRDMRecords`              | `GET /api/records`                                                                                   |
| `GET /record-variants/:id?record_status=:status` | `getInvenioRDMRecordVariant`           | `GET /api/records/:id` or `GET /api/records/:id/draft`                                               |
| `GET /me`                                        | `getInvenioRDMMe`                      | `GET /api/me`                                                                                        |
| `GET /events`                                    | `subscribeToEvents`                    | None; local server-sent event stream                                                                 |
| `GET /user/records`                              | `listInvenioRDMUserRecords`            | `GET /api/user/records`, optionally followed by one linked files request per draft or restricted hit |
| `DELETE /user/records/:id`                       | `deleteInvenioRDMRecordDraft`          | `DELETE /api/records/:id/draft`                                                                      |
| `GET /records/:id/permission`                    | `getInvenioRDMRecordPermission`        | Direct draft or published record lookup, optionally followed by an edit-permission user-record query |
| `GET /records/:id/versions?include_drafts=true`  | `listInvenioRDMRecordVersions`         | General versions request, optionally supplemented with a user-record lookup for drafts               |
| `POST /records/:id/versions`                     | `createInvenioRDMRecordVersion`        | Create a new-version draft, then import the previous files                                           |
| `POST /user/records/draft-with-files`            | `createInvenioRDMRecordDraftWithFiles` | Create a draft, then initialize, upload, and commit every file                                       |
| `POST /user/records/:id/files`                   | `uploadInvenioRDMRecordFiles`          | Require an editable draft, then upload every file                                                    |
| `DELETE /user/records/:id/files`                 | `deleteInvenioRDMRecordFile`           | Require an editable draft, then delete the named draft file                                          |
| `GET /jobs`                                      | `getLatestActiveJobId`                 | None                                                                                                 |
| `GET /jobs/:id`                                  | `getJobProgress`                       | None                                                                                                 |
| `POST /jobs/:id/cancel`                          | `cancelJob`                            | None directly; cancellation cleanup can delete an initialized draft file                             |
| `POST /files/download`                           | `downloadInvenioRDMFile`               | In the background: streaming `GET` to the hard-coded published or draft file-content endpoint        |
| `DELETE /files/download`                         | `deleteInvenioRDMFileDownload`         | None                                                                                                 |
| `POST /files/status`                             | `getInvenioRDMFileDownloadStatus`      | None                                                                                                 |
| `POST /files/import-cell`                        | `getInvenioRDMFileImportCell`          | None                                                                                                 |
| `GET /settings/downloads-directory`              | —                                      | None                                                                                                 |
| `POST /settings/downloads-directory`             | `setInvenioRDMDownloadDirectory`       | None                                                                                                 |
| `DELETE /settings/downloads-directory`           | `unsetInvenioRDMDownloadDirectory`     | None                                                                                                 |

## Why some routes are complex

Some routes are inherently complex because of how the InvenioRDM/ InvenioRDM API works:

- Retrieving the file collection for a draft or a record with restricted files from `/api/user/records` requires an extra request
- There is no API endpoint that simply tells us the permissions the current user has for a specific record. The extension uses the user ID stored during authentication and the user-record details to infer ownership because owner access is not included in the access-grants response. InvenioRDM also denies editors access to the access-grants endpoint, so edit permission requires a filtered user-record query as a workaround.
- Record refetching sends the known `record_status` so the backend can call the
  draft or published endpoint directly.

### `GET /records`

Send `GET /api/records` with `q`, `page`, `size`, `sort`, and `allversions`.

The request searches the general published record space. Results from
`/api/records` contain their file collections, but not if the files are restricted. If
`include_files=true`, follow `links.files` for restricted results whose files
are not included in the search response and add the result as `files`.

### `GET /record-variants/:id?record_status=:status`

The required `record_status` query parameter must be `draft` or `published`;
any other or missing value returns HTTP 400. Send `GET /api/records/:id` for a
published record or `GET /api/records/:id/draft` for a draft.

This route deliberately does not inspect `/api/user/records`; the caller
identifies the exact representation to fetch.

### `GET /user/records`

1. Send `GET /api/user/records` with `page` and `size`.
2. If `include_files=true`, follow `links.files` for each record whose
   `is_draft` field is true or whose `access.files` value is `restricted`, and
   add the result as `files`.

The user-record API is required here because general search cannot list the
authenticated user's unpublished drafts. File requests are optional because
they add one InvenioRDM call per affected result and are only needed by views that
show file details.

### `DELETE /user/records/:id`

Send `DELETE /api/records/:id/draft` to discard the selected draft. InvenioRDM
only allows this operation for authenticated users with edit access to the
draft and returns an empty `204 No Content` response on success. The extension
then publishes `record.versions.changed` with `record_id`,
`discarded_draft_id`, the nullable `parent_id`, and the corrected version list.
The list is loaded before deletion and the discarded draft is removed before
the event is published, so it does not depend on InvenioRDM's search index having
observed the deletion yet.

### `GET /records/:id/permission?record_status=:status`

The route determines the current user's effective `preview`, `edit`, or
`manage` permission as follows. The required `record_status` query parameter
must be `draft` or `published`; any other or missing value returns HTTP 400. The
route returns the permission as a JSON string.

1. Read the current user's cached InvenioRDM ID. It is stored with the access token
   during the OAuth callback (or obtained from the proxy authentication status).
   If no user ID is available, the request fails.
2. Retrieve the record directly from the endpoint selected by `record_status`:
   `GET /api/records/:id/draft` for a draft or `GET /api/records/:id` for a
   published record. This avoids returning wrong permissions when published and draft permissions can differ, and avoids the only eventually consistent user-record search,
   which could miss a newly created draft and cause a race condition.
3. If `parent.access.grants` is present (including an empty list), return
   `manage`. In the responses used by this route, that field marks owners and
   users who have been granted manage access.
4. Otherwise, check for edit permission with
   `GET /api/user/records?q=id:<record-id> AND parent.access.grant_tokens:<token>&page=1&size=1`.
   The grant token is the dot-separated Base64 encoding of `user`, the cached
   user ID, and `edit` (including normal Base64 padding). Return `edit` when the
   query has a hit and `preview` otherwise.

The route does not request `links.access_grants` and does not compare the
cached user ID with `parent.access.owned_by.user`. The cached ID is used only to
construct the edit grant token, avoiding an additional `/api/me` request.

### `GET /records/:id/versions`

Pass `include_drafts=true` to include unpublished drafts (either new version drafts or drafts of old versions being edited) in the returned
versions. The parameter defaults to `true`; pass `false` to return only the
published versions from InvenioRDM's general versions endpoint.

1. Send `GET /api/records/:id/versions` and take its published hits.
2. If there are no published hits, send `GET /api/records/:id/draft` and return
   that initial draft as the only version. Treat `401`, `403`, or `404` as no
   accessible draft and return an empty list.
3. Otherwise, obtain the published hits' parent ID, which identifies the
   version family.
4. Send
   `GET /api/user/records?q=parent.id:<parent-id>&page=1&size=25&allversions=true`.
5. Keep all records whose `is_draft` field is true and whose parent ID matches.
6. Append those drafts to the published versions. Preserve both representations
   when a draft and published record have the same ID.

The general versions call is the authoritative list of published versions but
does not include drafts. The direct draft lookup handles a first-version draft,
for which there is no published hit from which to derive the parent ID. The
user-record listing supplies accessible drafts from the version family when
published versions already exist. A `401` or `403` from the user-record listing
is ignored, so callers without user-record access still get the published
versions. Other errors are propagated.

The family query is filtered by parent ID but is currently limited to the first
25 matching user records. A draft outside that page will be omitted; the code
has a TODO to paginate the lookup.

## Details of other Routes

### `POST /user/records/:id/files`

Before starting the background job, the route puts the InvenioRDM user ID cached
during authentication and the production/sandbox flag into the job metadata.
This prevents an upload job from one InvenioRDM account being mistaken for a job
belonging to a different account without making another InvenioRDM API request.

The background job then:

1. Uses the supplied ID as a draft ID; the route is intrinsically draft-only.
2. For each new file, performs initialize, content upload, and
   commit against `/api/records/:id/draft/files`, as described for the
   draft-with-files route.

A published record cannot be modified in place and file-editing routes do not
create a new version automatically. InvenioRDM rejects an ID without an editable
draft.

### `DELETE /user/records/:id/files`

Send `DELETE /api/records/:id/draft/files/:file-key`. The route is
intrinsically draft-only, so it does not need a record status lookup.

### `GET /access-token`

If there is no stored token, this route reports that directly and makes no
InvenioRDM request. If a token is present, it sends `GET /api/me` with a five-second
timeout. A `200` means the token is valid and a `401` means it is invalid. Other
request failures are also reported as an invalid token.

This call is needed because the presence of a locally stored token does not
prove that InvenioRDM still accepts it.

### `GET /auth/login`, `GET /auth/callback`, and `GET /auth/logout`

Login constructs a InvenioRDM `/oauth/authorize` URL and redirects the browser to
it. This is not a InvenioRDM API request made by the Jupyter server; the browser
performs the navigation so the user can authorize the extension.

After InvenioRDM redirects back, the callback exchanges the authorization code by
sending `POST /oauth/token`. This is needed to obtain the Bearer access token
used by authenticated API calls. The returned token is stored locally. Logout
only removes that local token; it does not call InvenioRDM to revoke it.

### `GET /me`

Send `GET /api/me` and return only `email` and `id`. The request identifies the
InvenioRDM account represented by the current token. Permission checks use the user
ID cached during authentication instead, as does upload-job scoping.

### `POST /records/:id/versions`

1. Send `POST /api/records/:id/versions` to create an unpublished next-version
   draft.
2. Read the returned draft ID and send
   `POST /api/records/:draft-id/draft/actions/files-import`.

The extension then publishes `record.versions.changed` with the created draft
and a corrected version list. The list is loaded before creation and the new
draft is appended before publishing, so it does not depend on InvenioRDM's search
index having observed the creation yet.

InvenioRDM creates the version draft without files. The second call copies the
previous version's files so the new draft starts as a faithful editable version
instead of appearing empty.

### `POST /user/records/draft-with-files`

This starts a background upload job:

1. Send `POST /api/records` with `{"files": {"enabled": true}}` to create an
   empty, file-enabled draft.
2. Read the returned draft record ID and construct
   `/api/records/:id/draft/files`.
3. For each selected local file:
   1. Send `POST /api/records/:id/draft/files` with the file key to initialize
      its entry.
   2. Send `PUT` to the returned `links.content` URL to stream the bytes.
   3. Send `POST` to the returned `links.commit` URL to finalize the file.

Draft creation is needed because files must belong to a record. Initialization
lets InvenioRDM allocate the file entry and provide canonical content and commit
links; uploading transfers the bytes; committing makes the upload available in
the draft. If cancellation occurs after initialization, the extension sends
`DELETE` for that draft file so an empty file entry is not left behind.

### Job routes

`GET /jobs`, `GET /jobs/:id`, and `POST /jobs/:id/cancel` primarily operate on
the extension's in-memory job manager. Record-file upload jobs are tagged and
filtered by the InvenioRDM user ID cached during authentication and by the current
environment; looking them up does not make a InvenioRDM API request.

Cancellation itself makes no immediate InvenioRDM request. If an upload notices
the cancellation after its file entry has been initialized, its cleanup path
deletes that entry from the draft.

### `POST /files/download`

The background download job:

1. For a draft identifier, sends a streaming `GET` directly to
   `/api/records/:id/draft/files/:file-key/content`.
2. For a published identifier, sends a streaming `GET` directly to
   `/api/records/:id/files/:file-key/content`.
3. Writes the returned bytes locally.

The local destination is
`<downloads>/<record-id>/<draft|published>/<file-key>`.

### Routes with no InvenioRDM traffic

- `GET /hello` returns a static local response.
- `GET /events` keeps a local server-sent event connection open.
- `GET /jobs` reads and filters local job progress; upload-job filters use the
  cached InvenioRDM user ID and environment.
- `GET /jobs/:id` reads local job progress.
- `POST /jobs/:id/cancel` sets a local cancellation flag (with the conditional
  upload cleanup noted above).
- `DELETE /files/download` deletes a local download.
- `POST /files/status` checks for a local download.
- `POST /files/import-cell` constructs a cell action for a local download.
- All methods on `/settings/downloads-directory` read or update local settings.
