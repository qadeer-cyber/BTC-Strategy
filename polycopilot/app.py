import tkinter as tk
from tkinter import ttk
from .dashboard import Dashboard
from .settings import SettingsScreen
from .traders import TradersScreen
from .trades import TradesScreen
from .logs import LogsScreen
from .analytics import AnalyticsScreen


class App:
    def __init__(self, db, logger, bot):
        self.db = db
        self.logger = logger
        self.bot = bot
        
        self.root = tk.Tk()
        self.root.title('PolyCopilot - PolyMarket Copy Trading')
        self.root.geometry('1200x800')
        self.root.minsize(1000, 700)
        
        self._setup_styles()
        self._setup_ui()
        
        self._update_status()
        
    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.colors = {
            'bg': '#1E1E2E',
            'surface': '#2D2D3F',
            'surface_light': '#3D3D4F',
            'primary': '#00D4AA',
            'primary_hover': '#00E5BB',
            'success': '#4ADE80',
            'error': '#F87171',
            'warning': '#FBBF24',
            'text': '#FFFFFF',
            'text_secondary': '#A0A0B0',
            'border': '#404050'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        self.style.configure('TFrame', background=self.colors['bg'])
        self.style.configure('Card.TFrame', background=self.colors['surface'])
        self.style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['text'])
        self.style.configure('Card.TLabel', background=self.colors['surface'], foreground=self.colors['text'])
        self.style.configure('TButton', background=self.colors['surface'], foreground=self.colors['text'])
        self.style.configure('Primary.TButton', background=self.colors['primary'], foreground='#000000')
        self.style.configure('Danger.TButton', background=self.colors['error'], foreground='#000000')
        
    def _setup_ui(self):
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=0)
        self.root.grid_columnconfigure(1, weight=1)
        
        self._create_header()
        self._create_sidebar()
        self._create_content_area()
        
    def _create_header(self):
        header_frame = tk.Frame(self.root, bg=self.colors['surface'], height=60)
        header_frame.grid(row=0, column=0, columnspan=2, sticky='ew')
        header_frame.grid_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text='PolyCopilot',
            font=('Helvetica', 18, 'bold'),
            bg=self.colors['surface'],
            fg=self.colors['primary']
        )
        title_label.pack(side='left', padx=20, pady=10)
        
        self.status_frame = tk.Frame(header_frame, bg=self.colors['surface'])
        self.status_frame.pack(side='right', padx=20)
        
        self.bot_status_label = tk.Label(
            self.status_frame,
            text='Bot: STOPPED',
            font=('Helvetica', 12),
            bg=self.colors['surface'],
            fg=self.colors['text_secondary']
        )
        self.bot_status_label.pack(side='left', padx=10)
        
        self.connection_label = tk.Label(
            self.status_frame,
            text='Net: Checking...',
            font=('Helvetica', 12),
            bg=self.colors['surface'],
            fg=self.colors['text_secondary']
        )
        self.connection_label.pack(side='left', padx=10)
        
        mode = 'Dry-Run' if self.bot.is_dry_run else ('Paper' if self.bot.is_paper else 'Live')
        self.mode_label = tk.Label(
            self.status_frame,
            text=f'Mode: {mode}',
            font=('Helvetica', 12),
            bg=self.colors['surface'],
            fg=self.colors['warning']
        )
        self.mode_label.pack(side='left', padx=10)
        
    def _create_sidebar(self):
        sidebar = tk.Frame(self.root, bg=self.colors['surface'], width=200)
        sidebar.grid(row=1, column=0, sticky='ns')
        sidebar.grid_propagate(False)
        
        nav_buttons = [
            ('Dashboard', 'dashboard'),
            ('Traders', 'traders'),
            ('Trades', 'trades'),
            ('Analytics', 'analytics'),
            ('Logs', 'logs'),
            ('Settings', 'settings'),
        ]
        
        self.nav_buttons = {}
        
        for text, key in nav_buttons:
            btn = tk.Button(
                sidebar,
                text=text,
                font=('Helvetica', 12),
                bg=self.colors['surface'],
                fg=self.colors['text'],
                activebackground=self.colors['surface_light'],
                activeforeground=self.colors['text'],
                bd=0,
                pady=12,
                anchor='w',
                padx=20,
                command=lambda k=key: self._show_screen(k)
            )
            btn.pack(fill='x', pady=1)
            self.nav_buttons[key] = btn
        
        self._highlight_nav('dashboard')
        
        tk.Frame(sidebar, bg=self.colors['border'], height=1).pack(fill='x', padx=10, pady=20)
        
        self._create_bot_controls(sidebar)
        
    def _create_bot_controls(self, parent):
        controls_frame = tk.Frame(parent, bg=self.colors['surface'])
        controls_frame.pack(side='bottom', fill='x', padx=10, pady=10)
        
        self.start_btn = tk.Button(
            controls_frame,
            text='▶ Start',
            font=('Helvetica', 11),
            bg=self.colors['success'],
            fg='#000000',
            bd=0,
            pady=8,
            command=self._start_bot
        )
        self.start_btn.pack(fill='x', pady=2)
        
        self.pause_btn = tk.Button(
            controls_frame,
            text='⏸ Pause',
            font=('Helvetica', 11),
            bg=self.colors['warning'],
            fg='#000000',
            bd=0,
            pady=8,
            command=self._pause_bot,
            state='disabled'
        )
        self.pause_btn.pack(fill='x', pady=2)
        
        self.stop_btn = tk.Button(
            controls_frame,
            text='■ Stop',
            font=('Helvetica', 11),
            bg=self.colors['error'],
            fg='#000000',
            bd=0,
            pady=8,
            command=self._stop_bot,
            state='disabled'
        )
        self.stop_btn.pack(fill='x', pady=2)
        
    def _create_content_area(self):
        self.content_frame = tk.Frame(self.root, bg=self.colors['bg'])
        self.content_frame.grid(row=1, column=1, sticky='nsew')
        self.content_frame.grid_propagate(False)
        
        self.screens = {}
        
        self.screens['dashboard'] = Dashboard(self.content_frame, self.db, self.logger, self.bot)
        self.screens['traders'] = TradersScreen(self.content_frame, self.db, self.logger, self.bot)
        self.screens['trades'] = TradesScreen(self.content_frame, self.db, self.logger, self.bot)
        self.screens['analytics'] = AnalyticsScreen(self.content_frame, self.db, self.logger, self.bot)
        self.screens['logs'] = LogsScreen(self.content_frame, self.db, self.logger)
        self.screens['settings'] = SettingsScreen(self.content_frame, self.db, self.logger, self.bot)
        
        self._show_screen('dashboard')
        
    def _show_screen(self, screen_key):
        for key, screen in self.screens.items():
            if key == screen_key:
                screen.show()
                self.nav_buttons[key].configure(bg=self.colors['surface_light'])
            else:
                screen.hide()
                self.nav_buttons[key].configure(bg=self.colors['surface'])
        
        self._highlight_nav(screen_key)
        
    def _highlight_nav(self, active_key):
        for key, btn in self.nav_buttons.items():
            if key == active_key:
                btn.configure(bg=self.colors['primary'], fg='#000000')
            else:
                btn.configure(bg=self.colors['surface'], fg=self.colors['text'])
        
    def _start_bot(self):
        if self.bot.start():
            self.start_btn.configure(state='disabled', bg=self.colors['surface'])
            self.pause_btn.configure(state='normal')
            self.stop_btn.configure(state='normal')
            self._update_status()
            
    def _pause_bot(self):
        if self.bot.is_paused:
            self.bot.resume()
            self.pause_btn.configure(text='⏸ Pause', bg=self.colors['warning'])
        else:
            self.bot.pause()
            self.pause_btn.configure(text='▶ Resume', bg=self.colors['success'])
            
    def _stop_bot(self):
        self.bot.stop()
        self.start_btn.configure(state='normal', bg=self.colors['success'])
        self.pause_btn.configure(state='disabled', text='⏸ Pause', bg=self.colors['warning'])
        self.stop_btn.configure(state='disabled', bg=self.colors['surface'])
        self._update_status()
        
    def _update_status(self):
        status = self.bot.get_status()
        
        state_colors = {
            'running': self.colors['success'],
            'paused': self.colors['warning'],
            'stopped': self.colors['text_secondary']
        }
        
        state = status.get('state', 'stopped')
        color = state_colors.get(state, self.colors['text_secondary'])
        
        self.bot_status_label.configure(
            text=f'Bot: {state.upper()}',
            fg=color
        )
        
        mode = 'Dry-Run' if status.get('is_dry_run') else ('Paper' if status.get('is_paper') else 'Live')
        self.mode_label.configure(
            text=f'Mode: {mode}',
            fg=self.colors['warning'] if status.get('is_dry_run') else self.colors['primary']
        )
        
        self.root.after(1000, self._update_status)
        
    def run(self):
        self.root.mainloop()