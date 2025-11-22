# college_gui_complete_project_final.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv, os
import mysql.connector
from datetime import datetime

# Optional logo
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# ----------------------- DATABASE CONNECTION -----------------------
try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",           # Change if needed
        password="chintu20",   # Change if needed
        database="student_database"
    )
    cursor = conn.cursor()
    print("Connected to Database:", conn.database)
except mysql.connector.Error as e:
    messagebox.showerror("Database Error", str(e))
    raise SystemExit("MySQL connection failed.")

# ----------------------- DATABASE BACKUP -----------------------
def backup_database():
    """Creates a backup .sql file after every commit."""
    try:
        dump_path = os.path.join(os.getcwd(), "student_database_backup.sql")
        # Note: -p followed immediately by password (no space)
        cmd = f'mysqldump -u root -pchintu20 student_database > "{dump_path}"'
        os.system(cmd)
        print("Backup saved:", dump_path)
    except Exception as e:
        print("Backup failed:", e)

# ----------------------- SETUP TRIGGERS / FUNCTIONS / PROCEDURES -----------------------
def setup_sql_objects():
    try:
        # Trigger: Professor email lowercase
        cursor.execute("DROP TRIGGER IF EXISTS trg_student_Insert_Lowercase_Email;")
        cursor.execute("""
        CREATE TRIGGER trg_student_Insert_Lowercase_Email
        BEFORE INSERT ON Professor
        FOR EACH ROW
        BEGIN
            SET NEW.Email = LOWER(NEW.Email);
        END;
        """)

        # Trigger: Student DOB validation (student must be at least 18)
        cursor.execute("DROP TRIGGER IF EXISTS trg_Before_Student_Insert_Validate_DOB;")
        cursor.execute("""
        CREATE TRIGGER trg_Before_Student_Insert_Validate_DOB
        BEFORE INSERT ON Student
        FOR EACH ROW
        BEGIN
            IF NEW.DOB > DATE_SUB(CURDATE(), INTERVAL 18 YEAR) THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Invalid DOB: Student must be at least 18 years old.';
            END IF;
        END;
        """)

        # Procedure: Add New Student (includes Dept_ID)
        cursor.execute("DROP PROCEDURE IF EXISTS sp_AddNewStudent;")
        cursor.execute("""
        CREATE PROCEDURE sp_AddNewStudent(
            IN p_Stu_ID INT,
            IN p_Name VARCHAR(255),
            IN p_Phone VARCHAR(20),
            IN p_Email VARCHAR(255),
            IN p_DOB DATE,
            IN p_Gender VARCHAR(10),
            IN p_Clg_ID INT,
            IN p_Dept_ID INT
        )
        BEGIN
            INSERT INTO Student (Stu_ID, Name, Phone_No, Email, DOB, Gender, Clg_ID, Dept_ID)
            VALUES (p_Stu_ID, p_Name, p_Phone, p_Email, p_DOB, p_Gender, p_Clg_ID, p_Dept_ID);
        END;
        """)

        # Procedure: Get Students by Department (direct lookup using Student + Department)
        cursor.execute("DROP PROCEDURE IF EXISTS sp_GetStudentsByDepartment;")
        cursor.execute("""
        CREATE PROCEDURE sp_GetStudentsByDepartment(IN p_Dept_Name VARCHAR(255))
        BEGIN
            SELECT s.Name, s.Email
            FROM Student s
            JOIN Department d ON s.Dept_ID = d.Dept_ID
            WHERE d.Dept_Name = p_Dept_Name;
        END;
        """)

        # Function: Get Department HOD
        cursor.execute("DROP FUNCTION IF EXISTS fn_GetDepartmenttHOD;")
        cursor.execute("""
        CREATE FUNCTION fn_GetDepartmenttHOD(p_Dept_Name VARCHAR(255))
        RETURNS VARCHAR(255)
        READS SQL DATA
        BEGIN
            DECLARE v_HOD_Name VARCHAR(255);
            SELECT HOD INTO v_HOD_Name FROM Department WHERE Dept_Name = p_Dept_Name;
            RETURN v_HOD_Name;
        END;
        """)

        # Function: Get Student Count by College
        cursor.execute("DROP FUNCTION IF EXISTS fn_GetStudentCountByCollege_;")
        cursor.execute("""
        CREATE FUNCTION fn_GetStudentCountByCollege_(p_Clg_ID INT)
        RETURNS INT
        READS SQL DATA
        BEGIN
            DECLARE v_Student_Count INT;
            SELECT COUNT(*) INTO v_Student_Count FROM Student WHERE Clg_ID = p_Clg_ID;
            RETURN v_Student_Count;
        END;
        """)

        conn.commit()
        print("All Triggers, Procedures, and Functions created/updated.")
    except mysql.connector.Error as e:
        print("SQL Object Creation Error:", e)

# Try to create SQL objects (safe to run even if some referenced tables don't exist yet)
try:
    setup_sql_objects()
except Exception as ex:
    print("Could not complete SQL object setup (some tables might not exist yet):", ex)

# ----------------------- UTILITIES -----------------------
def show_status(msg):
    try:
        status_var.set(msg)
    except:
        pass

def export_tree_to_csv(tree, filename_prefix):
    rows = [tree.item(i)["values"] for i in tree.get_children()]
    if not rows:
        messagebox.showinfo("Export", "No data to export.")
        return
    file = filedialog.asksaveasfilename(defaultextension=".csv",
                                        initialfile=f"{filename_prefix}.csv",
                                        filetypes=[("CSV files", "*.csv")])
    if file:
        with open(file, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([tree.heading(c)["text"] for c in tree["columns"]])
            w.writerows(rows)
        messagebox.showinfo("Export", f"Exported to {file}")

# ----------------------- TABLE FRAME CLASS -----------------------
class TableFrame(ttk.Frame):
    def __init__(self, parent, table, columns, insert_q, update_q, delete_q, extra_buttons=None, sp_add=False):
        super().__init__(parent)
        self.table = table
        self.columns = columns
        self.insert_q = insert_q
        self.update_q = update_q
        self.delete_q = delete_q
        self.sp_add = sp_add

        ttk.Label(self, text=f"{table} Management", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=12, pady=(8,0))
        form = ttk.LabelFrame(self, text="Fields")
        form.pack(fill="x", padx=12, pady=8)
        self.entries = {}
        for c in columns:
            row = ttk.Frame(form); row.pack(fill="x", pady=2)
            ttk.Label(row, text=c, width=18).pack(side="left")
            e = ttk.Entry(row); e.pack(side="left", fill="x", expand=True)
            self.entries[c] = e

        btns = ttk.Frame(self); btns.pack(fill="x", padx=12, pady=6)
        ttk.Button(btns, text="Add", command=self.add_record).pack(side="left", padx=4)
        ttk.Button(btns, text="Update", command=self.update_record).pack(side="left", padx=4)
        ttk.Button(btns, text="Delete", command=self.delete_record).pack(side="left", padx=4)
        ttk.Button(btns, text="Refresh", command=self.fetch_data).pack(side="left", padx=4)
        if extra_buttons:
            for name, func in extra_buttons:
                ttk.Button(btns, text=name, command=func).pack(side="left", padx=4)

        frame = ttk.Frame(self); frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        self.tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        for c in columns:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=140, anchor="center")

        self.tree.bind("<ButtonRelease-1>", self.on_row_select)
        self.fetch_data()

    def fetch_data(self):
        try:
            cursor.execute(f"SELECT * FROM {self.table}")
            rows = cursor.fetchall()
        except mysql.connector.Error as e:
            rows = []
            print(f"Error fetching {self.table}: {e}")
        for r in self.tree.get_children(): self.tree.delete(r)
        for row in rows: self.tree.insert("", "end", values=row)
        show_status(f"{self.table}: {len(rows)} records loaded.")

    def add_record(self):
        vals = tuple(e.get() or None for e in self.entries.values())
        try:
            if self.sp_add and self.table == "Student":
                # Call stored procedure with the exact parameter order:
                # (Stu_ID, Name, Phone_No, Email, DOB, Gender, Clg_ID, Dept_ID)
                cursor.callproc("sp_AddNewStudent", vals)
            else:
                cursor.execute(self.insert_q, vals)
            conn.commit(); backup_database()
            self.fetch_data()
            messagebox.showinfo("Success", f"Record added to {self.table}.")
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def update_record(self):
        vals = [e.get() for e in self.entries.values()]
        # For update queries we expect queries to be written in the form that moves the key to the end.
        # Example update_q: "UPDATE Student SET Name=%s,... WHERE Stu_ID=%s"
        params = tuple(vals[1:] + vals[:1])
        try:
            cursor.execute(self.update_q, params)
            conn.commit(); backup_database()
            self.fetch_data()
            messagebox.showinfo("Updated", f"{self.table} record updated.")
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))

    def delete_record(self):
        sel = self.tree.focus()
        if not sel: return
        key = self.tree.item(sel)["values"][0]
        if not messagebox.askyesno("Confirm", f"Delete {self.table} ID {key}?"):
            return
        try:
            cursor.execute(self.delete_q, (key,))
            conn.commit(); backup_database()
            self.fetch_data()
            messagebox.showinfo("Deleted", f"{self.table} record deleted.")
        except mysql.connector.Error as e:
            messagebox.showerror("Error", str(e))

    def on_row_select(self, _):
        sel = self.tree.focus()
        if not sel: return
        vals = self.tree.item(sel)["values"]
        for i, c in enumerate(self.columns):
            self.entries[c].delete(0, "end")
            # If row shorter than columns (because SELECT * returns), guard it
            try:
                self.entries[c].insert(0, vals[i])
            except Exception:
                self.entries[c].insert(0, "")

# ----------------------- SPECIAL BUTTON FUNCTIONS -----------------------
def get_student_count():
    clg = college_tab.entries["Clg_ID"].get()
    if not clg:
        messagebox.showwarning("Input Required", "Enter College ID first.")
        return
    try:
        cursor.execute("SELECT fn_GetStudentCountByCollege_(%s)", (clg,))
        res = cursor.fetchone()
        total = res[0] if res else 0
        messagebox.showinfo("Student Count", f"Total Students: {total}")
    except mysql.connector.Error as e:
        messagebox.showerror("DB Error", f"Error while fetching count: {e}")

def get_students_by_dept():
    """
    New working implementation:
    - Reads Dept_Name from Department tab (Dept_Name field)
    - Calls stored procedure sp_GetStudentsByDepartment (created at startup)
    - Presents Name + Email in popup and allows CSV export
    """
    dept = dept_tab.entries["Dept_Name"].get().strip()
    if not dept:
        messagebox.showwarning("Input Required", "Enter Department Name first.")
        return

    try:
        # Call stored procedure
        cursor.callproc("sp_GetStudentsByDepartment", (dept,))
        result = []
        for r in cursor.stored_results():
            result.extend(r.fetchall())

        if not result:
            messagebox.showinfo("No Results", f"No students found for '{dept}'.")
            return

        # Popup window
        popup = tk.Toplevel(root)
        popup.title(f"Students in {dept}")
        popup.geometry("420x360")

        tv = ttk.Treeview(popup, columns=("Name", "Email"), show="headings")
        tv.heading("Name", text="Name")
        tv.heading("Email", text="Email")
        tv.column("Name", width=200, anchor="w")
        tv.column("Email", width=200, anchor="w")
        tv.pack(fill="both", expand=True, padx=10, pady=10)

        for row in result:
            tv.insert("", "end", values=row)

        ttk.Button(
            popup,
            text="Export CSV",
            command=lambda: export_tree_to_csv(tv, f"students_{dept}_{datetime.now().strftime('%Y%m%d')}")
        ).pack(pady=6)
    except mysql.connector.Error as e:
        messagebox.showerror("DB Error", f"Error while fetching students: {e}")

def get_hod():
    dept_input = course_tab.entries["Dept_ID"].get().strip()
    if not dept_input:
        messagebox.showwarning("Input Required", "Enter Department ID or Name.")
        return
    try:
        # Translate Dept_ID → Dept_Name if necessary
        cursor.execute("SELECT Dept_Name FROM Department WHERE Dept_ID = %s", (dept_input,))
        row = cursor.fetchone()
        dept_name = row[0] if row else dept_input
        cursor.execute("SELECT fn_GetDepartmenttHOD(%s)", (dept_name,))
        hod = cursor.fetchone()
        hod_name = hod[0] if hod and hod[0] else "No HOD found"
        messagebox.showinfo("HOD", f"HOD of '{dept_name}': {hod_name}")
    except mysql.connector.Error as e:
        messagebox.showerror("DB Error", f"Error while fetching HOD: {e}")



# ----------------------- GUI SETUP (wrapped in function) -----------------------
def open_main_app():
    global root, notebook, college_tab, dept_tab, prof_tab, course_tab, student_tab, status_var

    root = tk.Tk()
    root.title("College Management System — Final Version")
    root.geometry("1200x760")

    status_var = tk.StringVar(value="Ready")
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=8, pady=8)

    # ----------------------- HOME PAGE -----------------------
    home = tk.Frame(notebook, bg="#0b1226")
    home.pack(fill="both", expand=True)

    canvas = tk.Canvas(home, bg="#0b1226", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    # Accent panels
    canvas.create_rectangle(0, 0, 420, 2000, fill="#091327", outline="")          # left panel
    canvas.create_rectangle(440, 180, 1160, 540, fill="#0f172a", outline="#233044")  # main card

    # Logo (optional)
    if PIL_AVAILABLE:
        try:
            img = Image.open("college_logo.png").convert("RGBA").resize((140, 140))
            logo_img = ImageTk.PhotoImage(img)
            canvas.create_image(210, 110, image=logo_img)
        except Exception:
            canvas.create_text(210, 110, text="🏛️", font=("Segoe UI Emoji", 64), fill="#e6eef9")
    else:
        canvas.create_text(210, 110, text="🏛️", font=("Segoe UI Emoji", 64), fill="#e6eef9")

    # Title & subtitle
    canvas.create_text(700, 95, text="College Management System",
                       font=("Segoe UI Semibold", 30, "bold"), fill="#e6eef9")
    canvas.create_text(700, 135, text="Automated Academic & Administrative Dashboard",
                       font=("Segoe UI", 13), fill="#bcd0ff")

    # Team line
    canvas.create_text(700, 170, text="Developed by: Vikas V (PES2UG23CS689)  •  Vinaykumar N (PES2UG23CS694)",
                       font=("Segoe UI", 10), fill="#a8b9ff")

    # Card header text
    canvas.create_text(800, 210, text="Overview",
                       font=("Segoe UI", 16, "bold"), fill="#e6eef9")
    canvas.create_text(800, 240, text="Live stats fetched from the database",
                       font=("Segoe UI", 10), fill="#9fb1ff")

    # Helper to fetch stats
    def _fetch_stats():
        c = d = p = s = 0
        try:
            cursor.execute("SELECT COUNT(*) FROM College"); c = cursor.fetchone()[0]
        except: pass
        try:
            cursor.execute("SELECT COUNT(*) FROM Department"); d = cursor.fetchone()[0]
        except: pass
        try:
            cursor.execute("SELECT COUNT(*) FROM Professor"); p = cursor.fetchone()[0]
        except: pass
        try:
            cursor.execute("SELECT COUNT(*) FROM Student"); s = cursor.fetchone()[0]
        except: pass
        return c, d, p, s

    # Draw stat tiles inside the main card
    tile_w, tile_h = 280, 90
    start_x, start_y = 480, 280
    tile_gap_x, tile_gap_y = 28, 16

    _stat_items = []  # keep references to easily update text values

    def _draw_tiles():
        nonlocal _stat_items
        _stat_items.clear()
        labels = ["Colleges", "Departments", "Professors", "Students"]
        values = list(_fetch_stats())
        emojis = ["🏫", "🏛️", "👨‍🏫", "🎓"]

        for i, (label, val, emoji) in enumerate(zip(labels, values, emojis)):
            col = i % 2
            row = i // 2
            x = start_x + col * (tile_w + tile_gap_x)
            y = start_y + row * (tile_h + tile_gap_y)

            # tile background
            canvas.create_rectangle(x, y, x + tile_w, y + tile_h,
                                    fill="#0f293f", outline="#1f3a5a", width=1)
            # emoji
            canvas.create_text(x + 26, y + 30, text=emoji,
                               font=("Segoe UI Emoji", 18), anchor="w", fill="#aee0ff")
            # label
            canvas.create_text(x + 64, y + 28, text=label,
                               font=("Segoe UI", 10, "bold"), anchor="w", fill="#cfe6ff")
            # value (store id for refresh)
            val_id = canvas.create_text(x + 64, y + 54, text=str(val),
                                        font=("Segoe UI", 16, "bold"), anchor="w", fill="#ffffff")
            _stat_items.append((label, val_id))

    def _refresh_tiles():
        values = list(_fetch_stats())
        for i, (_, val_id) in enumerate(_stat_items):
            try:
                canvas.itemconfigure(val_id, text=str(values[i]))
            except:
                pass
        show_status("Stats refreshed.")

    _draw_tiles()

    # Buttons on card: Refresh Stats  &  Open Dashboard
    def _open_dashboard():
        notebook.select(college_tab)

    # Refresh button (canvas button)
    refresh_btn_tag = "refresh_btn"
    rx0, ry0, rx1, ry1 = 760, 480, 920, 520
    canvas.create_rectangle(rx0, ry0, rx1, ry1, fill="#1f3a8a", outline="#274690", tags=refresh_btn_tag)
    canvas.create_text((rx0+rx1)//2, (ry0+ry1)//2, text="Refresh Stats",
                       font=("Segoe UI Semibold", 11, "bold"), fill="#e6eef9", tags=refresh_btn_tag)
    canvas.tag_bind(refresh_btn_tag, "<Button-1>", lambda e: _refresh_tiles())

    # Primary button (canvas button)
    start_btn_tag = "start_btn"
    sx0, sy0, sx1, sy1 = 940, 480, 1120, 520
    canvas.create_rectangle(sx0, sy0, sx1, sy1, fill="#2563eb", outline="", tags=start_btn_tag)
    canvas.create_text((sx0+sx1)//2, (sy0+sy1)//2, text="Open Dashboard",
                       font=("Segoe UI Semibold", 11, "bold"), fill="white", tags=start_btn_tag)
    canvas.tag_bind(start_btn_tag, "<Button-1>", lambda e: _open_dashboard())

    # Footer
    canvas.create_text(700, 560, text="DBMS Mini Project • Live MySQL • CSV Export • Stored Procedures & Triggers",
                       font=("Segoe UI", 9), fill="#89a2ff")

    notebook.add(home, text="Home")

    # ----------------------- DATABASE TABS -----------------------
    def add_tab(title, cols, ins, upd, dele, extra=None, sp_add=False):
        frame = TableFrame(notebook, title, cols, ins, upd, dele, extra, sp_add)
        notebook.add(frame, text=title)
        return frame

    college_tab = add_tab("College",
        ["Clg_ID","Clg_Name","Address"],
        "INSERT INTO College VALUES(%s,%s,%s)",
        "UPDATE College SET Clg_Name=%s,Address=%s WHERE Clg_ID=%s",
        "DELETE FROM College WHERE Clg_ID=%s",
        [("Count Students", get_student_count)]
    )

    dept_tab = add_tab("Department",
        ["Dept_ID","Dept_Name","HOD"],
        "INSERT INTO Department VALUES(%s,%s,%s)",
        "UPDATE Department SET Dept_Name=%s,HOD=%s WHERE Dept_ID=%s",
        "DELETE FROM Department WHERE Dept_ID=%s",
        [("Get Students", get_students_by_dept)]
    )

    prof_tab = add_tab("Professor",
        ["Prof_ID","Name","Phone_No","Email","Address","Dept_ID"],
        "INSERT INTO Professor VALUES(%s,%s,%s,%s,%s,%s)",
        "UPDATE Professor SET Name=%s,Phone_No=%s,Email=%s,Address=%s,Dept_ID=%s WHERE Prof_ID=%s",
        "DELETE FROM Professor WHERE Prof_ID=%s"
    )

    course_tab = add_tab("Course",
        ["Course_ID","Course_Name","Credits","Dept_ID"],
        "INSERT INTO Course VALUES(%s,%s,%s,%s)",
        "UPDATE Course SET Course_Name=%s,Credits=%s,Dept_ID=%s WHERE Course_ID=%s",
        "DELETE FROM Course WHERE Course_ID=%s",
        [("Get HOD", get_hod)]
    )

    # Student tab now includes Dept_ID as requested
    student_tab = add_tab("Student",
        ["Stu_ID","Name","Phone_No","Email","DOB","Gender","Clg_ID","Dept_ID"],
        "INSERT INTO Student VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
        "UPDATE Student SET Name=%s,Phone_No=%s,Email=%s,DOB=%s,Gender=%s,Clg_ID=%s,Dept_ID=%s WHERE Stu_ID=%s",
        "DELETE FROM Student WHERE Stu_ID=%s",
        sp_add=True
    )

    
# ----------------------- ADMIN LOGIN PAGE -----------------------
def admin_login():
    login = tk.Tk()
    login.title("Admin Login")
    login.geometry("420x260")
    login.configure(bg="#0b1226")

    tk.Label(login, text="ADMIN LOGIN", font=("Segoe UI", 18, "bold"), bg="#0b1226", fg="white").pack(pady=18)

    f = ttk.Frame(login)
    f.pack(pady=6, padx=12, fill="x")

    ttk.Label(f, text="Username:", font=("Segoe UI", 11)).pack(anchor="w")
    username_entry = ttk.Entry(f, font=("Segoe UI", 12))
    username_entry.pack(fill="x", pady=6)

    ttk.Label(f, text="Password:", font=("Segoe UI", 11)).pack(anchor="w")
    password_entry = ttk.Entry(f, font=("Segoe UI", 12), show="*")
    password_entry.pack(fill="x", pady=6)

    def validate_login():
        u = username_entry.get().strip()
        p = password_entry.get().strip()

        if u == "Miniproject" and p == "DBMS":
            messagebox.showinfo("Login Success", "Welcome Admin!")
            login.destroy()
            open_main_app()     # Launch your full GUI
        else:
            messagebox.showerror("Login Failed", "Invalid Username or Password.")

    btn = ttk.Button(login, text="Login", command=validate_login)
    btn.pack(pady=12)

    # allow pressing Enter to submit
    login.bind('<Return>', lambda event: validate_login())

    login.mainloop()

# ----------------------- START APPLICATION -----------------------
if __name__ == "__main__":
    admin_login()
