import tkinter as tk  
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import sqlite3
from datetime import datetime, timedelta
import random
import os
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import hashlib

# ==================== DATABASE SETUP ====================
class Database:
    def __init__(self, db_name="library.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.init_tables()
        self.init_default_data()
    
    def init_tables(self):
        # Users Table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Students Table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            fullname TEXT,
            student_id TEXT UNIQUE,
            course TEXT,
            year_level TEXT,
            email TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Books Table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS books(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE,
            author TEXT,
            category TEXT,
            isbn TEXT,
            quantity INTEGER,
            available INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Borrow Requests Table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS borrow_requests(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            student_name TEXT,
            book_id INTEGER,
            book_title TEXT,
            status TEXT DEFAULT 'pending',
            borrow_date TEXT,
            due_date TEXT,
            return_date TEXT,
            request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (book_id) REFERENCES books(id)
        )''')
        
        # Reports Table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS reports(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            student_name TEXT,
            book_id INTEGER,
            book_title TEXT,
            action TEXT,
            date TEXT,
            time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (book_id) REFERENCES books(id)
        )''')
        
        self.conn.commit()
    
    def init_default_data(self):
        # Check if admin exists
        admin = self.cursor.execute("SELECT * FROM users WHERE username='admin'").fetchone()
        if not admin:
            self.cursor.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)",
                              ('admin', 'admin123', 'admin'))
        
        # Check if default student exists
        student = self.cursor.execute("SELECT * FROM users WHERE username='student'").fetchone()
        if not student:
            self.cursor.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)",
                              ('student', 'student123', 'student'))
        
        # Add default student profile
        student_profile = self.cursor.execute("SELECT * FROM students WHERE student_id='2024-00123'").fetchone()
        if not student_profile:
            self.cursor.execute("""INSERT INTO students(username,fullname,student_id,course,year_level,email,phone)
                                 VALUES(?,?,?,?,?,?,?)""",
                              ('student', 'Juan Dela Cruz', '2024-00123', 'BS Information Technology', 
                               '3rd Year', 'juan@student.edu', '+63-9123456789'))
        
        # Add sample books if none exist
        book_count = self.cursor.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        if book_count == 0:
            books_data = [
                ("Python Programming", "John Smith", "Programming", "978-0134685991", 5),
                ("Java Programming", "Herbert Schildt", "Programming", "978-0134885287", 4),
                ("C++ Fundamentals", "Bjarne Stroustrup", "Programming", "978-0321958327", 3),
                ("Database Management", "Carlos Coronel", "Database", "978-0357673348", 6),
                ("Networking Basics", "Wendell Odom", "Networking", "978-0135237922", 5),
                ("Cybersecurity Essentials", "Eric Cole", "Security", "978-0134687605", 4),
                ("Artificial Intelligence", "Stuart Russell", "AI", "978-0134685299", 3),
                ("Machine Learning", "Andrew Ng", "AI", "978-0262035613", 4),
                ("Web Development", "Jon Duckett", "Web", "978-1491901205", 7),
                ("JavaScript Basics", "Kyle Simpson", "Web", "978-1491904244", 6),
                ("Data Structures", "Michael Goodrich", "CS", "978-1118771570", 5),
                ("Algorithms", "Thomas Cormen", "CS", "978-0262033848", 4),
                ("Cloud Computing", "Nayan Ruparelia", "Cloud", "978-0262525305", 3),
                ("Operating Systems", "Andrew Tanenbaum", "OS", "978-0134670991", 4),
                ("Software Engineering", "Sommerville", "Engineering", "978-0133943024", 5),
                ("Computer Architecture", "David Patterson", "Architecture", "978-0128119051", 3),
                ("Mobile App Development", "Dave Holz", "Mobile", "978-1491903261", 4),
                ("Information Security", "Mark Ciampa", "Security", "978-0357673348", 3),
                ("Ethical Hacking", "Dave Kennedy", "Security", "978-0134686959", 2),
                ("Linux Administration", "Evi Nemeth", "Linux", "978-0134277554", 5),
                ("UI UX Design", "Don Norman", "Design", "978-0143127192", 4),
                ("Data Analytics", "Marty Kagan", "Analytics", "978-0134091921", 3),
                ("Game Development", "Jason Gregory", "Game Dev", "978-0367505560", 2),
                ("IoT Systems", "Jean-Paul Yaacoub", "IoT", "978-0128126585", 3),
                ("DevOps Basics", "Gene Kim", "DevOps", "978-1942788003", 4),
                ("Git Version Control", "Scott Chacon", "Version Control", "978-1484200766", 6),
                ("Robotics", "Daniel Ollervides", "Robotics", "978-0134837673", 2),
                ("Big Data", "Nathan Marz", "Big Data", "978-1617291234", 3),
                ("Blockchain", "Don Tapscott", "Blockchain", "978-1530067900", 2),
                ("Capstone Project Guide", "Project Team", "Reference", "978-0000000000", 8),
            ]
            
            for title, author, category, isbn, qty in books_data:
                try:
                    self.cursor.execute(
                        "INSERT INTO books(title,author,category,isbn,quantity,available) VALUES(?,?,?,?,?,?)",
                        (title, author, category, isbn, qty, qty)
                    )
                except:
                    pass
        
        self.conn.commit()
    
    def verify_user(self, username, password, role):
        # Support both plain text (old database) and hashed passwords
        user = self.cursor.execute(
            "SELECT * FROM users WHERE username=? AND role=?",
            (username, role)
        ).fetchone()
        
        if user:
            stored_password = user[2]
            # Check if password matches (plain text for backward compatibility)
            if stored_password == password:
                return user
        
        return None
    
    def close(self):
        self.conn.close()

# ==================== MAIN APPLICATION ====================
class LibraryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Library Management System")
        self.root.geometry("1400x900")
        self.root.resizable(False, False)
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.db = Database()
        self.current_user = None
        self.current_role = None
        self.current_student = None
        
        # Start with login
        self.show_login()
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def show_notification(self, message, color="green"):
        pop = tk.Toplevel(self.root)
        pop.overrideredirect(True)
        pop.geometry("300x70+500+100")
        pop.attributes('-topmost', True)
        tk.Label(pop, text=message, bg=color, fg="white", 
                font=("Arial", 11, "bold"), wraplength=280).pack(fill="both", expand=True, padx=10, pady=10)
        pop.after(2500, pop.destroy)
    
    # ==================== LOGIN PAGE ====================
    def show_login(self):
        self.clear_window()
        
        # Main frame
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill="both", expand=True)
        
        # Header
        header = tk.Frame(main_frame, bg="#2c3e50", height=100)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="📚 Library Management System", 
                font=("Arial", 28, "bold"), bg="#2c3e50", fg="white").pack(pady=20)
        
        # Login form
        form_frame = tk.Frame(main_frame, bg="white", bd=2, relief="groove")
        form_frame.pack(pady=50, padx=20, fill="both", expand=True)
        
        tk.Label(form_frame, text="LOGIN", font=("Arial", 20, "bold"), 
                bg="white", fg="#2c3e50").pack(pady=20)
        
        # Username
        tk.Label(form_frame, text="Username:", font=("Arial", 11), bg="white").pack(pady=5)
        username_entry = tk.Entry(form_frame, font=("Arial", 11), width=40)
        username_entry.pack(pady=5, ipady=5)
        
        # Password
        tk.Label(form_frame, text="Password:", font=("Arial", 11), bg="white").pack(pady=5)
        password_entry = tk.Entry(form_frame, font=("Arial", 11), width=40, show="*")
        password_entry.pack(pady=5, ipady=5)
        
        # Role
        tk.Label(form_frame, text="Role:", font=("Arial", 11), bg="white").pack(pady=5)
        role_var = tk.StringVar(value="student")
        role_combo = ttk.Combobox(form_frame, textvariable=role_var, 
                                 values=["admin", "student"], state="readonly", width=37, font=("Arial", 11))
        role_combo.pack(pady=5, ipady=5)
        
        def login():
            username = username_entry.get().strip()
            password = password_entry.get()
            role = role_var.get()
            
            if not username or not password:
                messagebox.showerror("Error", "Please fill in all fields")
                return
            
            user = self.db.verify_user(username, password, role)
            
            if user:
                self.current_user = username
                self.current_role = role
                
                if role == "student":
                    student = self.db.cursor.execute(
                        "SELECT * FROM students WHERE username=?", (username,)
                    ).fetchone()
                    self.current_student = student
                
                self.show_notification("✓ Login Successful!")
                
                if role == "admin":
                    self.show_admin_dashboard()
                else:
                    self.show_student_dashboard()
            else:
                messagebox.showerror("Error", "Invalid username, password, or role")
        
        # Buttons
        button_frame = tk.Frame(form_frame, bg="white")
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="LOGIN", command=login, 
                 bg="#27ae60", fg="white", font=("Arial", 12, "bold"), 
                 width=15, padx=20, pady=10).pack(side="left", padx=10)
        
        tk.Button(button_frame, text="EXIT", command=self.root.quit, 
                 bg="#e74c3c", fg="white", font=("Arial", 12, "bold"), 
                 width=15, padx=20, pady=10).pack(side="left", padx=10)
        
        # Demo credentials info
        info_frame = tk.Frame(main_frame, bg="#ecf0f1", bd=1, relief="solid")
        info_frame.pack(pady=10, padx=20, fill="x")
        
        tk.Label(info_frame, text="Demo Credentials - Admin: admin/admin123 | Student: student/student123", 
                font=("Arial", 10), bg="#ecf0f1", fg="#2c3e50").pack(pady=10)
    
    # ==================== STUDENT DASHBOARD ====================
    def show_student_dashboard(self):
        self.clear_window()
        
        # Header
        header = tk.Frame(self.root, bg="#3498db", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text=f"🎓 Student Dashboard - {self.current_student[2]}", 
                font=("Arial", 16, "bold"), bg="#3498db", fg="white").pack(side="left", padx=20, pady=15)
        
        tk.Button(header, text="Logout", command=lambda: self.logout(), 
                 bg="#e74c3c", fg="white", font=("Arial", 10, "bold")).pack(side="right", padx=20, pady=15)
        
        # Main content
        content = tk.Frame(self.root, bg="white")
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left panel - Student Info
        left_panel = tk.Frame(content, bg="#ecf0f1", bd=2, relief="solid")
        left_panel.pack(side="left", fill="both", padx=5, pady=5)
        left_panel.pack_propagate(False)
        left_panel.config(width=250)
        
        tk.Label(left_panel, text="📋 Your Information", font=("Arial", 12, "bold"), 
                bg="#ecf0f1", fg="#2c3e50").pack(pady=10, fill="x", padx=10)
        
        info_text = f"""
Name: {self.current_student[2]}
Student ID: {self.current_student[3]}
Course: {self.current_student[4]}
Year: {self.current_student[5]}
Email: {self.current_student[6] or 'N/A'}
Phone: {self.current_student[7] or 'N/A'}
        """
        
        tk.Label(left_panel, text=info_text, font=("Arial", 9), 
                bg="#ecf0f1", fg="#2c3e50", justify="left").pack(pady=10, padx=10, fill="both")
        
        tk.Label(left_panel, text="📚 My Borrowings", font=("Arial", 12, "bold"), 
                bg="#ecf0f1", fg="#2c3e50").pack(pady=(20, 10), fill="x", padx=10)
        
        # Get borrowing history
        borrowed = self.db.cursor.execute(
            "SELECT book_title, borrow_date, due_date, status FROM borrow_requests WHERE student_id=? ORDER BY request_date DESC",
            (self.current_student[3],)
        ).fetchall()
        
        if borrowed:
            for book, borrow, due, status in borrowed[:5]:
                status_color = "#27ae60" if status == "returned" else "#e74c3c"
                tk.Label(left_panel, text=f"• {book}\n  Due: {due}\n  Status: {status}", 
                        font=("Arial", 8), bg="#ecf0f1", fg="#2c3e50", 
                        wraplength=230, justify="left").pack(pady=5, padx=10, fill="x")
        else:
            tk.Label(left_panel, text="No borrowings yet", font=("Arial", 9), 
                    bg="#ecf0f1", fg="#95a5a6").pack(pady=10, padx=10)
        
        # Right panel - Book Management
        right_panel = tk.Frame(content, bg="white")
        right_panel.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # Search panel
        search_frame = tk.Frame(right_panel, bg="white", bd=1, relief="solid")
        search_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(search_frame, text="Search Books:", font=("Arial", 11, "bold"), 
                bg="white", fg="#2c3e50").pack(side="left", padx=10, pady=10)
        
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var, font=("Arial", 10), width=40)
        search_entry.pack(side="left", padx=5, pady=10)
        
        # Book list
        tree_frame = tk.Frame(right_panel, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("Title", "Author", "Category", "Available", "Action")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        tree.column("Title", width=250)
        tree.column("Author", width=150)
        tree.column("Category", width=100)
        tree.column("Available", width=80)
        tree.column("Action", width=80)
        
        for col in columns:
            tree.heading(col, text=col)
        
        tree.pack(fill="both", expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscroll=scrollbar.set)
        
        def load_books():
            tree.delete(*tree.get_children())
            query = self.db.cursor.execute(
                "SELECT id, title, author, category, available FROM books ORDER BY title"
            ).fetchall()
            
            for book in query:
                book_id, title, author, category, available = book
                
                # Check if student already borrowed this book
                borrowed_book = self.db.cursor.execute(
                    "SELECT * FROM borrow_requests WHERE student_id=? AND book_id=? AND status='borrowed'",
                    (self.current_student[3], book_id)
                ).fetchone()
                
                btn_text = "Borrowed" if borrowed_book else ("Request" if available > 0 else "NA")
                tree.insert("", "end", values=(title, author, category, available, btn_text))
        
        def search_books(*args):
            tree.delete(*tree.get_children())
            search_term = search_var.get().lower()
            query = self.db.cursor.execute(
                "SELECT id, title, author, category, available FROM books WHERE LOWER(title) LIKE ? OR LOWER(author) LIKE ? ORDER BY title",
                (f"%{search_term}%", f"%{search_term}%")
            ).fetchall()
            
            for book in query:
                book_id, title, author, category, available = book
                borrowed_book = self.db.cursor.execute(
                    "SELECT * FROM borrow_requests WHERE student_id=? AND book_id=? AND status='borrowed'",
                    (self.current_student[3], book_id)
                ).fetchone()
                
                btn_text = "Borrowed" if borrowed_book else ("Request" if available > 0 else "NA")
                tree.insert("", "end", values=(title, author, category, available, btn_text))
        
        search_var.trace("w", search_books)
        load_books()
        
        # Request button
        def request_book():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a book")
                return
            
            item = tree.item(selection[0])
            book_title = item['values'][0]
            
            # Get book details
            book = self.db.cursor.execute(
                "SELECT id, available FROM books WHERE title=?", (book_title,)
            ).fetchone()
            
            if not book or book[1] == 0:
                messagebox.showerror("Error", "Book not available")
                return
            
            # Check if already requested
            existing = self.db.cursor.execute(
                "SELECT * FROM borrow_requests WHERE student_id=? AND book_id=? AND status IN ('pending', 'borrowed')",
                (self.current_student[3], book[0])
            ).fetchone()
            
            if existing:
                messagebox.showinfo("Info", "You already have a pending or active request for this book")
                return
            
            # Create request
            today = datetime.now().strftime("%Y-%m-%d")
            due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
            
            self.db.cursor.execute(
                """INSERT INTO borrow_requests(student_id, student_name, book_id, book_title, status, borrow_date, due_date)
                   VALUES(?, ?, ?, ?, 'borrowed', ?, ?)""",
                (self.current_student[3], self.current_student[2], book[0], book_title, today, due_date)
            )
            
            # Update book availability
            self.db.cursor.execute(
                "UPDATE books SET available = available - 1 WHERE id=?", (book[0],)
            )
            
            self.db.conn.commit()
            
            # Add to reports
            self.db.cursor.execute(
                """INSERT INTO reports(student_id, student_name, book_id, book_title, action, date, time)
                   VALUES(?, ?, ?, ?, 'borrowed', ?, ?)""",
                (self.current_student[3], self.current_student[2], book[0], book_title, today, datetime.now().strftime("%H:%M:%S"))
            )
            self.db.conn.commit()
            
            self.show_notification(f"✓ Book requested: {book_title}")
            load_books()
        
        button_frame = tk.Frame(right_panel, bg="white")
        button_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(button_frame, text="Request Book", command=request_book, 
                 bg="#27ae60", fg="white", font=("Arial", 10, "bold"), 
                 padx=15, pady=8).pack(side="left", padx=5)
        
        tk.Button(button_frame, text="Return Book", command=self.show_return_book, 
                 bg="#3498db", fg="white", font=("Arial", 10, "bold"), 
                 padx=15, pady=8).pack(side="left", padx=5)
    
    def show_return_book(self):
        window = tk.Toplevel(self.root)
        window.title("Return Book")
        window.geometry("400x300")
        window.resizable(False, False)
        
        tk.Label(window, text="Return Book", font=("Arial", 14, "bold"), 
                bg="#3498db", fg="white").pack(fill="x", pady=10)
        
        frame = tk.Frame(window, bg="white")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Get borrowed books
        borrowed = self.db.cursor.execute(
            "SELECT id, book_title FROM borrow_requests WHERE student_id=? AND status='borrowed'",
            (self.current_student[3],)
        ).fetchall()
        
        if not borrowed:
            tk.Label(frame, text="No borrowed books", font=("Arial", 11), 
                    bg="white", fg="#95a5a6").pack(pady=20)
            return
        
        tk.Label(frame, text="Select book to return:", font=("Arial", 11, "bold"), 
                bg="white", fg="#2c3e50").pack(pady=10)
        
        book_var = tk.StringVar()
        books_list = [b[1] for b in borrowed]
        
        combo = ttk.Combobox(frame, textvariable=book_var, values=books_list, state="readonly", width=40)
        combo.pack(pady=10, ipady=5)
        
        def return_book():
            book_title = book_var.get()
            if not book_title:
                messagebox.showwarning("Warning", "Please select a book")
                return
            
            # Get book request
            request = self.db.cursor.execute(
                "SELECT id, book_id FROM borrow_requests WHERE student_id=? AND book_title=? AND status='borrowed'",
                (self.current_student[3], book_title)
            ).fetchone()
            
            if request:
                return_date = datetime.now().strftime("%Y-%m-%d")
                
                # Update request
                self.db.cursor.execute(
                    "UPDATE borrow_requests SET status='returned', return_date=? WHERE id=?",
                    (return_date, request[0])
                )
                
                # Update book availability
                self.db.cursor.execute(
                    "UPDATE books SET available = available + 1 WHERE id=?", (request[1],)
                )
                
                # Add to reports
                self.db.cursor.execute(
                    """INSERT INTO reports(student_id, student_name, book_id, book_title, action, date, time)
                       VALUES(?, ?, ?, ?, 'returned', ?, ?)""",
                    (self.current_student[3], self.current_student[2], request[1], book_title, 
                     return_date, datetime.now().strftime("%H:%M:%S"))
                )
                
                self.db.conn.commit()
                self.show_notification(f"✓ Book returned: {book_title}")
                window.destroy()
                self.show_student_dashboard()
        
        tk.Button(frame, text="Return Book", command=return_book, 
                 bg="#27ae60", fg="white", font=("Arial", 11, "bold"), 
                 padx=15, pady=8).pack(pady=20)
    
    # ==================== ADMIN DASHBOARD ====================
    def show_admin_dashboard(self):
        self.clear_window()
        
        # Header
        header = tk.Frame(self.root, bg="#2c3e50", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="⚙️ Admin Dashboard", font=("Arial", 16, "bold"), 
                bg="#2c3e50", fg="white").pack(side="left", padx=20, pady=15)
        
        tk.Button(header, text="Logout", command=lambda: self.logout(), 
                 bg="#e74c3c", fg="white", font=("Arial", 10, "bold")).pack(side="right", padx=20, pady=15)
        
        # Tab menu
        tab_frame = tk.Frame(self.root, bg="#34495e", height=50)
        tab_frame.pack(fill="x")
        tab_frame.pack_propagate(False)
        
        def show_tab(tab_name):
            content_frame.destroy()
            if tab_name == "Dashboard":
                self.admin_dashboard_content()
            elif tab_name == "Books":
                self.admin_books_content()
            elif tab_name == "Requests":
                self.admin_requests_content()
            elif tab_name == "Reports":
                self.admin_reports_content()
        
        tabs = ["Dashboard", "Books", "Requests", "Reports"]
        for tab in tabs:
            tk.Button(tab_frame, text=tab, command=lambda t=tab: show_tab(t),
                     bg="#34495e", fg="white", font=("Arial", 10, "bold"),
                     padx=20, pady=15, relief="flat", bd=0).pack(side="left", padx=5)
        
        # Content area
        content_frame = tk.Frame(self.root, bg="white")
        content_frame.pack(fill="both", expand=True)
        self.content_frame = content_frame
        
        self.admin_dashboard_content()
    
    def admin_dashboard_content(self):
        if hasattr(self, 'content_frame'):
            for w in self.content_frame.winfo_children():
                w.destroy()
        
        frame = self.content_frame
        
        # Statistics
        stats_frame = tk.Frame(frame, bg="white")
        stats_frame.pack(fill="x", padx=20, pady=20)
        
        # Total books
        total_books = self.db.cursor.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        total_available = self.db.cursor.execute("SELECT SUM(available) FROM books").fetchone()[0] or 0
        total_students = self.db.cursor.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        total_requests = self.db.cursor.execute("SELECT COUNT(*) FROM borrow_requests").fetchone()[0]
        
        stats = [
            ("📚 Total Books", total_books, "#3498db"),
            ("✓ Available", total_available, "#27ae60"),
            ("👥 Students", total_students, "#9b59b6"),
            ("📋 Requests", total_requests, "#e74c3c")
        ]
        
        for label, value, color in stats:
            stat_box = tk.Frame(stats_frame, bg=color, relief="solid", bd=1)
            stat_box.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            
            tk.Label(stat_box, text=label, font=("Arial", 11, "bold"), 
                    bg=color, fg="white").pack(pady=(15, 5))
            tk.Label(stat_box, text=str(value), font=("Arial", 24, "bold"), 
                    bg=color, fg="white").pack(pady=(5, 15))
        
        # Recent activities
        tk.Label(frame, text="📊 Recent Activities", font=("Arial", 13, "bold"), 
                bg="white", fg="#2c3e50").pack(anchor="w", padx=20, pady=(20, 10))
        
        tree_frame = tk.Frame(frame, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("Student", "Book", "Action", "Date", "Time")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
        tree.column("Student", width=150)
        tree.column("Book", width=250)
        tree.column("Action", width=80)
        tree.column("Date", width=100)
        tree.column("Time", width=80)
        
        tree.pack(fill="both", expand=True)
        
        reports = self.db.cursor.execute(
            "SELECT student_name, book_title, action, date, time FROM reports ORDER BY created_at DESC LIMIT 20"
        ).fetchall()
        
        for report in reports:
            tree.insert("", "end", values=report)
    
    def admin_books_content(self):
        if hasattr(self, 'content_frame'):
            for w in self.content_frame.winfo_children():
                w.destroy()
        
        frame = self.content_frame
        
        # Add book form
        form_frame = tk.Frame(frame, bg="#ecf0f1", relief="solid", bd=1)
        form_frame.pack(fill="x", padx=20, pady=20)
        
        tk.Label(form_frame, text="Add New Book", font=("Arial", 12, "bold"), 
                bg="#ecf0f1", fg="#2c3e50").pack(pady=10)
        
        input_frame = tk.Frame(form_frame, bg="#ecf0f1")
        input_frame.pack(fill="x", padx=10, pady=10)
        
        fields = {}
        field_names = ["Title", "Author", "Category", "ISBN", "Quantity"]
        
        for field in field_names:
            tk.Label(input_frame, text=f"{field}:", font=("Arial", 9), 
                    bg="#ecf0f1", fg="#2c3e50").pack(side="left", padx=5)
            entry = tk.Entry(input_frame, font=("Arial", 9), width=15)
            entry.pack(side="left", padx=5)
            fields[field] = entry
        
        def add_book():
            try:
                if not all(f.get().strip() for f in fields.values()):
                    messagebox.showwarning("Warning", "Please fill all fields")
                    return
                
                qty = int(fields["Quantity"].get())
                
                self.db.cursor.execute(
                    """INSERT INTO books(title, author, category, isbn, quantity, available)
                       VALUES(?, ?, ?, ?, ?, ?)""",
                    (fields["Title"].get(), fields["Author"].get(), fields["Category"].get(),
                     fields["ISBN"].get(), qty, qty)
                )
                self.db.conn.commit()
                
                self.show_notification("✓ Book added successfully")
                for entry in fields.values():
                    entry.delete(0, "end")
                self.admin_books_content()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        tk.Button(input_frame, text="Add Book", command=add_book, 
                 bg="#27ae60", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=5)
        
        # Books list
        tk.Label(frame, text="📚 Book Inventory", font=("Arial", 13, "bold"), 
                bg="white", fg="#2c3e50").pack(anchor="w", padx=20, pady=(20, 10))
        
        tree_frame = tk.Frame(frame, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("Title", "Author", "Category", "ISBN", "Total", "Available")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
        tree.column("Title", width=200)
        tree.column("Author", width=150)
        tree.column("Category", width=100)
        tree.column("ISBN", width=100)
        tree.column("Total", width=60)
        tree.column("Available", width=80)
        
        tree.pack(fill="both", expand=True)
        
        books = self.db.cursor.execute(
            "SELECT title, author, category, isbn, quantity, available FROM books ORDER BY title"
        ).fetchall()
        
        for book in books:
            tree.insert("", "end", values=book)
    
    def admin_requests_content(self):
        if hasattr(self, 'content_frame'):
            for w in self.content_frame.winfo_children():
                w.destroy()
        
        frame = self.content_frame
        
        tk.Label(frame, text="📋 Borrow Requests", font=("Arial", 13, "bold"), 
                bg="white", fg="#2c3e50").pack(anchor="w", padx=20, pady=(20, 10))
        
        tree_frame = tk.Frame(frame, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("Student", "Book", "Status", "Borrow Date", "Due Date", "Action")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
        tree.column("Student", width=150)
        tree.column("Book", width=200)
        tree.column("Status", width=80)
        tree.column("Borrow Date", width=100)
        tree.column("Due Date", width=100)
        tree.column("Action", width=80)
        
        tree.pack(fill="both", expand=True)
        
        requests = self.db.cursor.execute(
            "SELECT id, student_name, book_title, status, borrow_date, due_date FROM borrow_requests ORDER BY request_date DESC"
        ).fetchall()
        
        for req in requests:
            tree.insert("", "end", values=(req[1], req[2], req[3], req[4], req[5], "Manage"))
    
    def admin_reports_content(self):
        if hasattr(self, 'content_frame'):
            for w in self.content_frame.winfo_children():
                w.destroy()
        
        frame = self.content_frame
        
        # Export button
        button_frame = tk.Frame(frame, bg="white")
        button_frame.pack(fill="x", padx=20, pady=20)
        
        tk.Button(button_frame, text="Export to PDF", command=self.export_pdf, 
                 bg="#3498db", fg="white", font=("Arial", 10, "bold"), 
                 padx=15, pady=8).pack(side="left")
        
        tk.Label(frame, text="📊 Activity Reports", font=("Arial", 13, "bold"), 
                bg="white", fg="#2c3e50").pack(anchor="w", padx=20, pady=(10, 10))
        
        tree_frame = tk.Frame(frame, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("Student ID", "Student", "Book", "Action", "Date", "Time")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
        tree.column("Student ID", width=100)
        tree.column("Student", width=150)
        tree.column("Book", width=250)
        tree.column("Action", width=80)
        tree.column("Date", width=100)
        tree.column("Time", width=80)
        
        tree.pack(fill="both", expand=True)
        
        reports = self.db.cursor.execute(
            "SELECT student_id, student_name, book_title, action, date, time FROM reports ORDER BY created_at DESC"
        ).fetchall()
        
        for report in reports:
            tree.insert("", "end", values=report)
    
    def export_pdf(self):
        try:
            file_path = filedialog.asksaveasfilename(defaultextension=".pdf", 
                                                     filetypes=[("PDF files", "*.pdf")])
            if not file_path:
                return
            
            reports_data = self.db.cursor.execute(
                "SELECT student_id, student_name, book_title, action, date, time FROM reports ORDER BY created_at DESC"
            ).fetchall()
            
            pdf = SimpleDocTemplate(file_path)
            styles = getSampleStyleSheet()
            elements = []
            
            # Title
            elements.append(Paragraph("Library Management System - Activity Report", styles['Heading1']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                                    styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # Table
            table_data = [["Student ID", "Student Name", "Book Title", "Action", "Date", "Time"]]
            table_data.extend(reports_data)
            
            table = Table(table_data, colWidths=[80, 120, 180, 80, 80, 80])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            pdf.build(elements)
            
            self.show_notification(f"✓ PDF exported successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export PDF: {str(e)}")
    
    def logout(self):
        self.current_user = None
        self.current_role = None
        self.current_student = None
        self.show_login()

# ==================== MAIN ====================
if __name__ == "__main__":
    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()
