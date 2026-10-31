import os
import json

class ApexWorkspaceManager:
    def __init__(self, project_root):
        self.root = project_root
        self.vscode_dir = os.path.join(project_root, ".vscode")
        self.settings_path = os.path.join(self.vscode_dir, "settings.json")
        self.layout_path = os.path.join(self.vscode_dir, "tasks.json")

    def initialize_dashboard(self):
        """Component 4: Automatic Multi-Window Split Screen Interface Layout"""
        print("??? [Workspace] Synchronizing target paths with Visual Studio Code backend...")
        os.makedirs(self.vscode_dir, exist_ok=True)
        
        # Force strict terminal configurations and path variables into the IDE profile
        settings = {
            "terminal.integrated.defaultProfile.windows": "PowerShell",
            "terminal.integrated.scrollback": 10000,
            "files.autoSave": "afterDelay",
            "files.autoSaveDelay": 1000,
            "workbench.editor.closeEmptyGroups": False
        }
        
        # Build out automated task runner definitions to hook scripts into the hotkeys
        tasks = {
            "version": "2.0.0",
            "tasks": [
                {
                    "label": "Launch 10/10 Core Engine Swarm",
                    "type": "shell",
                    "command": "python",
                    "args": [f"{self.root}/Scripts/ApexCoreEngine.py"],
                    "runOptions": {"runOn": "folderOpen"},
                    "presentation": {"echo": True, "reveal": "always", "panel": "dedicated", "group": "apex"}
                }
            ]
        }
        
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
        with open(self.layout_path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=4)
            
        print("?? [Workspace] Extension configuration assets generated successfully.")
        print(f"?? Active Dashboard Profile Locked: {self.vscode_dir}")
