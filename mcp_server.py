#!/usr/bin/env python3

import os
import json
import subprocess
import shutil
import google.generativeai as genai

# --- ANSI Color Codes --- #
class Colors:
    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

# --- Configuration --- #
API_KEY = os.environ.get("AIzaSyDRTdtRjbMVD0scF6dWQ1Gm_knuolyzuAo") # Get API key from environment variable
PROJECTS_DIR = "./mcp_projects"
MODEL_NAME = "gemini-1.5-flash" # Using gemini-1.5-flash for general text generation

# --- Project Management Functions --- #
def get_project_path(project_name):
    return os.path.join(PROJECTS_DIR, project_name)

def get_project_data_path(project_name):
    return os.path.join(get_project_path(project_name), "project_data.json")

def load_project_data(project_name):
    project_data_path = get_project_data_path(project_name)
    if os.path.exists(project_data_path):
        with open(project_data_path, "r") as f:
            return json.load(f)
    return {"name": project_name, "history": [], "files": {}}

def save_project_data(project_data):
    project_path = get_project_path(project_data["name"])
    os.makedirs(project_path, exist_ok=True)
    project_data_path = get_project_data_path(project_data["name"])
    with open(project_data_path, "w") as f:
        json.dump(project_data, f, indent=4)

def list_projects():
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    projects = []
    for item in os.listdir(PROJECTS_DIR):
        item_path = os.path.join(PROJECTS_DIR, item)
        if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "project_data.json")):
            projects.append(item)
    return projects

def delete_project(project_name):
    project_path = get_project_path(project_name)
    if os.path.exists(project_path):
        shutil.rmtree(project_path)
        return True
    return False

# --- API Interaction Function --- #
def query_gemini_model(messages):
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
    
    # Convert history to Gemini format
    gemini_messages = []
    for msg in messages:
        if msg["role"] == "user":
            gemini_messages.append({"role": "user", "parts": [msg["content"]]})
        elif msg["role"] == "mcp": # Assuming mcp is the assistant
            gemini_messages.append({"role": "model", "parts": [msg["content"]]})

    try:
        response = model.generate_content(gemini_messages)
        return response.text
    except Exception as e:
        return f"Gemini API Error: {e}"

# --- Command Execution Function --- #
def execute_command(command, cwd=None):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True, cwd=cwd)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Command execution failed: {e.stderr}"
    except Exception as e:
        return f"An error occurred during command execution: {e}"

# --- Help System --- #
def display_help():
    help_message = f"""
{Colors.CYAN}MCP Server Commands:{Colors.RESET}

{Colors.YELLOW}1. run command: <your command>{Colors.RESET}
   (Short Description: Executes a shell command in the current project directory.)
   (Example: run command: ls -l)

{Colors.YELLOW}2. new{Colors.RESET}
   (Short Description: Creates a new project.)
   (Example: new)

{Colors.YELLOW}3. delete{Colors.RESET}
   (Short Description: Deletes an existing project.)
   (Example: delete)

{Colors.YELLOW}4. exit{Colors.RESET}
   (Short Description: Saves the current project and exits the MCP server.)
   (Example: exit)

{Colors.YELLOW}5. help{Colors.RESET}
   (Short Description: Displays this help message.)
   (Example: help)

{Colors.BRIGHT_WHITE}For any other queries, the MCP server will use the Gemini model to assist you.{Colors.RESET}
"""
    return help_message

# --- Main Chatbot Logic --- #
def process_user_input(user_input, current_project):
    if not API_KEY:
        return f"{Colors.RED}Error: Gemini API Key not set. Please set the GEMINI_API_KEY environment variable.{Colors.RESET}"

    # Basic command recognition (can be expanded later with NLP)
    if user_input.lower().startswith("run command:"):
        command = user_input[len("run command:"):].strip()
        output = execute_command(command, cwd=get_project_path(current_project["name"]))
        current_project["history"].append({"role": "user", "content": user_input})
        current_project["history"].append({"role": "mcp", "content": output})
        save_project_data(current_project)
        return f"{Colors.YELLOW}Executing command: {command}{Colors.RESET}\n{output}"
    elif user_input.lower() == "help":
        return display_help()
    
    messages = current_project["history"] + [
        {"role": "system", "content": "You are an expert programming assistant and a Termux environment manager. Provide concise and accurate information. If a user asks for a command, provide the exact command. If they ask for code, provide the full code. Be helpful and direct."},
        {"role": "user", "content": user_input}
    ]
    
    try:
        response_text = query_gemini_model(messages)
        current_project["history"].append({"role": "user", "content": user_input})
        current_project["history"].append({"role": "mcp", "content": response_text})
        save_project_data(current_project)
        return response_text
    except Exception as e:
        return f"{Colors.RED}An unexpected error occurred: {e}{Colors.RESET}"

# --- Main Loop --- #
def main():
    print(f"{Colors.CYAN}MCP Server for Termux (Google Gemini {MODEL_NAME}){Colors.RESET}")
    print(f"{Colors.YELLOW}Type \'run command: <your command>\' to execute shell commands.{Colors.RESET}")
    print(f"{Colors.YELLOW}Type \'help\' for a list of commands and examples.{Colors.RESET}")
    print(f"{Colors.YELLOW}Type \'exit\' to quit.{Colors.RESET}")

    current_project = None

    while True:
        if current_project is None:
            projects = list_projects()
            if projects:
                print(f"{Colors.GREEN}Existing projects:{Colors.RESET}")
                for i, p in enumerate(projects):
                    print(f"{Colors.BLUE}{i+1}. {p}{Colors.RESET}")
                choice = input(f"{Colors.MAGENTA}Enter project number to load, \'new\' to create a new project, or \'delete\' to delete a project: {Colors.RESET}")
                if choice.lower() == 'new':
                    project_name = input(f"{Colors.MAGENTA}Enter new project name: {Colors.RESET}")
                    current_project = load_project_data(project_name)
                elif choice.lower() == 'delete':
                    project_to_delete = input(f"{Colors.MAGENTA}Enter project name to delete: {Colors.RESET}")
                    if delete_project(project_to_delete):
                        print(f"{Colors.GREEN}Project \'{project_to_delete}\' deleted.{Colors.RESET}")
                    else:
                        print(f"{Colors.RED}Project \'{project_to_delete}\' not found.{Colors.RESET}")
                    continue
                else:
                    try:
                        project_index = int(choice) - 1
                        if 0 <= project_index < len(projects):
                            project_name = projects[project_index]
                            current_project = load_project_data(project_name)
                            print(f"{Colors.GREEN}Loaded project: {project_name}{Colors.RESET}")
                        else:
                            print(f"{Colors.RED}Invalid choice. Please try again.{Colors.RESET}")
                            continue
                    except ValueError:
                        print(f"{Colors.RED}Invalid choice. Please try again.{Colors.RESET}")
                        continue
            else:
                project_name = input(f"{Colors.MAGENTA}No existing projects. Enter a new project name to start: {Colors.RESET}")
                current_project = load_project_data(project_name)

        user_input = input(f"{Colors.BRIGHT_WHITE}[{current_project['name']}] You: {Colors.RESET}")
        if user_input.lower() == 'exit':
            print(f"{Colors.YELLOW}Saving project \'{current_project['name']}\' and exiting.{Colors.RESET}")
            save_project_data(current_project)
            break
        
        response = process_user_input(user_input, current_project)
        print(f"{Colors.BRIGHT_GREEN}[{current_project['name']}] MCP: {response}{Colors.RESET}")

if __name__ == "__main__":
    main()


