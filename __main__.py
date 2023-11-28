import subprocess

def clean_data():
    try:
        # Remove the CSV files
        subprocess.run(["rm", "data/processed_data.csv"], check=True)
        subprocess.run(["rm", "data/scaled_data.csv"], check=True)
        # Clean the models directory from any previous runs
        subprocess.run(["rm", "-rf", "models"], check=True)
        print("Data cleaned successfully.")
    except subprocess.CalledProcessError:
        print("An error occurred while cleaning the data.")


def run_script(script_name):
    try:
        subprocess.run(["python", script_name], check=True)
        print(f"Script {script_name} executed successfully.")
    except subprocess.CalledProcessError:
        print(f"An error occurred while executing {script_name}.")


if __name__ == "__main__":
    # Clean the data
    clean_data()
    scripts = [
        "data_preparation.py",
        "feature_engineering.py",
        "model.py",
        "train.py",
        "predict.py"
    ]

    for script in scripts:
        run_script(script)