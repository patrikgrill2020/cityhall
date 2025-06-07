import os
import sqlite3
from tkinter import Tk, Frame, Label, Entry, Button, StringVar, IntVar, ttk, messagebox
from datetime import datetime

DB_NAME = 'inventory.db'

class InventoryDB:
    """Simple SQLite wrapper for inventory transactions"""
    def __init__(self, db_path=DB_NAME):
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        self.conn.execute(
            '''CREATE TABLE IF NOT EXISTS transactions (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   trans_date TEXT NOT NULL,
                   item_name TEXT NOT NULL,
                   quantity INTEGER NOT NULL,
                   trans_type TEXT NOT NULL,
                   project_name TEXT
               )''')
        self.conn.commit()

    def insert(self, trans_date, item_name, quantity, trans_type, project_name=None):
        self.conn.execute(
            'INSERT INTO transactions (trans_date, item_name, quantity, trans_type, project_name) '\
            'VALUES (?,?,?,?,?)',
            (trans_date, item_name, quantity, trans_type, project_name))
        self.conn.commit()

    def fetch_by_date(self, start_date, end_date):
        cursor = self.conn.execute(
            'SELECT trans_date, item_name, quantity, trans_type, project_name '
            'FROM transactions WHERE trans_date BETWEEN ? AND ? '
            'ORDER BY trans_date',
            (start_date, end_date))
        return cursor.fetchall()

class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title('مدیریت انبار')
        self.root.geometry('600x400')
        style = ttk.Style(self.root)
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        self.db = InventoryDB()
        self.setup_ui()

    def setup_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True)

        self.add_frame = Frame(notebook)
        self.report_frame = Frame(notebook)
        notebook.add(self.add_frame, text='افزودن/اختصاص کالا')
        notebook.add(self.report_frame, text='گزارش‌گیری')

        self.build_add_frame()
        self.build_report_frame()

    def build_add_frame(self):
        Label(self.add_frame, text='تاریخ (YYYY-MM-DD):').grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.date_var = StringVar(value=datetime.today().strftime('%Y-%m-%d'))
        Entry(self.add_frame, textvariable=self.date_var).grid(row=0, column=1, padx=5, pady=5)

        Label(self.add_frame, text='نام کالا:').grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.item_var = StringVar()
        Entry(self.add_frame, textvariable=self.item_var).grid(row=1, column=1, padx=5, pady=5)

        Label(self.add_frame, text='مقدار:').grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.qty_var = IntVar(value=1)
        Entry(self.add_frame, textvariable=self.qty_var).grid(row=2, column=1, padx=5, pady=5)

        Label(self.add_frame, text='نوع تراکنش:').grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.type_var = StringVar(value='ورود')
        type_combo = ttk.Combobox(self.add_frame, textvariable=self.type_var, values=['ورود', 'خروج'], state='readonly')
        type_combo.grid(row=3, column=1, padx=5, pady=5)
        type_combo.bind('<<ComboboxSelected>>', self.toggle_project_entry)

        Label(self.add_frame, text='نام پروژه (برای خروج):').grid(row=4, column=0, padx=5, pady=5, sticky='e')
        self.project_var = StringVar()
        self.project_entry = Entry(self.add_frame, textvariable=self.project_var, state='disabled')
        self.project_entry.grid(row=4, column=1, padx=5, pady=5)

        Button(self.add_frame, text='ذخیره', command=self.save_transaction).grid(row=5, column=0, columnspan=2, pady=10)

    def toggle_project_entry(self, event=None):
        if self.type_var.get() == 'خروج':
            self.project_entry.config(state='normal')
        else:
            self.project_entry.delete(0, 'end')
            self.project_entry.config(state='disabled')

    def save_transaction(self):
        date_val = self.date_var.get()
        item = self.item_var.get()
        qty = self.qty_var.get()
        trans_type = self.type_var.get()
        project = self.project_var.get() if trans_type == 'خروج' else None
        if not date_val or not item or qty <= 0:
            messagebox.showerror('خطا', 'لطفاً تمام فیلدها را به‌درستی پر کنید.')
            return
        try:
            datetime.strptime(date_val, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror('خطا', 'فرمت تاریخ نادرست است.')
            return
        self.db.insert(date_val, item, qty, trans_type, project)
        messagebox.showinfo('موفق', 'تراکنش ذخیره شد.')
        self.item_var.set('')
        self.qty_var.set(1)
        self.project_var.set('')
        self.type_var.set('ورود')
        self.toggle_project_entry()

    def build_report_frame(self):
        Label(self.report_frame, text='از تاریخ (YYYY-MM-DD):').grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.start_var = StringVar()
        Entry(self.report_frame, textvariable=self.start_var).grid(row=0, column=1, padx=5, pady=5)

        Label(self.report_frame, text='تا تاریخ (YYYY-MM-DD):').grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.end_var = StringVar()
        Entry(self.report_frame, textvariable=self.end_var).grid(row=1, column=1, padx=5, pady=5)

        Button(self.report_frame, text='نمایش گزارش', command=self.show_report).grid(row=2, column=0, columnspan=2, pady=10)

        cols = ('تاریخ', 'نام کالا', 'مقدار', 'نوع تراکنش', 'نام پروژه')
        self.tree = ttk.Treeview(self.report_frame, columns=cols, show='headings')
        for col in cols:
            self.tree.heading(col, text=col)
        self.tree.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

    def show_report(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        start = self.start_var.get()
        end = self.end_var.get()
        try:
            datetime.strptime(start, '%Y-%m-%d')
            datetime.strptime(end, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror('خطا', 'فرمت تاریخ نادرست است.')
            return
        rows = self.db.fetch_by_date(start, end)
        for r in rows:
            self.tree.insert('', 'end', values=r)

if __name__ == '__main__':
    root = Tk()
    app = InventoryApp(root)
    root.mainloop()
