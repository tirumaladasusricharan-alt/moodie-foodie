from huggingface_hub import HfApi
import os

TOKEN = "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"
REPO_ID = "SRICHARAN3103/MoodieFoodie"

def deploy():
    print(f"\nSTARTING DEPLOYMENT FOR SRICHARAN3103...")
    api = HfApi()

    try:
        # 1. Create the Space (if not exists)
        print(f"Checking if Space {REPO_ID} exists...")
        api.create_repo(
            repo_id=REPO_ID,
            token=TOKEN,
            repo_type="space",
            space_sdk="docker",
            exist_ok=True
        )
        print("OK: Space is ready!")

        # 2. Upload everything
        print("\nUploading project files to Hugging Face...")
        
        # We'll upload individual files to avoid uploading huge build/dist folders
        files_to_upload = [
            "app.py", "database.py", "moodie_engine.py", "moodie_model.pkl", 
            "moodie_labels.pkl", "moodie_foodie.db", "requirements.txt", "Dockerfile",
            "food_data.py"
        ]
        
        for file in files_to_upload:
            if os.path.exists(file):
                print(f" - Sending {file}...")
                api.upload_file(
                    path_or_fileobj=file,
                    path_in_repo=file,
                    repo_id=REPO_ID,
                    repo_type="space",
                    token=TOKEN
                )

        # Upload folders
        for folder in ["templates", "static"]:
            if os.path.exists(folder):
                print(f" - Sending folder {folder}...")
                api.upload_folder(
                    folder_path=folder,
                    path_in_repo=folder,
                    repo_id=REPO_ID,
                    repo_type="space",
                    token=TOKEN
                )

        print(f"\nDEPLOYMENT COMPLETE!")
        print(f"Link: https://huggingface.co/spaces/{REPO_ID}")

    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    deploy()
