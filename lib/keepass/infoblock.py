#!/usr/bin/env python

'''
Classes and functions for the GroupInfo and EntryInfo blocks of a keepass file
'''

# This file is part of python-keepass and is Copyright (C) 2012 Brett Viren.
# 
# This code is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2, or (at your option) any
# later version.

import struct

# return tupleof (decode,encode) functions

def null_de(): return (lambda buf:None, lambda val:None)
def shunt_de(): return (lambda buf:buf, lambda val:val)

def ascii_de():
    from binascii import b2a_hex, a2b_hex
    return (lambda buf:b2a_hex(buf).replace('\0',''), 
            lambda val:a2b_hex(val)+'\0')

def string_de():
    return (lambda buf: buf.replace('\0',''), lambda val: val+'\0')

def short_de():
    return (lambda buf:struct.unpack("<H", buf)[0],
            lambda val:struct.pack("<H", val))

def int_de():
    return (lambda buf:struct.unpack("<I", buf)[0],
            lambda val:struct.pack("<I", val))

def date_de():
    from datetime import datetime
    def decode(buf):
        b = struct.unpack('<5B', buf)
        year = (b[0] << 6) | (b[1] >> 2);
        mon  = ((b[1] & 0b11)     << 2) | (b[2] >> 6);
        day  = ((b[2] & 0b111111) >> 1);
        hour = ((b[2] & 0b1)      << 4) | (b[3] >> 4);
        min  = ((b[3] & 0b1111)   << 2) | (b[4] >> 6);
        sec  = ((b[4] & 0b111111));
        #print 'dateify:',b,buf,year, mon, day, hour, min, sec
        return datetime(year, mon, day, hour, min, sec)

    def encode(val):
        year, mon, day, hour, min, sec = val.timetuple()[:6]
        b0 = 0x0000FFFF & ( (year>>6)&0x0000003F )
        b1 = 0x0000FFFF & ( ((year&0x0000003f)<<2) | ((mon>>2) & 0x00000003) )
        b2 = 0x0000FFFF & ( (( mon&0x00000003)<<6) | ((day&0x0000001F)<<1) \
                                | ((hour>>4)&0x00000001) )
        b3 = 0x0000FFFF & ( ((hour&0x0000000F)<<4) | ((min>>2)&0x0000000F) )
        b4 = 0x0000FFFF & ( (( min&0x00000003)<<6) | (sec&0x0000003F))
        return struct.pack('<5B',b0,b1,b2,b3,b4)
    return (decode,encode)

class InfoBase(object):
    'Base class for info type blocks'

    def __init__(self,format,string=None):
        self.format = format
        self.order = []         # keep field order
        if string: self.decode(string)
        return

    def __str__(self):
        ret = [self.__class__.__name__ + ':']
        for num,form in self.format.iteritems():
            try:
                value = self.__dict__[form[0]]
            except KeyError:
                continue
            ret.append('\t%s %s'%(form[0],value))
        return '\n'.join(ret)

    def decode(self,string):
        'Fill self from binary string'
        index = 0
        while True:
            substr = string[index:index+6]
            index += 6
            typ,siz = struct.unpack('<H I',substr)
            self.order.append((typ,siz))

            substr = string[index:index+siz]
            index += siz
            buf = struct.unpack('<%ds'%siz,substr)[0]

            name,decenc = self.format[typ]
            if name is None: break
            try:
                value = decenc[0](buf)
            except struct.error,msg:
                msg = '%s, typ = %d[%d] -> %s buf = "%s"'%\
                    (msg,typ,siz,self.format[typ],buf)
                raise struct.error,msg

            #print '%s: type = %d[%d] -> %s buf = "%s" value = %s'%\
            #    (name,typ,siz,self.format[typ],buf,str(value))
            self.__dict__[name] = value
            continue
        return

    def __len__(self):
        length = 0
        for typ,siz in self.order:
            length += 2+4+siz
        return length

    def encode(self):
        'Return binary string representatoin'
        string = ""
        for typ,siz in self.order:
            if typ == 0xFFFF:   # end of block
                encoded = None
            else:
                name,decenc = self.format[typ]
                value = self.__dict__[name]
                encoded = decenc[1](value)
                pass
            buf = struct.pack('<H',typ)
            buf += struct.pack('<I',siz)
            if encoded is not None:
                buf += struct.pack('<%ds'%siz,encoded)
            string += buf
            continue
        return string

    pass



class GroupInfo(InfoBase):
    '''One group: [FIELDTYPE(FT)][FIELDSIZE(FS)][FIELDDATA(FD)]
           [FT+FS+(FD)][FT+FS+(FD)][FT+FS+(FD)][FT+FS+(FD)][FT+FS+(FD)]...

[ 2 bytes] FIELDTYPE
[ 4 bytes] FIELDSIZE, size of FIELDDATA in bytes
[ n bytes] FIELDDATA, n = FIELDSIZE

Notes:
- Strings are stored in UTF-8 encoded form and are null-terminated.
- FIELDTYPE can be one of the following identifiers:
  * 0000: Invalid or comment block, block is ignored
  * 0001: Group ID, FIELDSIZE must be 4 bytes
          It can be any 32-bit value except 0 and 0xFFFFFFFF
  * 0002: Group name, FIELDDATA is an UTF-8 encoded string
  * 0003: Creation time, FIELDSIZE = 5, FIELDDATA = packed date/time
  * 0004: Last modification time, FIELDSIZE = 5, FIELDDATA = packed date/time
  * 0005: Last access time, FIELDSIZE = 5, FIELDDATA = packed date/time
  * 0006: Expiration time, FIELDSIZE = 5, FIELDDATA = packed date/time
  * 0007: Image ID, FIELDSIZE must be 4 bytes
  * 0008: Level, FIELDSIZE = 2
  * 0009: Flags, 32-bit value, FIELDSIZE = 4
  * FFFF: Group entry terminator, FIELDSIZE must be 0
  '''

    format = {
        0x0: ('ignored',null_de()),
        0x1: ('groupid',int_de()),
        0x2: ('group_name',string_de()),
        0x3: ('creation_time',date_de()),
        0x4: ('lastmod_time',date_de()),
        0x5: ('lastacc_time',date_de()),
        0x6: ('expire_time',date_de()),
        0x7: ('imageid',int_de()),
        0x8: ('level',short_de()),
        0x9: ('flags',int_de()),
        0xFFFF: (None,None),
        }

    def __init__(self,string=None):
        super(GroupInfo,self).__init__(GroupInfo.format,string)
        return

    def name(self):
        'Return the group_name'
        return self.group_name

    pass

class EntryInfo(InfoBase):
    '''One entry: [FIELDTYPE(FT)][FIELDSIZE(FS)][FIELDDATA(FD)]
           [FT+FS+(FD)][FT+FS+(FD)][FT+FS+(FD)][FT+FS+(FD)][FT+FS+(FD)]...

[ 2 bytes] FIELDTYPE
[ 4 bytes] FIELDSIZE, size of FIELDDATA in bytes
[ n bytes] FIELDDATA, n = FIELDSIZE

Notes:
- Strings are stored in UTF-8 encoded form and are null-terminated.
- FIELDTYPE can be one of the following identifiers:
  * 0000: Invalid or comment block, block is ignored
  * 0001: UUID, uniquely identifying an entry, FIELDSIZE must be 16
  * 0002: Group ID, identifying the group of the entry, FIELDSIZE = 4
          It can be any 32-bit value except 0 and 0xFFFFFFFF
  * 0003: Image ID, identifying the image/icon of the entry, FIELDSIZE = 4
  * 0004: Title of the entry, FIELDDATA is an UTF-8 encoded string
  * 0005: URL string, FIELDDATA is an UTF-8 encoded string
  * 0006: UserName string, FIELDDATA is an UTF-8 encoded string
  * 0007: Password string, FIELDDATA is an UTF-8 encoded string
  * 0008: Notes string, FIELDDATA is an UTF-8 encoded string
  * 0009: Creation time, FIELDSIZE = 5, FIELDDATA = packed date/time
  * 000A: Last modification time, FIELDSIZE = 5, FIELDDATA = packed date/time
  * 000B: Last access time, FIELDSIZE = 5, FIELDDATA = packed date/time
  * 000C: Expiration time, FIELDSIZE = 5, FIELDDATA = packed date/time
  * 000D: Binary description UTF-8 encoded string
  * 000E: Binary data
  * FFFF: Entry terminator, FIELDSIZE must be 0
  '''

    format = {
        0x0: ('ignored',null_de()),
        0x1: ('uuid',ascii_de()),
        0x2: ('groupid',int_de()),
        0x3: ('imageid',int_de()),
        0x4: ('title',string_de()),
        0x5: ('url',string_de()),
        0x6: ('username',string_de()),
        0x7: ('password',string_de()),
        0x8: ('notes',string_de()),
        0x9: ('creation_time',date_de()),
        0xa: ('last_mod_time',date_de()),
        0xb: ('last_acc_time',date_de()),
        0xc: ('expiration_time',date_de()),
        0xd: ('binary_desc',string_de()),
        0xe: ('binary_data',shunt_de()),
        0xFFFF: (None,None),
        }

    def __init__(self,string=None):
        super(EntryInfo,self).__init__(EntryInfo.format,string)
        return

    def name(self):
        'Return the title'
        return self.title

    pass

