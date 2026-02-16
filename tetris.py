import curses
import random
import time

# Board size
BOARD_W = 10
BOARD_H = 20

# Tetromino shapes (4x4 matrices)
SHAPES = {
    "I": [
        "....",
        "####",
        "....",
        "....",
    ],
    "O": [
        ".##.",
        ".##.",
        "....",
        "....",
    ],
    "T": [
        ".#..",
        "###.",
        "....",
        "....",
    ],
    "S": [
        ".##.",
        "##..",
        "....",
        "....",
    ],
    "Z": [
        "##..",
        ".##.",
        "....",
        "....",
    ],
    "J": [
        "#...",
        "###.",
        "....",
        "....",
    ],
    "L": [
        "..#.",
        "###.",
        "....",
        "....",
    ],
}


def rotate(shape):
    return ["".join(shape[3 - r][c] for r in range(4)) for c in range(4)]


def new_piece():
    name = random.choice(list(SHAPES))
    shape = SHAPES[name]
    x = BOARD_W // 2 - 2
    y = 0
    return {"name": name, "shape": shape, "x": x, "y": y}


def collide(board, piece, dx=0, dy=0, shape=None):
    if shape is None:
        shape = piece["shape"]
    for r in range(4):
        for c in range(4):
            if shape[r][c] == "#":
                bx = piece["x"] + c + dx
                by = piece["y"] + r + dy
                if bx < 0 or bx >= BOARD_W or by >= BOARD_H:
                    return True
                if by >= 0 and board[by][bx] == "#":
                    return True
    return False


def lock_piece(board, piece):
    for r in range(4):
        for c in range(4):
            if piece["shape"][r][c] == "#":
                bx = piece["x"] + c
                by = piece["y"] + r
                if 0 <= by < BOARD_H and 0 <= bx < BOARD_W:
                    board[by][bx] = "#"


def clear_lines(board):
    new_board = []
    cleared = 0
    for row in board:
        if all(cell == "#" for cell in row):
            cleared += 1
        else:
            new_board.append(row)
    while len(new_board) < BOARD_H:
        new_board.insert(0, ["."] * BOARD_W)
    return new_board, cleared


def draw(stdscr, board, piece, score, best_score):
    height, width = stdscr.getmaxyx()
    board_w_chars = BOARD_W * 2 + 2
    board_h_rows = BOARD_H + 1
    min_height = 3 + board_h_rows + 1
    min_width = max(board_w_chars, 18)

    def safe_addstr(y, x, text):
        if y < 0 or y >= height or x >= width:
            return
        if x < 0:
            text = text[-x:]
            x = 0
        if x < width:
            text = text[: max(0, width - x)]
            if not text:
                return
            try:
                stdscr.addnstr(y, x, text, len(text))
            except curses.error:
                # Ignore draw errors on tight terminals.
                return

    stdscr.erase()
    if height < min_height or width < min_width:
        safe_addstr(0, 0, "Terminal too small")
        safe_addstr(1, 0, f"Need {min_width}x{min_height} or larger")
        stdscr.refresh()
        return

    safe_addstr(0, 0, "TETRIS (q to quit)")
    safe_addstr(1, 0, f"Score: {score}  Best: {best_score}")

    # Draw board with piece overlay
    for y in range(BOARD_H):
        line = "|"
        for x in range(BOARD_W):
            cell = board[y][x]
            line += "[]" if cell == "#" else "  "
        line += "|"
        safe_addstr(3 + y, 0, line)

    # Overlay piece
    for r in range(4):
        for c in range(4):
            if piece["shape"][r][c] == "#":
                px = piece["x"] + c
                py = piece["y"] + r
                if 0 <= py < BOARD_H and 0 <= px < BOARD_W:
                    safe_addstr(3 + py, 1 + px * 2, "[]")

    safe_addstr(3 + BOARD_H, 0, "+" + "-" * (BOARD_W * 2) + "+")
    stdscr.refresh()


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)

    board = [["."] * BOARD_W for _ in range(BOARD_H)]
    piece = new_piece()
    score = 0
    best_score = 0

    drop_interval = 0.5
    last_drop = time.time()

    while True:
        now = time.time()
        key = stdscr.getch()

        if key == ord("q"):
            break
        elif key in (curses.KEY_LEFT, ord("a")):
            if not collide(board, piece, dx=-1):
                piece["x"] -= 1
        elif key in (curses.KEY_RIGHT, ord("d")):
            if not collide(board, piece, dx=1):
                piece["x"] += 1
        elif key in (curses.KEY_DOWN, ord("s")):
            if not collide(board, piece, dy=1):
                piece["y"] += 1
        elif key == curses.KEY_UP:
            while not collide(board, piece, dy=1):
                piece["y"] += 1
        elif key in (ord("w"), ord(" ")):
            rotated = rotate(piece["shape"])
            if not collide(board, piece, shape=rotated):
                piece["shape"] = rotated

        if now - last_drop >= drop_interval:
            last_drop = now
            if not collide(board, piece, dy=1):
                piece["y"] += 1
            else:
                lock_piece(board, piece)
                board, cleared = clear_lines(board)
                score += cleared * 100
                if score > best_score:
                    best_score = score
                piece = new_piece()
                if collide(board, piece):
                    stdscr.addstr(3 + BOARD_H + 2, 0, "Game Over! Press q to quit.")
                    stdscr.refresh()
                    while stdscr.getch() != ord("q"):
                        time.sleep(0.05)
                    break

        draw(stdscr, board, piece, score, best_score)
        time.sleep(0.02)


if __name__ == "__main__":
    curses.wrapper(main)
