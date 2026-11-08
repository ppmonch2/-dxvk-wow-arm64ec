from pathlib import Path
import struct, hashlib, json, sys, re

class PE:
    def __init__(self, path):
        self.path = Path(path)
        self.b = self.path.read_bytes()
        self.pe = self.u32(60)
        assert self.b[self.pe:self.pe+4] == b'PE\0\0'
        self.machine = self.u16(self.pe+4)
        n = self.u16(self.pe+6)
        self.opt = self.pe+24
        assert self.u16(self.opt) == 0x20b
        self.imagebase = self.u64(self.opt+24)
        self.sections = []
        start = self.opt+self.u16(self.pe+20)
        for i in range(n):
            s = start+40*i
            vs, va, size, raw = struct.unpack_from('<IIII', self.b, s+8)
            self.sections.append((va, max(vs,size), raw, size))
    def u16(self, o): return struct.unpack_from('<H', self.b, o)[0]
    def u32(self, o): return struct.unpack_from('<I', self.b, o)[0]
    def u64(self, o): return struct.unpack_from('<Q', self.b, o)[0]
    def off(self, rva):
        for va, vs, raw, size in self.sections:
            if va <= rva < va+size: return raw+rva-va
        if rva < self.u32(self.opt+60): return rva
        raise ValueError(hex(rva))
    def string(self, rva):
        o = self.off(rva)
        return self.b[o:self.b.index(b'\0',o)].decode(errors='replace')
    def directory(self, i): return struct.unpack_from('<II',self.b,self.opt+112+8*i)
    def imports(self, index=1):
        rva, size = self.directory(index)
        if not rva:return {}
        out = {}; start = self.off(rva)
        for o in range(start, start+size, 20):
            original, stamp, forward, name, thunk = struct.unpack_from('<IIIII', self.b,o)
            if not name: break
            entries = []; t = self.off(original or thunk)
            while self.u64(t):
                v = self.u64(t);t+=8
                entries.append('#'+str(v&0xffff) if v>>63 else self.string(v+2))
            out[self.string(name)] = entries
        return out
    def exports(self):
        rva,size = self.directory(0)
        if not rva:return {}
        o=self.off(rva);base=self.u32(o+16);n=self.u32(o+24)
        funcs=self.off(self.u32(o+28));names=self.off(self.u32(o+32));ords=self.off(self.u32(o+36))
        out={}
        for i in range(n):
            name=self.string(self.u32(names+4*i));ordn=self.u16(ords+2*i)
            addr=self.u32(funcs+4*ordn)
            out[name]={'ordinal':ordn+base,'forwarder':self.string(addr) if rva<=addr<rva+size else None}
        return out
    def report(self):
        return {'path':str(self.path),'size':len(self.b),'sha256':hashlib.sha256(self.b).hexdigest(),
                'machine':hex(self.machine),'image_base':hex(self.imagebase),'imports':self.imports(),
                'exports':self.exports(),'markers':[s.decode(errors='replace') for s in re.findall(rb'[\x20-\x7e]{6,}',self.b) if b'WOW-CUSTOM' in s],
                'subsystem':self.u16(self.opt+68),'dll_characteristics':hex(self.u16(self.opt+70))}

if __name__=='__main__':
    print(json.dumps([PE(p).report() for p in sys.argv[1:]],indent=2))
