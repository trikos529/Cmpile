import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import subprocess
import threading
import json
import hashlib
from pathlib import Path

# Set theme and color options
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class SimpleCompilerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("cmpail")
        self.geometry("800x700")
        
        # Variables
        self.selected_files = []
        self.output_dir = ctk.StringVar()
        self.exe_name = ctk.StringVar(value="output")
        self.compiler_var = ctk.StringVar(value="gcc")
        self.compiler_flags = ctk.StringVar(value="-O2 -Wall")
        self.packages_var = ctk.StringVar()
        
        # Build info file
        self.build_info_file = "build_info.json"
        self.build_info = self.load_build_info()
        
        self.setup_ui()
    
    def load_build_info(self):
        """Load previous build information"""
        if os.path.exists(self.build_info_file):
            try:
                with open(self.build_info_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_build_info(self):
        """Save current build information"""
        try:
            with open(self.build_info_file, 'w') as f:
                json.dump(self.build_info, f, indent=2)
        except:
            pass
    
    def get_file_hash(self, filepath):
        """Calculate MD5 hash of a file to detect changes"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
    
    def needs_recompile(self, source_file, obj_file):
        """Check if a file needs recompilation"""
        if not os.path.exists(obj_file):
            return True
        if not os.path.exists(source_file):
            return False
        
        source_hash = self.get_file_hash(source_file)
        old_hash = self.build_info.get(source_file, {}).get('hash')
        
        if source_hash != old_hash:
            return True
        
        source_mtime = os.path.getmtime(source_file)
        obj_mtime = os.path.getmtime(obj_file)
        
        return source_mtime > obj_mtime
    
    def setup_ui(self):
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main scrollable frame
        main_frame = ctk.CTkScrollableFrame(self, label_text="Compiler Settings")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # File selection
        ctk.CTkLabel(main_frame, text="Select Source Files:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        ctk.CTkButton(main_frame, text="Browse Files", command=self.browse_files).grid(row=0, column=1, pady=5, padx=5, sticky="e")
        
        # Selected files listbox (using CTkTextbox as listbox alternative)
        self.files_listbox = ctk.CTkTextbox(main_frame, height=100)
        self.files_listbox.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5, padx=5)
        self.files_listbox.configure(state="disabled")
        
        # Clear files button
        ctk.CTkButton(main_frame, text="Clear Selected", command=self.clear_files, fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE")).grid(row=2, column=0, pady=5, padx=5, sticky="w")
        
        # Compiler selection
        ctk.CTkLabel(main_frame, text="Compiler:").grid(row=3, column=0, sticky="w", pady=5, padx=5)
        compiler_combo = ctk.CTkComboBox(main_frame, variable=self.compiler_var, 
                                    values=["gcc", "g++", "clang", "clang++", "msvc"])
        compiler_combo.grid(row=3, column=1, sticky="ew", pady=5, padx=5)
        
        # Compiler flags
        ctk.CTkLabel(main_frame, text="Compiler Flags:").grid(row=4, column=0, sticky="w", pady=5, padx=5)
        ctk.CTkEntry(main_frame, textvariable=self.compiler_flags).grid(row=4, column=1, sticky="ew", pady=5, padx=5)
        
        # Packages/Libraries
        ctk.CTkLabel(main_frame, text="Packages/Libraries:").grid(row=5, column=0, sticky="w", pady=5, padx=5)
        packages_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        packages_frame.grid(row=5, column=1, sticky="ew", pady=5, padx=5)
        packages_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkEntry(packages_frame, textvariable=self.packages_var).grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(packages_frame, text="Common Libs", command=self.show_common_libs, width=100).grid(row=0, column=1, padx=(5, 0))
        
        # Output directory
        ctk.CTkLabel(main_frame, text="Output Directory:").grid(row=6, column=0, sticky="w", pady=5, padx=5)
        ctk.CTkEntry(main_frame, textvariable=self.output_dir).grid(row=6, column=1, sticky="ew", pady=5, padx=5)
        ctk.CTkButton(main_frame, text="Browse", command=self.browse_directory, width=100).grid(row=7, column=1, pady=5, padx=5, sticky="e")
        
        # Executable name
        ctk.CTkLabel(main_frame, text="Executable Name:").grid(row=8, column=0, sticky="w", pady=5, padx=5)
        ctk.CTkEntry(main_frame, textvariable=self.exe_name).grid(row=8, column=1, sticky="ew", pady=5, padx=5)
        
        # Options frame
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.grid(row=9, column=0, columnspan=2, sticky="ew", pady=10, padx=5)
        
        self.incremental_var = ctk.BooleanVar(value=True)
        self.clean_build_var = ctk.BooleanVar(value=False)
        
        ctk.CTkCheckBox(options_frame, text="Incremental Build", variable=self.incremental_var).pack(side="left", padx=20, pady=10)
        ctk.CTkCheckBox(options_frame, text="Clean Build", variable=self.clean_build_var).pack(side="left", padx=20, pady=10)
        
        # Compile buttons frame
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=10, column=0, columnspan=2, pady=20)
        
        ctk.CTkButton(button_frame, text="Compile", command=self.start_compile, font=("Arial", 16, "bold"), height=40, width=200).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Clean Build", command=self.clean_build, fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE")).pack(side="left", padx=10)
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(main_frame, mode='indeterminate')
        self.progress.grid(row=11, column=0, columnspan=2, sticky="ew", pady=10, padx=5)
        self.progress.set(0)
        
        # Output text area
        ctk.CTkLabel(main_frame, text="Compilation Output:").grid(row=12, column=0, sticky="w", pady=5, padx=5)
        self.output_text = ctk.CTkTextbox(main_frame, height=200)
        self.output_text.grid(row=13, column=0, columnspan=2, sticky="ew", pady=5, padx=5)
    
    def show_common_libs(self):
        """Show common library suggestions"""
        common_libs_window = ctk.CTkToplevel(self)
        common_libs_window.title("Common Libraries")
        common_libs_window.geometry("500x400")
        common_libs_window.attributes("-topmost", True)
        
        common_libs = {
            "Graphics": ["-lSDL2", "-lSDL2_image", "-lSDL2_ttf", "-lGL", "-lglfw", "-lGLEW"],
            "Math": ["-lm", "-lblas", "-llapack"],
            "Networking": ["-lssl", "-lcrypto", "-lcurl", "-lpthread"],
            "Multimedia": ["-lavcodec", "-lavformat", "-lavutil", "-lswscale"],
            "GUI": ["-lgtk-3", "-lglib-2.0", "-lgobject-2.0", "-lQt5Core", "-lQt5Gui", "-lQt5Widgets"],
            "System": ["-lpthread", "-ldl", "-lrt"]
        }
        
        notebook = ctk.CTkTabview(common_libs_window)
        notebook.pack(expand=True, fill='both', padx=10, pady=10)
        
        for category, libs in common_libs.items():
            notebook.add(category)
            frame = notebook.tab(category)
            
            for i, lib in enumerate(libs):
                btn = ctk.CTkButton(frame, text=lib, 
                               command=lambda l=lib: self.add_library(l))
                btn.grid(row=i//2, column=i%2, sticky="ew", padx=5, pady=5)
    
    def add_library(self, library):
        current = self.packages_var.get()
        if current:
            new_value = current + " " + library
        else:
            new_value = library
        self.packages_var.set(new_value)
    
    def browse_files(self):
        files = filedialog.askopenfilenames(
            title="Select Source Files",
            filetypes=[("C/C++ files", "*.c *.cpp *.cc *.cxx"), ("All files", "*.*")]
        )
        if files:
            for file in files:
                if file not in self.selected_files:
                    self.selected_files.append(file)
            self.update_files_list()
    
    def clear_files(self):
        self.selected_files = []
        self.update_files_list()
        
    def update_files_list(self):
        self.files_listbox.configure(state="normal")
        self.files_listbox.delete("0.0", "end")
        for file in self.selected_files:
            self.files_listbox.insert("end", file + "\n")
        self.files_listbox.configure(state="disabled")
    
    def browse_directory(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir.set(directory)
    
    def log_output(self, text):
        self.output_text.insert("end", text + "\n")
        self.output_text.see("end")
    
    def clean_build(self):
        self.clean_build_var.set(True)
        self.start_compile()
    
    def compile_files(self):
        try:
            self.progress.start()
            self.output_text.delete("0.0", "end")
            
            if not self.selected_files:
                messagebox.showerror("Error", "No files selected!")
                return
            
            output_dir = self.output_dir.get()
            if not output_dir:
                messagebox.showerror("Error", "Please select an output directory!")
                return
            
            exe_name = self.exe_name.get()
            if not exe_name:
                exe_name = "output"
            
            compiler = self.compiler_var.get()
            flags = self.compiler_flags.get()
            packages = self.packages_var.get()
            incremental = self.incremental_var.get()
            clean_build = self.clean_build_var.get()
            
            obj_dir = os.path.join(output_dir, "obj")
            os.makedirs(obj_dir, exist_ok=True)
            
            self.log_output(f"Starting compilation with {compiler}...")
            self.log_output(f"Output directory: {output_dir}")
            self.log_output(f"Object files directory: {obj_dir}")
            
            if clean_build:
                self.log_output("Performing clean build...")
                if os.path.exists(obj_dir):
                    for file in os.listdir(obj_dir):
                        if file.endswith('.o'):
                            os.remove(os.path.join(obj_dir, file))
                self.build_info = {}
            
            obj_files = []
            recompiled_count = 0
            skipped_count = 0
            
            for source_file in self.selected_files:
                base_name = os.path.splitext(os.path.basename(source_file))[0]
                obj_file = os.path.join(obj_dir, f"{base_name}.o")
                obj_files.append(obj_file)
                
                if incremental and not self.needs_recompile(source_file, obj_file):
                    self.log_output(f"✓ Skipped (unchanged): {os.path.basename(source_file)}")
                    skipped_count += 1
                    continue
                
                self.log_output(f"Compiling {os.path.basename(source_file)}...")
                
                compile_cmd = [compiler, "-c", source_file, "-o", obj_file]
                if flags:
                    compile_cmd.extend(flags.split())
                
                # IMPORTANT: Create startupinfo to hide console window for subprocess
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                result = subprocess.run(compile_cmd, capture_output=True, text=True, startupinfo=startupinfo)
                
                if result.returncode != 0:
                    self.log_output(f"Error compiling {source_file}:")
                    self.log_output(result.stderr)
                    messagebox.showerror("Compilation Error", f"Failed to compile {source_file}")
                    return
                else:
                    self.log_output(f"✓ Successfully compiled {os.path.basename(source_file)}")
                    recompiled_count += 1
                    
                    file_hash = self.get_file_hash(source_file)
                    if source_file not in self.build_info:
                        self.build_info[source_file] = {}
                    self.build_info[source_file]['hash'] = file_hash
            
            self.log_output("-" * 50)
            self.log_output(f"Summary: {recompiled_count} recompiled, {skipped_count} skipped")
            
            exe_path = os.path.join(output_dir, exe_name)
            if not exe_path.endswith('.exe'):
                exe_path += '.exe'
            
            needs_linking = (recompiled_count > 0 or not os.path.exists(exe_path))
            
            if needs_linking:
                self.log_output("Linking object files...")
                
                link_cmd = [compiler] + obj_files + ["-o", exe_path]
                if flags:
                    link_cmd.extend(flags.split())
                if packages:
                    link_cmd.extend(packages.split())
                
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                result = subprocess.run(link_cmd, capture_output=True, text=True, startupinfo=startupinfo)
                
                if result.returncode != 0:
                    self.log_output("Error during linking:")
                    self.log_output(result.stderr)
                    messagebox.showerror("Linking Error", "Failed to link object files")
                else:
                    self.log_output(f"✓ Successfully created executable: {exe_path}")
                    messagebox.showinfo("Success", f"Compilation completed!\nExecutable: {exe_path}")
            else:
                self.log_output("✓ No linking needed - no changes detected")
                messagebox.showinfo("Success", "Build completed - no changes detected!")
            
            self.save_build_info()
        
        except Exception as e:
            self.log_output(f"Unexpected error: {str(e)}")
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
        finally:
            self.progress.stop()
            self.clean_build_var.set(False)
    
    def start_compile(self):
        thread = threading.Thread(target=self.compile_files)
        thread.daemon = True
        thread.start()

def main():
    app = SimpleCompilerGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
