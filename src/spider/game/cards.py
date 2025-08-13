from dataclasses import dataclass

@dataclass
class Card:
    rank: int
    suit: str = "♠"
    face_up: bool = True
