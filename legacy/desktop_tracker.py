import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import json
import os
import datetime
import csv

class HighSchoolTracker:
    def __init__(self):
        self.users = {}
        self.load_data()

    def save_data(self):
        try:
            with open('tracker_data.json', 'w') as file:
                json.dump(self.users, file)
        except Exception as e:
            print(f"Error saving data: {e}")

    def load_data(self):
        try:
            if os.path.exists('tracker_data.json'):
                with open('tracker_data.json', 'r') as file:
                    file_content = file.read()
                    if file_content:
                        self.users = json.loads(file_content)
                    else:
                        self.users = {}
            else:
                self.users = {}
        except Exception as e:
            print(f"Error loading data: {e}")
            self.users = {}

    def add_user(self, username):
        if username not in self.users:
            self.users[username] = {
                "Awards & Honors": [],
                "Professional Experiences": [],
                "Summer Programs": [],
                "SAT/ACT/SATII/ACTII Scores": [],
                "AP Scores": [],
                "GPA": [],
                "Future Plans & Competitions": [],
                "Personal Goals": [],
                "Reflection Journal": []
            }
            self.save_data()
            print(f"User '{username}' created successfully.")
        else:
            print("Username already exists.")

    def add_entry(self, username, category, date, details):
        if username in self.users and category in self.users[username]:
            try:
                datetime_obj = datetime.datetime.strptime(date, "%m/%d/%Y")
                entry = f"{date}: {details}"
                self.users[username][category].append(entry)
                self.users[username][category].sort(key=lambda x: datetime.datetime.strptime(x.split(":")[0], "%m/%d/%Y"))
                self.save_data()
            except ValueError:
                print("Invalid date format. Please use MM/DD/YYYY.")
        else:
            print("Invalid username or category.")

    def view_entries(self, username, category):
        if username in self.users and category in self.users[username]:
            return "\n".join(self.users[username][category])
        else:
            return "Invalid username or category."

    def delete_entry(self, username, category, entry_index):
        if username in self.users and category in self.users[username]:
            try:
                del self.users[username][category][entry_index]
                self.save_data()
                return True
            except IndexError:
                return False
        return False

class HighSchoolTrackerApp:
    def __init__(self, root):
        self.tracker = HighSchoolTracker()
        self.root = root
        self.root.title("ScholarPath")
        self.root.configure(bg='#0077B6')

        self.label_font = ('Times New Roman', 20, 'bold')
        self.button_font = ('Times New Roman', 16, 'bold')
        self.button_color = '#FFD700'
        self.entry_font = ('Times New Roman', 16)
        self.listbox_font = ('Times New Roman', 16)
        self.title_font = ('Times New Roman', 28, 'italic', 'underline')
        self.border_color = '#0A1931'

        tk.Label(root, text="ScholarPath", bg='#0077B6', fg=self.border_color, font=self.title_font).pack(pady=20)

        frame1 = tk.Frame(root, bg='#0077B6')
        frame1.pack(pady=15)
        tk.Label(frame1, text="Enter your username:", bg='#0077B6', fg=self.border_color, font=self.label_font).pack(side=tk.LEFT, padx=10)
        self.username_entry = tk.Entry(frame1, font=self.entry_font, width=30)
        self.username_entry.pack(side=tk.LEFT, padx=10)
        tk.Button(frame1, text="Login", command=self.login, bg=self.button_color, font=self.button_font).pack(side=tk.LEFT, padx=10)

        self.category_listbox = tk.Listbox(root, font=self.listbox_font, width=60, height=10, borderwidth=2, relief="groove")
        self.category_listbox.pack(pady=15)

        self.entries_listbox = tk.Listbox(root, font=self.listbox_font, width=60, height=10, borderwidth=2, relief="groove")
        self.entries_listbox.pack(pady=15)

        frame2 = tk.Frame(root, bg='#0077B6')
        frame2.pack(pady=15)
        tk.Button(frame2, text="Add Entry", command=self.add_entry, bg=self.button_color, font=self.button_font).pack(side=tk.LEFT, padx=15)
        tk.Button(frame2, text="View Entries", command=self.view_entries, bg=self.button_color, font=self.button_font).pack(side=tk.LEFT, padx=15)
        tk.Button(frame2, text="Delete Entry", command=self.delete_entry, bg=self.button_color, font=self.button_font).pack(side=tk.LEFT, padx=15)
        tk.Button(frame2, text="Search Entries", command=self.search_entries, bg=self.button_color, font=self.button_font).pack(side=tk.LEFT, padx=15)
        tk.Button(frame2, text="Export Data", command=self.export_data, bg=self.button_color, font=self.button_font).pack(side=tk.LEFT, padx=15)
        tk.Button(frame2, text="Logout", command=self.logout, bg=self.button_color, font=self.button_font).pack(side=tk.LEFT, padx=15)

        self.current_category = None

    def login(self):
        username = self.username_entry.get()
        if username:
            if username not in self.tracker.users:
                create_user = messagebox.askyesno("User Not Found", "Username not found. Do you want to create a new user?")
                if create_user:
                    self.tracker.add_user(username)
                else:
                    return
            self.current_user = username
            self.update_category_list()

    def logout(self):
        self.current_user = None
        self.category_listbox.delete(0, tk.END)
        self.entries_listbox.delete(0, tk.END)
        self.username_entry.delete(0, tk.END)

    def update_category_list(self):
        self.category_listbox.delete(0, tk.END)
        self.entries_listbox.delete(0, tk.END)
        if self.current_user:
            for category in self.tracker.users[self.current_user].keys():
                self.category_listbox.insert(tk.END, category)

    def view_entries(self):
        category = self.get_selected_category()
        if category:
            self.current_category = category
            self.entries_listbox.delete(0, tk.END)
            for entry in self.tracker.users[self.current_user][category]:
                self.entries_listbox.insert(tk.END, entry)

    def add_entry(self):
        category = self.get_selected_category()
        if category:
            date = simpledialog.askstring("Input", "Enter the date (MM/DD/YYYY):")
            if not self.validate_date(date):
                messagebox.showerror("Invalid Date", "Please enter a valid date in MM/DD/YYYY format.")
                return

            if category in ["Personal Goals", "Reflection Journal"]:
                details = simpledialog.askstring("Input", f"Enter the details for {category}:")
                if date and details:
                    self.tracker.add_entry(self.current_user, category, date, details)
            elif category == "AP Scores":
                ap_exam = simpledialog.askstring("Input", "Enter the AP exam:")
                score = simpledialog.askstring("Input", "Enter the score:")
                if date and ap_exam and score:
                    details = f"{ap_exam} - {score}"
                    self.tracker.add_entry(self.current_user, category, date, details)
            else:
                details = simpledialog.askstring("Input", f"Enter the details for {category}:")
                if date and details:
                    self.tracker.add_entry(self.current_user, category, date, details)

    def delete_entry(self):
        if self.current_category:
            selected_index = self.entries_listbox.curselection()
            if selected_index:
                entry_index = selected_index[0]
                success = self.tracker.delete_entry(self.current_user, self.current_category, entry_index)
                if success:
                    messagebox.showinfo("Success", "Entry deleted successfully.")
                    self.view_entries()
                else:
                    messagebox.showerror("Error", "Failed to delete entry.")
            else:
                messagebox.showwarning("No Selection", "Please select an entry to delete.")
        else:
            messagebox.showwarning("No Category", "Please select and view a category first.")

    def get_selected_category(self):
        try:
            selected_index = self.category_listbox.curselection()[0]
            return self.category_listbox.get(selected_index)
        except IndexError:
            messagebox.showwarning("No Selection", "Please select a category.")
            return None

    def validate_date(self, date_str):
        """Validate the date format."""
        try:
            datetime.datetime.strptime(date_str, "%m/%d/%Y")
            return True
        except ValueError:
            return False

    def search_entries(self):
        """Search for entries based on user input."""
        search_term = simpledialog.askstring("Search", "Enter search term:")
        if search_term:
            self.entries_listbox.delete(0, tk.END)
            for entry in self.tracker.users[self.current_user][self.current_category]:
                if search_term.lower() in entry.lower():
                    self.entries_listbox.insert(tk.END, entry)

    def export_data(self):
        """Export user data to a CSV file."""
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if filename:
            with open(filename, 'w', newline='') as file:
                writer = csv.writer(file)
                for category, entries in self.tracker.users[self.current_user].items():
                    writer.writerow([category])
                    for entry in entries:
                        writer.writerow([entry])
                    writer.writerow([])  
            messagebox.showinfo("Export Successful", f"Data exported to {filename}")

def main():
    root = tk.Tk()
    app = HighSchoolTrackerApp(root)
    root.geometry("1000x800")
    root.mainloop()

if __name__ == "__main__":
    main()
