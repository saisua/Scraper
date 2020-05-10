print("Starting Interceptor imports...  ")
import sys
import socket
from multiprocessing import Manager, Process
from re import search, sub
from os import getcwd
import io

import pyshark
import pem
from pyshark.capture.capture import Capture
from pyshark.capture.live_capture import LiveCapture
from pyshark.packet.packet import Packet
from mitmproxy import proxy, options, http
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.addons import core
from click import echo
from PIL import Image
from ctypes import c_bool
#from cryptography.hazmat.backends import default_backend
#from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key

from Structures.Async_generator import AGenerator

print("Done (Interceptor)")

class Interceptor():
    stdout = sys.stdout

    async_gen:AGenerator
    non_realtime:Process=None
    __open:bool

    _manager:Manager

    ip:str
    port:int

    __capture:LiveCapture

    def __init__(self, manager:Manager=None, *, ip:str='127.0.0.1', port:int=None,
                        process_non_realtime:bool=False, non_realtime_capture_filter:str='',
                        non_realtime_interface:str='any'):
        self._manager = manager or Manager()

        self.async_gen = AGenerator()


        self.__open = file_a = self._manager.Value(c_bool, True)

        self.ip = ip
        self.port = port or Interceptor.__get_open_port(ip)
        #self.key = generate_private_key(65537, 2048, default_backend())

        if(process_non_realtime):
            self.start_pyshark_capture(non_realtime_capture_filter, non_realtime_interface)

            self.non_realtime = Process(target=self.non_realtime_process)
            self.non_realtime.start()

        opts = options.Options(
                listen_host=self.ip, mode="socks5",
                listen_port=self.port,
                confdir=f"{getcwd()}//Structures//.mitmproxy"
                )
        opts.add_option("body_size_limit", int, 0, "")
        opts.add_option("keep_host_header", bool, True, "")
        opts.add_option("showhost", bool, True, "")
        #opts.add_option("keep_host_header")

        pconf = proxy.config.ProxyConfig(opts)

        self.proxy = DumpMaster(opts, with_termlog=False, with_dumper=False)
        self.proxy.server = proxy.server.ProxyServer(pconf)
        self.proxy.addons.add(self)

        self.proxy_process = Process(target=self.proxy.run, daemon=True)
        self.proxy_process.start()

        if(manager is None):
            self._manager = Manager()
        else:
            self._manager = manager

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

    def running(self):
        echo(f"The interceptor is up and running in {self.ip}:{self.port}", file=self.stdout)

    def request(self, flow:http.HTTPFlow):
        #echo(f"request {flow.client_conn.address} -> {flow.server_conn.address}", file=self.stdout)
        pass
        

    def response(self, flow:http.HTTPFlow):
        #echo(f"response {flow.server_conn.address} -> {flow.client_conn.address}", file=self.stdout)
        pass
        #print(f"{flow.server_conn.address[0]} : {flow.response.headers.get('content-type')}")
        #if(not flow.server_conn.address[0] in self.logged_data):
        #    self.logged_data[flow.server_conn.address[0]] = []
        #self.logged_data[flow.server_conn.address[0]].append(flow.response.headers.get("content-type"))
        #content = (dict(map(Sniffer_event.keys_lower, flow.response.headers.items()))
        #                .get("content-type",""))

        #echo(f"\n\nRESPONSE {content}", file=self.stdout)

        #if(content.startswith("image")):
            #self.images+=1
            #self.async_gen.append(Sniffer_event.save_image(flow.response.raw_content, self.images, content))
        
    def start_pyshark_capture(self, capture_filter:str='', interface:str='any'):
        with open(f"{'//'.join(__file__.split('/')[:-1])}//.mitmproxy//ssl.key", "wb") as file:
            file.write(pem.parse_file(f"{'//'.join(__file__.split('/')[:-1])}//.mitmproxy//mitmproxy-ca.pem")[0].as_bytes())

        # Custom parameters got from https://github.com/eaufavor/pyshark-ssl
        self.__capture = Closable_LCapture(interface="lo",#interface,
            #bpf_filter=capture_filter,#sub(r"port \d*", capture_filter, f"port {self.port}"),
            display_filter="ssl",
            custom_parameters= ['-o', 'ssl.desegment_ssl_records:TRUE', 
                            '-o', 'ssl.desegment_ssl_application_data:TRUE',
                            '-o','tcp.desegment_tcp_streams:TRUE', 
                            '-o', f"ssl.keylog_file:{'//'.join(__file__.split('/')[:-1])}//.mitmproxy//ssl.key"]
            #decryption_key=(pem.parse_file())[0].as_text()
        )

    def non_realtime_process(self):
        print("Enabled non-realtime packet process in Interceptor")

        def print_packet(packet:Packet):
            pass
            #echo(type(packet.ssl), file=self.stdout)
            #echo(dir(packet.ssl), file=self.stdout)
            #echo(f"{packet.ip.src} -> {packet.ip.dst}", file=self.stdout)

        #capture.set_debug(True)
        self.__capture.apply_on_packets(print_packet)

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
        image.save(f"./Results/Images/image{image_num}.{extension}")

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
"""