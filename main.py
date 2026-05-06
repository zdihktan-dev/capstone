import tkinter as tk  
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import sqlite3
from datetime import datetime
import random
import os

# ---------------- NEW IMPORTS (FEATURES) ----------------
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# PDF EXPORT
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

# ---------------- DATABASE ----------------
conn = sqlite3.connect("library.db")
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS students(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    fullname TEXT,
    student_id TEXT,
    course TEXT,
    year_level TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS books(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    author TEXT,
    category TEXT,
    quantity INTEGER
)''')

cursor.execute("DROP TABLE IF EXISTS borrow_requests")

cursor.execute('''CREATE TABLE borrow_requests(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT,
    student_id TEXT,
    course TEXT,
    year_level TEXT,
    book_title TEXT,
    status TEXT,
    borrow_date TEXT,
    expiry_date TEXT,
    time TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS reports(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT,
    student_id TEXT,
    book_title TEXT,
    action TEXT,
    date TEXT,
    time TEXT
)''')

# ---------------- DEFAULT ----------------
cursor.execute("INSERT OR IGNORE INTO users(username,password,role) VALUES('admin','admin123','admin')")
cursor.execute("INSERT OR IGNORE INTO users(username,password,role) VALUES('student','student123','student')")

cursor.execute("""
INSERT OR IGNORE INTO students(username,fullname,student_id,course,year_level)
VALUES('student','Juan Dela Cruz','2024-00123','BS Information Technology','3rd Year')
""")

book_count = cursor.execute("SELECT COUNT(*) FROM books").fetchone()[0]
if book_count == 0:
    it_books = [
        "Python Programming","Java Programming","C++ Fundamentals","Database Management",
        "Networking Basics","Cybersecurity Essentials","Artificial Intelligence",
        "Machine Learning","Web Development HTML/CSS","JavaScript Basics",
        "Data Structures","Algorithms","Cloud Computing","Operating Systems",
        "Software Engineering","Computer Architecture","Mobile App Development",
        "Information Security","Ethical Hacking","Linux Administration",
        "UI UX Design","Data Analytics","Computer Graphics","Game Development",
        "IoT Systems","Digital Logic","Computer Networks","PHP Programming",
        "SQL Advanced","React Development","Flask Development","Django Development",
        "API Development","System Analysis","Capstone Project Guide","Arduino Programming",
        "Big Data","Blockchain Technology","AWS Cloud","Azure Fundamentals",
        "DevOps Basics","Git Version Control","Robotics Programming","TensorFlow Basics",
        "Cyber Forensics","Penetration Testing","E-Commerce Systems",
        "IT Project Management","Multimedia Systems","Computer Ethics"
    ]

    for book in it_books:
        cursor.execute("INSERT INTO books(title,author,quantity) VALUES(?,?,?)",
        (book,"IT Author",random.randint(1,10)))

conn.commit()

# ---------------- MAIN ----------------
root = tk.Tk()
root.title("Library System")
root.state('zoomed')
root.resizable(False, False)

current_user = ""

# ---------------- IMAGES ----------------
def load_img(path, size):
    if os.path.exists(path):
        img = Image.open(path)
        img = img.resize(size)
        return ImageTk.PhotoImage(img)
    return None

bg_img = load_img("background.jpg", (2000,800))
logo_img = load_img("logo.png", (120,120))

# ---------------- NEW FEATURE: NOTIFICATION POPUP ----------------
def notify(msg, color="green"):
    pop = tk.Toplevel(root)
    pop.overrideredirect(True)
    pop.geometry("250x60+1000+50")
    tk.Label(pop,text=msg,bg=color,fg="white",font=("Arial",10,"bold")).pack(fill="both",expand=True)
    pop.after(2000,pop.destroy)

# ---------------- HELPERS ----------------
def get_student(username):
    return cursor.execute("SELECT * FROM students WHERE username=?",(username,)).fetchone()

# ---------------- LOGIN (UPGRADED UI) ----------------
def login_page():
    for w in root.winfo_children(): w.destroy()

    frame = tk.Frame(root, bg="white", bd=5, relief="ridge")
    frame.place(x=500,y=150,width=350,height=400)

    tk.Label(frame,text="LIBRARY SYSTEM",font=("Arial",16,"bold"),bg="white").pack(pady=10)

    u = tk.Entry(frame)
    u.pack(pady=5)

    p = tk.Entry(frame,show="*")
    p.pack(pady=5)

    r = ttk.Combobox(frame,values=["admin","student"])
    r.pack(pady=5)

    def login():
        global current_user
        user = cursor.execute("SELECT * FROM users WHERE username=? AND password=? AND role=?",
        (u.get(),p.get(),r.get())).fetchone()

        if user:
            current_user = u.get()
            notify("Login Success")

            if r.get()=="admin":
                admin_dashboard()
            else:
                student_dashboard()
        else:
            messagebox.showerror("Error","Invalid Login")

    tk.Button(frame,text="LOGIN",command=login,bg="green",fg="white").pack(pady=10)

# ---------------- STUDENT DASHBOARD ----------------
def student_dashboard():
    for w in root.winfo_children():
        w.destroy()

    st = get_student(current_user)

    tk.Label(root,text="STUDENT DASHBOARD",font=("Arial",18,"bold")).pack()

    # ---------------- SEARCH SYSTEM (NEW FEATURE) ----------------
    search_var = tk.StringVar()

    def search_books(*args):
        tree.delete(*tree.get_children())
        for b in cursor.execute("SELECT title,quantity FROM books WHERE title LIKE ?",
        ('%'+search_var.get()+'%',)).fetchall():
            tree.insert("","end",values=b)

    tk.Entry(root,textvariable=search_var).pack()
    search_var.trace("w",search_books)

    # BOOK LIST
    tree = ttk.Treeview(root,columns=("Title","Qty"),show="headings",height=10)
    tree.heading("Title",text="Book Title")
    tree.heading("Qty",text="Quantity")
    tree.pack()

    for b in cursor.execute("SELECT title,quantity FROM books").fetchall():
        tree.insert("","end",values=b)

# ---------------- ADMIN DASHBOARD ----------------
def admin_dashboard():
    for w in root.winfo_children():
        w.destroy()

    tk.Label(root,text="ADMIN DASHBOARD",font=("Arial",18,"bold")).pack()

    # ---------------- MATPLOTLIB CHART (NEW FEATURE) ----------------
    data = cursor.execute("SELECT title,quantity FROM books").fetchall()
    names = [d[0][:10] for d in data[:5]]
    qty = [d[1] for d in data[:5]]

    fig = plt.Figure(figsize=(5,3))
    ax = fig.add_subplot(111)
    ax.bar(names,qty)
    ax.set_title("Top Books")

    canvas = FigureCanvasTkAgg(fig,root)
    canvas.get_tk_widget().pack()

# ---------------- PDF ----------------
def export_pdf():
    data = cursor.execute("SELECT student_name,student_id,book_title,date,time FROM reports").fetchall()
    pdf = SimpleDocTemplate("report.pdf")
    table = Table([("Name","ID","Book","Date","Time")]+data)
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID',(0,0),(-1,-1),1,colors.black)
    ]))
    pdf.build([table])
    notify("PDF Generated","blue")

# ---------------- START ----------------
login_page()
root.mainloop()
