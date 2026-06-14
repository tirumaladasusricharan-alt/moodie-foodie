import requests
import os
import sys

def deploy():
    print("\n" + "="*50)
    print("☁️ MOODIE FOODIE CLOUD DEPLOYER")
    print("="*50)
    
    username = input("\n👤 Enter your PythonAnywhere Username: ").strip()
    token = input("🔑 Enter your API Token (from Account -> API Token tab): ").strip()
    
    if not username or not token:
        print("❌ Error: Username and Token are required!")
        return

    base_url = f"https://www.pythonanywhere.com/api/v0/user/{username}/"
    headers = {'Authorization': f'Token {token}'}
    zip_path = "MoodieFoodie_Mobile.zip"

    if not os.path.exists(zip_path):
        print(f"❌ Error: {zip_path} not found! Run the ZIP command first.")
        return

    # 1. Upload File
    print(f"\n📤 1. Uploading {zip_path}...")
    with open(zip_path, 'rb') as f:
        response = requests.post(
            f"{base_url}files/path/home/{username}/{zip_path}",
            headers=headers,
            files={'content': f}
        )
    
    if response.status_code not in [200, 201]:
        print(f"❌ Upload failed: {response.text}")
        return
    print("✅ Upload successful!")

    # 2. Unzip (via Console)
    print("\n📦 2. Extracting files on server...")
    # Note: Starting a console and running a command is complex via API, 
    # but we can try to just create a task or a simple console command.
    # For now, we'll tell the user to run the unzip command in their console 
    # if the API console creation is restricted on free accounts.
    print("💡 Please go to your PythonAnywhere Consoles and run: unzip -o MoodieFoodie_Mobile.zip")

    # 3. Reload Web App
    domain = f"{username}.pythonanywhere.com"
    print(f"\n🔄 3. Reloading {domain}...")
    response = requests.post(
        f"{base_url}webapps/{domain}/reload/",
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"\n✨ SUCCESS! Your app is now LIVE at:")
        print(f"🔗 https://{domain}")
    else:
        print(f"\n⚠️ Uploaded, but couldn't reload automatically: {response.text}")
        print(f"💡 Go to the 'Web' tab and click 'Reload' manually.")

if __name__ == "__main__":
    deploy()
