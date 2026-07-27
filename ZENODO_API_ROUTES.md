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
API. There is no automatic fallback between the two except in the permission
and file/version flows described below.

### Drafts and published records

The extension uses `is_published` to choose a file-editing target:

- If `is_published` is false, the record is already a draft and is edited in
  place.
- If `is_published` is true, the published record is immutable. The extension
  rejects the file-editing request. A new-version draft must be created
  explicitly before its files can be changed.

Zenodo's published versions endpoint does not include an unpublished next
version. Consequently, the versions route combines the general versions API
with the user's record list to add an accessible draft.

For a single file lookup (e.g. for downloading files and constructing the local file location from the file metadata), the extension tries the draft file endpoint first and
falls back to the published file endpoint only on `403` or `404`. This lets one
code path handle both draft and published records without knowing the state in
advance.

TODO maybe cache/ propagate if file is from draft or published record

## Naming convention

Every Zenodo-facing operation uses the same verb, domain, resource, and
qualifier vocabulary across layers. Python uses `snake_case`, TypeScript uses
`camelCase`, and route handlers describe the REST resource and cardinality.
For example, `get_zenodo_record`, `getZenodoRecord`, and
`ZenodoRecordItemHandler` all describe the same operation.

The fixed verbs are `get`, `list`, `search`, `create`, `upload`, `delete`,
`open`, and `check`.

## Route summary

| Extension route                                       | Frontend call                                                | Zenodo traffic                                                                                  |
| ----------------------------------------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| `GET /hello`                                          | —                                                            | None                                                                                            |
| `GET /access-token`                                   | `useAccessTokenStatus`                                       | `GET /api/me` only when a stored token is present                                               |
| `GET /auth/login`                                     | `constructZenodoAuthUrl`                                     | Browser redirect to `/oauth/authorize`; no server-to-server API call                            |
| `GET /auth/callback`                                  | —                                                            | `POST /oauth/token`                                                                             |
| `GET /auth/logout`                                    | `constructZenodoAuthUrl`                                     | None; removes the locally stored token                                                          |
| `GET /records`                                        | `searchZenodoRecords`                                        | `GET /api/records`, optionally followed by one linked files request per hit                     |
| `GET /records/:id`                                    | `getZenodoRecord`                                            | `GET /api/records/:id`                                                                          |
| `GET /me`                                             | `getZenodoMe`                                                | `GET /api/me`                                                                                   |
| `GET /events`                                         | —                                                            | None; local server-sent event stream                                                            |
| `GET /user/records`                                   | `listZenodoUserRecords`                                      | `GET /api/user/records`, optionally followed by one linked files request per hit                |
| `GET /user/records/:id`                               | `getZenodoUserRecord`                                        | User-record search, followed by its linked files request if present                             |
| `GET /records/:id/permission`                         | `getZenodoRecordPermission`                                  | User-record lookup, `/api/me`, and sometimes general record details and/or linked access grants |
| `GET /records/:id/versions`                           | `listZenodoRecordVersions`                                   | General versions request plus a targeted user-record lookup or listing used to find a draft     |
| `POST /records/:id/versions`                          | `createZenodoRecordVersion`                                  | Create a new-version draft, then import the previous files                                      |
| `POST /user/records/draft-with-files`                 | `createZenodoRecordDraftWithFiles`                           | Create a draft, then initialize, upload, and commit every file                                  |
| `POST /user/records/:id/files`                        | `uploadZenodoRecordFiles`                                    | `/api/me`, require an editable draft, then upload every file                                    |
| `DELETE /user/records/:id/files`                      | `deleteZenodoRecordFile`                                     | Require an editable draft, then delete the named draft file                                     |
| `GET /jobs`                                           | `getLatestActiveJobId`                                       | Usually none; an upload-job query calls `/api/me` to scope jobs to the Zenodo account           |
| `GET /jobs/:id`                                       | `getJobProgress`                                             | None                                                                                            |
| `POST /jobs/:id/cancel`                               | `cancelJob`                                                  | None directly; cancellation cleanup can delete an initialized draft file                        |
| `POST /files/download`                                | `downloadZenodoFile`                                         | In the background: draft-first file metadata lookup and a streaming request to its link         |
| `DELETE /files/download`                              | `deleteZenodoFileDownload`                                   | Draft-first file metadata lookup, then local deletion                                           |
| `POST /files/status`                                  | `getZenodoFileDownloadStatus`                                | Draft-first file metadata lookup, then a local existence check                                  |
| `POST /files/import-cell`                             | `getZenodoFileImportCell`                                    | One draft-first file metadata lookup, then local cell construction                              |
| `GET`, `POST`, `DELETE /settings/downloads-directory` | `setZenodoDownloadDirectory`, `unsetZenodoDownloadDirectory` | None                                                                                            |

## Details of the most problematic Routes

Some routes are inherently complex because of how the Zenodo/ InvenioRDM API works:

- Retrieving info about the files on a record always requires an extra request per file, which is a lot
- There is no API endpoint that simply tells us the permissions the current user has for a specific record. Instead of only sending an authenticated request to the zenodo api, we need to know the user id beforehand (or request it again) and we need the details of the record to infer if the current user is the owner because if we have access because of that, we cannot see that in the access_grants response.
- Getting details for drafts and published records requires us to use two different endpoints, so if we want to make a call to the correct endpoint, we need to infer/cache/send from the client if a specific record is still in the draft stage or not. This is unneccessarily complex, so we usually just make two calls and get the details from the one that succeeds.

### `GET /records`

1. Send `GET /api/records` with `q`, `page`, `size`, `sort`, and `allversions`.
2. If the extension's `include_files` query flag is true, inspect every hit's
   `links.files` value and send `GET` to that link. Store the response in the
   record's `files` field.

The first request searches the general published record space. The optional
linked requests are needed because search hits do not reliably contain the
expanded file collection required by the UI. Following `links.files` also
avoids constructing a file-collection URL from assumptions about the record.

### `GET /records/:id`

Send `GET /api/records/:id` for general record details. Published record
details already contain the file collection, so no linked files request is
needed.

This route deliberately does not inspect `/api/user/records`; it represents the
general-record view.

### `GET /user/records`

1. Send `GET /api/user/records` with `page` and `size`.
2. If `include_files=true`, follow `links.files` for every returned record and
   add the result as `files`.

The user-record API is required here because general search cannot list the
authenticated user's unpublished drafts. File requests are optional because
they add one Zenodo call per result and are only needed by views that show file
details.

### `GET /user/records/:id`

1. Search `GET /api/user/records?q=id:<id>&size=10&allversions=true` and select
   the exact matching ID.
2. Follow the selected record's `links.files` URL, if present.

The first request resolves the record in the authenticated user's view, which
is what exposes draft state and owned records. The second request is especially
important for drafts because their file list is not included in the user-record
search result. The underlying request helper accepts `include_files=false` for
callers that only need record metadata; this route keeps the default value of
`true` because its frontend response includes files.

### `GET /records/:id/permission`

The route determines the current user's effective `view`, `preview`, `edit`, or
`manage` permission as follows:

1. Try to retrieve the ID from user records with
   `GET /api/user/records?...`. File expansion is disabled because permissions
   only require record metadata.
2. If no exact user-record hit is found, retrieve general details with
   `GET /api/records/:id`.
3. If the user-record request instead fails with `401` or `403`, meaning that the user is not logged in, return `view`
   immediately. Other HTTP errors are propagated.
4. Send `GET /api/me` and read the current user's ID.
5. If that ID occurs in the record's `owners`, return `manage` without querying
   access grants.
6. Otherwise, read `links.access_grants` from the record. If there is no such
   link, return `view`.
7. Send `GET` to `links.access_grants`. If that request returns `403`, return
   `view`; propagate other errors.
8. Keep grants whose subject is the current user and whose permission is one of
   `manage`, `edit`, `preview`, or `view`. Return the highest permission in that
   order, defaulting to `view`.

The record-detail and access-grant calls cannot be collapsed into only an
access-grant call:

- `access_grants` is a link returned in the record details. The extension
  follows that link instead of hard-coding an assumed endpoint.
  - TODO maybe hardcode link to access grants route so we do not need to read record details for that? but we need to do that anyway to find out if we are the owner
- The access-grants response can be empty when only the owner has access. It
  therefore cannot say whether the current user is the owner; the record's
  `owners` field is needed to infer `manage` rights.
- `/api/me` is needed to determine which owner or grant subject represents the
  current token. The server does not cache the zenodo user id right now.
  - TODO maybe cache user id serverside?

### `GET /records/:id/versions`

1. Send `GET /api/records/:id/versions` and take its published hits.
2. If there are no published hits, search
   `GET /api/user/records?q=id:<id>&size=10&allversions=true` and return the
   exact matching user record as the only version. Treat `401`, `403`, or `404`
   as no accessible record and return an empty list.
3. Otherwise, obtain the published hits' parent ID, which identifies the
   version family.
4. Send `GET /api/user/records?page=1&size=25&allversions=true`.
5. Keep draft records with the same parent ID. If more than one matches,
   select the one with the greatest `versions.index`.
6. Append that draft to the published versions, replacing a published hit with
   the same ID if necessary.

The general versions call is the authoritative list of published versions but
does not include drafts. The targeted user-record lookup handles a first-version
draft, for which there is no published hit from which to derive the parent ID.
The user-record listing supplies an editable next-version draft when published
versions already exist. A `401` or `403` from the user-record listing is
ignored, so callers without user-record access still get the published
versions. Other errors are propagated.

The user-record scan is currently limited to 25 records and is not filtered by
the target concept ID. A draft outside that page will be omitted; the code has
a TODO to replace this with a targeted or paginated lookup.

### `POST /user/records/:id/files`

Before starting the background job, the route sends `GET /api/me` to put the
Zenodo user ID and production/sandbox flag into the job metadata. This prevents
an upload job from one Zenodo account being mistaken for a job belonging to a
different account.

The background job then:

1. Resolves the record through `/api/user/records` without expanding its files.
   Only `is_published` is needed to choose the edit target.
2. If the record is already a draft, uses it as the edit target.
3. If it is published, rejects the edit; callers must first create a draft
   explicitly with `POST /records/:id/versions`.
4. For each new file on a draft, performs initialize, content upload, and
   commit against the editable draft, as described for the draft-with-files route.

User records are required to determine whether the supplied ID is an owned
draft or a published record. A published record cannot be modified in place
and file-editing routes do not create a new version automatically.

### `DELETE /user/records/:id/files`

1. Resolve the editable draft in the same way as the upload route: fetch the
   user record, use it directly if it is a draft, or reject the request if it
   is published.
2. Read `links.files` from that draft and send `DELETE links.files/:file-key`.

The lookup is required because only a draft's file collection is mutable. The
final request removes the named draft file.

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

Send `GET /api/me` and return only `email` and `id`. The request is needed to
identify the Zenodo account represented by the current token. The same profile
call is reused internally for permission checks and upload-job scoping.

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
2. Read the returned `links.files` value.
3. For each selected local file:
   1. Send `POST links.files` with the file key to initialize its entry.
   2. Send `PUT` to the returned `links.content` URL to stream the bytes.
   3. Send `POST` to the returned `links.commit` URL to finalize the file.

Draft creation is needed because files must belong to a record. Initialization
lets Zenodo allocate the file entry and provide canonical content and commit
links; uploading transfers the bytes; committing makes the upload available in
the draft. If cancellation occurs after initialization, the extension sends
`DELETE` for that draft file so an empty file entry is not left behind.

### Job routes

`GET /jobs`, `GET /jobs/:id`, and `POST /jobs/:id/cancel` primarily operate on
the extension's in-memory job manager. Looking up upload jobs is the exception:
`GET /jobs?job_type=upload...` sends `GET /api/me` so results can be filtered by
the current Zenodo account and environment.

Cancellation itself makes no immediate Zenodo request. If an upload notices
the cancellation after its file entry has been initialized, its cleanup path
deletes that entry from the draft.

### `POST /files/download`

The background download job:

1. Sends `GET /api/records/:id/draft/files/:file-key` for file metadata.
2. On `403` or `404`, sends `GET /api/records/:id/files/:file-key` instead.
3. Reads `links.download`, or `links.content` as a fallback, from the metadata.
4. Sends a streaming `GET` to that returned link and writes the bytes locally.

The draft-first lookup supports unpublished files while the fallback supports
published files and users who cannot access a draft. File metadata supplies
both a safe destination filename and Zenodo's canonical download URL. The
streaming request is the call that transfers the actual file contents.

### `DELETE /files/download`

This performs the same draft-first, published-fallback metadata lookup. The
metadata is needed to reconstruct the sanitized local path. The route then
deletes only the local copy; it does not delete the file from Zenodo.

### `POST /files/status`

This performs the same draft-first, published-fallback metadata lookup and uses
the returned filename to test whether the corresponding local file exists. It
does not download any content.

### `POST /files/import-cell`

This performs one draft-first, published-fallback file metadata lookup. The
same metadata response is used both to calculate the expected local download
path and to construct the generated cell. The route then checks that the local
file exists and constructs the Jupyter code-cell action locally.

### Routes with no Zenodo traffic

- `GET /hello` returns a static local response.
- `GET /events` keeps a local server-sent event connection open.
- `GET /jobs/:id` reads local job progress.
- `POST /jobs/:id/cancel` sets a local cancellation flag (with the conditional
  upload cleanup noted above).
- All methods on `/settings/downloads-directory` read or update local settings.
