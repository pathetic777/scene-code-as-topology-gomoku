import json
import os
import re
import time
import threading
import urllib.request
import urllib.error
from render_10games_video_en import render_frame_en, AXIS_EN_MAP
import imageio

API_URL = "https://api.deepseek.com/chat/completions"
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "YOUR_API_KEY_HERE")
MODEL_ID = "deepseek-flash"
MODEL_DISPLAY = "DeepSeek-V4.1-Flash-1017 (Thinking ON)"

BOARD_SIZE = 15
COLS = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O']

OUT_DIR = r"d:\work\gomoku_arena"
JSON_PATH = os.path.join(OUT_DIR, "deepseek_thinking_10games_results.json")
VIDEO_EN_PATH = os.path.join(OUT_DIR, "deepseek_thinking_10games_video_EN.mp4")

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
        ("horizontal", 0, 1, False),
        ("vertical", 1, 0, False),
        ("diag_backslash", 1, 1, True),
        ("diag_slash", 1, -1, True),
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
                        idxs = [i for i, v in enumerate(vals) if v == color]
                        is_consecutive = (idxs[-1] - idxs[0] + 1 == cnt)
                        priority_empty = []
                        for i, (cr, cc) in enumerate(cells):
                            if board[cr][cc] == 0 and any(abs(i - si) == 1 for si in idxs):
                                priority_empty.append(rc_to_coord(cr, cc))
                        key = (color, axis, stones)
                        if key not in seen and priority_empty:
                            seen.add(key)
                            chains.append({
                                "color": "black" if color == 1 else "white",
                                "axis": axis,
                                "count": cnt,
                                "isConsecutive": is_consecutive,
                                "nodes": list(stones),
                                "openEnds3D": priority_empty
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
            "- If the opponent has a chain of length 4 or open 3, block its openEndsToExtendOrBlock immediately!\n"
            "- Otherwise extend your longest 3D ray line or play near center (H8).\n"
            "Reply with one short line ending with MOVE: <Col><Row> (e.g., MOVE: H8)."
        )
        user_prompt = f"{code_3d}\n\nYour turn as {color_name}. Output MOVE: <Col><Row>"

    illegal_retries = 0
    for attempt in range(1, 5):
        t0 = time.time()
        payload = {
            "model": MODEL_ID,
            "thinking": {"type": "enabled"},
            "temperature": 0.25 if attempt == 1 else 0.6,
            "max_tokens": 4096,
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
            resp = urllib.request.urlopen(req, timeout=75)
            data = json.loads(resp.read().decode("utf-8"))
            elapsed_ms = int((time.time() - t0) * 1000)
            msg_obj = data.get("choices", [{}])[0].get("message", {})
            raw_text = (msg_obj.get("content") or "").strip()
            reasoning_tokens = data.get("usage", {}).get("completion_tokens_details", {}).get("reasoning_tokens", 0)

            explicit = list(re.finditer(r"MOVE\s*[:=]\s*\*?\*?([A-O])\s*(1[0-5]|[1-9])(?!\d)", raw_text.upper()))
            matches = explicit if explicit else list(re.finditer(r"\b([A-O])\s*(1[0-5]|[1-9])(?!\d)", raw_text.upper()))
            if not matches and msg_obj.get("reasoning_content"):
                # Fallback scan end of reasoning_content if content was empty
                matches = list(re.finditer(r"\b([A-O])\s*(1[0-5]|[1-9])(?!\d)", msg_obj["reasoning_content"][-200:].upper()))

            if matches:
                m = matches[-1]
                parsed = coord_to_rc(f"{m.group(1)}{m.group(2)}")
                if parsed:
                    r, c, coord = parsed
                    if coord not in occupied_set:
                        return r, c, coord, elapsed_ms, illegal_retries, reasoning_tokens, raw_text
                    else:
                        illegal_retries += 1
                        print(f"  [DS-Think G{game_idx} #{ply}] {agent_type} ILLEGAL MOVE on occupied {coord}! Retrying...")
                        user_prompt += f"\nERROR: {coord} is already occupied! Do NOT play any of {sorted(list(occupied_set))}. Pick an EMPTY coordinate."
        except Exception as e:
            print(f"  [DS-Think G{game_idx} #{ply}] Error ({e}), retrying in 2s...")
            time.sleep(2)

    for dist in range(8):
        for dr in range(-dist, dist + 1):
            for dc in range(-dist, dist + 1):
                r, c = 7 + dr, 7 + dc
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == 0:
                    return r, c, rc_to_coord(r, c), 1000, illegal_retries, 0, "Fallback"

def save_checkpoint(results):
    results["games"].sort(key=lambda g: g["gameIndex"])
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

def play_single_game(g_idx, results, results_lock):
    black_agent = "A_2D" if (g_idx % 2 == 1) else "B_3D"
    white_agent = "B_3D" if (g_idx % 2 == 1) else "A_2D"

    board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    moves = []
    occupied_set = set()

    print(f">>> Starting DeepSeek-THINKING Game {g_idx}/10 | Black: {black_agent} vs White: {white_agent}")
    winner_info = None

    for ply in range(1, 39):
        color_num = 1 if (ply % 2 == 1) else 2
        cur_agent = black_agent if color_num == 1 else white_agent

        r, c, coord, ms, retries, r_tokens, raw = call_llm_move(cur_agent, color_num, board, moves, occupied_set, g_idx, ply)
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
            "reasoningTokens": r_tokens,
            "illegalRetries": retries,
            "raw": raw[:120]
        })

        with results_lock:
            if cur_agent == "A_2D":
                results["agentA_IllegalMoves"] += retries
                results["agentA_TotalReasoningTokens"] += r_tokens
            else:
                results["agentB_IllegalMoves"] += retries
                results["agentB_TotalReasoningTokens"] += r_tokens

        print(f"[DS-Think G{g_idx} | Ply {ply:02d}] {cur_agent} ({'B' if color_num==1 else 'W'}) -> {coord} ({ms}ms, think_tok={r_tokens}, retries={retries})")

        win_check = check_winner(board, r, c)
        if win_check:
            winner_info = {"winnerAgent": cur_agent, **win_check}
            print(f"*** DS-THINK GAME {g_idx} FINISHED in {ply} moves! WINNER: {cur_agent} via {win_check['axis']} ***")
            break

    game_record = {
        "gameIndex": g_idx,
        "blackAgent": black_agent,
        "whiteAgent": white_agent,
        "winnerAgent": winner_info["winnerAgent"] if winner_info else "DRAW",
        "winAxis": winner_info["axis"] if winner_info else "Draw (38-Move Equilibrium)",
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

def render_both_videos(data):
    writer_zh = imageio.get_writer(VIDEO_ZH_PATH, fps=15, codec="libx264", quality=8, pixelformat="yuv420p")
    stats_zh = {"model": MODEL_DISPLAY, "a_wins": 0, "b_wins": 0, "draws": 0, "a_diag": 0, "b_diag": 0, "a_err": 0, "b_err": 0}
    total_games = len(data["games"])

    for g in data["games"]:
        g_idx = g["gameIndex"]
        b_agent, w_agent = g["blackAgent"], g["whiteAgent"]
        board = [[0]*BOARD_SIZE for _ in range(BOARD_SIZE)]
        cur_moves = []
        intro = render_frame(g_idx, total_games, b_agent, w_agent, board, cur_moves, stats_zh,
                             banner_text=f"Game {g_idx} / {total_games} Start | Black: {b_agent} vs White: {w_agent}")
        for _ in range(10): writer_zh.append_data(intro)

        for m in g["moves"]:
            if m.get("illegalRetries", 0) > 0:
                if m["agent"] == "A_2D": stats_zh["a_err"] += m["illegalRetries"]
                else: stats_zh["b_err"] += m["illegalRetries"]
            board[m["r"]][m["c"]] = m["color"]
            cur_moves.append(m)
            sf = render_frame(g_idx, total_games, b_agent, w_agent, board, cur_moves, stats_zh)
            for _ in range(4): writer_zh.append_data(sf)

        if g["winnerAgent"] == "A_2D":
            stats_zh["a_wins"] += 1
            if g.get("isDiagonalWin"): stats_zh["a_diag"] += 1
            banner = f"Game {g_idx} Winner: Agent A (2D Matrix) [{g.get('winAxis')}]"
        elif g["winnerAgent"] == "B_3D":
            stats_zh["b_wins"] += 1
            if g.get("isDiagonalWin"): stats_zh["b_diag"] += 1
            banner = f"Game {g_idx} Winner: Agent B (Three.js 3D/4D Code) [{g.get('winAxis')}]"
        else:
            stats_zh["draws"] += 1
            banner = f"Game {g_idx} Result: Agreed Draw ({g['totalMoves']} Moves)"

        ef = render_frame(g_idx, total_games, b_agent, w_agent, board, cur_moves, stats_zh, win_line=g.get("winLine"), banner_text=banner)
        for _ in range(22): writer_zh.append_data(ef)
    writer_zh.close()
    print("Saved Chinese DeepSeek-Thinking video to:", VIDEO_ZH_PATH)

    writer_en = imageio.get_writer(VIDEO_EN_PATH, fps=15, codec="libx264", quality=8, pixelformat="yuv420p")
    stats_en = {"model": MODEL_DISPLAY, "a_wins": 0, "b_wins": 0, "draws": 0, "a_diag": 0, "b_diag": 0, "a_err": 0, "b_err": 0}
    for g in data["games"]:
        g_idx = g["gameIndex"]
        b_agent, w_agent = g["blackAgent"], g["whiteAgent"]
        board = [[0]*BOARD_SIZE for _ in range(BOARD_SIZE)]
        cur_moves = []
        intro = render_frame_en(g_idx, total_games, b_agent, w_agent, board, cur_moves, stats_en,
                                banner_text=f"Game {g_idx}/{total_games} Start | Black: {b_agent} vs White: {w_agent}")
        for _ in range(10): writer_en.append_data(intro)

        for m in g["moves"]:
            if m.get("illegalRetries", 0) > 0:
                if m["agent"] == "A_2D": stats_en["a_err"] += m["illegalRetries"]
                else: stats_en["b_err"] += m["illegalRetries"]
            board[m["r"]][m["c"]] = m["color"]
            cur_moves.append(m)
            sf = render_frame_en(g_idx, total_games, b_agent, w_agent, board, cur_moves, stats_en)
            for _ in range(4): writer_en.append_data(sf)

        axis_en = AXIS_EN_MAP.get(g.get("winAxis"), g.get("winAxis", ""))
        if g["winnerAgent"] == "A_2D":
            stats_en["a_wins"] += 1
            if g.get("isDiagonalWin"): stats_en["a_diag"] += 1
            banner = f"Game {g_idx} Winner: Agent A (2D Matrix) [{axis_en}]"
        elif g["winnerAgent"] == "B_3D":
            stats_en["b_wins"] += 1
            if g.get("isDiagonalWin"): stats_en["b_diag"] += 1
            banner = f"Game {g_idx} Winner: Agent B (Three.js 3D/4D) [{axis_en}]"
        else:
            stats_en["draws"] += 1
            banner = f"Game {g_idx} Result: Agreed Draw ({g['totalMoves']} moves)"

        ef = render_frame_en(g_idx, total_games, b_agent, w_agent, board, cur_moves, stats_en, win_line=g.get("winLine"), banner_text=banner)
        for _ in range(22): writer_en.append_data(ef)
    writer_en.close()
    print("Saved English DeepSeek-Thinking video to:", VIDEO_EN_PATH)

def main():
    results = {
        "model": MODEL_DISPLAY,
        "totalGames": 10,
        "agentA_2D_Wins": 0,
        "agentB_3D_Wins": 0,
        "draws": 0,
        "agentA_DiagWins": 0,
        "agentB_DiagWins": 0,
        "agentA_IllegalMoves": 0,
        "agentB_IllegalMoves": 0,
        "agentA_TotalReasoningTokens": 0,
        "agentB_TotalReasoningTokens": 0,
        "games": []
    }
    results_lock = threading.Lock()

    # Run all 10 games in 2 batches of 5 concurrent threads
    for batch_start in (1, 6):
        threads = []
        for g in range(batch_start, batch_start + 5):
            t = threading.Thread(target=play_single_game, args=(g, results, results_lock))
            t.start()
            threads.append(t)
            time.sleep(0.3)
        for t in threads:
            t.join()

    print("\n================ DEEPSEEK THINKING-ON 10 GAMES COMPLETED ================")
    print(f"Agent A (2D Text) Wins: {results['agentA_2D_Wins']} (Diag: {results['agentA_DiagWins']}, Illegal: {results['agentA_IllegalMoves']}, ThinkTokens: {results['agentA_TotalReasoningTokens']})")
    print(f"Agent B (Three.js 3D/4D) Wins: {results['agentB_3D_Wins']} (Diag: {results['agentB_DiagWins']}, Illegal: {results['agentB_IllegalMoves']}, ThinkTokens: {results['agentB_TotalReasoningTokens']})")
    print(f"Draws: {results['draws']}")

    render_both_videos(results)

if __name__ == "__main__":
    main()
