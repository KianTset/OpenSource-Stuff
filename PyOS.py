#Made By : KianKamikaze On Github.
#Licensed By : Apache License 2.0
import sys
import datetime

class PyOS:
    """
    A simulated terminal-based operating system written in Python.
    It features a virtual file system and a set of core commands.
    """
    def __init__(self, user="user"):
        self.user = user
        self.hostname = "pyos-main"
        # The root of our virtual file system.
        # 'type' can be 'dir' or 'file'.
        # 'children' for directories, 'content' for files.
        self.file_system = {
            "type": "dir",
            "children": {
                "home": {
                    "type": "dir",
                    "children": {
                        user: {
                            "type": "dir",
                            "children": {
                                "welcome.txt": {
                                    "type": "file",
                                    "content": "Welcome to PyOS! Type 'help' to see available commands."
                                }
                            }
                        }
                    }
                },
                "etc": {
                    "type": "dir",
                    "children": {
                        "os-release": {
                            "type": "file",
                            "content": "PyOS Version 1.0 (Simulated)"
                        }
                    }
                }
            }
        }
        self.current_path = ["home", user] # Start in the user's home directory
        self.commands = self._get_commands()

    def _get_commands(self):
        """Maps command strings to their corresponding methods."""
        return {
            "help": self._help,
            "ls": self._ls,
            "cd": self._cd,
            "mkdir": self._mkdir,
            "cat": self._cat,
            "echo": self._echo,
            "rm": self._rm,
            "pwd": self._pwd,
            "date": self._date,
            "exit": self._exit,
        }

    def _get_node_from_path(self, path_list):
        """Navigates the file system to find a specific node."""
        node = self.file_system
        for part in path_list:
            if part in node["children"] and node["children"][part]["type"] == "dir":
                node = node["children"][part]
            else:
                return None # Path does not exist
        return node

    def _get_current_node(self):
        """Helper to get the node for the current working directory."""
        return self._get_node_from_path(self.current_path)

    def _get_prompt(self):
        """Generates the command prompt string."""
        path_str = "/" + "/".join(self.current_path) if self.current_path else "/"
        return f"{self.user}@{self.hostname}:{path_str}$ "

    # --- Command Implementations ---

    def _help(self, args):
        """Lists all available commands and their functions."""
        print("PyOS Command List:")
        print("  help          - Shows this help message.")
        print("  ls [path]     - Lists contents of a directory.")
        print("  cd <path>     - Changes the current directory. Use '..' for parent, '/' for root.")
        print("  mkdir <name>  - Creates a new directory.")
        print("  cat <file>    - Displays the content of a file.")
        print("  echo <text> > <file> - Writes text to a file, creating it if necessary.")
        print("  rm <name>     - Removes a file or an empty directory.")
        print("  pwd           - Prints the current working directory path.")
        print("  date          - Displays the current date and time.")
        print("  exit          - Exits the PyOS session.")

    def _ls(self, args):
        """Lists the contents of the current directory."""
        node = self._get_current_node()
        contents = list(node["children"].keys())
        if not contents:
            return
        for name in sorted(contents):
            item = node["children"][name]
            # Add a slash to directories for clarity
            display_name = name + "/" if item["type"] == "dir" else name
            print(display_name, end="  ")
        print() # Newline at the end

    def _cd(self, args):
        """Changes the current directory."""
        if not args:
            self.current_path = ["home", self.user] # Go home if no args
            return
            
        path = args[0]
        if path == "/":
            self.current_path = []
            return
        if path == "..":
            if self.current_path:
                self.current_path.pop()
            return
        
        current_node = self._get_current_node()
        if path in current_node["children"] and current_node["children"][path]["type"] == "dir":
            self.current_path.append(path)
        else:
            print(f"cd: no such directory: {path}")

    def _mkdir(self, args):
        """Creates a new directory."""
        if not args:
            print("mkdir: missing operand")
            return
        dir_name = args[0]
        current_node = self._get_current_node()
        if dir_name in current_node["children"]:
            print(f"mkdir: cannot create directory '{dir_name}': File exists")
        else:
            current_node["children"][dir_name] = {"type": "dir", "children": {}}

    def _cat(self, args):
        """Displays file content."""
        if not args:
            print("cat: missing operand")
            return
        file_name = args[0]
        current_node = self._get_current_node()
        if file_name in current_node["children"] and current_node["children"][file_name]["type"] == "file":
            print(current_node["children"][file_name]["content"])
        else:
            print(f"cat: {file_name}: No such file or it is a directory")

    def _echo(self, args):
        """Writes text to a file."""
        try:
            redirect_index = args.index(">")
            file_name = args[redirect_index + 1]
            content_list = args[:redirect_index]
            content = " ".join(content_list)
            
            current_node = self._get_current_node()
            # Overwrite or create new file
            current_node["children"][file_name] = {"type": "file", "content": content}
        except (ValueError, IndexError):
            print("Usage: echo <text> > <filename>")

    def _rm(self, args):
        """Removes a file or an empty directory."""
        if not args:
            print("rm: missing operand")
            return
        name = args[0]
        current_node = self._get_current_node()
        if name not in current_node["children"]:
            print(f"rm: cannot remove '{name}': No such file or directory")
            return
        
        item_to_remove = current_node["children"][name]
        if item_to_remove["type"] == "dir" and item_to_remove["children"]:
            print(f"rm: failed to remove '{name}': Directory not empty")
            return
            
        del current_node["children"][name]

    def _pwd(self, args):
        """Prints the current working directory path."""
        path_str = "/" + "/".join(self.current_path) if self.current_path else "/"
        print(path_str)

    def _date(self, args):
        """Prints the current date and time."""
        print(datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Y"))

    def _exit(self, args):
        """Exits the simulation."""
        print("Shutting down PyOS...")
        sys.exit(0)

    def run(self):
        """The main loop of the operating system shell."""
        print("PyOS [Version 1.0]")
        print("(c) Simulated Corporation. All rights reserved.")
        print()
        
        while True:
            prompt = self._get_prompt()
            try:
                user_input = input(prompt)
            except (EOFError, KeyboardInterrupt):
                # Handle Ctrl+D or Ctrl+C gracefully
                print("\nExiting.")
                break
                
            if not user_input.strip():
                continue

            parts = user_input.split()
            command = parts[0]
            args = parts[1:]

            if command in self.commands:
                try:
                    self.commands[command](args)
                except Exception as e:
                    print(f"An error occurred executing '{command}': {e}")
            else:
                print(f"{command}: command not found")

if __name__ == "__main__":
    os_instance = PyOS()
    os_instance.run()