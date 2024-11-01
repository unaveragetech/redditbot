
import sys

def main():
    # Check if arguments are provided
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command.startswith("!botrun(") and command.endswith(")"):
            # Extract script name and arguments
            inner_command = command[len("!botrun("):-1]
            if "-" in inner_command:
                script_name, arguments = inner_command.split("-", 1)
                print(f"Script name: {script_name}")
                print(f"Arguments: {arguments}")
            else:
                script_name, arguments = inner_command, ""
                print(f"Script name: {script_name}")
                print("No arguments provided.")
        else:
            print("Invalid command format. Use !botrun(script-name-arguments).")
    else:
        print("No command provided.")

if __name__ == "__main__":
    main()
