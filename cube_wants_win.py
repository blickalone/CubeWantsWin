import pygame
import time

pygame.init()

SCREEN_W = 1060
SCREEN_H = 820
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
clock  = pygame.time.Clock()
pygame.display.set_caption("Cube Wants Win")


def get_font(size, bold=False):
    names = ["Arial", "DejaVu Sans"]
    for name in names:
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            if f is not None:
                return f
        except Exception:
            pass
    return pygame.font.Font(None, size)

font_sm   = get_font(13)
font_md   = get_font(15)
font_bold = get_font(17, bold=True)
font_ttl  = get_font(30, bold=True)
font_big  = get_font(46, bold=True)

# ── Цвета ─────────────────────────────────────────────────────────────────────
C_BG       = (10,  10,  16)
C_CELL     = (20,  20,  30)
C_GRID     = (28,  28,  40)
C_WALL     = (65,  65,  80)
C_WHITE    = (230, 230, 242)
C_GRAY     = (105, 105, 120)
C_GRAY2    = (45,  45,  60)
C_YELLOW   = (255, 208,  0)
C_GREEN    = (45,  200,  70)
C_RED      = (235,  55,  55)
C_CYAN     = (0,   200, 215)
C_MAGENTA  = (200,  40, 200)
C_ORANGE   = (240, 140,  30)
C_BLUE     = (60,  110, 215)
C_BLACK    = (5,    5,   8)
C_SLIDER   = (30,  30,  46)
C_KNOB     = (180, 180, 200)

# ── Типы ──────────────────────────────────────────────────────────────────────
EMPTY = 0
WALL  = 1
GOAL  = 2

B_WALL = 4   # слово "WALL"
B_GOAL = 5   # слово "GOAL"
B_IS   = 6   # слово "IS"
B_STOP = 7   # слово "STOP"
B_WIN  = 8   # слово "WIN"
B_KILL = 9   # слово "KILL"
B_PUSH = 10  # слово "PUSH"

# Какие блоки можно толкать
PUSHABLE = [B_WALL, B_GOAL, B_IS, B_STOP, B_WIN, B_KILL, B_PUSH]

# Цвета блоков-слов
B_COLOR = {
    B_WALL: (195, 115, 35),
    B_GOAL: (190, 175,  0),
    B_IS  : (0,   185, 195),
    B_STOP: (200,  50,  50),
    B_WIN : (35,  185,  60),
    B_KILL: (185,  35, 185),
    B_PUSH: (60,  105, 210),
}
B_LABEL = {
    B_WALL:"WALL", B_GOAL:"GOAL", B_IS:"IS",
    B_STOP:"STOP", B_WIN:"WIN",  B_KILL:"KILL", B_PUSH:"PUSH",
}

MAX_LVL = 10

FACE_NAMES = [
    "Обычное","Весёлое","Решительное","Злое","Удивлённое",
    "Грустное","Хитрое","Сонное","Влюблённое","Крутое",
]

PALETTE = [
    (255,0,0),(255,100,0),(255,230,0),(100,255,0),(0,210,0),(0,255,120),
    (0,220,255),(0,100,255),(30,0,255),(130,0,255),(255,0,255),(255,0,100),
    (255,128,0),(128,255,0),(0,200,128),(0,128,255),(128,0,255),(255,0,128),
    (140,140,140),(255,255,255),(180,50,50),(50,180,50),(50,50,200),
    (190,190,50),(190,50,190),(50,190,190),(160,80,0),(80,0,160),
    (255,185,200),(165,210,240),
]

# ── Глобальное состояние игры ─────────────────────────────────────────────────
hero_r    = 0       # строка героя
hero_c    = 0       # столбец героя
goal_r    = 8       # строка цели
goal_c    = 8       # столбец цели
walls     = []      # список (r, c)
blocks    = []      # список [тип, r, c]
steps     = 0
max_steps = 40
game_over = False
game_won  = False
history   = []      # [(hero_r, hero_c, копия_blocks, steps), ...]
optimal   = -1
rule_stop = False
rule_win  = False
rule_kill = False
cur_lvl   = 1
unlocked  = 1
screen_name = "MENU"
cube_color  = [70, 130, 220]
cube_face   = 0
tick        = 0     # для анимации


# ═══════════════════════════════════════════════════════════════════════════════
# ЛОГИКА ПРАВИЛ
# ═══════════════════════════════════════════════════════════════════════════════
def update_rules():
    global rule_stop, rule_win, rule_kill
    rule_stop = False
    rule_win  = False
    rule_kill = False
    # Для каждого блока смотрим: есть ли правее/ниже IS, а потом свойство
    for i in range(len(blocks)):
        t1, r1, c1 = blocks[i]
        # Ищем IS справа (r1, c1+1) и свойство (r1, c1+2)
        for j in range(len(blocks)):
            t2, r2, c2 = blocks[j]
            if t2 == B_IS and r2 == r1 and c2 == c1 + 1:
                # нашли IS справа — ищем свойство ещё правее
                for k in range(len(blocks)):
                    t3, r3, c3 = blocks[k]
                    if r3 == r1 and c3 == c1 + 2:
                        if t1 == B_WALL and t3 == B_STOP: rule_stop = True
                        if t1 == B_GOAL and t3 == B_WIN:  rule_win  = True
                        if t1 == B_WALL and t3 == B_KILL: rule_kill = True
        # Ищем IS снизу (r1+1, c1) и свойство (r1+2, c1)
        for j in range(len(blocks)):
            t2, r2, c2 = blocks[j]
            if t2 == B_IS and r2 == r1 + 1 and c2 == c1:
                for k in range(len(blocks)):
                    t3, r3, c3 = blocks[k]
                    if r3 == r1 + 2 and c3 == c1:
                        if t1 == B_WALL and t3 == B_STOP: rule_stop = True
                        if t1 == B_GOAL and t3 == B_WIN:  rule_win  = True
                        if t1 == B_WALL and t3 == B_KILL: rule_kill = True


# ═══════════════════════════════════════════════════════════════════════════════
# РЕШАТЕЛЬ BFS (простой, без frozenset и heapq)
# ═══════════════════════════════════════════════════════════════════════════════
def solve_bfs():
    """BFS по состояниям (герой + блоки). Возвращает минимальное число ходов."""
    # Превращаем список в кортеж для хранения в visited
    start_blocks = tuple(sorted((t, r, c) for t, r, c in blocks))
    start_state  = (hero_r, hero_c, start_blocks)
    walls_set    = set()
    for r, c in walls:
        walls_set.add((r, c))

    visited = {}           # state -> min_cost
    visited[start_state] = 0
    queue   = [start_state]
    q_cost  = [0]
    dirs    = [(-1,0),(1,0),(0,-1),(0,1)]
    t_start = time.time()

    best = -1
    head = 0   # индекс начала очереди (вместо deque)

    while head < len(queue):
        if time.time() - t_start > 3.0:
            return -1   # слишком долго

        state_now = queue[head]
        cost_now  = q_cost[head]
        head += 1

        if cost_now > max_steps:
            continue

        hr, hc, blk = state_now

        # Считаем активные правила для этого состояния
        rs = False  # rule_stop
        rw = False  # rule_win
        blk_list = list(blk)
        for i in range(len(blk_list)):
            t1, r1, c1 = blk_list[i]
            for j in range(len(blk_list)):
                t2, r2, c2 = blk_list[j]
                if t2 == B_IS and r2 == r1 and c2 == c1 + 1:
                    for k in range(len(blk_list)):
                        t3, r3, c3 = blk_list[k]
                        if r3 == r1 and c3 == c1 + 2:
                            if t1 == B_WALL and t3 == B_STOP: rs = True
                            if t1 == B_GOAL and t3 == B_WIN:  rw = True
                if t2 == B_IS and r2 == r1 + 1 and c2 == c1:
                    for k in range(len(blk_list)):
                        t3, r3, c3 = blk_list[k]
                        if r3 == r1 + 2 and c3 == c1:
                            if t1 == B_WALL and t3 == B_STOP: rs = True
                            if t1 == B_GOAL and t3 == B_WIN:  rw = True

        # Проверяем победу
        if rw and hr == goal_r and hc == goal_c:
            if best == -1 or cost_now < best:
                best = cost_now
            continue

        # Генерируем ходы
        for dr, dc in dirs:
            nr, nc = hr + dr, hc + dc
            if nr < 0 or nr > 8 or nc < 0 or nc > 8:
                continue

            # Что находится на (nr, nc)
            cell_type = EMPTY
            if (nr, nc) in walls_set:
                cell_type = WALL
            cell_block_idx = -1
            for idx in range(len(blk_list)):
                if blk_list[idx][1] == nr and blk_list[idx][2] == nc:
                    cell_block_idx = idx
                    break
            if cell_block_idx >= 0:
                cell_type = blk_list[cell_block_idx][0]  # тип блока

            new_blk = None

            if cell_type in PUSHABLE:
                # Пытаемся толкнуть блок
                nnr, nnc = nr + dr, nc + dc
                if nnr < 0 or nnr > 8 or nnc < 0 or nnc > 8:
                    continue
                if (nnr, nnc) in walls_set:
                    continue
                # Проверяем — нет ли другого блока на (nnr, nnc)
                occupied = False
                for idx2 in range(len(blk_list)):
                    if blk_list[idx2][1] == nnr and blk_list[idx2][2] == nnc:
                        occupied = True
                        break
                if occupied:
                    continue
                # Двигаем блок
                new_list = []
                for idx2 in range(len(blk_list)):
                    if idx2 == cell_block_idx:
                        new_list.append((blk_list[idx2][0], nnr, nnc))
                    else:
                        new_list.append(blk_list[idx2])
                new_blk = (nr, nc, tuple(sorted(new_list)))

            elif cell_type == WALL:
                if rs:
                    continue   # WALL IS STOP — нельзя
                new_blk = (nr, nc, blk)

            else:
                new_blk = (nr, nc, blk)

            if new_blk is None:
                continue
            new_cost = cost_now + 1
            if new_blk not in visited or visited[new_blk] > new_cost:
                visited[new_blk] = new_cost
                queue.append(new_blk)
                q_cost.append(new_cost)

    return best


# ═══════════════════════════════════════════════════════════════════════════════
# ЗАГРУЗКА УРОВНЕЙ
# ═══════════════════════════════════════════════════════════════════════════════
def load_level(lvl):
    global hero_r, hero_c, goal_r, goal_c, walls, blocks
    global steps, max_steps, game_over, game_won, history, optimal
    global rule_stop, rule_win, rule_kill, cur_lvl, screen_name, tick

    cur_lvl   = lvl
    steps     = 0
    game_over = False
    game_won  = False
    history   = []
    tick      = 0

    # ── УРОВЕНЬ 1: Туториал ───────────────────────────────────────────────────
    # Правила уже стоят. Просто дойди до цели, обойдя стены.
    if lvl == 1:
        hero_r, hero_c = 4, 0
        goal_r, goal_c = 4, 8
        walls = [
            (1,4),(2,4),(3,4),
            (5,4),(6,4),(7,4),
        ]
        blocks = [
            [B_WALL,0,0],[B_IS,0,1],[B_STOP,0,2],
            [B_GOAL,0,6],[B_IS,0,7],[B_WIN,0,8],
        ]
        max_steps = 22

    # ── УРОВЕНЬ 2: Сломанное правило ─────────────────────────────────────────
    # GOAL IS WIN не собрано — IS стоит отдельно.
    # Нужно его подтолкнуть, чтобы собрать правило, потом идти к цели.
    elif lvl == 2:
        hero_r, hero_c = 0, 0
        goal_r, goal_c = 8, 8
        walls = [
            (2,2),(2,3),(2,4),(2,5),
            (6,3),(6,4),(6,5),(6,6),
        ]
        blocks = [
            [B_WALL,0,3],[B_IS,0,4],[B_STOP,0,5],
            [B_GOAL,4,5],[B_IS,5,3],[B_WIN,4,7],
        ]
        max_steps = 40

    # ── УРОВЕНЬ 3: Опасные стены ──────────────────────────────────────────────
    # Нужно собрать GOAL IS WIN, избегая сборки WALL IS KILL.
    # Стены расположены так, что к цели два пути — один смертельный.
    elif lvl == 3:
        hero_r, hero_c = 0, 0
        goal_r, goal_c = 8, 8
        walls = [
            (0,4),(1,4),(2,4),(3,4),
            (4,4),
            (5,4),(6,4),(7,4),(8,4),
        ]
        blocks = [
            [B_WALL,1,1],[B_IS,1,2],[B_STOP,1,3],
            [B_GOAL,7,5],[B_IS,5,5],[B_WIN,7,7],
            [B_KILL,3,6],
        ]
        max_steps = 55

    # ── УРОВЕНЬ 4: Переключатель ──────────────────────────────────────────────
    # Единственный IS используется двумя правилами.
    # Чтобы пройти стены — нужно WALL IS STOP (IS у WALL).
    # Чтобы победить — нужно GOAL IS WIN (IS у GOAL).
    # Придётся двигать IS туда-обратно.
    elif lvl == 4:
        hero_r, hero_c = 4, 0
        goal_r, goal_c = 4, 8
        walls = [
            (2,3),(2,4),(2,5),(2,6),
            (6,2),(6,3),(6,4),(6,5),
            (3,6),(4,6),(5,6),
        ]
        blocks = [
            [B_WALL,4,2],[B_IS,4,3],[B_STOP,4,4],
            [B_GOAL,8,5],[B_WIN,8,7],
        ]
        max_steps = 60

    # ── УРОВЕНЬ 5: Лабиринт со словами ───────────────────────────────────────
    # Блоки-слова загораживают путь, их нужно толкать,
    # но если толкнешь не туда — соберёшь WALL IS KILL.
    elif lvl == 5:
        hero_r, hero_c = 0, 0
        goal_r, goal_c = 8, 8
        walls = [
            (1,2),(2,2),(3,2),
            (5,6),(6,6),(7,6),
            (4,0),(4,1),(4,2),(4,3),(4,4),
        ]
        blocks = [
            [B_WALL,2,4],[B_IS,2,5],[B_STOP,2,6],
            [B_GOAL,6,2],[B_IS,6,3],[B_WIN,6,4],
            [B_KILL,0,5],[B_PUSH,3,7],[B_PUSH,5,1],
        ]
        max_steps = 65

    # ── УРОВЕНЬ 6: Двойной замок ──────────────────────────────────────────────
    # Два пути к цели. Один заблокирован стенами (нужно STOP),
    # другой открыт, но там KILL — нужно разрушить правило KILL
    # (убрать IS из цепочки), потом пройти.
    elif lvl == 6:
        hero_r, hero_c = 4, 4
        goal_r, goal_c = 0, 8
        walls = [
            (1,0),(2,0),(3,0),
            (1,2),(2,2),(3,2),
            (0,4),(0,5),(0,6),
            (6,2),(7,2),(8,2),
            (6,5),(7,5),(8,5),
        ]
        blocks = [
            [B_WALL,0,0],[B_IS,0,1],[B_STOP,0,2],
            [B_GOAL,0,6],[B_IS,1,7],[B_WIN,0,8],
            [B_WALL,5,3],[B_IS,5,4],[B_KILL,5,5],
        ]
        max_steps = 70

    # ── УРОВЕНЬ 7: Трёхходовка ────────────────────────────────────────────────
    # Три правила, три IS-блока, и все мешают друг другу.
    # Нужно собрать только нужные, остальные разобрать.
    elif lvl == 7:
        hero_r, hero_c = 8, 0
        goal_r, goal_c = 0, 8
        walls = [
            (2,2),(2,3),(2,4),(2,5),(2,6),
            (6,2),(6,3),(6,4),(6,5),(6,6),
            (4,3),(4,4),(4,5),
        ]
        blocks = [
            [B_WALL,1,0],[B_IS,1,1],[B_STOP,1,2],
            [B_GOAL,0,6],[B_IS,0,5],[B_WIN,0,8],
            [B_WALL,7,6],[B_IS,7,7],[B_KILL,7,8],
            [B_PUSH,4,0],[B_PUSH,4,1],[B_PUSH,4,2],
        ]
        max_steps = 75

    # ── УРОВЕНЬ 8: Зеркало ────────────────────────────────────────────────────
    # Симметричный уровень — всё выглядит одинаково с обеих сторон,
    # но только один путь ведёт к победе.
    # IS-блок нужно перенести через весь уровень.
    elif lvl == 8:
        hero_r, hero_c = 4, 0
        goal_r, goal_c = 4, 8
        walls = [
            (1,3),(2,3),(3,3),
            (1,5),(2,5),(3,5),
            (5,3),(6,3),(7,3),
            (5,5),(6,5),(7,5),
            (0,4),(8,4),
        ]
        blocks = [
            [B_WALL,0,0],[B_IS,1,0],[B_STOP,2,0],
            [B_GOAL,4,4],[B_WIN,0,8],
            [B_WALL,6,8],[B_IS,7,8],[B_KILL,8,8],
            [B_PUSH,3,4],[B_PUSH,5,4],
        ]
        max_steps = 80

    # ── УРОВЕНЬ 9: Паутина ────────────────────────────────────────────────────
    # Густая сеть стен. KILL активно с самого начала —
    # нужно СНАЧАЛА разобрать его, потом собрать WIN, потом пройти.
    elif lvl == 9:
        hero_r, hero_c = 0, 0
        goal_r, goal_c = 8, 8
        walls = [
            (1,1),(1,3),(1,5),(1,7),
            (3,0),(3,2),(3,4),(3,6),(3,8),
            (5,1),(5,3),(5,5),(5,7),
            (7,0),(7,2),(7,4),(7,6),(7,8),
        ]
        blocks = [
            [B_WALL,0,3],[B_IS,0,4],[B_KILL,0,5],   # WALL IS KILL — сразу активно!
            [B_WALL,2,0],[B_IS,2,1],[B_STOP,2,2],
            [B_GOAL,6,5],[B_WIN,6,7],
            [B_IS,4,6],
        ]
        max_steps = 85

    # ── УРОВЕНЬ 10: ФИНАЛ ────────────────────────────────────────────────────
    # Всё вместе. Нет ни одного правила изначально.
    # Нужно собрать сразу WALL IS STOP и GOAL IS WIN,
    # при этом не собрав WALL IS KILL.
    # Блоки PUSH перегораживают короткие пути.
    elif lvl == 10:
        hero_r, hero_c = 4, 4
        goal_r, goal_c = 0, 0
        walls = [
            (0,2),(0,3),(0,4),(0,5),(0,6),
            (2,0),(3,0),(4,0),(5,0),(6,0),
            (8,2),(8,3),(8,4),(8,5),(8,6),
            (2,8),(3,8),(4,8),(5,8),(6,8),
            (2,2),(2,3),(2,5),(2,6),
            (6,2),(6,3),(6,5),(6,6),
        ]
        blocks = [
            [B_WALL,1,2],[B_IS,1,3],[B_STOP,1,4],
            [B_GOAL,0,8],[B_WIN,1,8],
            [B_IS,3,6],
            [B_WALL,7,4],[B_IS,7,5],[B_KILL,7,6],
            [B_PUSH,4,2],[B_PUSH,4,6],[B_PUSH,2,4],[B_PUSH,6,4],
        ]
        max_steps = 95

    update_rules()
    history = [(hero_r, hero_c, [list(b) for b in blocks], steps)]

    # Вычисляем оптимум
    pygame.display.set_caption("Cube Wants Win  [считаю оптимум...]")
    pygame.display.flip()
    optimal = solve_bfs()
    pygame.display.set_caption("Cube Wants Win")


# ═══════════════════════════════════════════════════════════════════════════════
# ДВИЖЕНИЕ
# ═══════════════════════════════════════════════════════════════════════════════
def try_move(dr, dc):
    global hero_r, hero_c, steps, game_over, game_won

    if game_over:
        return

    nr = hero_r + dr
    nc = hero_c + dc

    # Выход за границу
    if nr < 0 or nr > 8 or nc < 0 or nc > 8:
        return

    # Сохраняем состояние для отмены
    history.append((hero_r, hero_c, [list(b) for b in blocks], steps))

    # Что стоит на (nr, nc)?
    walls_set = set()
    for r, c in walls:
        walls_set.add((r, c))

    cell = EMPTY
    if (nr, nc) in walls_set:
        cell = WALL

    block_idx = -1
    for i in range(len(blocks)):
        if blocks[i][1] == nr and blocks[i][2] == nc:
            block_idx = i
            cell = blocks[i][0]
            break

    # Блок — пробуем толкнуть
    if cell in PUSHABLE:
        nnr = nr + dr
        nnc = nc + dc
        if nnr < 0 or nnr > 8 or nnc < 0 or nnc > 8:
            history.pop()
            return
        if (nnr, nnc) in walls_set:
            history.pop()
            return
        # Проверяем — занята ли клетка другим блоком
        occupied = False
        for i in range(len(blocks)):
            if blocks[i][1] == nnr and blocks[i][2] == nnc:
                occupied = True
                break
        if occupied:
            history.pop()
            return
        # Двигаем блок
        blocks[block_idx][1] = nnr
        blocks[block_idx][2] = nnc
        hero_r = nr
        hero_c = nc
        update_rules()
        steps += 1
        check_result()
        return

    # Стена
    if cell == WALL:
        if rule_stop:
            history.pop()
            return
        # WALL IS STOP не активно — можно пройти сквозь стену
        hero_r = nr
        hero_c = nc
        update_rules()
        steps += 1
        check_result()
        return

    # Пустая клетка
    if cell == EMPTY:
        hero_r = nr
        hero_c = nc
        update_rules()
        steps += 1
        check_result()
        return

    history.pop()


def undo():
    global hero_r, hero_c, steps, game_over, game_won, blocks

    if len(history) <= 1:
        return
    if game_over:
        return

    history.pop()
    prev = history[-1]
    hero_r = prev[0]
    hero_c = prev[1]
    blocks = [list(b) for b in prev[2]]
    steps  = prev[3]
    update_rules()


def check_result():
    global game_over, game_won, unlocked

    if rule_win and hero_r == goal_r and hero_c == goal_c:
        game_won  = True
        game_over = True
        if cur_lvl >= unlocked and unlocked < MAX_LVL:
            unlocked = cur_lvl + 1
        return

    # WALL IS KILL — стоим на стене?
    if rule_kill:
        walls_set = set()
        for r, c in walls:
            walls_set.add((r, c))
        if (hero_r, hero_c) in walls_set:
            game_over = True
            game_won  = False
            return

    if steps >= max_steps:
        game_over = True
        game_won  = False


# ═══════════════════════════════════════════════════════════════════════════════
# РИСОВАНИЕ ЛИЦА  (без бликов, красивые дуги ртов)
# ═══════════════════════════════════════════════════════════════════════════════
def draw_arc_mouth(cx, cy, rx, ry, flip, thick, surf=None):
    import math
    if surf is None:
        surf = screen
    pts = []
    steps2 = 20
    for i in range(steps2 + 1):
        t = i / steps2
        angle = math.pi * t
        x = cx + rx * math.cos(angle)
        if flip:
            y = cy - ry * math.sin(angle)   # улыбка
        else:
            y = cy + ry * math.sin(angle)   # грусть
        pts.append((int(x), int(y)))
    if len(pts) >= 2:
        pygame.draw.lines(surf, C_WHITE, False, pts, thick)


def draw_face(cx, cy, sz, face, color, surf=None):
    if surf is None:
        surf = screen

    r = sz // 2
    col = (color[0], color[1], color[2])

    # Тело кубика
    pygame.draw.rect(surf, col,
                     (cx - r, cy - r, sz, sz), border_radius=max(4, sz // 8))
    # Рамка
    border_c = (max(0, col[0] - 80),
                max(0, col[1] - 80),
                max(0, col[2] - 80))
    pygame.draw.rect(surf, border_c,
                     (cx - r, cy - r, sz, sz),
                     2, border_radius=max(4, sz // 8))

    # Позиции элементов
    eo  = sz // 5          # смещение глаза по X
    ey  = cy - sz // 8    # Y глаз
    er  = max(2, sz // 9) # радиус глаза
    my  = cy + sz // 5    # Y рта
    mr  = sz // 4         # ширина рта

    def eye(ox, squint=False):
        if squint:
            pygame.draw.line(surf, C_WHITE,
                             (cx + ox - er, ey), (cx + ox + er, ey), 2)
        else:
            pygame.draw.circle(surf, C_WHITE, (cx + ox, ey), er)
            pygame.draw.circle(surf, (20, 20, 20),
                               (cx + ox + 1, ey + 1), max(1, er // 2))

    def brow(ox, dy_left, dy_right):
        pygame.draw.line(surf, C_WHITE,
                         (cx + ox - er, ey - er - 3 - dy_left),
                         (cx + ox + er, ey - er - 3 - dy_right), 2)

    def neutral():
        pygame.draw.line(surf, C_WHITE,
                         (cx - mr // 2, my), (cx + mr // 2, my), 2)

    if face == 0:   # Обычное
        eye(-eo); eye(eo); neutral()

    elif face == 1: # Весёлое
        eye(-eo); eye(eo)
        draw_arc_mouth(cx, my + mr // 6, mr // 2, mr // 5, False, 2, surf)
    elif face == 2: # Решительное
        brow(-eo, 2, -2); brow(eo, -2, 2)
        eye(-eo); eye(eo); neutral()

    elif face == 3: # Злое
        brow(-eo, 4, -2); brow(eo, -2, 4)
        eye(-eo); eye(eo)
        draw_arc_mouth(cx, my + mr // 6, mr // 2, mr // 5, False, 2, surf)

    elif face == 4: # Удивлённое
        # Большие глаза
        pygame.draw.circle(surf, C_WHITE, (cx - eo, ey), er + 2)
        pygame.draw.circle(surf, C_WHITE, (cx + eo, ey), er + 2)
        pygame.draw.circle(surf, (20, 20, 20), (cx - eo + 1, ey + 1), max(1, er // 2))
        pygame.draw.circle(surf, (20, 20, 20), (cx + eo + 1, ey + 1), max(1, er // 2))
        # Открытый рот
        pygame.draw.ellipse(surf, C_WHITE,
                            (cx - mr // 4, my - mr // 5,
                             mr // 2, mr // 3 + 2))

    elif face == 5: # Грустное
        brow(-eo, -3, 1); brow(eo, 1, -3)
        eye(-eo); eye(eo)
        draw_arc_mouth(cx, my - mr // 4, mr // 2, mr // 4, True, 2, surf)

    elif face == 6: # Хитрое
        eye(-eo)
        eye(eo, squint=True)   # правый глаз прищурен
        draw_arc_mouth(cx, my + mr // 6, mr // 2, mr // 5, False, 2, surf)

    elif face == 7: # Сонное
        eye(-eo, squint=True); eye(eo, squint=True)
        draw_arc_mouth(cx, my + mr // 6, mr // 2, mr // 5, False, 2, surf)
        zz = font_sm.render("z", True, C_WHITE)
        surf.blit(zz, (cx + eo + er + 2, ey - er - 4))

    elif face == 8: # Влюблённое — сердечки
        import math
        for ox in [-eo, eo]:
            hcx, hcy = cx + ox, ey
            hs = max(3, er)
            pts = []
            for i in range(30):
                a = 2 * math.pi * i / 30
                hx2 = hs * (16 * (math.sin(a) ** 3)) / 16
                hy2 = -hs * (13 * math.cos(a) - 5 * math.cos(2*a)
                              - 2 * math.cos(3*a) - math.cos(4*a)) / 16
                pts.append((int(hcx + hx2), int(hcy + hy2)))
            if len(pts) >= 3:
                pygame.draw.polygon(surf, C_RED, pts)
        draw_arc_mouth(cx, my + mr // 6, mr // 2, mr // 5, False, 2, surf)

    else:            # Крутое — очки
        gw = er * 2 + 4
        gh = er + 4
        for ox in [-eo, eo]:
            pygame.draw.rect(surf, C_WHITE,
                             (cx + ox - gw // 2, ey - gh // 2, gw, gh),
                             border_radius=3)
            pygame.draw.rect(surf, (15, 15, 15),
                             (cx + ox - gw // 2 + 1, ey - gh // 2 + 1,
                              gw - 2, gh - 2),
                             border_radius=2)
        pygame.draw.line(surf, C_WHITE,
                         (cx - eo + gw // 2, ey),
                         (cx + eo - gw // 2, ey), 2)
        neutral()


def draw_mini_face(surf, x, y, sz, face):
    cx, cy = x + sz // 2, y + sz // 2
    eo  = sz // 5
    ey  = cy - sz // 8
    er  = max(2, sz // 9)
    my  = cy + sz // 5
    mr  = sz // 4

    def eye(ox):
        pygame.draw.circle(surf, C_WHITE, (cx + ox, ey), er)

    def brow_line(ox, a, b):
        pygame.draw.line(surf, C_WHITE,
                         (cx + ox - er, ey - er - 2 - a),
                         (cx + ox + er, ey - er - 2 - b), 1)

    if face == 0:
        eye(-eo); eye(eo)
        pygame.draw.line(surf, C_WHITE, (cx - mr//2, my), (cx + mr//2, my), 1)

    elif face == 1:
        eye(-eo); eye(eo)
        draw_arc_mouth(cx, my + mr // 6, mr // 2, mr // 5, False, 2, surf)

    elif face == 2:
        brow_line(-eo, 2, -1); brow_line(eo, -1, 2)
        eye(-eo); eye(eo)
        pygame.draw.line(surf, C_WHITE, (cx - mr//2, my), (cx + mr//2, my), 1)

    elif face == 3:
        brow_line(-eo, 3, -1); brow_line(eo, -1, 3)
        eye(-eo); eye(eo)
        draw_arc_mouth(cx, my + mr//6, mr//2, mr//5, False, 2, surf)

    elif face == 4:
        pygame.draw.circle(surf, C_WHITE, (cx - eo, ey), er + 2)
        pygame.draw.circle(surf, C_WHITE, (cx + eo, ey), er + 2)
        pygame.draw.ellipse(surf, C_WHITE,
                            (cx - mr//4, my - mr//5, mr//2, mr//3 + 2))

    elif face == 5:
        brow_line(-eo, -2, 1); brow_line(eo, 1, -2)
        eye(-eo); eye(eo)
        draw_arc_mouth(cx, my + mr//6, mr//2, mr//5, False, 2, surf)

    elif face == 6:
        eye(-eo)
        pygame.draw.line(surf, C_WHITE,
                         (cx + eo - er, ey), (cx + eo + er, ey), 2)
        draw_arc_mouth(cx + mr//6, my - mr//5, mr//3, mr//5, True, 2, surf)

    elif face == 7:
        pygame.draw.line(surf, C_WHITE, (cx - eo - er, ey), (cx - eo + er, ey), 2)
        pygame.draw.line(surf, C_WHITE, (cx + eo - er, ey), (cx + eo + er, ey), 2)
        draw_arc_mouth(cx, my + mr // 6, mr // 2, mr // 5, False, 2, surf)

    elif face == 8:
        pygame.draw.circle(surf, C_RED, (cx - eo, ey), er)
        pygame.draw.circle(surf, C_RED, (cx + eo, ey), er)
        draw_arc_mouth(cx, my - mr//4, mr//2, mr//4, True, 2, surf)

    else:
        gw = er * 2 + 4; gh = er + 4
        for ox in [-eo, eo]:
            pygame.draw.rect(surf, C_WHITE,
                             (cx + ox - gw//2, ey - gh//2, gw, gh),
                             border_radius=3)
            pygame.draw.rect(surf, (15, 15, 15),
                             (cx + ox - gw//2 + 1, ey - gh//2 + 1, gw-2, gh-2),
                             border_radius=2)
        pygame.draw.line(surf, C_WHITE,
                         (cx - eo + gw//2, ey), (cx + eo - gw//2, ey), 2)
        pygame.draw.line(surf, C_WHITE, (cx - mr//2, my), (cx + mr//2, my), 1)


# ═══════════════════════════════════════════════════════════════════════════════
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ РИСОВАНИЯ
# ═══════════════════════════════════════════════════════════════════════════════
def in_box(x, y, w, h, mx, my):
    return x <= mx <= x + w and y <= my <= y + h

def draw_btn(text, x, y, w, h, hover, fnt=None, danger=False):
    if fnt is None:
        fnt = font_bold
    if danger:
        bg = (155, 25, 25) if hover else (85, 15, 15)
    else:
        bg = C_YELLOW if hover else (38, 38, 58)
    tc = C_BLACK if (hover and not danger) else C_WHITE
    pygame.draw.rect(screen, bg, (x, y, w, h), border_radius=8)
    pygame.draw.rect(screen, C_GRAY2, (x, y, w, h), 1, border_radius=8)
    t = fnt.render(text, True, tc)
    screen.blit(t, t.get_rect(center=(x + w // 2, y + h // 2)))

def draw_slider_ctrl(sx, sy, sw, sh, value, color, label, mx, my, click):
    pygame.draw.rect(screen, C_SLIDER, (sx, sy, sw, sh), border_radius=4)
    fw = value * sw // 255
    if fw > 0:
        pygame.draw.rect(screen, color, (sx, sy, fw, sh), border_radius=4)
    kx = sx + fw - 8
    pygame.draw.rect(screen, C_KNOB, (kx, sy - 3, 16, sh + 6), border_radius=8)
    t = font_sm.render(label + ": " + str(value), True, C_WHITE)
    screen.blit(t, (sx, sy - 19))
    # Обновление
    if click and sx <= mx <= sx + sw and sy - 10 <= my <= sy + sh + 10:
        new_val = (mx - sx) * 255 // sw
        if new_val < 0:   new_val = 0
        if new_val > 255: new_val = 255
        return new_val
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# ОТРИСОВКА ВСЕХ ЭКРАНОВ
# ═══════════════════════════════════════════════════════════════════════════════
def draw_everything():
    import math

    mx, my = pygame.mouse.get_pos()
    click  = pygame.mouse.get_pressed()[0]
    screen.fill(C_BG)

    global tick, cube_color
    tick = (tick + 1) % 628

    # ─── МЕНЮ ────────────────────────────────────────────────────────────────
    if screen_name == "MENU":
        # Фон-сетка
        for i in range(0, SCREEN_W, 44):
            pygame.draw.line(screen, (17, 17, 25), (i, 0), (i, SCREEN_H))
        for j in range(0, SCREEN_H, 44):
            pygame.draw.line(screen, (17, 17, 25), (0, j), (SCREEN_W, j))

        # Кубик покачивается
        bob = int(math.sin(tick * 0.01) * 9)
        draw_face(SCREEN_W // 2, 185 + bob, 120, cube_face, cube_color)

        t = font_big.render("CUBE WANTS WIN", True, C_YELLOW)
        screen.blit(t, t.get_rect(center=(SCREEN_W // 2, 305)))
        sub = font_sm.render("— игра о правилах и логике —", True, C_GRAY)
        screen.blit(sub, sub.get_rect(center=(SCREEN_W // 2, 336)))

        items = [
            ("ИГРАТЬ",       378, False),
            ("КАСТОМИЗАЦИЯ", 434, False),
            ("КАК ИГРАТЬ",   490, False),
            ("ВЫХОД",        554, True),
        ]
        for lbl, yy, danger in items:
            hov = in_box(SCREEN_W // 2 - 115, yy, 230, 46, mx, my)
            draw_btn(lbl, SCREEN_W // 2 - 115, yy, 230, 46, hov, danger=danger)

    # ─── ВЫБОР УРОВНЯ ────────────────────────────────────────────────────────
    elif screen_name == "LEVELS":
        t = font_ttl.render("ВЫБОР УРОВНЯ", True, C_YELLOW)
        screen.blit(t, t.get_rect(center=(SCREEN_W // 2, 52)))

        diff_names = ["Обучение","Лёгкий","Средний","Средний","Сложный",
                      "Сложный","Очень сложный","Эксперт","Эксперт","ФИНАЛ"]
        diff_cols  = [
            C_GREEN, C_GREEN,
            (210,175,0),(210,175,0),
            C_ORANGE, C_ORANGE,
            C_RED, C_MAGENTA, C_MAGENTA,
            C_YELLOW,
        ]

        BW, BH, GX, GY, COLS = 195, 88, 24, 95, 5
        for i in range(MAX_LVL):
            ci = i % COLS
            ri = i // COLS
            bx = 28 + ci * (BW + GX)
            by = GY + ri * (BH + GX)
            unlk = (i + 1) <= unlocked
            hov  = in_box(bx, by, BW, BH, mx, my) and unlk

            bg = (46, 46, 18) if hov else ((26, 26, 40) if unlk else (18, 18, 28))
            pygame.draw.rect(screen, bg, (bx, by, BW, BH), border_radius=10)
            brd = C_YELLOW if hov else C_GRAY2
            pygame.draw.rect(screen, brd, (bx, by, BW, BH), 1, border_radius=10)

            nc = C_YELLOW if unlk else (45, 45, 55)
            nt = font_big.render(str(i + 1), True, nc)
            screen.blit(nt, (bx + 12, by + 4))

            if unlk:
                dc = diff_cols[i]
                dt = font_sm.render(diff_names[i], True, dc)
                screen.blit(dt, (bx + BW - dt.get_width() - 8, by + 10))
                draw_mini_face(screen, bx + BW - 50, by + BH - 50, 42, cube_face)
            else:
                lt = font_bold.render("???", True, C_GRAY)
                screen.blit(lt, (bx + BW - 44, by + BH // 2 - 10))

        hov_b = in_box(28, SCREEN_H - 56, 110, 40, mx, my)
        draw_btn("НАЗАД", 28, SCREEN_H - 56, 110, 40, hov_b, font_md)

    # ─── КАСТОМИЗАЦИЯ ────────────────────────────────────────────────────────
    elif screen_name == "CUSTOM":
        t = font_ttl.render("КАСТОМИЗАЦИЯ", True, C_YELLOW)
        screen.blit(t, t.get_rect(center=(SCREEN_W // 2, 40)))

        draw_face(SCREEN_W // 2, 130, 105, cube_face, cube_color)
        fn = font_md.render(FACE_NAMES[cube_face], True, C_WHITE)
        screen.blit(fn, fn.get_rect(center=(SCREEN_W // 2, 196)))

        # Слайдеры
        sx, sy, sw, sh = 52, 244, 210, 12
        screen.blit(font_bold.render("ЦВЕТ:", True, C_WHITE), (sx, sy - 28))
        for i, (lbl, col) in enumerate(
                [("R", (235, 90, 90)), ("G", (90, 225, 90)), ("B", (90, 90, 235))]):
            nv = draw_slider_ctrl(sx, sy + i * 46, sw, sh,
                                  cube_color[i], col, lbl, mx, my, click)
            if nv is not None:
                cube_color[i] = nv

        # Превью цвета
        px2, py2 = sx + 224, sy + 8
        pygame.draw.rect(screen, tuple(cube_color), (px2, py2, 56, 56), border_radius=8)
        pygame.draw.rect(screen, C_WHITE, (px2 - 1, py2 - 1, 58, 58), 1, border_radius=9)
        hx_str = "#{:02X}{:02X}{:02X}".format(*cube_color)
        screen.blit(font_sm.render(hx_str, True, C_GRAY), (px2, py2 + 60))

        # Палитра
        pal_x, pal_y = 52, 392
        screen.blit(font_bold.render("ПАЛИТРА:", True, C_WHITE), (pal_x, pal_y - 22))
        for i, c in enumerate(PALETTE):
            ppx = pal_x + (i % 6) * 47
            ppy = pal_y + (i // 6) * 47
            pygame.draw.rect(screen, c, (ppx, ppy, 41, 41), border_radius=6)
            if list(c) == cube_color:
                pygame.draw.rect(screen, C_WHITE, (ppx - 2, ppy - 2, 45, 45), 2, border_radius=8)

        # Лица
        fx2, fy2 = 572, 232
        screen.blit(font_bold.render("ЭМОЦИЯ:", True, C_WHITE), (fx2, fy2 - 22))
        for i in range(10):
            ex = fx2 + (i % 5) * 94
            ey = fy2 + (i // 5) * 112
            hov2 = in_box(ex, ey, 82, 82, mx, my)
            sel  = (cube_face == i)
            pygame.draw.rect(screen, (30, 30, 46), (ex, ey, 82, 82), border_radius=10)
            brd2 = C_YELLOW if sel else (C_WHITE if hov2 else C_GRAY2)
            pygame.draw.rect(screen, brd2,
                             (ex - (2 if sel else 1), ey - (2 if sel else 1),
                              82 + (4 if sel else 2), 82 + (4 if sel else 2)),
                             (2 if sel else 1), border_radius=12)
            draw_mini_face(screen, ex, ey, 82, i)
            nt2 = font_sm.render(FACE_NAMES[i], True, C_YELLOW if sel else C_GRAY)
            screen.blit(nt2, nt2.get_rect(center=(ex + 41, ey + 92)))

        hov_b = in_box(28, SCREEN_H - 56, 110, 40, mx, my)
        draw_btn("НАЗАД", 28, SCREEN_H - 56, 110, 40, hov_b, font_md)

    # ─── КАК ИГРАТЬ ──────────────────────────────────────────────────────────
    elif screen_name == "DESC":
        t = font_ttl.render("КАК ИГРАТЬ", True, C_YELLOW)
        screen.blit(t, t.get_rect(center=(SCREEN_W // 2, 46)))

        lines = [
            (True,  "УПРАВЛЕНИЕ",                       C_WHITE),
            (False, "WASD / стрелки — двигать кубик",   C_WHITE),
            (False, "Z  или  U — отменить ход",         C_WHITE),
            (False, "R — начать уровень заново",        C_WHITE),
            (False, "ESC — вернуться в меню",           C_WHITE),
            (True,  "",                                  C_WHITE),
            (True,  "БЛОКИ-СЛОВА",                      C_CYAN),
            (False, "WALL — статическая стена",         (195,115,35)),
            (False, "GOAL — клетка цели",               (190,175,0)),
            (False, "IS   — связка (создаёт правило)",  C_CYAN),
            (False, "STOP — блокирует движение сквозь стены", C_RED),
            (False, "WIN  — победа при касании цели",   C_GREEN),
            (False, "KILL — смерть при касании стены",  C_MAGENTA),
            (False, "PUSH — эти блоки можно толкать",   C_BLUE),
            (True,  "",                                  C_WHITE),
            (True,  "ПРАВИЛА ИГРЫ",                     C_YELLOW),
            (False, "Поставь три блока в ряд:",         C_WHITE),
            (False, "WALL  IS  STOP  -> стены блокируют путь", C_WHITE),
            (False, "GOAL  IS  WIN   -> дойди до цели и победи!", C_WHITE),
            (False, "WALL  IS  KILL  -> стены убивают!", C_WHITE),
            (False, "Блоки-слова можно толкать — меняй правила!", C_YELLOW),
        ]
        y = 94
        for is_hdr, text, col in lines:
            if text == "":
                y += 8
                continue
            fnt2 = font_bold if is_hdr else font_md
            t2   = fnt2.render(text, True, col)
            screen.blit(t2, (75, y))
            y += 26 if is_hdr else 22

        hov_b = in_box(28, SCREEN_H - 56, 110, 40, mx, my)
        draw_btn("НАЗАД", 28, SCREEN_H - 56, 110, 40, hov_b, font_md)

    # ─── ИГРА ────────────────────────────────────────────────────────────────
    elif screen_name == "GAME":
        CELL = 68
        OX, OY, G = 26, 26, 9

        walls_set = set()
        for r, c in walls:
            walls_set.add((r, c))

        blocks_pos = {}
        for b in blocks:
            blocks_pos[(b[1], b[2])] = b[0]

        # Сетка
        for r in range(G):
            for c in range(G):
                x, y = OX + c * CELL, OY + r * CELL
                pygame.draw.rect(screen, C_CELL,
                                 (x + 1, y + 1, CELL - 2, CELL - 2),
                                 border_radius=4)
                pygame.draw.rect(screen, C_GRID,
                                 (x, y, CELL, CELL), 1, border_radius=4)

        # Цель (пульсирует)
        pulse = int(math.sin(tick * 0.008) * 35)
        gc2 = OX + goal_c * CELL
        gr2 = OY + goal_r * CELL
        glow_col = (0, 120 + pulse, 0)
        pygame.draw.rect(screen, glow_col,
                         (gc2 + 2, gr2 + 2, CELL - 4, CELL - 4),
                         border_radius=6)
        pygame.draw.rect(screen, C_GREEN,
                         (gc2 + 2, gr2 + 2, CELL - 4, CELL - 4),
                         2, border_radius=6)
        ct = font_sm.render("ЦЕЛЬ", True, C_GREEN)
        screen.blit(ct, ct.get_rect(center=(gc2 + CELL // 2, gr2 + CELL // 2)))

        # Стены
        for wr, wc in walls_set:
            wx, wy = OX + wc * CELL, OY + wr * CELL
            pygame.draw.rect(screen, C_WALL,
                             (wx + 2, wy + 2, CELL - 4, CELL - 4),
                             border_radius=5)
            pygame.draw.rect(screen, (82, 82, 98),
                             (wx + 2, wy + 2, CELL - 4, CELL - 4),
                             1, border_radius=5)

        # Блоки-слова
        for b in blocks:
            bt, br, bc = b
            bx, by = OX + bc * CELL, OY + br * CELL
            col = B_COLOR.get(bt, C_GRAY)
            pygame.draw.rect(screen, col,
                             (bx + 3, by + 3, CELL - 6, CELL - 6),
                             border_radius=7)
            border_c2 = (max(0, col[0] - 60),
                         max(0, col[1] - 60),
                         max(0, col[2] - 60))
            pygame.draw.rect(screen, border_c2,
                             (bx + 3, by + 3, CELL - 6, CELL - 6),
                             1, border_radius=7)
            lbl = B_LABEL.get(bt, "?")
            fnt3 = font_sm if len(lbl) > 3 else font_md
            lt   = fnt3.render(lbl, True, C_BLACK)
            screen.blit(lt, lt.get_rect(center=(bx + CELL // 2, by + CELL // 2)))

        # Герой
        hx = OX + hero_c * CELL
        hy = OY + hero_r * CELL
        draw_face(hx + CELL // 2, hy + CELL // 2,
                  CELL - 8, cube_face, cube_color)

        # ── Правая панель ─────────────────────────────────────────────────
        PX = OX + G * CELL + 20
        PW = SCREEN_W - PX - 12

        lt2 = font_bold.render("УРОВЕНЬ " + str(cur_lvl), True, C_YELLOW)
        screen.blit(lt2, (PX, 28))

        # Прогресс-бар
        if max_steps > 0:
            pct = steps / max_steps
        else:
            pct = 0
        if pct > 1:
            pct = 1
        bar_c = C_GREEN if pct < 0.5 else (C_YELLOW if pct < 0.8 else C_RED)
        screen.blit(font_md.render(
            "Шаги: " + str(steps) + " / " + str(max_steps),
            True, C_WHITE), (PX, 62))
        pygame.draw.rect(screen, C_GRAY2, (PX, 84, PW, 7), border_radius=4)
        pygame.draw.rect(screen, bar_c, (PX, 84, int(PW * pct), 7), border_radius=4)

        # Оптимум
        if optimal > 0:
            ot_str = "Оптимально: " + str(optimal) + " ходов"
        else:
            ot_str = "Оптимум: не найден"
        screen.blit(font_sm.render(ot_str, True, C_GRAY), (PX, 98))

        # Правила
        ry = 126
        screen.blit(font_bold.render("ПРАВИЛА:", True, C_WHITE), (PX, ry))
        ry += 22
        rule_list = [
            ("WALL IS STOP", rule_stop),
            ("GOAL IS WIN",  rule_win),
            ("WALL IS KILL", rule_kill),
        ]
        for rname, active in rule_list:
            col2 = C_GREEN if active else (42, 62, 42)
            pygame.draw.circle(screen, col2, (PX + 7, ry + 8), 5)
            if active:
                pygame.draw.circle(screen, C_GREEN, (PX + 7, ry + 8), 3)
            screen.blit(font_sm.render(rname, True, col2), (PX + 18, ry))
            ry += 21

        # Блоки-легенда
        ry += 8
        screen.blit(font_bold.render("БЛОКИ:", True, C_WHITE), (PX, ry))
        ry += 20
        for bt2, lbl2 in B_LABEL.items():
            if ry > SCREEN_H - 125:
                break
            col3 = B_COLOR.get(bt2, C_GRAY)
            pygame.draw.rect(screen, col3, (PX, ry, 13, 13), border_radius=3)
            screen.blit(font_sm.render(lbl2, True, C_WHITE), (PX + 18, ry))
            ry += 19

        # Управление
        ry = SCREEN_H - 108
        pygame.draw.line(screen, C_GRAY2, (PX, ry), (PX + PW, ry))
        ry += 7
        ctrl_lines = [
            "WASD / стрелки — ход",
            "Z — отменить  |  R — рестарт",
            "ESC — в меню",
        ]
        for line in ctrl_lines:
            screen.blit(font_sm.render(line, True, C_GRAY), (PX, ry))
            ry += 20

        # ── Оверлей конца игры ─────────────────────────────────────────
        if game_over:
            ovl = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            ovl.fill((0, 0, 0, 168))
            screen.blit(ovl, (0, 0))

            cx2 = SCREEN_W // 2
            cy2 = SCREEN_H // 2 - 68

            if game_won:
                wt = font_big.render("ПОБЕДА!", True, C_GREEN)
                screen.blit(wt, wt.get_rect(center=(cx2, cy2)))

                r1 = font_md.render(
                    "Ваш результат: " + str(steps) + " ходов",
                    True, C_WHITE)
                screen.blit(r1, r1.get_rect(center=(cx2, cy2 + 54)))

                if optimal > 0:
                    diff = steps - optimal
                    if diff == 0:
                        star = "★★★  ИДЕАЛЬНО!"
                    elif diff <= 4:
                        star = "★★☆  Хорошо!"
                    else:
                        star = "★☆☆  Есть куда расти"
                    r2 = font_md.render(
                        "Оптимально: " + str(optimal) + "   " + star,
                        True, C_YELLOW)
                    screen.blit(r2, r2.get_rect(center=(cx2, cy2 + 80)))

                yb = cy2 + 116
                if cur_lvl < MAX_LVL:
                    hov_n = in_box(cx2 - 138, yb, 128, 44, mx, my)
                    draw_btn("Следующий", cx2 - 138, yb, 128, 44, hov_n, font_md)
                hov_m = in_box(cx2 + 10, yb, 128, 44, mx, my)
                draw_btn("В меню", cx2 + 10, yb, 128, 44, hov_m, font_md)

            else:
                if steps >= max_steps:
                    msg = "ЛИМИТ ШАГОВ"
                else:
                    msg = "ВЫ ПОГИБЛИ"
                mt = font_big.render(msg, True, C_RED)
                screen.blit(mt, mt.get_rect(center=(cx2, cy2)))

                yb = cy2 + 70
                hov_r = in_box(cx2 - 138, yb, 128, 44, mx, my)
                hov_m = in_box(cx2 + 10,  yb, 128, 44, mx, my)
                draw_btn("Рестарт", cx2 - 138, yb, 128, 44, hov_r, font_md)
                draw_btn("В меню",  cx2 + 10,  yb, 128, 44, hov_m, font_md)

    pygame.display.flip()


# ═══════════════════════════════════════════════════════════════════════════════
# ГЛАВНЫЙ ЦИКЛ
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    global screen_name, cube_face

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # ── МЕНЮ ──────────────────────────────────────────────────
                if screen_name == "MENU":
                    CX = SCREEN_W // 2
                    if in_box(CX - 115, 378, 230, 46, mx, my):
                        screen_name = "LEVELS"
                    elif in_box(CX - 115, 434, 230, 46, mx, my):
                        screen_name = "CUSTOM"
                    elif in_box(CX - 115, 490, 230, 46, mx, my):
                        screen_name = "DESC"
                    elif in_box(CX - 115, 554, 230, 46, mx, my):
                        running = False   # ВЫХОД

                # ── УРОВНИ ────────────────────────────────────────────────
                elif screen_name == "LEVELS":
                    if in_box(28, SCREEN_H - 56, 110, 40, mx, my):
                        screen_name = "MENU"
                    else:
                        BW, BH, GX, GY, COLS = 195, 88, 24, 95, 5
                        for i in range(MAX_LVL):
                            bx = 28 + (i % COLS) * (BW + GX)
                            by = GY + (i // COLS) * (BH + GX)
                            if in_box(bx, by, BW, BH, mx, my) and (i + 1) <= unlocked:
                                load_level(i + 1)
                                screen_name = "GAME"
                                break

                # ── КАСТОМИЗАЦИЯ ──────────────────────────────────────────
                elif screen_name == "CUSTOM":
                    if in_box(28, SCREEN_H - 56, 110, 40, mx, my):
                        screen_name = "MENU"
                    else:
                        # Палитра
                        pal_x, pal_y = 52, 392
                        for i, c in enumerate(PALETTE):
                            ppx = pal_x + (i % 6) * 47
                            ppy = pal_y + (i // 6) * 47
                            if in_box(ppx, ppy, 41, 41, mx, my):
                                cube_color[0] = c[0]
                                cube_color[1] = c[1]
                                cube_color[2] = c[2]
                        # Лица
                        fx2, fy2 = 572, 232
                        for i in range(10):
                            ex = fx2 + (i % 5) * 94
                            ey = fy2 + (i // 5) * 112
                            if in_box(ex, ey, 82, 82, mx, my):
                                cube_face = i

                # ── КАК ИГРАТЬ ────────────────────────────────────────────
                elif screen_name == "DESC":
                    if in_box(28, SCREEN_H - 56, 110, 40, mx, my):
                        screen_name = "MENU"

                # ── ИГРА — конец ──────────────────────────────────────────
                elif screen_name == "GAME" and game_over:
                    cx2 = SCREEN_W // 2
                    cy2 = SCREEN_H // 2 - 68
                    if game_won:
                        yb = cy2 + 116
                        if cur_lvl < MAX_LVL and in_box(cx2 - 138, yb, 128, 44, mx, my):
                            load_level(cur_lvl + 1)
                        elif in_box(cx2 + 10, yb, 128, 44, mx, my):
                            screen_name = "MENU"
                    else:
                        yb = cy2 + 70
                        if in_box(cx2 - 138, yb, 128, 44, mx, my):
                            load_level(cur_lvl)
                        elif in_box(cx2 + 10, yb, 128, 44, mx, my):
                            screen_name = "MENU"

            # ── КЛАВИАТУРА ────────────────────────────────────────────────
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if screen_name == "GAME":
                        screen_name = "LEVELS"
                    elif screen_name != "MENU":
                        screen_name = "MENU"

                elif event.key == pygame.K_r and screen_name == "GAME":
                    load_level(cur_lvl)

                elif screen_name == "GAME" and not game_over:
                    if event.key == pygame.K_z or event.key == pygame.K_u:
                        undo()
                    elif event.key == pygame.K_w or event.key == pygame.K_UP:
                        try_move(-1, 0)
                    elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                        try_move(1, 0)
                    elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                        try_move(0, -1)
                    elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                        try_move(0, 1)

        draw_everything()
        clock.tick(60)

    pygame.quit()


main()