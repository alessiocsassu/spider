from __future__ import annotations

from random import shuffle
from time import time
from typing import List, Optional, Tuple

from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.events import Click
from textual.widgets import Button, Footer, Header, Static

from ..game import actions, rules
from ..game.cards import Card
from ..game.state import GameState


# ---------------------- helpers & theme ----------------------

RANK_LABELS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
TAIL_COLOR = "#2f579c"  # colore per la run ordinata in coda

def fmt_mmss(seconds: int) -> str:
    m, s = divmod(max(0, int(seconds)), 60)
    return f"{m:02d}:{s:02d}"

def points_for_move(delta_s: float) -> int:
    """Più veloce = più punti."""
    if delta_s <= 2:
        return 10
    if delta_s <= 5:
        return 7
    if delta_s <= 10:
        return 4
    if delta_s <= 20:
        return 2
    return 1

def suit_of(c: Card) -> str:
    return getattr(c, "suit", "♠")

def base_style_for(c: Card) -> str:
    return "bold #eaeaea on #1f1f1f" if c.face_up else "dim"


# ---------------------- widgets ----------------------

class ColumnWidget(Static):
    """Colonna di carte (1 riga = 1 carta)."""

    def __init__(self, idx: int):
        super().__init__(id=f"col{idx}", classes="col")
        self.idx = idx
        self.sel_from: Optional[int] = None

    def render(self) -> Text:
        app: SpiderApp = self.app  # type: ignore
        col = app.state.columns[self.idx]
        t = Text()

        if not col:
            t.append("[ ]", style="dim")
            return t

         # --- tail discendente in coda (movibile) ---
        run_start = len(col)
        if col and col[-1].face_up:
            i = len(col) - 1
            while i > 0:
                a, b = col[i - 1], col[i]
                if a.face_up and b.face_up and a.rank == b.rank + 1:
                    i -= 1
                else:
                    break
            run_start = i

        # --- sequenza completa K→A in coda (verde) ---
        full_start: Optional[int] = None
        if len(col) - run_start >= 13:
            window = col[-13:]
            ok = all(c.face_up for c in window) and all(
                window[k].rank == 13 - k for k in range(13)
            )
            if ok:
                full_start = len(col) - 13

        # --- sottosequenze bloccate (grigio) ---
        blocked_ranges: list[tuple[int, int]] = []
        n = len(col)
        i = 0
        while i < n - 1:
            # inizio potenziale run
            if (
                col[i].face_up and col[i + 1].face_up
                and col[i].rank == col[i + 1].rank + 1
            ):
                start = i
                j = i + 1
                while (
                    j < n - 1
                    and col[j].face_up and col[j + 1].face_up
                    and col[j].rank == col[j + 1].rank + 1
                ):
                    j += 1
                # segment [start..j]; è "bloccata" se NON arriva in fondo
                if j < n - 1 and (j - start + 1) >= 2:
                    blocked_ranges.append((start, j))
                i = j + 1
            else:
                i += 1

        def is_blocked_index(k: int) -> bool:
            return any(a <= k <= b for (a, b) in blocked_ranges)

        # --- rendering ---
        for i, c in enumerate(col):
            label = (RANK_LABELS[c.rank - 1] + suit_of(c)) if c.face_up else "■"
            style = base_style_for(c)

            # tail movibile (blu)
            if c.face_up and i >= run_start:
                style = f"bold #ffffff on {TAIL_COLOR}"

            # sequenza completa (verde)
            if full_start is not None and i >= full_start:
                style = "bold #d9ffd9 on #0f3d0f"

            # sottosequenza bloccata (grigio chiaro) — solo se NON tail/green
            if (
                c.face_up
                and is_blocked_index(i)
                and not (i >= run_start)
                and not (full_start is not None and i >= full_start)
            ):
                style = "bold #e0e0e0 on #2a2a2a"  # un po' più chiaro del bg normale

            # selezione (vince su tutto)
            if self.sel_from is not None and i >= self.sel_from:
                style = "reverse"

            t.append(f" {label} ", style=style)
            if i < len(col) - 1:
                t.append("\n")

        return t


class StockWidget(Static):
    def render(self) -> Text:
        app: SpiderApp = self.app  # type: ignore
        return Text(f"Deal:{len(app.state.stock)}")


class FoundWidget(Static):
    def render(self) -> Text:
        app: SpiderApp = self.app  # type: ignore
        return Text(f"Completed:{app.state.foundations}")


# ---------------------- app ----------------------

class SpiderApp(App):
    """Spider (1 seme) – TUI con click-to-move, punteggio e timer."""

    CSS_PATH = "theming.css"

    BINDINGS = [
        ("n", "new_game", "New"),
        ("d", "deal", "Deal"),
        ("u", "undo", "Undo"),
        ("R", "redo", "Redo"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.state = GameState()
        self.columns: List[ColumnWidget] = []

        # HUD
        self.stock = StockWidget(id="stock")
        self.found = FoundWidget(id="found")
        self.hud_time = Static(id="hud_time")
        self.hud_msg = Static(id="hud_msg")

        # selezione
        self.selected: Optional[Tuple[int, int]] = None  # (src_col_idx, start_index)

        # timer & punteggio
        self.t0 = time()
        self.last_move_ts = self.t0
        self._timer = None  # handle set_interval

        # stato partita
        self.game_over = False

    # ---------- layout ----------
    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(id="top"):
            yield Button("New [n]", id="btn_new")
            yield Button("Deal [d]", id="btn_deal")
            yield self.stock
            yield self.found
            yield self.hud_time
            yield self.hud_msg
        with Horizontal(id="board"):
            for i in range(10):
                colw = ColumnWidget(i)
                self.columns.append(colw)
                yield colw
        yield Footer()

    # ---------- lifecycle & loop ----------
    def on_mount(self) -> None:
        self.action_new_game()
        self._timer = self.set_interval(1.0, self._tick)

    def _tick(self) -> None:
        if self.game_over:
            return
        dt = int(time() - self.t0)
        self.hud_time.update(f" ⏱ {fmt_mmss(dt)}  |  Score: {self.state.score} ")

    # ---------- victory ----------
    def _check_victory(self) -> None:
        """Se hai completato tutte le 8 fondazioni, chiudi la partita."""
        if not self.game_over and self.state.foundations >= 8:
            self._on_win()

    def _on_win(self) -> None:
        self.game_over = True
        dt = int(time() - self.t0)
        bonus = max(0, 1000 - dt)  # bonus finale: più veloce = più punti
        self.state.score += bonus

        # ferma il timer in modo compatibile con versioni diverse
        try:
            if self._timer is not None:
                for meth in ("pause", "stop", "cancel"):
                    if hasattr(self._timer, meth):
                        getattr(self._timer, meth)()
                        break
        except Exception:
            pass

        # disabilita Deal
        try:
            self.query_one("#btn_deal", Button).disabled = True
        except Exception:
            pass

        # HUD finale
        self.hud_msg.update(f" 🎉 You won!  +{bonus} bonus ")
        self.hud_time.update(f" ⏱ {fmt_mmss(dt)}  |  Score: {self.state.score} ")

    # ---------- utils ----------
    def _new_game_setup(self) -> None:
        deck: List[Card] = [Card(r) for _ in range(8) for r in range(1, 14)]  # 104 carte, 1 seme
        shuffle(deck)

        self.state.columns = [[] for _ in range(10)]
        self.state.stock = []
        self.state.foundations = 0
        self.state.moves = 0
        self.state.history.clear()
        self.state.future.clear()
        self.state.score = 0

        # distribuzione iniziale (come Spider 1-suit)
        for i in range(4):
            for _ in range(6):
                self.state.columns[i].append(deck.pop())
        for i in range(4, 10):
            for _ in range(5):
                self.state.columns[i].append(deck.pop())
        for i in range(10):
            self.state.columns[i][-1].face_up = True

        # 5 giri di deal (10 carte)
        for _ in range(5):
            self.state.stock.append([deck.pop() for _ in range(10)])

        # timer
        self.t0 = time()
        self.last_move_ts = self.t0

    def _refresh_all(self) -> None:
        for c in self.columns:
            c.refresh()
            try:
                c.scroll_end(animate=False)
            except Exception:
                pass
        self.stock.refresh()
        self.found.refresh()

        # aggiorna HUD e controlla vittoria
        if not self.game_over:
            self._tick()
        self._check_victory()

    def _hit_index(self, colw: ColumnWidget, y_click: int) -> int:
        """Converte la Y del click nell'indice di carta, considerando bordo/padding/scroll."""
        border_top = 1
        pad_top = int(colw.styles.padding.top or 0)
        try:
            scroll = int(colw.scroll_offset.y)  # Textual 0.59+
        except AttributeError:
            scroll = int(getattr(colw, "scroll_y", 0))  # fallback per versioni vecchie
        content_y = max(0, y_click - border_top - pad_top + scroll)
        col = self.state.columns[colw.idx]
        return 0 if not col else min(len(col) - 1, content_y)

    def _clear_selection(self) -> None:
        if self.selected is not None:
            src_idx, _ = self.selected
            self.columns[src_idx].sel_from = None
            self.columns[src_idx].remove_class("-selected")
            self.selected = None

    # ---------- actions ----------
    def action_new_game(self) -> None:
        self._new_game_setup()
        self.game_over = False

        # ri-attiva Deal
        try:
            self.query_one("#btn_deal", Button).disabled = False
        except Exception:
            pass

        # reset timer (ferma l’eventuale precedente e ricrealo)
        try:
            if self._timer is not None and hasattr(self._timer, "cancel"):
                self._timer.cancel()
        except Exception:
            pass
        self._timer = self.set_interval(1.0, self._tick)

        self._clear_selection()
        self._refresh_all()
        self.hud_msg.update(" New ")

    def action_deal(self) -> None:
        if self.game_over:
            return
        self._clear_selection()
        if actions.deal(self.state):
            self._refresh_all()
            self.hud_msg.update(" Deal ")
        else:
            self.hud_msg.update(" Can't deal ")

    def action_undo(self) -> None:
        if self.game_over:
            return
        self._clear_selection()
        if actions.undo(self.state):
            self._refresh_all()
            self.hud_msg.update(" Undo ")
        else:
            self.hud_msg.update(" Nothing to undo ")

    def action_redo(self) -> None:
        if self.game_over:
            return
        self._clear_selection()
        if actions.redo(self.state):
            self._refresh_all()
            self.hud_msg.update(" Redo ")
        else:
            self.hud_msg.update(" Nothing to redo ")

    # ---------- UI events ----------
    @on(Button.Pressed, "#btn_new")
    def _btn_new(self) -> None:
        self.action_new_game()

    @on(Button.Pressed, "#btn_deal")
    def _btn_deal(self) -> None:
        self.action_deal()

    @on(Click, ".col")
    def on_column_click(self, event: Click) -> None:
        if self.game_over:
            return
        if not isinstance(event.control, ColumnWidget):
            return

        colw: ColumnWidget = event.control
        col = self.state.columns[colw.idx]
        i = self._hit_index(colw, int(event.y))

        # se non ho una selezione attiva, provo a selezionare una run da questa colonna
        if self.selected is None:
            if col and rules.can_take_run(col, i):
                colw.sel_from = i
                colw.add_class("-selected")
                self.selected = (colw.idx, i)
                colw.refresh()
                self.hud_msg.update(" Select ")
            else:
                self.hud_msg.update(" Can't pick ")
            return

        # ho già una selezione: provo a spostare nella colonna cliccata
        src_idx, start = self.selected
        if actions.move(self.state, src_idx, start, colw.idx):
            now = time()
            gained = points_for_move(now - self.last_move_ts)
            self.state.score += gained
            self.last_move_ts = now
            self.hud_msg.update(f" +{gained} pts ")
            self._clear_selection()
            self._refresh_all()
        else:
            self.hud_msg.update(" Invalid ")
            self._clear_selection()
            self._refresh_all()


def main() -> None:
    SpiderApp().run()