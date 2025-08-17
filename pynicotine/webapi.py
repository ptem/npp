#This is just a random text

from pynicotine import slskmessages
from pynicotine.events import events
from pynicotine.config import config
from pynicotine.logfacility import log
from pynicotine.core import core
from pynicotine.slskmessages import FileListMessage
from pynicotine.core import core
from pynicotine.logfacility import log
from pynicotine.transfers import TransferStatus
from pynicotine.webapi_models import WebApiSearchResult, FileDownloadedNotification, WebApiSearchModel, FileToDownload, TransferModel

from threading import Thread
import pathlib
from difflib import SequenceMatcher
import requests
from fastapi import FastAPI
import uvicorn
import time
import asyncio

class AsyncUvicorn:

    exception_caught = False
    
    def __init__(self, local_ip: str, local_port: int):
        uvicorn_config = uvicorn.Config(app, local_ip, local_port)
        self.server = uvicorn.Server(uvicorn_config)
        self.thread = Thread(name="WebApiThread", daemon=True, target=self.__run_server)

    def __run_server(self): 
        try:
            if not self.server.started:
                self.server.run()
        except SystemExit:
            print("Error while starting the Web API server.")
            time.sleep(5)
            self.__run_server()

    def start(self):
            self.thread.start()

    def stop(self):
        if self.thread.is_alive():
            self.server.should_exit = True
            while self.thread.is_alive():
                continue
    
    def thread_excepthook(args):
        print(f"EXCEPTION! {args[1]}")

    excepthook = thread_excepthook

#####################
# WEB API COMPONENT #
#####################

class WebApiComponent:

    def __init__(self):

        self.api_server = None
        self.active_searches = {}
        self.session = requests.Session()

        for event_name, callback in (
            ("quit", self._quit),
            ("start", self._start),
            ("file-search-response", self._file_search_response),
            # ("download-notification", self._download_notification),
            # ("download-notification-web-api", self._download_notification_web_api)
        ):
            events.connect(event_name, callback)

    def _start(self):

        if config.sections["web_api"]["enable"]:
            log.add(f"Web API loaded")
            
            try:
                self.api_server = AsyncUvicorn(config.sections["web_api"]["local_ip"], config.sections["web_api"]["local_port"])
                self.api_server.start()

            except Exception as error:
                print(f"Exception when starting the Web API Server: {error}")
                self.api_server.stop()

    def _quit(self):
        
        print("Stop the WebAPI")
        if self.api_server is not None:
            self.api_server.stop()
    
    def _parse_search_response(self, msg, search):

            def get_string_similarity(a, b):
                return SequenceMatcher(None, a, b).ratio()

            items_to_return = []

            for _code, file_path, size, _ext, file_attributes, *_unused in msg.list:
                file_path_split = file_path.split("\\")
                file_path_split = reversed(file_path_split)
                file_name = next(file_path_split)
                file_extension = pathlib.Path(file_name).suffix[1:]
                h_quality, bitrate, h_length, length = FileListMessage.parse_audio_quality_length(size, file_attributes)
                if msg.freeulslots:
                    inqueue = 0
                else:
                    inqueue = msg.inqueue or 1  # Ensure value is always >= 1
                search_similarity = get_string_similarity(search.term, file_name)

                item = WebApiSearchResult(
                                        user = msg.username,
                                        ip_address = msg.addr[0],
                                        port = msg.addr[1],
                                        has_free_slots = msg.freeulslots,
                                        inqueue = inqueue,
                                        ulspeed = msg.ulspeed or 0, 
                                        file_name = file_name,
                                        file_extension=file_extension,
                                        file_path = file_path,
                                        file_size = size,
                                        file_h_length = h_length,
                                        bitrate = bitrate,
                                        search_similarity = search_similarity,
                                        file_attributes=file_attributes
                                    )

                items_to_return.append(item)
            
            return items_to_return
                
    def _file_search_response(self, msg):

        if msg.token not in slskmessages.SEARCH_TOKENS_ALLOWED:
            msg.token = None
            return

        search_req = core.search.searches.get(msg.token)
        if search_req:
            if not hasattr(search_req,"results"):
                search_req.results = []
            
            for item in self._parse_search_response(msg, search_req):
                search_req.results.append(item)
                

    def _download_notification(self, status=None):
        if status:
            print("Download finished")
        else:
            print("Download just started")

    def _download_notification_web_api(self, username, virtual_path, download_file_path):
        
        file = FileDownloadedNotification(user=username, virtual_file_path=virtual_path, file_download_path=download_file_path)
        print(f"Download finished in: {download_file_path}")
        data = file.model_dump()
        response = self.session.post(f'http://{config.sections["web_api"]["remote_ip"]}:{config.sections["web_api"]["remote_port"]}/download/notification', json=data)

##########################
# WEB API IMPLEMENTATION #
##########################
app = FastAPI()

@app.get("/foo")
async def root():
    return {"message": "Hello World"}

@app.get("/search/global")
async def do_web_api_global_search(search: WebApiSearchModel):

    max_simultaneous_searches = config.sections["web_api"]["max_simultaneous_searches"]
    if len(core.search.searches) < max_simultaneous_searches:
        search_token = core.search.do_search(search.search_term, mode="global")
        await asyncio.sleep(search.wait_for_seconds)
        search_req = core.search.searches.get(search_token)
        if search_req:
            search_req.is_ignored = True
        core.search.remove_search(search_token)
        
        if not hasattr(search_req,"results"):
            return "No results found. Please, try with another search string."
        else:
            return search_req
    else:
        return "Too many simultaneous searches. Please, try again later."


@app.get("/download")
async def download_file(file: FileToDownload):

    core.downloads.enqueue_download(file.file_owner, file.file_virtual_path, folder_path=None, size=file.file_size, file_attributes=file.file_attributes)
    return f"Download enqueued: {file.file_virtual_path}"

@app.get("/download/getdownloads")
async def get_dowloads():

    core_transfers = core.downloads.get_transfer_list()
    list_to_send = []
    for transfer in core_transfers:
        list_to_send.append(TransferModel(
                                username=transfer.username, 
                                virtual_path=transfer.virtual_path,
                                download_path=transfer.folder_path,
                                status=transfer.status,
                                size=transfer.size,
                                current_byte_offset=transfer.current_byte_offset,
                                download_percentage=f"{transfer.current_byte_offset*100/transfer.size:.2f}%" if transfer.current_byte_offset else "0%",
                                file_attributes=transfer.file_attributes))
    return list_to_send

@app.delete("/download/abortandclean")
async def abort_and_clean_all_downloads():
    core.downloads.clear_downloads(statuses=[TransferStatus.FINISHED, TransferStatus.CANCELLED])
    return "All downloads will be aborted and cleaned"

'''
    Data needed for a download:

                "user") => 'merciero23'
                "file_path_data") => '@@xpgbc\\TEMAS COMPARTIDOS 2\\mp3\\4635732_Love___Happiness__Yemaya___Ochun__Feat__India_David_Penn_Vocal_Mix.mp3'
                "size_data") => 18527131
                "file_attributes_data") => 
'''
