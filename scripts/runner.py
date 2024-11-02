import sys
import os
import subprocess

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command.startswith("!botrun(") and command.endswith(")"):
            # Extract script name and arguments
            inner_command = command[len("!botrun("):-1]
            if "-" in inner_command:
                script_name, arguments = inner_command.split("-", 1)
            else:
                script_name, arguments = inner_command, ""
            
            script_name = script_name.strip()
            arguments = arguments.strip()

            print(f"Running script: {script_name} with arguments: {arguments}")

            # Create a directory for results
            results_dir = f"results/{script_name}"
            os.makedirs(results_dir, exist_ok=True)

            # Run the script in a subprocess
            try:
                result = subprocess.run(
                    ["python", f"scripts/{script_name}"] + arguments.split(),
                    capture_output=True,
                    text=True
                )
                # Save output to a log file
                with open(os.path.join(results_dir, "output.log"), "w") as log_file:
                    log_file.write(result.stdout)
                    log_file.write(result.stderr)

                print("Script executed successfully.")
            except Exception as e:
                print(f"An error occurred: {e}")
        else:
            print("Invalid command format. Use !botrun(script-name-arguments).")
    else:
        print("No command provided.")

if __name__ == "__main__":
    main()
