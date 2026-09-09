# -*- coding: utf-8 -*-
# ClashNodeX Modern Setup Wizard (安装向导)
# 版本: v1.3.0 (Build 2026.09.09)
# 纯白/浅灰现代极客风格 · 无黑边 · 驱动器可视化空间卡片 · 零闪烁平滑启动 · 2K/3K/4K 高分屏自适应等比放大

import os
import sys
import shutil
import time
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


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


def refresh_windows_icon_cache():
    try:
        # SHCNE_ASSOCCHANGED = 0x08000000, SHCNF_IDLIST = 0x0000
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
    except Exception:
        pass


def get_res_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


def get_drives_info():
    drives = []
    for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
        root = letter + ':\\'
        if os.path.exists(root):
            try:
                usage = shutil.disk_usage(root)
                free_gb = usage.free / (1024 ** 3)
                total_gb = usage.total / (1024 ** 3)
                used_gb = total_gb - free_gb
                used_pct = (used_gb / total_gb) * 100 if total_gb > 0 else 0
                drives.append({
                    'letter': letter,
                    'root': root,
                    'free_gb': free_gb,
                    'total_gb': total_gb,
                    'used_pct': used_pct,
                    'is_system': letter.upper() == 'C'
                })
            except Exception:
                pass
    return drives


def get_default_install_dir():
    candidates = ['D:\\Program Files\\ClashNodeX',
                  'E:\\Program Files\\ClashNodeX',
                  'F:\\Program Files\\ClashNodeX']
    for c in candidates:
        drive = c[:3]
        if os.path.exists(drive):
            try:
                usage = shutil.disk_usage(drive)
                if usage.free > 1 * (1024 ** 3):
                    return c
            except Exception:
                pass
    return 'C:\\Program Files\\ClashNodeX'


def get_all_desktop_paths():
    paths = []
    dp = os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
    if os.path.exists(dp):
        paths.append(dp)

    up = os.path.join(os.path.expanduser('~'), 'Desktop')
    if os.path.exists(up) and up not in paths:
        paths.append(up)

    for custom in ['F:\\桌面', 'D:\\桌面', 'E:\\桌面']:
        if os.path.exists(custom) and custom not in paths:
            paths.append(custom)

    return paths


class ClashNodeXInstaller(tk.Tk):
    def __init__(self):
        super().__init__()
        # Smooth startup: hide window first to prevent 200x200 grey box or position jumping
        self.withdraw()

        self.scale = get_screen_scale_factor()

        self.title('Clash 节点跃迁 (ClashNodeX) v1.3.0 - 安装向导')
        
        # Grand, expansive, high-DPI modern window size (base 960x640, scaled by DPI)
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        target_w = self._scale(960)
        target_h = self._scale(640)
        self.window_w = min(int(sw * 0.90), max(self._scale(840), target_w))
        self.window_h = min(int(sh * 0.90), max(self._scale(560), target_h))

        self.geometry(f'{self.window_w}x{self.window_h}')
        self.minsize(self._scale(820), self._scale(540))
        self.resizable(False, False)
        self.configure(bg='#FFFFFF')

        # Fonts definition (Tkinter points are automatically DPI-scaled, clean & clear)
        self.font_title = ('Microsoft YaHei UI', 15, 'bold')
        self.font_subtitle = ('Microsoft YaHei UI', 11, 'bold')
        self.font_badge = ('Microsoft YaHei UI', 9, 'bold')
        self.font_heading = ('Microsoft YaHei UI', 13, 'bold')
        self.font_body = ('Microsoft YaHei UI', 10)
        self.font_body_bold = ('Microsoft YaHei UI', 10, 'bold')
        self.font_small = ('Microsoft YaHei UI', 9)
        self.font_small_bold = ('Microsoft YaHei UI', 9, 'bold')
        self.font_tiny = ('Microsoft YaHei UI', 8)
        self.font_btn = ('Microsoft YaHei UI', 10, 'bold')
        self.font_code = ('Consolas', 10)
        self.font_log = ('Consolas', 9)

        icon_path = get_res_path('app_icon.ico')
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self.drives = get_drives_info()
        
        # Choose smart default directory: non-system drive with >= 2GB space
        non_sys = [d for d in self.drives if not d['is_system'] and d['free_gb'] >= 2.0]
        if non_sys:
            default_drive = non_sys[0]['letter']
            self.install_dir = default_drive + ':\\ClashNodeX'
            self.selected_drive_letter = default_drive
        else:
            self.install_dir = 'C:\\ClashNodeX'
            self.selected_drive_letter = 'C'

        self.var_path = tk.StringVar(value=self.install_dir)
        self.var_desktop_ico = tk.BooleanVar(value=True)
        self.var_startmenu = tk.BooleanVar(value=True)
        self.var_launch_now = tk.BooleanVar(value=True)

        self.current_step = 1
        self.drive_card_widgets = {}
        self.step_widgets = []

        self._setup_styles()
        self._build_layout()
        self._show_step_1()

        # Center and smoothly reveal window
        self._center_window()
        self.update_idletasks()
        self.deiconify()

    def _scale(self, val: int) -> int:
        return int(round(val * self.scale))

    def _center_window(self):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - self.window_w) // 2)
        y = max(0, (sh - self.window_h) // 2)
        self.geometry(f'{self.window_w}x{self.window_h}+{x}+{y}')

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Installer.Horizontal.TProgressbar',
                        troughcolor='#F1F5F9',
                        background='#0284C7',
                        lightcolor='#38BDF8',
                        darkcolor='#0284C7',
                        bordercolor='#E2E8F0',
                        thickness=self._scale(18))
        style.configure('Drive.Horizontal.TProgressbar',
                        troughcolor='#F1F5F9',
                        background='#0284C7',
                        lightcolor='#38BDF8',
                        darkcolor='#0284C7',
                        bordercolor='#E2E8F0',
                        thickness=self._scale(8))

    def _build_layout(self):
        # Master Horizontal Container
        self.body_frame = tk.Frame(self, bg='#FFFFFF')
        self.body_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        # Left Hero Branding Sidebar (Spacious width, scaled)
        sidebar_w = self._scale(280)
        self.sidebar = tk.Frame(self.body_frame, bg='#F8FAFC', width=sidebar_w, bd=0)
        self.sidebar.pack(fill=tk.Y, side=tk.LEFT)
        self.sidebar.pack_propagate(False)

        # Sidebar right separator line
        sidebar_sep = tk.Frame(self.body_frame, bg='#E2E8F0', width=1)
        sidebar_sep.pack(fill=tk.Y, side=tk.LEFT)

        self._build_sidebar_content()

        # Right Main Content Area
        self.right_panel = tk.Frame(self.body_frame, bg='#FFFFFF')
        self.right_panel.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # Bottom Action Bar
        bottom_sep = tk.Frame(self, bg='#E2E8F0', height=1)
        bottom_sep.pack(fill=tk.X, side=tk.TOP)

        bottom_h = self._scale(72)
        self.bottom_bar = tk.Frame(self, bg='#FFFFFF', height=bottom_h)
        self.bottom_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.bottom_bar.pack_propagate(False)

        self._build_bottom_bar_content()

    def _build_sidebar_content(self):
        top_hero = tk.Frame(self.sidebar, bg='#F8FAFC')
        top_hero.pack(fill=tk.X, padx=self._scale(24), pady=(self._scale(28), self._scale(18)))

        # Bright Fox Logo (Lanczos high-quality resize, scaled with DPI)
        fox_path = get_res_path('app_icon.png')
        self.img_sidebar_fox = None
        logo_sz = self._scale(80)
        if HAS_PIL and os.path.exists(fox_path):
            try:
                im = Image.open(fox_path).resize((logo_sz, logo_sz), Image.Resampling.LANCZOS)
                self.img_sidebar_fox = ImageTk.PhotoImage(im)
                lbl_logo = tk.Label(top_hero, image=self.img_sidebar_fox, bg='#F8FAFC')
                lbl_logo.pack(anchor=tk.W, pady=(0, self._scale(12)))
            except Exception:
                pass

        lbl_appname = tk.Label(top_hero, text='Clash 节点跃迁',
                               font=self.font_title,
                               fg='#0F172A', bg='#F8FAFC')
        lbl_appname.pack(anchor=tk.W)

        lbl_en = tk.Label(top_hero, text='ClashNodeX',
                          font=self.font_subtitle,
                          fg='#0284C7', bg='#F8FAFC')
        lbl_en.pack(anchor=tk.W, pady=(self._scale(2), self._scale(8)))

        # Version Pill Badge
        badge_frame = tk.Frame(top_hero, bg='#E0F2FE', padx=self._scale(10), pady=self._scale(4))
        badge_frame.pack(anchor=tk.W)
        lbl_badge = tk.Label(badge_frame, text='⚡ v1.3.0 (Build 2026.09.09)',
                             font=self.font_badge,
                             fg='#0369A1', bg='#E0F2FE')
        lbl_badge.pack()

        # Step Breadcrumb Navigation
        nav_box = tk.Frame(self.sidebar, bg='#F8FAFC')
        nav_box.pack(fill=tk.X, padx=self._scale(24), pady=(self._scale(24), 0))

        tk.Label(nav_box, text='安装步骤', font=self.font_small_bold,
                 fg='#94A3B8', bg='#F8FAFC').pack(anchor=tk.W, pady=(0, self._scale(12)))

        steps = [
            ('①', '选择路径与配置'),
            ('②', '极速部署写入'),
            ('③', '跃迁就绪启动')
        ]
        self.step_widgets = []
        for idx, (num, name) in enumerate(steps, 1):
            row = tk.Frame(nav_box, bg='#F8FAFC')
            row.pack(fill=tk.X, pady=self._scale(5))
            lbl_num = tk.Label(row, text=num, font=self.font_small_bold,
                               fg='#94A3B8', bg='#F8FAFC', width=2)
            lbl_num.pack(side=tk.LEFT)
            lbl_txt = tk.Label(row, text=name, font=self.font_small,
                               fg='#64748B', bg='#F8FAFC')
            lbl_txt.pack(side=tk.LEFT, padx=self._scale(8))
            self.step_widgets.append((lbl_num, lbl_txt))

        self._update_step_nav_display(1)

        # Bottom Assurance
        bottom_info = tk.Frame(self.sidebar, bg='#F8FAFC')
        bottom_info.pack(side=tk.BOTTOM, fill=tk.X, padx=self._scale(20), pady=self._scale(20))
        tk.Label(bottom_info, text='🛡️ 纯本地执行 · 零隐私采集\n❤️ 开源免费 · 点赞关注即赞助',
                 font=self.font_tiny, fg='#94A3B8', bg='#F8FAFC', justify=tk.LEFT).pack(anchor=tk.W)

    def _update_step_nav_display(self, current_step):
        for idx, (lbl_num, lbl_txt) in enumerate(self.step_widgets, 1):
            if idx == current_step:
                lbl_num.config(fg='#0284C7', text='▶')
                lbl_txt.config(fg='#0284C7', font=self.font_small_bold)
            elif idx < current_step:
                lbl_num.config(fg='#10B981', text='✓')
                lbl_txt.config(fg='#10B981', font=self.font_small)
            else:
                lbl_num.config(fg='#94A3B8', text=['①', '②', '③'][idx - 1])
                lbl_txt.config(fg='#94A3B8', font=self.font_small)

    def _build_bottom_bar_content(self):
        inner = tk.Frame(self.bottom_bar, bg='#FFFFFF')
        inner.pack(fill=tk.BOTH, expand=True, padx=self._scale(28), pady=self._scale(14))

        self.lbl_bottom_hint = tk.Label(inner, text='Clash Verge 专属极客管家 · 智能节点跃迁与多维精准测速',
                                        font=self.font_small, fg='#64748B', bg='#FFFFFF')
        self.lbl_bottom_hint.pack(side=tk.LEFT)

        self.btn_cancel = tk.Button(inner, text='取消', font=self.font_small,
                                    bg='#F1F5F9', fg='#475569', activebackground='#E2E8F0',
                                    relief=tk.FLAT, bd=0, padx=self._scale(20), pady=self._scale(7), cursor='hand2',
                                    command=self.destroy)
        self.btn_cancel.pack(side=tk.RIGHT, padx=(self._scale(12), 0))

        self.btn_action = tk.Button(inner, text='立即安装', font=self.font_btn,
                                    bg='#0284C7', fg='#FFFFFF', activebackground='#0369A1',
                                    relief=tk.FLAT, bd=0, padx=self._scale(30), pady=self._scale(8), cursor='hand2',
                                    command=self._on_action_clicked)
        self.btn_action.pack(side=tk.RIGHT)

    def _clear_right_panel(self):
        for w in self.right_panel.winfo_children():
            w.destroy()

    def _show_step_1(self):
        self._clear_right_panel()
        self.current_step = 1
        self._update_step_nav_display(1)

        container = tk.Frame(self.right_panel, bg='#FFFFFF')
        container.pack(fill=tk.BOTH, expand=True, padx=self._scale(32), pady=self._scale(24))

        # Step Title Header
        title_box = tk.Frame(container, bg='#FFFFFF')
        title_box.pack(fill=tk.X, pady=(0, self._scale(16)))

        tk.Label(title_box, text='📁 选择安装目标位置', font=self.font_heading,
                 fg='#0F172A', bg='#FFFFFF').pack(anchor=tk.W)
        tk.Label(title_box, text='可自由安装至任意磁盘或移动设备，推荐选择空间充裕的非系统盘 (如 D/E/F 盘)',
                 font=self.font_small, fg='#64748B', bg='#FFFFFF').pack(anchor=tk.W, pady=(self._scale(4), 0))

        # Visual Drive Cards Frame
        lbl_drive_sec = tk.Label(container, text='已检测到本地磁盘 (点击卡片快速选定目标盘):',
                                 font=self.font_small_bold, fg='#334155', bg='#FFFFFF')
        lbl_drive_sec.pack(anchor=tk.W, pady=(0, self._scale(10)))

        drives_grid = tk.Frame(container, bg='#FFFFFF')
        drives_grid.pack(fill=tk.X, pady=(0, self._scale(16)))

        self.drive_card_widgets.clear()
        for idx, d in enumerate(self.drives[:4]):  # Show up to 4 main drives
            card = self._create_drive_card(drives_grid, d)
            card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0 if idx == 0 else self._scale(8), 0))
            self.drive_card_widgets[d['letter']] = card

        self._highlight_selected_drive_card()

        # Path Entry Box
        path_box_wrapper = tk.Frame(container, bg='#FFFFFF')
        path_box_wrapper.pack(fill=tk.X, pady=(0, self._scale(8)))

        tk.Label(path_box_wrapper, text='自定义安装路径:', font=self.font_small_bold,
                 fg='#334155', bg='#FFFFFF').pack(anchor=tk.W, pady=(0, self._scale(5)))

        path_row = tk.Frame(path_box_wrapper, bg='#FFFFFF', bd=1, relief=tk.SOLID)
        path_row.pack(fill=tk.X)

        self.entry_path = tk.Entry(path_row, textvariable=self.var_path, font=self.font_code,
                                   relief=tk.FLAT, bd=0, bg='#FFFFFF', fg='#0F172A')
        self.entry_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=self._scale(12), pady=self._scale(10))

        btn_browse = tk.Button(path_row, text='📂 浏览...', font=self.font_small,
                               bg='#F1F5F9', fg='#334155', activebackground='#E2E8F0',
                               relief=tk.FLAT, bd=0, padx=self._scale(18), pady=self._scale(6), cursor='hand2',
                               command=self._action_browse)
        btn_browse.pack(side=tk.RIGHT, padx=self._scale(4), pady=self._scale(4))

        # Dynamic Disk Space Indicator Badge
        self.lbl_space_info = tk.Label(container, text='', font=self.font_small,
                                       bg='#FFFFFF', anchor=tk.W)
        self.lbl_space_info.pack(anchor=tk.W, pady=(0, self._scale(16)))
        self._update_space_info()
        self.var_path.trace_add('write', lambda *args: self._on_path_changed())

        # Options Box
        opt_sec = tk.Label(container, text='⚙️ 安装附加选项:',
                           font=self.font_small_bold, fg='#334155', bg='#FFFFFF')
        opt_sec.pack(anchor=tk.W, pady=(0, self._scale(8)))

        opt_frame = tk.Frame(container, bg='#F8FAFC', bd=1, relief=tk.SOLID)
        opt_frame.pack(fill=tk.X)

        c1 = tk.Checkbutton(opt_frame, text='在桌面创建快捷方式 (高清跃迁小狐狸 LOGO)',
                            variable=self.var_desktop_ico, font=self.font_small,
                            bg='#F8FAFC', fg='#1E293B', activebackground='#F8FAFC', selectcolor='#FFFFFF')
        c1.pack(anchor=tk.W, padx=self._scale(14), pady=self._scale(6))

        c2 = tk.Checkbutton(opt_frame, text='在开始菜单创建程序组与一键卸载脚本',
                            variable=self.var_startmenu, font=self.font_small,
                            bg='#F8FAFC', fg='#1E293B', activebackground='#F8FAFC', selectcolor='#FFFFFF')
        c2.pack(anchor=tk.W, padx=self._scale(14), pady=(0, self._scale(6)))

        c3 = tk.Checkbutton(opt_frame, text='安装成功后立即启动 ClashNodeX 极客管家',
                            variable=self.var_launch_now, font=self.font_body_bold,
                            bg='#F8FAFC', fg='#0284C7', activebackground='#F8FAFC', selectcolor='#FFFFFF')
        c3.pack(anchor=tk.W, padx=self._scale(14), pady=(0, self._scale(8)))

    def _create_drive_card(self, parent, drive):
        letter = drive['letter']
        free_gb = drive['free_gb']
        total_gb = drive['total_gb']
        is_sys = drive['is_system']

        card = tk.Frame(parent, bg='#FFFFFF', bd=1, relief=tk.SOLID, cursor='hand2',
                        padx=self._scale(10), pady=self._scale(10))

        # Header Row (Drive letter + tag)
        top_row = tk.Frame(card, bg='#FFFFFF')
        top_row.pack(fill=tk.X)

        title_text = f"💾 {letter}: 盘"
        lbl_letter = tk.Label(top_row, text=title_text, font=self.font_body_bold,
                              fg='#0F172A', bg='#FFFFFF')
        lbl_letter.pack(side=tk.LEFT)

        tag_text = '系统盘' if is_sys else '推荐'
        tag_bg = '#F1F5F9' if is_sys else '#DCFCE7'
        tag_fg = '#64748B' if is_sys else '#15803D'
        lbl_tag = tk.Label(top_row, text=tag_text, font=self.font_tiny,
                           bg=tag_bg, fg=tag_fg, padx=self._scale(5), pady=self._scale(2))
        lbl_tag.pack(side=tk.RIGHT)

        # Space Details
        space_txt = f"{free_gb:.1f} GB 可用"
        lbl_space = tk.Label(card, text=space_txt, font=self.font_small,
                             fg='#475569', bg='#FFFFFF')
        lbl_space.pack(anchor=tk.W, pady=(self._scale(5), self._scale(5)))

        # Mini Capacity Progressbar
        pbar = ttk.Progressbar(card, style='Drive.Horizontal.TProgressbar',
                               orient=tk.HORIZONTAL, mode='determinate', maximum=100)
        pbar.pack(fill=tk.X)
        pbar['value'] = drive['used_pct']

        # Bind click event recursively to all child widgets
        def _on_click(event=None, l=letter):
            self._select_drive(l)

        card.bind('<Button-1>', _on_click)
        lbl_letter.bind('<Button-1>', _on_click)
        lbl_tag.bind('<Button-1>', _on_click)
        lbl_space.bind('<Button-1>', _on_click)
        top_row.bind('<Button-1>', _on_click)

        card.drive_info = drive
        card.lbl_letter = lbl_letter
        card.lbl_space = lbl_space
        card.top_row = top_row
        return card

    def _select_drive(self, letter):
        self.selected_drive_letter = letter
        self.var_path.set(letter + ':\\ClashNodeX')
        self._highlight_selected_drive_card()
        self._update_space_info()

    def _highlight_selected_drive_card(self):
        for letter, card in self.drive_card_widgets.items():
            if letter.upper() == self.selected_drive_letter.upper():
                card.config(bg='#F0F9FF', relief=tk.SOLID, bd=2)
                card.lbl_letter.config(bg='#F0F9FF', fg='#0284C7')
                card.lbl_space.config(bg='#F0F9FF', fg='#0369A1')
                card.top_row.config(bg='#F0F9FF')
            else:
                card.config(bg='#FFFFFF', relief=tk.SOLID, bd=1)
                card.lbl_letter.config(bg='#FFFFFF', fg='#0F172A')
                card.lbl_space.config(bg='#FFFFFF', fg='#475569')
                card.top_row.config(bg='#FFFFFF')

    def _on_path_changed(self):
        p = self.var_path.get().strip()
        if p and len(p) >= 2 and p[1] == ':':
            drive_letter = p[0].upper()
            if drive_letter != self.selected_drive_letter:
                self.selected_drive_letter = drive_letter
                self._highlight_selected_drive_card()
        self._update_space_info()

    def _update_space_info(self):
        target = self.var_path.get().strip()
        if not target:
            self.lbl_space_info.config(text='⚠️ 请输入有效的安装路径', fg='#EF4444')
            return
        root = os.path.splitdrive(target)[0] + '\\'
        if os.path.exists(root):
            try:
                usage = shutil.disk_usage(root)
                free_gb = usage.free / (1024 ** 3)
                if free_gb >= 1.0:
                    txt = f"✓ 目标盘 ({root}) 空间充裕: 剩余 {free_gb:.1f} GB 可用 (程序所需空间约 120 MB)"
                    self.lbl_space_info.config(text=txt, fg='#16A34A')
                else:
                    txt = f"⚠️ 目标盘 ({root}) 剩余空间紧张: 仅剩 {free_gb:.2f} GB 可用"
                    self.lbl_space_info.config(text=txt, fg='#DC2626')
            except Exception:
                self.lbl_space_info.config(text='✓ 目标磁盘就绪 (程序所需空间约 120 MB)', fg='#64748B')
        else:
            self.lbl_space_info.config(text='⚠️ 目标磁盘驱动器不存在，请重新选择', fg='#EF4444')

    def _action_browse(self):
        cur_root = os.path.splitdrive(self.var_path.get())[0] + '\\'
        sel = filedialog.askdirectory(title='选择 ClashNodeX 安装目录', initialdir=cur_root)
        if sel:
            norm = os.path.normpath(sel)
            if not norm.lower().endswith('clashnodex'):
                norm = os.path.join(norm, 'ClashNodeX')
            self.var_path.set(norm)

    def _on_action_clicked(self):
        if self.current_step == 1:
            dest = self.var_path.get().strip()
            if not dest:
                messagebox.showwarning('提示', '请先输入或选择有效的安装目标路径！', parent=self)
                return
            self._start_install(dest)
        elif self.current_step == 3:
            dest = self.var_path.get().strip()
            exe_path = os.path.join(dest, 'ClashNodeX.exe')
            if self.var_launch_now.get() and os.path.exists(exe_path):
                try:
                    subprocess.Popen([exe_path], cwd=dest)
                except Exception as e:
                    messagebox.showerror('启动失败', f'无法启动程序: {e}', parent=self)
            self.destroy()

    def _start_install(self, dest_dir):
        self.current_step = 2
        self._clear_right_panel()
        self._update_step_nav_display(2)

        container = tk.Frame(self.right_panel, bg='#FFFFFF')
        container.pack(fill=tk.BOTH, expand=True, padx=self._scale(32), pady=self._scale(24))

        # Header
        title_box = tk.Frame(container, bg='#FFFFFF')
        title_box.pack(fill=tk.X, pady=(0, self._scale(16)))

        tk.Label(title_box, text='⚡ 正在部署 ClashNodeX 组件...',
                 font=self.font_heading, fg='#0F172A', bg='#FFFFFF').pack(anchor=tk.W)
        tk.Label(title_box, text='正在解压运行环境、跃迁引擎、智能路由测速内核及高像素狐狸素材',
                 font=self.font_small, fg='#64748B', bg='#FFFFFF').pack(anchor=tk.W, pady=(self._scale(4), 0))

        self.lbl_status = tk.Label(container, text='准备创建运行主目录...',
                                   font=self.font_body_bold, fg='#0284C7', bg='#FFFFFF')
        self.lbl_status.pack(anchor=tk.W, pady=(0, self._scale(8)))

        self.progress = ttk.Progressbar(container, style='Installer.Horizontal.TProgressbar',
                                       orient=tk.HORIZONTAL, mode='determinate', maximum=100)
        self.progress.pack(fill=tk.X, pady=(0, self._scale(16)))

        # Clean Log Terminal
        log_frame = tk.Frame(container, bg='#F8FAFC', bd=1, relief=tk.SOLID)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, self._scale(8)))

        self.txt_log = tk.Text(log_frame, font=self.font_log, bg='#F8FAFC', fg='#334155',
                               relief=tk.FLAT, bd=0, wrap=tk.WORD)
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=self._scale(12), pady=self._scale(10))

        self.btn_action.config(text='正在部署...', state=tk.DISABLED, bg='#94A3B8')
        self.btn_cancel.config(state=tk.DISABLED)

        t = threading.Thread(target=self._worker_install, args=(dest_dir,), daemon=True)
        t.start()

    def _append_log(self, text):
        self.txt_log.insert(tk.END, text + '\n')
        self.txt_log.see(tk.END)

    def _update_progress(self, val, msg):
        def _fn():
            self.progress['value'] = val
            self.lbl_status.config(text=msg)
        self.after(0, _fn)

    def _worker_install(self, dest_dir):
        try:
            time.sleep(0.3)
            self._update_progress(10, '正在创建安装目录...')
            self._append_log(f'创建目标路径: {dest_dir}')
            os.makedirs(dest_dir, exist_ok=True)

            self._update_progress(30, '正在解压并写入 ClashNodeX.exe 主程序...')
            src_exe = get_res_path('ClashNodeX.exe')
            if not os.path.exists(src_exe):
                fallback = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'ClashNodeX.exe')
                if os.path.exists(fallback):
                    src_exe = fallback

            target_exe = os.path.join(dest_dir, 'ClashNodeX.exe')
            self._append_log(f'写入主执行文件: {target_exe}')
            shutil.copy2(src_exe, target_exe)

            self._update_progress(50, '正在写入极客跃迁狐狸高清图标资源...')
            for ico_name in ['app_icon.ico', 'app_icon.png']:
                src_ico = get_res_path(ico_name)
                if os.path.exists(src_ico):
                    shutil.copy2(src_ico, os.path.join(dest_dir, ico_name))
                    self._append_log(f'写入资源: {ico_name}')

            self._update_progress(65, '正在生成产品使用指南与功能手册...')
            guide_path = os.path.join(dest_dir, '产品说明与使用指南.txt')
            with open(guide_path, 'w', encoding='utf-8') as f:
                f.write(
'===================================================================\n'
'⚡ Clash 节点跃迁 (ClashNodeX) v1.3.0 (Build 2026.09.09)\n'
'Clash Verge 专属极客管家 · 智能节点跃迁与多维精准测速切换\n'
'===================================================================\n\n'
'【核心功能亮点】\n'
'1. 节点智能跃迁与无感热替换:\n'
'   - 自动与 Clash Verge / Mihomo 核心实时同步。\n'
'   - 支持多模式延迟测速 (TCP 握手、HTTP Connect、真连接握手、DNS 校验)。\n'
'   - 毫秒级一键跃迁至最优极速节点，无感热替换。\n'
'2. 多维度精准测速引擎:\n'
'   - 真连接 HTTP 204 精准延迟测速与 TCP 延迟测试。\n'
'   - 支持多线程批量并发测速，迅速识别超时或失效节点。\n'
'   - 测速结果智能着色，梯级分明。\n'
'3. 全面代理分组排序管理:\n'
'   - 支持分组任意置顶、上移、下移，配置即时写入并同步到 Clash Verge。\n'
'4. 极致易用的交互与经典浅白皮肤:\n'
'   - 宽阔大气的卡片式设计，按键均带有微动反馈质感。\n'
'   - 独创极客跃迁狐狸圆形 LOGO，纯自主设计无版权侵权风险。\n'
'5. 全能导入与多协议支持:\n'
'   - 扫码识别二维码、剪贴板一键解析、直链一键抓取、节点批量排序与去重。\n\n'
'【开源与支持】\n'
' - 纯本地运行，不采集任何隐私数据，安全可靠。\n'
' - 点赞、分享与关注即是最好的赞助！\n'
'===================================================================\n'
                )
            self._append_log('已生成产品说明指南: 产品说明与使用指南.txt')

            self._update_progress(78, '正在生成快捷卸载工具...')
            uninst_bat = os.path.join(dest_dir, '卸载 ClashNodeX.bat')
            with open(uninst_bat, 'w', encoding='gbk', errors='ignore') as f:
                f.write('@echo off\nchcp 936 >nul\necho 正在卸载 ClashNodeX...\ntaskkill /F /IM ClashNodeX.exe >nul 2>&1\ntimeout /t 1 >nul\ndel /f /q "%USERPROFILE%\\Desktop\\Clash 节点跃迁 (ClashNodeX).lnk" >nul 2>&1\ndel /f /q "F:\\桌面\\Clash 节点跃迁 (ClashNodeX).lnk" >nul 2>&1\nrmdir /s /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Clash 节点跃迁" >nul 2>&1\ncd /d %~dp0..\nrmdir /s /q "' + dest_dir + '" >nul 2>&1\necho 卸载完成！\npause\n')
            self._append_log('已生成卸载模块: 卸载 ClashNodeX.bat')

            self._update_progress(88, '正在创建桌面与系统开始菜单快捷方式...')
            target_ico = os.path.join(dest_dir, 'app_icon.ico')

            if self.var_desktop_ico.get():
                self._create_desktop_shortcut(target_exe, dest_dir, target_ico)
                self._append_log('已成功在桌面创建极客狐狸快捷方式')

            if self.var_startmenu.get():
                self._create_startmenu_shortcut(target_exe, dest_dir, target_ico)
                self._append_log('已成功在开始菜单创建程序组')

            # Force Windows shell to refresh icon caches
            refresh_windows_icon_cache()

            self._update_progress(100, '部署全部完成！')
            self._append_log('所有模块与核心资源写入成功！')
            time.sleep(0.5)

            self.after(200, lambda: self._show_step_3(dest_dir))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror('安装错误', f'安装过程遇到异常:\n{e}', parent=self))
            self.after(0, lambda: self.btn_cancel.config(state=tk.NORMAL))

    def _create_desktop_shortcut(self, exe_path, work_dir, ico_path):
        desktops = get_all_desktop_paths()
        for d in desktops:
            if os.path.exists(d):
                lnk = os.path.join(d, 'Clash 节点跃迁 (ClashNodeX).lnk')
                try:
                    import win32com.client
                    wsh = win32com.client.Dispatch('WScript.Shell')
                    sc = wsh.CreateShortcut(lnk)
                    sc.TargetPath = exe_path
                    sc.WorkingDirectory = work_dir
                    sc.IconLocation = f'{ico_path},0'
                    sc.Description = 'Clash 节点跃迁 (ClashNodeX)'
                    sc.Save()
                    continue
                except Exception:
                    pass
                try:
                    vbs = os.path.join(work_dir, '_mklnk.vbs')
                    with open(vbs, 'w', encoding='utf-8-sig') as f:
                        f.write(f'Set s = CreateObject("WScript.Shell").CreateShortcut("{lnk}")\ns.TargetPath = "{exe_path}"\ns.WorkingDirectory = "{work_dir}"\ns.IconLocation = "{ico_path},0"\ns.Save\n')
                    subprocess.run(['cscript', '//nologo', vbs], creationflags=0x08000000)
                    if os.path.exists(vbs):
                        os.remove(vbs)
                except Exception:
                    pass

    def _create_startmenu_shortcut(self, exe_path, work_dir, ico_path):
        sm_dir = os.path.join(os.getenv('APPDATA', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Clash 节点跃迁')
        os.makedirs(sm_dir, exist_ok=True)
        lnk = os.path.join(sm_dir, 'Clash 节点跃迁 (ClashNodeX).lnk')
        try:
            import win32com.client
            wsh = win32com.client.Dispatch('WScript.Shell')
            sc = wsh.CreateShortcut(lnk)
            sc.TargetPath = exe_path
            sc.WorkingDirectory = work_dir
            sc.IconLocation = f'{ico_path},0'
            sc.Description = 'Clash 节点跃迁 (ClashNodeX)'
            sc.Save()
            return
        except Exception:
            pass
        try:
            vbs = os.path.join(work_dir, '_mksm.vbs')
            with open(vbs, 'w', encoding='utf-8-sig') as f:
                f.write(f'Set s = CreateObject("WScript.Shell").CreateShortcut("{lnk}")\ns.TargetPath = "{exe_path}"\ns.WorkingDirectory = "{work_dir}"\ns.IconLocation = "{ico_path},0"\ns.Save\n')
            subprocess.run(['cscript', '//nologo', vbs], creationflags=0x08000000)
            if os.path.exists(vbs):
                os.remove(vbs)
        except Exception:
            pass

    def _show_step_3(self, dest_dir):
        self._clear_right_panel()
        self.current_step = 3
        self._update_step_nav_display(3)

        container = tk.Frame(self.right_panel, bg='#FFFFFF')
        container.pack(fill=tk.BOTH, expand=True, padx=self._scale(32), pady=self._scale(24))

        # Hero Success Celebration
        hero_box = tk.Frame(container, bg='#FFFFFF')
        hero_box.pack(fill=tk.X, pady=(self._scale(6), self._scale(16)))

        tk.Label(hero_box, text='🎉 安装顺利完成！',
                 font=self.font_title, fg='#059669', bg='#FFFFFF').pack(anchor=tk.W)
        tk.Label(hero_box, text=f'Clash 节点跃迁 (ClashNodeX) v1.3.0 已就绪并部署至:\n{dest_dir}',
                 font=self.font_small, fg='#334155', bg='#FFFFFF', justify=tk.LEFT).pack(anchor=tk.W, pady=(self._scale(5), 0))

        # Path Card with Open Directory Button
        path_card = tk.Frame(container, bg='#F8FAFC', bd=1, relief=tk.SOLID)
        path_card.pack(fill=tk.X, pady=(0, self._scale(16)))

        inner_p = tk.Frame(path_card, bg='#F8FAFC')
        inner_p.pack(fill=tk.X, padx=self._scale(14), pady=self._scale(12))

        tk.Label(inner_p, text='📂 安装主目录:', font=self.font_small_bold,
                 fg='#0F172A', bg='#F8FAFC').pack(side=tk.LEFT)
        tk.Label(inner_p, text=dest_dir, font=self.font_code,
                 fg='#0284C7', bg='#F8FAFC').pack(side=tk.LEFT, padx=(self._scale(10), 0))

        btn_open = tk.Button(inner_p, text='打开目录', font=self.font_tiny,
                             bg='#E0F2FE', fg='#0369A1', activebackground='#BAE6FD',
                             relief=tk.FLAT, bd=0, padx=self._scale(12), pady=self._scale(4), cursor='hand2',
                             command=lambda: os.startfile(dest_dir))
        btn_open.pack(side=tk.RIGHT)

        # Quick Start Highlights Card
        card = tk.Frame(container, bg='#FFFFFF', bd=1, relief=tk.SOLID)
        card.pack(fill=tk.X, pady=(0, self._scale(16)))

        tk.Label(card, text='✨ 极客核心特性速览:', font=self.font_small_bold,
                 fg='#0F172A', bg='#FFFFFF').pack(anchor=tk.W, padx=self._scale(16), pady=(self._scale(12), self._scale(6)))

        tips = (
            '• 智能节点跃迁: 自动与 Clash Verge / Mihomo 实时连接，毫秒级热替换最优节点\n'
            '• 多模式精准测速: 支持真连接 HTTP 204、TCP 握手、Connect 等多维度测速\n'
            '• 智能一键优选: 智能识别最优低延迟节点，一键无感切换生效\n'
            '• 灵活分组管理: 支持分组任意上移、下移、置顶，配置即时写入并同步至客户端'
        )
        tk.Label(card, text=tips, font=self.font_small,
                 fg='#475569', bg='#FFFFFF', justify=tk.LEFT).pack(anchor=tk.W, padx=self._scale(16), pady=(0, self._scale(12)))

        # Launch Now Checkbox
        c_now = tk.Checkbutton(container, text='立即启动 Clash 节点跃迁 (ClashNodeX)',
                               variable=self.var_launch_now, font=self.font_body_bold,
                               bg='#FFFFFF', fg='#0284C7', activebackground='#FFFFFF', selectcolor='#FFFFFF')
        c_now.pack(anchor=tk.W, pady=(0, self._scale(8)))

        self.btn_action.config(text='完成并体验', state=tk.NORMAL, bg='#0284C7')
        self.btn_cancel.pack_forget()


if __name__ == '__main__':
    app = ClashNodeXInstaller()
    app.mainloop()
