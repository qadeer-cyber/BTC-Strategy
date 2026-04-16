import tkinter as tk
from tkinter import ttk


class AnalyticsScreen:
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
        
        self._create_summary_section()
        self._create_trader_stats_section()
        self._create_market_stats_section()
        
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
        
    def _create_summary_section(self):
        section = self._create_section(self.scrollable, 'Performance Summary')
        
        stats = self.db.get_performance_stats()
        
        grid = tk.Frame(section, bg='#2D2D3F')
        grid.pack(fill='x')
        
        metrics = [
            ('Total Trades', str(stats.get('total_trades', 0))),
            ('Closed Trades', str(stats.get('closed_trades', 0))),
            ('Failed Trades', str(stats.get('failed_trades', 0))),
            ('Skipped Trades', str(stats.get('skipped_trades', 0))),
            ('Total P&L', f"${stats.get('total_pnl', 0):.2f}"),
            ('Total Wins', f"${stats.get('total_wins', 0):.2f}"),
            ('Total Losses', f"${stats.get('total_losses', 0):.2f}"),
            ('Today Trades', str(stats.get('today_trades', 0))),
        ]
        
        for i, (label, value) in enumerate(metrics):
            row = i // 4
            col = i % 4
            
            cell = tk.Frame(grid, bg='#2D2D3F')
            cell.grid(row=row, column=col, padx=10, pady=10, sticky='ew')
            
            tk.Label(
                cell,
                text=label,
                font=('Helvetica', 10),
                bg='#2D2D3F',
                fg='#A0A0B0'
            ).pack()
            
            tk.Label(
                cell,
                text=value,
                font=('Helvetica', 16, 'bold'),
                bg='#2D2D3F',
                fg='#00D4AA'
            ).pack()
            
        grid.grid_columnconfigure((0,1,2,3), weight=1)
        
    def _create_trader_stats_section(self):
        section = self._create_section(self.scrollable, 'Per-Trader Statistics')
        
        tree_frame = tk.Frame(section, bg='#2D2D3F')
        tree_frame.pack(fill='both', expand=True)
        
        columns = ('Wallet', 'Trades', 'Closed', 'Wins', 'Losses', 'Win Rate', 'P&L', 'Volume')
        
        self.trader_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.trader_tree.heading(col, text=col)
            if col == 'Wallet':
                self.trader_tree.column(col, width=150)
            else:
                self.trader_tree.column(col, width=80)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.trader_tree.yview)
        self.trader_tree.configure(yscrollcommand=scrollbar.set)
        
        self.trader_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
    def _create_market_stats_section(self):
        section = self._create_section(self.scrollable, 'Per-Market Statistics')
        
        tree_frame = tk.Frame(section, bg='#2D2D3F')
        tree_frame.pack(fill='both', expand=True)
        
        columns = ('Market', 'Trades', 'Wins', 'Losses', 'Win Rate', 'P&L', 'Volume')
        
        self.market_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.market_tree.heading(col, text=col)
            if col == 'Market':
                self.market_tree.column(col, width=200)
            else:
                self.market_tree.column(col, width=80)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.market_tree.yview)
        self.market_tree.configure(yscrollcommand=scrollbar.set)
        
        self.market_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
    def _refresh_data(self):
        if self.bot and hasattr(self.bot, 'get_performance'):
            perf = self.bot.get_performance()
            
            trader_stats = perf.get('per_trader', [])
            self._update_trader_tree(trader_stats)
            
            market_stats = perf.get('per_market', [])
            self._update_market_tree(market_stats)
            
    def _update_trader_tree(self, traders):
        for item in self.trader_tree.get_children():
            self.trader_tree.delete(item)
        
        for trader in traders[:20]:
            wallet = (trader.get('wallet', '') or '')[:12] + '...'
            trades = str(trader.get('total_trades', 0))
            closed = str(trader.get('closed_trades', 0))
            wins = str(trader.get('wins', 0))
            losses = str(trader.get('losses', 0))
            win_rate = f"{trader.get('win_rate', 0):.1f}%"
            pnl = f"${trader.get('pnl', 0):.2f}"
            volume = f"${trader.get('total_volume', 0):.2f}"
            
            self.trader_tree.insert('', 'end', values=(wallet, trades, closed, wins, losses, win_rate, pnl, volume))
            
    def _update_market_tree(self, markets):
        for item in self.market_tree.get_children():
            self.market_tree.delete(item)
        
        for market in markets[:20]:
            name = (market.get('market', '') or '')[:30]
            trades = str(market.get('trades', 0))
            wins = str(market.get('wins', 0))
            losses = str(market.get('losses', 0))
            win_rate = f"{market.get('win_rate', 0):.1f}%"
            pnl = f"${market.get('pnl', 0):.2f}"
            volume = f"${market.get('volume', 0):.2f}"
            
            self.market_tree.insert('', 'end', values=(name, trades, wins, losses, win_rate, pnl, volume))
            
    def show(self):
        self.frame.grid()
        self._refresh_data()
        
    def hide(self):
        self.frame.grid_remove()