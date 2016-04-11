import os
from random import choice
from tornado import gen, ioloop, web, websocket

port = 6789

class SendALot(websocket.WebSocketHandler):
   def check_origin(self, origin):
       return True

   @gen.coroutine
   def open(self):
       print('Client connected: going to send lots of data...')
       alphabet = 'abcdefghijklmnopqrstuvwxyz0123456789 '
       i = 1
       while True:
           rand = ''.join((choice(alphabet) for _ in range(2**16)))
           id_ = '{:08}'.format(i)
           yield self.write_message(id_ + rand)
           # self.write_message(id_ + rand)
           print(id_)
           i += 1

   def on_message(self, message):
       pass

   def on_close(self):
       print('Connection dropped.')

app = web.Application([('/', SendALot)])
print('Waiting for connection on {}.'.format(port))
app.listen(port)
ioloop.IOLoop.instance().start()

