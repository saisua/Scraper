print("Starting Interceptor imports  ")
import sys
import socket
import io
import typing
from multiprocessing import Manager, Process, RLock, Condition
import re
from re import search, sub
from os import getcwd
from operator import sub as subtract
from random import choice, randint

import pyshark
import pem
import mitmproxy
from pyshark.capture.capture import Capture
from pyshark.capture.live_capture import LiveCapture
from pyshark.packet.packet import Packet
from mitmproxy import proxy, options, http
from mitmproxy.net.http.request import Request
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.addons import core
from click import echo
from ctypes import c_bool, c_char_p
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

from Structures.Async_generator import AGenerator
from Settings.Identity import Identity

### TESTS
from PIL import Image
from difflib import SequenceMatcher 


print("Done (Interceptor)")

class Interceptor():
    stdout = sys.stdout
    key_dir = f"{'//'.join(__file__.split('/')[:-1])}//.mitmproxy//mitmproxy-ca.pem"

    async_gen:AGenerator
    non_realtime:Process=None
    __open:bool
    active:bool

    _manager:Manager

    ip:str
    port:int

    __capture:LiveCapture

    identity_script:str

    ### TESTS
    video_num:int = 0
    lock:Condition
    video_saved:int = 1
    video_strips:list
    video:bytearray

    video_check_num:int = 2
    video_check:list = []
    video_s_check:list

    def __init__(self, manager:Manager=None, *, ip:str='127.0.0.1', port:int=None,
                        process_non_realtime:bool=False, non_realtime_capture_filter:str='',
                        non_realtime_interface:str='any'):
        self.new_identity()


        self._manager = manager or Manager()

        self.async_gen = AGenerator()


        self.__open = self._manager.Value(c_bool, True)
        self.active = self._manager.Value(c_bool, True)

        self.ip = ip
        self.port = port or Interceptor.__get_open_port(ip)

        ### TESTS
        if(True):
            Interceptor.lock = self._manager.Condition(self._manager.RLock())
            Interceptor.video = self._manager.Value('b', b"")
            Interceptor.video_strips = self._manager.list()
        ### TESTS END

        if(process_non_realtime):
            #self.key = generate_private_key(65537, 2048, default_backend())
            #print(dir(self.key))
            with open(Interceptor.key_dir, "rb") as key_file:
                self.key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                    backend=default_backend()
                    )

            #print(len(self.key.private_bytes()))

            self.start_pyshark_capture(non_realtime_capture_filter, non_realtime_interface)

            self.non_realtime = Process(target=self.non_realtime_process)
            self.non_realtime.start()

        opts = options.Options(
                listen_host=self.ip, mode="socks5",
                listen_port=self.port,
                confdir=f"{'//'.join(__file__.split('/')[:-1])}//.mitmproxy"
                )
        opts.add_option("body_size_limit", int, 0, "")
        opts.add_option("keep_host_header", bool, True, "")
        opts.add_option("showhost", bool, True, "")
        #opts.add_option("client_certs", str, Interceptor.key_dir, "")
        #opts.add_option("keep_host_header")


        pconf = proxy.config.ProxyConfig(opts)

        self.proxy = DumpMaster(opts, with_termlog=False, with_dumper=False)
        self.proxy.server = proxy.server.ProxyServer(pconf)
        self.proxy.addons.add(self)

        self.proxy_process = Process(target=self.proxy.run, daemon=True)
        self.proxy_process.start()

        ### TESTS
        #open(f".//Results//Videos//video.mp4", "wb")


    def close(self):
        self.__open.value = False
        
        self.proxy.shutdown()

        self.proxy_process.terminate()
        self.proxy_process.join(3)

        
        if(not self.non_realtime is None):
            self.__capture.close()

            # No terminate to ensure tshark is closed
            self.non_realtime.join(5)

        self.async_gen(all=True)

        ### TESTS
        #Interceptor.video_check.join()

        try:
            if(len(Interceptor.video.value)):
                print("Storing video data... ", end='')
                with open(f"{'//'.join(__file__.split('/')[:-1])}//..//Results//Videos//video.mp4", "wb") as file:
                    file.write(Interceptor.video.value)

                with open(f"{'//'.join(__file__.split('/')[:-1])}//..//Results//Videos//video.dat", "w") as file:
                    file.write('\n'.join(map(str, Interceptor.video_strips)))

                print("DONE")
        except:
            pass

    def request(self, flow:http.HTTPFlow):
        """
            The full HTTP request has been read.
        """

        #echo("request", file=self.stdout)
        #echo(f"request {flow.client_conn.address} -> {flow.server_conn.address}", file=self.stdout)

        if(self.active.value):
            pass

            #content = flow.request.headers.get("content-type","")
            #echo(content, file=Interceptor.stdout)

            #echo(flow.request.url, file=Interceptor.stdout)

    def response(self, flow:http.HTTPFlow):
        """
            The full HTTP response has been read.
        """
        
        #echo("response", file=self.stdout)
        echo(f"response {flow.response.headers.get('content-type','')}", file=self.stdout)
        #echo(f"response {flow.server_conn.address} -> {flow.client_conn.address}", file=self.stdout)

        #flow.intercept()
        #flow.resume()

        if(self.active.value):
            pass
            #if('text/html' in flow.response.headers.get("content-type")):
            #    b = flow.response.content.find(b"<body")
            #    if(b >= 0):
            #        index = flow.response.content.find(b"<script", start=b)
                    
            #        flow.response.content = (flow.response.content[:index] +
            #                                self.identity_script +
            #                                flow.response.content[index:])
                    

            #content = flow.response.headers.get("content-type","")
            #print(content)

            #if(content.startswith("image")):
                #self.images+=1
                #self.async_gen.append(Interceptor.save_image(flow.response.raw_content, self.images, content))

            #if(flow.response.headers.get("content-type","").startswith("video")):
                #Interceptor.video_num += 1
                #self.async_gen.append(Interceptor.save_video(flow.response.raw_content, Interceptor.video_num))
            
    def http_connect(self, flow: mitmproxy.http.HTTPFlow):
        """
            An HTTP CONNECT request was received. Setting a non 2xx response on
            the flow will return the response to the client abort the
            connection. CONNECT requests and responses do not generate the usual
            HTTP handler events. CONNECT requests are only valid in regular and
            upstream proxy modes.
        """

    def requestheaders(self, flow: mitmproxy.http.HTTPFlow):
        """
            HTTP request headers were successfully read. At this point, the body
            is empty.
        """

    def responseheaders(self, flow: mitmproxy.http.HTTPFlow):
        """
            HTTP response headers were successfully read. At this point, the body
            is empty.
        """

    def error(self, flow: mitmproxy.http.HTTPFlow):
        """
            An HTTP error has occurred, e.g. invalid server responses, or
            interrupted connections. This is distinct from a valid server HTTP
            error response, which is simply a response with an HTTP error code.
        """

    def tcp_start(self, flow: mitmproxy.tcp.TCPFlow):
        """
            A TCP connection has started.
        """

    def tcp_message(self, flow: mitmproxy.tcp.TCPFlow):
        """
            A TCP connection has received a message. The most recent message
            will be flow.messages[-1]. The message is user-modifiable.
        """
        echo("tcp_message", file=Interceptor.stdout)

    def tcp_error(self, flow: mitmproxy.tcp.TCPFlow):
        """
            A TCP error has occurred.
        """

    def tcp_end(self, flow: mitmproxy.tcp.TCPFlow):
        """
            A TCP connection has ended.
        """

    def websocket_handshake(self, flow: mitmproxy.http.HTTPFlow):
        """
            Called when a client wants to establish a WebSocket connection. The
            WebSocket-specific headers can be manipulated to alter the
            handshake. The flow object is guaranteed to have a non-None request
            attribute.
        """

    def websocket_start(self, flow: mitmproxy.websocket.WebSocketFlow):
        """
            A websocket connection has commenced.
        """

    def websocket_message(self, flow: mitmproxy.websocket.WebSocketFlow):
        """
            Called when a WebSocket message is received from the client or
            server. The most recent message will be flow.messages[-1]. The
            message is user-modifiable. Currently there are two types of
            messages, corresponding to the BINARY and TEXT frame types.
        """
        echo("websocket_message", file=Interceptor.stdout)

    def websocket_error(self, flow: mitmproxy.websocket.WebSocketFlow):
        """
            A websocket connection has had an error.
        """

    def websocket_end(self, flow: mitmproxy.websocket.WebSocketFlow):
        """
            A websocket connection has ended.
        """

    def clientconnect(self, layer: mitmproxy.proxy.protocol.Layer):
        """
            A client has connected to mitmproxy. Note that a connection can
            correspond to multiple HTTP requests.
        """

    def clientdisconnect(self, layer: mitmproxy.proxy.protocol.Layer):
        """
            A client has disconnected from mitmproxy.
        """

    def serverconnect(self, conn: mitmproxy.connections.ServerConnection):
        """
            Mitmproxy has connected to a server. Note that a connection can
            correspond to multiple requests.
        """

    def serverdisconnect(self, conn: mitmproxy.connections.ServerConnection):
        """
            Mitmproxy has disconnected from a server.
        """

    def next_layer(self, layer: mitmproxy.proxy.protocol.Layer):
        """
            Network layers are being switched. You may change which layer will
            be used by returning a new layer object from this event.
        """

    # General lifecycle
    def configure(self, updated: typing.Set[str]):
        """
            Called when configuration changes. The updated argument is a
            set-like object containing the keys of all changed options. This
            event is called during startup with all options in the updated set.
        """

    def done(self):
        """
            Called when the addon shuts down, either by being removed from
            the mitmproxy instance, or when mitmproxy itself shuts down. On
            shutdown, this event is called after the event loop is
            terminated, guaranteeing that it will be the final event an addon
            sees. Note that log handlers are shut down at this point, so
            calls to log functions will produce no output.
        """

    def load(self, entry: mitmproxy.addonmanager.Loader):
        """
            Called when an addon is first loaded. This event receives a Loader
            object, which contains methods for adding options and commands. This
            method is where the addon configures itself.
        """

    def log(self, entry: mitmproxy.log.LogEntry):
        """
            Called whenever a new log entry is created through the mitmproxy
            context. Be careful not to log from this event, which will cause an
            infinite loop!
        """

    def running(self):
        """
            Called when the proxy is completely up and running. At this point,
            you can expect the proxy to be bound to a port, and all addons to be
            loaded.
        """
        echo(f"The interceptor is up and running in {self.ip}:{self.port}", file=self.stdout)

    def update(self, flows: typing.Sequence[mitmproxy.flow.Flow]):
        """
            Update is called when one or more flow objects have been modified,
            usually from a different addon.
        """


    def start_pyshark_capture(self, capture_filter:str='', interface:str='any'):
        with open(f"{'//'.join(__file__.split('/')[:-1])}//.mitmproxy//ssl.key", "wb") as file:
            #file.write(self.key.private_bytes())
            file.write(pem.parse_file(Interceptor.key_dir)[0].as_bytes())

        # Custom parameters got from https://github.com/eaufavor/pyshark-ssl
        self.__capture = Closable_LCapture(interface="lo",#interface,
            #bpf_filter=capture_filter,#sub(r"port \d*", capture_filter, f"port {self.port}"),
            display_filter = "ssl",
            custom_parameters = ['-o', 'ssl.desegment_ssl_records:TRUE', 
                            '-o', 'ssl.desegment_ssl_application_data:TRUE',
                            '-o','tcp.desegment_tcp_streams:TRUE', 
                            '-o', f"ssl.keylog_file:{'//'.join(__file__.split('/')[:-1])}//.mitmproxy//ssl.key"]
            #decryption_key=(pem.parse_file())[0].as_text()
        )

    def non_realtime_process(self):
        print("Enabled non-realtime packet process in Interceptor")

        def print_packet(packet:Packet):
            pass
            tmp_var = packet.ssl.get("app_data", None)

            if(tmp_var):
                #echo(tmp_var.binary_value.decode("utf-8")[:30], file=self.stdout)
                #UnicodeDecodeError
                echo(self.key.decrypt(
                        tmp_var.binary_value,
                        padding.OAEP(
                            mgf=padding.MGF1(algorithm=hashes.SHA256()),
                            algorithm=hashes.SHA256(),
                            label=None
                        )
                    ).decode("utf-8")[:30], file=self.stdout)
                echo('', file=Interceptor.stdout)
            #echo(dir(packet.ssl.get("app_data", b'')), file=self.stdout)
            #echo(f"{packet.ip.src} -> {packet.ip.dst}", file=self.stdout)

        #capture.set_debug(True)
        self.__capture.apply_on_packets(print_packet)

    # Auxiliar

    def new_identity(self):
        self.identity_script = "<script type='text/javascript'>\n"

        for obj, param, value in Identity.identity():
            self.identity_script += (
                f"Object.defineProperty({obj}, '{param}',"+
                        "{get: function () { "+
                            (f"return '{value}';" if type(value) is str else f"return {value};")+
                        "}});\n"
             )

        self.identity_script = bytes(f"{self.identity_script}\n</script>\n", "utf-8")
        #print(self.identity_script)

    def aux_video(self, pos:int, proc_num:int):
        raise NotImplementedError

        from time import sleep

        while(Interceptor.video_check_num > len(Interceptor.video_strips)): 
            if(self.__open.value):
                sleep(.5)
            else:
                return

        while(True):
            if(not pos):
                echo(f"CHECK video {Interceptor.video_check_num}", file=Interceptor.stdout)

            #echo(f"1", file=Interceptor.stdout)
            raw = Interceptor.video.value[Interceptor.video_strips[Interceptor.video_check_num-2]:Interceptor.video_strips[Interceptor.video_check_num-1]]
            raw = raw[len(raw)//3:len(raw)-len(raw)//3]

            #echo(f"2", file=Interceptor.stdout)
            video = Interceptor.video.value[:Interceptor.video_strips[Interceptor.video_check_num-2]]
            video = video[len(video)//proc_num*pos:len(video)//proc_num*(pos+1)]

            #echo(f"3", file=Interceptor.stdout)
            video_check = (3* -len(raw) + len(video))
            Interceptor.video_s_check.value += str(len(SequenceMatcher(None, raw, video)
                    .find_longest_match(0, len(raw), 
                            0 if video_check < 0 else video_check, 
                            len(video)))) + ","

            #echo(f"4", file=Interceptor.stdout)
            if(Interceptor.video_s_check.value.count(',') == proc_num):
                echo(f"TEST{pos} 1", file=Interceptor.stdout)
                if(sum(tuple(map(int, Interceptor.video_s_check.value[:-1].split(',')))) > len(raw)//4):
                    Interceptor.video.value = (
                        Interceptor.video.value[:Interceptor.video_strips[Interceptor.video_check_num-2]]
                        +
                        Interceptor.video.value[Interceptor.video_strips[Interceptor.video_check_num-1]:]
                    )
                    echo(f"DISCARDED video {Interceptor.video_check_num}", file=Interceptor.stdout)
                else:
                    echo(f"ACCEPTED video {Interceptor.video_check_num}", file=Interceptor.stdout)

                Interceptor.video_check_num += 1
                Interceptor.video_s_check.value = ""
                echo(f"TEST{pos} 2", file=Interceptor.stdout)

            echo(f"SPLIT{pos} video {Interceptor.video_check_num} {Interceptor.video_s_check.value}", file=Interceptor.stdout)

            while(len(Interceptor.video_s_check.value) or Interceptor.video_check_num > len(Interceptor.video_strips)): 
                if(self.__open.value):
                    sleep(.5)
                else:
                    return

    @staticmethod
    async def save_video(raw:bytes, num):
        echo(f"GOT video {num}/{Interceptor.video_saved}", file=Interceptor.stdout)
        Interceptor.lock.wait_for(lambda: Interceptor.video_saved == num)
        #echo(f"IN video {num}", file=Interceptor.stdout)

        Interceptor.video.value += raw
        Interceptor.video_strips.append(len(Interceptor.video.value))
        
        echo(f"DONE video {num}", file=Interceptor.stdout)
        Interceptor.video_saved += 1
        Interceptor.lock.notify_all()
        #echo("DONE\r", nl=False, file=Interceptor.stdout)

    # Properties

    @property
    def address(self) -> str:
        return f"{self.ip}:{self.port}"

    # Static methods

    @staticmethod
    async def save_image(data:bytes, image_num:int, content:str):
        image = Image.open(io.BytesIO(data))
        extension = search(r'[\/](.+)[;?]',content).group(1)

        #echo(f"image{image_num}.{f}", file=Sniffer_event.stdout)
        image.save(f".//Results//Images//image{image_num}.{extension}")

    @staticmethod
    def keys_lower(data:tuple) -> tuple:
        return (data[0].lower(), data[1])

    @staticmethod 
    def __get_open_port(ip:str) -> int:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((ip, 0))
        p = s.getsockname()[1]
        s.close()
        return p


class Closable_LCapture(LiveCapture):
    from asyncio.subprocess import Process as AProcess
    import asyncio

    lcapture_tshark:AProcess=None

    def __init__(self, *args, **kwargs):
        self.is_open = Manager().Value(c_bool, True)

        super().__init__(*args, **kwargs)

    def sniff_continuously(self, packet_count=None):
        """
        Captures from the set interface, returning a generator which returns packets continuously.

        Can be used as follows:
        for packet in capture.sniff_continuously():
            print 'Woo, another packet:', packet

        Note: you can also call capture.apply_on_packets(packet_callback) which should have a slight performance boost.

        :param packet_count: an amount of packets to capture, then stop.
        """
        
        self.lcapture_tshark = (self.lcapture_tshark or 
                self.eventloop.run_until_complete(self._get_tshark_process()))

        self._running_processes.add(self.lcapture_tshark)

        # Retained for backwards compatibility and to add documentation.
        return self._packets_from_tshark_sync(packet_count=packet_count, 
                                            tshark_process=self.lcapture_tshark)

    def _packets_from_tshark_sync(self, tshark_process, packet_count=None, timeout:float=3.0,
                                    max_data_length:int=10000):
        """
        Returns a generator of packets.
        This is the sync version of packets_from_tshark. It wait for the completion of each coroutine and
         reimplements reading packets in a sync way, yielding each packet as it arrives.

        :param packet_count: If given, stops after this amount of packets is captured.
        """
        # NOTE: This has code duplication with the async version, think about how to solve this

        psml_structure, data = self.eventloop.run_until_complete(self._get_psml_struct(tshark_process.stdout))
        packets_captured = 0

        data = b""
        try:
            while self.is_open.value:
                try:
                    packet, data = self.eventloop.run_until_complete(
                        self._get_packet_from_stream(tshark_process.stdout, 
                                                    data,
                                                    psml_structure=psml_structure,
                                                    got_first_packet=packets_captured > 0, 
                                                    timeout=timeout))
                except EOFError:
                    echo("Caught EOF", file=Interceptor.stdout)
                    self._log.debug("EOF reached (sync)")
                    break

                if(packet is False): continue

                if packet:
                    packets_captured += 1
                    yield packet
                if packet_count and packets_captured >= packet_count:
                    break
                if len(data) > max_data_length:
                    data = b''
        finally:
            if tshark_process in self._running_processes:
                self.eventloop.run_until_complete(self._cleanup_subprocess(tshark_process))

    async def _get_packet_from_stream(self, stream, existing_data, 
                                            got_first_packet=True, 
                                            psml_structure=None,
                                            timeout:float=3.0):
        """A coroutine which returns a single packet if it can be read from the given StreamReader.

        :return a tuple of (packet, remaining_data). The packet will be None if there was not enough XML data to create
        a packet. remaining_data is the leftover data which was not enough to create a packet from.
        :raises EOFError if EOF was reached.
        """
        import asyncio
        from pyshark.tshark.tshark_json import packet_from_json_packet
        from pyshark.tshark.tshark_xml import packet_from_xml_packet, psml_structure_from_xml

        # yield each packet in existing_data
        if self.use_json:
            packet, existing_data = self._extract_packet_json_from_data(existing_data,
                                                                        got_first_packet=got_first_packet)
        else:
            packet, existing_data = self._extract_tag_from_data(existing_data)

        if packet:
            if self.use_json:
                packet = packet_from_json_packet(packet)
            else:
                packet = packet_from_xml_packet(packet, psml_structure=psml_structure)
            return packet, existing_data

        if(not self.is_open.value):
            raise EOFError()
        
        
        future = asyncio.create_task(stream.read(self.DEFAULT_BATCH_SIZE))
        try:
            await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            return False, existing_data

        new_data = future.result()

        existing_data += new_data

        if not new_data:
            # Reached EOF
            raise EOFError()
        return None, existing_data

    def close(self):
        print("Closing pyshark live capture")
        self.is_open.value = False

        super().close()
        print("Successfully closed pyshark live capture")

"""
Response:
    ['__abstractmethods__', '__annotations__', '__class__', '__delattr__', '__dict__', 
    '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', 
    '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', 
    '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', 
    '__subclasshook__', '__weakref__', '_abc_impl', '_get_content_type_charset', '_get_cookies', 
    '_guess_encoding', '_set_cookies', 'content', 'cookies', 'copy', 'data', 'decode', 'encode', 
    'from_state', 'get_content', 'get_state', 'get_text', 'headers', 'http_version', 'is_replay', 
    'make', 'raw_content', 'reason', 'refresh', 'replace', 'set_content', 'set_state', 'set_text', 
    'status_code', 'stream', 'text', 'timestamp_end', 'timestamp_start', 'wrap']

ResponseData:
    ['__abstractmethods__', '__annotations__', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', 
    '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__',
    '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__',
    '__subclasshook__', '__weakref__', '_abc_impl', 'content', 'copy', 'from_state', 'get_state', 'headers', 'http_version',
    'reason', 'set_state', 'status_code', 'timestamp_end', 'timestamp_start']
"""

"""
http.HTTPFLOW:
    ['__abstractmethods__', '__annotations__', '__class__', '__delattr__', 
    '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', 
    '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', 
    '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', 
    '__str__', '__subclasshook__', '__weakref__', '_abc_impl', '_backup', '_stateobject_attributes', 
    'backup', 'client_conn', 'copy', 'error', 'from_state', 'get_state', 'id', 'intercept', 
    'intercepted', 'kill', 'killable', 'live', 'marked', 'metadata', 'mode', 'modified', 
    'replace', 'reply', 'request', 'response', 'resume', 'revert', 'server_conn', 'set_state', 'type']

Request:
    ['__abstractmethods__', '__annotations__', '__class__', '__delattr__', '__dict__', '__dir__', 
    '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', 
    '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', 
    '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', 
    '__subclasshook__', '__weakref__', '_abc_impl', '_get_content_type_charset', '_get_cookies', 
    '_get_multipart_form', '_get_query', '_get_urlencoded_form', '_guess_encoding', 
    '_parse_host_header', '_set_cookies', '_set_multipart_form', '_set_query', '_set_urlencoded_form', 
    'anticache', 'anticomp', 'constrain_encoding', 'content', 'cookies', 'copy', 'data', 
    'decode', 'encode', 'first_line_format', 'from_state', 'get_content', 'get_state', 
    'get_text', 'headers', 'host', 'host_header', 'http_version', 'is_replay', 'make', 
    'method', 'multipart_form', 'path', 'path_components', 'port', 'pretty_host', 'pretty_url', 
    'query', 'raw_content', 'replace', 'scheme', 'set_content', 'set_state', 'set_text', 
    'stream', 'text', 'timestamp_end', 'timestamp_start', 'url', 'urlencoded_form', 'wrap']

RequestData:
    ['__abstractmethods__', '__annotations__', '__class__', '__delattr__', '__dict__', '__dir__', 
    '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', 
    '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', 
    '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', 
    '__subclasshook__', '__weakref__', '_abc_impl', 'content', 'copy', 'first_line_format', 
    'from_state', 'get_state', 'headers', 'host', 'http_version', 'method', 'path', 'port', 
    'scheme', 'set_state', 'timestamp_end', 'timestamp_start']
"""

"""
pyshark

Layer (ssl)
    ['DATA_LAYER', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', 
    '__format__', '__ge__', '__getattr__', '__getattribute__', '__getstate__', '__gt__', '__hash__', 
    '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', 
    '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setstate__', '__sizeof__', 
    '__str__', '__subclasshook__', '__weakref__', '_all_fields', '_field_prefix', 
    '_get_all_field_lines', '_get_all_fields_with_alternates', '_get_field_or_layer_repr', 
    '_get_field_repr', '_layer_name', '_sanitize_field_name', 'app_data', 'field_names', 'get', 
    'get_field', 'get_field_by_showname', 'get_field_value', 'layer_name', 'pretty_print', 
    'raw_mode', 'record', 'record_length', 'record_opaque_type', 'record_version']

ssl.app_data
    ['__add__', '__class__', '__class__', '__contains__', '__delattr__', '__delattr__', '__dict__', 
    '__dir__', '__dir__', '__doc__', '__doc__', '__eq__', '__eq__', '__format__', '__format__', 
    '__ge__', '__ge__', '__getattr__', '__getattribute__', '__getattribute__', '__getitem__', 
    '__getnewargs__', '__getstate__', '__getstate__', '__gt__', '__gt__', '__hash__', '__hash__', 
    '__init__', '__init__', '__init_subclass__', '__init_subclass__', '__iter__', '__le__', 
    '__le__', '__len__', '__lt__', '__lt__', '__mod__', '__module__', '__module__', '__mul__', 
    '__ne__', '__ne__', '__new__', '__new__', '__reduce__', '__reduce__', '__reduce_ex__', 
    '__reduce_ex__', '__repr__', '__repr__', '__rmod__', '__rmul__', '__setattr__', '__setattr__', 
    '__setstate__', '__setstate__', '__sizeof__', '__sizeof__', '__slots__', '__str__', '__str__', 
    '__subclasshook__', '__subclasshook__', '__weakref__', 'add_field', 'all_fields', 
    'alternate_fields', 'base16_value', 'binary_value', 'capitalize', 'casefold', 'center', 
    'count', 'encode', 'endswith', 'expandtabs', 'fields', 'find', 'format', 'format_map', 
    'get_default_value', 'hex_value', 'hide', 'index', 'int_value', 'isalnum', 'isalpha', 
    'isascii', 'isdecimal', 'isdigit', 'isidentifier', 'islower', 'isnumeric', 'isprintable', 
    'isspace', 'istitle', 'isupper', 'join', 'ljust', 'lower', 'lstrip', 'main_field', 'maketrans', 
    'name', 'partition', 'pos', 'raw_value', 'replace', 'rfind', 'rindex', 'rjust', 'rpartition', 
    'rsplit', 'rstrip', 'show', 'showname', 'showname_key', 'showname_value', 'size', 'split', 
    'splitlines', 'startswith', 'strip', 'swapcase', 'title', 'translate', 'unmaskedvalue', 'upper', 
    'zfill']
"""

"""
crypto

RSAPrivateKey
    ['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', 
    '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', 
    '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', 
    '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_backend', '_evp_pkey', '_key_size', 
    '_rsa_cdata', 'decrypt', 'key_size', 'private_bytes', 'private_numbers', 'public_key', 'sign', 
    'signer']
"""