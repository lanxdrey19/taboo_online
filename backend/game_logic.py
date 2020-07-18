from asyncio import Event, wait, sleep, FIRST_COMPLETED
from json import dumps
from flask_socketio import send
from typing import Dict, List

from functions import is_correct, random_word_and_taboo_words, words_list, get_words
from models import Player, Session

ROUND_TIME: int = 60


class Turn:
    def __init__(self, current_speaker: Player, session: Session):
        words: List[str] = random_word_and_taboo_words(words_list)
        self.current_word = words[0]
        self.taboo_words = words[1:]
        self.current_speaker: Player = current_speaker
        self.answered_players: List[Player] = []
        self.unanswered_players: List[Player] = list(filter(lambda x: x.name != current_speaker.name, session.participants.values()))
        session.current_turn = self
        self.time_left = ROUND_TIME

async def timer_routine() -> None:
    await sleep(delay=60)
    pass

async def run_turn(turn: Turn):
    timer = timer_routine()
    for _ in range(len(turn.unanswered) + len(turn.answered)):
        done, _ = await wait([turn.answer_event.wait(), timer], return_when=FIRST_COMPLETED)
        if done is None:
            break
        else:
            turn.answer_event.clear()
            continue

async def lobby(session: Session):
    await session.started.wait()
    print(f"Started session {session.id_}")
    for p in session.participants.keys():
        player: Player = session.participants[p]
        turn: Turn = Turn(player, session)
        send(dumps({"round_started": {}}), json=True, room=session.id_)
        await run_turn(turn)
        send(dumps({"round_ended": {p.name:p.points for p in session.participants.values()}}), json=True, room=session.id_)
    pass

def answer(session: Session, guess: str, name: str) -> bool:
    if is_correct(session.current_turn, guess, session.participants[name], session.current_turn.time_left, ROUND_TIME):
        session.current_turn.answer_event.set()
        return True
    return False

