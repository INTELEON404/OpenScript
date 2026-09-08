```
{
  "repository": {
    "name": "OpenScript",
    "description": "Essential scripts for system task automation",
    "license": "MIT"
  },
  "languages": [
    "Python",
    "Bash"
  ],
  "scripts_directory": [
    {
      "language": "Python",
      "path": "python",
      "description": "Data parsing & system utilities"
    },
    {
      "language": "Bash",
      "path": "bash",
      "description": "Shell automation & workflow macros"
    }
  ],
  "execution_commands": {
    "python": "python3 main.py | tee python_output.log",
    "bash": "bash setup.sh | tee bash_output.log"
  }
}
```
