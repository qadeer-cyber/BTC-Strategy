import tkinter as tk
from tkinter import ttk


class LogsScreen:
    def __init__(self, parent, db, logger):
        self.db = db
        self.logger = logger
        
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
            text='System Logs',
            font=('Helvetica', 14, 'bold'),
            bg='#2D2D3F',
            fg='#FFFFFF'
        ).pack(side='left', padx=20)
        
        self.level_var = tk.StringVar(value='all')
        
        tk.Label(toolbar, text='Level:', bg='#2D2D3F', fg='#A0A0B0').pack(side='left', padx=(20, 5))
        
        for level in ['all', 'debug', 'info', 'warning', 'error']:
            tk.Radiobutton(
                toolbar, text=level.upper(), variable=self.level_var, value=level,
                bg='#2D2D3F', fg='#FFFFFF', selectcolor='#3D3D4F',
                command=self._refresh_logs
            ).pack(side='left', padx=3)
        
        self.refresh_btn = tk.Button(
            toolbar,
            text='⟳ Refresh',
            font=('Helvetica', 10),
            bg='#3D3D4F',
            fg='#FFFFFF',
            bd=0,
            pady=8,
            padx=15,
            command=self._refresh_logs
        )
        self.refresh_btn.pack(side='right', padx=10, pady=10)
        
        content = tk.Frame(self.frame, bg='#1E1E2E')
        content.grid(row=1, column=0, sticky='nsew', padx=20, pady=10)
        
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)
        
        columns = ('Time', 'Level', 'Category', 'Message')
        
        self.tree = ttk.Treeview(content, columns=columns, show='headings')
        
        self.tree.heading('#0', text='')
        self.tree.column('#0', width=0, stretch=False)
        
        for col in columns:
            self.tree.heading(col, text=col)
            if col == 'Message':
                self.tree.column(col, width=500)
            elif col == 'Category':
                self.tree.column(col, width=120)
            else:
                self.tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(content, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        self.tree.tag_configure('debug', foreground='#A0A0B0')
        self.tree.tag_configure('info', foreground='#4ADE80')
        self.tree.tag_configure('warning', foreground='#FBBF24')
        self.tree.tag_configure('error', foreground='#F87171')
        
    def _refresh_logs(self):
        level = self.level_var.get()
        
        if level == 'all':
            logs = self.db.get_logs(limit=200)
        else:
            logs = self.db.get_logs(limit=200, level=level)
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for log in logs:
            time = (log.get('timestamp', '') or '')[-19:-3] or '--'
            level = (log.get('level', '') or 'info').lower()
            category = log.get('category', 'general') or 'general'
            message = log.get('message', '') or ''
            
            if len(message) > 100:
                message = message[:100] + '...'
            
            self.tree.insert('', 'end', values=(time, level.upper(), category, message), tags=(level,))
            
    def show(self):
        self.frame.grid()
        self._refresh_logs()
        
    def hide(self):
        self.frame.grid_remove()