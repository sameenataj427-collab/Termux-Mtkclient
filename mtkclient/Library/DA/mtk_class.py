#!/usr/bin/env python3
import os
import logging
from struct import unpack
from mtkclient.config.usb_ids import default_ids
from mtkclient.config.payloads import PathConfig
from mtkclient.Library.pltools import PLTools
from mtkclient.Library.mtk_preloader import Preloader
from mtkclient.Library.DA.mtk_daloader import DAloader
from mtkclient.Library.Port import Port
from mtkclient.Library.gui_utils import LogBase, logsetup
from mtkclient.Library.error import ErrorHandler

class Mtk(metaclass=LogBase):
    def __init__(self, config, loglevel=logging.INFO, serialportname: str = None, preinit=True):
        self.config = config
        self.pathconfig = PathConfig()
        self.__logger, self.info, self.debug, self.warning, self.error = logsetup(self, None, loglevel, config.gui)
        self.eh = ErrorHandler()
        self.serialportname = serialportname or os.environ.get("TERMUX_USB_FD")
        
        if preinit:
            self.setup(config.vid, config.pid, config.interface, self.serialportname)

    def setup(self, vid=None, pid=None, interface=None, serialportname: str = None):
        if serialportname:
            self.port = Port(mtk=self, portconfig=[], serialportname=serialportname, loglevel=self.__logger.level)
        else:
            portconfig = [[vid, pid, interface or -1]] if vid and vid != -1 else default_ids
            self.port = Port(mtk=self, portconfig=portconfig, loglevel=self.__logger.level)
            
        self.preloader = Preloader(self, self.__logger.level)
        self.daloader = DAloader(self, self.__logger.level)

    def parse_preloader(self, preloader):
        if isinstance(preloader, str) and os.path.exists(preloader):
            with open(preloader, "rb") as rf:
                data = rf.read()
        else:
            data = preloader
        data = bytearray(data)
        if data[:4] == b'\x4d\x4d\x4d\x01':
            jump_offset = unpack("<I", data[0x30:0x34])[0]
            daaddr = unpack("<I", data[0x1C:0x20])[0] + jump_offset
            return daaddr, data[jump_offset:]
        return self.config.chipconfig.da_payload_addr, data

    def bypass_security(self):
        plt = PLTools(self, self.__logger.level)
        payload_path = self.config.payloadfile or os.path.join(self.pathconfig.get_payloads_path(), "generic_patcher_payload.bin")
        if os.path.exists(payload_path):
            return plt.runpayload(filename=payload_path)
        return False

    def crasher(self, display=True, mode=None):
        plt = PLTools(self, self.__logger.level)
        modes = [mode] if mode is not None else range(3)
        for m in modes:
            try:
                plt.crash(m)
                if self.preloader.init(): return True
            except: continue
        return False
