import asyncio, websockets, sys, pickle
from concurrent.futures import ThreadPoolExecutor
from time import time

class Tris():
    def __init__(self, config):
        self.config = config

    def __str__(self):
        "Disegna una scacchiera 3x3 con posizioni occupate determinate dalla lista n"

        n = self.config
        return f"""
      |     |     
   {n[0]}  |  {n[1]}  |  {n[2]}  
 _____|_____|_____
      |     |     
   {n[3]}  |  {n[4]}  |  {n[5]}  
 _____|_____|_____
      |     |     
   {n[6]}  |  {n[7]}  |  {n[8]}   
      |     |      """


async def ainput(prompt: str = ""):
    "Funzione che permette di cercare un input in maniera asincrona"
    
    with ThreadPoolExecutor(1, "AsyncInput", lambda x: print(x, end="", flush=True), (prompt,)) as executor:
        return (await asyncio.get_event_loop().run_in_executor(
            executor, sys.stdin.readline
        )).rstrip()            
                


async def main_handler(game_type):
    async with websockets.connect("ws://ilmiotris.herokuapp.com") as socket:

        if game_type == "NEW":
            await socket.send('new')
            join_code = await socket.recv()
            print("Invia il codice ", join_code, "ai tuoi amici per giocare con loro!")
            print(await socket.recv())

        else:
            green_light = 'Codice non valido, riprovare'
            while green_light == 'Codice non valido, riprovare':
                print("Inserisci il codice per connetterti ad una lobby:")
                join_code = await ainput()
                if not join_code.isdigit() or int(join_code) not in range(1000, 10000):
                    print(green_light)
                    continue
                await socket.send(join_code)
                green_light = await socket.recv()
                print(green_light)

        pin = await socket.recv()
        playing = bool(pin)
        print("\nPer giocare, seleziona il numero corrispondente alla casella")
        print(Tris(list(range(1, 10))))

        while playing:
            current_player = await socket.recv()
            if not current_player:
                print("Attendi il tuo turno!", end='\r')
                playing = bool(await socket.recv())
            else:   
                board = pickle.loads(await socket.recv())
                if any(i != ' ' for i in board.config):
                    print(board)
                move = await ainput("Qual è la tua mossa?: ")
                while (not move.isdigit() or
                       int(move) not in range(1, 10) or
                       board.config[int(move)-1]!=' '):
                    print("Mossa non valida, riprova")
                    move = await ainput("Qual è la tua mossa?: ")
                board.config[int(move)-1] = pin
                await socket.send(pickle.dumps(board))
                print(board)
                playing = bool(await socket.recv())

        outcome = await socket.recv()
        last_board = pickle.loads(await socket.recv())
        if not current_player:
            print(last_board)
        if outcome == 'tie':
            print("Pareggio!")
        else:
            print(['Hai perso!', 'Hai vinto!'][pin == outcome], end ='\n\n')

def main():
    while True:
        command = ""
        print("Usa NEW per iniziare una nuova partita o JOIN per unirti ad una partita\n")
        while True:
            command = input().upper()
            check = command in ("JOIN", "NEW")
            if check:
                break
            else:
                print("Non ho capito, ripeti")
        try:
            asyncio.get_event_loop().run_until_complete(main_handler(command))
        except:
            print("\nErrore di rete!\n")
            raise
main()
