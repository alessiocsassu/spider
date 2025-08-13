from spider.game.cards import Card
from spider.game.state import GameState
from spider.game.actions import move, complete_sequences, deal, undo, redo

def test_move_ok_and_flip():
    s = GameState()
    s.columns[0] = [Card(9, face_up=False), Card(8, face_up=True), Card(7, face_up=True)]
    s.columns[1] = [Card(9, face_up=True)]
    ok = move(s, 0, 1, 1)
    assert ok
    assert [c.rank for c in s.columns[1]] == [9, 8, 7]
    assert len(s.columns[0]) == 1 and s.columns[0][0].face_up

def test_move_reject_wrong_run():
    s = GameState()
    s.columns[0] = [Card(9, face_up=True), Card(7, face_up=True)]
    s.columns[1] = [Card(8, face_up=True)]
    ok = move(s, 0, 0, 1)
    assert not ok
    assert [c.rank for c in s.columns[0]] == [9, 7]
    assert [c.rank for c in s.columns[1]] == [8]

def test_move_onto_empty_ok():
    s = GameState()
    s.columns[0] = [Card(6, face_up=True), Card(5, face_up=True)]
    s.columns[2] = []
    ok = move(s, 0, 0, 2)
    assert ok
    assert [c.rank for c in s.columns[2]] == [6, 5]

def test_complete_sequence_removed_and_counted():
    s = GameState()
    seq = [Card(r, face_up=True) for r in range(13, 0, -1)]
    s.columns[0] = [Card(9, face_up=True)] + seq
    removed = complete_sequences(s, 0)
    assert removed == 1
    assert [c.rank for c in s.columns[0]] == [9]
    assert s.foundations == 1

def test_deal_blocks_on_empty_column():
    s = GameState()
    s.columns = [[Card(5, face_up=True)]] + [[]] + [[Card(9, face_up=True)] for _ in range(8)]
    s.stock = [[Card(1) for _ in range(10)]]
    ok = deal(s)
    assert not ok
    assert len(s.stock) == 1

def test_deal_distributes_and_faces_up():
    s = GameState()
    s.columns = [[Card(5, face_up=True)] for _ in range(10)]
    round_cards = [Card(i) for i in range(1, 11)]
    s.stock = [round_cards]
    ok = deal(s)
    assert ok
    assert len(s.stock) == 0
    for i in range(10):
        assert s.columns[i][-1].face_up

def test_undo_redo_cycle():
    s = GameState()
    s.columns[0] = [Card(9, face_up=True), Card(8, face_up=True)]
    s.columns[1] = [Card(10, face_up=True)]
    assert move(s, 0, 0, 1)  # 8 su 9
    after_move = [c.rank for c in s.columns[1]]
    assert undo(s)
    assert [c.rank for c in s.columns[1]] == [10]
    assert redo(s)
    assert [c.rank for c in s.columns[1]] == after_move
