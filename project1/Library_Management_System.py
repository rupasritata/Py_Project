import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime, timedelta

DATA_FILE = "library_gui_data.json"


# ----------------- Data Models -----------------

class Book:
    def __init__(self, book_id, title, author, total_copies, category="General"):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.total_copies = total_copies
        self.available_copies = total_copies
        self.category = category

    def to_dict(self):
        return {
            "book_id": self.book_id,
            "title": self.title,
            "author": self.author,
            "total_copies": self.total_copies,
            "available_copies": self.available_copies,
            "category": self.category,
        }

    @staticmethod
    def from_dict(d):
        b = Book(
            d["book_id"],
            d["title"],
            d["author"],
            d["total_copies"],
            d.get("category", "General"),
        )
        b.available_copies = d.get("available_copies", d["total_copies"])
        return b


class Member:
    def __init__(self, member_id, name, borrowed_books=None):
        self.member_id = member_id
        self.name = name
        # list of dicts: {book_id, issue_date, due_date}
        self.borrowed_books = borrowed_books or []

    def to_dict(self):
        return {
            "member_id": self.member_id,
            "name": self.name,
            "borrowed_books": self.borrowed_books,
        }

    @staticmethod
    def from_dict(d):
        return Member(d["member_id"], d["name"], d.get("borrowed_books", []))


class Library:
    def __init__(self):
        self.books = {}    # id -> Book
        self.members = {}  # id -> Member
        self.next_book_id = 1
        self.next_member_id = 1

    # ---- Basic operations ----

    def add_book(self, title, author, total_copies, category="General"):
        book = Book(self.next_book_id, title, author, total_copies, category)
        self.books[self.next_book_id] = book
        self.next_book_id += 1
        return book

    def add_member(self, name):
        member = Member(self.next_member_id, name)
        self.members[self.next_member_id] = member
        self.next_member_id += 1
        return member

    def issue_book(self, member_id, book_id):
        member = self.members.get(member_id)
        book = self.books.get(book_id)

        if member is None:
            raise ValueError("Invalid member ID")
        if book is None:
            raise ValueError("Invalid book ID")
        if book.available_copies <= 0:
            raise ValueError("No copies available")
        for item in member.borrowed_books:
            if item["book_id"] == book_id:
                raise ValueError("Member already borrowed this book")

        book.available_copies -= 1
        issue_date = datetime.today()
        due_date = issue_date + timedelta(days=14)

        member.borrowed_books.append({
            "book_id": book_id,
            "issue_date": issue_date.strftime("%Y-%m-%d"),
            "due_date": due_date.strftime("%Y-%m-%d"),
        })
        return issue_date, due_date

    def return_book(self, member_id, book_id, fine_per_day=2):
        member = self.members.get(member_id)
        book = self.books.get(book_id)

        if member is None:
            raise ValueError("Invalid member ID")
        if book is None:
            raise ValueError("Invalid book ID")

        record = None
        for item in member.borrowed_books:
            if item["book_id"] == book_id:
                record = item
                break

        if record is None:
            raise ValueError("This member did not borrow that book")

        member.borrowed_books.remove(record)
        book.available_copies += 1

        due_date = datetime.strptime(record["due_date"], "%Y-%m-%d")
        today = datetime.today()
        days_late = max(0, (today - due_date).days)
        fine = days_late * fine_per_day
        return days_late, fine

    # ---- Save / Load ----

    def save(self, filename=DATA_FILE):
        data = {
            "books": [b.to_dict() for b in self.books.values()],
            "members": [m.to_dict() for m in self.members.values()],
            "next_book_id": self.next_book_id,
            "next_member_id": self.next_member_id,
        }
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

    def load(self, filename=DATA_FILE):
        try:
            with open(filename) as f:
                data = json.load(f)
        except FileNotFoundError:
            return

        self.books = {b["book_id"]: Book.from_dict(b) for b in data.get("books", [])}
        self.members = {m["member_id"]: Member.from_dict(m) for m in data.get("members", [])}
        self.next_book_id = data.get("next_book_id", 1)
        self.next_member_id = data.get("next_member_id", 1)


# ----------------- Tkinter GUI -----------------

class LibraryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Library Management System")
        self.geometry("900x550")

        self.library = Library()
        self.library.load()

        self.current_role = None  # "admin" or "student"

        # for selection
        self.selected_book_id = None
        self.selected_member_id = None

        self.create_widgets()
        self.refresh_books()
        self.refresh_members()

        # Save automatically on close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # show login dialog
        self.show_login_dialog()

    # ---------- Login System ----------

    def show_login_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Login")
        dialog.geometry("300x250")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        role_var = tk.StringVar(value="student")
        username_var = tk.StringVar()
        password_var = tk.StringVar()

        ttk.Label(dialog, text="Select Role:").pack(pady=(15, 5))
        role_frame = ttk.Frame(dialog)
        role_frame.pack()
        ttk.Radiobutton(role_frame, text="Student", value="student", variable=role_var).pack(side="left", padx=5)
        ttk.Radiobutton(role_frame, text="Admin", value="admin", variable=role_var).pack(side="left", padx=5)

        ttk.Label(dialog, text="Username:").pack(pady=(15, 2))
        ttk.Entry(dialog, textvariable=username_var).pack(padx=20, fill="x")

        ttk.Label(dialog, text="Password:").pack(pady=(10, 2))
        ttk.Entry(dialog, textvariable=password_var, show="*").pack(padx=20, fill="x")

        def handle_login():
            role = role_var.get()
            u = username_var.get().strip()
            p = password_var.get().strip()

            # simple hard-coded credentials
            if role == "admin" and u == "admin" and p == "admin123":
                self.current_role = "admin"
                messagebox.showinfo("Login", "Logged in as Admin", parent=dialog)
                dialog.destroy()
                self.apply_role_permissions()
            elif role == "student" and u == "student" and p == "student123":
                self.current_role = "student"
                messagebox.showinfo("Login", "Logged in as Student", parent=dialog)
                dialog.destroy()
                self.apply_role_permissions()
            else:
                messagebox.showerror("Login Failed", "Invalid username/password", parent=dialog)

        ttk.Button(dialog, text="Login", command=handle_login).pack(pady=15)

    def apply_role_permissions(self):
        # Students cannot add/update/delete books or members
        is_student = (self.current_role == "student")
        state = "disabled" if is_student else "normal"

        for btn in [
            self.add_book_btn,
            self.update_book_btn,
            self.delete_book_btn,
            self.add_member_btn,
            self.update_member_btn,
            self.delete_member_btn,
        ]:
            btn["state"] = state

    # ---------- Widgets ----------

    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.books_frame = ttk.Frame(notebook)
        self.members_frame = ttk.Frame(notebook)
        self.issue_frame = ttk.Frame(notebook)

        notebook.add(self.books_frame, text="Books")
        notebook.add(self.members_frame, text="Members")
        notebook.add(self.issue_frame, text="Issue / Return")

        # ----- Books Tab -----
        form = ttk.Frame(self.books_frame)
        form.pack(fill="x", pady=5)

        ttk.Label(form, text="Title:").grid(row=0, column=0, sticky="w", padx=2, pady=2)
        self.title_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.title_var, width=25).grid(row=0, column=1, padx=2)

        ttk.Label(form, text="Author:").grid(row=0, column=2, sticky="w", padx=2)
        self.author_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.author_var, width=20).grid(row=0, column=3, padx=2)

        ttk.Label(form, text="Category:").grid(row=0, column=4, sticky="w", padx=2)
        self.category_var = tk.StringVar(value="General")
        ttk.Combobox(
            form,
            textvariable=self.category_var,
            values=[
                "General",
                "Fiction",
                "Non-Fiction",
                "Science",
                "Technology",
                "History",
                "Comics",
                "Other",
            ],
            state="readonly",
            width=15,
        ).grid(row=0, column=5, padx=2)

        ttk.Label(form, text="Copies:").grid(row=0, column=6, sticky="w", padx=2)
        self.copies_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.copies_var, width=6).grid(row=0, column=7, padx=2)

        self.add_book_btn = ttk.Button(form, text="Add Book", command=self.add_book)
        self.add_book_btn.grid(row=0, column=8, padx=8)

        # search + update/delete row
        ttk.Label(form, text="Search:").grid(row=1, column=0, sticky="w", padx=2, pady=(4, 2))
        self.book_search_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.book_search_var, width=25).grid(row=1, column=1, padx=2, pady=(4, 2))
        ttk.Button(form, text="Search", command=self.search_books).grid(row=1, column=2, padx=2, pady=(4, 2))
        ttk.Button(form, text="Show All", command=self.refresh_books).grid(row=1, column=3, padx=2, pady=(4, 2))

        self.update_book_btn = ttk.Button(form, text="Update Selected", command=self.update_book)
        self.update_book_btn.grid(row=1, column=5, padx=4, pady=(4, 2))
        self.delete_book_btn = ttk.Button(form, text="Delete Selected", command=self.delete_book)
        self.delete_book_btn.grid(row=1, column=6, padx=4, pady=(4, 2))

        self.books_tree = ttk.Treeview(
            self.books_frame,
            columns=("id", "title", "author", "category", "avail"),
            show="headings",
        )
        self.books_tree.heading("id", text="ID")
        self.books_tree.heading("title", text="Title")
        self.books_tree.heading("author", text="Author")
        self.books_tree.heading("category", text="Category")
        self.books_tree.heading("avail", text="Available/Total")

        self.books_tree.column("id", width=40, anchor="center")
        self.books_tree.column("title", width=220)
        self.books_tree.column("author", width=140)
        self.books_tree.column("category", width=110, anchor="center")
        self.books_tree.column("avail", width=110, anchor="center")

        self.books_tree.pack(fill="both", expand=True, pady=5)
        self.books_tree.bind("<<TreeviewSelect>>", self.on_book_select)

        # ----- Members Tab -----
        mform = ttk.Frame(self.members_frame)
        mform.pack(fill="x", pady=5)

        ttk.Label(mform, text="Name:").grid(row=0, column=0, sticky="w", padx=2, pady=2)
        self.member_name_var = tk.StringVar()
        ttk.Entry(mform, textvariable=self.member_name_var, width=25).grid(row=0, column=1, padx=2)

        self.add_member_btn = ttk.Button(mform, text="Add Member", command=self.add_member)
        self.add_member_btn.grid(row=0, column=2, padx=8)

        ttk.Label(mform, text="Search:").grid(row=1, column=0, sticky="w", padx=2, pady=(4, 2))
        self.member_search_var = tk.StringVar()
        ttk.Entry(mform, textvariable=self.member_search_var, width=25).grid(row=1, column=1, padx=2, pady=(4, 2))
        ttk.Button(mform, text="Search", command=self.search_members).grid(row=1, column=2, padx=2, pady=(4, 2))
        ttk.Button(mform, text="Show All", command=self.refresh_members).grid(row=1, column=3, padx=2, pady=(4, 2))

        self.update_member_btn = ttk.Button(mform, text="Update Selected", command=self.update_member)
        self.update_member_btn.grid(row=1, column=4, padx=4, pady=(4, 2))
        self.delete_member_btn = ttk.Button(mform, text="Delete Selected", command=self.delete_member)
        self.delete_member_btn.grid(row=1, column=5, padx=4, pady=(4, 2))

        self.members_tree = ttk.Treeview(
            self.members_frame,
            columns=("id", "name", "borrowed"),
            show="headings",
        )
        self.members_tree.heading("id", text="ID")
        self.members_tree.heading("name", text="Name")
        self.members_tree.heading("borrowed", text="Borrowed Books")

        self.members_tree.column("id", width=40, anchor="center")
        self.members_tree.column("name", width=200)
        self.members_tree.column("borrowed", width=320)

        self.members_tree.pack(fill="both", expand=True, pady=5)
        self.members_tree.bind("<<TreeviewSelect>>", self.on_member_select)

        # ----- Issue / Return Tab -----
        iframe = ttk.Frame(self.issue_frame)
        iframe.pack(fill="x", pady=10)

        ttk.Label(iframe, text="Member ID:").grid(row=0, column=0, sticky="w")
        self.issue_member_var = tk.StringVar()
        ttk.Entry(iframe, textvariable=self.issue_member_var, width=10).grid(row=0, column=1, padx=5)

        ttk.Label(iframe, text="Book ID:").grid(row=0, column=2, sticky="w")
        self.issue_book_var = tk.StringVar()
        ttk.Entry(iframe, textvariable=self.issue_book_var, width=10).grid(row=0, column=3, padx=5)

        ttk.Button(iframe, text="Issue Book", command=self.issue_book).grid(row=0, column=4, padx=10)
        ttk.Button(iframe, text="Return Book", command=self.return_book).grid(row=0, column=5, padx=10)

        self.log_text = tk.Text(self.issue_frame, height=15)
        self.log_text.pack(fill="both", expand=True, pady=5)

    # ----- Books -----

    def add_book(self):
        title = self.title_var.get().strip()
        author = self.author_var.get().strip()
        category = self.category_var.get().strip()
        copies_str = self.copies_var.get().strip()

        if not title or not author or not copies_str:
            messagebox.showerror("Error", "Please fill all book fields")
            return

        try:
            copies = int(copies_str)
            if copies <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Copies must be a positive integer")
            return

        book = self.library.add_book(title, author, copies, category)
        self.refresh_books()

        self.title_var.set("")
        self.author_var.set("")
        self.copies_var.set("")
        self.category_var.set("General")

        messagebox.showinfo("Success", f"Book added with ID {book.book_id}")

    def refresh_books(self):
        for row in self.books_tree.get_children():
            self.books_tree.delete(row)

        for b in self.library.books.values():
            self.books_tree.insert(
                "",
                "end",
                values=(
                    b.book_id,
                    b.title,
                    b.author,
                    b.category,
                    f"{b.available_copies}/{b.total_copies}",
                ),
            )

    def search_books(self):
        keyword = self.book_search_var.get().strip().lower()
        for row in self.books_tree.get_children():
            self.books_tree.delete(row)

        if not keyword:
            self.refresh_books()
            return

        for b in self.library.books.values():
            if (
                keyword in b.title.lower()
                or keyword in b.author.lower()
                or keyword == str(b.book_id)
            ):
                self.books_tree.insert(
                    "",
                    "end",
                    values=(
                        b.book_id,
                        b.title,
                        b.author,
                        b.category,
                        f"{b.available_copies}/{b.total_copies}",
                    ),
                )

    def on_book_select(self, event):
        selected = self.books_tree.selection()
        if not selected:
            self.selected_book_id = None
            return
        values = self.books_tree.item(selected[0], "values")
        try:
            self.selected_book_id = int(values[0])
        except (ValueError, IndexError):
            self.selected_book_id = None
            return

        book = self.library.books.get(self.selected_book_id)
        if book:
            self.title_var.set(book.title)
            self.author_var.set(book.author)
            self.copies_var.set(str(book.total_copies))
            self.category_var.set(book.category)

    def update_book(self):
        if self.selected_book_id is None:
            messagebox.showerror("Error", "Please select a book to update")
            return

        book = self.library.books.get(self.selected_book_id)
        if not book:
            messagebox.showerror("Error", "Selected book not found")
            return

        title = self.title_var.get().strip()
        author = self.author_var.get().strip()
        category = self.category_var.get().strip()
        copies_str = self.copies_var.get().strip()

        if not title or not author or not copies_str:
            messagebox.showerror("Error", "Please fill all book fields")
            return

        try:
            new_total = int(copies_str)
            if new_total <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Copies must be a positive integer")
            return

        # update book fields
        book.title = title
        book.author = author
        book.category = category

        diff = new_total - book.total_copies
        book.total_copies = new_total
        book.available_copies += diff
        if book.available_copies < 0:
            book.available_copies = 0

        self.refresh_books()
        messagebox.showinfo("Success", "Book updated successfully")

    def delete_book(self):
        if self.selected_book_id is None:
            messagebox.showerror("Error", "Please select a book to delete")
            return

        book = self.library.books.get(self.selected_book_id)
        if not book:
            messagebox.showerror("Error", "Selected book not found")
            return

        if book.available_copies != book.total_copies:
            messagebox.showerror("Error", "Cannot delete book. Some copies are issued.")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete this book?"):
            del self.library.books[self.selected_book_id]
            self.selected_book_id = None
            self.refresh_books()
            messagebox.showinfo("Success", "Book deleted successfully")

    # ----- Members -----

    def add_member(self):
        name = self.member_name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter member name")
            return

        m = self.library.add_member(name)
        self.refresh_members()

        self.member_name_var.set("")
        messagebox.showinfo("Success", f"Member added with ID {m.member_id}")

    def refresh_members(self):
        for row in self.members_tree.get_children():
            self.members_tree.delete(row)

        for m in self.library.members.values():
            borrowed_ids = [str(item["book_id"]) for item in m.borrowed_books]
            borrowed_str = ", ".join(borrowed_ids) if borrowed_ids else "-"
            self.members_tree.insert(
                "",
                "end",
                values=(
                    m.member_id,
                    m.name,
                    borrowed_str,
                ),
            )

    def search_members(self):
        keyword = self.member_search_var.get().strip().lower()
        for row in self.members_tree.get_children():
            self.members_tree.delete(row)

        if not keyword:
            self.refresh_members()
            return

        for m in self.library.members.values():
            if (
                keyword in m.name.lower()
                or keyword == str(m.member_id)
            ):
                borrowed_ids = [str(item["book_id"]) for item in m.borrowed_books]
                borrowed_str = ", ".join(borrowed_ids) if borrowed_ids else "-"
                self.members_tree.insert(
                    "",
                    "end",
                    values=(
                        m.member_id,
                        m.name,
                        borrowed_str,
                    ),
                )

    def on_member_select(self, event):
        selected = self.members_tree.selection()
        if not selected:
            self.selected_member_id = None
            return
        values = self.members_tree.item(selected[0], "values")
        try:
            self.selected_member_id = int(values[0])
        except (ValueError, IndexError):
            self.selected_member_id = None
            return

        member = self.library.members.get(self.selected_member_id)
        if member:
            self.member_name_var.set(member.name)

    def update_member(self):
        if self.selected_member_id is None:
            messagebox.showerror("Error", "Please select a member to update")
            return

        member = self.library.members.get(self.selected_member_id)
        if not member:
            messagebox.showerror("Error", "Selected member not found")
            return

        name = self.member_name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter member name")
            return

        member.name = name
        self.refresh_members()
        messagebox.showinfo("Success", "Member updated successfully")

    def delete_member(self):
        if self.selected_member_id is None:
            messagebox.showerror("Error", "Please select a member to delete")
            return

        member = self.library.members.get(self.selected_member_id)
        if not member:
            messagebox.showerror("Error", "Selected member not found")
            return

        if member.borrowed_books:
            messagebox.showerror("Error", "Cannot delete member. They still have borrowed books.")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete this member?"):
            del self.library.members[self.selected_member_id]
            self.selected_member_id = None
            self.refresh_members()
            messagebox.showinfo("Success", "Member deleted successfully")

    # ----- Issue / Return -----

    def issue_book(self):
        mid = self.issue_member_var.get().strip()
        bid = self.issue_book_var.get().strip()

        try:
            member_id = int(mid)
            book_id = int(bid)
        except ValueError:
            messagebox.showerror("Error", "IDs must be integers")
            return

        try:
            issue_date, due_date = self.library.issue_book(member_id, book_id)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        self.refresh_books()
        self.refresh_members()

        msg = (
            f"Issued book {book_id} to member {member_id} "
            f"on {issue_date.strftime('%Y-%m-%d')}, "
            f"due {due_date.strftime('%Y-%m-%d')}\n"
        )
        self.log_text.insert("end", msg)
        self.log_text.see("end")

    def return_book(self):
        mid = self.issue_member_var.get().strip()
        bid = self.issue_book_var.get().strip()

        try:
            member_id = int(mid)
            book_id = int(bid)
        except ValueError:
            messagebox.showerror("Error", "IDs must be integers")
            return

        try:
            days_late, fine = self.library.return_book(member_id, book_id)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        self.refresh_books()
        self.refresh_members()

        if days_late > 0:
            msg = (
                f"Returned book {book_id} from member {member_id}. "
                f"Late by {days_late} day(s). Fine: ₹{fine}\n"
            )
        else:
            msg = (
                f"Returned book {book_id} from member {member_id}. No fine.\n"
            )

        self.log_text.insert("end", msg)
        self.log_text.see("end")

    # ----- Closing -----

    def on_close(self):
        # Save data before closing
        self.library.save()
        self.destroy()


if __name__ == "__main__":
    app = LibraryApp()
    app.mainloop()
