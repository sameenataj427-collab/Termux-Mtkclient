#!/usr/bin/env python3
# (c) B.Kerler 2022-2024, MIT License
import os
import sys
import logging
from struct import pack, unpack
from binascii import hexlify

from mtkclient.Library.mtk_crypto import (
    calc_checksum, decode_imei, is_luhn_valid, encode_imei, 
    decrypt_cssd, create_cssd, patch_md1img, make_luhn_checksum
)
from mtkclient.Library.utils import getint, find_binary
from mtkclient.Library.gui_utils import LogBase, logsetup
from mtkclient.config.payloads import PathConfig
from mtkclient.Library.error import ErrorHandler

class DaHandler(metaclass=LogBase):
    def __init__(self, mtk, loglevel=logging.INFO):
        self.__logger, self.info, self.debug, self.warning, self.error = logsetup(self, None, loglevel, mtk.config.gui)
        self.mtk = mtk
        self.config = mtk.config
        self.pathconfig = PathConfig()
        self.eh = ErrorHandler()

    def connect(self, mtk, directory: str = "."):
        # Termux USB Bridge logic
        fd = os.environ.get("TERMUX_USB_FD")
        if fd is not None:
            self.info(f"Termux USB FD detected: {fd}.")
            mtk.port.cdc.connected = True
        else:
            mtk.port.cdc.connect()

        if not mtk.port.cdc.connected:
            mtk.preloader.init(directory=directory)
        return mtk

    def da_read(self, partitionname, parttype, filename, offset=0, length=None):
        gpt = self.mtk.daloader.get_partition_data(parttype=parttype)
        for entry in gpt:
            if entry.name.lower() == partitionname.lower():
                d_len = length if length else entry.sectors * self.config.pagesize
                self.mtk.daloader.readflash(addr=(entry.sector * self.config.pagesize) + offset,
                                            length=d_len, filename=filename, parttype=parttype)
                return True
        return False

    def da_vbmeta(self, vbmode: int = 3):
        res = self.mtk.daloader.detect_partition("vbmeta", "user")
        if res[0]:
            data = self.mtk.daloader.readflash(addr=res[1].sector * self.config.pagesize,
                                               length=res[1].sectors * self.config.pagesize)
            if data:
                patched = bytearray(data)
                # Apply standard mtkclient vbmeta patch
                patched[0x78:0x7c] = int.to_bytes(vbmode, 4, 'big')
                self.mtk.daloader.writeflash(addr=res[1].sector * self.config.pagesize,
                                             length=len(patched), wdata=patched)
                self.info("Vbmeta patched successfully.")

    def handle_da_cmds(self, mtk, cmd, args):
        if not mtk or not mtk.daloader:
            self.error("DA not active.")
            return

        if cmd == "gpt":
            data, guid = self.mtk.daloader.get_gpt()
            if guid:
                with open("gpt.bin", "wb") as wf:
                    wf.write(data)
                self.info("GPT dumped to gpt.bin")
        elif cmd == "printgpt":
            _, guid = mtk.daloader.get_gpt()
            if guid: guid.print()
        elif cmd == "r":
            off = getint(args.offset) if args.offset else 0
            length = getint(args.length) if args.length else None
            self.da_read(args.partitionname, args.parttype, args.filename, off, length)
        elif cmd == "w":
            parts = args.partitionname.split(",")
            files = args.filename.split(",")
            for i, part in enumerate(parts):
                res = self.mtk.daloader.detect_partition(part, args.parttype)
                if res[0]:
                    self.mtk.daloader.writeflash(addr=res[1].sector * self.config.pagesize,
                                                 length=res[1].sectors * self.config.pagesize,
                                                 filename=files[i], parttype=args.parttype)
        elif cmd == "e":
            parts = args.partitionname.split(",")
            for part in parts:
                res = self.mtk.daloader.detect_partition(part, args.parttype)
                if res[0]:
                    self.mtk.daloader.formatflash(addr=res[1].sector * self.config.pagesize,
                                                  length=res[1].sectors * self.config.pagesize,
                                                  partitionname=part, parttype=args.parttype)
        elif cmd == "reset":
            mtk.daloader.shutdown(bootmode=0)
            self.info("Device reset initiated.")
        elif cmd == "da":
            self._handle_sub(mtk, args)

    def _handle_sub(self, mtk, args):
        sub = args.subcmd
        if sub == "peek":
            data = mtk.daloader.peek(getint(args.address), getint(args.length))
            print(hexlify(data).decode())
        elif sub == "poke":
            val = bytes.fromhex(args.data.replace("0x", ""))
            mtk.daloader.poke(getint(args.address), val)
        elif sub == "rpmb":
            if args.rpmb_subcmd == "r":
                mtk.daloader.read_rpmb(args.filename, args.sector, args.sectors)
            elif args.rpmb_subcmd == "w":
                mtk.daloader.write_rpmb(args.filename, args.sector, args.sectors)
        elif sub == "vbmeta":
            self.da_vbmeta(getint(args.vbmode))

    @staticmethod
    def close():
        sys.exit(0)
