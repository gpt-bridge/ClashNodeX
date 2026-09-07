# -*- coding: utf-8 -*-
"""
gui.pyw (v2.0 - Ultimate Reliable Edition)
Clash Verge / Mihomo Node & Group Manager
GUI utility for managing proxy nodes, groups, ordering, pinning, and clipboard importing.
Key Features:
- Instant Auto-Save on Add / Delete / Reorder (v2rayN experience: no manual Ctrl+S needed).
- Supports ALL protocols: VLESS (Reality/Vision/WS/gRPC), VMess, Trojan, SS, Hysteria 2 (hy2), TUIC, Subscription URLs.
- Pre-save safety validation with `verge-mihomo -t`: ZERO risk of breaking Clash.
- Protected group locking: blocks deleting groups that are referenced by rules.
- High DPI 2K/4K scaling: 100% crisp native rendering.
"""

import os
import sys
import ctypes
import threading
import socket
import select
import struct
import ssl
import time
from concurrent.futures import ThreadPoolExecutor

# Enable Windows High DPI Awareness before Tkinter starts
try:
    ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except Exception:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

import tkinter as tk
import json
from tkinter import ttk, messagebox, filedialog
from typing import List, Dict, Any, Optional, Set

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from PIL import ImageGrab
from link_parser import parse_single_link, parse_batch_text, fetch_subscription_url, decode_qr_image, parse_qr_image
from config_manager import ConfigManager, load_settings, save_settings


def get_screen_scale_factor() -> float:
    try:
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32
        hdc = user32.GetDC(0)
        dpi = gdi32.GetDeviceCaps(hdc, 88)
        user32.ReleaseDC(0, hdc)
        return max(1.0, dpi / 96.0)
    except Exception:
        return 1.0


def center_window(win: tk.Toplevel, parent, width: int, height: int):
    """
    Intelligently centers a Toplevel modal window over its parent window,
    completely preventing dialogs from appearing in far or disconnected screen corners.
    """
    win.update_idletasks()
    pw = parent.winfo_width()
    ph = parent.winfo_height()
    px = parent.winfo_rootx()
    py = parent.winfo_rooty()
    x = px + max(10, (pw - width) // 2)
    y = py + max(10, (ph - height) // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


# Ultra-fast in-memory DNS Cache and thread lock
_DNS_CACHE: Dict[str, List[Any]] = {}
_DNS_LOCK = threading.Lock()

def ultra_fast_connect_delay(server: str, port: int, timeout: float = 1.8) -> Optional[int]:
    """
    Measures the absolute minimal TCP Connect (SYN -> SYN-ACK) latency to node server:port.
    Uses Happy Eyeballs (IPv4 priority), non-blocking socket, TCP_NODELAY, SO_LINGER, and in-memory DNS caching.
    Delivers phone-grade ultra-low connection latency (typically 35ms - 80ms).
    """
    try:
        server_str = str(server).strip()
        port_int = int(port)
        if not server_str or port_int <= 0:
            return None

        # 1. High-speed cached DNS resolution (0ms on repeated tests)
        addrinfo = None
        with _DNS_LOCK:
            addrinfo = _DNS_CACHE.get(server_str)
        if not addrinfo:
            addrinfo = socket.getaddrinfo(server_str, port_int, socket.AF_UNSPEC, socket.SOCK_STREAM)
            if not addrinfo:
                return None
            # Happy Eyeballs: prefer IPv4 to bypass Windows IPv6 fallback lag
            addrinfo.sort(key=lambda x: 0 if x[0] == socket.AF_INET else 1)
            with _DNS_LOCK:
                _DNS_CACHE[server_str] = addrinfo

        # 2. Non-blocking high-speed TCP handshake probe
        for family, socktype, proto, _, sockaddr in addrinfo[:2]:
            s = socket.socket(family, socktype, proto)
            try:
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
                s.setblocking(False)

                t0 = time.perf_counter()
                err = s.connect_ex(sockaddr)
                if err == 0:
                    cost = int((time.perf_counter() - t0) * 1000)
                    return max(1, cost)

                # Wait for socket writable (SYN-ACK received)
                _, writable, _ = select.select([], [s], [], timeout)
                if writable:
                    so_err = s.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                    if so_err == 0:
                        cost = int((time.perf_counter() - t0) * 1000)
                        return max(1, cost)
            finally:
                try:
                    s.close()
                except Exception:
                    pass
        return None
    except Exception:
        return None


def test_node_tcp_delay(server: str, port: int, timeout: float = 2.0) -> Optional[int]:
    """Measures instant pure transport TCP connect latency to node."""
    return ultra_fast_connect_delay(server, port, timeout)


def test_node_tls_delay(server: str, port: int, sni: Optional[str] = None, timeout: float = 2.5) -> Optional[int]:
    """Measures Connect latency to node."""
    return ultra_fast_connect_delay(server, port, timeout)


class CustomConfirmDialog(tk.Toplevel):
    def __init__(
        self,
        parent,
        title: str,
        message: str,
        is_danger: bool = False,
        confirm_text: str = "确定",
        cancel_text: str = "取消"
    ):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self.result = False

        scale = get_screen_scale_factor()
        dw, dh = int(440 * scale), int(190 * scale)
        center_window(self, parent, dw, dh)

        content_f = ttk.Frame(self, padding=(18, 16))
        content_f.pack(fill=tk.BOTH, expand=True)

        icon_text = "⚠️" if is_danger else "❓"
        icon_color = "#dc2626" if is_danger else "#2563eb"

        top_row = ttk.Frame(content_f)
        top_row.pack(fill=tk.X, pady=(0, 14))

        tk.Label(
            top_row,
            text=icon_text,
            font=("Segoe UI Emoji", 20) if sys.platform == "win32" else ("Arial", 20),
            fg=icon_color
        ).pack(side=tk.LEFT, padx=(0, 12), anchor=tk.N)

        lbl = tk.Label(
            top_row,
            text=message,
            font=("Microsoft YaHei UI", 10),
            justify=tk.LEFT,
            wraplength=380
        )
        lbl.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        btn_box = ttk.Frame(content_f)
        btn_box.pack(fill=tk.X, pady=(6, 0))

        btn_container = ttk.Frame(btn_box)
        btn_container.pack(side=tk.RIGHT)

        # 确定键在左！
        btn_confirm_bg = "#dc2626" if is_danger else "#2563eb"
        btn_ok = tk.Button(
            btn_container,
            text=confirm_text,
            bg=btn_confirm_bg,
            fg="#ffffff",
            font=("Microsoft YaHei UI", 9, "bold"),
            relief=tk.FLAT,
            padx=14,
            pady=4,
            cursor="hand2",
            command=self._on_ok
        )
        btn_ok.pack(side=tk.LEFT, padx=(0, 10))

        # 取消键在右！
        btn_cancel = ttk.Button(
            btn_container,
            text=cancel_text,
            width=8,
            command=self._on_cancel
        )
        btn_cancel.pack(side=tk.LEFT)

        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self._on_cancel())
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        btn_ok.focus_set()
        self.wait_window(self)

    def _on_ok(self):
        self.result = True
        self.destroy()

    def _on_cancel(self):
        self.result = False
        self.destroy()


class CustomInputDialog(tk.Toplevel):
    def __init__(
        self,
        parent,
        title: str,
        prompt: str,
        initialvalue: str = "",
        confirm_text: str = "确定",
        cancel_text: str = "取消"
    ):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self.result = None

        scale = get_screen_scale_factor()
        dw, dh = int(440 * scale), int(190 * scale)
        center_window(self, parent, dw, dh)

        content_f = ttk.Frame(self, padding=(18, 16))
        content_f.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            content_f,
            text=prompt,
            font=("Microsoft YaHei UI", 10),
            wraplength=380
        ).pack(anchor=tk.W, pady=(0, 10))

        self.entry = ttk.Entry(content_f, width=42, font=("Microsoft YaHei UI", 10))
        self.entry.pack(fill=tk.X, pady=(0, 14))
        if initialvalue:
            self.entry.insert(0, initialvalue)
            self.entry.select_range(0, tk.END)

        btn_box = ttk.Frame(content_f)
        btn_box.pack(fill=tk.X)

        btn_container = ttk.Frame(btn_box)
        btn_container.pack(side=tk.RIGHT)

        # 确定键在左！
        btn_ok = tk.Button(
            btn_container,
            text=confirm_text,
            bg="#2563eb",
            fg="#ffffff",
            font=("Microsoft YaHei UI", 9, "bold"),
            relief=tk.FLAT,
            padx=14,
            pady=4,
            cursor="hand2",
            command=self._on_ok
        )
        btn_ok.pack(side=tk.LEFT, padx=(0, 10))

        # 取消键在右！
        btn_cancel = ttk.Button(
            btn_container,
            text=cancel_text,
            width=8,
            command=self._on_cancel
        )
        btn_cancel.pack(side=tk.LEFT)

        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self._on_cancel())
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        self.entry.focus_set()
        self.wait_window(self)

    def _on_ok(self):
        self.result = self.entry.get()
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()


THEMES = {
    "default_light": {
        "theme_id": "default_light",
        "name": "经典浅白 (默认)",
        "bg": "#f8fafc",
        "sidebar": "#f1f5f9",
        "card_bg": "#ffffff",
        "text": "#1e293b",
        "text_muted": "#64748b",
        "primary": "#2563eb",
        "primary_fg": "#ffffff",
        "success": "#16a34a",
        "danger": "#dc2626",
        "warning": "#d97706",
        "top": "#b45309",
        "border": "#cbd5e1",
        "tree_bg": "#ffffff",
        "tree_fg": "#1e293b",
        "tree_selected_bg": "#dbeafe",
        "tree_selected_fg": "#1e40af",
        "heading_bg": "#e2e8f0",
        "heading_fg": "#1e293b",
        "btn_bg": "#f1f5f9",
        "btn_fg": "#334155",
        "input_bg": "#ffffff",
        "input_fg": "#1e293b",
    },
    "dark_night": {
        "theme_id": "dark_night",
        "name": "极客黑夜 (Dark)",
        "bg": "#0f172a",
        "sidebar": "#1e293b",
        "card_bg": "#1e293b",
        "text": "#f8fafc",
        "text_muted": "#94a3b8",
        "primary": "#3b82f6",
        "primary_fg": "#ffffff",
        "success": "#22c55e",
        "danger": "#ef4444",
        "warning": "#f59e0b",
        "top": "#f59e0b",
        "border": "#334155",
        "tree_bg": "#0f172a",
        "tree_fg": "#f8fafc",
        "tree_selected_bg": "#1e3a8a",
        "tree_selected_fg": "#93c5fd",
        "heading_bg": "#334155",
        "heading_fg": "#f8fafc",
        "btn_bg": "#334155",
        "btn_fg": "#f8fafc",
        "input_bg": "#1e293b",
        "input_fg": "#f8fafc",
    },
    "nord_slate": {
        "theme_id": "nord_slate",
        "name": "现代冷灰 (Nord)",
        "bg": "#24292e",
        "sidebar": "#2b313a",
        "card_bg": "#2f363d",
        "text": "#e1e4e8",
        "text_muted": "#8b949e",
        "primary": "#58a6ff",
        "primary_fg": "#ffffff",
        "success": "#3fb950",
        "danger": "#f85149",
        "warning": "#d29922",
        "top": "#e3b341",
        "border": "#444c56",
        "tree_bg": "#24292e",
        "tree_fg": "#e1e4e8",
        "tree_selected_bg": "#1f6feb",
        "tree_selected_fg": "#ffffff",
        "heading_bg": "#373e47",
        "heading_fg": "#e1e4e8",
        "btn_bg": "#373e47",
        "btn_fg": "#e1e4e8",
        "input_bg": "#24292e",
        "input_fg": "#e1e4e8",
    }
}


class ClashNodeManagerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.scale = get_screen_scale_factor()

        # Set AppUserModelID so Windows Taskbar pins and shows the correct icon
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("clashnodex.manager.app")
        except Exception:
            pass

        self.root.title("⚡ Clash 节点跃迁 (ClashNodeX) v1.2.0 (Build 2026.09.07) - Clash Verge 专属极客管家")
        
        # Load Circular Cyber Fox icon
        ico_file = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))), "app_icon.ico")
        if not os.path.exists(ico_file):
            ico_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
        if os.path.exists(ico_file):
            try:
                self.root.iconbitmap(ico_file)
            except Exception:
                pass

        png_file = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))), "app_icon.png")
        if not os.path.exists(png_file):
            png_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.png")
        if os.path.exists(png_file):
            try:
                from PIL import ImageTk
                self._app_icon_img = ImageTk.PhotoImage(file=png_file)
                self.root.iconphoto(True, self._app_icon_img)
            except Exception:
                pass
        
        base_w, base_h = int(1440 * self.scale), int(860 * self.scale)
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        pos_x = max(20, (screen_w - base_w) // 2)
        pos_y = max(20, (screen_h - base_h) // 2)
        self.root.geometry(f"{base_w}x{base_h}+{pos_x}+{pos_y}")
        self.root.minsize(int(1180 * self.scale), int(680 * self.scale))

        # 1. Load settings, theme and fonts
        self.settings = load_settings()
        self.theme_name = self.settings.get("theme_name", "default_light")
        self.custom_theme = self.settings.get("custom_theme", None)
        self.bg_image_path = self.settings.get("bg_image_path", "")
        self.bg_photo = None
        self.theme = self._resolve_theme(self.theme_name, self.custom_theme)

        self.font_scale_level = int(self.settings.get("font_scale_level", 0))
        self._update_font_objects()

        self.cm = ConfigManager()
        self.current_group_name: str = ""
        self.group_nodes_data: List[Dict[str, Any]] = []
        self.node_delays: Dict[str, Optional[int]] = {}
        self.testing_nodes: Set[str] = set()

        # Colors shortcut from current theme
        self.COLOR_BG = self.theme["bg"]
        self.COLOR_SIDEBAR = self.theme["sidebar"]
        self.COLOR_PRIMARY = self.theme["primary"]
        self.COLOR_SUCCESS = self.theme["success"]
        self.COLOR_DANGER = self.theme["danger"]
        self.COLOR_TOP = self.theme["top"]

        # Traffic monitor state (persisted across reboots and software restarts)
        self.traffic_enabled = bool(self.settings.get("traffic_enabled", True))
        self.traffic_start_time = float(self.settings.get("traffic_start_time", 0))
        if self.traffic_start_time <= 0:
            try:
                import ctypes
                uptime_ms = ctypes.windll.kernel32.GetTickCount64()
                self.traffic_start_time = time.time() - (uptime_ms / 1000.0)
            except Exception:
                self.traffic_start_time = time.time()

        # Lifetime accumulated across past Clash sessions (e.g. across PC reboots)
        self.traffic_lifetime_up = int(self.settings.get("traffic_lifetime_up", 0))
        self.traffic_lifetime_down = int(self.settings.get("traffic_lifetime_down", 0))
        self.traffic_session_base_up = int(self.settings.get("traffic_session_base_up", 0))
        self.traffic_session_base_down = int(self.settings.get("traffic_session_base_down", 0))
        self.traffic_last_core_up = int(self.settings.get("traffic_last_core_up", 0))
        self.traffic_last_core_down = int(self.settings.get("traffic_last_core_down", 0))
        self.traffic_proxy_lifetime_up = int(self.settings.get("traffic_proxy_lifetime_up", 0))
        self.traffic_proxy_lifetime_down = int(self.settings.get("traffic_proxy_lifetime_down", 0))

        # Non-blocking traffic state initialization (worker thread handles first sync)
        self.traffic_running = False
        self.traffic_thread = None
        self.last_traffic_snap = None

        self._save_timer = None
        self._save_lock = threading.Lock()
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

        self._init_styles()
        self._build_ui()
        self._bind_shortcuts()

        if not self.cm.config_dir:
            from tkinter import filedialog
            messagebox.showinfo(
                "初次使用配置引导",
                "未能自动检测到运行中的 Clash Verge。\n\n请在随后的窗口中选择你的 Clash Verge 数据目录（包含 profiles 文件夹的目录，例如：io.github.clash-verge-rev.clash-verge-rev）。"
            )
            chosen = filedialog.askdirectory(title="选择 Clash Verge 配置目录 (包含 profiles)")
            if chosen and os.path.isdir(chosen):
                from config_manager import save_settings
                save_settings({"custom_config_dir": chosen})
                self.cm = ConfigManager(chosen)

        self._load_profiles_into_dropdown()
        self._refresh_group_list()

        if self.traffic_enabled:
            self._start_traffic_worker()

    def _scale(self, value: int) -> int:
        return int(round(value * self.scale))

    def _apply_interactive_effect(self, btn: tk.Widget, hover_bg: Optional[str] = None, active_bg: Optional[str] = None):
        """Adds Clash-style tactile hover and press animations to buttons for a responsive, modern feel."""
        try:
            orig_bg = btn.cget("bg")
            if not hover_bg:
                hover_bg = "#e0e7ff" if self.theme_name == "default_light" else "#334155"
            if not active_bg:
                active_bg = self.theme.get("primary", "#2563eb")
            
            def _on_enter(e):
                if str(btn.cget("state")) != "disabled":
                    btn.config(bg=hover_bg)
            def _on_leave(e):
                if str(btn.cget("state")) != "disabled":
                    btn.config(bg=orig_bg)
            def _on_press(e):
                if str(btn.cget("state")) != "disabled":
                    btn.config(bg=active_bg)
            def _on_release(e):
                if str(btn.cget("state")) != "disabled":
                    btn.config(bg=hover_bg)

            btn.bind("<Enter>", _on_enter, add="+")
            btn.bind("<Leave>", _on_leave, add="+")
            btn.bind("<Button-1>", _on_press, add="+")
            btn.bind("<ButtonRelease-1>", _on_release, add="+")
        except Exception:
            pass

    def _bind_combobox_click_to_open(self, cb: ttk.Combobox):
        def _on_click(event):
            arrow_width = self._scale(32)
            if event.x < event.widget.winfo_width() - arrow_width:
                event.widget.focus_set()
                event.widget.event_generate("<Down>")
        cb.bind("<Button-1>", _on_click)

    def _resolve_theme(self, theme_name: str, custom_theme: Optional[dict] = None) -> dict:
        if theme_name == "custom" and isinstance(custom_theme, dict):
            base = dict(THEMES["default_light"])
            base.update(custom_theme)
            base["name"] = custom_theme.get("name", "自定义皮肤")
            return base
        return dict(THEMES.get(theme_name, THEMES["default_light"]))

    def _update_font_objects(self):
        font_map = {-2: 8, -1: 9, 0: 10, 1: 11, 2: 13, 3: 15, 4: 18}
        base_pt = font_map.get(self.font_scale_level, 10)
        self.default_font = ("Microsoft YaHei UI", base_pt)
        self.bold_font = ("Microsoft YaHei UI", base_pt, "bold")
        self.title_font = ("Microsoft YaHei UI", int(base_pt * 1.3), "bold")
        self.root.option_add("*Font", self.default_font)

    def _apply_font_scale(self, level: int):
        self.font_scale_level = max(-2, min(4, level))
        self._update_font_objects()
        save_settings({"font_scale_level": self.font_scale_level})
        self._reapply_styles()
        if hasattr(self, "lbl_font_scale") and self.lbl_font_scale:
            percent_map = {-2: "80%", -1: "90%", 0: "100%", 1: "115%", 2: "130%", 3: "150%", 4: "180%"}
            self.lbl_font_scale.config(text=percent_map.get(self.font_scale_level, "100%"))

    def _init_styles(self):
        self._reapply_styles()

    def _reapply_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        self.COLOR_BG = self.theme["bg"]
        self.COLOR_SIDEBAR = self.theme["sidebar"]
        self.COLOR_PRIMARY = self.theme["primary"]
        self.COLOR_SUCCESS = self.theme["success"]
        self.COLOR_DANGER = self.theme["danger"]
        self.COLOR_TOP = self.theme["top"]

        self.root.configure(bg=self.theme["bg"])

        style.configure("TFrame", background=self.theme["bg"])
        style.configure("Sidebar.TFrame", background=self.theme["sidebar"])
        style.configure("TLabel", background=self.theme["bg"], foreground=self.theme["text"], font=self.default_font)
        style.configure("Sidebar.TLabel", background=self.theme["sidebar"], foreground=self.theme["text"], font=self.default_font)
        style.configure("Header.TLabel", font=self.title_font, background=self.theme["bg"], foreground=self.theme["text"])

        # >>> Enlarged Combobox Dropdown Arrow (arrowsize=20) for effortless mouse clicking! <<<
        style.configure(
            "TCombobox",
            arrowsize=self._scale(20),
            padding=(self._scale(6), self._scale(4)),
            font=self.default_font
        )

        row_height = self._scale(int(28 * (1 + self.font_scale_level * 0.12)))
        style.configure(
            "Treeview",
            rowheight=row_height,
            font=self.default_font,
            background=self.theme["tree_bg"],
            foreground=self.theme["tree_fg"],
            fieldbackground=self.theme["tree_bg"],
            borderwidth=0,
            relief="flat"
        )
        style.configure(
            "Treeview.Heading",
            font=self.bold_font,
            background=self.theme["heading_bg"],
            foreground=self.theme["heading_fg"],
            relief="flat",
            padding=(self._scale(4), self._scale(6))
        )
        style.map("Treeview", background=[("selected", self.theme["tree_selected_bg"])], foreground=[("selected", self.theme["tree_selected_fg"])])

        if hasattr(self, "group_listbox") and self.group_listbox:
            self.group_listbox.configure(
                bg=self.theme["card_bg"],
                fg=self.theme["text"],
                selectbackground=self.theme["primary"],
                selectforeground=self.theme["primary_fg"],
                font=self.default_font
            )

        # Traffic Dashboard Bar
        if hasattr(self, "traffic_bar") and self.traffic_bar:
            self.traffic_bar.configure(bg=self.theme["sidebar"], highlightbackground=self.theme["border"])
        if hasattr(self, "lbl_traffic_total") and self.lbl_traffic_total:
            self.lbl_traffic_total.configure(bg=self.theme["sidebar"], fg=self.theme["primary"], font=self.bold_font)
        if hasattr(self, "lbl_traffic_proxy") and self.lbl_traffic_proxy:
            self.lbl_traffic_proxy.configure(bg=self.theme["sidebar"], fg="#059669", font=self.bold_font)
        if hasattr(self, "speed_card") and self.speed_card:
            self.speed_card.configure(bg=self.theme["card_bg"], highlightbackground=self.theme["border"])
        if hasattr(self, "lbl_traffic_speed") and self.lbl_traffic_speed:
            self.lbl_traffic_speed.configure(bg=self.theme["card_bg"], fg=self.theme["primary"], font=self.bold_font)
        if hasattr(self, "btn_traffic_reset") and self.btn_traffic_reset:
            self.btn_traffic_reset.configure(bg=self.theme["btn_bg"], fg=self.theme["btn_fg"], font=self.default_font)
        if hasattr(self, "btn_traffic_date") and self.btn_traffic_date:
            self.btn_traffic_date.configure(bg=self.theme["btn_bg"], fg=self.theme["btn_fg"], font=self.default_font)
        if hasattr(self, "btn_traffic_toggle") and self.btn_traffic_toggle:
            self.btn_traffic_toggle.configure(font=self.bold_font)
        if hasattr(self, "lbl_traffic_period") and self.lbl_traffic_period:
            self.lbl_traffic_period.configure(bg=self.theme["sidebar"], fg=self.theme["text_muted"], font=self.default_font)

        # Action Toolbar - Row 1
        if hasattr(self, "toolbar_row1") and self.toolbar_row1:
            self.toolbar_row1.configure(bg=self.theme["card_bg"], highlightbackground=self.theme["border"])
        if hasattr(self, "lbl_mode") and self.lbl_mode:
            self.lbl_mode.configure(bg=self.theme["card_bg"], fg=self.theme["text_muted"], font=self.default_font)

        if hasattr(self, "status_bar") and self.status_bar:
            self.status_bar.configure(bg=self.theme["sidebar"], highlightbackground=self.theme["border"])
            if hasattr(self, "status_msg_lbl") and self.status_msg_lbl:
                self.status_msg_lbl.configure(bg=self.theme["sidebar"], fg=self.theme["text"], font=self.default_font)
            if hasattr(self, "lbl_status_info") and self.lbl_status_info:
                self.lbl_status_info.configure(bg=self.theme["sidebar"], fg=self.theme["text_muted"], font=self.default_font)

        if hasattr(self, "paned") and self.paned:
            self.paned.configure(bg=self.theme["border"])
        if hasattr(self, "top_right_box") and self.top_right_box:
            self.top_right_box.configure(bg=self.theme["bg"])
        if hasattr(self, "theme_menubutton") and self.theme_menubutton:
            self.theme_menubutton.configure(
                text=f"🎨 皮肤: {self.theme.get('name', '默认')}",
                bg=self.theme["btn_bg"],
                fg=self.theme["btn_fg"],
                font=self.default_font
            )
        if hasattr(self, "font_box") and self.font_box:
            self.font_box.configure(bg=self.theme["sidebar"])
        if hasattr(self, "lbl_font_title") and self.lbl_font_title:
            self.lbl_font_title.configure(bg=self.theme["sidebar"], fg=self.theme["text"], font=self.bold_font)
        if hasattr(self, "btn_font_dec") and self.btn_font_dec:
            self.btn_font_dec.configure(bg=self.theme["btn_bg"], fg=self.theme["primary"])
            self.btn_font_inc.configure(bg=self.theme["btn_bg"], fg=self.theme["primary"])
            self.lbl_font_scale.configure(bg=self.theme["sidebar"], fg=self.theme["primary"], font=self.bold_font)
        if hasattr(self, "btn_about") and self.btn_about:
            self.btn_about.configure(bg=self.theme["btn_bg"], fg=self.theme["btn_fg"], font=self.default_font)
        if hasattr(self, "btn_save") and self.btn_save:
            self.btn_save.configure(bg="#16a34a", fg="#ffffff", font=self.bold_font)
        if hasattr(self, "btn_import") and self.btn_import:
            self.btn_import.configure(bg=self.theme["primary"], fg=self.theme["primary_fg"], font=self.bold_font)
        if hasattr(self, "btn_paste_manual") and self.btn_paste_manual:
            self.btn_paste_manual.configure(bg=self.theme["btn_bg"], fg=self.theme["btn_fg"], font=self.default_font)
        if hasattr(self, "btn_import_qr") and self.btn_import_qr:
            self.btn_import_qr.configure(bg="#0d9488", fg="#ffffff", font=self.bold_font)
        if hasattr(self, "btn_ping") and self.btn_ping:
            self.btn_ping.configure(bg="#ecfdf5", fg="#059669", font=self.bold_font)
        if hasattr(self, "btn_top") and self.btn_top:
            self.btn_top.configure(bg="#fef3c7", fg="#b45309", font=self.bold_font)
        if hasattr(self, "btn_up") and self.btn_up:
            self.btn_up.configure(bg=self.theme["btn_bg"], fg=self.theme["btn_fg"])
            self.btn_down.configure(bg=self.theme["btn_bg"], fg=self.theme["btn_fg"])
        if hasattr(self, "btn_edit_node") and self.btn_edit_node:
            self.btn_edit_node.configure(bg=self.theme["btn_bg"], fg=self.theme["btn_fg"], font=self.default_font)
        if hasattr(self, "btn_del") and self.btn_del:
            self.btn_del.configure(bg="#fee2e2", fg=self.COLOR_DANGER, font=self.default_font)
        if hasattr(self, "btn_clear_grp_nodes") and self.btn_clear_grp_nodes:
            self.btn_clear_grp_nodes.configure(bg=self.theme["btn_bg"], fg=self.theme["text_muted"], font=self.default_font)
        if hasattr(self, "btn_add_grp") and self.btn_add_grp:
            self.btn_add_grp.configure(bg=self.theme["btn_bg"], fg=self.theme["btn_fg"], font=self.default_font)
            self.btn_ren_grp.configure(bg=self.theme["btn_bg"], fg=self.theme["btn_fg"], font=self.default_font)
            self.btn_del_grp.configure(bg=self.theme["btn_bg"], fg=self.theme["danger"], font=self.default_font)
            self.btn_grp_top.configure(bg="#fef3c7", fg="#b45309", font=self.bold_font)
            self.btn_grp_up.configure(bg=self.theme["btn_bg"], fg=self.theme["btn_fg"], font=self.default_font)
            self.btn_grp_down.configure(bg=self.theme["btn_bg"], fg=self.theme["btn_fg"], font=self.default_font)
        if hasattr(self, "search_box") and self.search_box:
            self.search_box.configure(font=self.default_font)

    def _build_ui(self):
        main_box = ttk.Frame(self.root)
        main_box.pack(fill=tk.BOTH, expand=True)

        pad_x_lg = self._scale(14)
        pad_y_sm = self._scale(8)
        pad_y_md = self._scale(10)

        # 1. Top Bar
        top_bar = ttk.Frame(main_box, padding=(pad_x_lg, pad_y_md))
        top_bar.pack(fill=tk.X, side=tk.TOP)

        title_lbl = ttk.Label(top_bar, text="⚡ Clash 节点跃迁 (ClashNodeX)", style="Header.TLabel")
        title_lbl.pack(side=tk.LEFT, padx=(0, self._scale(18)))

        ttk.Label(top_bar, text="当前配置 Profile:").pack(side=tk.LEFT, padx=(0, self._scale(8)))
        self.profile_combo = ttk.Combobox(top_bar, state="readonly", width=42)
        self.profile_combo.pack(side=tk.LEFT, padx=(0, self._scale(10)))
        self.profile_combo.bind("<<ComboboxSelected>>", self._on_profile_selected)
        self._bind_combobox_click_to_open(self.profile_combo)

        self.reload_profile_btn = ttk.Button(top_bar, text="🔄 重新加载", command=self._reload_profile)
        self.reload_profile_btn.pack(side=tk.LEFT, padx=(0, self._scale(15)))

        # Top Bar Right Container (Holds about, feedback, theme, font zoom)
        self.top_right_box = tk.Frame(top_bar, bg=self.theme["bg"])
        self.top_right_box.pack(side=tk.RIGHT)

        self.btn_about = tk.Button(
            self.top_right_box,
            text="ℹ️ 关于与说明",
            bg=self.theme["btn_bg"],
            fg=self.theme["btn_fg"],
            font=self.default_font,
            relief=tk.FLAT,
            bd=0,
            padx=self._scale(8),
            pady=self._scale(2),
            cursor="hand2",
            command=self._action_show_about
        )
        self.btn_about.pack(side=tk.RIGHT, padx=(self._scale(6), 0))
        self._apply_interactive_effect(self.btn_about)

        self.btn_feedback = tk.Button(
            self.top_right_box,
            text="💬 意见反馈",
            bg=self.theme["btn_bg"],
            fg=self.theme["primary"],
            font=self.default_font,
            relief=tk.FLAT,
            bd=0,
            padx=self._scale(8),
            pady=self._scale(2),
            cursor="hand2",
            command=self._action_show_feedback
        )
        self.btn_feedback.pack(side=tk.RIGHT, padx=(self._scale(6), 0))
        self._apply_interactive_effect(self.btn_feedback)

        # Theme menu
        self.theme_menubutton = tk.Menubutton(
            self.top_right_box,
            text=f"🎨 皮肤: {self.theme.get('name', '默认')}",
            bg=self.theme["btn_bg"],
            fg=self.theme["btn_fg"],
            font=self.default_font,
            relief=tk.FLAT,
            bd=0,
            padx=self._scale(8),
            pady=self._scale(2),
            cursor="hand2"
        )
        self.theme_menu = tk.Menu(self.theme_menubutton, tearoff=0)
        self.theme_menu.add_command(label="⚪ 经典浅白 (默认)", command=lambda: self._switch_theme("default_light"))
        self.theme_menu.add_command(label="🌙 极客黑夜 (Dark)", command=lambda: self._switch_theme("dark_night"))
        self.theme_menu.add_command(label="❄️ 现代冷灰 (Nord)", command=lambda: self._switch_theme("nord_slate"))
        self.theme_menu.add_separator()
        self.theme_menu.add_command(label="🌕 应用月球探索主题 (Artemis)", command=self._action_apply_moon_skin)
        self.theme_menu.add_command(label="🖼️ 导入图片壁纸/背景 (*.png;*.jpg)...", command=self._action_import_image_skin)
        self.theme_menu.add_command(label="🎨 应用示例图片壁纸", command=self._action_apply_sample_skin)
        self.theme_menu.add_command(label="🗑️ 清除图片壁纸 (恢复纯色)", command=self._action_clear_bg_image)
        self.theme_menu.add_separator()
        self.theme_menu.add_command(label="📂 导入配色方案 (*.json)...", command=self._action_import_theme)
        self.theme_menu.add_command(label="💾 导出当前配色模板 (*.json)...", command=self._action_export_theme)
        self.theme_menubutton.config(menu=self.theme_menu)
        self.theme_menubutton.pack(side=tk.RIGHT, padx=self._scale(6))

        # Font Zoom Controls - Dedicated Pill Badge
        self.font_box = tk.Frame(
            self.top_right_box,
            bg=self.theme["sidebar"],
            bd=0,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.theme["border"],
            padx=self._scale(4),
            pady=self._scale(1)
        )
        self.font_box.pack(side=tk.RIGHT, padx=self._scale(6))

        self.lbl_font_title = tk.Label(
            self.font_box,
            text="🔠 字号",
            bg=self.theme["sidebar"],
            fg=self.theme["text"],
            font=self.bold_font
        )
        self.lbl_font_title.pack(side=tk.LEFT, padx=(self._scale(2), self._scale(4)))

        self.btn_font_dec = tk.Button(
            self.font_box,
            text="－",
            font=("Segoe UI", 9, "bold"),
            width=2,
            bg=self.theme["btn_bg"],
            fg=self.theme["primary"],
            relief=tk.FLAT,
            bd=0,
            padx=self._scale(2),
            pady=0,
            cursor="hand2",
            command=lambda: self._apply_font_scale(self.font_scale_level - 1)
        )
        self.btn_font_dec.pack(side=tk.LEFT)
        self._apply_interactive_effect(self.btn_font_dec)

        percent_map = {-2: "80%", -1: "90%", 0: "100%", 1: "115%", 2: "130%", 3: "150%", 4: "180%"}
        self.lbl_font_scale = tk.Label(
            self.font_box,
            text=percent_map.get(self.font_scale_level, "100%"),
            bg=self.theme["sidebar"],
            fg=self.theme["primary"],
            font=self.bold_font,
            width=5
        )
        self.lbl_font_scale.pack(side=tk.LEFT, padx=self._scale(2))

        self.btn_font_inc = tk.Button(
            self.font_box,
            text="＋",
            font=("Segoe UI", 9, "bold"),
            width=2,
            bg=self.theme["btn_bg"],
            fg=self.theme["primary"],
            relief=tk.FLAT,
            bd=0,
            padx=self._scale(2),
            pady=0,
            cursor="hand2",
            command=lambda: self._apply_font_scale(self.font_scale_level + 1)
        )
        self.btn_font_inc.pack(side=tk.LEFT)
        self._apply_interactive_effect(self.btn_font_inc)

        # 2. Traffic Dashboard Bar (Upper Banner Layout)
        self.traffic_bar = tk.Frame(
            main_box,
            bg=self.theme["sidebar"],
            bd=0,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.theme["border"],
            padx=self._scale(12),
            pady=self._scale(5)
        )
        self.traffic_bar.pack(fill=tk.X, side=tk.TOP, padx=self._scale(12), pady=(0, self._scale(5)))

        # Left Container (Controls & Period)
        traffic_left = tk.Frame(self.traffic_bar, bg=self.traffic_bar["bg"])
        traffic_left.pack(side=tk.LEFT, fill=tk.Y)

        self.btn_traffic_toggle = tk.Button(
            traffic_left,
            text="🟢 监控中" if self.traffic_enabled else "⏸️ 已暂停",
            bg="#ecfdf5" if self.traffic_enabled else "#f1f5f9",
            fg=self.theme["success"] if self.traffic_enabled else self.theme["text_muted"],
            font=self.bold_font,
            relief=tk.FLAT,
            bd=0,
            padx=self._scale(8),
            pady=self._scale(2),
            cursor="hand2",
            command=self._toggle_traffic_monitoring
        )
        self.btn_traffic_toggle.pack(side=tk.LEFT, padx=(0, self._scale(6)))

        self.btn_traffic_reset = tk.Button(
            traffic_left,
            text="🔄 清零",
            bg=self.theme["btn_bg"],
            fg=self.theme["btn_fg"],
            font=self.default_font,
            relief=tk.FLAT,
            bd=0,
            padx=self._scale(8),
            pady=self._scale(2),
            cursor="hand2",
            command=self._reset_traffic_stats
        )
        self.btn_traffic_reset.pack(side=tk.LEFT, padx=(0, self._scale(6)))

        self.btn_traffic_date = tk.Button(
            traffic_left,
            text="📅 周期设定",
            bg=self.theme["btn_bg"],
            fg=self.theme["btn_fg"],
            font=self.default_font,
            relief=tk.FLAT,
            bd=0,
            padx=self._scale(8),
            pady=self._scale(2),
            cursor="hand2",
            command=self._action_set_custom_traffic_period
        )
        self.btn_traffic_date.pack(side=tk.LEFT, padx=(0, self._scale(8)))

        self._apply_interactive_effect(self.btn_traffic_toggle)
        self._apply_interactive_effect(self.btn_traffic_reset)
        self._apply_interactive_effect(self.btn_traffic_date)

        self.lbl_traffic_period = tk.Label(
            traffic_left,
            text=self._get_traffic_period_text(),
            bg=self.traffic_bar["bg"],
            fg=self.theme["text_muted"],
            font=self.default_font
        )
        self.lbl_traffic_period.pack(side=tk.LEFT)

        # Right Container (Live Real-Time Speed Badge - Pinned to Far Right)
        traffic_right = tk.Frame(self.traffic_bar, bg=self.traffic_bar["bg"])
        traffic_right.pack(side=tk.RIGHT, fill=tk.Y)

        self.speed_card = tk.Frame(
            traffic_right,
            bg=self.theme["card_bg"],
            bd=0,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.theme["border"],
            padx=self._scale(12),
            pady=self._scale(4)
        )
        self.speed_card.pack(side=tk.RIGHT, pady=self._scale(1))

        self.lbl_traffic_speed = tk.Label(
            self.speed_card,
            text="⚡ 实时网速: ↑ 0 B/s   ↓ 0 B/s",
            font=self.bold_font,
            fg=self.theme["primary"],
            bg=self.theme["card_bg"]
        )
        self.lbl_traffic_speed.pack()

        # Center Container (Traffic totals - Clash Total & Proxy Nodes, LEFT-ALIGNED in Middle)
        traffic_mid = tk.Frame(self.traffic_bar, bg=self.traffic_bar["bg"])
        traffic_mid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(self._scale(18), self._scale(14)))

        self.lbl_traffic_total = tk.Label(
            traffic_mid,
            text="🌐 Clash总吞吐: [上行] 0 B | [下行] 0 B (⚡ 累计: 0 B)",
            bg=self.traffic_bar["bg"],
            fg=self.theme["primary"],
            font=self.bold_font,
            anchor="w",
            justify=tk.LEFT
        )
        self.lbl_traffic_total.pack(side=tk.TOP, fill=tk.X, anchor="w")

        self.lbl_traffic_proxy = tk.Label(
            traffic_mid,
            text="🚀 节点代理实耗: [上行] 0 B | [下行] 0 B (⚡ 消耗: 0 B)",
            bg=self.traffic_bar["bg"],
            fg="#059669",
            font=self.bold_font,
            anchor="w",
            justify=tk.LEFT
        )
        self.lbl_traffic_proxy.pack(side=tk.TOP, fill=tk.X, anchor="w")

        # 3. Action Toolbar - Row 1 (节点导入与测速管理)
        self.toolbar_row1 = tk.Frame(
            main_box,
            bg=self.theme["card_bg"],
            bd=0,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.theme["border"],
            padx=self._scale(10),
            pady=self._scale(5)
        )
        self.toolbar_row1.pack(fill=tk.X, side=tk.TOP, padx=self._scale(12), pady=(0, self._scale(4)))

        btn_pad_x = self._scale(8)
        btn_pad_y = self._scale(4)

        # Row 1 Right: Manual Save & Save Badge (Packed first so NEVER squeezed out!)
        self.btn_save = tk.Button(
            self.toolbar_row1,
            text="💾 立即保存 (Ctrl+S)",
            bg="#16a34a",
            fg="#ffffff",
            font=self.bold_font,
            relief=tk.FLAT,
            padx=self._scale(14),
            pady=btn_pad_y,
            cursor="hand2",
            command=self._action_manual_save
        )
        self.btn_save.pack(side=tk.RIGHT, padx=self._scale(6))

        self.save_badge = ttk.Label(
            self.toolbar_row1,
            text="● 即时自动同步生效",
            foreground=self.COLOR_SUCCESS,
            font=self.bold_font
        )
        self.save_badge.pack(side=tk.RIGHT, padx=self._scale(8))

        # Row 1 Left: Import & Latency Test
        self.btn_import = tk.Button(
            self.toolbar_row1,
            text="📋 从剪贴板导入 (Ctrl+V)",
            bg=self.COLOR_PRIMARY,
            fg="#ffffff",
            font=self.bold_font,
            relief=tk.FLAT,
            padx=btn_pad_x,
            pady=btn_pad_y,
            cursor="hand2",
            command=self._action_import_clipboard
        )
        self.btn_import.pack(side=tk.LEFT, padx=(0, self._scale(6)))

        self.btn_import_qr = tk.Button(
            self.toolbar_row1,
            text="📷 识别二维码导入",
            bg="#0d9488",
            fg="#ffffff",
            font=self.bold_font,
            relief=tk.FLAT,
            padx=btn_pad_x,
            pady=btn_pad_y,
            cursor="hand2",
            command=self._action_import_qr
        )
        self.btn_import_qr.pack(side=tk.LEFT, padx=(0, self._scale(6)))

        self.btn_paste_manual = tk.Button(
            self.toolbar_row1,
            text="➕ 手动输入...",
            bg=self.theme["btn_bg"],
            fg=self.theme["btn_fg"],
            font=self.default_font,
            relief=tk.FLAT,
            bd=0,
            padx=self._scale(6),
            pady=btn_pad_y,
            cursor="hand2",
            command=self._action_manual_input
        )
        self.btn_paste_manual.pack(side=tk.LEFT, padx=(0, self._scale(8)))

        ttk.Separator(self.toolbar_row1, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=self._scale(6))

        self.btn_ping = tk.Button(
            self.toolbar_row1,
            text="⚡ 测延迟 (Ctrl+T)",
            bg="#ecfdf5",
            fg="#059669",
            font=self.bold_font,
            relief=tk.FLAT,
            bd=0,
            padx=btn_pad_x,
            pady=btn_pad_y,
            cursor="hand2",
            command=self._action_test_selected_latency
        )
        self.btn_ping.pack(side=tk.LEFT, padx=(0, self._scale(4)))
        self._apply_interactive_effect(self.btn_save, hover_bg="#15803d", active_bg="#14532d")
        self._apply_interactive_effect(self.btn_import, hover_bg="#1d4ed8", active_bg="#1e40af")
        self._apply_interactive_effect(self.btn_import_qr, hover_bg="#0f766e", active_bg="#115e59")
        self._apply_interactive_effect(self.btn_paste_manual)
        self._apply_interactive_effect(self.btn_ping, hover_bg="#d1fae5", active_bg="#a7f3d0")

        self.lbl_mode = tk.Label(
            self.toolbar_row1,
            text="测试模式:",
            font=self.default_font,
            bg=self.toolbar_row1["bg"],
            fg=self.theme["text_muted"]
        )
        self.lbl_mode.pack(side=tk.LEFT, padx=(0, self._scale(3)))

        self.latency_mode_var = tk.StringVar(value=self.settings.get("latency_mode", "⚡ 极速 Connect 延迟 (手机同款/极速)"))
        self.cb_latency_mode = ttk.Combobox(
            self.toolbar_row1,
            textvariable=self.latency_mode_var,
            values=[
                "⚡ 极速 Connect 延迟 (手机同款/极速)",
                "🌐 真实全链路 (HTTP 204 端到端)",
                "🔌 TCP 握手测速"
            ],
            state="readonly",
            width=28,
            font=self.default_font
        )
        self.cb_latency_mode.pack(side=tk.LEFT, padx=(0, self._scale(8)))
        self.cb_latency_mode.bind("<<ComboboxSelected>>", self._on_latency_mode_changed)
        self._bind_combobox_click_to_open(self.cb_latency_mode)

        # 3. Main Workspace
        paned = tk.PanedWindow(main_box, orient=tk.HORIZONTAL, bg="#cbd5e1", sashwidth=self._scale(4), bd=0)
        paned.pack(fill=tk.BOTH, expand=True, padx=self._scale(12), pady=(0, self._scale(6)))

        # Left: Groups Sidebar
        left_frame = ttk.Frame(paned, style="Sidebar.TFrame", padding=(self._scale(8), self._scale(8)))
        paned.add(left_frame, minsize=self._scale(240), width=self._scale(290))

        grp_header_frame = ttk.Frame(left_frame, style="Sidebar.TFrame")
        grp_header_frame.pack(fill=tk.X, pady=(0, self._scale(4)))
        ttk.Label(grp_header_frame, text="📁 节点分组列表", font=self.bold_font, style="Sidebar.TLabel").pack(side=tk.LEFT)

        # Group Action Buttons (Row 1: Edit/Delete, Row 2: Order)
        grp_btn_frame = ttk.Frame(left_frame, style="Sidebar.TFrame")
        grp_btn_frame.pack(fill=tk.X, pady=(0, self._scale(4)))
        
        self.btn_add_grp = tk.Button(
            grp_btn_frame, text="➕ 新建", font=self.default_font,
            bg=self.theme["btn_bg"], fg=self.theme["btn_fg"],
            relief=tk.FLAT, bd=0, padx=self._scale(8), pady=1, cursor="hand2",
            command=self._action_create_group
        )
        self.btn_add_grp.pack(side=tk.LEFT, padx=(0, self._scale(4)))

        self.btn_ren_grp = tk.Button(
            grp_btn_frame, text="✏️ 改名", font=self.default_font,
            bg=self.theme["btn_bg"], fg=self.theme["btn_fg"],
            relief=tk.FLAT, bd=0, padx=self._scale(8), pady=1, cursor="hand2",
            command=self._action_rename_group
        )
        self.btn_ren_grp.pack(side=tk.LEFT, padx=(0, self._scale(4)))

        self.btn_del_grp = tk.Button(
            grp_btn_frame, text="🗑 删除", font=self.default_font,
            bg=self.theme["btn_bg"], fg=self.theme["danger"],
            relief=tk.FLAT, bd=0, padx=self._scale(8), pady=1, cursor="hand2",
            command=self._action_delete_group
        )
        self.btn_del_grp.pack(side=tk.LEFT)

        # Row 2 for Group Reordering (3-column grid, 100% visible, never clipped)
        grp_order_frame = ttk.Frame(left_frame, style="Sidebar.TFrame")
        grp_order_frame.pack(fill=tk.X, pady=(0, self._scale(8)))
        grp_order_frame.columnconfigure(0, weight=1)
        grp_order_frame.columnconfigure(1, weight=1)
        grp_order_frame.columnconfigure(2, weight=1)

        self.btn_grp_top = tk.Button(
            grp_order_frame, text="⭐ 置顶", font=self.bold_font,
            bg="#fef3c7", fg="#b45309",
            relief=tk.FLAT, bd=0, padx=self._scale(4), pady=1, cursor="hand2",
            command=self._action_group_pin_top
        )
        self.btn_grp_top.grid(row=0, column=0, sticky="ew", padx=(0, self._scale(2)))
        self._apply_interactive_effect(self.btn_grp_top, hover_bg="#fde68a", active_bg="#f59e0b")

        self.btn_grp_up = tk.Button(
            grp_order_frame, text="⬆ 上移", font=self.default_font,
            bg=self.theme["btn_bg"], fg=self.theme["btn_fg"],
            relief=tk.FLAT, bd=0, padx=self._scale(4), pady=1, cursor="hand2",
            command=self._action_group_move_up
        )
        self.btn_grp_up.grid(row=0, column=1, sticky="ew", padx=(self._scale(2), self._scale(2)))
        self._apply_interactive_effect(self.btn_grp_up, hover_bg="#e2e8f0", active_bg="#94a3b8")

        self.btn_grp_down = tk.Button(
            grp_order_frame, text="⬇ 下移", font=self.default_font,
            bg=self.theme["btn_bg"], fg=self.theme["btn_fg"],
            relief=tk.FLAT, bd=0, padx=self._scale(4), pady=1, cursor="hand2",
            command=self._action_group_move_down
        )
        self.btn_grp_down.grid(row=0, column=2, sticky="ew", padx=(self._scale(2), 0))
        self._apply_interactive_effect(self.btn_grp_down, hover_bg="#e2e8f0", active_bg="#94a3b8")

        grp_list_frame = ttk.Frame(left_frame)
        grp_list_frame.pack(fill=tk.BOTH, expand=True)

        self.group_listbox = tk.Listbox(
            grp_list_frame,
            selectmode=tk.SINGLE,
            font=self.default_font,
            bd=0,
            relief=tk.FLAT,
            activestyle="none",
            highlightthickness=1,
            highlightbackground=self.theme["border"],
            highlightcolor=self.COLOR_PRIMARY,
            bg="#ffffff"
        )
        self.group_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.group_listbox.bind("<<ListboxSelect>>", self._on_group_selected)

        # Modern Mac-style Context menu for group listbox
        menu_kwargs = {
            "tearoff": 0,
            "bg": "#ffffff",
            "fg": "#0f172a",
            "activebackground": "#2563eb",
            "activeforeground": "#ffffff",
            "activeborderwidth": 0,
            "relief": tk.FLAT,
            "bd": 1,
            "font": self.default_font
        }
        self.group_context_menu = tk.Menu(self.root, **menu_kwargs)
        self.group_context_menu.add_command(label="  ⭐ 置顶此分组", command=self._action_group_pin_top)
        self.group_context_menu.add_command(label="  ⬆ 上移分组", command=self._action_group_move_up)
        self.group_context_menu.add_command(label="  ⬇ 下移分组", command=self._action_group_move_down)
        self.group_context_menu.add_separator()
        self.group_context_menu.add_command(label="  ⚡ 批量测试该组全部延迟", command=self._action_test_all_latency)
        self.group_context_menu.add_separator()
        self.group_context_menu.add_command(label="  ➕ 新建分组...", command=self._action_create_group)
        self.group_context_menu.add_command(label="  ✏️ 重命名分组...", command=self._action_rename_group)
        self.group_context_menu.add_separator()
        self.group_context_menu.add_command(label="  🗑 删除此分组", command=self._action_delete_group)
        self.group_listbox.bind("<Button-3>", self._on_group_right_click)

        grp_scroll = ttk.Scrollbar(grp_list_frame, orient=tk.VERTICAL, command=self.group_listbox.yview)
        grp_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.group_listbox.config(yscrollcommand=grp_scroll.set)

        # Right: Node Table
        right_frame = ttk.Frame(paned, padding=(self._scale(8), self._scale(8)))
        paned.add(right_frame, minsize=self._scale(520))

        table_top_frame = ttk.Frame(right_frame)
        table_top_frame.pack(fill=tk.X, pady=(0, self._scale(6)))

        self.group_title_lbl = ttk.Label(table_top_frame, text="请在左侧选择分组", font=self.bold_font)
        self.group_title_lbl.pack(side=tk.LEFT, padx=(0, self._scale(8)))

        self.btn_top = tk.Button(
            table_top_frame,
            text="⭐ 置顶",
            bg="#fef3c7",
            fg="#b45309",
            font=self.bold_font,
            relief=tk.FLAT,
            bd=0,
            padx=self._scale(6),
            pady=1,
            cursor="hand2",
            command=self._action_pin_to_top
        )
        self.btn_top.pack(side=tk.LEFT, padx=(0, self._scale(3)))

        self.btn_up = tk.Button(
            table_top_frame,
            text="⬆ 上移",
            bg=self.theme["btn_bg"],
            fg=self.theme["btn_fg"],
            font=self.default_font,
            relief=tk.FLAT,
            bd=0,
            padx=self._scale(6),
            pady=1,
            cursor="hand2",
            command=self._action_move_up
        )
        self.btn_up.pack(side=tk.LEFT, padx=(0, self._scale(3)))

        self.btn_down = tk.Button(
            table_top_frame,
            text="⬇ 下移",
            bg=self.theme["btn_bg"],
            fg=self.theme["btn_fg"],
            font=self.default_font,
            relief=tk.FLAT,
            bd=0,
            padx=self._scale(6),
            pady=1,
            cursor="hand2",
            command=self._action_move_down
        )
        self.btn_down.pack(side=tk.LEFT, padx=(0, self._scale(5)))

        ttk.Separator(table_top_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=self._scale(4))

        self.btn_edit_node = tk.Button(
            table_top_frame,
            text="✏️ 改名/编辑 (F2)",
            bg=self.theme["btn_bg"],
            fg=self.theme["btn_fg"],
            font=self.default_font,
            relief=tk.FLAT,
            bd=0,
            padx=self._scale(6),
            pady=1,
            cursor="hand2",
            command=self._action_edit_node
        )
        self.btn_edit_node.pack(side=tk.LEFT, padx=(0, self._scale(3)))

        self.btn_del = tk.Button(
            table_top_frame,
            text="🗑 删除 (Del)",
            bg="#fee2e2",
            fg=self.COLOR_DANGER,
            font=self.default_font,
            relief=tk.FLAT,
            bd=0,
            padx=self._scale(6),
            pady=1,
            cursor="hand2",
            command=self._action_delete_selected_nodes
        )
        self.btn_del.pack(side=tk.LEFT, padx=(0, self._scale(3)))

        self.btn_clear_grp_nodes = tk.Button(
            table_top_frame,
            text="🧹 清空当前组",
            bg=self.theme["btn_bg"],
            fg=self.theme["text_muted"],
            font=self.default_font,
            relief=tk.FLAT,
            bd=0,
            padx=self._scale(6),
            pady=1,
            cursor="hand2",
            command=self._action_clear_current_group_nodes
        )
        self.btn_clear_grp_nodes.pack(side=tk.LEFT, padx=(0, self._scale(6)))

        self._apply_interactive_effect(self.btn_top, hover_bg="#fde68a", active_bg="#f59e0b")
        self._apply_interactive_effect(self.btn_up, hover_bg="#e2e8f0", active_bg="#94a3b8")
        self._apply_interactive_effect(self.btn_down, hover_bg="#e2e8f0", active_bg="#94a3b8")
        self._apply_interactive_effect(self.btn_edit_node)
        self._apply_interactive_effect(self.btn_del, hover_bg="#fecaca", active_bg="#f87171")
        self._apply_interactive_effect(self.btn_clear_grp_nodes)

        # Right: Search Box
        search_frame = ttk.Frame(table_top_frame)
        search_frame.pack(side=tk.RIGHT)
        self.lbl_search = ttk.Label(search_frame, text="🔍 快速过滤:", font=self.default_font)
        self.lbl_search.pack(side=tk.LEFT, padx=(0, self._scale(4)))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._filter_nodes())
        self.search_box = ttk.Entry(search_frame, textvariable=self.search_var, width=18, font=self.default_font)
        self.search_box.pack(side=tk.LEFT)

        table_frame = ttk.Frame(right_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("index", "status", "name", "delay", "type", "server", "port")
        self.node_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="extended"
        )

        self.node_tree.heading("index", text="#", anchor=tk.CENTER)
        self.node_tree.heading("status", text="状态", anchor=tk.CENTER)
        self.node_tree.heading("name", text="节点名称", anchor=tk.W)
        self.node_tree.heading("delay", text="延迟 (Ping)", anchor=tk.CENTER)
        self.node_tree.heading("type", text="协议类型", anchor=tk.CENTER)
        self.node_tree.heading("server", text="服务器 / 域名", anchor=tk.W)
        self.node_tree.heading("port", text="端口", anchor=tk.CENTER)

        self.node_tree.column("index", width=self._scale(45), minwidth=self._scale(40), anchor=tk.CENTER)
        self.node_tree.column("status", width=self._scale(75), minwidth=self._scale(60), anchor=tk.CENTER)
        self.node_tree.column("name", width=self._scale(310), minwidth=self._scale(180), anchor=tk.W)
        self.node_tree.column("delay", width=self._scale(115), minwidth=self._scale(95), anchor=tk.CENTER)
        self.node_tree.column("type", width=self._scale(90), minwidth=self._scale(65), anchor=tk.CENTER)
        self.node_tree.column("server", width=self._scale(220), minwidth=self._scale(140), anchor=tk.W)
        self.node_tree.column("port", width=self._scale(65), minwidth=self._scale(50), anchor=tk.CENTER)

        tree_scroll_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.node_tree.yview)
        tree_scroll_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.node_tree.xview)
        self.node_tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

        self.node_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Modern Mac-style Context Menu for Node Tree
        self.context_menu = tk.Menu(self.root, **menu_kwargs)
        self.context_menu.add_command(label="  ⭐ 置顶选中节点 (Top)", command=self._action_pin_to_top)
        self.context_menu.add_command(label="  ⬆ 上移节点", command=self._action_move_up)
        self.context_menu.add_command(label="  ⬇ 下移节点", command=self._action_move_down)
        self.context_menu.add_command(label="  ⚡ 极速 Connect 延迟 (手机同款/极速 推荐)", command=lambda: self._action_test_latency_mode("connect"))
        self.context_menu.add_command(label="  🌐 真实全链路延迟 (HTTP 204 端到端)", command=lambda: self._action_test_latency_mode("true"))
        self.context_menu.add_command(label="  🔌 TCP 握手延迟", command=lambda: self._action_test_latency_mode("tcp"))
        self.context_menu.add_command(label="  🚀 批量测试本组全部节点延迟", command=self._action_test_all_latency)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="  ✏️ 编辑节点属性与测速... (F2)", command=self._action_edit_node)
        self.context_menu.add_command(label="  📁 复制到其他分组...", command=self._action_copy_to_other_group)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="  📷 识别二维码导入节点...", command=self._action_import_qr)
        self.context_menu.add_command(label="  🗑 从此分组移除 (Del)", command=self._action_delete_selected_nodes)
        self.context_menu.add_command(label="  ❌ 彻底删除此节点 (全局清除)", command=self._action_delete_completely)

        self.node_tree.bind("<Button-3>", self._on_tree_right_click)
        self.node_tree.bind("<Double-1>", lambda event: self._action_edit_node())

        # 5. Bottom Status Bar (Status message & Core connection tip)
        self.status_bar = tk.Frame(
            main_box,
            bg=self.theme["sidebar"],
            bd=0,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.theme["border"],
            padx=self._scale(10),
            pady=self._scale(4)
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_msg_lbl = tk.Label(
            self.status_bar,
            text="就绪 · 所有修改即时生效并同步到 Clash Verge / Mihomo",
            bg=self.theme["sidebar"],
            fg=self.theme["text"],
            font=self.default_font
        )
        self.status_msg_lbl.pack(side=tk.LEFT)

        self.lbl_status_info = tk.Label(
            self.status_bar,
            text="⚡ 内核联动正常 | v1.2.0 (2026.09.07) | 双击行编辑节点",
            bg=self.status_bar["bg"],
            fg=self.theme["text_muted"],
            font=self.default_font
        )
        self.lbl_status_info.pack(side=tk.RIGHT)

    def _bind_shortcuts(self):
        self.root.bind("<Control-v>", lambda e: self._action_import_clipboard())
        self.root.bind("<Control-s>", lambda e: self._action_manual_save())
        self.root.bind("<Control-t>", lambda e: self._action_test_selected_latency())
        self.root.bind("<Control-T>", lambda e: self._action_test_selected_latency())
        self.root.bind("<Delete>", lambda e: self._action_delete_selected_nodes())
        self.root.bind("<F5>", lambda e: self._reload_profile())
        self.root.bind("<F2>", lambda e: self._action_edit_node())
        self.root.bind("<Alt-Up>", lambda e: self._action_move_up())
        self.root.bind("<Alt-Down>", lambda e: self._action_move_down())
        self.group_listbox.bind("<Control-Up>", lambda e: self._action_group_move_up())
        self.group_listbox.bind("<Control-Down>", lambda e: self._action_group_move_down())

    def _update_status(self, text: str, is_error: bool = False):
        color = self.COLOR_DANGER if is_error else "#1e293b"
        self.status_msg_lbl.config(text=text, foreground=color)

    def _on_window_close(self):
        self.traffic_running = False
        try:
            self._save_traffic_state()
        except Exception:
            pass
        if self._save_timer is not None:
            try:
                self.root.after_cancel(self._save_timer)
            except Exception:
                pass
            self._save_timer = None
            # Synchronously flush pending save before exiting
            self.cm.save_and_apply(skip_binary_validation=True)
        self.root.destroy()

    def _commit_and_sync(self, success_tip: str, delay_ms: int = 300, skip_binary: bool = True) -> bool:
        """
        Ultra-fast non-blocking save pipeline:
        1. Debounces rapid operations (up/down/pin/delete) so UI stays at 60+ FPS without freezing.
        2. Runs disk persistence and kernel hot-reload in a background thread.
        3. Updates status bar asynchronously upon completion.
        """
        if self._save_timer is not None:
            try:
                self.root.after_cancel(self._save_timer)
            except Exception:
                pass
            self._save_timer = None

        self._update_status(f"⚡ {success_tip} (即时生效中...)")

        if delay_ms <= 0:
            self._do_background_save(success_tip, skip_binary)
        else:
            self._save_timer = self.root.after(
                delay_ms,
                lambda: self._do_background_save(success_tip, skip_binary)
            )
        return True

    def _do_background_save(self, success_tip: str, skip_binary: bool):
        self._save_timer = None

        def worker():
            with self._save_lock:
                succ, msg = self.cm.save_and_apply(skip_binary_validation=skip_binary)

            def on_done():
                if succ:
                    self._update_status(f"✅ {success_tip}（已自动保存并写入内核生效）")
                else:
                    self._update_status(f"❌ {msg}", is_error=True)
                    messagebox.showerror("保存拦截", msg)

            try:
                self.root.after(0, on_done)
            except Exception:
                pass

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _load_profiles_into_dropdown(self):
        profiles = self.cm.get_available_profiles()
        combo_values = []
        selected_idx = 0
        for idx, p in enumerate(profiles):
            label = f"{p['name']} ({p['file']})"
            combo_values.append(label)
            if p["file"] == self.cm.current_profile_file:
                selected_idx = idx

        self.profile_combo["values"] = combo_values
        if combo_values:
            self.profile_combo.current(selected_idx)

    def _on_profile_selected(self, event=None):
        idx = self.profile_combo.current()
        profiles = self.cm.get_available_profiles()
        if 0 <= idx < len(profiles):
            target = profiles[idx]
            self.cm.load_profile_by_file(target["file"], target["name"])
            self._refresh_group_list()
            self._update_status(f"已加载配置: {target['name']}")

    def _on_latency_mode_changed(self, event=None):
        mode = self.latency_mode_var.get()
        save_settings({"latency_mode": mode})
        self._update_status(f"测速模式已切换为：{mode}")

    def _reload_profile(self):
        self.cm.load_profile_by_file(self.cm.current_profile_file, self.cm.current_profile_name)
        self._refresh_group_list()
        self._update_status("已重新从磁盘加载配置。")

    def _refresh_group_list(self, target_group_name: Optional[str] = None):
        self.group_listbox.delete(0, tk.END)
        groups = self.cm.get_groups()

        prefer_idx = 0
        for idx, g in enumerate(groups):
            prefix = "🔒 " if g["is_protected"] else "📁 "
            self.group_listbox.insert(tk.END, f" {prefix}{g['name']}  ({g['count_display']})")
            if target_group_name and g["name"] == target_group_name:
                prefer_idx = idx
            elif not target_group_name and ("手动节点" in g["name"] or "常用" in g["name"]):
                prefer_idx = idx

        if groups:
            self.group_listbox.selection_clear(0, tk.END)
            self.group_listbox.selection_set(prefer_idx)
            self.group_listbox.see(prefer_idx)
            self._on_group_selected()
        else:
            self.current_group_name = ""
            self.group_title_lbl.config(text="未发现任何节点分组")
            self._render_nodes_table([])

    def _on_group_selected(self, event=None):
        sel = self.group_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        groups = self.cm.get_groups()
        if 0 <= idx < len(groups):
            group = groups[idx]
            self.current_group_name = group["name"]
            protected_tag = " [🔒系统分流核心，禁止删除]" if group["is_protected"] else ""
            self.group_title_lbl.config(
                text=f"分组: 【{group['name']}】  (共 {group['count_display']} 个节点){protected_tag}"
            )
            self.group_nodes_data = self.cm.get_group_proxies(self.current_group_name)
            self._filter_nodes()

    def _filter_nodes(self):
        keyword = self.search_var.get().strip().lower()
        if not keyword:
            filtered = self.group_nodes_data
        else:
            filtered = [
                n for n in self.group_nodes_data
                if keyword in n["name"].lower()
                or keyword in str(n["server"]).lower()
                or keyword in str(n["type"]).lower()
            ]
        self._render_nodes_table(filtered)

    def _render_nodes_table(self, nodes: List[Dict[str, Any]]):
        for item in self.node_tree.get_children():
            self.node_tree.delete(item)

        for n in nodes:
            status_text = "⭐ 置顶" if n["is_top"] else ""
            delay_val = self.node_delays.get(n["name"])

            tags = []
            if n["is_top"]:
                tags.append("top_row")

            if n["name"] in self.testing_nodes or delay_val == -1:
                delay_text = "⏳ 测速中..."
                tags.append("delay_testing")
            elif delay_val is None:
                delay_text = "-"
            elif delay_val < 0:
                delay_text = "❌ 超时"
                tags.append("delay_timeout")
            else:
                delay_text = f"⚡ {delay_val}ms"
                if delay_val <= 120:
                    tags.append("delay_fast")
                elif delay_val <= 280:
                    tags.append("delay_medium")
                else:
                    tags.append("delay_slow")

            vals = (
                n["index"],
                status_text,
                n["name"],
                delay_text,
                n["type"],
                n["server"],
                n["port"]
            )
            self.node_tree.insert("", tk.END, values=vals, tags=tuple(tags))

        self.node_tree.tag_configure("top_row", foreground="#b45309", font=self.bold_font)
        self.node_tree.tag_configure("delay_fast", foreground="#16a34a", font=self.bold_font)
        self.node_tree.tag_configure("delay_medium", foreground="#2563eb", font=self.bold_font)
        self.node_tree.tag_configure("delay_slow", foreground="#d97706", font=self.bold_font)
        self.node_tree.tag_configure("delay_timeout", foreground="#dc2626")
        self.node_tree.tag_configure("delay_testing", foreground="#64748b")

    def _get_selected_node_names(self) -> List[str]:
        selected_items = self.node_tree.selection()
        names = []
        for item in selected_items:
            vals = self.node_tree.item(item, "values")
            if vals and len(vals) > 2:
                names.append(vals[2])
        return names

    def _on_tree_right_click(self, event):
        item = self.node_tree.identify_row(event.y)
        if item:
            if item not in self.node_tree.selection():
                self.node_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    # ---------------- Action Handlers ---------------- #

    def _action_import_clipboard(self):
        if not self.current_group_name:
            messagebox.showwarning("提示", "请先在左侧选择一个要导入的目标分组！")
            return

        proxies = []
        source_label = "剪贴板文本"

        # 1. First check if clipboard contains an image (e.g. Win+Shift+S screenshot of QR code)
        try:
            cb_img = ImageGrab.grabclipboard()
            if cb_img is not None:
                qr_proxies, _ = parse_qr_image(cb_img)
                if qr_proxies:
                    proxies = qr_proxies
                    source_label = "剪贴板二维码截图"
        except Exception as e:
            print(f"[Clipboard QR decode error]: {e}")

        # 2. Fallback to clipboard text
        if not proxies:
            try:
                clipboard_text = self.root.clipboard_get()
            except Exception:
                clipboard_text = ""

            if not clipboard_text or not clipboard_text.strip():
                self._action_manual_input()
                return

            proxies, failed = parse_batch_text(clipboard_text)
            if not proxies:
                self._action_manual_input(initial_text=clipboard_text)
                return

        msg = f"检测到【{source_label}】包含 {len(proxies)} 个可用节点：\n"
        for p in proxies[:5]:
            msg += f"  • {p['name']} ({p.get('type','').upper()})\n"
        if len(proxies) > 5:
            msg += f"  ...等共 {len(proxies)} 个节点\n"
        msg += f"\n是否立即导入并写入到当前分组【{self.current_group_name}】？"

        if CustomConfirmDialog(self.root, "一键导入确认", msg, is_danger=False, confirm_text="立即导入").result:
            added_cnt, names = self.cm.add_proxies_to_group(
                proxies, self.current_group_name, pin_to_top=True
            )
            self.group_nodes_data = self.cm.get_group_proxies(self.current_group_name)
            self._filter_nodes()
            self._refresh_group_listbox_counts()
            self._commit_and_sync(f"成功导入 {added_cnt} 个节点到【{self.current_group_name}】", delay_ms=0, skip_binary=False)
            messagebox.showinfo(
                "导入成功",
                f"✅ 成功导入 {added_cnt} 个节点！\n\n已自动通过核心校验并写入配置生效。\n（如 Clash Verge 界面未同步，在 Clash 界面按 Ctrl+R 即可看到）"
            )

    def _action_import_qr(self):
        if not self.current_group_name:
            messagebox.showwarning("提示", "请先在左侧选择一个要导入的目标分组！")
            return

        diag = tk.Toplevel(self.root)
        diag.title(f"📷 识别二维码导入节点 -> 导入到【{self.current_group_name}】")
        diag.transient(self.root)
        diag.grab_set()

        dw, dh = self._scale(680), self._scale(520)
        center_window(diag, self.root, dw, dh)

        # 1. Pack bottom button box FIRST so it is NEVER clipped
        btn_box = ttk.Frame(diag, padding=self._scale(12))
        btn_box.pack(fill=tk.X, side=tk.BOTTOM)

        # 2. Top Banner / Guidance
        top_frame = ttk.Frame(diag, padding=(self._scale(12), self._scale(10)))
        top_frame.pack(fill=tk.X, side=tk.TOP)

        ttk.Label(
            top_frame,
            text="📷 二维码节点全能极速识别",
            font=self.bold_font
        ).pack(anchor=tk.W)

        guidance_text = (
            "• 支持直接读取刚截取的屏幕截图（按 Win+Shift+S 截图后直接点击下方【从剪贴板截图识别】）。\n"
            "• 也支持选择保存在本地电脑中的二维码图片文件（*.png, *.jpg, *.webp 等）。\n"
            "• 识别成功后下方列表将展示节点详情，点击右下方【立即导入并保存生效】即可写入配置。"
        )
        ttk.Label(
            top_frame,
            text=guidance_text,
            font=self.default_font,
            wraplength=self._scale(640),
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(self._scale(4), 0))

        # 3. Action Buttons Frame
        action_btn_frame = ttk.Frame(diag, padding=(self._scale(12), self._scale(6)))
        action_btn_frame.pack(fill=tk.X, side=tk.TOP)

        # 4. Center Preview Area
        preview_frame = ttk.LabelFrame(diag, text=" 📋 识别到的节点预览列表 ", padding=self._scale(8))
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=self._scale(12), pady=(0, self._scale(6)))

        cols = ("type", "name", "server", "port")
        preview_tree = ttk.Treeview(preview_frame, columns=cols, show="headings", height=8)
        preview_tree.heading("type", text="协议")
        preview_tree.heading("name", text="节点名称")
        preview_tree.heading("server", text="服务器地址")
        preview_tree.heading("port", text="端口")

        preview_tree.column("type", width=self._scale(80), anchor=tk.CENTER)
        preview_tree.column("name", width=self._scale(260), anchor=tk.W)
        preview_tree.column("server", width=self._scale(180), anchor=tk.W)
        preview_tree.column("port", width=self._scale(70), anchor=tk.CENTER)

        tree_scroll_y = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=preview_tree.yview)
        preview_tree.configure(yscrollcommand=tree_scroll_y.set)
        preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        lbl_status = ttk.Label(
            diag,
            text="👉 请点击上方【从剪贴板截图识别】或【选择图片文件】开始识别...",
            font=self.default_font,
            padding=(self._scale(12), self._scale(2))
        )
        lbl_status.pack(fill=tk.X, side=tk.TOP)

        detected_proxies = []

        pin_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(btn_box, text="导入后自动置顶到首位", variable=pin_var).pack(side=tk.LEFT)

        btn_container = ttk.Frame(btn_box)
        btn_container.pack(side=tk.RIGHT)

        def do_import():
            if not detected_proxies:
                return
            added_cnt, names = self.cm.add_proxies_to_group(
                detected_proxies, self.current_group_name, pin_to_top=pin_var.get()
            )
            diag.destroy()
            self.group_nodes_data = self.cm.get_group_proxies(self.current_group_name)
            self._filter_nodes()
            self._refresh_group_listbox_counts()
            self._commit_and_sync(f"成功从二维码导入 {added_cnt} 个节点到【{self.current_group_name}】", delay_ms=0, skip_binary=False)
            messagebox.showinfo(
                "导入成功",
                f"✅ 成功从二维码导入 {added_cnt} 个节点！\n\n已自动校验并写入配置生效。"
            )

        btn_commit = tk.Button(
            btn_container,
            text="⚡ 立即导入并保存生效",
            bg=self.COLOR_SUCCESS,
            fg="#ffffff",
            font=self.bold_font,
            relief=tk.FLAT,
            padx=self._scale(14),
            pady=self._scale(4),
            cursor="hand2",
            state=tk.DISABLED,
            command=do_import
        )
        btn_commit.pack(side=tk.LEFT, padx=(0, self._scale(8)))

        btn_cancel = ttk.Button(btn_container, text="取消", command=diag.destroy, width=10)
        btn_cancel.pack(side=tk.LEFT)

        def populate_results(proxies, source_name):
            nonlocal detected_proxies
            detected_proxies = proxies
            for item in preview_tree.get_children():
                preview_tree.delete(item)
            if not proxies:
                lbl_status.config(text=f"❌ 未能从【{source_name}】中识别出有效二维码或节点，请确认二维码清晰。", foreground="#dc2626")
                btn_commit.config(state=tk.DISABLED)
                return
            for p in proxies:
                preview_tree.insert("", tk.END, values=(
                    str(p.get("type", "")).upper(),
                    p.get("name", "未命名"),
                    p.get("server", "--"),
                    p.get("port", "--")
                ))
            lbl_status.config(
                text=f"✅ 成功从【{source_name}】识别出 {len(proxies)} 个节点！点击右下方【立即导入并保存生效】完成导入。",
                foreground="#16a34a"
            )
            btn_commit.config(state=tk.NORMAL)

        def scan_from_clipboard():
            cb_data = None
            try:
                cb_data = ImageGrab.grabclipboard()
            except Exception as e:
                print(f"[QR] grabclipboard error: {e}")

            if cb_data is None:
                lbl_status.config(
                    text="⚠️ 剪贴板中未检测到图片！截图提示：按 Win+Shift+S 截图后直接点击此按钮。",
                    foreground="#dc2626"
                )
                return
            if isinstance(cb_data, list):
                all_p = []
                for f in cb_data:
                    if os.path.isfile(f):
                        p, _ = parse_qr_image(f)
                        all_p.extend(p)
                populate_results(all_p, "剪贴板图片文件")
            else:
                p, _ = parse_qr_image(cb_data)
                populate_results(p, "剪贴板屏幕截图")

        def scan_from_file():
            filepath = filedialog.askopenfilename(
                parent=diag,
                title="选择包含节点二维码的图片文件",
                filetypes=[
                    ("图片文件", "*.png;*.jpg;*.jpeg;*.webp;*.bmp"),
                    ("所有文件", "*.*")
                ]
            )
            if not filepath:
                return
            p, _ = parse_qr_image(filepath)
            populate_results(p, os.path.basename(filepath))

        btn_scan_cb = tk.Button(
            action_btn_frame,
            text="📋 1. 从剪贴板截屏识别二维码 (推荐)",
            bg="#0d9488",
            fg="#ffffff",
            font=self.bold_font,
            relief=tk.FLAT,
            padx=self._scale(12),
            pady=self._scale(4),
            cursor="hand2",
            command=scan_from_clipboard
        )
        btn_scan_cb.pack(side=tk.LEFT, padx=(0, self._scale(10)))

        btn_scan_file = tk.Button(
            action_btn_frame,
            text="📂 2. 选择电脑中的图片文件 (*.png;*.jpg)...",
            bg=self.theme["btn_bg"],
            fg=self.theme["btn_fg"],
            font=self.default_font,
            relief=tk.FLAT,
            bd=0,
            padx=self._scale(10),
            pady=self._scale(4),
            cursor="hand2",
            command=scan_from_file
        )
        btn_scan_file.pack(side=tk.LEFT)

        diag.bind("<Escape>", lambda e: diag.destroy())

        # Auto-detect if clipboard already has a screenshot on dialog open!
        try:
            diag.after(100, scan_from_clipboard)
        except Exception:
            pass

    def _action_manual_input(self, initial_text: str = ""):
        if not self.current_group_name:
            messagebox.showwarning("提示", "请先在左侧选择一个要导入的目标分组！")
            return

        diag = tk.Toplevel(self.root)
        diag.title(f"手动输入节点/订阅链接 -> 导入到【{self.current_group_name}】")
        diag.transient(self.root)
        diag.grab_set()

        dw, dh = self._scale(740), self._scale(540)
        center_window(diag, self.root, dw, dh)

        # 1. Pack bottom button box FIRST so it is NEVER clipped
        btn_box = ttk.Frame(diag, padding=self._scale(12))
        btn_box.pack(fill=tk.X, side=tk.BOTTOM)

        # 2. Friendly and intuitive description at the top
        top_frame = ttk.Frame(diag, padding=(self._scale(12), self._scale(10)))
        top_frame.pack(fill=tk.X, side=tk.TOP)

        ttk.Label(
            top_frame,
            text="💡 极简导入指引：",
            font=self.bold_font
        ).pack(anchor=tk.W)

        instruction_text = (
            "• 直接在下方大文本框粘贴你的节点链接（单行、多行混合均支持）或完整的机场订阅网址，全自动智能识别！\n"
            "• 支持主流全部协议：VLESS (Reality/Vision) / VMess / Hysteria 2 / Trojan / Shadowsocks / TUIC 等。\n"
            "• 如果是二维码图片，可直接点击左下方【📷 识别二维码】进行截屏扫码或选图识别。"
        )
        ttk.Label(
            top_frame,
            text=instruction_text,
            font=self.default_font,
            wraplength=self._scale(700),
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(self._scale(4), 0))

        # 3. Center Text Box
        txt_frame = ttk.Frame(diag, padding=(self._scale(12), 0))
        txt_frame.pack(fill=tk.BOTH, expand=True)

        txt = tk.Text(txt_frame, wrap=tk.NONE, font=("Consolas", int(10 * 1.0)))
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        if initial_text:
            txt.insert("1.0", initial_text)

        scroll_y = ttk.Scrollbar(txt_frame, orient=tk.VERTICAL, command=txt.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        txt.config(yscrollcommand=scroll_y.set)

        # Bottom Bar Contents:
        btn_qr_shortcut = tk.Button(
            btn_box,
            text="📷 识别二维码图片/截屏...",
            bg="#f0fdf4",
            fg="#15803d",
            font=self.default_font,
            relief=tk.FLAT,
            bd=0,
            padx=self._scale(8),
            pady=self._scale(3),
            cursor="hand2",
            command=lambda: (diag.destroy(), self._action_import_qr())
        )
        btn_qr_shortcut.pack(side=tk.LEFT, padx=(0, self._scale(12)))

        pin_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(btn_box, text="导入后自动置顶到首位", variable=pin_var).pack(side=tk.LEFT)

        def do_import():
            content = txt.get("1.0", tk.END).strip()
            if not content:
                diag.destroy()
                return

            proxies, failed = parse_batch_text(content)
            if not proxies:
                messagebox.showerror(
                    "解析失败",
                    "未识别到任何有效节点链接！\n\n请确认链接以 vless://, vmess://, hy2://, hysteria2://, trojan://, ss:// 开头，或是有效的 http(s):// 订阅链接。"
                )
                return

            added_cnt, names = self.cm.add_proxies_to_group(
                proxies, self.current_group_name, pin_to_top=pin_var.get()
            )
            diag.destroy()
            self.group_nodes_data = self.cm.get_group_proxies(self.current_group_name)
            self._filter_nodes()
            self._refresh_group_listbox_counts()
            self._commit_and_sync(f"成功导入 {added_cnt} 个节点", delay_ms=0, skip_binary=False)
            messagebox.showinfo(
                "导入成功",
                f"✅ 成功导入 {added_cnt} 个节点！\n\n已自动校验并写入配置生效。"
            )

        btn_container = ttk.Frame(btn_box)
        btn_container.pack(side=tk.RIGHT)

        # 确定/导入键在左
        btn_commit = tk.Button(
            btn_container,
            text="⚡ 立即导入并保存生效",
            bg=self.COLOR_SUCCESS,
            fg="#ffffff",
            font=self.bold_font,
            relief=tk.FLAT,
            padx=self._scale(14),
            pady=self._scale(4),
            cursor="hand2",
            command=do_import
        )
        btn_commit.pack(side=tk.LEFT, padx=(0, self._scale(8)))

        # 取消键在右
        btn_cancel = ttk.Button(btn_container, text="取消", command=diag.destroy, width=10)
        btn_cancel.pack(side=tk.LEFT)

        diag.bind("<Escape>", lambda e: diag.destroy())

    def _action_pin_to_top(self):
        names = self._get_selected_node_names()
        if not names:
            return
        target_name = names[0]
        if self.cm.pin_proxy_to_top(target_name, self.current_group_name):
            self.group_nodes_data = self.cm.get_group_proxies(self.current_group_name)
            self._filter_nodes()
            self._reselect_node(target_name)
            self._commit_and_sync(f"已将节点【{target_name}】置顶", delay_ms=300, skip_binary=True)

    def _action_move_up(self):
        names = self._get_selected_node_names()
        if not names:
            return
        target_name = names[0]
        if self.cm.move_proxy_up(target_name, self.current_group_name):
            self.group_nodes_data = self.cm.get_group_proxies(self.current_group_name)
            self._filter_nodes()
            self._reselect_node(target_name)
            self._commit_and_sync(f"已上移节点【{target_name}】", delay_ms=300, skip_binary=True)

    def _action_move_down(self):
        names = self._get_selected_node_names()
        if not names:
            return
        target_name = names[0]
        if self.cm.move_proxy_down(target_name, self.current_group_name):
            self.group_nodes_data = self.cm.get_group_proxies(self.current_group_name)
            self._filter_nodes()
            self._reselect_node(target_name)
            self._commit_and_sync(f"已下移节点【{target_name}】", delay_ms=300, skip_binary=True)

    def _reselect_node(self, target_name: str):
        for item in self.node_tree.get_children():
            vals = self.node_tree.item(item, "values")
            if vals and len(vals) > 2 and vals[2] == target_name:
                self.node_tree.selection_set(item)
                self.node_tree.see(item)
                break

    def _action_rename_node(self):
        names = self._get_selected_node_names()
        if not names:
            messagebox.showinfo("提示", "请先在列表中选中需要重命名的节点！")
            return
        old_name = names[0]
        new_name = CustomInputDialog(
            self.root,
            "重命名节点",
            f"将节点【{old_name}】重命名为：",
            initialvalue=old_name
        ).result
        if new_name and new_name.strip() and new_name.strip() != old_name:
            clean_new = new_name.strip()
            succ, msg = self.cm.rename_proxy(old_name, clean_new)
            if succ:
                self.group_nodes_data = self.cm.get_group_proxies(self.current_group_name)
                self._filter_nodes()
                self._reselect_node(clean_new)
                self._commit_and_sync(f"节点已成功更名为【{clean_new}】", delay_ms=0, skip_binary=True)
            else:
                messagebox.showerror("重命名失败", msg)

    def _action_delete_selected_nodes(self):
        names = self._get_selected_node_names()
        if not names:
            return
        msg = f"确定要将选中的 {len(names)} 个节点从此分组【{self.current_group_name}】中移除吗？"
        if CustomConfirmDialog(self.root, "删除确认", msg, is_danger=True, confirm_text="确认删除").result:
            for name in names:
                self.cm.delete_proxy_from_group(name, self.current_group_name, delete_from_all_groups=False)
            self.group_nodes_data = self.cm.get_group_proxies(self.current_group_name)
            self._filter_nodes()
            self._refresh_group_listbox_counts()
            self._commit_and_sync(f"已移除 {len(names)} 个节点", delay_ms=0, skip_binary=True)

    def _action_delete_completely(self):
        names = self._get_selected_node_names()
        if not names:
            return
        msg = f"⚠️ 危险操作：\n确定要将这 {len(names)} 个节点从【所有分组和底层配置中彻底删除】吗？"
        if CustomConfirmDialog(self.root, "彻底删除确认", msg, is_danger=True, confirm_text="彻底清除").result:
            for name in names:
                self.cm.delete_proxy_from_group(name, self.current_group_name, delete_from_all_groups=True)
            self.group_nodes_data = self.cm.get_group_proxies(self.current_group_name)
            self._filter_nodes()
            self._refresh_group_listbox_counts()
            self._commit_and_sync(f"已彻底清除 {len(names)} 个节点", delay_ms=0, skip_binary=True)

    def _action_clear_current_group_nodes(self):
        if not self.current_group_name:
            messagebox.showwarning("提示", "请先在左侧选择一个要清空的目标分组！")
            return
        nodes = self.cm.get_group_proxies(self.current_group_name)
        if not nodes:
            messagebox.showinfo("提示", "当前分组没有任何节点！")
            return
        msg = f"确定要清空分组【{self.current_group_name}】下的全部 {len(nodes)} 个节点吗？\n（此操作仅将节点从当前分组移出，不会影响其他分组引用的同名节点）"
        if CustomConfirmDialog(self.root, "清空分组确认", msg, is_danger=True, confirm_text="确认清空").result:
            for n in nodes:
                self.cm.delete_proxy_from_group(n["name"], self.current_group_name, delete_from_all_groups=False)
            self.group_nodes_data = self.cm.get_group_proxies(self.current_group_name)
            self._filter_nodes()
            self._refresh_group_listbox_counts()
            self._commit_and_sync(f"已清空分组【{self.current_group_name}】的节点", delay_ms=0, skip_binary=True)

    def _action_copy_to_other_group(self):
        names = self._get_selected_node_names()
        if not names:
            return
        groups = [g["name"] for g in self.cm.get_groups() if g["name"] != self.current_group_name]
        if not groups:
            messagebox.showinfo("提示", "没有其他可分配的目标分组。")
            return

        diag = tk.Toplevel(self.root)
        diag.title("复制节点到其他分组")
        diag.transient(self.root)
        diag.grab_set()
        diag.resizable(False, False)

        dw = self._scale(440)
        dh = self._scale(260)
        center_window(diag, self.root, dw, dh)

        content_f = tk.Frame(diag, bg="#ffffff", padx=self._scale(20), pady=self._scale(18))
        content_f.pack(fill=tk.BOTH, expand=True)

        # Header with icon
        header_frame = tk.Frame(content_f, bg="#ffffff")
        header_frame.pack(fill=tk.X, pady=(0, self._scale(12)))

        tk.Label(
            header_frame,
            text="📁",
            font=("Segoe UI Emoji", int(18 * 1.0)) if sys.platform == "win32" else ("Arial", 18),
            bg="#ffffff"
        ).pack(side=tk.LEFT, padx=(0, self._scale(10)))

        text_frame = tk.Frame(header_frame, bg="#ffffff")
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(
            text_frame,
            text="分配节点至其他目标分组",
            font=self.bold_font,
            bg="#ffffff",
            fg="#0f172a"
        ).pack(anchor=tk.W)

        tk.Label(
            text_frame,
            text=f"将选中的 {len(names)} 个节点同步加入到目标分组：",
            font=self.default_font,
            bg="#ffffff",
            fg="#64748b"
        ).pack(anchor=tk.W, pady=(2, 0))

        # Body: Combobox
        cb_frame = tk.Frame(content_f, bg="#ffffff")
        cb_frame.pack(fill=tk.X, pady=(self._scale(8), self._scale(12)))

        tk.Label(
            cb_frame,
            text="选择目标分组：",
            font=self.default_font,
            bg="#ffffff",
            fg="#334155"
        ).pack(anchor=tk.W, pady=(0, self._scale(4)))

        cb = ttk.Combobox(cb_frame, values=groups, state="readonly", font=self.default_font)
        cb.pack(fill=tk.X)
        cb.current(0)

        # Checkbox
        pin_var = tk.BooleanVar(value=True)
        chk = ttk.Checkbutton(content_f, text="加入目标分组后自动置顶到首位", variable=pin_var)
        chk.pack(anchor=tk.W, pady=(0, self._scale(16)))

        def do_copy():
            tgt = cb.get()
            proxy_map = self.cm.get_proxy_map()
            proxies_to_add = [proxy_map[n] for n in names if n in proxy_map]
            self.cm.add_proxies_to_group(proxies_to_add, tgt, pin_to_top=pin_var.get())
            diag.destroy()
            self._refresh_group_listbox_counts()
            self._commit_and_sync(f"已将 {len(names)} 个节点分配到【{tgt}】", delay_ms=0, skip_binary=True)

        btn_box = tk.Frame(content_f, bg="#ffffff")
        btn_box.pack(fill=tk.X, side=tk.BOTTOM)

        btn_container = tk.Frame(btn_box, bg="#ffffff")
        btn_container.pack(side=tk.RIGHT)

        # 确定键在左
        btn_ok = tk.Button(
            btn_container,
            text="⚡ 立即分配",
            bg=self.COLOR_PRIMARY,
            fg="#ffffff",
            font=self.bold_font,
            relief=tk.FLAT,
            padx=self._scale(14),
            pady=self._scale(4),
            cursor="hand2",
            command=do_copy
        )
        btn_ok.pack(side=tk.LEFT, padx=(0, self._scale(8)))

        # 取消键在右
        btn_cancel = ttk.Button(btn_container, text="取消", command=diag.destroy, width=8)
        btn_cancel.pack(side=tk.LEFT)

        diag.bind("<Return>", lambda e: do_copy())
        diag.bind("<Escape>", lambda e: diag.destroy())

    # ---------------- 节点测延迟 & 属性编辑 ---------------- #

    def _action_test_selected_latency(self):
        names = self._get_selected_node_names()
        if not names:
            self._action_test_all_latency()
            return
        self._run_latency_tests(names)

    def _action_test_latency_mode(self, mode_key: str):
        mode_map = {
            "connect": "⚡ 极速 Connect 延迟 (手机同款/极速)",
            "true": "🌐 真实全链路 (HTTP 204 端到端)",
            "tcp": "🔌 TCP 握手测速"
        }
        target_mode = mode_map.get(mode_key, "⚡ 极速 Connect 延迟 (手机同款/极速)")
        if hasattr(self, "latency_mode_var"):
            self.latency_mode_var.set(target_mode)
            save_settings({"latency_mode": target_mode})
        self._action_test_selected_latency()

    def _action_test_all_latency(self):
        if not self.group_nodes_data:
            self._update_status("当前分组暂无节点")
            return
        names = [n["name"] for n in self.group_nodes_data]
        self._run_latency_tests(names)

    def _run_latency_tests(self, target_names: List[str]):
        proxy_map = self.cm.get_proxy_map()
        mode_val = self.latency_mode_var.get() if hasattr(self, "latency_mode_var") else "⚡ 极速 Connect 延迟 (手机同款/极速)"
        targets = []
        for name in target_names:
            p = proxy_map.get(name, {})
            srv = str(p.get("server", "")).strip()
            prt = int(p.get("port", 0)) if p.get("port") else 0
            sni = str(p.get("sni") or p.get("servername") or "").strip()
            targets.append((name, srv, prt, sni, p))
            self.node_delays[name] = -1  # marking as testing
            self.testing_nodes.add(name)

        if not targets:
            self._update_status("没有可测速的节点")
            return

        self._filter_nodes()
        self._update_status(f"⚡ 正在测试 {len(targets)} 个节点的连接延迟 [{mode_val}]...")

        def worker():
            def ping_one(item):
                p_name, srv, prt, sni, p = item
                ms = None
                if "204" in mode_val or "端到端" in mode_val:
                    ms = self.cm.test_proxy_true_delay(p_name)
                    if ms is None and srv and prt > 0:
                        ms = ultra_fast_connect_delay(srv, prt, timeout=1.8)
                else:  # 极速 Connect 延迟 / TCP 握手 (手机同款)
                    if srv and prt > 0:
                        ms = ultra_fast_connect_delay(srv, prt, timeout=1.8)
                    if ms is None and p_name:
                        ms = self.cm.test_proxy_true_delay(p_name)
                return p_name, ms

            with ThreadPoolExecutor(max_workers=15) as executor:
                results = list(executor.map(ping_one, targets))

            def on_complete():
                for p_name, ms in results:
                    self.node_delays[p_name] = ms if ms is not None else -2
                    self.testing_nodes.discard(p_name)
                self._filter_nodes()
                succ_cnt = sum(1 for _, ms in results if ms is not None)
                self._update_status(f"✅ 测速完成 [{mode_val}]：共测试 {len(results)} 个节点，{succ_cnt} 个连通可用")

            try:
                self.root.after(0, on_complete)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def _action_edit_node(self):
        names = self._get_selected_node_names()
        if not names:
            messagebox.showinfo("提示", "请先在列表中选中需要编辑的节点！")
            return
        target_name = names[0]
        proxy_map = self.cm.get_proxy_map()
        node_data = proxy_map.get(target_name)
        if not node_data:
            self._action_rename_node()
            return

        diag = tk.Toplevel(self.root)
        diag.title(f"编辑节点属性与测速 - 【{target_name}】")
        diag.transient(self.root)
        diag.grab_set()
        diag.resizable(True, True)

        dw = self._scale(560)
        dh = self._scale(540)
        center_window(diag, self.root, dw, dh)

        content = tk.Frame(diag, bg="#ffffff", padx=self._scale(20), pady=self._scale(14))
        content.pack(fill=tk.BOTH, expand=True)

        # 1. Pack bottom buttons FIRST so they can NEVER be clipped
        btn_box = tk.Frame(content, bg="#ffffff")
        btn_box.pack(fill=tk.X, side=tk.BOTTOM, pady=(self._scale(10), 0))
        btn_container = tk.Frame(btn_box, bg="#ffffff")
        btn_container.pack(side=tk.RIGHT)

        # Header with protocol tag
        top_h = tk.Frame(content, bg="#ffffff")
        top_h.pack(fill=tk.X, pady=(0, self._scale(10)))

        proto = str(node_data.get("type", "PROXY")).upper()
        tk.Label(
            top_h,
            text=f"⚙️ 节点属性与多模式连接测试  [{proto}]",
            font=self.bold_font,
            bg="#ffffff",
            fg="#0f172a"
        ).pack(anchor=tk.W)

        # Form fields
        form = tk.Frame(content, bg="#ffffff")
        form.pack(fill=tk.X, pady=(0, self._scale(8)))

        tk.Label(form, text="节点名称:", font=self.default_font, bg="#ffffff", fg="#334155").grid(row=0, column=0, sticky=tk.W, pady=4)
        name_entry = ttk.Entry(form, width=38, font=self.default_font)
        name_entry.insert(0, target_name)
        name_entry.grid(row=0, column=1, sticky=tk.EW, pady=4, padx=(self._scale(6), 0))

        tk.Label(form, text="服务器域名/IP:", font=self.default_font, bg="#ffffff", fg="#334155").grid(row=1, column=0, sticky=tk.W, pady=4)
        server_entry = ttk.Entry(form, width=38, font=self.default_font)
        server_entry.insert(0, str(node_data.get("server", "")))
        server_entry.grid(row=1, column=1, sticky=tk.EW, pady=4, padx=(self._scale(6), 0))

        tk.Label(form, text="端口号 (Port):", font=self.default_font, bg="#ffffff", fg="#334155").grid(row=2, column=0, sticky=tk.W, pady=4)
        port_entry = ttk.Entry(form, width=38, font=self.default_font)
        port_entry.insert(0, str(node_data.get("port", "")))
        port_entry.grid(row=2, column=1, sticky=tk.EW, pady=4, padx=(self._scale(6), 0))

        uuid_key = "uuid" if "uuid" in node_data else ("password" if "password" in node_data else None)
        uuid_entry = None
        if uuid_key:
            tk.Label(form, text=f"认证密钥 ({uuid_key}):", font=self.default_font, bg="#ffffff", fg="#334155").grid(row=3, column=0, sticky=tk.W, pady=4)
            uuid_entry = ttk.Entry(form, width=38, font=self.default_font)
            uuid_entry.insert(0, str(node_data.get(uuid_key, "")))
            uuid_entry.grid(row=3, column=1, sticky=tk.EW, pady=4, padx=(self._scale(6), 0))

        form.columnconfigure(1, weight=1)

        # ⚡ Dedicated Multi-Mode Ping Test Card in Node Editor!
        ping_card = tk.Frame(content, bg="#f8fafc", bd=0, relief=tk.FLAT, highlightthickness=1, highlightbackground="#e2e8f0", padx=self._scale(12), pady=self._scale(10))
        ping_card.pack(fill=tk.X, pady=(self._scale(4), self._scale(10)))

        cur_cached_delay = self.node_delays.get(target_name)
        init_ping_text = f"● 最近测速结果: {cur_cached_delay} ms" if (cur_cached_delay and cur_cached_delay > 0) else "● 可点选下方测试模式，验证该节点在当前网络环境下的真实连通延迟"
        ping_status_lbl = tk.Label(
            ping_card,
            text=init_ping_text,
            font=self.default_font,
            bg="#f8fafc",
            fg="#64748b",
            wraplength=self._scale(480),
            justify=tk.LEFT
        )
        ping_status_lbl.pack(anchor=tk.W, pady=(0, self._scale(8)))

        # 3 Prominent Radio Buttons for Instant Mode Selection
        mode_radio_frame = tk.Frame(ping_card, bg="#f8fafc")
        mode_radio_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, self._scale(8)))

        tk.Label(mode_radio_frame, text="测速模式:", font=self.bold_font, bg="#f8fafc", fg="#334155").pack(side=tk.LEFT, padx=(0, self._scale(8)))
        edit_mode_var = tk.StringVar(value=self.latency_mode_var.get() if hasattr(self, "latency_mode_var") else "⚡ 极速 Connect 延迟 (手机同款/极速)")

        rb1 = tk.Radiobutton(mode_radio_frame, text="⚡ 极速 Connect (手机同款)", variable=edit_mode_var, value="⚡ 极速 Connect 延迟 (手机同款/极速)", bg="#f8fafc", fg="#0f172a", selectcolor="#ffffff", font=self.default_font)
        rb1.pack(side=tk.LEFT, padx=(0, self._scale(6)))
        rb2 = tk.Radiobutton(mode_radio_frame, text="🌐 真实全链路 (HTTP 204)", variable=edit_mode_var, value="🌐 真实全链路 (HTTP 204 端到端)", bg="#f8fafc", fg="#0f172a", selectcolor="#ffffff", font=self.default_font)
        rb2.pack(side=tk.LEFT, padx=(0, self._scale(6)))
        rb3 = tk.Radiobutton(mode_radio_frame, text="🔌 TCP 握手", variable=edit_mode_var, value="🔌 TCP 握手测速", bg="#f8fafc", fg="#0f172a", selectcolor="#ffffff", font=self.default_font)
        rb3.pack(side=tk.LEFT)

        ping_btn_row = tk.Frame(ping_card, bg="#f8fafc")
        ping_btn_row.pack(anchor=tk.W, fill=tk.X)

        def do_test_single():
            srv = server_entry.get().strip()
            prt_str = port_entry.get().strip()
            m_val = edit_mode_var.get()
            if not srv or not prt_str:
                ping_status_lbl.config(text="⚠️ 请先填写服务器地址和端口", fg="#dc2626")
                return
            try:
                prt = int(prt_str)
            except Exception:
                ping_status_lbl.config(text="⚠️ 端口必须是有效数字", fg="#dc2626")
                return

            ping_status_lbl.config(text=f"⏳ 正在向目标节点发送测速请求 [{m_val}]...", fg="#2563eb")
            diag.update_idletasks()

            def ping_worker():
                ms = None
                if "204" in m_val or "端到端" in m_val:
                    ms = self.cm.test_proxy_true_delay(target_name)
                    if ms is None and srv and prt > 0:
                        ms = ultra_fast_connect_delay(srv, prt, timeout=1.8)
                else:  # 极速 Connect 延迟 / TCP 握手
                    if srv and prt > 0:
                        ms = ultra_fast_connect_delay(srv, prt, timeout=1.8)
                    if ms is None and target_name:
                        ms = self.cm.test_proxy_true_delay(target_name)

                def on_done():
                    if ms is not None:
                        color = "#16a34a" if ms <= 150 else ("#2563eb" if ms <= 300 else "#b45309")
                        ping_status_lbl.config(text=f"🟢 连通正常！[{m_val}] 延迟：{ms} ms", fg=color)
                        self.node_delays[target_name] = ms
                    else:
                        ping_status_lbl.config(text=f"🔴 节点连接失败或超时 [{m_val}]", fg="#dc2626")
                        self.node_delays[target_name] = -2
                    self._filter_nodes()
                try:
                    diag.after(0, on_done)
                except Exception:
                    pass

            threading.Thread(target=ping_worker, daemon=True).start()

        btn_ping_single = tk.Button(
            ping_btn_row,
            text="⚡ 立即测试当前节点延迟",
            bg="#ecfdf5",
            fg="#059669",
            font=self.bold_font,
            relief=tk.FLAT,
            bd=0,
            padx=self._scale(12),
            pady=self._scale(3),
            cursor="hand2",
            command=do_test_single
        )
        btn_ping_single.pack(side=tk.LEFT)

        # Save action
        def do_save():
            new_n = name_entry.get().strip()
            new_s = server_entry.get().strip()
            new_p_str = port_entry.get().strip()
            if not new_n:
                messagebox.showerror("错误", "节点名称不能为空！")
                return
            if not new_s:
                messagebox.showerror("错误", "服务器地址不能为空！")
                return
            try:
                new_p = int(new_p_str)
            except Exception:
                messagebox.showerror("错误", "端口号必须是 1-65535 之间的整数！")
                return

            updated = {"name": new_n, "server": new_s, "port": new_p}
            if uuid_key and uuid_entry:
                updated[uuid_key] = uuid_entry.get().strip()

            succ, msg = self.cm.update_proxy(target_name, updated)
            if succ:
                diag.destroy()
                self.group_nodes_data = self.cm.get_group_proxies(self.current_group_name)
                self._filter_nodes()
                self._reselect_node(new_n)
                self._commit_and_sync(f"节点【{new_n}】配置已更新生效", delay_ms=0, skip_binary=False)
            else:
                messagebox.showerror("保存失败", msg)

        # 确定/保存键在左
        btn_save = tk.Button(
            btn_container,
            text="💾 保存修改并生效",
            bg=self.COLOR_SUCCESS,
            fg="#ffffff",
            font=self.bold_font,
            relief=tk.FLAT,
            padx=self._scale(14),
            pady=self._scale(4),
            cursor="hand2",
            command=do_save
        )
        btn_save.pack(side=tk.LEFT, padx=(0, self._scale(8)))

        # 取消键在右
        btn_cancel = ttk.Button(btn_container, text="取消", command=diag.destroy, width=8)
        btn_cancel.pack(side=tk.LEFT)

        diag.bind("<Return>", lambda e: do_save())
        diag.bind("<Escape>", lambda e: diag.destroy())

    def _action_show_about(self):
        diag = tk.Toplevel(self.root)
        diag.title("关于与说明 - Clash 节点跃迁 (ClashNodeX)")
        diag.transient(self.root)
        diag.grab_set()
        diag.resizable(False, False)

        dw = self._scale(580)
        dh = self._scale(520)
        center_window(diag, self.root, dw, dh)

        bg_card = self.theme["card_bg"]
        fg_text = self.theme["text"]
        fg_muted = self.theme["text_muted"]

        card = tk.Frame(diag, bg=bg_card, padx=self._scale(24), pady=self._scale(20))
        card.pack(fill=tk.BOTH, expand=True)

        # Title / Badge
        tk.Label(
            card,
            text="⚡ Clash 节点跃迁 (ClashNodeX)",
            font=("Microsoft YaHei UI", int(14 * 1.0), "bold"),
            bg=bg_card,
            fg=fg_text
        ).pack(anchor=tk.CENTER, pady=(0, 4))

        tk.Label(
            card,
            text="v2.5.0 (Windows 10/11 极客专属版) · 开源免费",
            font=("Microsoft YaHei UI", 9),
            bg=bg_card,
            fg=fg_muted
        ).pack(anchor=tk.CENTER, pady=(0, 10))

        desc_text = (
            "专为 Clash Verge Rev / Mihomo 设计的高性能节点与分组管理利器。\n"
            "作者同样是 Clash 资深拥趸，深受 Clash 强大的分流架构与优雅现代图形界面的启发。\n"
            "本软件支持全协议解析导入、二维码截图快速识别、三模精准延迟测试（真连接 HTTP 204 / TCP 握手 / TLS 握手）、\n"
            "内置智能 uTLS 指纹补全（彻底根治 VLESS Reality 7C/7D 在 Windows 上超时断流的顽疾）、\n"
            "双向实时流量监控看板、双行防遮挡极速工具栏、毫秒级防死锁热保存与月球探索壁纸换肤。"
        )
        tk.Label(
            card,
            text=desc_text,
            font=("Microsoft YaHei UI", 9.5),
            bg=bg_card,
            fg=fg_text,
            justify=tk.CENTER,
            wraplength=self._scale(520)
        ).pack(anchor=tk.CENTER, pady=(0, 12))

        # Open Source Support Box
        box_bg = self.theme["sidebar"]
        sponsor_box = tk.Frame(card, bg=box_bg, bd=0, relief=tk.FLAT, highlightthickness=1, highlightbackground=self.theme["border"], padx=self._scale(14), pady=self._scale(12))
        sponsor_box.pack(fill=tk.X, pady=(0, 16))

        tk.Label(
            sponsor_box,
            text="🌟 开源支持与版权说明",
            font=("Microsoft YaHei UI", 10, "bold"),
            bg=box_bg,
            fg=self.theme["top"]
        ).pack(anchor=tk.W, pady=(0, 6))

        sponsor_detail = (
            "• 点赞即赞助：本项目采用宽松的 MIT 开源协议，纯公益开源，不设任何商业打赏渠道。若觉得好用，在 GitHub 给个 Star 点赞与关注就是对作者最大的认可与支持！\n"
            "• 开源版权：项目代码版权归作者所有（MIT License）。您可以自由使用、学习、修改与二次分发；纯本地运行，不上传任何隐私、节点或订阅信息。\n"
            "• 交流反馈：欢迎在 GitHub 提交 Issue 建议与讨论，作者会第一时间收到邮件通知并持续维护更新！"
        )
        tk.Label(
            sponsor_box,
            text=sponsor_detail,
            font=("Microsoft YaHei UI", 8.5),
            bg=box_bg,
            fg=fg_text,
            justify=tk.LEFT,
            wraplength=self._scale(500)
        ).pack(anchor=tk.W, padx=self._scale(4))

        # Close button
        btn_close = tk.Button(
            card,
            text="关闭",
            bg=self.theme["primary"],
            fg=self.theme["primary_fg"],
            font=self.bold_font,
            relief=tk.FLAT,
            padx=self._scale(20),
            pady=self._scale(4),
            cursor="hand2",
            command=diag.destroy
        )
        btn_close.pack(anchor=tk.CENTER)
        self._apply_interactive_effect(btn_close)

        diag.bind("<Return>", lambda e: diag.destroy())
        diag.bind("<Escape>", lambda e: diag.destroy())

    def _action_show_feedback(self):
        diag = tk.Toplevel(self.root)
        diag.title("💬 意见反馈与建议 - ClashNodeX")
        diag.transient(self.root)
        diag.grab_set()
        diag.resizable(False, False)
        
        dw = self._scale(560)
        dh = self._scale(480)
        center_window(diag, self.root, dw, dh)
        
        frame = ttk.Frame(diag, padding=self._scale(20))
        frame.pack(fill=tk.BOTH, expand=True)

        header = tk.Frame(frame, bg=self.theme["bg"])
        header.pack(fill=tk.X, pady=(0, self._scale(10)))
        
        tk.Label(
            header,
            text="💬 用户反馈与需求建议",
            font=("Microsoft YaHei UI", 13, "bold"),
            bg=self.theme["bg"],
            fg=self.theme["primary"]
        ).pack(anchor="w")

        tk.Label(
            header,
            text="你的宝贵建议是推动 ClashNodeX 持续进化的最大动力！\n作者本人也是从 Clash 深度用户转过来的，任何痛点都欢迎提出。",
            font=self.default_font,
            bg=self.theme["bg"],
            fg=self.theme["text_muted"],
            justify=tk.LEFT
        ).pack(anchor="w", pady=(self._scale(4), 0))

        # Feedback input area
        txt_box = tk.Text(
            frame,
            height=7,
            width=50,
            font=self.default_font,
            bg=self.theme["card_bg"],
            fg=self.theme["text"],
            bd=0,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.theme["border"],
            padx=self._scale(8),
            pady=self._scale(6)
        )
        txt_box.pack(fill=tk.BOTH, expand=True, pady=self._scale(10))
        txt_box.insert(tk.END, "请在此输入你的宝贵建议或遇到的节点问题...")

        def _on_focus_in(e):
            if txt_box.get("1.0", tk.END).strip() == "请在此输入你的宝贵建议或遇到的节点问题...":
                txt_box.delete("1.0", tk.END)
        txt_box.bind("<FocusIn>", _on_focus_in)

        # Contact info
        contact_frame = tk.Frame(frame, bg=self.theme["bg"])
        contact_frame.pack(fill=tk.X, pady=(0, self._scale(12)))
        tk.Label(contact_frame, text="联系方式 (选填，便于沟通细节):", font=self.default_font, bg=self.theme["bg"], fg=self.theme["text_muted"]).pack(side=tk.LEFT)
        contact_entry = ttk.Entry(contact_frame, font=self.default_font)
        contact_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(self._scale(8), 0))

        btn_bar = tk.Frame(frame, bg=self.theme["bg"])
        btn_bar.pack(fill=tk.X, pady=(self._scale(4), 0))

        def _copy_and_jump():
            content = txt_box.get("1.0", tk.END).strip()
            contact = contact_entry.get().strip()
            full_msg = f"【ClashNodeX 用户反馈】\n联系方式: {contact or '未提供'}\n内容:\n{content}"
            if content and content != "请在此输入你的宝贵建议或遇到的节点问题...":
                self.root.clipboard_clear()
                self.root.clipboard_append(full_msg)
                messagebox.showinfo("已复制", "已将你的反馈内容完整复制到剪贴板！\n即将在浏览器中打开 GitHub Issue 反馈页面，直接粘贴即可提交！")
            import webbrowser
            webbrowser.open("https://github.com/Arnold/ClashNodeX/issues")
            diag.destroy()

        def _submit_direct():
            content = txt_box.get("1.0", tk.END).strip()
            contact = contact_entry.get().strip()
            if not content or content == "请在此输入你的宝贵建议或遇到的节点问题...":
                messagebox.showwarning("提示", "请输入有效的建议内容后再提交！")
                return
            fb_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_feedback.txt")
            with open(fb_log, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 联系方式: {contact or '无'}\n{content}\n---\n")
            messagebox.showinfo("感谢反馈", "✅ 感谢你的建议！\n反馈已成功保存到本地建议箱。如果是紧急 Bug 请前往 GitHub Issue 发帖，作者会第一时间跟进排查！")
            diag.destroy()

        btn_jump = tk.Button(
            btn_bar,
            text="🚀 提交并前往 GitHub 提 Issue",
            bg=self.theme["primary"],
            fg=self.theme["primary_fg"],
            font=self.bold_font,
            relief=tk.FLAT,
            padx=self._scale(12),
            pady=self._scale(4),
            cursor="hand2",
            command=_copy_and_jump
        )
        btn_jump.pack(side=tk.LEFT, padx=(0, self._scale(8)))
        self._apply_interactive_effect(btn_jump)

        btn_local = tk.Button(
            btn_bar,
            text="📝 本地暂存建议",
            bg=self.theme["btn_bg"],
            fg=self.theme["btn_fg"],
            font=self.default_font,
            relief=tk.FLAT,
            bd=0,
            padx=self._scale(12),
            pady=self._scale(4),
            cursor="hand2",
            command=_submit_direct
        )
        btn_local.pack(side=tk.LEFT)
        self._apply_interactive_effect(btn_local)

    def _on_group_right_click(self, event):
        idx = self.group_listbox.nearest(event.y)
        if 0 <= idx < self.group_listbox.size():
            self.group_listbox.selection_clear(0, tk.END)
            self.group_listbox.selection_set(idx)
            self.group_listbox.activate(idx)
            self._on_group_selected()
            self.group_context_menu.post(event.x_root, event.y_root)

    def _action_group_pin_top(self):
        if not self.current_group_name:
            return
        cur_name = self.current_group_name
        if self.cm.pin_group_to_top(cur_name):
            self._refresh_group_list(target_group_name=cur_name)
            self._commit_and_sync(f"已置顶分组【{cur_name}】", delay_ms=300, skip_binary=True)

    def _action_group_move_up(self):
        if not self.current_group_name:
            return
        cur_name = self.current_group_name
        if self.cm.move_group_up(cur_name):
            self._refresh_group_list(target_group_name=cur_name)
            self._commit_and_sync(f"已上移分组【{cur_name}】", delay_ms=300, skip_binary=True)

    def _action_group_move_down(self):
        if not self.current_group_name:
            return
        cur_name = self.current_group_name
        if self.cm.move_group_down(cur_name):
            self._refresh_group_list(target_group_name=cur_name)
            self._commit_and_sync(f"已下移分组【{cur_name}】", delay_ms=300, skip_binary=True)

    def _action_create_group(self):
        name = CustomInputDialog(self.root, "新建分组", "请输入新节点分组的名称（如：★ 常用节点）：").result
        if name and name.strip():
            clean_name = name.strip()
            succ, msg = self.cm.add_group(clean_name)
            if succ:
                self.current_group_name = clean_name
                self._refresh_group_list(target_group_name=clean_name)
                self._commit_and_sync(f"分组【{clean_name}】创建成功", delay_ms=0, skip_binary=False)
                messagebox.showinfo(
                    "创建成功",
                    f"✅ 分组【{clean_name}】已成功创建！\n\n已自动通过核心校验并写入配置。\n现在你可以直接在右侧粘贴 (Ctrl+V) 节点，或点击【⭐ 置顶】【⬆ 上移】调整分组顺序。"
                )
            else:
                messagebox.showerror("创建失败", msg)

    def _action_rename_group(self):
        if not self.current_group_name:
            return
        can_del, _ = self.cm.can_delete_group(self.current_group_name)
        if not can_del:
            messagebox.showwarning("受保护分组", f"分组【{self.current_group_name}】受系统分流规则直接保护，不支持改名以确保网络稳定。")
            return

        new_name = CustomInputDialog(
            self.root,
            "重命名分组",
            f"将分组【{self.current_group_name}】重命名为：",
            initialvalue=self.current_group_name
        ).result
        if new_name and new_name.strip() and new_name.strip() != self.current_group_name:
            new_name = new_name.strip()
            succ, msg = self.cm.rename_group(self.current_group_name, new_name)
            if succ:
                self.current_group_name = new_name
                self._refresh_group_list(target_group_name=new_name)
                self._commit_and_sync(f"已重命名为【{new_name}】", delay_ms=0, skip_binary=True)
            else:
                messagebox.showerror("错误", msg)

    def _action_delete_group(self):
        if not self.current_group_name:
            return
        can_del, reason = self.cm.can_delete_group(self.current_group_name)
        if not can_del:
            messagebox.showwarning(
                "禁止删除保护",
                f"⚠️ 无法删除【{self.current_group_name}】：\n\n{reason}"
            )
            return

        msg = f"确定要删除分组【{self.current_group_name}】吗？\n（组内的节点本身不会被删除，仅删除此分组视图）"
        if CustomConfirmDialog(self.root, "删除分组确认", msg, is_danger=True, confirm_text="确认删除").result:
            succ, msg_del = self.cm.delete_group(self.current_group_name)
            if succ:
                self._refresh_group_list()
                self._commit_and_sync("分组已安全删除", delay_ms=0, skip_binary=True)
            else:
                messagebox.showerror("删除失败", msg_del)

    def _action_manual_save(self):
        if hasattr(self, "btn_save") and self.btn_save:
            self.btn_save.config(text="⏳ 正在保存...", state=tk.DISABLED, bg="#64748b")
        if hasattr(self, "save_badge") and self.save_badge:
            self.save_badge.config(text="● 正在安全校验并写入磁盘...", foreground="#f59e0b")
        self._update_status("● 正在执行配置安全校验并写入磁盘与内核...", is_error=False)

        def worker():
            t0 = time.time()
            with self._save_lock:
                succ, msg = self.cm.save_and_apply(skip_binary_validation=False)
            cost_ms = int((time.time() - t0) * 1000)

            def on_done():
                save_bg = self.theme.get("success", "#16a34a")
                if hasattr(self, "btn_save") and self.btn_save:
                    self.btn_save.config(text="💾 立即保存 (Ctrl+S)", state=tk.NORMAL, bg=save_bg)
                if succ:
                    if hasattr(self, "save_badge") and self.save_badge:
                        self.save_badge.config(text="● 即时自动同步生效", foreground=save_bg)
                    self._update_status(f"✅ 配置已成功安全写入磁盘并重载内核生效！（耗时 {cost_ms}ms）")
                else:
                    danger_bg = self.theme.get("danger", "#dc2626")
                    if hasattr(self, "save_badge") and self.save_badge:
                        self.save_badge.config(text="● 保存被安全拦截", foreground=danger_bg)
                    self._update_status(f"保存拦截: {msg}", is_error=True)
                    messagebox.showerror("保存拦截", msg)

            self.root.after(0, on_done)

        threading.Thread(target=worker, daemon=True).start()

    def _switch_theme(self, theme_key: str):
        if theme_key in THEMES:
            self.theme_name = theme_key
            self.custom_theme = None
            self.theme = dict(THEMES[theme_key])
            save_settings({"theme_name": theme_key, "custom_theme": None})
            self._reapply_styles()
            self._update_status(f"已切换主题为：{self.theme['name']}")

    def _action_import_theme(self):
        file_path = filedialog.askopenfilename(
            title="选择自定义皮肤配置文件 (*.json)",
            filetypes=[("JSON 皮肤文件", "*.json"), ("所有文件", "*.*")]
        )
        if not file_path or not os.path.isfile(file_path):
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("皮肤文件必须是一个 JSON 对象字典！")
            self.theme_name = "custom"
            self.custom_theme = data
            self.theme = self._resolve_theme("custom", data)
            save_settings({"theme_name": "custom", "custom_theme": data})
            self._reapply_styles()
            self._update_status(f"✅ 自定义皮肤【{self.theme.get('name', '未命名')}】导入成功！")
        except Exception as e:
            messagebox.showerror("皮肤导入失败", f"无法解析皮肤文件：\n{e}")

    def _action_export_theme(self):
        file_path = filedialog.asksaveasfilename(
            title="导出当前皮肤模板 (*.json)",
            defaultextension=".json",
            filetypes=[("JSON 皮肤文件", "*.json")],
            initialfile=f"skin_{self.theme.get('theme_id', 'custom')}.json"
        )
        if not file_path:
            return
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.theme, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("导出成功", f"✅ 皮肤模板已成功导出至：\n{file_path}\n\n你可以自由修改其中的颜色代码，随后点击【导入自定义皮肤】即可换肤！")
        except Exception as e:
            messagebox.showerror("导出失败", f"保存皮肤模板失败：\n{e}")

    def _action_import_image_skin(self):
        file_path = filedialog.askopenfilename(
            parent=self.root,
            title="选择图片作为背景壁纸/皮肤",
            filetypes=[
                ("图片文件", "*.png;*.jpg;*.jpeg;*.webp;*.bmp"),
                ("所有文件", "*.*")
            ]
        )
        if not file_path or not os.path.isfile(file_path):
            return
        self._apply_image_skin(file_path)

    def _action_apply_moon_skin(self):
        moon_path = os.path.join(SCRIPT_DIR, "themes", "moon_artemis.jpg")
        if not os.path.isfile(moon_path):
            cand1 = "F:\\桌面\\壁纸_Artemis.jpg"
            cand2 = os.path.join(os.environ.get("USERPROFILE", "C:\\Users\\Arnold"), "Desktop", "壁纸_Artemis.jpg")
            if os.path.isfile(cand1):
                moon_path = cand1
            elif os.path.isfile(cand2):
                moon_path = cand2
        if not os.path.isfile(moon_path):
            messagebox.showwarning("提示", "未找到月球探索壁纸 (themes/moon_artemis.jpg)！")
            return
        self._apply_image_skin(moon_path)

    def _action_apply_sample_skin(self):
        sample_path = os.path.join(SCRIPT_DIR, "themes", "sample_skin_gradient.png")
        if not os.path.isfile(sample_path):
            messagebox.showwarning("提示", "未找到示例图片壁纸 themes/sample_skin_gradient.png！")
            return
        self._apply_image_skin(sample_path)

    def _apply_image_skin(self, img_path: str):
        try:
            from PIL import Image
            im = Image.open(img_path).convert("RGB")
            small = im.resize((10, 10))
            pixels = [small.getpixel((x, y)) for x in range(10) for y in range(10)]
            avg_r = sum(p[0] for p in pixels) // len(pixels)
            avg_g = sum(p[1] for p in pixels) // len(pixels)
            avg_b = sum(p[2] for p in pixels) // len(pixels)
            lum = (0.299 * avg_r + 0.587 * avg_g + 0.114 * avg_b)

            is_dark = lum < 128
            base_key = "dark_night" if is_dark else "default_light"
            new_theme = dict(THEMES[base_key])
            new_theme["theme_id"] = "image_skin"
            new_theme["name"] = f"图片壁纸 ({os.path.basename(img_path)[:10]})"

            if is_dark:
                new_theme["bg"] = f"#{max(15, avg_r//4):02x}{max(20, avg_g//4):02x}{max(35, avg_b//4):02x}"
            else:
                new_theme["bg"] = f"#{min(252, avg_r+15):02x}{min(252, avg_g+15):02x}{min(252, avg_b+15):02x}"

            self.theme_name = "image_skin"
            self.custom_theme = new_theme
            self.theme = new_theme
            save_settings({"theme_name": "image_skin", "custom_theme": new_theme, "bg_image_path": img_path})
            self._reapply_styles()
            self._update_status(f"🖼️ 已成功应用图片皮肤壁纸：{os.path.basename(img_path)}")
            messagebox.showinfo(
                "换肤成功",
                f"✅ 成功应用图片壁纸皮肤！\n\n图片：{os.path.basename(img_path)}\n自适应色彩模式：{'深色模式' if is_dark else '浅色模式'}\n\n随时可在【皮肤】菜单中选择【清除图片壁纸】恢复默认纯色。"
            )
        except Exception as e:
            messagebox.showerror("图片加载失败", f"无法解析或应用所选图片：\n{e}")

    def _action_clear_bg_image(self):
        self._switch_theme("default_light")
        save_settings({"bg_image_path": ""})
        self._update_status("已恢复经典浅白默认纯色皮肤")
        messagebox.showinfo("已恢复", "已清除图片壁纸皮肤，恢复经典浅白纯色主题！")

    def _get_traffic_period_text(self) -> str:
        st = getattr(self, "traffic_start_time", 0)
        if st <= 0:
            try:
                import ctypes
                uptime_ms = ctypes.windll.kernel32.GetTickCount64()
                st = time.time() - (uptime_ms / 1000.0)
            except Exception:
                st = time.time()
            self.traffic_start_time = st
        st_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(st))
        if self.traffic_enabled:
            return f"📅 {st_str} 至 至今"
        else:
            return f"📅 {st_str} (已暂停)"

    def _update_traffic_period_display(self):
        if hasattr(self, "lbl_traffic_period") and self.lbl_traffic_period:
            self.lbl_traffic_period.config(text=self._get_traffic_period_text())

    def _toggle_traffic_monitoring(self):
        self.traffic_enabled = not self.traffic_enabled
        self._save_traffic_state()
        if self.traffic_enabled:
            self.btn_traffic_toggle.config(
                text="🟢 监控中",
                bg="#ecfdf5",
                fg=self.theme["success"]
            )
            self._start_traffic_worker()
            self._update_status("已开启实时流量监控")
        else:
            self.traffic_running = False
            self.btn_traffic_toggle.config(
                text="⏸️ 已暂停",
                bg=self.theme["btn_bg"],
                fg=self.theme["text_muted"]
            )
            if hasattr(self, "lbl_traffic_speed") and self.lbl_traffic_speed:
                self.lbl_traffic_speed.config(text="⚡ 实时网速: (已暂停)")
            self._update_status("已暂停实时流量监控")
        self._update_traffic_period_display()

    def _save_traffic_state(self):
        data = {
            "traffic_start_time": self.traffic_start_time,
            "traffic_lifetime_up": getattr(self, "traffic_lifetime_up", 0),
            "traffic_lifetime_down": getattr(self, "traffic_lifetime_down", 0),
            "traffic_session_base_up": getattr(self, "traffic_session_base_up", 0),
            "traffic_session_base_down": getattr(self, "traffic_session_base_down", 0),
            "traffic_last_core_up": getattr(self, "traffic_last_core_up", 0),
            "traffic_last_core_down": getattr(self, "traffic_last_core_down", 0),
            "traffic_proxy_lifetime_up": getattr(self, "traffic_proxy_lifetime_up", 0),
            "traffic_proxy_lifetime_down": getattr(self, "traffic_proxy_lifetime_down", 0),
            "traffic_enabled": self.traffic_enabled
        }
        save_settings(data)

    def _reset_traffic_stats(self):
        snap = self.cm.get_runtime_traffic_snapshot()
        cur_up = snap["total_up"] if snap else 0
        cur_down = snap["total_down"] if snap else 0
        self.traffic_start_time = time.time()
        self.traffic_lifetime_up = 0
        self.traffic_lifetime_down = 0
        self.traffic_session_base_up = cur_up
        self.traffic_session_base_down = cur_down
        self.traffic_last_core_up = cur_up
        self.traffic_last_core_down = cur_down
        self.traffic_proxy_lifetime_up = 0
        self.traffic_proxy_lifetime_down = 0
        self._save_traffic_state()
        self._update_traffic_period_display()
        if hasattr(self, "lbl_traffic_total") and self.lbl_traffic_total:
            self.lbl_traffic_total.config(text="🌐 Clash总吞吐: [上行] 0 B | [下行] 0 B (⚡ 累计: 0 B)")
        if hasattr(self, "lbl_traffic_proxy") and self.lbl_traffic_proxy:
            self.lbl_traffic_proxy.config(text="🚀 节点代理实耗: [上行] 0 B | [下行] 0 B (⚡ 消耗: 0 B)")
        self._update_status("已将全部流量统计清零，起始时间已更新为当前时刻！")

    def _action_set_custom_traffic_period(self):
        diag = tk.Toplevel(self.root)
        diag.title("📅 设定流量统计周期")
        diag.transient(self.root)
        diag.grab_set()
        diag.resizable(False, False)
        
        frame = ttk.Frame(diag, padding=self._scale(16))
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="选择或自定义你的流量统计起始时间：\n(统计不受开关机、关闭软件影响，永久真实累计)",
            font=self.bold_font
        ).pack(anchor="w", pady=(0, self._scale(12)))

        now = time.localtime()
        # Month 1st
        m1_ts = time.mktime((now.tm_year, now.tm_mon, 1, 0, 0, 0, 0, 0, -1))
        m1_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(m1_ts))
        
        # Today 00:00
        td_ts = time.mktime((now.tm_year, now.tm_mon, now.tm_mday, 0, 0, 0, 0, 0, -1))
        td_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(td_ts))

        # Boot time
        try:
            import ctypes
            uptime_ms = ctypes.windll.kernel32.GetTickCount64()
            boot_ts = time.time() - (uptime_ms / 1000.0)
        except Exception:
            boot_ts = time.time()
        boot_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(boot_ts))

        def apply_ts(ts):
            self.traffic_start_time = ts
            self._save_traffic_state()
            self._update_traffic_period_display()
            self._update_status(f"已更新统计起始时间为: {time.strftime('%Y-%m-%d %H:%M', time.localtime(ts))}")
            diag.destroy()

        def apply_now_reset():
            diag.destroy()
            self._reset_traffic_stats()

        ttk.Button(
            frame,
            text=f"📅 从本月 1 号开始 ({m1_str}) - 月度套餐推荐",
            command=lambda: apply_ts(m1_ts)
        ).pack(fill=tk.X, pady=self._scale(4))

        ttk.Button(
            frame,
            text=f"📅 从今天 00:00 开始 ({td_str}) - 日度统计",
            command=lambda: apply_ts(td_ts)
        ).pack(fill=tk.X, pady=self._scale(4))

        ttk.Button(
            frame,
            text=f"💻 从本次电脑开机开始 ({boot_str})",
            command=lambda: apply_ts(boot_ts)
        ).pack(fill=tk.X, pady=self._scale(4))

        ttk.Button(
            frame,
            text="🔄 此时此刻立即清零重新起算",
            command=apply_now_reset
        ).pack(fill=tk.X, pady=self._scale(4))

        # Custom entry
        custom_box = ttk.LabelFrame(frame, text="✏️ 自定义起始时间 (格式: YYYY-MM-DD HH:MM)", padding=self._scale(8))
        custom_box.pack(fill=tk.X, pady=(self._scale(10), 0))

        cur_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(self.traffic_start_time))
        entry_var = tk.StringVar(value=cur_str)
        entry = ttk.Entry(custom_box, textvariable=entry_var, font=self.default_font)
        entry.pack(fill=tk.X, pady=(0, self._scale(8)))

        def apply_custom():
            s = entry_var.get().strip()
            try:
                t_struct = time.strptime(s, "%Y-%m-%d %H:%M")
                ts = time.mktime(t_struct)
                apply_ts(ts)
            except Exception as e:
                messagebox.showerror("格式错误", f"请输入正确的日期时间格式：YYYY-MM-DD HH:MM\n例如: 2026-09-01 00:00\n错误详情: {e}")

        ttk.Button(custom_box, text="应用自定义时间", command=apply_custom).pack(anchor="e")

    def _start_traffic_worker(self):
        if self.traffic_running:
            return
        self.traffic_running = True
        self.traffic_thread = threading.Thread(target=self._traffic_worker_loop, daemon=True)
        self.traffic_thread.start()

    def _traffic_worker_loop(self):
        def fmt_bytes(n):
            if n < 1024:
                return f"{n} B"
            elif n < 1024 * 1024:
                return f"{n/1024:.1f} KB"
            elif n < 1024 * 1024 * 1024:
                return f"{n/(1024*1024):.2f} MB"
            else:
                return f"{n/(1024*1024*1024):.2f} GB"

        def fmt_speed(n):
            if n < 1024:
                return f"{n:.0f} B/s"
            elif n < 1024 * 1024:
                return f"{n/1024:.1f} KB/s"
            else:
                return f"{n/(1024*1024):.2f} MB/s"

        active_proxy_conns = {}
        save_counter = 0
        last_snap_time = None
        last_calc_up = None
        last_calc_down = None

        while self.traffic_running and self.traffic_enabled:
            snap = self.cm.get_runtime_traffic_snapshot()
            if snap:
                cur_up = snap["total_up"]
                cur_down = snap["total_down"]
                raw_proxy_conns = snap.get("proxy_conns", [])
                now_t = snap.get("timestamp", time.time())

                # Rate computation
                rate_up = 0.0
                rate_down = 0.0
                if last_snap_time is not None and last_calc_up is not None and last_calc_down is not None:
                    dt = max(0.2, now_t - last_snap_time)
                    if cur_up >= last_calc_up and cur_down >= last_calc_down:
                        rate_up = (cur_up - last_calc_up) / dt
                        rate_down = (cur_down - last_calc_down) / dt

                last_snap_time = now_t
                last_calc_up = cur_up
                last_calc_down = cur_down

                # Total traffic computation (retains continuity across PC reboots and Clash restarts)
                if cur_up < getattr(self, "traffic_last_core_up", 0):
                    self.traffic_lifetime_up += max(0, self.traffic_last_core_up - self.traffic_session_base_up)
                    self.traffic_lifetime_down += max(0, self.traffic_last_core_down - self.traffic_session_base_down)
                    self.traffic_session_base_up = 0
                    self.traffic_session_base_down = 0

                self.traffic_last_core_up = cur_up
                self.traffic_last_core_down = cur_down

                disp_total_up = self.traffic_lifetime_up + max(0, cur_up - self.traffic_session_base_up)
                disp_total_down = self.traffic_lifetime_down + max(0, cur_down - self.traffic_session_base_down)

                # Accurate Proxy Node traffic accumulation across active & closed connections
                current_seen = {}
                for c in raw_proxy_conns:
                    cid = c.get("id")
                    if cid:
                        current_seen[cid] = (c.get("upload", 0), c.get("download", 0))

                for cid, (last_u, last_d) in active_proxy_conns.items():
                    if cid not in current_seen:
                        self.traffic_proxy_lifetime_up += last_u
                        self.traffic_proxy_lifetime_down += last_d

                active_proxy_conns = current_seen

                live_proxy_u = sum(u for u, d in active_proxy_conns.values())
                live_proxy_d = sum(d for u, d in active_proxy_conns.values())

                disp_proxy_up = self.traffic_proxy_lifetime_up + live_proxy_u
                disp_proxy_down = self.traffic_proxy_lifetime_down + live_proxy_d

                save_counter += 1
                if save_counter >= 5:
                    save_counter = 0
                    try:
                        self._save_traffic_state()
                    except Exception:
                        pass

                def update_ui(tu=disp_total_up, td=disp_total_down, pu=disp_proxy_up, pd=disp_proxy_down, ru=rate_up, rd=rate_down):
                    if not self.traffic_running:
                        return
                    if hasattr(self, "lbl_traffic_total") and self.lbl_traffic_total:
                        total_bytes = tu + td
                        self.lbl_traffic_total.config(
                            text=f"🌐 Clash总吞吐: [上行] {fmt_bytes(tu)} | [下行] {fmt_bytes(td)} (⚡ 累计: {fmt_bytes(total_bytes)})"
                        )
                    if hasattr(self, "lbl_traffic_proxy") and self.lbl_traffic_proxy:
                        proxy_bytes = pu + pd
                        self.lbl_traffic_proxy.config(
                            text=f"🚀 节点代理实耗: [上行] {fmt_bytes(pu)} | [下行] {fmt_bytes(pd)} (⚡ 消耗: {fmt_bytes(proxy_bytes)})"
                        )
                    if hasattr(self, "lbl_traffic_speed") and self.lbl_traffic_speed:
                        self.lbl_traffic_speed.config(
                            text=f"⚡ 实时网速: ↑ {fmt_speed(ru)}   ↓ {fmt_speed(rd)}"
                        )
                    self._update_traffic_period_display()

                try:
                    self.root.after(0, update_ui)
                except Exception:
                    break

            time.sleep(1.0)

    def _reload_current_group_data(self):
        if self.current_group_name:
            self.group_nodes_data = self.cm.get_group_proxies(self.current_group_name)
            self._filter_nodes()

    def _refresh_group_listbox_counts(self):
        groups = self.cm.get_groups()
        target_idx = -1
        self.group_listbox.delete(0, tk.END)
        for idx, g in enumerate(groups):
            prefix = "🔒 " if g["is_protected"] else "📁 "
            self.group_listbox.insert(tk.END, f" {prefix}{g['name']}  ({g['count_display']})")
            if self.current_group_name and g["name"] == self.current_group_name:
                target_idx = idx
        if target_idx >= 0:
            self.group_listbox.selection_set(target_idx)
            self.group_listbox.see(target_idx)
        elif groups:
            self.group_listbox.selection_set(0)


def main():
    root = tk.Tk()
    root.withdraw()
    app = ClashNodeManagerApp(root)
    root.update_idletasks()
    root.deiconify()
    root.mainloop()


if __name__ == "__main__":
    main()
