"""OTBMaster3D: desktop chess with clocks, engines, and OpenGL rendering."""

import json
import math
import random
import struct
import threading
import time
import wave
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

import chess
import chess.engine
import chess.polyglot
import glfw
from OpenGL.GL import *
from OpenGL.GLU import *

try:
    import winsound
except ImportError:
    winsound = None

APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "config.json"
ENGINE_DIR = APP_DIR / "engines"
BOOK_DIR = APP_DIR / "books"
SOUND_DIR = APP_DIR / "sounds"

WIDTH, HEIGHT = 1180, 800
BOARD_Y = 0.0

DEFAULT_LIGHT = (0.77, 0.68, 0.53)
DEFAULT_DARK = (0.31, 0.20, 0.12)
DEFAULT_FRAME = (0.22, 0.11, 0.05)
WHITE_PIECE = (0.88, 0.82, 0.68)
BLACK_PIECE = (0.16, 0.14, 0.12)
SELECT = (0.25, 0.63, 0.92)
LEGAL = (0.24, 0.78, 0.38)
COORD = (0.88, 0.84, 0.72)

PROFILES = {
    chess.PAWN: [
        (0.30, 0.00),
        (0.34, 0.06),
        (0.31, 0.12),
        (0.23, 0.17),
        (0.18, 0.25),
        (0.15, 0.50),
        (0.18, 0.60),
        (0.14, 0.67),
    ],
    chess.ROOK: [
        (0.35, 0.00),
        (0.38, 0.06),
        (0.34, 0.13),
        (0.25, 0.19),
        (0.21, 0.63),
        (0.28, 0.68),
        (0.31, 0.78),
    ],
    chess.KNIGHT: [
        (0.35, 0.00),
        (0.38, 0.06),
        (0.33, 0.14),
        (0.24, 0.20),
        (0.20, 0.47),
    ],
    chess.BISHOP: [
        (0.35, 0.00),
        (0.39, 0.06),
        (0.34, 0.14),
        (0.24, 0.20),
        (0.18, 0.54),
        (0.22, 0.63),
        (0.15, 0.72),
    ],
    chess.QUEEN: [
        (0.38, 0.00),
        (0.41, 0.07),
        (0.36, 0.15),
        (0.25, 0.22),
        (0.19, 0.62),
        (0.28, 0.70),
        (0.31, 0.80),
    ],
    chess.KING: [
        (0.40, 0.00),
        (0.43, 0.07),
        (0.38, 0.15),
        (0.26, 0.22),
        (0.20, 0.67),
        (0.30, 0.75),
        (0.27, 0.84),
    ],
}

GLYPHS = {
    "1": [((0.5, 0.05), (0.5, 0.95)), ((0.35, 0.8), (0.5, 0.95))],
    "2": [
        ((0.15, 0.8), (0.3, 0.95)),
        ((0.3, 0.95), (0.7, 0.95)),
        ((0.7, 0.95), (0.85, 0.8)),
        ((0.85, 0.8), (0.15, 0.05)),
        ((0.15, 0.05), (0.85, 0.05)),
    ],
    "3": [
        ((0.15, 0.95), (0.75, 0.95)),
        ((0.75, 0.95), (0.85, 0.82)),
        ((0.85, 0.82), (0.55, 0.53)),
        ((0.55, 0.53), (0.85, 0.22)),
        ((0.85, 0.22), (0.75, 0.05)),
        ((0.75, 0.05), (0.15, 0.05)),
    ],
    "4": [
        ((0.75, 0.05), (0.75, 0.95)),
        ((0.75, 0.95), (0.15, 0.35)),
        ((0.15, 0.35), (0.9, 0.35)),
    ],
    "5": [
        ((0.85, 0.95), (0.2, 0.95)),
        ((0.2, 0.95), (0.2, 0.55)),
        ((0.2, 0.55), (0.72, 0.55)),
        ((0.72, 0.55), (0.85, 0.42)),
        ((0.85, 0.42), (0.85, 0.18)),
        ((0.85, 0.18), (0.72, 0.05)),
        ((0.72, 0.05), (0.15, 0.05)),
    ],
    "6": [
        ((0.8, 0.88), (0.68, 0.95)),
        ((0.68, 0.95), (0.3, 0.95)),
        ((0.3, 0.95), (0.15, 0.72)),
        ((0.15, 0.72), (0.15, 0.18)),
        ((0.15, 0.18), (0.3, 0.05)),
        ((0.3, 0.05), (0.7, 0.05)),
        ((0.7, 0.05), (0.85, 0.18)),
        ((0.85, 0.18), (0.85, 0.45)),
        ((0.85, 0.45), (0.7, 0.58)),
        ((0.7, 0.58), (0.15, 0.58)),
    ],
    "7": [((0.15, 0.95), (0.85, 0.95)), ((0.85, 0.95), (0.38, 0.05))],
    "8": [
        ((0.3, 0.5), (0.15, 0.65)),
        ((0.15, 0.65), (0.15, 0.82)),
        ((0.15, 0.82), (0.3, 0.95)),
        ((0.3, 0.95), (0.7, 0.95)),
        ((0.7, 0.95), (0.85, 0.82)),
        ((0.85, 0.82), (0.85, 0.65)),
        ((0.85, 0.65), (0.7, 0.5)),
        ((0.7, 0.5), (0.3, 0.5)),
        ((0.3, 0.5), (0.15, 0.35)),
        ((0.15, 0.35), (0.15, 0.18)),
        ((0.15, 0.18), (0.3, 0.05)),
        ((0.3, 0.05), (0.7, 0.05)),
        ((0.7, 0.05), (0.85, 0.18)),
        ((0.85, 0.18), (0.85, 0.35)),
        ((0.85, 0.35), (0.7, 0.5)),
    ],
    "A": [
        ((0.1, 0.05), (0.5, 0.95)),
        ((0.5, 0.95), (0.9, 0.05)),
        ((0.25, 0.45), (0.75, 0.45)),
    ],
    "B": [
        ((0.15, 0.05), (0.15, 0.95)),
        ((0.15, 0.95), (0.62, 0.95)),
        ((0.62, 0.95), (0.82, 0.8)),
        ((0.82, 0.8), (0.82, 0.62)),
        ((0.82, 0.62), (0.62, 0.5)),
        ((0.62, 0.5), (0.15, 0.5)),
        ((0.62, 0.5), (0.84, 0.37)),
        ((0.84, 0.37), (0.84, 0.18)),
        ((0.84, 0.18), (0.62, 0.05)),
        ((0.62, 0.05), (0.15, 0.05)),
    ],
    "C": [
        ((0.85, 0.82), (0.7, 0.95)),
        ((0.7, 0.95), (0.28, 0.95)),
        ((0.28, 0.95), (0.12, 0.78)),
        ((0.12, 0.78), (0.12, 0.22)),
        ((0.12, 0.22), (0.28, 0.05)),
        ((0.28, 0.05), (0.7, 0.05)),
        ((0.7, 0.05), (0.85, 0.18)),
    ],
    "D": [
        ((0.15, 0.05), (0.15, 0.95)),
        ((0.15, 0.95), (0.58, 0.95)),
        ((0.58, 0.95), (0.85, 0.7)),
        ((0.85, 0.7), (0.85, 0.3)),
        ((0.85, 0.3), (0.58, 0.05)),
        ((0.58, 0.05), (0.15, 0.05)),
    ],
    "E": [
        ((0.85, 0.95), (0.15, 0.95)),
        ((0.15, 0.95), (0.15, 0.05)),
        ((0.15, 0.5), (0.72, 0.5)),
        ((0.15, 0.05), (0.85, 0.05)),
    ],
    "F": [
        ((0.15, 0.05), (0.15, 0.95)),
        ((0.15, 0.95), (0.85, 0.95)),
        ((0.15, 0.5), (0.72, 0.5)),
    ],
    "G": [
        ((0.85, 0.8), (0.7, 0.95)),
        ((0.7, 0.95), (0.28, 0.95)),
        ((0.28, 0.95), (0.12, 0.78)),
        ((0.12, 0.78), (0.12, 0.22)),
        ((0.12, 0.22), (0.28, 0.05)),
        ((0.28, 0.05), (0.72, 0.05)),
        ((0.72, 0.05), (0.85, 0.2)),
        ((0.85, 0.2), (0.85, 0.48)),
        ((0.85, 0.48), (0.55, 0.48)),
    ],
    "H": [
        ((0.15, 0.05), (0.15, 0.95)),
        ((0.85, 0.05), (0.85, 0.95)),
        ((0.15, 0.5), (0.85, 0.5)),
    ],
}


@dataclass
class TimeControl:
    name: str
    initial_seconds: float
    increment_seconds: float


TIME_CONTROLS = {
    "Hyperbullet 15+0": TimeControl("Hyperbullet 15+0", 15, 0),
    "Hyperbullet 20+0": TimeControl("Hyperbullet 20+0", 20, 0),
    "Hyperbullet 30+0": TimeControl("Hyperbullet 30+0", 30, 0),
    "Hyperbullet 30+1": TimeControl("Hyperbullet 30+1", 30, 1),
    "Bullet 1+0": TimeControl("Bullet 1+0", 60, 0),
    "Bullet 1+1": TimeControl("Bullet 1+1", 60, 1),
    "Bullet 2+0": TimeControl("Bullet 2+0", 120, 0),
    "Bullet 2+1": TimeControl("Bullet 2+1", 120, 1),
    "Blitz 3+0": TimeControl("Blitz 3+0", 180, 0),
    "Blitz 3+2": TimeControl("Blitz 3+2", 180, 2),
    "Blitz 5+0": TimeControl("Blitz 5+0", 300, 0),
    "Blitz 5+3": TimeControl("Blitz 5+3", 300, 3),
    "Rapid 10+0": TimeControl("Rapid 10+0", 600, 0),
    "Rapid 10+5": TimeControl("Rapid 10+5", 600, 5),
    "Rapid 15+10": TimeControl("Rapid 15+10", 900, 10),
    "Rapid 20+0": TimeControl("Rapid 20+0", 1200, 0),
    "Classical 30+0": TimeControl("Classical 30+0", 1800, 0),
    "Classical 30+20": TimeControl("Classical 30+20", 1800, 20),
    "Classical 45+15": TimeControl("Classical 45+15", 2700, 15),
    "Classical 60+0": TimeControl("Classical 60+0", 3600, 0),
    "Classical 60+30": TimeControl("Classical 60+30", 3600, 30),
    "Classical 90+30": TimeControl("Classical 90+30", 5400, 30),
}


def default_config():
    return {
        "light_square": list(DEFAULT_LIGHT),
        "dark_square": list(DEFAULT_DARK),
        "frame_color": list(DEFAULT_FRAME),
        "show_coordinates": True,
        "time_control": "Bullet 1+0",
        "engine_side": "None",
        "engine_path": "",
        "book_path": "",
        "clock_mode": "Online",
        "clock_binding": "Spacebar",
        "custom_initial": 300.0,
        "custom_increment": 0.0,
        "camera_yaw": 0.0,
        "camera_pitch": math.radians(34),
        "camera_distance": 12.4,
        "camera_pan_x": 0.0,
        "camera_pan_z": 0.0,
    }


def load_config():
    config = default_config()
    if CONFIG_PATH.exists():
        try:
            saved_config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            config.update(
                {key: value for key, value in saved_config.items() if key in config}
            )
        except Exception:
            pass
    return config


def save_config(config):
    try:
        CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")
    except Exception:
        pass


def ensure_dirs():
    ENGINE_DIR.mkdir(exist_ok=True)
    BOOK_DIR.mkdir(exist_ok=True)
    SOUND_DIR.mkdir(exist_ok=True)


def ensure_sounds():
    ensure_dirs()

    def wood(path, pitch, duration, volume, double=False):
        rate = 44100
        total = int(rate * duration)
        rng = random.Random(1000 + int(pitch))
        frames = bytearray()
        for i in range(total):
            t = i / rate
            body = (
                0.75 * math.sin(2 * math.pi * pitch * t)
                + 0.27 * math.sin(2 * math.pi * pitch * 2.08 * t)
            ) * math.exp(-t * 32)
            click = rng.uniform(-1, 1) * math.exp(-t * 120) * 0.55
            second = 0
            if double and t > 0.042:
                tt = t - 0.042
                second = (
                    0.45
                    * (
                        math.sin(2 * math.pi * pitch * 0.78 * tt)
                        + rng.uniform(-0.25, 0.25)
                    )
                    * math.exp(-tt * 38)
                )
            v = max(-1, min(1, (body + click + second) * volume))
            frames += struct.pack("<h", int(32767 * v))
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(frames)

    def tone(path):
        rate = 44100
        total = int(rate * 0.12)
        frames = bytearray()
        for i in range(total):
            t = i / rate
            v = (
                0.28
                * (
                    math.sin(2 * math.pi * 800 * t)
                    + 0.4 * math.sin(2 * math.pi * 1200 * t)
                )
                * math.exp(-t * 22)
            )
            frames += struct.pack("<h", int(32767 * max(-1, min(1, v))))
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(frames)

    m = SOUND_DIR / "move.wav"
    c = SOUND_DIR / "capture.wav"
    k = SOUND_DIR / "check.wav"
    if not m.exists():
        wood(m, 155, 0.105, 0.72)
    if not c.exists():
        wood(c, 118, 0.145, 0.78, True)
    if not k.exists():
        tone(k)
    return m, c, k


_sound_lock = threading.Lock()


def play_sound_blocking(path):
    if winsound is None:
        return
    with _sound_lock:
        winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_NODEFAULT)


def play_sound(path):
    threading.Thread(target=play_sound_blocking, args=(path,), daemon=True).start()


def setup_gl(w, h):
    glViewport(0, 0, max(1, w), max(1, h))
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(40, w / max(1, float(h)), 0.1, 80)
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)
    glEnable(GL_NORMALIZE)
    glEnable(GL_MULTISAMPLE)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.28, 0.28, 0.28, 1))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.92, 0.92, 0.92, 1))
    glClearColor(0.055, 0.055, 0.065, 1)


def material(rgb, shininess=35):
    glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, (*rgb, 1))
    glMaterialfv(GL_FRONT, GL_SPECULAR, (0.32, 0.32, 0.32, 1))
    glMaterialf(GL_FRONT, GL_SHININESS, shininess)


def draw_box(cx, cy, cz, sx, sy, sz, color):
    material(color, 18)
    x0, x1 = cx - sx / 2, cx + sx / 2
    y0, y1 = cy - sy / 2, cy + sy / 2
    z0, z1 = cz - sz / 2, cz + sz / 2
    faces = [
        ((0, 1, 0), [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]),
        ((0, -1, 0), [(x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)]),
        ((0, 0, -1), [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)]),
        ((0, 0, 1), [(x1, y0, z1), (x0, y0, z1), (x0, y1, z1), (x1, y1, z1)]),
        ((-1, 0, 0), [(x0, y0, z1), (x0, y0, z0), (x0, y1, z0), (x0, y1, z1)]),
        ((1, 0, 0), [(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)]),
    ]
    glBegin(GL_QUADS)
    for n, vs in faces:
        glNormal3f(*n)
        for v in vs:
            glVertex3f(*v)
    glEnd()


def lathe(profile, color, segments=30):
    material(color, 70)
    for j in range(len(profile) - 1):
        r0, y0 = profile[j]
        r1, y1 = profile[j + 1]
        dr = r1 - r0
        dy = y1 - y0
        glBegin(GL_QUAD_STRIP)
        for i in range(segments + 1):
            a = 2 * math.pi * i / segments
            ca, sa = math.cos(a), math.sin(a)
            nx, ny, nz = dy * ca, -dr, dy * sa
            ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
            glNormal3f(nx / ln, ny / ln, nz / ln)
            glVertex3f(r0 * ca, y0, r0 * sa)
            glVertex3f(r1 * ca, y1, r1 * sa)
        glEnd()


def sphere(r, y, color, slices=22, stacks=12):
    material(color, 72)
    q = gluNewQuadric()
    glPushMatrix()
    glTranslatef(0, y, 0)
    gluSphere(q, r, slices, stacks)
    glPopMatrix()
    gluDeleteQuadric(q)


def draw_piece_shape(pt, color):
    lathe(PROFILES[pt], color)
    if pt == chess.PAWN:
        sphere(0.16, 0.79, color)
    elif pt == chess.ROOK:
        for a in (0, 90, 180, 270):
            glPushMatrix()
            glRotatef(a, 0, 1, 0)
            glTranslatef(0.20, 0.84, 0)
            draw_box(0, 0, 0, 0.17, 0.16, 0.18, color)
            glPopMatrix()
    elif pt == chess.KNIGHT:
        glPushMatrix()
        glTranslatef(0, 0.55, 0.02)
        glRotatef(-18, 1, 0, 0)
        draw_box(0, 0.12, 0, 0.30, 0.43, 0.22, color)
        glTranslatef(0, 0.27, -0.06)
        glRotatef(-28, 1, 0, 0)
        draw_box(0, 0, 0, 0.25, 0.30, 0.25, color)
        glPopMatrix()
    elif pt == chess.BISHOP:
        sphere(0.19, 0.84, color)
        sphere(0.075, 1.02, color)
    elif pt == chess.QUEEN:
        sphere(0.18, 0.86, color)
        for a in range(0, 360, 60):
            glPushMatrix()
            glRotatef(a, 0, 1, 0)
            glTranslatef(0.19, 0.98, 0)
            sphere(0.055, 0, color, 10, 8)
            glPopMatrix()
    elif pt == chess.KING:
        sphere(0.17, 0.91, color)
        draw_box(0, 1.08, 0, 0.09, 0.32, 0.09, color)
        draw_box(0, 1.16, 0, 0.27, 0.08, 0.09, color)


def draw_piece(piece, x, z, lifted=False):
    glPushMatrix()
    glTranslatef(x, 0.045 + (0.20 if lifted else 0), z)
    if piece.color == chess.BLACK:
        glRotatef(180, 0, 1, 0)
    draw_piece_shape(piece.piece_type, WHITE_PIECE if piece.color else BLACK_PIECE)
    glPopMatrix()


def draw_glyph(ch, x, y, z, scale=0.18, flip_text=False):
    segs = GLYPHS.get(ch.upper())
    if not segs:
        return
    glDisable(GL_LIGHTING)
    glColor3f(*COORD)
    glLineWidth(1.5)
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(90, 1, 0, 0)
    if flip_text:
        glRotatef(180, 0, 0, 1)
    glScalef(scale, scale, scale)
    glBegin(GL_LINES)
    for a, b in segs:
        glVertex3f(a[0] - 0.5, a[1] - 0.5, 0)
        glVertex3f(b[0] - 0.5, b[1] - 0.5, 0)
    glEnd()
    glPopMatrix()
    glEnable(GL_LIGHTING)


class EngineManager:
    def __init__(self, app):
        self.app = app
        self.engine = None
        self.path = ""
        self.lock = threading.Lock()
        self.thinking = False

    def load(self, path):
        self.unload()
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(path)
            self.path = path
            return True, f"Loaded engine: {Path(path).name}"
        except Exception as e:
            self.engine = None
            return False, f"Engine load failed: {e}"

    def unload(self):
        with self.lock:
            if self.engine:
                try:
                    self.engine.quit()
                except Exception:
                    pass
            self.engine = None
            self.thinking = False

    def request_move(self):
        if not self.engine or self.thinking:
            return
        self.thinking = True

        def worker():
            try:
                with self.lock:
                    if not self.engine:
                        return
                    result = self.engine.play(
                        self.app.board.copy(), chess.engine.Limit(time=0.12)
                    )
                self.app.pending_engine_move = result.move
            except Exception as e:
                self.app.pending_engine_error = str(e)
            finally:
                self.thinking = False

        threading.Thread(target=worker, daemon=True).start()


class Chess3D:
    def __init__(self):
        ensure_dirs()
        self.cfg = load_config()
        if not glfw.init():
            raise RuntimeError("GLFW init failed.")
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
        glfw.window_hint(glfw.SAMPLES, 4)
        glfw.window_hint(glfw.RESIZABLE, glfw.TRUE)
        self.window = glfw.create_window(WIDTH, HEIGHT, "OTBMaster3D", None, None)
        if not self.window:
            glfw.terminate()
            raise RuntimeError("Could not create OpenGL window.")
        glfw.make_context_current(self.window)
        glfw.swap_interval(1)
        self.width, self.height = WIDTH, HEIGHT
        setup_gl(WIDTH, HEIGHT)
        self.board = chess.Board()
        self.light_square = tuple(self.cfg["light_square"])
        self.dark_square = tuple(self.cfg["dark_square"])
        self.frame_color = tuple(self.cfg["frame_color"])
        self.show_coordinates = bool(self.cfg["show_coordinates"])
        self.yaw = float(self.cfg.get("camera_yaw", 0.0))
        self.pitch = float(self.cfg.get("camera_pitch", math.radians(34)))
        self.distance = float(self.cfg.get("camera_distance", 12.4))
        self.pan_x = float(self.cfg.get("camera_pan_x", 0.0))
        self.pan_z = float(self.cfg.get("camera_pan_z", 0.0))
        self.target_y = 0.25
        self.selected = self.drag_piece = self.drag_world = self.left_down_pos = None
        self.was_drag = False
        self.right_drag = False
        self.ctrl_left_rotate = False
        self.last_mouse = (0, 0)
        self.board_pan_drag = False
        self.pan_start_world = None
        self.pan_start_offset = (0.0, 0.0)
        self.camera_dirty = False
        self.last_camera_change = 0.0
        self.sound_move, self.sound_capture, self.sound_check = ensure_sounds()
        tc = TIME_CONTROLS.get(self.cfg["time_control"], TIME_CONTROLS["Bullet 1+0"])
        self.white_time = tc.initial_seconds
        self.black_time = tc.initial_seconds
        self.increment = tc.increment_seconds
        self.active_clock_color = chess.WHITE
        self.last_clock_tick = time.perf_counter()
        self.clock_history = []
        self.clock_paused = False
        self.clock_mode = self.cfg.get("clock_mode", "Online")
        self.clock_binding = self.cfg.get("clock_binding", "Spacebar")
        self.awaiting_clock_press = False
        self.awaiting_clock_color = None
        self.game_started = False
        self.game_over = False
        self.result_text = "Ready"
        self.engine_side = {
            "None": None,
            "White": chess.WHITE,
            "Black": chess.BLACK,
        }.get(self.cfg["engine_side"])
        self.engine_manager = EngineManager(self)
        self.pending_engine_move = None
        self.pending_engine_error = None
        self.book_path = self.cfg.get("book_path", "")
        self.ui = None
        glfw.set_window_user_pointer(self.window, self)
        glfw.set_framebuffer_size_callback(self.window, self._resize)
        glfw.set_scroll_callback(self.window, self._scroll)
        glfw.set_mouse_button_callback(self.window, self._mouse)
        glfw.set_cursor_pos_callback(self.window, self._cursor)
        glfw.set_key_callback(self.window, self._key)

    @staticmethod
    def _s(w):
        return glfw.get_window_user_pointer(w)

    @staticmethod
    def _resize(w, x, y):
        s = Chess3D._s(w)
        s.width, s.height = max(1, x), max(1, y)
        setup_gl(s.width, s.height)

    @staticmethod
    def _scroll(w, dx, dy):
        s = Chess3D._s(w)
        s.distance = max(7, min(22, s.distance - dy * 0.7))
        s.mark_camera_dirty()

    @staticmethod
    def _mouse(w, b, a, m):
        s = Chess3D._s(w)
        p = glfw.get_cursor_pos(w)
        if a == glfw.PRESS and s.clock_mode == "OTB":
            binding_map = {
                "Middle Mouse": glfw.MOUSE_BUTTON_MIDDLE,
                "Mouse Button 4": glfw.MOUSE_BUTTON_4,
                "Mouse Button 5": glfw.MOUSE_BUTTON_5,
            }
            if s.clock_binding in binding_map and b == binding_map[s.clock_binding]:
                s.hit_clock()
                return
        if b == glfw.MOUSE_BUTTON_LEFT:
            if a == glfw.PRESS and (m & glfw.MOD_CONTROL):
                s.ctrl_left_rotate = True
                s.last_mouse = p
                s.board_pan_drag = False
                s.drag_piece = None
                return
            elif a == glfw.RELEASE and s.ctrl_left_rotate:
                s.ctrl_left_rotate = False
                s.mark_camera_dirty()
                return
            elif a == glfw.PRESS:
                s.left_press(p)
            elif a == glfw.RELEASE:
                s.left_release(p)
        elif b == glfw.MOUSE_BUTTON_RIGHT:
            if a == glfw.PRESS:
                s.right_drag = True
                s.last_mouse = p
            elif a == glfw.RELEASE:
                s.right_drag = False
                s.mark_camera_dirty()

    @staticmethod
    def _cursor(w, x, y):
        s = Chess3D._s(w)
        if s.right_drag or s.ctrl_left_rotate:
            dx = x - s.last_mouse[0]
            dy = y - s.last_mouse[1]
            s.yaw += dx * 0.009
            s.pitch = max(math.radians(14), min(math.radians(72), s.pitch + dy * 0.007))
            s.last_mouse = (x, y)
            s.mark_camera_dirty()
        elif glfw.get_mouse_button(w, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS:
            s.left_motion((x, y))

    @staticmethod
    def _key(w, key, sc, action, mods):
        if action != glfw.PRESS:
            return
        s = Chess3D._s(w)
        if key == glfw.KEY_ESCAPE:
            glfw.set_window_should_close(w, True)
        elif (
            key == glfw.KEY_SPACE
            and s.clock_mode == "OTB"
            and s.clock_binding == "Spacebar"
        ):
            s.hit_clock()
        elif key == glfw.KEY_F and mods & glfw.MOD_CONTROL:
            s.flip_board()
        elif key == glfw.KEY_U:
            s.takeback()

    def mark_camera_dirty(self):
        self.camera_dirty = True
        self.last_camera_change = time.perf_counter()

    def maybe_persist_camera(self):
        if self.camera_dirty and time.perf_counter() - self.last_camera_change > 0.35:
            self.camera_dirty = False
            self.persist()

    def camera(self):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        cp = math.cos(self.pitch)
        eye = (
            math.sin(self.yaw) * cp * self.distance,
            math.sin(self.pitch) * self.distance + self.target_y,
            -math.cos(self.yaw) * cp * self.distance,
        )
        gluLookAt(*eye, 0, self.target_y, 0, 0, 1, 0)
        glLightfv(GL_LIGHT0, GL_POSITION, (4, 9, -6, 1))

    def draw_board(self):
        draw_box(0, -0.14, 0, 8.72, 0.28, 8.72, self.frame_color)
        legal = self.legal_targets()
        for r in range(8):
            for f in range(8):
                sq = chess.square(f, r)
                col = self.light_square if (f + r) % 2 == 0 else self.dark_square
                if sq == self.selected:
                    col = SELECT
                elif sq in legal:
                    col = tuple(0.60 * c + 0.40 * l for c, l in zip(col, LEGAL))
                draw_box(f - 3.5, 0.005, r - 3.5, 0.995, 0.025, 0.995, col)
        if self.show_coordinates:
            # Camera initially looks from negative Z toward positive Z. With this projection,
            # screen-left corresponds to +X, so reverse the file labels to render A..H left-to-right.
            for f, ch in enumerate("HGFEDCBA"):
                draw_glyph(ch, f - 3.5, 0.035, -4.12, 0.18, flip_text=True)
            # Rank 1 belongs at the near-left corner and increases away from White.
            for r, ch in enumerate("12345678"):
                draw_glyph(ch, 4.12, 0.035, r - 3.5, 0.18, flip_text=True)

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.camera()
        glPushMatrix()
        glTranslatef(self.pan_x, 0, self.pan_z)
        self.draw_board()
        for sq, p in self.board.piece_map().items():
            if self.drag_piece == sq and self.was_drag and self.drag_world:
                continue
            draw_piece(
                p,
                chess.square_file(sq) - 3.5,
                chess.square_rank(sq) - 3.5,
                sq == self.selected,
            )
        if self.drag_piece is not None and self.was_drag and self.drag_world:
            p = self.board.piece_at(self.drag_piece)
            if p:
                x, _, z = self.drag_world
                draw_piece(
                    p,
                    max(-3.85, min(3.85, x - self.pan_x)),
                    max(-3.85, min(3.85, z - self.pan_z)),
                    True,
                )
        glPopMatrix()

    def ray_to_board(self, mx, my):
        vp = glGetIntegerv(GL_VIEWPORT)
        model = glGetDoublev(GL_MODELVIEW_MATRIX)
        proj = glGetDoublev(GL_PROJECTION_MATRIX)
        near = gluUnProject(mx, vp[3] - my, 0, model, proj, vp)
        far = gluUnProject(mx, vp[3] - my, 1, model, proj, vp)
        dy = far[1] - near[1]
        if abs(dy) < 1e-8:
            return None
        t = (BOARD_Y - near[1]) / dy
        if t < 0:
            return None
        return (
            near[0] + t * (far[0] - near[0]),
            BOARD_Y,
            near[2] + t * (far[2] - near[2]),
        )

    def square_at_mouse(self, pos):
        p = self.ray_to_board(*pos)
        if not p:
            return None
        f = int(math.floor((p[0] - self.pan_x) + 4))
        r = int(math.floor((p[2] - self.pan_z) + 4))
        return chess.square(f, r) if 0 <= f < 8 and 0 <= r < 8 else None

    def legal_targets(self):
        if self.selected is None:
            return set()
        return {
            m.to_square
            for m in self.board.legal_moves
            if m.from_square == self.selected
        }

    def human_can_move(self):
        return (
            not self.game_over
            and not self.awaiting_clock_press
            and not (self.game_started and self.engine_side == self.board.turn)
        )

    def try_move(self, fr, to, is_engine=False):
        if fr is None or to is None or fr == to:
            return False
        if not is_engine and not self.human_can_move():
            return False
        p = self.board.piece_at(fr)
        if not p:
            return False
        promo = (
            chess.QUEEN
            if p.piece_type == chess.PAWN and chess.square_rank(to) in (0, 7)
            else None
        )
        mv = chess.Move(fr, to, promotion=promo)
        if mv not in self.board.legal_moves:
            return False
        mover = self.board.turn
        capture = self.board.is_capture(mv)
        if self.game_started:
            self.clock_history.append(
                (self.white_time, self.black_time, self.active_clock_color)
            )
        self.board.push(mv)
        if self.game_started:
            if self.clock_mode == "OTB" and not is_engine:
                self.awaiting_clock_press = True
                self.awaiting_clock_color = mover
                self.active_clock_color = mover
                mover_name = "White" if mover == chess.WHITE else "Black"
                self.result_text = (
                    f"{mover_name} moved - hit clock ({self.clock_binding})"
                )
            else:
                if mover == chess.WHITE:
                    self.white_time += self.increment
                else:
                    self.black_time += self.increment
                self.active_clock_color = self.board.turn
                self.last_clock_tick = time.perf_counter()
        play_sound(self.sound_capture if capture else self.sound_move)
        if self.board.is_check():
            threading.Timer(0.15, lambda: play_sound(self.sound_check)).start()
        self.refresh_move_list()
        self.update_game_end()
        if self.game_started and not self.game_over and not self.awaiting_clock_press:
            self.maybe_request_engine_move()
        return True

    def hit_clock(self):
        if (
            self.clock_mode != "OTB"
            or not self.game_started
            or self.game_over
            or not self.awaiting_clock_press
        ):
            return
        mover = self.awaiting_clock_color
        if mover == chess.WHITE:
            self.white_time += self.increment
        elif mover == chess.BLACK:
            self.black_time += self.increment
        self.awaiting_clock_press = False
        self.awaiting_clock_color = None
        self.active_clock_color = self.board.turn
        self.last_clock_tick = time.perf_counter()
        self.result_text = "Clock hit"
        self.maybe_request_engine_move()

    def update_game_end(self):
        if self.board.is_checkmate():
            self.game_over = True
            self.game_started = False
            self.result_text = "Checkmate"
        elif self.board.is_stalemate():
            self.game_over = True
            self.game_started = False
            self.result_text = "Stalemate"
        elif self.board.is_insufficient_material():
            self.game_over = True
            self.game_started = False
            self.result_text = "Draw - insufficient material"

    def left_press(self, pos):
        sq = self.square_at_mouse(pos)
        self.left_down_pos = pos
        self.was_drag = False
        if (
            self.human_can_move()
            and self.selected is not None
            and sq in self.legal_targets()
        ):
            if self.try_move(self.selected, sq):
                self.selected = None
                return
        p = self.board.piece_at(sq) if sq is not None else None
        if self.human_can_move() and p and p.color == self.board.turn:
            self.selected = sq
            self.drag_piece = sq
            self.drag_world = self.ray_to_board(*pos)
            self.board_pan_drag = False
        else:
            self.board_pan_drag = True
            self.pan_start_world = None
            self.pan_start_offset = (self.pan_x, self.pan_z)

    def left_motion(self, pos):
        if self.left_down_pos:
            dx = pos[0] - self.left_down_pos[0]
            dy = pos[1] - self.left_down_pos[1]
            if dx * dx + dy * dy > 16:
                self.was_drag = True
        if self.drag_piece is not None:
            self.drag_world = self.ray_to_board(*pos)
        elif self.board_pan_drag and self.was_drag:
            cur = self.ray_to_board(*pos)
            if cur:
                if self.pan_start_world is None:
                    self.pan_start_world = cur
                    self.pan_start_offset = (self.pan_x, self.pan_z)
                else:
                    self.pan_x = self.pan_start_offset[0] + (
                        cur[0] - self.pan_start_world[0]
                    )
                    self.pan_z = self.pan_start_offset[1] + (
                        cur[2] - self.pan_start_world[2]
                    )
                    self.mark_camera_dirty()

    def left_release(self, pos):
        if self.drag_piece is not None:
            src = self.drag_piece
            dst = self.square_at_mouse(pos)
            if self.was_drag:
                moved = self.try_move(src, dst)
                self.selected = None if moved else src
        elif self.board_pan_drag and self.was_drag:
            self.mark_camera_dirty()
        self.drag_piece = self.drag_world = self.left_down_pos = None
        self.board_pan_drag = False
        self.pan_start_world = None
        self.was_drag = False

    def refresh_move_list(self):
        if not hasattr(self, "move_text"):
            return
        b = chess.Board()
        sans = []
        for mv in self.board.move_stack:
            sans.append(b.san(mv))
            b.push(mv)
        lines = []
        for i in range(0, len(sans), 2):
            move_no = i // 2 + 1
            white = sans[i]
            black = sans[i + 1] if i + 1 < len(sans) else ""
            lines.append(f"{move_no}. {white} {black}".rstrip())
        self.move_text.config(state="normal")
        self.move_text.delete("1.0", "end")
        self.move_text.insert("1.0", "\n".join(lines))
        self.move_text.config(state="disabled")
        self.move_text.see("end")

    def takeback(self):
        if self.engine_manager.thinking or not self.board.move_stack:
            return
        pops = (
            2 if self.engine_side is not None and len(self.board.move_stack) >= 2 else 1
        )
        for _ in range(pops):
            if self.board.move_stack:
                self.board.pop()
            if self.clock_history:
                self.white_time, self.black_time, self.active_clock_color = (
                    self.clock_history.pop()
                )
        self.selected = None
        self.game_over = False
        self.awaiting_clock_press = False
        self.awaiting_clock_color = None
        self.result_text = "Move taken back"
        self.last_clock_tick = time.perf_counter()
        self.refresh_move_list()

    def reset_board(self):
        self.board.reset()
        self.clock_history.clear()
        self.selected = None
        self.game_started = False
        self.game_over = False
        self.clock_paused = False
        self.awaiting_clock_press = False
        self.awaiting_clock_color = None
        self.result_text = "Board reset"
        self.refresh_move_list()

    def reset_view(self):
        self.yaw = 0.0
        self.pitch = math.radians(34)
        self.distance = 12.4
        self.pan_x = 0.0
        self.pan_z = 0.0
        self.mark_camera_dirty()
        self.persist()
        self.result_text = "View reset"

    def flip_board(self):
        self.yaw += math.pi
        self.mark_camera_dirty()

    def stop_clock(self):
        if not self.game_started or self.game_over:
            return
        self.clock_paused = not self.clock_paused
        self.last_clock_tick = time.perf_counter()
        self.result_text = "Clock stopped" if self.clock_paused else "Clock resumed"
        self.stop_btn.config(text="Resume Clock" if self.clock_paused else "Stop Clock")

    def selected_time_control(self):
        """Return the selected preset or a validated custom time control."""
        selected = self.time_control_var.get()
        if selected != "Custom":
            return TIME_CONTROLS[selected]

        try:
            initial = float(self.custom_initial_var.get())
            increment = float(self.custom_increment_var.get())
            if initial <= 0 or increment < 0:
                raise ValueError
        except (TypeError, ValueError):
            messagebox.showerror(
                "Time control",
                "Custom initial seconds must be > 0 and increment must be >= 0.",
            )
            return None

        return TimeControl("Custom", initial, increment)

    def reset_clock(self):
        time_control = self.selected_time_control()
        if time_control is None:
            return

        self.white_time = time_control.initial_seconds
        self.black_time = time_control.initial_seconds
        self.increment = time_control.increment_seconds
        self.active_clock_color = chess.WHITE
        self.clock_paused = False
        self.awaiting_clock_press = False
        self.awaiting_clock_color = None
        self.last_clock_tick = time.perf_counter()
        self.result_text = f"Clock reset - {time_control.name}"
        if hasattr(self, "stop_btn"):
            self.stop_btn.config(text="Stop Clock")

    def start_game(self):
        time_control = self.selected_time_control()
        if time_control is None:
            return

        self.board.reset()
        self.clock_history.clear()
        self.white_time = time_control.initial_seconds
        self.black_time = time_control.initial_seconds
        self.increment = time_control.increment_seconds
        self.active_clock_color = chess.WHITE
        self.last_clock_tick = time.perf_counter()
        self.clock_paused = False
        self.awaiting_clock_press = False
        self.awaiting_clock_color = None
        self.game_started = True
        self.game_over = False
        self.result_text = f"Game started - {time_control.name}"
        self.clock_mode = self.clock_mode_var.get()
        self.clock_binding = self.clock_binding_var.get()
        self.engine_side = {"None": None, "White": chess.WHITE, "Black": chess.BLACK}[
            self.engine_side_var.get()
        ]
        self.book_path = self.book_var.get()
        self.refresh_move_list()
        self.persist()
        self.maybe_request_engine_move()

    def resign(self):
        if self.game_started and not self.game_over:
            loser = "White" if self.board.turn == chess.WHITE else "Black"
            self.game_started = False
            self.game_over = True
            self.result_text = f"{loser} resigned"

    def offer_draw(self):
        if self.game_started and not self.game_over:
            self.result_text = "Draw offered"

    def update_clock(self):
        now = time.perf_counter()
        if not self.game_started or self.game_over or self.clock_paused:
            self.last_clock_tick = now
            return
        e = now - self.last_clock_tick
        self.last_clock_tick = now
        if self.active_clock_color == chess.WHITE:
            self.white_time = max(0, self.white_time - e)
            if self.white_time <= 0:
                self.game_started = False
                self.game_over = True
                self.result_text = "White flagged"
        else:
            self.black_time = max(0, self.black_time - e)
            if self.black_time <= 0:
                self.game_started = False
                self.game_over = True
                self.result_text = "Black flagged"

    @staticmethod
    def fmt_clock(s):
        s = max(0, s)
        return (
            f"{int(s)//60}:{s%60:04.1f}" if s < 20 else f"{int(s)//60}:{int(s)%60:02d}"
        )

    def pick_book_move(self):
        path = self.book_var.get() if self.book_var else self.book_path
        if not path or not Path(path).exists():
            return None
        try:
            with chess.polyglot.open_reader(path) as rd:
                es = list(rd.find_all(self.board))
                if not es:
                    return None
                return random.choices(es, weights=[max(1, e.weight) for e in es], k=1)[
                    0
                ].move
        except Exception:
            return None

    def maybe_request_engine_move(self):
        if not (
            self.game_started
            and not self.game_over
            and self.engine_side is not None
            and self.board.turn == self.engine_side
        ):
            return
        bm = self.pick_book_move()
        if bm:
            self.pending_engine_move = bm
        elif self.engine_manager.engine:
            self.engine_manager.request_move()

    def apply_pending_engine_move(self):
        if self.pending_engine_error:
            self.result_text = f"Engine error: {self.pending_engine_error}"
            self.pending_engine_error = None
        mv = self.pending_engine_move
        if mv is None:
            return
        self.pending_engine_move = None
        if mv in self.board.legal_moves:
            self.try_move(mv.from_square, mv.to_square, True)

    def refresh_engines(self):
        self.engine_combo["values"] = [""] + [
            str(p) for p in sorted(ENGINE_DIR.glob("*.exe"))
        ]

    def refresh_books(self):
        self.book_combo["values"] = [""] + [
            str(p) for p in sorted(BOOK_DIR.glob("*.bin"))
        ]

    def load_engine(self):
        path = self.engine_var.get()
        if not path:
            return
        ok, msg = self.engine_manager.load(path)
        self.result_text = msg
        if not ok:
            messagebox.showerror("UCI engine", msg)
        self.persist()

    def browse_engine(self):
        p = filedialog.askopenfilename(
            initialdir=ENGINE_DIR, filetypes=[("Engine", "*.exe"), ("All", "*.*")]
        )
        if p:
            self.engine_var.set(p)
            self.load_engine()

    def browse_book(self):
        p = filedialog.askopenfilename(
            initialdir=BOOK_DIR, filetypes=[("Polyglot", "*.bin"), ("All", "*.*")]
        )
        if p:
            self.book_var.set(p)
            self.book_path = p
            self.persist()

    @staticmethod
    def hex(rgb):
        return "#" + "".join(f"{max(0,min(255,round(c*255))):02x}" for c in rgb)

    def choose_color(self, which):
        current = {
            "light": self.light_square,
            "dark": self.dark_square,
            "frame": self.frame_color,
        }[which]
        c = colorchooser.askcolor(color=self.hex(current))
        if c and c[0]:
            val = tuple(v / 255 for v in c[0])
            if which == "light":
                self.light_square = val
            elif which == "dark":
                self.dark_square = val
            else:
                self.frame_color = val
            self.persist()

    def apply_preset(self, name):
        presets = {
            "Wood": ((0.77, 0.68, 0.53), (0.31, 0.20, 0.12), (0.22, 0.11, 0.05)),
            "Tournament Green": (
                (0.92, 0.90, 0.78),
                (0.30, 0.48, 0.34),
                (0.16, 0.22, 0.14),
            ),
            "Blue": ((0.88, 0.90, 0.92), (0.31, 0.43, 0.57), (0.14, 0.18, 0.24)),
            "Grey": ((0.82, 0.82, 0.82), (0.35, 0.35, 0.35), (0.18, 0.18, 0.18)),
        }
        self.light_square, self.dark_square, self.frame_color = presets[name]
        self.persist()

    def persist(self):
        save_config(
            {
                "light_square": list(self.light_square),
                "dark_square": list(self.dark_square),
                "frame_color": list(self.frame_color),
                "show_coordinates": self.show_coordinates,
                "time_control": (
                    self.time_control_var.get()
                    if hasattr(self, "time_control_var") and self.time_control_var
                    else self.cfg["time_control"]
                ),
                "engine_side": (
                    self.engine_side_var.get()
                    if hasattr(self, "engine_side_var") and self.engine_side_var
                    else self.cfg["engine_side"]
                ),
                "engine_path": (
                    self.engine_var.get()
                    if hasattr(self, "engine_var") and self.engine_var
                    else self.cfg.get("engine_path", "")
                ),
                "book_path": (
                    self.book_var.get()
                    if hasattr(self, "book_var") and self.book_var
                    else self.book_path
                ),
                "camera_yaw": self.yaw,
                "camera_pitch": self.pitch,
                "camera_distance": self.distance,
                "camera_pan_x": self.pan_x,
                "camera_pan_z": self.pan_z,
                "clock_mode": (
                    self.clock_mode_var.get()
                    if hasattr(self, "clock_mode_var")
                    else self.clock_mode
                ),
                "clock_binding": (
                    self.clock_binding_var.get()
                    if hasattr(self, "clock_binding_var")
                    else self.clock_binding
                ),
                "custom_initial": (
                    float(self.custom_initial_var.get())
                    if hasattr(self, "custom_initial_var")
                    else self.cfg.get("custom_initial", 300.0)
                ),
                "custom_increment": (
                    float(self.custom_increment_var.get())
                    if hasattr(self, "custom_increment_var")
                    else self.cfg.get("custom_increment", 0.0)
                ),
            }
        )

    def toggle_coords(self):
        self.show_coordinates = bool(self.coords_var.get())
        self.persist()

    def build_ui(self):
        root = tk.Tk()
        self.ui = root
        root.title("OTBMaster3D - Controls")
        root.geometry("620x780+10+10")
        root.resizable(False, True)
        self.white_clock_var = tk.StringVar(value=self.fmt_clock(self.white_time))
        self.black_clock_var = tk.StringVar(value=self.fmt_clock(self.black_time))
        self.status_var = tk.StringVar(value=self.result_text)
        self.time_control_var = tk.StringVar(value=self.cfg["time_control"])
        self.engine_side_var = tk.StringVar(value=self.cfg["engine_side"])
        self.engine_var = tk.StringVar(value=self.cfg.get("engine_path", ""))
        self.book_var = tk.StringVar(value=self.cfg.get("book_path", ""))
        self.coords_var = tk.BooleanVar(value=self.show_coordinates)
        self.clock_mode_var = tk.StringVar(value=self.cfg.get("clock_mode", "Online"))
        self.clock_binding_var = tk.StringVar(
            value=self.cfg.get("clock_binding", "Spacebar")
        )
        self.custom_initial_var = tk.StringVar(
            value=str(self.cfg.get("custom_initial", 300.0))
        )
        self.custom_increment_var = tk.StringVar(
            value=str(self.cfg.get("custom_increment", 0.0))
        )
        outer = ttk.Frame(root)
        outer.pack(fill="both", expand=True, padx=6, pady=6)
        left = ttk.Frame(outer, width=390)
        left.pack(side="left", fill="both", expand=False)
        right = ttk.LabelFrame(outer, text="Moves", width=165)
        right.pack(side="right", fill="both", expand=False, padx=(8, 0))
        right.pack_propagate(False)

        clocks = ttk.Frame(left)
        clocks.pack(fill="x", pady=4)
        ttk.Label(clocks, text="Black").grid(row=0, column=0, sticky="w")
        ttk.Label(
            clocks, textvariable=self.black_clock_var, font=("Consolas", 18, "bold")
        ).grid(row=0, column=1, sticky="e")
        ttk.Label(clocks, text="White").grid(row=1, column=0, sticky="w")
        ttk.Label(
            clocks, textvariable=self.white_clock_var, font=("Consolas", 18, "bold")
        ).grid(row=1, column=1, sticky="e")
        clocks.columnconfigure(1, weight=1)

        game = ttk.LabelFrame(left, text="Game")
        game.pack(fill="x", pady=3)
        ttk.Combobox(
            game,
            state="readonly",
            textvariable=self.time_control_var,
            values=list(TIME_CONTROLS) + ["Custom"],
            width=22,
        ).pack(fill="x", padx=6, pady=4)
        self.customrow = ttk.Frame(game)
        ttk.Label(self.customrow, text="Custom sec").pack(side="left")
        ttk.Entry(self.customrow, textvariable=self.custom_initial_var, width=8).pack(
            side="left", padx=(4, 10)
        )
        ttk.Label(self.customrow, text="Inc").pack(side="left")
        ttk.Entry(self.customrow, textvariable=self.custom_increment_var, width=6).pack(
            side="left", padx=4
        )

        def update_custom_visibility(*_):
            if self.time_control_var.get() == "Custom":
                self.customrow.pack(
                    fill="x", padx=6, pady=2, after=game.winfo_children()[0]
                )
            else:
                self.customrow.pack_forget()

        self.time_control_var.trace_add("write", update_custom_visibility)
        update_custom_visibility()
        clockrow = ttk.Frame(game)
        clockrow.pack(fill="x", padx=6, pady=2)
        ttk.Label(clockrow, text="Clock mode").pack(side="left")
        ttk.Combobox(
            clockrow,
            state="readonly",
            textvariable=self.clock_mode_var,
            values=["Online", "OTB"],
            width=9,
        ).pack(side="left", padx=4)
        ttk.Label(clockrow, text="Hit").pack(side="left", padx=(8, 0))
        ttk.Combobox(
            clockrow,
            state="readonly",
            textvariable=self.clock_binding_var,
            values=["Spacebar", "Middle Mouse", "Mouse Button 4", "Mouse Button 5"],
            width=16,
        ).pack(side="left", padx=4)
        row = ttk.Frame(game)
        row.pack(fill="x", padx=4, pady=2)
        ttk.Button(row, text="Start", command=self.start_game).pack(
            side="left", expand=True, fill="x", padx=2
        )
        ttk.Button(row, text="Resign", command=self.resign).pack(
            side="left", expand=True, fill="x", padx=2
        )
        ttk.Button(row, text="Draw", command=self.offer_draw).pack(
            side="left", expand=True, fill="x", padx=2
        )
        ttk.Button(game, text="Takeback", command=self.takeback).pack(
            fill="x", padx=6, pady=3
        )
        row2 = ttk.Frame(game)
        row2.pack(fill="x", padx=4, pady=2)
        ttk.Button(row2, text="Reset Board", command=self.reset_board).pack(
            side="left", expand=True, fill="x", padx=2
        )
        ttk.Button(row2, text="Flip Board", command=self.flip_board).pack(
            side="left", expand=True, fill="x", padx=2
        )
        ttk.Button(game, text="Reset View", command=self.reset_view).pack(
            fill="x", padx=6, pady=3
        )
        self.stop_btn = ttk.Button(game, text="Stop Clock", command=self.stop_clock)
        self.stop_btn.pack(fill="x", padx=6, pady=(3, 3))
        ttk.Button(game, text="Reset Clock", command=self.reset_clock).pack(
            fill="x", padx=6, pady=(0, 6)
        )

        settings = ttk.LabelFrame(left, text="Settings")
        settings.pack(fill="x", pady=4)
        ttk.Label(settings, text="Engine side").pack(anchor="w", padx=6, pady=(4, 0))
        ttk.Combobox(
            settings,
            state="readonly",
            textvariable=self.engine_side_var,
            values=["None", "White", "Black"],
        ).pack(fill="x", padx=6)
        self.engine_combo = ttk.Combobox(
            settings, state="readonly", textvariable=self.engine_var
        )
        self.engine_combo.pack(fill="x", padx=6, pady=2)
        er = ttk.Frame(settings)
        er.pack(fill="x", padx=5)
        ttk.Button(er, text="Refresh Engines", command=self.refresh_engines).pack(
            side="left", expand=True, fill="x", padx=1
        )
        ttk.Button(er, text="Browse", command=self.browse_engine).pack(
            side="left", expand=True, fill="x", padx=1
        )
        ttk.Button(er, text="Load", command=self.load_engine).pack(
            side="left", expand=True, fill="x", padx=1
        )
        ttk.Label(settings, text="Opening book").pack(anchor="w", padx=6, pady=(5, 0))
        self.book_combo = ttk.Combobox(
            settings, state="readonly", textvariable=self.book_var
        )
        self.book_combo.pack(fill="x", padx=6)
        br = ttk.Frame(settings)
        br.pack(fill="x", padx=5, pady=2)
        ttk.Button(br, text="Refresh Books", command=self.refresh_books).pack(
            side="left", expand=True, fill="x", padx=1
        )
        ttk.Button(br, text="Browse", command=self.browse_book).pack(
            side="left", expand=True, fill="x", padx=1
        )
        ttk.Separator(settings).pack(fill="x", padx=6, pady=5)
        preset = ttk.Combobox(
            settings,
            state="readonly",
            values=["Wood", "Tournament Green", "Blue", "Grey"],
        )
        preset.set("Wood")
        preset.pack(fill="x", padx=6)
        preset.bind("<<ComboboxSelected>>", lambda e: self.apply_preset(preset.get()))
        cr = ttk.Frame(settings)
        cr.pack(fill="x", padx=5, pady=3)
        ttk.Button(cr, text="Light", command=lambda: self.choose_color("light")).pack(
            side="left", expand=True, fill="x", padx=1
        )
        ttk.Button(cr, text="Dark", command=lambda: self.choose_color("dark")).pack(
            side="left", expand=True, fill="x", padx=1
        )
        ttk.Button(
            cr, text="Board Frame", command=lambda: self.choose_color("frame")
        ).pack(side="left", expand=True, fill="x", padx=1)
        ttk.Checkbutton(
            settings,
            text="Show coordinates",
            variable=self.coords_var,
            command=self.toggle_coords,
        ).pack(anchor="w", padx=6, pady=(0, 5))

        ttk.Label(left, textvariable=self.status_var, wraplength=360).pack(
            fill="x", pady=6
        )
        ttk.Label(
            left,
            text=(
                "Ctrl+F flip | U takeback | right-drag or Ctrl+left-drag rotate | "
                "left-drag empty board pan | wheel zoom"
            ),
            wraplength=360,
        ).pack(fill="x")

        self.move_text = tk.Text(
            right, width=17, font=("Consolas", 10), state="disabled", wrap="none"
        )
        self.move_text.pack(fill="both", expand=True, padx=4, pady=4)

        self.refresh_engines()
        self.refresh_books()
        self.refresh_move_list()
        remembered = self.engine_var.get()
        if remembered and Path(remembered).exists():
            ok, msg = self.engine_manager.load(remembered)
            self.result_text = msg
        return root

    def ui_tick(self):
        if glfw.window_should_close(self.window):
            try:
                self.ui.destroy()
            except Exception:
                pass
            return
        self.update_clock()
        self.apply_pending_engine_move()
        self.maybe_persist_camera()
        self.white_clock_var.set(self.fmt_clock(self.white_time))
        self.black_clock_var.set(self.fmt_clock(self.black_time))
        self.status_var.set(self.result_text)
        self.draw()
        glfw.swap_buffers(self.window)
        glfw.poll_events()
        self.ui.after(8, self.ui_tick)

    def run(self):
        root = self.build_ui()
        self.ui_tick()
        try:
            root.mainloop()
        finally:
            self.persist()
            self.engine_manager.unload()
            try:
                glfw.destroy_window(self.window)
            except Exception:
                pass
            glfw.terminate()


if __name__ == "__main__":
    Chess3D().run()
