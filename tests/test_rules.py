from spider.game.cards import Card
from spider.game.rules import is_descending_run, can_take_run, can_place

def test_is_descending_run_ok():
    run = [Card(8), Card(7), Card(6)]
    assert is_descending_run(run)

def test_is_descending_run_break():
    run = [Card(8), Card(6)]
    assert not is_descending_run(run)

def test_can_take_run_start_hidden():
    col = [Card(9, face_up=False), Card(8), Card(7)]
    assert not can_take_run(col, 0)

def test_can_take_run_ok_from_middle():
    col = [Card(10), Card(9), Card(8), Card(7)]
    assert can_take_run(col, 1)

def test_can_place_rules():
    assert can_place(Card(7), Card(6))
    assert not can_place(Card(7), Card(8))
    assert can_place(None, Card(13))
