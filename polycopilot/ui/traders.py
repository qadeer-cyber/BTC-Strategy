import tkinter as tk
from tkinter import ttk
import threading


class TradersScreen:
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
        
        self.refresh_btn = tk.Button(
            toolbar,
            text='⟳ Refresh Leaderboard',
            font=('Helvetica', 10),
            bg='#3D3D4F',
            fg='#FFFFFF',
            bd=0,
            pady=8,
            padx=15,
            command=self._refresh_traders
        )
        self.refresh_btn.pack(side='left', padx=10, pady=10)
        
        self.search_entry = tk.Entry(
            toolbar,
            font=('Helvetica', 10),
            bg='#3D3D4F',
            fg='#FFFFFF',
            width=30
        )
        self.search_entry.pack(side='left', padx=10)
        self.search_entry.insert(0, 'Search traders...')
        self.search_entry.bind('<FocusIn>', lambda e: self.search_entry.delete(0, 'end') if self.search_entry.get() == 'Search traders...' else None)
        
        content = tk.Frame(self.frame, bg='#1E1E2E')
        content.grid(row=1, column=0, sticky='nsew', padx=20, pady=10)
        
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)
        
        columns = ('Name', 'Volume', 'P&L', 'Trades', 'Last Active', 'Status')
        
        self.tree = ttk.Treeview(content, columns=columns, show='headings')
        
        self.tree.heading('#0', text='')
        self.tree.column('#0', width=0, stretch=False)
        
        for col in columns:
            self.tree.heading(col, text=col)
            if col == 'Name':
                self.tree.column(col, width=200)
            elif col in ['Volume', 'P&L', 'Trades']:
                self.tree.column(col, width=100)
            else:
                self.tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(content, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        self.tree.tag_configure('followed', background='#00D4AA20')
        self.tree.tag_configure('blacklisted', background='#F8717120')
        
        controls = tk.Frame(self.frame, bg='#2D2D3F', height=60)
        controls.grid(row=2, column=0, sticky='ew')
        controls.grid_propagate(False)
        
        self.follow_btn = tk.Button(
            controls,
            text='✓ Follow',
            font=('Helvetica', 10),
            bg='#00D4AA',
            fg='#000000',
            bd=0,
            pady=8,
            padx=20,
            command=self._follow_trader
        )
        self.follow_btn.pack(side='left', padx=10, pady=10)
        
        self.unfollow_btn = tk.Button(
            controls,
            text='✗ Unfollow',
            font=('Helvetica', 10),
            bg='#3D3D4F',
            fg='#FFFFFF',
            bd=0,
            pady=8,
            padx=20,
            command=self._unfollow_trader
        )
        self.unfollow_btn.pack(side='left', padx=10, pady=10)
        
        self.blacklist_btn = tk.Button(
            controls,
            text='⛔ Blacklist',
            font=('Helvetica', 10),
            bg='#F87171',
            fg='#000000',
            bd=0,
            pady=8,
            padx=20,
            command=self._blacklist_trader
        )
        self.blacklist_btn.pack(side='left', padx=10, pady=10)
        
        self.remove_blacklist_btn = tk.Button(
            controls,
            text='✓ Remove Blacklist',
            font=('Helvetica', 10),
            bg='#3D3D4F',
            fg='#FFFFFF',
            bd=0,
            pady=8,
            padx=20,
            command=self._remove_blacklist
        )
        self.remove_blacklist_btn.pack(side='left', padx=10, pady=10)
        
    def _refresh_traders(self):
        self.refresh_btn.configure(state='disabled', text='Loading...')
        
        def fetch():
            try:
                if self.bot and self.bot.scanner:
                    traders = self.bot.scanner.fetch_leaderboard()
                    
                    filtered = self.bot.scanner.filter_traders(traders)
                    
                    self.frame.after(0, lambda: self._update_tree(filtered))
                else:
                    traders = self.db.get_all_traders()
                    self.frame.after(0, lambda: self._update_tree(traders))
            except Exception as e:
                self.logger.error(f'Error refreshing traders: {e}', 'traders')
            finally:
                self.frame.after(0, lambda: self.refresh_btn.configure(state='normal', text='⟳ Refresh Leaderboard'))
        
        threading.Thread(target=fetch, daemon=True).start()
        
    def _update_tree(self, traders):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for trader in traders:
            wallet = trader.get('wallet_address', '')
            name = trader.get('display_name', wallet[:10])
            volume = f"${trader.get('total_volume', 0):,.0f}"
            pnl = f"${trader.get('total_pnl', 0):,.0f}"
            trades = str(trader.get('trade_count', 0))
            
            last_active = trader.get('last_active', '')
            if last_active:
                try:
                    from datetime import datetime
                    last = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
                    last_active = last.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            is_followed = trader.get('is_followed', 0)
            is_blacklisted = trader.get('is_blacklisted', 0)
            
            status = 'Following' if is_followed else ('Blacklisted' if is_blacklisted else 'Available')
            
            tags = []
            if is_followed:
                tags.append('followed')
            if is_blacklisted:
                tags.append('blacklisted')
            
            self.tree.insert('', 'end', values=(name, volume, pnl, trades, last_active, status), tags=tags, text=wallet)
            
    def _follow_trader(self):
        selected = self.tree.selection()
        if not selected:
            return
            
        wallet = self.tree.item(selected[0])['text']
        
        if self.bot and self.bot.scanner:
            self.bot.scanner.follow_trader(wallet)
        
        self._refresh_traders()
        
    def _unfollow_trader(self):
        selected = self.tree.selection()
        if not selected:
            return
            
        wallet = self.tree.item(selected[0])['text']
        
        if self.bot and self.bot.scanner:
            self.bot.scanner.unfollow_trader(wallet)
        
        self._refresh_traders()
        
    def _blacklist_trader(self):
        selected = self.tree.selection()
        if not selected:
            return
            
        wallet = self.tree.item(selected[0])['text']
        
        if self.bot and self.bot.scanner:
            self.bot.scanner.blacklist_trader(wallet)
        
        self._refresh_traders()
        
    def _remove_blacklist(self):
        selected = self.tree.selection()
        if not selected:
            return
            
        wallet = self.tree.item(selected[0])['text']
        
        if self.bot and self.bot.scanner:
            self.bot.scanner.unblacklist_trader(wallet)
        
        self._refresh_traders()
        
    def show(self):
        self.frame.grid()
        self._refresh_traders()
        
    def hide(self):
        self.frame.grid_remove()