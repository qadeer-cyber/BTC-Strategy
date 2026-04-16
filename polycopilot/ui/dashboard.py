import tkinter as tk
from tkinter import ttk
import threading


class Dashboard:
    def __init__(self, parent, db, logger, bot):
        self.db = db
        self.logger = logger
        self.bot = bot
        
        self.frame = tk.Frame(parent, bg='#1E1E2E')
        
        self._setup_ui()
        
        self._refresh_data()
        
    def _setup_ui(self):
        self.frame.grid_rowconfigure(0, weight=0)
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        self._create_status_bar()
        self._create_cards_area()
        self._create_tables_area()
        
    def _create_status_bar(self):
        status_bar = tk.Frame(self.frame, bg='#2D2D3F', height=40)
        status_bar.grid(row=0, column=0, sticky='ew', padx=20, pady=(10, 5))
        status_bar.grid_propagate(False)
        
        self.refresh_btn = tk.Button(
            status_bar,
            text='⟳ Refresh',
            font=('Helvetica', 10),
            bg='#3D3D4F',
            fg='#FFFFFF',
            bd=0,
            pady=5,
            padx=15,
            command=self._refresh_data
        )
        self.refresh_btn.pack(side='right')
        
        self.last_sync_label = tk.Label(
            status_bar,
            text='Last sync: --',
            font=('Helvetica', 10),
            bg='#2D2D3F',
            fg='#A0A0B0'
        )
        self.last_sync_label.pack(side='right', padx=20)
        
    def _create_cards_area(self):
        cards_frame = tk.Frame(self.frame, bg='#1E1E2E')
        cards_frame.grid(row=1, column=0, sticky='nsew', padx=20, pady=10)
        
        cards_frame.grid_columnconfigure((0,1,2,3), weight=1)
        
        self.status_cards = {}
        
        status_data = [
            ('Tracked Traders', '0', '#00D4AA'),
            ('Today Copies', '0', '#4ADE80'),
            ('Open Positions', '0', '#FBBF24'),
            ('Closed Today', '0', '#A0A0B0'),
        ]
        
        for i, (title, default, color) in enumerate(status_data):
            card = self._create_card(cards_frame, title, default, color)
            card.grid(row=0, column=i, padx=5, pady=5, sticky='ew')
            self.status_cards[title] = card
        
        perf_data = [
            ('Total P&L', '$0.00', '#4ADE80'),
            ('Today P&L', '$0.00', '#00D4AA'),
            ('Win Rate', '0%', '#A0A0B0'),
            ('W/L', '0/0', '#FBBF24'),
        ]
        
        for i, (title, default, color) in enumerate(perf_data):
            card = self._create_card(cards_frame, title, default, color)
            card.grid(row=1, column=i, padx=5, pady=5, sticky='ew')
            self.status_cards[title] = card
        
        risk_data = [
            ('Failed Trades', '0', '#F87171'),
            ('Skipped Trades', '0', '#FBBF24'),
            ('Current Exposure', '$0.00', '#FBBF24'),
            ('Max Exposure', '$0.00', '#A0A0B0'),
        ]
        
        for i, (title, default, color) in enumerate(risk_data):
            card = self._create_card(cards_frame, title, default, color)
            card.grid(row=2, column=i, padx=5, pady=5, sticky='ew')
            self.status_cards[title] = card
            
    def _create_card(self, parent, title, default_value, color):
        card_frame = tk.Frame(parent, bg='#2D2D3F', padx=15, pady=15)
        
        title_label = tk.Label(
            card_frame,
            text=title,
            font=('Helvetica', 10),
            bg='#2D2D3F',
            fg='#A0A0B0'
        )
        title_label.pack(anchor='w')
        
        value_label = tk.Label(
            card_frame,
            text=default_value,
            font=('Helvetica', 20, 'bold'),
            bg='#2D2D3F',
            fg=color
        )
        value_label.pack(anchor='w', pady=(5, 0))
        
        card_frame.value_label = value_label
        return card_frame
        
    def _create_tables_area(self):
        tables_frame = tk.Frame(self.frame, bg='#1E1E2E')
        tables_frame.grid(row=3, column=0, sticky='nsew', padx=20, pady=10)
        
        tables_frame.grid_rowconfigure(0, weight=1)
        tables_frame.grid_columnconfigure(0, weight=1)
        tables_frame.grid_columnconfigure(1, weight=1)
        
        left_frame = tk.Frame(tables_frame, bg='#2D2D3F')
        left_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        
        tk.Label(
            left_frame,
            text='Recent Source Trades',
            font=('Helvetica', 12, 'bold'),
            bg='#2D2D3F',
            fg='#FFFFFF',
            pady=10
        ).pack()
        
        self.source_trades_tree = self._create_tree(
            left_frame,
            ['Trader', 'Market', 'Side', 'Amount', 'Time']
        )
        self.source_trades_tree.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        right_frame = tk.Frame(tables_frame, bg='#2D2D3F')
        right_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 0))
        
        tk.Label(
            right_frame,
            text='Recent Copied Trades',
            font=('Helvetica', 12, 'bold'),
            bg='#2D2D3F',
            fg='#FFFFFF',
            pady=10
        ).pack()
        
        self.copied_trades_tree = self._create_tree(
            right_frame,
            ['Market', 'Side', 'Amount', 'Status', 'P&L', 'Time']
        )
        self.copied_trades_tree.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
    def _create_tree(self, parent, columns):
        tree = ttk.Treeview(parent, columns=columns, show='headings', height=8)
        
        tree.heading('#0', text='')
        tree.column('#0', width=0, stretch=False)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        tree.tag_configure('even', background='#2D2D3F')
        tree.tag_configure('odd', background='#333344')
        
        return tree
        
    def _refresh_data(self):
        def fetch():
            try:
                perf = self.bot.get_performance() if hasattr(self.bot, 'get_performance') else {}
                
                status = self.bot.get_status()
                
                traders = self.db.get_followed_traders()
                today_trades = self.db.get_today_copied_trades()
                open_trades = self.db.get_open_trades()
                
                self.frame.after(0, lambda: self._update_cards({
                    'Tracked Traders': str(len(traders)),
                    'Today Copies': str(len(today_trades)),
                    'Open Positions': str(len(open_trades)),
                    'Closed Today': str(len([t for t in today_trades if t.get('status') == 'closed'])),
                    'Total P&L': f"${perf.get('total_pnl', 0):.2f}",
                    'Today P&L': f"${perf.get('today_pnl', 0):.2f}",
                    'Win Rate': f"{perf.get('win_rate', 0):.1f}%",
                    'W/L': f"{perf.get('winners', 0)}/{perf.get('losers', 0)}",
                    'Failed Trades': str(perf.get('failed_trades', 0)),
                    'Skipped Trades': str(perf.get('skipped_trades', 0)),
                    'Current Exposure': f"${perf.get('current_exposure', 0):.2f}",
                    'Max Exposure': f"${status.get('max_exposure', 500):.2f}",
                }))
                
                signals = self.db.get_unseen_signals()[:10]
                self.frame.after(0, lambda: self._update_source_trades(signals))
                
                recent_copies = self.db.get_all_copied_trades(limit=10)
                self.frame.after(0, lambda: self._update_copied_trades(recent_copies))
                
                import datetime
                self.frame.after(0, lambda: self.last_sync_label.configure(
                    text=f"Last sync: {datetime.datetime.now().strftime('%H:%M:%S')}"
                ))
                
            except Exception as e:
                self.logger.error(f'Error refreshing dashboard: {e}', 'dashboard')
        
        threading.Thread(target=fetch, daemon=True).start()
        
    def _update_cards(self, values):
        for title, value in values.items():
            if title in self.status_cards:
                self.status_cards[title].value_label.configure(text=value)
                
    def _update_source_trades(self, signals):
        for item in self.source_trades_tree.get_children():
            self.source_trades_tree.delete(item)
        
        for sig in signals:
            trader = sig.get('trader_wallet', '')[:8] + '...'
            market = sig.get('market_question', '')[:20]
            side = sig.get('side', '').upper()
            amount = f"${sig.get('amount', 0):.2f}"
            time = sig.get('timestamp', '')[-8:]
            
            self.source_trades_tree.insert('', 0, values=(trader, market, side, amount, time))
            
    def _update_copied_trades(self, trades):
        for item in self.copied_trades_tree.get_children():
            self.copied_trades_tree.delete(item)
        
        for trade in trades:
            market = trade.get('market_question', '')[:20]
            side = trade.get('side', '').upper()
            amount = f"${trade.get('amount', 0):.2f}"
            status = trade.get('status', 'unknown').upper()
            pnl = f"${trade.get('pnl', 0):.2f}" if trade.get('pnl') else '--'
            time = trade.get('copied_at', '')[-8:]
            
            self.copied_trades_tree.insert('', 0, values=(market, side, amount, status, pnl, time))
        
    def show(self):
        self.frame.grid()
        self._refresh_data()
        
    def hide(self):
        self.frame.grid_remove()