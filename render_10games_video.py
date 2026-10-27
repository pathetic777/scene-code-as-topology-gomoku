import json
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio

OUT_DIR = r"d:\work\gomoku_arena"
JSON_PATH = os.path.join(OUT_DIR, "gomoku_10games_results.json")
VIDEO_PATH = os.path.join(OUT_DIR, "gomoku_10games_arena_video.mp4")

BOARD_SIZE = 15
COLS = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O']

def get_font(size, mono=False, bold=False):
    candidates = []
    if mono:
        candidates = [
            r"C:\Windows\Fonts\consolab.ttf" if bold else r"C:\Windows\Fonts\consola.ttf",
            r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc",
        ]
    else:
        candidates = [
            r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
        ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

FONT_TITLE = get_font(22, mono=False, bold=True)
FONT_SUB = get_font(15, mono=True, bold=False)
FONT_H2 = get_font(17, mono=False, bold=True)
FONT_SCORE = get_font(44, mono=True, bold=True)
FONT_MONO = get_font(13, mono=True, bold=False)
FONT_LABEL = get_font(14, mono=True, bold=True)
FONT_BANNER = get_font(30, mono=False, bold=True)

# 3D Perspective Projection matching Three.js camera(0, 18.5, 13.5) looking at (0, 0, 0.4)
def project_3d(x, y, z, vp_cx=1330, vp_cy=535, scale=920.0):
    cam_x, cam_y, cam_z = 0.0, 17.8, 13.2
    look_x, look_y, look_z = 0.0, 0.0, 0.35

    # Forward vector
    fx, fy, fz = look_x - cam_x, look_y - cam_y, look_z - cam_z
    fl = math.sqrt(fx*fx + fy*fy + fz*fz)
    fx, fy, fz = fx/fl, fy/fl, fz/fl

    # Right vector (cross(f, up=(0,1,0)))
    rx, ry, rz = -fz, 0.0, fx
    rl = math.sqrt(rx*rx + ry*ry + rz*rz)
    rx, ry, rz = rx/rl, ry/rl, rz/rl

    # Up vector (cross(r, f))
    ux = ry*fz - rz*fy
    uy = rz*fx - rx*fz
    uz = rx*fy - ry*fx

    dx, dy, dz = x - cam_x, y - cam_y, z - cam_z
    cx = dx*rx + dy*ry + dz*rz
    cy = dx*ux + dy*uy + dz*uz
    cz = dx*fx + dy*fy + dz*fz
    if cz <= 0.1:
        cz = 0.1

    sx = vp_cx + (cx / cz) * scale
    sy = vp_cy - (cy / cz) * scale
    return sx, sy, cz

def rc_to_coord(r, c):
    return f"{COLS[c]}{r + 1}"

def coord_to_rc(coord_str):
    c = COLS.index(coord_str[0])
    r = int(coord_str[1:]) - 1
    return r, c

def build_2d_text(board, moves):
    lines = ["   " + " ".join(COLS)]
    for r in range(BOARD_SIZE):
        row_num = f"{r + 1:2d}"
        cells = ["B" if board[r][c] == 1 else ("W" if board[r][c] == 2 else ".") for c in range(BOARD_SIZE)]
        lines.append(f"{row_num} {' '.join(cells)}")
    hist = " ".join([f"{i+1}.{'B' if m['color']==1 else 'W'}({m['coord']})" for i, m in enumerate(moves[-10:])])
    return lines + [f"Moves: {hist or 'Empty'}"]

def extract_chains(board):
    dirs = [
        ("X_Horiz", 0, 1),
        ("Z_Vert", 1, 0),
        ("U_Diag1(\\)", 1, 1),
        ("V_Diag2(/)", 1, -1),
    ]
    chains = []
    seen = set()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            for axis, dr, dc in dirs:
                er, ec = r + 4*dr, c + 4*dc
                if not (0 <= er < BOARD_SIZE and 0 <= ec < BOARD_SIZE):
                    continue
                cells = [(r + k*dr, c + k*dc) for k in range(5)]
                vals = [board[cr][cc] for cr, cc in cells]
                for color in (1, 2):
                    opp = 2 if color == 1 else 1
                    if opp in vals:
                        continue
                    cnt = vals.count(color)
                    if cnt >= 2:
                        stones = tuple(rc_to_coord(cr, cc) for cr, cc in cells if board[cr][cc] == color)
                        idxs = [i for i, v in enumerate(vals) if v == color]
                        p_empty = [rc_to_coord(cr, cc) for i, (cr, cc) in enumerate(cells) if board[cr][cc] == 0 and any(abs(i-si)==1 for si in idxs)]
                        key = (color, axis, stones)
                        if key not in seen and p_empty:
                            seen.add(key)
                            chains.append({
                                "color": "black" if color == 1 else "white",
                                "axis": axis,
                                "count": cnt,
                                "nodes": list(stones),
                                "open": p_empty
                            })
    chains.sort(key=lambda x: x["count"], reverse=True)
    return chains[:10]

def build_threejs_lines(board, moves):
    lines = [
        "// === Live Three.js 3D/4D Spatial Scene Code ===",
        "const root = new THREE.Group();"
    ]
    for m in moves[-11:]:
        x, z = m["c"] + 1, m["r"] + 1
        u, v = x - z, x + z
        wx, wz = m["c"] - 7, m["r"] - 7
        cname = "black" if m["color"] == 1 else "white"
        lines.append(
            f"spawnStone3D(root, {{step:{m['ply']}, color:'{cname}', coord:'{m['coord']}', pos3D:[{wx},0.3,{wz}], axes4D:{{x:{x},z:{z},u_diag1:{u},v_diag2:{v}}}}});"
        )
    chains = extract_chains(board)
    if chains:
        lines.append("// === 3D Spatial Ray Line Objects ===")
        for ch in chains[:7]:
            lines.append(
                f"create3DRayLine(root, {{color:'{ch['color']}', axis:'{ch['axis']}', len:{ch['count']}, nodes:{json.dumps(ch['nodes'])}, open3D:{json.dumps(ch['open'])}}});"
            )
    lines.append("scene.add(root);")
    return lines, chains

def render_frame(game_idx, total_games, black_agent, white_agent, board, moves, stats, win_line=None, banner_text=None):
    img = Image.new("RGB", (1920, 1080), (16, 18, 22))
    draw = ImageDraw.Draw(img)

    # Left Sidebar Panel
    draw.rectangle([16, 16, 736, 1064], fill=(28, 28, 30), outline=(58, 58, 62), width=2)
    draw.text((34, 28), "五子棋双 Agent 空间表征博弈实验台 (10局实机录屏)", fill=(255, 255, 255), font=FONT_TITLE)
    draw.text((34, 60), f"Model: {stats['model']} | Pure Empty Board | 15x15 Grid", fill=(156, 204, 101), font=FONT_SUB)

    # Scoreboard Box
    draw.rectangle([34, 90, 718, 224], fill=(18, 18, 20), outline=(68, 68, 72), width=2)
    draw.text((50, 102), "Agent A: 2D 文本矩阵派", fill=(129, 212, 250), font=FONT_H2)
    draw.text((55, 132), str(stats["a_wins"]), fill=(129, 212, 250), font=FONT_SCORE)
    draw.text((50, 192), f"斜线胜: {stats['a_diag']} | 空间幻觉: {stats['a_err']}", fill=(180, 180, 185), font=FONT_MONO)

    draw.text((295, 115), f"第 {game_idx} / {total_games} 局", fill=(255, 213, 79), font=FONT_H2)
    draw.text((275, 145), f"手数: #{len(moves)} | 和局: {stats.get('draws', 0)}", fill=(230, 230, 230), font=FONT_SUB)
    b_label = "Agent A(2D)" if black_agent == "A_2D" else "Agent B(3D)"
    w_label = "Agent A(2D)" if white_agent == "A_2D" else "Agent B(3D)"
    draw.text((255, 185), f"执黑: {b_label} | 执白: {w_label}", fill=(200, 200, 200), font=FONT_MONO)

    draw.text((465, 102), "Agent B: Three.js 3D/4D派", fill=(255, 183, 77), font=FONT_H2)
    draw.text((635, 132), str(stats["b_wins"]), fill=(255, 183, 77), font=FONT_SCORE)
    draw.text((485, 192), f"斜线胜: {stats['b_diag']} | 空间幻觉: {stats['b_err']}", fill=(180, 180, 185), font=FONT_MONO)

    # Agent A 2D Text Box
    last_a = next((m for m in reversed(moves) if m["agent"] == "A_2D"), None)
    last_a_str = f"{last_a['coord']} ({last_a['ms']}ms)" if last_a else "--"
    draw.text((34, 236), f"Agent A (Baseline: 2D 文本输入) | 最新落子: {last_a_str}", fill=(129, 212, 250), font=FONT_H2)
    draw.rectangle([34, 264, 718, 595], fill=(14, 14, 16), outline=(55, 55, 60), width=1)
    a_lines = build_2d_text(board, moves)
    for idx, line in enumerate(a_lines[:18]):
        draw.text((46, 272 + idx * 17), line[:76], fill=(207, 216, 220), font=FONT_MONO)

    # Agent B Three.js 3D/4D Code Box
    last_b = next((m for m in reversed(moves) if m["agent"] == "B_3D"), None)
    last_b_str = f"{last_b['coord']} ({last_b['ms']}ms)" if last_b else "--"
    draw.text((34, 608), f"Agent B (Ours: Three.js 3D/4D 空间代码) | 最新落子: {last_b_str}", fill=(255, 183, 77), font=FONT_H2)
    draw.rectangle([34, 636, 718, 1046], fill=(14, 14, 16), outline=(55, 55, 60), width=1)
    b_lines, chains = build_threejs_lines(board, moves)
    for idx, line in enumerate(b_lines[:22]):
        draw.text((44, 646 + idx * 17), line[:78], fill=(255, 224, 178), font=FONT_MONO)

    # Right Viewport: 3D Three.js Perspective Board
    # Draw 3D outer rim & wooden top face
    rim_pts = [project_3d(x, -0.25, z)[:2] for x, z in [(-8.4, -8.4), (8.4, -8.4), (8.4, 8.4), (-8.4, 8.4)]]
    rim_bot = [project_3d(x, -0.85, z)[:2] for x, z in [(-8.4, 8.4), (8.4, 8.4)]]
    draw.polygon([rim_pts[3], rim_pts[2], rim_bot[1], rim_bot[0]], fill=(62, 39, 35))
    draw.polygon(rim_pts, fill=(93, 64, 55), outline=(45, 28, 22))

    top_pts = [project_3d(x, 0.0, z)[:2] for x, z in [(-7.8, -7.8), (7.8, -7.8), (7.8, 7.8), (-7.8, 7.8)]]
    draw.polygon(top_pts, fill=(184, 134, 75), outline=(78, 52, 46))

    # 15x15 Grid lines
    for i in range(-7, 8):
        p1 = project_3d(-7, 0.02, i)[:2]
        p2 = project_3d(7, 0.02, i)[:2]
        draw.line([p1, p2], fill=(43, 29, 14), width=2)

        q1 = project_3d(i, 0.02, -7)[:2]
        q2 = project_3d(i, 0.02, 7)[:2]
        draw.line([q1, q2], fill=(43, 29, 14), width=2)

    # Coordinate Labels A-O and 1-15
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

    # Star points
    for sx, sz in [(-4,-4), (4,-4), (0,0), (-4,4), (4,4)]:
        px, py, _ = project_3d(sx, 0.03, sz)
        draw.ellipse([px-4, py-3, px+4, py+3], fill=(30, 20, 10))

    # Draw 3D Ray Topology Lines (Active chains)
    for ch in chains:
        if len(ch["nodes"]) >= 2:
            r1, c1 = coord_to_rc(ch["nodes"][0])
            r2, c2 = coord_to_rc(ch["nodes"][-1])
            p1 = project_3d(c1 - 7, 0.35, r1 - 7)[:2]
            p2 = project_3d(c2 - 7, 0.35, r2 - 7)[:2]
            col_rgb = (255, 167, 38) if ch["color"] == "black" else (0, 230, 118)
            draw.line([p1, p2], fill=col_rgb, width=3)

    # Sort stones back-to-front by Z for painters algorithm
    sorted_moves = sorted(moves, key=lambda m: (m["r"], m["c"]))
    for m in sorted_moves:
        wx, wz = m["c"] - 7, m["r"] - 7
        sx, sy, cz = project_3d(wx, 0.22, wz)
        rad_x = max(10, int(390 / cz))
        rad_y = max(8, int(305 / cz))

        # Drop shadow
        draw.ellipse([sx - rad_x + 3, sy - rad_y + 5, sx + rad_x + 3, sy + rad_y + 5], fill=(65, 45, 25))

        if m["color"] == 1:
            # 3D Black Stone + Specular Highlight
            draw.ellipse([sx - rad_x, sy - rad_y, sx + rad_x, sy + rad_y], fill=(24, 24, 28), outline=(10, 10, 12))
            draw.ellipse([sx - rad_x//2, sy - rad_y//2, sx - 2, sy - 2], fill=(95, 95, 105))
        else:
            # 3D White Stone + Specular Highlight
            draw.ellipse([sx - rad_x, sy - rad_y, sx + rad_x, sy + rad_y], fill=(242, 242, 246), outline=(160, 160, 170))
            draw.ellipse([sx - rad_x//2, sy - rad_y//2, sx - 2, sy - 2], fill=(255, 255, 255))

        # Highlight latest move ring
        if moves and m["ply"] == moves[-1]["ply"]:
            draw.ellipse([sx - rad_x - 4, sy - rad_y - 3, sx + rad_x + 4, sy + rad_y + 3], outline=(0, 229, 255), width=3)

    # Draw winning 5-in-a-row 3D Laser Beam
    if win_line and len(win_line) >= 2:
        f_node, l_node = win_line[0], win_line[-1]
        p1 = project_3d(f_node["c"] - 7, 0.45, f_node["r"] - 7)[:2]
        p2 = project_3d(l_node["c"] - 7, 0.45, l_node["r"] - 7)[:2]
        draw.line([p1, p2], fill=(255, 23, 68), width=8)
        draw.line([p1, p2], fill=(255, 235, 59), width=3)

    # Top-Right 3D Viewport Badge
    draw.rectangle([1560, 28, 1895, 128], fill=(22, 22, 26), outline=(80, 80, 88), width=1)
    draw.text((1576, 38), "● REC 3D WebGL 实时空间视口", fill=(255, 82, 82), font=FONT_SUB)
    draw.text((1576, 65), f"四维斜线轴: u = x-z | v = x+z", fill=(129, 212, 250), font=FONT_MONO)
    draw.text((1576, 92), f"激活 3D 连线向量: {len(chains)} 条", fill=(255, 183, 77), font=FONT_MONO)

    if banner_text:
        draw.rectangle([820, 475, 1840, 575], fill=(15, 15, 18), outline=(255, 202, 40), width=3)
        draw.text((850, 508), banner_text, fill=(255, 202, 40), font=FONT_BANNER)

    return np.array(img)

def generate_video():
    if not os.path.exists(JSON_PATH):
        print("JSON results not found!")
        return
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    writer = imageio.get_writer(VIDEO_PATH, fps=15, codec="libx264", quality=8, pixelformat="yuv420p")
    stats = {
        "model": data.get("model", "gemini-3.8-flash-high"),
        "a_wins": 0,
        "b_wins": 0,
        "draws": 0,
        "a_diag": 0,
        "b_diag": 0,
        "a_err": 0,
        "b_err": 0,
    }

    total_games = len(data["games"])
    for g in data["games"]:
        g_idx = g["gameIndex"]
        b_agent = g["blackAgent"]
        w_agent = g["whiteAgent"]
        board = [[0]*BOARD_SIZE for _ in range(BOARD_SIZE)]
        cur_moves = []

        # Intro frames for game
        intro_frame = render_frame(
            g_idx, total_games, b_agent, w_agent, board, cur_moves, stats,
            banner_text=f"第 {g_idx} / {total_games} 局开始 | 执黑: {b_agent} vs 执白: {w_agent}"
        )
        for _ in range(10):
            writer.append_data(intro_frame)

        for m in g["moves"]:
            if m.get("illegalRetries", 0) > 0:
                if m["agent"] == "A_2D":
                    stats["a_err"] += m["illegalRetries"]
                else:
                    stats["b_err"] += m["illegalRetries"]
            board[m["r"]][m["c"]] = m["color"]
            cur_moves.append(m)
            step_frame = render_frame(g_idx, total_games, b_agent, w_agent, board, cur_moves, stats)
            for _ in range(4):
                writer.append_data(step_frame)

        if g["winnerAgent"] == "A_2D":
            stats["a_wins"] += 1
            if g.get("isDiagonalWin"):
                stats["a_diag"] += 1
            banner = f"第 {g_idx} 局获胜: Agent A (2D文本派) [{g.get('winAxis')}]"
        elif g["winnerAgent"] == "B_3D":
            stats["b_wins"] += 1
            if g.get("isDiagonalWin"):
                stats["b_diag"] += 1
            banner = f"第 {g_idx} 局获胜: Agent B (Three.js 3D/4D代码派) [{g.get('winAxis')}]"
        else:
            stats["draws"] += 1
            banner = f"第 {g_idx} 局结果: 双方和局 (共 {g['totalMoves']} 手均势僵持)"

        end_frame = render_frame(
            g_idx, total_games, b_agent, w_agent, board, cur_moves, stats,
            win_line=g.get("winLine"),
            banner_text=banner
        )
        for _ in range(22):
            writer.append_data(end_frame)

    writer.close()
    print(f"Video saved successfully to: {VIDEO_PATH}")

if __name__ == "__main__":
    generate_video()
