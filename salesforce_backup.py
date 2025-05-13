import os
import json
import pandas as pd
from simple_salesforce import Salesforce, SalesforceLogin, SFType
from getpass import getpass
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue

class SalesforceBackupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Salesforce Backup Tool")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        self.sf = None
        self.available_objects = []
        self.selected_objects_set = set()  # Track selected objects
        self.backup_thread = None
        self.stop_event = threading.Event()
        
        self.setup_ui()
        
    def setup_ui(self):
        # Configure style
        style = ttk.Style()
        style.configure('TButton', padding=5)
        style.configure('TLabel', padding=5)
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Credentials Frame
        cred_frame = ttk.LabelFrame(main_frame, text="Salesforce Credentials", padding="10")
        cred_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(cred_frame, text="Username:").grid(row=0, column=0, sticky=tk.W)
        self.username_var = tk.StringVar()
        ttk.Entry(cred_frame, textvariable=self.username_var, width=40).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(cred_frame, text="Password:").grid(row=1, column=0, sticky=tk.W)
        self.password_var = tk.StringVar()
        ttk.Entry(cred_frame, textvariable=self.password_var, show="*", width=40).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(cred_frame, text="Security Token:").grid(row=2, column=0, sticky=tk.W)
        self.token_var = tk.StringVar()
        ttk.Entry(cred_frame, textvariable=self.token_var, show="*", width=40).grid(row=2, column=1, sticky=tk.W, padx=5)
        
        self.sandbox_var = tk.BooleanVar()
        ttk.Checkbutton(cred_frame, text="Sandbox", variable=self.sandbox_var).grid(row=0, column=2, padx=10)
        
        self.connect_btn = ttk.Button(cred_frame, text="Connect", command=self.connect_to_salesforce)
        self.connect_btn.grid(row=2, column=2, padx=5)
        
        # Objects Frame
        obj_frame = ttk.LabelFrame(main_frame, text="Available Objects", padding="10")
        obj_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Search
        search_frame = ttk.Frame(obj_frame)
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_objects)
        ttk.Entry(search_frame, textvariable=self.search_var, width=40).pack(side=tk.LEFT, padx=5)
        
        # Objects Listbox with Scrollbar
        list_frame = ttk.Frame(obj_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.objects_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, 
                                         activestyle='none', font=('Arial', 10))
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.objects_listbox.yview)
        self.objects_listbox.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.objects_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add binding for selection change
        self.objects_listbox.bind('<<ListboxSelect>>', lambda e: self.update_selected_display())
        
        # Selected Objects Display
        selected_frame = ttk.LabelFrame(obj_frame, text="Selected Objects", padding="5")
        selected_frame.pack(fill=tk.X, pady=5)
        
        self.selected_objects_var = tk.StringVar(value="Selected: None")
        ttk.Label(selected_frame, textvariable=self.selected_objects_var, wraplength=800).pack(fill=tk.X)
        
        # Select All/None buttons
        btn_frame = ttk.Frame(obj_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Select All", command=self.select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Selection", command=self.clear_selection).pack(side=tk.LEFT, padx=5)
        
        # Output Frame
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=10, wrap=tk.WORD)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Buttons Frame
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        self.backup_btn = ttk.Button(action_frame, text="Start Backup", command=self.start_backup, state=tk.DISABLED)
        self.backup_btn.pack(side=tk.RIGHT, padx=5)
        
        self.stop_btn = ttk.Button(action_frame, text="Stop", command=self.stop_backup, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.RIGHT, padx=5)
        
        self.browse_btn = ttk.Button(action_frame, text="Browse Output Directory", command=self.browse_directory)
        self.browse_btn.pack(side=tk.LEFT, padx=5)
        
        self.output_dir = os.path.join(os.getcwd(), "backups")
        self.output_dir_var = tk.StringVar(value=f"Output Directory: {self.output_dir}")
        ttk.Label(action_frame, textvariable=self.output_dir_var).pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
    def log(self, message):
        self.output_text.insert(tk.END, f"{message}\n")
        self.output_text.see(tk.END)
        self.root.update_idletasks()
        
    def connect_to_salesforce(self):
        username = self.username_var.get()
        password = self.password_var.get()
        token = self.token_var.get()
        domain = 'test' if self.sandbox_var.get() else 'login'
        
        if not all([username, password, token]):
            messagebox.showerror("Error", "Please fill in all credentials")
            return
            
        self.connect_btn.config(state=tk.DISABLED)
        self.status_var.set("Connecting to Salesforce...")
        
        # Run connection in a separate thread to prevent UI freeze
        def connect_thread():
            try:
                self.sf = self.get_salesforce_connection(username, password, token, domain)
                if self.sf:
                    self.available_objects = self.get_available_objects()
                    self.root.after(0, self.populate_objects_list)
                    self.root.after(0, lambda: self.status_var.set("Connected to Salesforce"))
                    self.root.after(0, lambda: self.backup_btn.config(state=tk.NORMAL))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Failed to connect to Salesforce"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Connection failed: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.connect_btn.config(state=tk.NORMAL))
        
        threading.Thread(target=connect_thread, daemon=True).start()
        
    def get_salesforce_connection(self, username, password, security_token, domain='login'):
        try:
            session_id, instance = SalesforceLogin(
                username=username,
                password=password,
                security_token=security_token,
                domain=domain
            )
            sf = Salesforce(instance=instance, session_id=session_id)
            self.log("Successfully connected to Salesforce!")
            return sf
        except Exception as e:
            self.log(f"Error connecting to Salesforce: {str(e)}")
            return None
            
    def get_available_objects(self):
        try:
            objects = [obj for obj in self.sf.describe()['sobjects'] if obj['queryable']]
            return sorted([obj['name'] for obj in objects])
        except Exception as e:
            self.log(f"Error retrieving objects: {str(e)}")
            return []
            
    def populate_objects_list(self):
        self.objects_listbox.delete(0, tk.END)
        for obj in self.available_objects:
            self.objects_listbox.insert(tk.END, obj)
    
    def filter_objects(self, *args):
        search_term = self.search_var.get().lower()
        
        # Update selected objects from current selection before filtering
        current_selection = {self.objects_listbox.get(i) for i in self.objects_listbox.curselection()}
        self.selected_objects_set.update(current_selection)
        
        self.objects_listbox.delete(0, tk.END)
        visible_items = []
        
        for obj in self.available_objects:
            if search_term in obj.lower():
                self.objects_listbox.insert(tk.END, obj)
                visible_items.append(obj)
        
        # Restore selection from our tracking set
        for i, obj in enumerate(visible_items):
            if obj in self.selected_objects_set:
                self.objects_listbox.selection_set(i)
        
        self.update_selected_display()
    
    def update_selected_display(self):
        # Update our tracking set with current selection
        current_selection = {self.objects_listbox.get(i) for i in self.objects_listbox.curselection()}
        self.selected_objects_set.update(current_selection)
        
        if self.selected_objects_set:
            self.selected_objects_var.set(f"Selected: {', '.join(sorted(self.selected_objects_set))}")
        else:
            self.selected_objects_var.set("Selected: None")
    
    def select_all(self):
        self.objects_listbox.selection_set(0, tk.END)
        # Update our tracking set with all visible items
        self.selected_objects_set.update(self.objects_listbox.get(0, tk.END))
        self.update_selected_display()
    
    def clear_selection(self):
        # Clear both the listbox selection and our tracking set
        self.objects_listbox.selection_clear(0, tk.END)
        self.selected_objects_set.clear()
        self.update_selected_display()
    
    def browse_directory(self):
        folder = filedialog.askdirectory(initialdir=self.output_dir)
        if folder:
            self.output_dir = folder
            self.output_dir_var.set(f"Output Directory: {self.output_dir}")
    
    def start_backup(self):
        if not self.selected_objects_set:
            messagebox.showwarning("Warning", "Please select at least one object to backup")
            return
            
        # Use our tracked selection set instead of current listbox selection
        self.selected_objects = self.selected_objects_set.copy()
        
        # Disable UI elements during backup
        self.backup_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.connect_btn.config(state=tk.DISABLED)
        self.status_var.set("Backup in progress...")
        self.progress_var.set(0)
        self.output_text.delete(1.0, tk.END)
        self.stop_event.clear()
        
        # Start backup in a separate thread
        self.backup_thread = threading.Thread(target=self.run_backup, daemon=True)
        self.backup_thread.start()
        
        # Start progress update
        self.update_progress()
    
    def stop_backup(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to stop the backup?"):
            self.stop_event.set()
            self.status_var.set("Stopping backup...")
    
    def update_progress(self):
        if hasattr(self, 'current_progress') and hasattr(self, 'total_objects'):
            progress = (self.current_progress / self.total_objects) * 100
            self.progress_var.set(progress)
        
        if hasattr(self, 'backup_thread') and self.backup_thread.is_alive():
            self.root.after(500, self.update_progress)
        else:
            self.backup_complete()
    
    def backup_complete(self):
        self.backup_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.connect_btn.config(state=tk.NORMAL)
        self.status_var.set("Backup completed" if not self.stop_event.is_set() else "Backup stopped")
    
    def run_backup(self):
        try:
            total_objects = len(self.selected_objects)
            self.total_objects = total_objects
            self.current_progress = 0
            
            for i, obj_name in enumerate(self.selected_objects, 1):
                if self.stop_event.is_set():
                    self.log(f"Backup stopped by user")
                    break
                    
                self.current_progress = i
                self.root.after(0, lambda: self.status_var.set(f"Backing up {obj_name} ({i}/{total_objects})"))
                self.backup_object(obj_name)
                
            if not self.stop_event.is_set():
                self.root.after(0, lambda: self.log("\nBackup completed successfully!"))
        except Exception as e:
            self.root.after(0, lambda: self.log(f"\nError during backup: {str(e)}"))
    
    def backup_object(self, object_name):
        try:
            output_dir = os.path.join(self.output_dir, datetime.now().strftime('%Y%m%d_%H%M%S'))
            os.makedirs(output_dir, exist_ok=True)
            
            self.log(f"\nBacking up {object_name}...")
            
            # Get all fields for the object
            desc = getattr(self.sf, object_name).describe()
            field_names = [field['name'] for field in desc['fields']]
            
            # Query records with pagination
            query = f"SELECT {', '.join(field_names)} FROM {object_name} ORDER BY Id"
            result = self.sf.query_all(query)
            records = result['records']
            total_size = result['totalSize']
            
            if total_size == 0:
                self.log(f"No records found for {object_name}")
                return
            
            # Handle pagination if there are more records
            while not result['done'] and not self.stop_event.is_set():
                result = self.sf.query_more(result['nextRecordsUrl'], identifier_is_url=True)
                records.extend(result['records'])
                self.log(f"Retrieved {len(records)} of {total_size} records...")
            
            if self.stop_event.is_set():
                self.log("Backup stopped by user")
                return
                
            # Convert to DataFrame and save as CSV
            df = pd.DataFrame(records)
            
            # Remove the 'attributes' column if it exists
            if 'attributes' in df.columns:
                df = df.drop(columns=['attributes'])
            
            # Save to CSV
            filename = os.path.join(output_dir, f"{object_name}.csv")
            df.to_csv(filename, index=False)
            
            self.log(f"Successfully backed up {len(df)} records to {filename}")
            
        except Exception as e:
            self.log(f"Error backing up {object_name}: {str(e)}")
            raise

def main():
    root = tk.Tk()
    app = SalesforceBackupApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()