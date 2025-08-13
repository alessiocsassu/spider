from .cards import Card

def is_descending_run(cards: list[Card]) -> bool:
    if not cards:
        return False
    for a, b in zip(cards, cards[1:]):
        if not (a.face_up and b.face_up and a.rank == b.rank + 1):
            return False
    return True

def can_take_run(column: list[Card], start: int) -> bool:
    if start < 0 or start >= len(column):
        return False
    if not column[start].face_up:
        return False
    return is_descending_run(column[start:])

def can_place(dst_top: Card | None, moving_front: Card) -> bool:
    if dst_top is None:
        return True
    if not dst_top.face_up:
        return False
    return dst_top.rank == moving_front.rank + 1

def complete_seq_window(column: list[Card]) -> tuple[int, int] | None:
    if len(column) < 13:
        return None
    i = len(column) - 13
    window = column[i:]
    need = list(range(13, 0, -1))
    for k, c in enumerate(window):
        if not c.face_up or c.rank != need[k]:
            return None
    return i, len(column)
