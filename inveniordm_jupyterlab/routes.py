from jupyter_server.utils import url_path_join

from inveniordm_auth.remote_servers import RemoteServerRegistry
from inveniordm_jupyterlab.user_settings import (
    InvenioRDMUserSettings,
    InvenioRDMUserSettingsFromFile,
)
from inveniordm_jupyterlab.util.job_manager import JobManager
from inveniordm_jupyterlab.util.sse import EventBus

from .handlers import (
    APIHandler,
    HelloRouteHandler,
    InvenioRDMAccessTokenHandler,
    InvenioRDMAuthHandler,
    InvenioRDMCurrentRemoteServerHandler,
    InvenioRDMDownloadLocationSettingHandler,
    InvenioRDMEventsHandler,
    InvenioRDMFileDownloadHandler,
    InvenioRDMFileDownloadStatusHandler,
    InvenioRDMFileImportCellHandler,
    InvenioRDMMeHandler,
    InvenioRDMRecordCollectionHandler,
    InvenioRDMRecordDraftWithFilesHandler,
    InvenioRDMRecordFileCollectionHandler,
    InvenioRDMRecordPermissionHandler,
    InvenioRDMRecordVariantItemHandler,
    InvenioRDMRecordVersionCollectionHandler,
    InvenioRDMRemoteServersDefaultHandler,
    InvenioRDMRemoteServersHandler,
    InvenioRDMUserRecordCollectionHandler,
    InvenioRDMUserRecordItemHandler,
    JobCancelHandler,
    JobProgressHandler,
    JobsHandler,
)
from .handlers.base import contents_root
from .inveniordm_download_manager import InvenioRDMDownloadManager
from .inveniordm_requests.inveniordm_requests import InvenioRDMRequests
from .inveniordm_requests.inveniordm_requests_factory_create import (
    create_inveniordm_requests_factory,
)


def setup_route_handlers(
    web_app,
    remote_servers: RemoteServerRegistry,
    request_mode: str,
):
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    event_bus = EventBus()
    job_manager = JobManager()
    inveniordm_requests_factory = create_inveniordm_requests_factory(
        remote_servers,
        request_mode,
    )

    def get_inveniordm_requests(handler: APIHandler) -> InvenioRDMRequests:
        return inveniordm_requests_factory.create_inveniordm_requests(handler)

    def create_job_metadata(
        inveniordm_requests: InvenioRDMRequests,
    ) -> dict[str, object]:
        return {
            "inveniordm_user_id": inveniordm_requests.inveniordm_user_id,
            "remote_server_id": inveniordm_requests_factory.get_remote_server_id(
                inveniordm_requests
            ),
        }

    def get_user_settings(handler: APIHandler) -> InvenioRDMUserSettings:
        return InvenioRDMUserSettingsFromFile(contents_root(handler))

    def get_inveniordm_download_manager(
        handler: APIHandler,
    ) -> InvenioRDMDownloadManager:
        settings = get_user_settings(handler)
        inveniordm_requests = get_inveniordm_requests(handler)
        return InvenioRDMDownloadManager(
            settings.get_downloads_directory(),
            remote_server_id=inveniordm_requests_factory.get_remote_server_id(
                inveniordm_requests
            ),
            job_manager=job_manager,
        )

    def get_job_manager(handler: APIHandler) -> JobManager:
        return job_manager

    inveniordm_base_url = url_path_join(base_url, "inveniordm-jupyterlab")
    handlers = [
        (url_path_join(inveniordm_base_url, "hello"), HelloRouteHandler),
        (
            url_path_join(inveniordm_base_url, "access-token"),
            InvenioRDMAccessTokenHandler,
            {"inveniordm_requests_factory": inveniordm_requests_factory},
        ),
        (
            url_path_join(inveniordm_base_url, "remote-servers"),
            InvenioRDMRemoteServersHandler,
            {"remote_servers": remote_servers, "request_mode": request_mode},
        ),
        (
            url_path_join(inveniordm_base_url, "remote-servers", "default"),
            InvenioRDMRemoteServersDefaultHandler,
            {"remote_servers": remote_servers, "request_mode": request_mode},
        ),
        (
            url_path_join(inveniordm_base_url, "remote-servers", "current"),
            InvenioRDMCurrentRemoteServerHandler,
            {"inveniordm_requests_factory": inveniordm_requests_factory},
        ),
        (
            url_path_join(inveniordm_base_url, "auth", r"(login|logout|callback)"),
            InvenioRDMAuthHandler,
            {"inveniordm_auth_controller": inveniordm_requests_factory.auth_controller},
        ),
        (
            url_path_join(inveniordm_base_url, "records"),
            InvenioRDMRecordCollectionHandler,
            {"get_inveniordm_requests": get_inveniordm_requests},
        ),
        (
            url_path_join(inveniordm_base_url, "record-variants", r"([^/]+)"),
            InvenioRDMRecordVariantItemHandler,
            {"get_inveniordm_requests": get_inveniordm_requests},
        ),
        (
            url_path_join(inveniordm_base_url, "me"),
            InvenioRDMMeHandler,
            {"get_inveniordm_requests": get_inveniordm_requests},
        ),
        (
            url_path_join(inveniordm_base_url, "events"),
            InvenioRDMEventsHandler,
            {"event_bus": event_bus},
        ),
        (
            url_path_join(inveniordm_base_url, "user", "records"),
            InvenioRDMUserRecordCollectionHandler,
            {"get_inveniordm_requests": get_inveniordm_requests},
        ),
        (
            url_path_join(
                inveniordm_base_url,
                "user",
                "records",
                "draft-with-files",
            ),
            InvenioRDMRecordDraftWithFilesHandler,
            {
                "get_inveniordm_requests": get_inveniordm_requests,
                "get_job_manager": get_job_manager,
                "event_bus": event_bus,
            },
        ),
        (
            url_path_join(
                inveniordm_base_url,
                "records",
                r"([^/]+)",
                "versions",
            ),
            InvenioRDMRecordVersionCollectionHandler,
            {
                "get_inveniordm_requests": get_inveniordm_requests,
                "event_bus": event_bus,
            },
        ),
        (
            url_path_join(
                inveniordm_base_url,
                "records",
                r"([^/]+)",
                "permission",
            ),
            InvenioRDMRecordPermissionHandler,
            {"get_inveniordm_requests": get_inveniordm_requests},
        ),
        (
            url_path_join(inveniordm_base_url, "user", "records", r"([^/]+)"),
            InvenioRDMUserRecordItemHandler,
            {
                "get_inveniordm_requests": get_inveniordm_requests,
                "event_bus": event_bus,
            },
        ),
        (
            url_path_join(
                inveniordm_base_url,
                "user",
                "records",
                r"([^/]+)",
                "files",
            ),
            InvenioRDMRecordFileCollectionHandler,
            {
                "get_inveniordm_requests": get_inveniordm_requests,
                "get_job_manager": get_job_manager,
                "create_job_metadata": create_job_metadata,
                "event_bus": event_bus,
            },
        ),
        (
            url_path_join(inveniordm_base_url, "jobs"),
            JobsHandler,
            {
                "get_job_manager": get_job_manager,
                "get_inveniordm_requests": get_inveniordm_requests,
                "create_job_metadata": create_job_metadata,
            },
        ),
        (
            url_path_join(
                inveniordm_base_url,
                "jobs",
                r"([^/]+)",
                "cancel",
            ),
            JobCancelHandler,
            {"get_job_manager": get_job_manager},
        ),
        (
            url_path_join(inveniordm_base_url, "jobs", r"([^/]+)"),
            JobProgressHandler,
            {"get_job_manager": get_job_manager},
        ),
        (
            url_path_join(inveniordm_base_url, "files", "download"),
            InvenioRDMFileDownloadHandler,
            {
                "get_inveniordm_requests": get_inveniordm_requests,
                "get_inveniordm_download_manager": get_inveniordm_download_manager,
                "event_bus": event_bus,
            },
        ),
        (
            url_path_join(inveniordm_base_url, "files", "status"),
            InvenioRDMFileDownloadStatusHandler,
            {
                "get_inveniordm_requests": get_inveniordm_requests,
                "get_inveniordm_download_manager": get_inveniordm_download_manager,
            },
        ),
        (
            url_path_join(inveniordm_base_url, "files", "import-cell"),
            InvenioRDMFileImportCellHandler,
            {
                "get_inveniordm_requests": get_inveniordm_requests,
                "get_inveniordm_download_manager": get_inveniordm_download_manager,
            },
        ),
        (
            url_path_join(inveniordm_base_url, "settings", "downloads-directory"),
            InvenioRDMDownloadLocationSettingHandler,
            {"get_user_settings": get_user_settings},
        ),
    ]

    web_app.add_handlers(host_pattern, handlers)
