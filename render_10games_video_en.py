import json
import os
import numpy as np
from PIL import Image, ImageDraw
import imageio
from render_10games_video import (
    OUT_DIR, JSON_PATH, BOARD_SIZE, COLS,
    get_font, project_3d, coord_to_rc, build_2d_text, build_threejs_lines
)

VIDEO_EN_PATH = os.path.join(OUT_DIR, "gomoku_10games_arena_video_EN.mp4")

FONT_TITLE = get_font(20, mono=True, bold=True)
FONT_SUB = get_font(14, mono=True, bold=False)
FONT_H2 = get_font(16, mono=True, bold=True)
FONT_SCORE = get_font(44, mono=True, bold=True)
FONT_MONO = get_font(13, mono=True, bold=False)
FONT_LABEL = get_font(14, mono=True, bold=True)
FONT_BANNER = get_font(26, mono=True, bold=True)

AXIS_EN_MAP = {
    "diag_slash (反斜线 /)": "Slash Diagonal (/)",
    "diag_backslash (正斜线 \\)": "Backslash Diagonal (\\)",
    "vertical (竖线)": "Vertical Axis (|)",
    "horizontal (横线)": "Horizontal Axis (-)",
    "Draw (Stalemate / Agreed Draw)": "Agreed Draw (Late-Game Equilibrium)"
}

def render_frame_en(game_idx, total_games, black_agent, white_agent, board, moves, stats, win_line=None, banner_text=None):
    img = Image.new("RGB", (1920, 1080), (16, 18, 22))
    draw = ImageDraw.Draw(img)

    # Left Sidebar Panel
    draw.rectangle([16, 16, 736, 1064], fill=(28, 28, 30), outline=(58, 58, 62), width=2)
    draw.text((34, 28), "Dual-Agent Spatial Representation Arena (10-Game Pilot)", fill=(255, 255, 255), font=FONT_TITLE)
    draw.text((34, 58), f"Base Model: {stats['model']} | 15x15 Pure Empty Board", fill=(156, 204, 101), font=FONT_SUB)

    # Scoreboard Box
    draw.rectangle([34, 90, 718, 224], fill=(18, 18, 20), outline=(68, 68, 72), width=2)
    draw.text((48, 102), "Agent A: 2D Matrix Baseline", fill=(129, 212, 250), font=FONT_H2)
    draw.text((55, 132), str(stats["a_wins"]), fill=(129, 212, 250), font=FONT_SCORE)
    draw.text((48, 192), f"Diag Wins: {stats['a_diag']} | Illegal: {stats['a_err']}", fill=(180, 180, 185), font=FONT_MONO)

    draw.text((285, 112), f"Game {game_idx} / {total_games}", fill=(255, 213, 79), font=FONT_H2)
    draw.text((270, 142), f"Ply: #{len(moves)} | Draws: {stats.get('draws', 0)}", fill=(230, 230, 230), font=FONT_SUB)
    b_label = "Agent A(2D)" if black_agent == "A_2D" else "Agent B(3D)"
    w_label = "Agent A(2D)" if white_agent == "A_2D" else "Agent B(3D)"
    draw.text((248, 185), f"Black: {b_label} | White: {w_label}", fill=(200, 200, 200), font=FONT_MONO)

    draw.text((445, 102), "Agent B: Three.js 3D/4D Code", fill=(255, 183, 77), font=FONT_H2)
    draw.text((635, 132), str(stats["b_wins"]), fill=(255, 183, 77), font=FONT_SCORE)
    draw.text((470, 192), f"Diag Wins: {stats['b_diag']} | Illegal: {stats['b_err']}", fill=(180, 180, 185), font=FONT_MONO)

    # Agent A 2D Text Box
    last_a = next((m for m in reversed(moves) if m["agent"] == "A_2D"), None)
    last_a_str = f"{last_a['coord']} ({last_a['ms']}ms)" if last_a else "--"
    draw.text((34, 236), f"Agent A (Baseline: 2D Matrix Input) | Last: {last_a_str}", fill=(129, 212, 250), font=FONT_H2)
    draw.rectangle([34, 264, 718, 595], fill=(14, 14, 16), outline=(55, 55, 60), width=1)
    a_lines = build_2d_text(board, moves)
    for idx, line in enumerate(a_lines[:18]):
        draw.text((46, 272 + idx * 17), line[:76], fill=(207, 216, 220), font=FONT_MONO)

    # Agent B Three.js 3D/4D Code Box
    last_b = next((m for m in reversed(moves) if m["agent"] == "B_3D"), None)
    last_b_str = f"{last_b['coord']} ({last_b['ms']}ms)" if last_b else "--"
    draw.text((34, 608), f"Agent B (Ours: Three.js 3D/4D Scene Code) | Last: {last_b_str}", fill=(255, 183, 77), font=FONT_H2)
    draw.rectangle([34, 636, 718, 1046], fill=(14, 14, 16), outline=(55, 55, 60), width=1)
    b_lines, chains = build_threejs_lines(board, moves)
    for idx, line in enumerate(b_lines[:22]):
        draw.text((44, 646 + idx * 17), line[:78], fill=(255, 224, 178), font=FONT_MONO)

    # Right Viewport: 3D Three.js Perspective Board
    rim_pts = [project_3d(x, -0.25, z)[:2] for x, z in [(-8.4, -8.4), (8.4, -8.4), (8.4, 8.4), (-8.4, 8.4)]]
    rim_bot = [project_3d(x, -0.85, z)[:2] for x, z in [(-8.4, 8.4), (8.4, 8.4)]]
    draw.polygon([rim_pts[3], rim_pts[2], rim_bot[1], rim_bot[0]], fill=(62, 39, 35))
    draw.polygon(rim_pts, fill=(93, 64, 55), outline=(45, 28, 22))

    top_pts = [project_3d(x, 0.0, z)[:2] for x, z in [(-7.8, -7.8), (7.8, -7.8), (7.8, 7.8), (-7.8, 7.8)]]
    draw.polygon(top_pts, fill=(184, 134, 75), outline=(78, 52, 46))

    for i in range(-7, 8):
        p1 = project_3d(-7, 0.02, i)[:2]
        p2 = project_3d(7, 0.02, i)[:2]
        draw.line([p1, p2], fill=(43, 29, 14), width=2)
        q1 = project_3d(i, 0.02, -7)[:2]
        q2 = project_3d(i, 0.02, 7)[:2]
        draw.line([q1, q2], fill=(43, 29, 14), width=2)

    for i in range(15):
        pos = i - 7
        tx, ty, _ = project_3d(pos, 0.05, -7.55)
        draw.text((tx - 5, ty - 8), COLS[i], fill=(255, 224, 130), font=FONT_LABEL)
        bx, by, _ = project_3d(pos, 0.05, 7.55)
        draw.text((bx - 5, by - 8), COLS[i], fill=(255, 224, 130), font=FONT_LABEL)
        lx, ly, _ = project_3d(-7.58, 0.05, pos)
        draw.text((lx - 10, ly - 8), str(i + 1), fill=(129, 212, 250), font=FONT_LABEL)
        rx, ry, _ = project_3d(7.58, 0.05, pos)
        draw.text((rx - 6, ry - 8), str(i + 1), fill=(129, 212, 250), font=FONT_LABEL)

    for sx, sz in [(-4,-4), (4,-4), (0,0), (-4,4), (4,4)]:
        px, py, _ = project_3d(sx, 0.03, sz)
        draw.ellipse([px-4, py-3, px+4, py+3], fill=(30, 20, 10))

    for ch in chains:
        if len(ch["nodes"]) >= 2:
            r1, c1 = coord_to_rc(ch["nodes"][0])
            r2, c2 = coord_to_rc(ch["nodes"][-1])
            p1 = project_3d(c1 - 7, 0.35, r1 - 7)[:2]
            p2 = project_3d(c2 - 7, 0.35, r2 - 7)[:2]
            col_rgb = (255, 167, 38) if ch["color"] == "black" else (0, 230, 118)
            draw.line([p1, p2], fill=col_rgb, width=3)

    sorted_moves = sorted(moves, key=lambda m: (m["r"], m["c"]))
    for m in sorted_moves:
        wx, wz = m["c"] - 7, m["r"] - 7
        sx, sy, cz = project_3d(wx, 0.22, wz)
        rad_x = max(10, int(390 / cz))
        rad_y = max(8, int(305 / cz))
        draw.ellipse([sx - rad_x + 3, sy - rad_y + 5, sx + rad_x + 3, sy + rad_y + 5], fill=(65, 45, 25))
        if m["color"] == 1:
            draw.ellipse([sx - rad_x, sy - rad_y, sx + rad_x, sy + rad_y], fill=(24, 24, 28), outline=(10, 10, 12))
            draw.ellipse([sx - rad_x//2, sy - rad_y//2, sx - 2, sy - 2], fill=(95, 95, 105))
        else:
            draw.ellipse([sx - rad_x, sy - rad_y, sx + rad_x, sy + rad_y], fill=(242, 242, 246), outline=(160, 160, 170))
            draw.ellipse([sx - rad_x//2, sy - rad_y//2, sx - 2, sy - 2], fill=(255, 255, 255))
        if moves and m["ply"] == moves[-1]["ply"]:
            draw.ellipse([sx - rad_x - 4, sy - rad_y - 3, sx + rad_x + 4, sy + rad_y + 3], outline=(0, 229, 255), width=3)

    if win_line and len(win_line) >= 2:
        f_node, l_node = win_line[0], win_line[-1]
        p1 = project_3d(f_node["c"] - 7, 0.45, f_node["r"] - 7)[:2]
        p2 = project_3d(l_node["c"] - 7, 0.45, l_node["r"] - 7)[:2]
        draw.line([p1, p2], fill=(255, 23, 68), width=8)
        draw.line([p1, p2], fill=(255, 235, 59), width=3)

    draw.rectangle([1530, 28, 1895, 128], fill=(22, 22, 26), outline=(80, 80, 88), width=1)
    draw.text((1546, 38), "● REC 3D WebGL Spatial Viewport", fill=(255, 82, 82), font=FONT_SUB)
    draw.text((1546, 65), "4D Diagonal Axes: u=x-z | v=x+z", fill=(129, 212, 250), font=FONT_MONO)
    draw.text((1546, 92), f"Active 3D Ray Vectors: {len(chains)}", fill=(255, 183, 77), font=FONT_MONO)

    if banner_text:
        draw.rectangle([800, 475, 1875, 575], fill=(15, 15, 18), outline=(255, 202, 40), width=3)
        draw.text((825, 510), banner_text, fill=(255, 202, 40), font=FONT_BANNER)

    return np.array(img)

def generate_en_video():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    writer = imageio.get_writer(VIDEO_EN_PATH, fps=15, codec="libx264", quality=8, pixelformat="yuv420p")
    stats = {"model": data.get("model", "gemini-3.8-flash-high"), "a_wins": 0, "b_wins": 0, "draws": 0, "a_diag": 0, "b_diag": 0, "a_err": 0, "b_err": 0}
    total_games = len(data["games"])

    for g in data["games"]:
        g_idx = g["gameIndex"]
        b_agent, w_agent = g["blackAgent"], g["whiteAgent"]
        board = [[0]*BOARD_SIZE for _ in range(BOARD_SIZE)]
        cur_moves = []
        intro = render_frame_en(g_idx, total_games, b_agent, w_agent, board, cur_moves, stats,
                                banner_text=f"Game {g_idx}/{total_games} Start | Black: {b_agent} vs White: {w_agent}")
        for _ in range(10):
            writer.append_data(intro)

        for m in g["moves"]:
            board[m["r"]][m["c"]] = m["color"]
            cur_moves.append(m)
            step_f = render_frame_en(g_idx, total_games, b_agent, w_agent, board, cur_moves, stats)
            for _ in range(4):
                writer.append_data(step_f)

        axis_en = AXIS_EN_MAP.get(g.get("winAxis"), g.get("winAxis", ""))
        if g["winnerAgent"] == "A_2D":
            stats["a_wins"] += 1
            if g.get("isDiagonalWin"): stats["a_diag"] += 1
            banner = f"Game {g_idx} Winner: Agent A (2D Matrix) [{axis_en}]"
        elif g["winnerAgent"] == "B_3D":
            stats["b_wins"] += 1
            if g.get("isDiagonalWin"): stats["b_diag"] += 1
            banner = f"Game {g_idx} Winner: Agent B (Three.js 3D/4D) [{axis_en}]"
        else:
            stats["draws"] += 1
            banner = f"Game {g_idx} Result: Agreed Draw ({g['totalMoves']} moves equilibrium)"

        end_f = render_frame_en(g_idx, total_games, b_agent, w_agent, board, cur_moves, stats, win_line=g.get("winLine"), banner_text=banner)
        for _ in range(22):
            writer.append_data(end_f)

    writer.close()
    print("Saved English video to:", VIDEO_EN_PATH)

if __name__ == "__main__":
    generate_en_video()
