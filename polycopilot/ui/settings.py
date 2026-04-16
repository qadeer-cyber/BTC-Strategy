import tkinter as tk
from tkinter import ttk
import threading


class SettingsScreen:
    def __init__(self, parent, db, logger, bot):
        self.db = db
        self.logger = logger
        self.bot = bot
        
        self.frame = tk.Frame(parent, bg='#1E1E2E')
        self._setup_ui()
        
    def _setup_ui(self):
        canvas = tk.Canvas(self.frame, bg='#1E1E2E')
        scrollbar = ttk.Scrollbar(self.frame, orient='vertical', command=canvas.yview)
        self.scrollable = tk.Frame(canvas, bg='#1E1E2E')
        
        self.scrollable.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )
        
        canvas.create_window((0, 0), window=self.scrollable, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self._create_bot_settings()
        self._create_copy_settings()
        self._create_risk_settings()
        self._create_trader_filters()
        self._create_connection_settings()
        
    def _create_section(self, parent, title):
        section = tk.LabelFrame(
            parent,
            text=title,
            font=('Helvetica', 12, 'bold'),
            bg='#2D2D3F',
            fg='#FFFFFF',
            padx=10,
            pady=10
        )
        section.pack(fill='x', padx=20, pady=10)
        return section
        
    def _create_bot_settings(self):
        section = self._create_section(self.scrollable, 'Bot Settings')
        
        row = tk.Frame(section, bg='#2D2D3F')
        row.pack(fill='x', pady=5)
        
        tk.Label(row, text='Polling Interval (sec):', bg='#2D2D3F', fg='#A0A0B0').pack(side='left')
        
        self.poll_interval_var = tk.StringVar(value='30')
        tk.Entry(row, textvariable=self.poll_interval_var, width=10, bg='#3D3D4F', fg='#FFFFFF').pack(side='left', padx=10)
        
        row2 = tk.Frame(section, bg='#2D2D3F')
        row2.pack(fill='x', pady=5)
        
        tk.Label(row2, text='Mode:', bg='#2D2D3F', fg='#A0A0B0').pack(side='left')
        
        self.mode_var = tk.StringVar(value='dry_run')
        
        modes = [
            ('dry_run', 'Dry-Run (No Execution)'),
            ('paper', 'Paper Trading'),
            ('live', 'Live Trading')
        ]
        
        for val, text in modes:
            tk.Radiobutton(
                row2, text=text, variable=self.mode_var, value=val,
                bg='#2D2D3F', fg='#FFFFFF', selectcolor='#3D3D4F'
            ).pack(side='left', padx=10)
            
    def _create_copy_settings(self):
        section = self._create_section(self.scrollable, 'Copy Settings')
        
        row = tk.Frame(section, bg='#2D2D3F')
        row.pack(fill='x', pady=5)
        
        tk.Label(row, text='Copy Mode:', bg='#2D2D3F', fg='#A0A0B0').pack(side='left')
        
        self.copy_mode_var = tk.StringVar(value='fixed')
        
        for mode in ['fixed', 'proportional', 'weighted']:
            tk.Radiobutton(
                row, text=mode.capitalize(), variable=self.copy_mode_var, value=mode,
                bg='#2D2D3F', fg='#FFFFFF', selectcolor='#3D3D4F'
            ).pack(side='left', padx=10)
        
        row2 = tk.Frame(section, bg='#2D2D3F')
        row2.pack(fill='x', pady=5)
        
        tk.Label(row2, text='Fixed Amount ($):', bg='#2D2D3F', fg='#A0A0B0').pack(side='left')
        
        self.fixed_amount_var = tk.StringVar(value='10.0')
        tk.Entry(row2, textvariable=self.fixed_amount_var, width=10, bg='#3D3D4F', fg='#FFFFFF').pack(side='left', padx=10)
        
        row3 = tk.Frame(section, bg='#2D2D3F')
        row3.pack(fill='x', pady=5)
        
        tk.Label(row3, text='Sell Mode:', bg='#2D2D3F', fg='#A0A0B0').pack(side='left')
        
        self.sell_mode_var = tk.StringVar(value='all')
        
        for mode in ['all', 'proportional', 'fixed', 'ignore']:
            tk.Radiobutton(
                row3, text=mode.capitalize(), variable=self.sell_mode_var, value=mode,
                bg='#2D2D3F', fg='#FFFFFF', selectcolor='#3D3D4F'
            ).pack(side='left', padx=10)
            
    def _create_risk_settings(self):
        section = self._create_section(self.scrollable, 'Risk Controls')
        
        row = tk.Frame(section, bg='#2D2D3F')
        row.pack(fill='x', pady=5)
        
        tk.Label(row, text='Max Daily Loss ($):', bg='#2D2D3F', fg='#A0A0B0').pack(side='left')
        self.max_daily_loss_var = tk.StringVar(value='100')
        tk.Entry(row, textvariable=self.max_daily_loss_var, width=10, bg='#3D3D4F', fg='#FFFFFF').pack(side='left', padx=10)
        
        row2 = tk.Frame(section, bg='#2D2D3F')
        row2.pack(fill='x', pady=5)
        
        tk.Label(row2, text='Max Exposure ($):', bg='#2D2D3F', fg='#A0A0B0').pack(side='left')
        self.max_exposure_var = tk.StringVar(value='500')
        tk.Entry(row2, textvariable=self.max_exposure_var, width=10, bg='#3D3D4F', fg='#FFFFFF').pack(side='left', padx=10)
        
        row3 = tk.Frame(section, bg='#2D2D3F')
        row3.pack(fill='x', pady=5)
        
        tk.Label(row3, text='Max Concurrent:', bg='#2D2D3F', fg='#A0A0B0').pack(side='left')
        self.max_concurrent_var = tk.StringVar(value='5')
        tk.Entry(row3, textvariable=self.max_concurrent_var, width=10, bg='#3D3D4F', fg='#FFFFFF').pack(side='left', padx=10)
        
        row4 = tk.Frame(section, bg='#2D2D3F')
        row4.pack(fill='x', pady=5)
        
        tk.Label(row4, text='Stale Trade Threshold (min):', bg='#2D2D3F', fg='#A0A0B0').pack(side='left')
        self.stale_threshold_var = tk.StringVar(value='60')
        tk.Entry(row4, textvariable=self.stale_threshold_var, width=10, bg='#3D3D4F', fg='#FFFFFF').pack(side='left', padx=10)
        
        row5 = tk.Frame(section, bg='#2D2D3F')
        row5.pack(fill='x', pady=5)
        
        tk.Checkbutton(
            row5, text='Copy Buys Only', variable=tk.BooleanVar(value=True),
            bg='#2D2D3F', fg='#FFFFFF', selectcolor='#3D3D4F'
        ).pack(side='left')
        
    def _create_trader_filters(self):
        section = self._create_section(self.scrollable, 'Trader Filters')
        
        row = tk.Frame(section, bg='#2D2D3F')
        row.pack(fill='x', pady=5)
        
        tk.Label(row, text='Min Volume ($):', bg='#2D2D3F', fg='#A0A0B0').pack(side='left')
        self.min_volume_var = tk.StringVar(value='0')
        tk.Entry(row, textvariable=self.min_volume_var, width=10, bg='#3D3D4F', fg='#FFFFFF').pack(side='left', padx=10)
        
        row2 = tk.Frame(section, bg='#2D2D3F')
        row2.pack(fill='x', pady=5)
        
        tk.Label(row2, text='Min P&L ($):', bg='#2D2D3F', fg='#A0A0B0').pack(side='left')
        self.min_pnl_var = tk.StringVar(value='0')
        tk.Entry(row2, textvariable=self.min_pnl_var, width=10, bg='#3D3D4F', fg='#FFFFFF').pack(side='left', padx=10)
        
        row3 = tk.Frame(section, bg='#2D2D3F')
        row3.pack(fill='x', pady=5)
        
        tk.Label(row3, text='Min Trade Count:', bg='#2D2D3F', fg='#A0A0B0').pack(side='left')
        self.min_trades_var = tk.StringVar(value='0')
        tk.Entry(row3, textvariable=self.min_trades_var, width=10, bg='#3D3D4F', fg='#FFFFFF').pack(side='left', padx=10)
        
        row4 = tk.Frame(section, bg='#2D2D3F')
        row4.pack(fill='x', pady=5)
        
        tk.Label(row4, text='Max Inactivity (days):', bg='#2D2D3F', fg='#A0A0B0').pack(side='left')
        self.max_inactivity_var = tk.StringVar(value='30')
        tk.Entry(row4, textvariable=self.max_inactivity_var, width=10, bg='#3D3D4F', fg='#FFFFFF').pack(side='left', padx=10)
        
    def _create_connection_settings(self):
        section = self._create_section(self.scrollable, 'Connection Settings')
        
        row = tk.Frame(section, bg='#2D2D3F')
        row.pack(fill='x', pady=5)
        
        tk.Label(row, text='Bullpen CLI Path:', bg='#2D2D3F', fg='#A0A0B0').pack(side='left')
        self.bullpen_path_var = tk.StringVar(value='/usr/local/bin/bullpen')
        tk.Entry(row, textvariable=self.bullpen_path_var, width=30, bg='#3D3D4F', fg='#FFFFFF').pack(side='left', padx=10)
        
        row2 = tk.Frame(section, bg='#2D2D3F')
        row2.pack(fill='x', pady=5)
        
        tk.Label(row2, text='Wallet Address:', bg='#2D2D3F', fg='#A0A0B0').pack(side='left')
        self.wallet_var = tk.StringVar(value='')
        tk.Entry(row2, textvariable=self.wallet_var, width=40, bg='#3D3D4F', fg='#FFFFFF').pack(side='left', padx=10)
        
        save_btn = tk.Button(
            section,
            text='Save Settings',
            font=('Helvetica', 11, 'bold'),
            bg='#00D4AA',
            fg='#000000',
            bd=0,
            pady=10,
            padx=20,
            command=self._save_settings
        )
        save_btn.pack(pady=15)
        
    def _save_settings(self):
        try:
            config = {
                'poll_interval': int(self.poll_interval_var.get()),
                'is_dry_run': self.mode_var.get() == 'dry_run',
                'is_paper': self.mode_var.get() == 'paper',
                'copy_mode': self.copy_mode_var.get(),
                'fixed_amount': float(self.fixed_amount_var.get()),
                'sell_mode': self.sell_mode_var.get(),
                'max_daily_loss': float(self.max_daily_loss_var.get()),
                'max_exposure': float(self.max_exposure_var.get()),
                'max_concurrent': int(self.max_concurrent_var.get()),
                'stale_threshold_minutes': int(self.stale_threshold_var.get()),
                'trader_filters': {
                    'min_volume': float(self.min_volume_var.get()),
                    'min_pnl': float(self.min_pnl_var.get()),
                    'min_trades': int(self.min_trades_var.get()),
                    'max_inactivity_days': int(self.max_inactivity_var.get())
                },
                'bullpen_path': self.bullpen_path_var.get(),
                'wallet_address': self.wallet_var.get()
            }
            
            for key, value in config.items():
                self.db.set_setting(key, value)
            
            if self.bot:
                self.bot.update_config(config)
                self.bot.set_mode(config['is_dry_run'], config['is_paper'])
            
            self.logger.info('Settings saved', 'settings')
            
        except Exception as e:
            self.logger.error(f'Failed to save settings: {e}', 'settings')
            
    def show(self):
        self.frame.grid()
        
    def hide(self):
        self.frame.grid_remove()