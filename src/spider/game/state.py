from dataclasses import dataclass, field
from typing import List, Tuple
from .cards import Card

@dataclass
class GameState:
    columns: List[List[Card]] = field(default_factory=lambda: [[] for _ in range(10)])
    stock: List[List[Card]] = field(default_factory=list)
    foundations: int = 0
    moves: int = 0
    history: List[Tuple] = field(default_factory=list)
    future: List[Tuple] = field(default_factory=list)
    score: int = 0

def snapshot(state: GameState) -> Tuple:
    cols = [[Card(c.rank, c.suit, c.face_up) for c in col] for col in state.columns]
    stock = [[Card(c.rank, c.suit, c.face_up) for c in pile] for pile in state.stock]
    return (cols, stock, state.foundations, state.moves)

def restore(state: GameState, snap: Tuple) -> None:
    cols, stock, foundations, moves = snap
    state.columns = [[Card(c.rank, c.suit, c.face_up) for c in col] for col in cols]
    state.stock = [[Card(c.rank, c.suit, c.face_up) for c in pile] for pile in stock]
    state.foundations = foundations
    state.moves = moves
