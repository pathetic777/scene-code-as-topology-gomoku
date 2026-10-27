import json
import os
import re
import time
import threading
import urllib.request
import urllib.error

API_URL = "https://ai.juziai.cc/v1/chat/completions"
API_KEY = os.environ.get("OPENAI_API_KEY", "YOUR_API_KEY_HERE")
MODEL_NAME = "gemini-3.8-flash-high"

BOARD_SIZE = 15
COLS = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O']

OUT_DIR = r"d:\work\gomoku_arena"
JSON_PATH = os.path.join(OUT_DIR, "gomoku_10games_results.json")
PRELOAD_JS_PATH = os.path.join(OUT_DIR, "gomoku_10games_preload.js")

# Global Rate Limiter
rate_lock = threading.Lock()
last_request_time = 0.0
MIN_INTERVAL_SEC = 0.6

def wait_for_rate_slot():
    global last_request_time
    with rate_lock:
        now = time.time()
        wait = MIN_INTERVAL_SEC - (now - last_request_time)
        if wait > 0:
            time.sleep(wait)
        last_request_time = time.time()

def rc_to_coord(r, c):
    return f"{COLS[c]}{r + 1}"

def coord_to_rc(coord_str):
    if not coord_str:
        return None
    m = re.search(r"([A-O])\s*(1[0-5]|[1-9])(?!\d)", coord_str.strip().upper())
    if not m:
        return None
    c = COLS.index(m.group(1))
    r = int(m.group(2)) - 1
    if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
        return r, c, f"{COLS[c]}{r + 1}"
    return None

def check_winner(board, last_r, last_c):
    color = board[last_r][last_c]
    if not color:
        return None
    dirs = [
        ("horizontal (横线)", 0, 1, False),
        ("vertical (竖线)", 1, 0, False),
        ("diag_backslash (正斜线 \\)", 1, 1, True),
        ("diag_slash (反斜线 /)", 1, -1, True),
    ]
    for name, dr, dc, is_diag in dirs:
        line = [{"r": last_r, "c": last_c}]
        for step in range(1, 5):
            nr, nc = last_r + dr * step, last_c + dc * step
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == color:
                line.append({"r": nr, "c": nc})
            else:
                break
        for step in range(1, 5):
            nr, nc = last_r - dr * step, last_c - dc * step
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == color:
                line.insert(0, {"r": nr, "c": nc})
            else:
                break
        if len(line) >= 5:
            return {"winner": color, "axis": name, "isDiagonal": is_diag, "line": line}
    return None

def build_2d_text_representation(board, moves):
    lines = ["   " + " ".join(COLS)]
    for r in range(BOARD_SIZE):
        row_num = f"{r + 1:2d}"
        cells = ["B" if board[r][c] == 1 else ("W" if board[r][c] == 2 else ".") for c in range(BOARD_SIZE)]
        lines.append(f"{row_num} {' '.join(cells)}")
    hist = " ".join([f"{i+1}.{'B' if m['color']==1 else 'W'}({m['coord']})" for i, m in enumerate(moves)])
    return f"/* 2D Text Board (B=Black, W=White, .=Empty) */\n" + "\n".join(lines) + f"\n\nMove History: {hist or 'None (Empty Board)'}"

def extract_3d_spatial_chains(board):
    dirs = [
        ("X_Horizontal (same z)", 0, 1),
        ("Z_Vertical (same x)", 1, 0),
        ("U_Diag_Backslash (same u_diag1 = x-z)", 1, 1),
        ("V_Diag_Slash (same v_diag2 = x+z)", 1, -1),
    ]
    chains = []
    seen = set()

    # Scan all 5-intersection spatial windows along the 4 axes (X, Z, U_diag1, V_diag2)
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            for axis, dr, dc in dirs:
                end_r = r + 4 * dr
                end_c = c + 4 * dc
                if not (0 <= end_r < BOARD_SIZE and 0 <= end_c < BOARD_SIZE):
                    continue
                cells = [(r + k * dr, c + k * dc) for k in range(5)]
                vals = [board[cr][cc] for cr, cc in cells]
                for color in (1, 2):
                    opp = 2 if color == 1 else 1
                    if opp in vals:
                        continue
                    cnt = vals.count(color)
                    if cnt >= 2:
                        stones = tuple(rc_to_coord(cr, cc) for cr, cc in cells if board[cr][cc] == color)
                        empties = [rc_to_coord(cr, cc) for cr, cc in cells if board[cr][cc] == 0]
                        # Check if both outer ends of a 3-chain are open (Open Three)
                        is_consecutive = False
                        idxs = [i for i, v in enumerate(vals) if v == color]
                        if idxs[-1] - idxs[0] + 1 == cnt:
                            is_consecutive = True
                        priority_Empty = []
                        for i, (cr, cc) in enumerate(cells):
                            if board[cr][cc] == 0:
                                # Empty cell directly adjacent to a stone in this 5-window
                                if any(abs(i - si) == 1 for si in idxs):
                                    priority_Empty.append(rc_to_coord(cr, cc))
                        key = (color, axis, stones)
                        if key not in seen and priority_Empty:
                            seen.add(key)
                            chains.append({
                                "color": "black" if color == 1 else "white",
                                "axis": axis,
                                "count": cnt,
                                "isConsecutive": is_consecutive,
                                "nodes": list(stones),
                                "openEnds3D": priority_Empty
                            })

    chains.sort(key=lambda x: (x["count"], x["isConsecutive"]), reverse=True)
    return chains[:14]

def build_threejs_scene_code(board, moves):
    lines = [
        "// === Live Three.js 3D/4D Gomoku Spatial Scene Code ===",
        "// Coordinate System: x=Col(1..15), z=Row(1..15), u_diag1=x-z (constant on \\ diagonal), v_diag2=x+z (constant on / diagonal)",
        "const root = new THREE.Group();"
    ]
    for i, m in enumerate(moves):
        x = m["c"] + 1
        z = m["r"] + 1
        u = x - z
        v = x + z
        wx = m["c"] - 7
        wz = m["r"] - 7
        cname = "black" if m["color"] == 1 else "white"
        lines.append(
            f"spawnStone3D(root, {{ step: {i+1}, color: '{cname}', coord: '{m['coord']}', pos3D: [{wx}, 0.3, {wz}], axes4D: {{ x: {x}, z: {z}, u_diag1: {u}, v_diag2: {v} }} }});"
        )
    chains = extract_3d_spatial_chains(board)
    if chains:
        lines.append("\n// === 3D Spatial Ray Line Meshes (Active Connected Vectors in Scene) ===")
        for ch in chains:
            lines.append(
                f"create3DRayLine(root, {{ color: '{ch['color']}', axis: '{ch['axis']}', length: {ch['count']}, stones: {json.dumps(ch['nodes'])}, openEndsToExtendOrBlock: {json.dumps(ch['openEnds3D'])} }});"
            )
    lines.append("scene.add(root);")
    return "\n".join(lines)

def call_llm_move(agent_type, color_num, board, moves, occupied_set, game_idx, ply):
    color_name = "Black (B)" if color_num == 1 else "White (W)"
    if agent_type == "A_2D":
        text_2d = build_2d_text_representation(board, moves)
        sys_prompt = (
            f"You are playing Gomoku (Five-in-a-Row) on a 15x15 board (Columns A-O, Rows 1-15). You play as {color_name}.\n"
            "Analyze the 2D text board and choose your best move on an EMPTY (.) intersection.\n"
            "Reply ONLY with your chosen coordinate in format MOVE: <Col><Row> (for example: MOVE: H8)."
        )
        user_prompt = f"{text_2d}\n\nYour turn as {color_name}. Output MOVE: <Col><Row>"
    else:
        code_3d = build_threejs_scene_code(board, moves)
        sys_prompt = (
            f"You are an expert Gomoku AI reasoning directly over a Three.js 3D/4D spatial scene graph on a 15x15 board (Columns A-O, Rows 1-15). You play as {color_name}.\n"
            "In this Three.js scene code:\n"
            "1. Each stone has 4D spatial coordinates: x (Col), z (Row), u_diag1 = x - z (stones with equal u_diag1 are collinear on the \\ diagonal!), and v_diag2 = x + z (stones with equal v_diag2 are collinear on the / diagonal!).\n"
            "2. Active connected lines (length >= 2) and their exact open ends (openEndsToExtendOrBlock) are explicitly generated as create3DRayLine() objects in the scene code.\n"
            "Priority Rules:\n"
            "- If you have a chain of length 4 with an open end, play that open end immediately to win!\n"
            "- If the opponent has a chain of length 4 or open 3 (2 open ends), block its openEndsToExtendOrBlock immediately!\n"
            "- Otherwise extend your longest 3D ray line or play near center (H8).\n"
            "Reply with one short line ending with MOVE: <Col><Row> (e.g., MOVE: H8)."
        )
        user_prompt = f"{code_3d}\n\nYour turn as {color_name}. Output MOVE: <Col><Row>"

    illegal_retries = 0
    for attempt in range(1, 5):
        wait_for_rate_slot()
        t0 = time.time()
        payload = {
            "model": MODEL_NAME,
            "temperature": 0.2 if attempt == 1 else 0.6,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        try:
            req = urllib.request.Request(
                API_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0"
                }
            )
            resp = urllib.request.urlopen(req, timeout=65)
            data = json.loads(resp.read().decode("utf-8"))
            elapsed_ms = int((time.time() - t0) * 1000)
            raw_text = (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()

            explicit = list(re.finditer(r"MOVE\s*[:=]\s*\*?\*?([A-O])\s*(1[0-5]|[1-9])(?!\d)", raw_text.upper()))
            matches = explicit if explicit else list(re.finditer(r"\b([A-O])\s*(1[0-5]|[1-9])(?!\d)", raw_text.upper()))
            if matches:
                m = matches[-1]
                parsed = coord_to_rc(f"{m.group(1)}{m.group(2)}")
                if parsed:
                    r, c, coord = parsed
                    if coord not in occupied_set:
                        return r, c, coord, elapsed_ms, illegal_retries, raw_text
                    else:
                        illegal_retries += 1
                        print(f"  [G{game_idx} #{ply}] {agent_type} ILLEGAL MOVE on occupied {coord}! Retrying...")
                        user_prompt += f"\nERROR: {coord} is already occupied! Do NOT play any of {sorted(list(occupied_set))}. Pick an EMPTY coordinate."
            else:
                print(f"  [G{game_idx} #{ply}] {agent_type} unparseable output: {raw_text!r}")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"  [G{game_idx} #{ply}] HTTP 429 Rate Limit! Backing off 15s...")
                time.sleep(15)
            else:
                print(f"  [G{game_idx} #{ply}] HTTP {e.code} error, backing off 5s...")
                time.sleep(5)
        except Exception as e:
            print(f"  [G{game_idx} #{ply}] Network error ({e}), backing off 5s...")
            time.sleep(5)

    # Fallback if 4 attempts failed
    for dist in range(8):
        for dr in range(-dist, dist + 1):
            for dc in range(-dist, dist + 1):
                r, c = 7 + dr, 7 + dc
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == 0:
                    return r, c, rc_to_coord(r, c), 1000, illegal_retries, "Fallback"

def save_checkpoint(results):
    results["games"].sort(key=lambda g: g["gameIndex"])
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    with open(PRELOAD_JS_PATH, "w", encoding="utf-8") as f:
        f.write("window.PRELOADED_10GAMES_DATA = " + json.dumps(results, ensure_ascii=False, indent=2) + ";\n")

def play_single_game(g_idx, results, results_lock):
    # Odd games: A_2D is Black; Even games: B_3D is Black
    black_agent = "A_2D" if (g_idx % 2 == 1) else "B_3D"
    white_agent = "B_3D" if (g_idx % 2 == 1) else "A_2D"

    board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    moves = []
    occupied_set = set()

    print(f"\n>>> Starting Game {g_idx}/10 | Black: {black_agent} vs White: {white_agent} (Empty Board)")
    winner_info = None

    for ply in range(1, 75):
        color_num = 1 if (ply % 2 == 1) else 2
        cur_agent = black_agent if color_num == 1 else white_agent

        r, c, coord, ms, retries, raw = call_llm_move(cur_agent, color_num, board, moves, occupied_set, g_idx, ply)
        board[r][c] = color_num
        occupied_set.add(coord)

        moves.append({
            "ply": ply,
            "agent": cur_agent,
            "color": color_num,
            "r": r,
            "c": c,
            "coord": coord,
            "ms": ms,
            "illegalRetries": retries,
            "raw": raw[:120]
        })

        with results_lock:
            if cur_agent == "A_2D":
                results["agentA_IllegalMoves"] += retries
            else:
                results["agentB_IllegalMoves"] += retries

        print(f"[Game {g_idx} | Ply {ply:02d}] {cur_agent} ({'B' if color_num==1 else 'W'}) -> {coord} ({ms}ms, retries={retries})")

        win_check = check_winner(board, r, c)
        if win_check:
            winner_info = {"winnerAgent": cur_agent, **win_check}
            print(f"*** GAME {g_idx} FINISHED in {ply} moves! WINNER: {cur_agent} via {win_check['axis']} ***")
            break

    game_record = {
        "gameIndex": g_idx,
        "blackAgent": black_agent,
        "whiteAgent": white_agent,
        "winnerAgent": winner_info["winnerAgent"] if winner_info else "DRAW",
        "winAxis": winner_info["axis"] if winner_info else "None",
        "isDiagonalWin": winner_info["isDiagonal"] if winner_info else False,
        "winLine": winner_info["line"] if winner_info else [],
        "totalMoves": len(moves),
        "moves": moves
    }

    with results_lock:
        if winner_info:
            if winner_info["winnerAgent"] == "A_2D":
                results["agentA_2D_Wins"] += 1
                if winner_info["isDiagonal"]:
                    results["agentA_DiagWins"] += 1
            else:
                results["agentB_3D_Wins"] += 1
                if winner_info["isDiagonal"]:
                    results["agentB_DiagWins"] += 1
        else:
            results["draws"] += 1
        results["games"].append(game_record)
        save_checkpoint(results)

def main():
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            results = json.load(f)
        results["model"] = MODEL_NAME
    else:
        results = {
            "model": MODEL_NAME,
            "totalGames": 10,
            "agentA_2D_Wins": 0,
            "agentB_3D_Wins": 0,
            "draws": 0,
            "agentA_DiagWins": 0,
            "agentB_DiagWins": 0,
            "agentA_IllegalMoves": 0,
            "agentB_IllegalMoves": 0,
            "games": []
        }

    done_indices = {g["gameIndex"] for g in results.get("games", [])}
    remaining = [g for g in range(1, 11) if g not in done_indices]
    print(f"Loaded {len(done_indices)} completed games ({sorted(list(done_indices))}). Remaining games: {remaining}")

    results_lock = threading.Lock()

    # Run remaining games concurrently
    for i in range(0, len(remaining), 6):
        batch = remaining[i:i+6]
        threads = []
        for g in batch:
            t = threading.Thread(target=play_single_game, args=(g, results, results_lock))
            t.start()
            threads.append(t)
            time.sleep(0.8)
        for t in threads:
            t.join()

    print("\n================ ALL 10 GAMES COMPLETED ================")
    print(f"Agent A (2D Text) Wins: {results['agentA_2D_Wins']} (Diagonal: {results['agentA_DiagWins']}, Illegal Moves: {results['agentA_IllegalMoves']})")
    print(f"Agent B (Three.js 3D/4D) Wins: {results['agentB_3D_Wins']} (Diagonal: {results['agentB_DiagWins']}, Illegal Moves: {results['agentB_IllegalMoves']})")
    print(f"Draws: {results['draws']}")

if __name__ == "__main__":
    main()
