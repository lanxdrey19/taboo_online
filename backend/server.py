import asyncio
from asyncio import Event
from sanic import Sanic, request
from sanic.response import json, text
from sanic_cors import CORS
import socketio
from json import dumps
from typing import Dict, List
from uuid import uuid4

from game_logic import lobby, answer
from functions import is_correct
from models import Player, Session

app = Sanic(__name__)
CORS(app)
socket = socketio.AsyncServer(async_mode='sanic', cors_allowed_origins="*")
socket.attach(app)

sessions: Dict[str, Session] = {}

@app.route('/host', methods=["POST"])
def host(request) -> str:
    data = request.json
    if type(data) == dict:
        name = data["name"]
        id_ = data["id"]
        session = Session(id_, name)
        sessions[id_] = session
        asyncio.create_task(lobby(session, socket))
        return json({"id": id_})
    else:
        return "ERROR"

@app.route('/list')
def list_handler(request) -> str:
    return json([s.name for s in sessions.values()])

@socket.on('join')
async def on_join(sid, data):
    id_: int = data["id"]
    name: str = data["name"]
    try:
        session: Session = sessions[id_]
        session.participants[name] = Player(name, sid)
    except KeyError:
        await socket.emit("room-does-not-exist")
    await socket.emit("joined", {"name": name, "is_host": session.host == name}, room=id_)
    for p in session.participants.values():
        await socket.emit("joined", {"name": p.name, "is_host": session.host == p.name}, to=sid)
    socket.enter_room(sid, id_)

@socket.on('start')
async def on_start(sid, data):
    id_: str = data["id"]
    session = sessions[id_]
    # if session.name == name:
    session.started.set()
    await socket.emit("started", room=id_)

@socket.on('answer')
async def on_answer(sid, data):
    name: str = data["name"]
    id_: str = data["id"]
    guess: str = data["guess"]
    session = sessions[id_]
    if not await answer(session, guess, name):
        await socket.emit("message", {"message": guess}, room=id_)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
