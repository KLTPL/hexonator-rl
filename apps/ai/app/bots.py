"""Hex bots.

For now there is only MockBot. The real model (MCTS / AlphaZero) will implement
exactly the same `Bot` interface, so the backend and frontend won't notice the swap.

Board convention (shared across the whole project):
- board[row][col], square n x n board, drawn as a rhombus
- 0 = empty, 1 = red, 2 = blue
- red (1) connects TOP to BOTTOM (row 0 to row n-1) and moves first
- blue (2) connects LEFT to RIGHT (column 0 to column n-1)

This module does not depend on FastAPI, so it can be tested and used on its own.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Protocol

EMPTY, RED, BLUE = 0, 1, 2
MIN_SIZE, MAX_SIZE = 3, 19

# The 6 neighbours of cell (row, col) on a rhombus board
NEIGHBORS = ((-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0))

Board = list[list[int]]


class InvalidPosition(ValueError):
    """A position the bot cannot respond to (bad board, wrong turn, etc.)."""


@dataclass(frozen=True)
class BotMove:
    row: int
    col: int
    # Move probability distribution (n x n, sums to 1, occupied cells = 0).
    # The real model will return its policy head output here -> the frontend can draw a heatmap.
    policy: Board | None
    # Position evaluation in [-1, 1] from the perspective of the player to move (value head).
    evaluation: float | None
    bot: str


class Bot(Protocol):
    name: str

    def choose_move(self, board: Board, to_move: int) -> BotMove: ...


def validate_position(board: Board, to_move: int) -> None:
    """Checks that the position makes sense. Raises InvalidPosition with a description.

    Deliberately does NOT check whether someone has already won - that is the job of
    the game engine in the backend (BFS / union-find). The bot is only asked for a
    move in an ongoing game.
    """
    size = len(board)
    if not MIN_SIZE <= size <= MAX_SIZE:
        raise InvalidPosition(
            f"Board size must be between {MIN_SIZE} and {MAX_SIZE}, got {size}."
        )
    for r, row in enumerate(board):
        if len(row) != size:
            raise InvalidPosition(
                f"Board must be square: row {r} has {len(row)} cells instead of {size}."
            )
        for c, cell in enumerate(row):
            if cell not in (EMPTY, RED, BLUE):
                raise InvalidPosition(
                    f"Cell ({r}, {c}) has value {cell!r}, allowed values are 0, 1, 2."
                )
    if to_move not in (RED, BLUE):
        raise InvalidPosition(f"toMove must be 1 or 2, got {to_move!r}.")

    red = sum(row.count(RED) for row in board)
    blue = sum(row.count(BLUE) for row in board)
    # Red moves first, so there are as many red stones as blue, or one more.
    # NOTE: once the swap rule is added, this check will need to be relaxed.
    if red == blue:
        expected = RED
    elif red == blue + 1:
        expected = BLUE
    else:
        raise InvalidPosition(f"Inconsistent stone count: {red} red, {blue} blue.")
    if to_move != expected:
        raise InvalidPosition(
            f"It is player {expected}'s turn, not player {to_move}'s."
        )
    if red + blue == size * size:
        raise InvalidPosition("The board is full - there are no moves left.")


class MockBot:
    """Pretends to be a real bot. It doesn't think - it samples, but returns the full response format.

    Strategies:
    - "random": every empty cell with equal probability
    - "local":  prefers cells next to stones and closer to the centre, so it looks
                less nonsensical and gives a more interesting "heatmap" for testing the frontend
    """

    def __init__(self, strategy: str = "local", seed: int | None = None) -> None:
        if strategy not in ("random", "local"):
            raise ValueError(f"Unknown strategy: {strategy!r}")
        self.strategy = strategy
        self.name = f"mock-{strategy}"
        self._rng = random.Random(seed)

    def choose_move(self, board: Board, to_move: int) -> BotMove:
        validate_position(board, to_move)
        size = len(board)
        weights = [
            [self._weight(board, r, c) for c in range(size)] for r in range(size)
        ]

        total = sum(sum(row) for row in weights)
        policy = [[w / total for w in row] for row in weights]

        cells = [(r, c) for r in range(size) for c in range(size)]
        flat = [weights[r][c] for r, c in cells]
        row, col = self._rng.choices(cells, weights=flat, k=1)[0]

        # Fake evaluation - only so the frontend has something to show on the eval bar.
        evaluation = round(self._rng.uniform(-0.3, 0.3), 3)
        return BotMove(
            row=row, col=col, policy=policy, evaluation=evaluation, bot=self.name
        )

    def _weight(self, board: Board, r: int, c: int) -> float:
        if board[r][c] != EMPTY:
            return 0.0
        if self.strategy == "random":
            return 1.0
        size = len(board)
        near_stone = any(
            0 <= r + dr < size and 0 <= c + dc < size and board[r + dr][c + dc] != EMPTY
            for dr, dc in NEIGHBORS
        )
        center = (size - 1) / 2
        dist = max(abs(r - center), abs(c - center)) / max(
            center, 1
        )  # 0 at the centre, 1 at the edge
        return 1.0 + (3.0 if near_stone else 0.0) + 2.0 * (1.0 - dist)
