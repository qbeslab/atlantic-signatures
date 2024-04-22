"""
API for sending messages to and from the Create
"""
import json
from enum import IntEnum, IntFlag
import socket

__all__ = ['BreakLoop', 'PACKETS', 'HEADERLEN', 'PORT', 'ALT_PORT', 'Protocol']


class BreakLoop(Exception):
    pass


class PACKETS(IntFlag):
    COMMAND    = 0x01
    CONFIG     = 0x02
    DATA       = 0x04
    START      = 0x08
    CLOSE      = 0x10
    
    ACKCOMMAND = 0xfe
    ACKCONFIG  = 0xfd
    ACKDATA    = 0xfb
    ACKSTART   = 0xf7
    ACKCLOSE   = 0xef

    @classmethod
    def get_ack(cls, value: int) -> int:
        return bytes([0xff ^ value])
    
    @classmethod
    def get_ackb(cls, value: bytes) -> bytes:
        return bytes([0xff ^ int.from_bytes(value, byteorder='big')])
    
    def __bytes__(self) -> bytes:
        return bytes([self.value])
    
    



    
    
# Magic numbers
HEADERLEN = 3
MAXBYTES  = 10**HEADERLEN

# Port 10,000 is the default port but we cannot guarantee that some other
# process wont start using that port. Thus an alternative port: 10,001 is
# reserved as a fallback.
PORT = 10000
ALT_PORT = 10001


                
def _to_packet(pb, chunk):
    return b'%s%*d%s' % (pb, HEADERLEN, len(chunk), chunk)

def ipackets(pb, b=None):
    msglen = 0 if b is None else len(b)
    if not msglen:
        yield pb
        
    else:
        for i in range(0, msglen, MAXBYTES):
            yield _to_packet(pb, b[i: i + MAXBYTES])
        
        if not msglen % MAXBYTES:
            yield _to_packet(pb, b'')
            
            
class Protocol:
        
    def send_close(self):
        self._send(bytes(PACKETS.CLOSE))
    
    def recv_close(self, payload):
        self._client_sock.send(bytes(PACKETS.ACKCLOSE))
        raise BreakLoop()
            
    # ----------- Helper Methods for sending and receiving --------------------
        
    def _send(self, pb, b=None):
        """Helper method for sending packets."""
        try:
            for sp in ipackets(pb, b):
                self._client_sock.send(sp)
            
            if self._client_sock.recv(1) != PACKETS.get_ackb(pb):
                raise OSError('The last command was not properly acknowledged')
        except:
            self._client_sock.close()
            raise
            
    def _recv(self):
        try:
            d = self._client_sock.recv(1 + HEADERLEN)
            pb, _headerlen = d[0], d[1:]
            if _headerlen:
                payload = self._client_sock.recv(int(_headerlen))
            else:
                payload = b''

        except socket.timeout:
            self._client_sock.close()
            if hasattr(self, '_sock'):
                # Host has its own socket to close
                self._sock.close()
            raise
            
        return pb, payload

            
            
            
            
            
            
            
            
            
            
            