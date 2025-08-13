import json
from pathlib import Path
from typing import Dict, Any, List
from .state import GameState
from .cards import Card

def to_dict(state: GameState) -> Dict[str, Any]:
    return {
        "columns": [[{"r": c.rank, "s": c.suit, "u": c.face_up} for c in col] for col in state.columns],
        "stock": [[{"r": c.rank, "s": c.suit, "u": c.face_up} for c in pile] for pile in state.stock],
        "foundations": state.foundations,
        "moves": state.moves,
        "score": state.score,
    }

def from_dict(data: Dict[str, Any]) -> GameState:
    s = GameState()
    s.columns = [[Card(c["r"], c.get("s", "♠"), c.get("u", True)) for c in col] for col in data.get("columns", [[] for _ in range(10)])]
    s.stock = [[Card(c["r"], c.get("s", "♠"), c.get("u", False)) for c in pile] for pile in data.get("stock", [])]
    s.foundations = int(data.get("foundations", 0))
    s.moves = int(data.get("moves", 0))
    s.score = int(data.get("score", 0))
    s.history.clear()
    s.future.clear()
    return s

def save(state: GameState, path: Path) -> None:
    path.write_text(json.dumps(to_dict(state)))

def load(path: Path) -> GameState:
    data = json.loads(path.read_text())
    return from_dict(data)
