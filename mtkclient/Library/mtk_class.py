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
         plt.crash(m)
                if self.preloader.init(): return True
            except: continue
        return False
 defaults if no header found
        return self.config.chipconfig.da_payload_addr, data

    def run_exploit(self, mode=None):
        """
        Universal Exploit Wrapper.
        Calls the full PLTools library to support kamakiri, amonet, etc.
        """
        plt = PLTools(self, self.__logger.level)
        try:
            if mode:
                return plt.run_exploit(mode)
            else:
                # Default to automatic detection
                return plt.run_exploit()
        except Exception as e:
            self.error(f"Exploit failed: {str(e)}")
            return False

    def bypass_security(self):
        """
        Supports the generic security bypass used by standard MTK client.
        Relies on the external payloads directory to keep this file clean.
        """
        plt = PLTools(self, self.__logger.level)
        payload_path = self.config.payloadfile or os.path.join(self.pathconfig.get_payloads_path(), "generic_patcher_payload.bin")
        
        if os.path.exists(payload_path):
            if plt.runpayload(filename=payload_path):
                # Re-handshake after payload execution to confirm BROM access
                self.port.run_handshake()
                return True
        self.error("Universal security bypass failed or payload missing.")
        return False

    def get_device_info(self):
        """Standard MTK command to retrieve hardware IDs."""
        return self.preloader.get_hw_info()

    def crasher(self, display=True, mode=None):
        """Universal BROM crasher for forcing devices into the correct mode."""
        plt = PLTools(self, self.__logger.level)
        modes = [mode] if mode is not None else range(3)
        for m in modes:
            try:
                plt.crash(m)
                if self.preloader.init(): 
                    return True
            except: 
                continue
        return False
         # break
            i += 1
        if not patched:
            self.warning("Failed to patch preloader security")
        else:
            # with open("preloader.patched", "wb") as wf:
            #    wf.write(data)
            #    print("Patched !")
            # self.info(f"Patched preloader security: {hex(i)}")
            data = data
        return data

    def parse_preloader(self, preloader):
        if isinstance(preloader, str):
            if os.path.exists(preloader):
                with open(preloader, "rb") as rf:
                    data = rf.read()
        else:
            data = preloader
        data = bytearray(data)
        magic = unpack("<I", data[:4])[0]
        if magic == 0x014D4D4D:
            self.info("Valid preloader detected.")
            daaddr = unpack("<I", data[0x1C:0x20])[0]
            # dasize = unpack("<I", data[0x20:0x24])[0]
            # maxsize = unpack("<I", data[0x24:0x28])[0]
            # content_offset = unpack("<I", data[0x28:0x2C])[0]
            # sig_length = unpack("<I", data[0x2C:0x30])[0]
            jump_offset = unpack("<I", data[0x30:0x34])[0]
            daaddr = jump_offset + daaddr
            dadata = data[jump_offset:]
        else:
            self.warning("Preloader detected as shellcode, might fail to run.")
            daaddr = self.config.chipconfig.da_payload_addr
            dadata = data
        return daaddr, dadata

    def setup(self, vid=None, pid=None, interface=None, serialportname: str = None):
        if vid is None:
            vid = self.vid
        if pid is None:
            pid = self.pid
        if interface is None:
            interface = self.interface
        if vid != -1 and pid != -1:
            if interface == -1:
                for dev in default_ids:
                    if dev[0] == vid and dev[1] == pid:
                        interface = dev[2]
                        break
            portconfig = [[vid, pid, interface]]
        else:
            portconfig = default_ids
        import os; import os; self.port = Port(mtk=self, portconfig=portconfig, serialportname=serialportname, loglevel=self.__logger.level) if not os.environ.get("TERMUX_USB_FD") else Port(mtk=self, portconfig=[], serialportname=os.environ.get("TERMUX_USB_FD"), loglevel=self.__logger.level) if not os.environ.get("TERMUX_USB_FD") else Port(mtk=self, portconfig=[], serialportname=os.environ.get("TERMUX_USB_FD"), loglevel=self.__logger.level)
        self.preloader = Preloader(self, self.__logger.level)
        self.daloader = DAloader(self, self.__logger.level)

    def crasher(self, display=True, mode=None):
        rmtk = self
        plt = PLTools(self, self.__logger.level)
        if self.config.enforcecrash or self.config.meid is None or not self.config.is_brom:
            self.info("We're not in bootrom, trying to crash da...")
            if mode is None:
                for crashmode in range(0, 3):
                    try:
                        plt.crash(crashmode)
                    except Exception:
                        pass
                    rmtk = Mtk(config=self.config, loglevel=self.__logger.level,
                               serialportname=rmtk.port.serialportname)
                    rmtk.preloader.display = display
                    if rmtk.preloader.init():
                        if rmtk.config.is_brom:
                            break
            else:
                try:
                    plt.crash(mode)
                except Exception as err:
                    self.__logger.debug(str(err))
                    pass
                rmtk = Mtk(config=self.config, loglevel=self.__logger.level, serialportname=rmtk.port.serialportname)
                rmtk.preloader.display = display
                if rmtk.preloader.init():
                    return rmtk
        return rmtk

    def bypass_security(self):
        if self.config.chipconfig.damode == 6:
            return self
        mtk = self.crasher()
        plt = PLTools(mtk, self.__logger.level)
        if self.config.payloadfile is None:
            if self.config.chipconfig.loader is None:
                self.config.payloadfile = os.path.join(self.pathconfig.get_payloads_path(),
                                                       "generic_patcher_payload.bin")
            else:
                self.config.payloadfile = os.path.join(self.pathconfig.get_payloads_path(),
                                                       self.config.chipconfig.loader)
        if plt.runpayload(filename=self.config.payloadfile):
            if mtk.serialportname:
                mtk.port.serial_handshake()
            else:
                mtk.port.run_handshake()
            return mtk
        else:
            self.error("Error on running kamakiri payload")
        return self
