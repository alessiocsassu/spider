from typing import Optional, List, Tuple
from .state import GameState, snapshot
from .cards import Card
from . import rules

def complete_sequences(state: GameState, col_idx: int) -> int:
    col = state.columns[col_idx]
    removed = 0
    while True:
        win = rules.complete_seq_window(col)
        if not win:
            break
        a, b = win
        del col[a:b]
        state.foundations += 1
        removed += 1
    return removed

def move(state: GameState, src: int, start: int, dst: int) -> bool:
    if src == dst:
        return False
    if src < 0 or src >= len(state.columns) or dst < 0 or dst >= len(state.columns):
        return False
    scol = state.columns[src]
    dcol = state.columns[dst]
    if not rules.can_take_run(scol, start):
        return False
    moving = scol[start:]
    dst_top: Optional[Card] = dcol[-1] if dcol else None
    if not rules.can_place(dst_top, moving[0]):
        return False
    state.history.append(snapshot(state))
    state.future.clear()
    dcol.extend(moving)
    del scol[start:]
    if scol and not scol[-1].face_up:
        scol[-1].face_up = True
    complete_sequences(state, dst)
    state.moves += 1
    return True

def deal(state: GameState) -> bool:
    if any(len(c) == 0 for c in state.columns):
        return False
    if not state.stock:
        return False
    state.history.append(snapshot(state))
    state.future.clear()
    round_cards = state.stock.pop(0)
    for i, col in enumerate(state.columns):
        card = round_cards[i]
        card.face_up = True
        col.append(card)
        complete_sequences(state, i)
    state.moves += 1
    return True

def undo(state: GameState) -> bool:
    if not state.history:
        return False
    snap = state.history.pop()
    state.future.append(snapshot(state))
    from .state import restore
    restore(state, snap)
    return True

def redo(state: GameState) -> bool:
    if not state.future:
        return False
    snap = state.future.pop()
    state.history.append(snapshot(state))
    from .state import restore
    restore(state, snap)
    return True

def list_legal_moves(state: GameState) -> List[Tuple[int, int, int]]:
    out: List[Tuple[int, int, int]] = []
    for s_idx, scol in enumerate(state.columns):
        for start in range(len(scol)):
            if not rules.can_take_run(scol, start):
                continue
            front = scol[start]
            for d_idx, dcol in enumerate(state.columns):
                if d_idx == s_idx:
                    continue
                top = dcol[-1] if dcol else None
                if rules.can_place(top, front):
                    out.append((s_idx, start, d_idx))
    return out

def hint(state: GameState) -> Optional[Tuple[int, int, int]]:
    moves = list_legal_moves(state)
    if not moves:
        return None
    moves.sort(key=lambda m: (len(state.columns[m[2]]), -m[1]))
    return moves[0]

def auto_move_one(state: GameState) -> bool:
    h = hint(state)
    if not h:
        return False
    s, start, d = h
    return move(state, s, start, d)

def is_win(state: GameState) -> bool:
    return state.foundations >= 8
