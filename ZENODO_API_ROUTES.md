# Zenodo API calls made by the JupyterLab extension

This document describes the Jupyter Server routes registered below
`<jupyter-base-url>/zenodo-jupyterlab`, the requests they make to the configured
Zenodo instance, and why those requests are needed. The configured instance is
either `https://zenodo.org` or `https://sandbox.zenodo.org`.

All extension routes require an authenticated Jupyter user. That is separate
from Zenodo authentication: calls to public Zenodo APIs can be made without a
Zenodo access token, while user records, drafts, grants, and write operations
normally require one. When a token is available, the extension sends it as a
Bearer token even when calling a public endpoint.

## The record distinctions used by the extension

### General records and user records

- **General records** come from `/api/records`. Search, record details, and the
  versions endpoint represent the generally visible, published record space.
  These calls are also used when the user is not logged in to Zenodo.
- **User records** come from `/api/user/records`. This is the authenticated
  user's working view and can contain both their published records and their
  unpublished drafts. The extension uses this view when ownership, draft state,
  or editability matters.
- Fetching one user record is implemented as a search of `/api/user/records`
  with `q=id:<record-id>`, `size=10`, and `allversions=true`, followed by an
  exact string comparison of the returned IDs. The exact comparison prevents a
  nonmatching search hit from being treated as the requested record.

The route name expresses which view is requested. `GET /records/:id` always
uses the general record API; `GET /user/records/:id` always uses the user-record
API. There is no automatic fallback between the two except in the file/version
flows described below.

### Drafts and published records

The extension uses `is_published` to choose a file-editing target:

- If `is_published` is false, the record is already a draft and is edited in
  place.
- If `is_published` is true, the published record is immutable. The extension
  rejects the file-editing request. A new-version draft must be created
  explicitly before its files can be changed.

Zenodo's published versions endpoint does not include an unpublished next
version. Consequently, the versions route combines the general versions API
with the user's record list to add accessible drafts. It uses the boolean
`is_draft` field, rather than `status`, to identify drafts in that list.

File operations include a `record_status` of either `draft` or `published` in
their file identifier. Downloads use only the matching draft or published file
endpoint. Local paths include the status as well as the record ID and file key,
so the two variants can be downloaded without overwriting one another.

## Naming convention

Every Zenodo-facing operation uses the same verb, domain, resource, and
qualifier vocabulary across layers. Python uses `snake_case`, TypeScript uses
`camelCase`, and route handlers describe the REST resource and cardinality.
For example, `get_zenodo_record`, `getZenodoRecord`, and
`ZenodoRecordItemHandler` all describe the same operation.

The fixed verbs are `get`, `list`, `search`, `create`, `upload`, `delete`,
`open`, and `check`.

## Route summary

| Extension route                                 | Frontend call                      | Zenodo traffic                                                                                        |
| ----------------------------------------------- | ---------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `GET /hello`                                    | —                                  | None                                                                                                  |
| `GET /access-token`                             | `useAccessTokenStatus`             | `GET /api/me` only when a stored token is present                                                     |
| `GET /auth/login`                               | `constructZenodoAuthUrl`           | Browser redirect to `/oauth/authorize`; no server-to-server API call                                  |
| `GET /auth/callback`                            | —                                  | `POST /oauth/token`                                                                                   |
| `GET /auth/logout`                              | `constructZenodoAuthUrl`           | None; removes the locally stored token                                                                |
| `GET /records`                                  | `searchZenodoRecords`              | `GET /api/records`                                                                                    |
| `GET /records/:id`                              | `getZenodoRecord`                  | `GET /api/records/:id`                                                                                |
| `GET /me`                                       | `getZenodoMe`                      | `GET /api/me`                                                                                         |
| `GET /events`                                   | `subscribeToEvents`                | None; local server-sent event stream                                                                  |
| `GET /user/records`                             | `listZenodoUserRecords`            | `GET /api/user/records`, optionally followed by one linked files request per draft or restricted hit  |
| `GET /user/records/:id`                         | `getZenodoUserRecord`              | User-record search, followed by its linked files request if it is a draft or its files are restricted |
| `DELETE /user/records/:id`                      | `deleteZenodoRecordDraft`          | `DELETE /api/records/:id/draft`                                                                       |
| `GET /records/:id/permission`                   | `getZenodoRecordPermission`        | Direct draft or published record lookup, optionally followed by an edit-permission user-record query  |
| `GET /records/:id/versions?include_drafts=true` | `listZenodoRecordVersions`         | General versions request, optionally supplemented with a user-record lookup for drafts                |
| `POST /records/:id/versions`                    | `createZenodoRecordVersion`        | Create a new-version draft, then import the previous files                                            |
| `POST /user/records/draft-with-files`           | `createZenodoRecordDraftWithFiles` | Create a draft, then initialize, upload, and commit every file                                        |
| `POST /user/records/:id/files`                  | `uploadZenodoRecordFiles`          | Require an editable draft, then upload every file                                                     |
| `DELETE /user/records/:id/files`                | `deleteZenodoRecordFile`           | Require an editable draft, then delete the named draft file                                           |
| `GET /jobs`                                     | `getLatestActiveJobId`             | None                                                                                                  |
| `GET /jobs/:id`                                 | `getJobProgress`                   | None                                                                                                  |
| `POST /jobs/:id/cancel`                         | `cancelJob`                        | None directly; cancellation cleanup can delete an initialized draft file                              |
| `POST /files/download`                          | `downloadZenodoFile`               | In the background: streaming `GET` to the hard-coded published or draft file-content endpoint         |
| `DELETE /files/download`                        | `deleteZenodoFileDownload`         | None                                                                                                  |
| `POST /files/status`                            | `getZenodoFileDownloadStatus`      | None                                                                                                  |
| `POST /files/import-cell`                       | `getZenodoFileImportCell`          | None                                                                                                  |
| `GET /settings/downloads-directory`             | —                                  | None                                                                                                  |
| `POST /settings/downloads-directory`            | `setZenodoDownloadDirectory`       | None                                                                                                  |
| `DELETE /settings/downloads-directory`          | `unsetZenodoDownloadDirectory`     | None                                                                                                  |

## Details of the most problematic Routes

Some routes are inherently complex because of how the Zenodo/ InvenioRDM API works:

- Retrieving the file collection for a draft or a record with restricted files from `/api/user/records` requires an extra request
- There is no API endpoint that simply tells us the permissions the current user has for a specific record. The extension uses the user ID stored during authentication and the user-record details to infer ownership because owner access is not included in the access-grants response. Zenodo also denies editors access to the access-grants endpoint, so edit permission requires a filtered user-record query as a workaround.
- Getting details for drafts and published records requires us to use two different endpoints, so if we want to make a call to the correct endpoint, we need to infer/cache/send from the client if a specific record is still in the draft stage or not. This is unneccessarily complex, so we usually just make two calls and get the details from the one that succeeds if we can't avoid it.

### `GET /records`

Send `GET /api/records` with `q`, `page`, `size`, `sort`, and `allversions`.

The request searches the general published record space. Results from
`/api/records` contain their file collections, but not if the files are restricted. If
`include_files=true`, follow `links.files` for restricted results whose files
are not included in the search response and add the result as `files`.

### `GET /records/:id`

Send `GET /api/records/:id` for general record details. Published record
details already contain the file collection, so no linked files request is
needed.

This route deliberately does not inspect `/api/user/records`; it represents the
general-record view.

### `GET /user/records`

1. Send `GET /api/user/records` with `page` and `size`.
2. If `include_files=true`, follow `links.files` for each record whose
   `is_draft` field is true or whose `access.files` value is `restricted`, and
   add the result as `files`.

The user-record API is required here because general search cannot list the
authenticated user's unpublished drafts. File requests are optional because
they add one Zenodo call per affected result and are only needed by views that
show file details.

### `GET /user/records/:id`

1. Search `GET /api/user/records?q=id:<id>&size=10&allversions=true` and select
   the exact matching ID.
2. If the selected record's `is_draft` field is true or its `access.files`
   value is `restricted`, follow its `links.files` URL, if present.

The first request resolves the record in the authenticated user's view, which
is what exposes draft state and records accessible to the user. The second
request is especially important for drafts and restricted files because their
file lists are not included in the user-record search result. The underlying
request helper accepts `include_files=false` for callers that only need record
metadata; this route keeps the default value of `true` because its frontend
response includes files.

### `DELETE /user/records/:id`

Send `DELETE /api/records/:id/draft` to discard the selected draft. InvenioRDM
only allows this operation for authenticated users with edit access to the
draft and returns an empty `204 No Content` response on success. The extension
then publishes `record.changed.<id>` with type `draft_discarded`; the record
details listener responds by attempting to reload the discarded record.

### `GET /records/:id/permission?record_status=:status`

The route determines the current user's effective `preview`, `edit`, or
`manage` permission as follows. The required `record_status` query parameter
must be `draft` or `published`; any other or missing value returns HTTP 400. The
route returns the permission as a JSON string.

1. Read the current user's cached Zenodo ID. It is stored with the access token
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
published versions from Zenodo's general versions endpoint.

1. Send `GET /api/records/:id/versions` and take its published hits.
2. If there are no published hits, search
   `GET /api/user/records?q=id:<id>&size=10&allversions=true` and return the
   exact matching user record as the only version. Treat `401`, `403`, or `404`
   as no accessible record and return an empty list.
3. Otherwise, obtain the published hits' parent ID, which identifies the
   version family.
4. Send
   `GET /api/user/records?q=parent.id:<parent-id>&page=1&size=25&allversions=true`.
5. Keep all records whose `is_draft` field is true and whose parent ID matches.
6. Append those drafts to the published versions and deduplicate by record ID,
   preferring the draft representation when a published hit has the same ID.

The general versions call is the authoritative list of published versions but
does not include drafts. The targeted user-record lookup handles a first-version
draft, for which there is no published hit from which to derive the parent ID.
The user-record listing supplies accessible drafts from the version family when
published versions already exist. A `401` or `403` from the user-record listing
is ignored, so callers without user-record access still get the published
versions. Other errors are propagated.

The family query is filtered by parent ID but is currently limited to the first
25 matching user records. A draft outside that page will be omitted; the code
has a TODO to paginate the lookup.

### `POST /user/records/:id/files`

Before starting the background job, the route puts the Zenodo user ID cached
during authentication and the production/sandbox flag into the job metadata.
This prevents an upload job from one Zenodo account being mistaken for a job
belonging to a different account without making another Zenodo API request.

The background job then:

1. Resolves the record through `/api/user/records` without expanding its files.
   Only `is_published` is needed to choose the edit target.
2. If the record is already a draft, uses it as the edit target.
3. If it is published, rejects the edit; callers must first create a draft
   explicitly with `POST /records/:id/versions`.
4. For each new file on a draft, performs initialize, content upload, and
   commit against `/api/records/:id/draft/files`, as described for the
   draft-with-files route.

User records are required to determine whether the supplied ID is a draft or a
published record in the user's working view. A published record cannot be
modified in place and file-editing routes do not create a new version
automatically.

### `DELETE /user/records/:id/files`

1. Resolve the editable draft in the same way as the upload route: fetch the
   user record, use it directly if it is a draft, or reject the request if it
   is published.
2. Read the draft record ID and send
   `DELETE /api/records/:id/draft/files/:file-key`.

The lookup is required because only a draft's file collection is mutable.

## Details of other Routes

### `GET /access-token`

If there is no stored token, this route reports that directly and makes no
Zenodo request. If a token is present, it sends `GET /api/me` with a five-second
timeout. A `200` means the token is valid and a `401` means it is invalid. Other
request failures are also reported as an invalid token.

This call is needed because the presence of a locally stored token does not
prove that Zenodo still accepts it.

### `GET /auth/login`, `GET /auth/callback`, and `GET /auth/logout`

Login constructs a Zenodo `/oauth/authorize` URL and redirects the browser to
it. This is not a Zenodo API request made by the Jupyter server; the browser
performs the navigation so the user can authorize the extension.

After Zenodo redirects back, the callback exchanges the authorization code by
sending `POST /oauth/token`. This is needed to obtain the Bearer access token
used by authenticated API calls. The returned token is stored locally. Logout
only removes that local token; it does not call Zenodo to revoke it.

### `GET /me`

Send `GET /api/me` and return only `email` and `id`. The request identifies the
Zenodo account represented by the current token. Permission checks use the user
ID cached during authentication instead, as does upload-job scoping.

### `POST /records/:id/versions`

1. Send `POST /api/records/:id/versions` to create an unpublished next-version
   draft.
2. Read the returned draft ID and send
   `POST /api/records/:draft-id/draft/actions/files-import`.

Zenodo creates the version draft without files. The second call copies the
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
lets Zenodo allocate the file entry and provide canonical content and commit
links; uploading transfers the bytes; committing makes the upload available in
the draft. If cancellation occurs after initialization, the extension sends
`DELETE` for that draft file so an empty file entry is not left behind.

### Job routes

`GET /jobs`, `GET /jobs/:id`, and `POST /jobs/:id/cancel` primarily operate on
the extension's in-memory job manager. Record-file upload jobs are tagged and
filtered by the Zenodo user ID cached during authentication and by the current
environment; looking them up does not make a Zenodo API request.

Cancellation itself makes no immediate Zenodo request. If an upload notices
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

### Routes with no Zenodo traffic

- `GET /hello` returns a static local response.
- `GET /events` keeps a local server-sent event connection open.
- `GET /jobs` reads and filters local job progress; upload-job filters use the
  cached Zenodo user ID and environment.
- `GET /jobs/:id` reads local job progress.
- `POST /jobs/:id/cancel` sets a local cancellation flag (with the conditional
  upload cleanup noted above).
- `DELETE /files/download` deletes a local download.
- `POST /files/status` checks for a local download.
- `POST /files/import-cell` constructs a cell action for a local download.
- All methods on `/settings/downloads-directory` read or update local settings.
