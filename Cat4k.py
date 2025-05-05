import os
import sys
import subprocess
import platform
import urllib.request
import json
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import uuid

# Constants
MINECRAFT_DIR = os.path.expanduser("~/.minecraft")
VERSIONS_DIR = os.path.join(MINECRAFT_DIR, "versions")
JAVA_DIR = os.path.expanduser("~/.catclient/java")
VERSION_MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
TLAUNCHER_AUTH_URL = "https://auth.tlauncher.org/authenticate"

# Lunar Client-like theme
LUNAR_THEME = {
    'bg': '#0a0a0a',
    'sidebar': '#1a1a1a',
    'accent': '#00bfff',
    'text': '#ffffff',
    'text_secondary': '#b0b0b0',
    'button': '#2a2a2a',
    'button_hover': '#3a3a3a',
    'input_bg': '#2a2a2a'
}

class CatClientHDRV0(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CatClient HDRV0")
        self.geometry("1200x700")
        self.configure(bg=LUNAR_THEME['bg'])
        self.config = configparser.ConfigParser()
        self.config_file = os.path.join(MINECRAFT_DIR, "catclient_config.ini")
        self.logged_in = False
        self.access_token = None
        self.username = None
        self.uuid = None
        self.versions = {}
        self.modpacks = ["Modpack 1", "Modpack 2", "Modpack 3"]  # Placeholder modpacks

        # Load or initialize config
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            self.config['settings'] = {'mode': 'offline', 'java_path': '', 'client_token': str(uuid.uuid4())}
            with open(self.config_file, 'w') as f:
                self.config.write(f)

        # Ensure client_token exists
        if 'client_token' not in self.config['settings']:
            self.config['settings']['client_token'] = str(uuid.uuid4())
            with open(self.config_file, 'w') as f:
                self.config.write(f)

        # Fetch Minecraft versions
        self.fetch_versions()

        # Initialize UI
        self.init_ui()

    def fetch_versions(self):
        """Fetch available Minecraft versions."""
        try:
            with urllib.request.urlopen(VERSION_MANIFEST_URL) as response:
                data = json.loads(response.read().decode())
                self.versions = {v["id"]: v["url"] for v in data["versions"]}
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch versions: {e}")
            self.versions = {}

    def init_ui(self):
        """Set up the Lunar Client-like GUI."""
        main_container = tk.Frame(self, bg=LUNAR_THEME['bg'])
        main_container.pack(fill="both", expand=True)

        # Sidebar
        sidebar = tk.Frame(main_container, bg=LUNAR_THEME['sidebar'], width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Sidebar buttons
        for text in ["Home", "Modpacks", "Settings"]:
            btn = tk.Button(sidebar, text=text, font=("Arial", 12), bg=LUNAR_THEME['button'], fg=LUNAR_THEME['text'],
                            activebackground=LUNAR_THEME['button_hover'], bd=0, command=lambda t=text: self.show_page(t))
            btn.pack(fill="x", pady=5, padx=10)

        # Content area
        self.content_area = tk.Frame(main_container, bg=LUNAR_THEME['bg'])
        self.content_area.pack(side="left", fill="both", expand=True)

        # Initialize pages
        self.home_page = self.create_home_page()
        self.modpacks_page = self.create_modpacks_page()
        self.settings_page = self.create_settings_page()

        # Show home page by default
        self.show_page("Home")

    def show_page(self, page_name):
        """Switch between pages."""
        for page in [self.home_page, self.modpacks_page, self.settings_page]:
            page.pack_forget()
        if page_name == "Home":
            self.home_page.pack(fill="both", expand=True)
        elif page_name == "Modpacks":
            self.modpacks_page.pack(fill="both", expand=True)
        elif page_name == "Settings":
            self.settings_page.pack(fill="both", expand=True)

    def create_home_page(self):
        """Create the home page with version selection and play button."""
        frame = tk.Frame(self.content_area, bg=LUNAR_THEME['bg'])
        
        # Version selection
        version_label = tk.Label(frame, text="Select Version:", bg=LUNAR_THEME['bg'], fg=LUNAR_THEME['text'])
        version_label.pack(pady=5)
        self.version_combo = ttk.Combobox(frame, values=list(self.versions.keys()), state="readonly")
        self.version_combo.pack(pady=5)
        self.version_combo.set("1.20.1")  # Default version

        # Play button
        play_button = tk.Button(frame, text="PLAY", font=("Arial", 16, "bold"), bg=LUNAR_THEME['accent'], fg=LUNAR_THEME['text'],
                                command=self.prepare_and_launch)
        play_button.pack(pady=20)
        
        return frame

    def create_modpacks_page(self):
        """Create the modpacks page with modpack installer."""
        frame = tk.Frame(self.content_area, bg=LUNAR_THEME['bg'])
        
        # Modpack list
        modpack_list = tk.Listbox(frame, bg=LUNAR_THEME['input_bg'], fg=LUNAR_THEME['text'], font=("Arial", 12))
        modpack_list.pack(fill="both", expand=True, padx=20, pady=20)
        for modpack in self.modpacks:
            modpack_list.insert(tk.END, modpack)
        
        # Install button
        install_button = tk.Button(frame, text="Install Modpack", font=("Arial", 12), bg=LUNAR_THEME['button'], fg=LUNAR_THEME['text'],
                                   command=lambda: self.install_modpack(modpack_list.get(tk.ACTIVE)))
        install_button.pack(pady=10)
        
        return frame

    def create_settings_page(self):
        """Create the settings page with authentication."""
        frame = tk.Frame(self.content_area, bg=LUNAR_THEME['bg'])
        
        # Authentication section
        auth_frame = tk.LabelFrame(frame, text="Authentication", bg=LUNAR_THEME['bg'], fg=LUNAR_THEME['text_secondary'])
        auth_frame.pack(fill="x", padx=20, pady=10)
        
        # Mode selection
        mode_label = tk.Label(auth_frame, text="Mode:", bg=LUNAR_THEME['bg'], fg=LUNAR_THEME['text'])
        mode_label.pack(anchor="w")
        self.mode_combo = ttk.Combobox(auth_frame, values=["Offline Mode", "TLauncher Mode"], state="readonly")
        self.mode_combo.pack(fill="x", pady=5)
        self.mode_combo.bind("<<ComboboxSelected>>", self.update_mode)
        self.mode_combo.set(self.config['settings']['mode'])

        # TLauncher login fields
        self.auth_fields_frame = tk.Frame(auth_frame, bg=LUNAR_THEME['bg'])
        tk.Label(self.auth_fields_frame, text="Username/Email:", bg=LUNAR_THEME['bg'], fg=LUNAR_THEME['text']).pack(anchor="w")
        self.auth_entry = tk.Entry(self.auth_fields_frame, bg=LUNAR_THEME['input_bg'], fg=LUNAR_THEME['text'])
        self.auth_entry.pack(fill="x", pady=2)
        tk.Label(self.auth_fields_frame, text="Password:", bg=LUNAR_THEME['bg'], fg=LUNAR_THEME['text']).pack(anchor="w")
        self.password_entry = tk.Entry(self.auth_fields_frame, show="*", bg=LUNAR_THEME['input_bg'], fg=LUNAR_THEME['text'])
        self.password_entry.pack(fill="x", pady=2)
        login_button = tk.Button(self.auth_fields_frame, text="Login", bg=LUNAR_THEME['button'], fg=LUNAR_THEME['text'],
                                 command=self.login)
        login_button.pack(pady=5)
        self.update_mode()

        return frame

    def update_mode(self, event=None):
        """Update UI based on selected mode."""
        mode = self.mode_combo.get()
        self.config['settings']['mode'] = mode
        with open(self.config_file, 'w') as f:
            self.config.write(f)
        if mode == "Offline Mode":
            self.auth_fields_frame.pack_forget()
        elif mode == "TLauncher Mode":
            self.auth_fields_frame.pack(fill="x", pady=10)

    def login(self):
        """Authenticate with TLauncher."""
        auth_input = self.auth_entry.get()
        password = self.password_entry.get()
        client_token = self.config['settings']['client_token']
        payload = {
            "username": auth_input,
            "password": password,
            "clientToken": client_token,
            "requestUser": True
        }
        try:
            req = urllib.request.Request(
                TLAUNCHER_AUTH_URL,
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'TLauncher/2.0 (Java; Windows 10)'
                }
            )
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                print(data)  # For debugging
                self.access_token = data['accessToken']
                self.uuid = data['selectedProfile']['id']
                self.username = data['selectedProfile']['name']
                self.logged_in = True
                messagebox.showinfo("Success", f"Logged in as {self.username}")
        except urllib.error.HTTPError as e:
            error_message = e.read().decode()
            print(f"Error response: {error_message}")  # Print detailed error
            messagebox.showerror("Error", f"Authentication failed: {e.code} {e.reason}\nDetails: {error_message}")
            self.logged_in = False
        except Exception as e:
            messagebox.showerror("Error", f"Authentication failed: {e}")
            self.logged_in = False

    def install_modpack(self, modpack_name):
        """Install the selected modpack (placeholder)."""
        messagebox.showinfo("Modpack Installer", f"Installing {modpack_name}...")
        # Placeholder: Implement modpack download and installation logic here

    def install_java_if_needed(self):
        """Install Zulu OpenJDK if not present (simplified)."""
        if not os.path.exists(JAVA_DIR):
            os.makedirs(JAVA_DIR)
            java_url = "https://cdn.azul.com/zulu/bin/zulu17.36.17-ca-jdk17.0.4-win_x64.zip"  # Example URL
            messagebox.showinfo("Java", "Installing Zulu OpenJDK (placeholder)...")
            # Placeholder: Download and extract Zulu OpenJDK
        java_path = os.path.join(JAVA_DIR, "bin", "java.exe" if platform.system() == "Windows" else "java")
        self.config['settings']['java_path'] = java_path
        with open(self.config_file, 'w') as f:
            self.config.write(f)
        return java_path

    def prepare_and_launch(self):
        """Prepare and launch Minecraft."""
        if self.config['settings']['mode'] == "TLauncher Mode" and not self.logged_in:
            messagebox.showerror("Error", "Please log in with TLauncher first.")
            return

        version = self.version_combo.get()
        if not version:
            messagebox.showerror("Error", "Please select a version.")
            return

        java_path = self.install_java_if_needed()

        # Launch command (simplified)
        launch_cmd = [
            java_path,
            "-Djava.library.path=" + VERSIONS_DIR,
            "-cp", MINECRAFT_DIR,  # Placeholder: Update classpath
            "net.minecraft.client.main.Main",
            "--username", self.username if self.logged_in else "Player",
            "--version", version,
            "--gameDir", MINECRAFT_DIR,
            "--assetsDir", os.path.join(MINECRAFT_DIR, "assets"),
            "--assetIndex", version.split('.')[1],  # Simplified
            "--uuid", self.uuid if self.logged_in else str(uuid.uuid4()),
            "--accessToken", self.access_token if self.logged_in else "0"
        ]
        try:
            subprocess.Popen(launch_cmd, cwd=MINECRAFT_DIR)
            messagebox.showinfo("Success", "Minecraft is launching...")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch: {e}")

if __name__ == "__main__":
    app = CatClientHDRV0()
    app.mainloop()
