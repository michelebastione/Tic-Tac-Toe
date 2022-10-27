import asyncio, websockets, os, pickle
from random import random, randint


host = "localhost"
port = 8765
lobbies = {}

class Tris():
    def __init__(self, config):
        self.config = config

    def update(self):
        self.r1 = self.config[:3]
        self.r2 = self.config[3:6]
        self.r3 = self.config[6:]
        self.c1 = self.config[::3]
        self.c2 = self.config[1::3]
        self.c3 = self.config[2::3]
        self.d1 = self.config[::4]
        self.d2 = self.config[2:7:2]
        self.discriminant=[self.r1, self.r2, self.r3,
                           self.c1, self.c2, self.c3,
                           self.d1, self.d2]

    def win(self, pin):
        self.update()
        return any(all(j==pin for j in i)for i in self.discriminant)

    def tie(self):
        self.update()
        return all(i != ' ' for i in self.config)
    


async def response(websocket, path):
    new_or_join = await websocket.recv()
    if new_or_join == 'new':                                ##Se riceve un segnale di nuovo gioco,
        while(join_code := randint(1000, 9999))in lobbies:  ##aggiunge una chiave al dizionario 'lobby'
            join_code = randint(1000, 9999)
            continue                                        ##e crea una chiave random e aspetta un avversario 
        await websocket.send(str(join_code))
        lobbies[join_code] = {'waiting_for_opponent' : True,
                              'board' : Tris([' ']*9),
                              'current player' : random() <= 0.5,
                              'pin' : random() <= 0.5}
        game = lobbies[join_code]
        while game['waiting_for_opponent']:
            await asyncio.sleep(0)
        await websocket.send("Connessione stabilita!")
        current_player = True
        pin = 'X' if game['pin'] else 'O'
        await websocket.send(pin)

    else:                                               ##Ricevendo un segnale join, controlla che la chiave sia valida
        while int(new_or_join) not in lobbies:          ##e avvia la comunicazione tra i client invertendo il primo valore del dizionario
            await websocket.send('Codice non valido, riprovare')
            new_or_join = await websocket.recv()
        await websocket.send("Connessione stabilita!")
        lobbies[(join_code := int(new_or_join))]['waiting_for_opponent'] = False
        game = lobbies[join_code]
        current_player = False
        pin = 'X' if not game['pin'] else 'O'
        await websocket.send(pin)

    while True:    
        if game['current player'] == current_player:
            await websocket.send('1')
            await websocket.send(pickle.dumps(game['board']))
            game['board'] = pickle.loads(await websocket.recv())
            game['current player'] = not game['current player']
        else:
            await websocket.send('')
            await asyncio.sleep(0)
        if game['board'].win('X'):
            await websocket.send('')
            await websocket.send('X')
            await websocket.send(pickle.dumps(game['board']))
            break
        elif game['board'].win('O'):
            await websocket.send('')
            await websocket.send('O')
            await websocket.send(pickle.dumps(game['board']))
            break
        elif game['board'].tie():
            await websocket.send('')
            await websocket.send('tie')
            await websocket.send(pickle.dumps(game['board']))
            break
        else:
            await websocket.send('1')

    if join_code in lobbies:
        del lobbies[join_code]


start_server = websockets.serve(response, host, port)
print("Server started, listening on port ", port)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
