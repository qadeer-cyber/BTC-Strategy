import tkinter as tk
from tkinter import ttk


class TradesScreen:
    def __init__(self, parent, db, logger, bot):
        self.db = db
        self.logger = logger
        self.bot = bot
        
        self.frame = tk.Frame(parent, bg='#1E1E2E')
        self._setup_ui()
        
    def _setup_ui(self):
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        toolbar = tk.Frame(self.frame, bg='#2D2D3F', height=50)
        toolbar.grid(row=0, column=0, sticky='ew')
        toolbar.grid_propagate(False)
        
        tk.Label(
            toolbar,
            text='Trade History',
            font=('Helvetica', 14, 'bold'),
            bg='#2D2D3F',
            fg='#FFFFFF'
        ).pack(side='left', padx=20)
        
        self.refresh_btn = tk.Button(
            toolbar,
            text='⟳ Refresh',
            font=('Helvetica', 10),
            bg='#3D3D4F',
            fg='#FFFFFF',
            bd=0,
            pady=8,
            padx=15,
            command=self._refresh_trades
        )
        self.refresh_btn.pack(side='right', padx=10, pady=10)
        
        content = tk.Frame(self.frame, bg='#1E1E2E')
        content.grid(row=1, column=0, sticky='nsew', padx=20, pady=10)
        
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)
        
        columns = ('Trader', 'Market', 'Side', 'Amount', 'Price', 'Status', 'P&L', 'Time')
        
        self.tree = ttk.Treeview(content, columns=columns, show='headings')
        
        for col in columns:
            self.tree.heading(col, text=col)
            if col in ['Trader', 'Market']:
                self.tree.column(col, width=180)
            else:
                self.tree.column(col, width=90)
        
        scrollbar = ttk.Scrollbar(content, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        self.tree.tag_configure('open', foreground='#FBBF24')
        self.tree.tag_configure('closed', foreground='#4ADE80')
        self.tree.tag_configure('failed', foreground='#F87171')
        self.tree.tag_configure('skipped', foreground='#A0A0B0')
        
    def _refresh_trades(self):
        trades = self.db.get_all_copied_trades(limit=200)
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for trade in trades:
            trader = (trade.get('trader_wallet', '') or '')[:10] + '...'
            market = (trade.get('market_question', '') or '')[:25]
            side = (trade.get('side', '') or '').upper()
            amount = f"${trade.get('amount', 0):.2f}"
            price = f"${trade.get('price', 0):.2f}"
            status = (trade.get('status', 'unknown') or 'unknown').upper()
            
            pnl = trade.get('pnl')
            pnl_str = f"${pnl:.2f}" if pnl is not None else '--'
            
            time = (trade.get('copied_at', '') or '')[-8:] or '--'
            
            tags = [status.lower()]
            
            self.tree.insert('', 'end', values=(trader, market, side, amount, price, status, pnl_str, time), tags=tags)
            
    def show(self):
        self.frame.grid()
        self._refresh_trades()
        
    def hide(self):
        self.frame.grid_remove()