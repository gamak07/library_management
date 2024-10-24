import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

# Initialize the database and create the 'books' and 'users' tables
def init_db():
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            year INTEGER,
            available INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            borrowed_books TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Admin Functions
def add_book(title, author, year):
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO books (title, author, year, available) VALUES (?, ?, ?, ?)''',
                   (title, author, year, 1))
    conn.commit()
    conn.close()
    messagebox.showinfo("Success", "Book added successfully!")

def view_books(tree):
    for row in tree.get_children():
        tree.delete(row)
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, author, year, available FROM books")
    for book in cursor.fetchall():
        availability = "Yes" if book[4] else "No"
        tree.insert("", "end", values=(book[0], book[1], book[2], book[3], availability))
    conn.close()

def edit_book(book_id, title, author, year):
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    cursor.execute('''UPDATE books SET title = ?, author = ?, year = ? WHERE id = ?''', (title, author, year, book_id))
    conn.commit()
    conn.close()
    messagebox.showinfo("Success", "Book details updated successfully!")

def delete_book(book_id):
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM books WHERE id = ?''', (book_id,))
    conn.commit()
    conn.close()
    messagebox.showinfo("Success", "Book deleted successfully!")

# User Functions
def borrow_book(user_name, selected_book):
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    
    # Check availability
    cursor.execute("SELECT available FROM books WHERE id = ?", (selected_book[0],))
    available = cursor.fetchone()
    
    if available and available[0] == 1:
        cursor.execute("UPDATE books SET available = 0 WHERE id = ?", (selected_book[0],))
        
        # Add to user's borrowed books
        cursor.execute("SELECT borrowed_books FROM users WHERE name = ?", (user_name,))
        result = cursor.fetchone()
        
        if result is None:
            cursor.execute("INSERT INTO users (name, borrowed_books) VALUES (?, ?)", (user_name, str(selected_book[0])))
        else:
            borrowed_books = result[0] + "," + str(selected_book[0])
            cursor.execute("UPDATE users SET borrowed_books = ? WHERE name = ?", (borrowed_books, user_name))

        conn.commit()
        messagebox.showinfo("Success", "Book borrowed successfully!")
    else:
        messagebox.showwarning("Warning", "Book is not available.")

    conn.close()

def return_book(user_name, selected_book):
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()

    # Remove from user's borrowed books
    cursor.execute("SELECT borrowed_books FROM users WHERE name = ?", (user_name,))
    result = cursor.fetchone()

    if result and result[0]:
        borrowed_books = result[0].split(",")
        
        if str(selected_book[0]) in borrowed_books:
            borrowed_books.remove(str(selected_book[0]))
            cursor.execute("UPDATE users SET borrowed_books = ? WHERE name = ?", (','.join(borrowed_books), user_name))
            cursor.execute("UPDATE books SET available = 1 WHERE id = ?", (selected_book[0],))
            conn.commit()
            messagebox.showinfo("Success", "Book returned successfully!")
        else:
            messagebox.showwarning("Warning", "You have not borrowed this book.")
    else:
        messagebox.showwarning("Warning", "You have no borrowed books.")

    conn.close()

def view_user_books(user_name, tree):
    for row in tree.get_children():
        tree.delete(row)
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    cursor.execute("SELECT borrowed_books FROM users WHERE name = ?", (user_name,))
    result = cursor.fetchone()
    
    if result and result[0]:
        book_ids = result[0].split(",")
        for book_id in book_ids:
            cursor.execute("SELECT id, title, author, year FROM books WHERE id = ?", (book_id,))
            book = cursor.fetchone()
            if book:
                tree.insert("", "end", values=(book[0], book[1], book[2], book[3]))

    conn.close()

# Admin Portal
class AdminPortal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Admin Portal")
        self.geometry("600x400")
        
        # Input Fields
        tk.Label(self, text="Title").grid(row=0, column=0, padx=10, pady=10)
        self.title_entry = tk.Entry(self)
        self.title_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(self, text="Author").grid(row=1, column=0, padx=10, pady=10)
        self.author_entry = tk.Entry(self)
        self.author_entry.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(self, text="Year").grid(row=2, column=0, padx=10, pady=10)
        self.year_entry = tk.Entry(self)
        self.year_entry.grid(row=2, column=1, padx=10, pady=10)

        # Buttons
        add_button = tk.Button(self, text="Add Book", command=self.add_book)
        add_button.grid(row=3, column=0, columnspan=2, pady=10)

        edit_button = tk.Button(self, text="Edit Book", command=self.edit_book)
        edit_button.grid(row=3, column=0, columnspan=2, pady=10, sticky='e')

        delete_button = tk.Button(self, text="Delete Book", command=self.delete_book)
        delete_button.grid(row=3, column=0, columnspan=2, pady=10, sticky='w')

        # Treeview for displaying books
        columns = ("ID", "Title", "Author", "Year", "Available")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

        # Load the books into the Treeview
        view_books(self.tree)

        # Bind selection
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        self.selected_book = None  # To store the selected book's ID

    def on_tree_select(self, event):
        selected_item = self.tree.selection()
        if selected_item:
            item = self.tree.item(selected_item[0])
            self.selected_book = item['values'][0]  # Get the ID of the selected book
            self.title_entry.delete(0, tk.END)
            self.author_entry.delete(0, tk.END)
            self.year_entry.delete(0, tk.END)

            # Populate the input fields with the selected book's details
            self.title_entry.insert(0, item['values'][1])
            self.author_entry.insert(0, item['values'][2])
            self.year_entry.insert(0, item['values'][3])

    def add_book(self):
        title = self.title_entry.get()
        author = self.author_entry.get()
        year = self.year_entry.get()

        if title and author and year.isdigit():
            add_book(title, author, int(year))
            self.title_entry.delete(0, tk.END)
            self.author_entry.delete(0, tk.END)
            self.year_entry.delete(0, tk.END)
            view_books(self.tree)  # Refresh the book list
            user_portal.load_books()  # Update user portal's book list
        else:
            messagebox.showerror("Error", "Please fill out all fields correctly.")

    def edit_book(self):
        if self.selected_book:
            title = self.title_entry.get()
            author = self.author_entry.get()
            year = self.year_entry.get()

            if title and author and year.isdigit():
                edit_book(self.selected_book, title, author, int(year))
                view_books(self.tree)  # Refresh the book list
                user_portal.load_books()  # Update user portal's book list
            else:
                messagebox.showerror("Error", "Please fill out all fields correctly.")
        else:
            messagebox.showwarning("Warning", "Please select a book to edit.")

    def delete_book(self):
        if self.selected_book:
            delete_book(self.selected_book)
            self.title_entry.delete(0, tk.END)
            self.author_entry.delete(0, tk.END)
            self.year_entry.delete(0, tk.END)
            view_books(self.tree)  # Refresh the book list
            user_portal.load_books()  # Update user portal's book list
        else:
            messagebox.showwarning("Warning", "Please select a book to delete.")

# User Portal
class UserPortal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("User Portal")
        self.geometry("600x400")
        
        tk.Label(self, text="Enter Your Name:").grid(row=0, column=0, padx=10, pady=10)
        self.user_name_entry = tk.Entry(self)
        self.user_name_entry.grid(row=0, column=1, padx=10, pady=10)

        # Buttons
        self.borrow_button = tk.Button(self, text="View Available Books", command=self.load_books)
        self.borrow_button.grid(row=1, column=0, columnspan=2, pady=10)

        self.borrow_button = tk.Button(self, text="Borrow Book", command=self.borrow_book)
        self.borrow_button.grid(row=1, column=0, columnspan=2, pady=10, sticky='w')

        self.return_button = tk.Button(self, text="Return Book", command=self.return_book)
        self.return_button.grid(row=1, column=0, columnspan=2, pady=10, sticky='e')

        # Treeview for available books
        columns = ("ID", "Title", "Author", "Year")
        self.available_books_tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.available_books_tree.heading(col, text=col)
        self.available_books_tree.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

        # Treeview for borrowed books
        self.borrowed_books_tree = ttk.Treeview(self, columns=columns, show="headings")
        self.borrowed_books_tree.heading("ID", text="ID")
        self.borrowed_books_tree.heading("Title", text="Title")
        self.borrowed_books_tree.heading("Author", text="Author")
        self.borrowed_books_tree.heading("Year", text="Year")
        self.borrowed_books_tree.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

    def load_books(self):
        for row in self.available_books_tree.get_children():
            self.available_books_tree.delete(row)
        conn = sqlite3.connect('library.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, author, year FROM books WHERE available = 1")
        for book in cursor.fetchall():
            self.available_books_tree.insert("", "end", values=book)
        conn.close()

    def load_borrowed_books(self):
        user_name = self.user_name_entry.get()
        view_user_books(user_name.strip(), self.borrowed_books_tree)

    def borrow_book(self):
        user_name = self.user_name_entry.get()
        selected_book = self.available_books_tree.selection()
        if selected_book:
            book_data = self.available_books_tree.item(selected_book[0])['values']
            borrow_book(user_name.strip(), book_data)
            self.load_books()  # Refresh the available books
            self.load_borrowed_books()  # Refresh borrowed books

    def return_book(self):
        user_name = self.user_name_entry.get()
        selected_book = self.borrowed_books_tree.selection()
        if selected_book:
            book_data = self.borrowed_books_tree.item(selected_book[0])['values']
            return_book(user_name.strip(), book_data)
            self.load_borrowed_books()  # Refresh the borrowed books
            self.load_books()  # Refresh the available books

# Initialize the database
init_db()

# Start both portals
admin_portal = AdminPortal()
user_portal = UserPortal()

admin_portal.mainloop()
