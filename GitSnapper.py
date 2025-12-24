#!/usr/bin/env python3
import requests
import os
import math
import sys
import zipfile
import time

def get_total_repos(username):
    url = f"https://api.github.com/users/{username}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        user_data = response.json()
        
        # Check if user exists
        if "message" in user_data and user_data["message"] == "Not Found":
            return -1  # User doesn't exist
            
        return user_data.get("public_repos", 0)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return -1  # User doesn't exist
        else:
            print(f"HTTP Error: {e}")
            return 0
    except requests.exceptions.RequestException as e:
        print(f"Network Error: {e}")
        return 0
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 0

def get_repos_info(username, per_page=100):
    total_repos = get_total_repos(username)
    
    # Check if user doesn't exist
    if total_repos == -1:
        return None  # Special value to indicate user doesn't exist
    
    if total_repos == 0:
        return []  # User exists but has no repos
    
    print(f"\nFound total {total_repos} repositories.\n")
    pages = math.ceil(total_repos / per_page)
    
    repos_info = []
    for page in range(1, pages + 1):
        url = f"https://api.github.com/users/{username}/repos?per_page={per_page}&page={page}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Handle API errors
            if isinstance(data, dict) and "message" in data:
                print(f"API Error: {data['message']}")
                break
                
            for repo in data:
                repos_info.append({
                    "name": repo["name"],
                    "clone_url": repo["clone_url"],
                    "html_url": repo["html_url"],
                    "description": repo.get("description", ""),
                    "size": repo.get("size", 0)
                })
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            break
        except Exception as e:
            print(f"Unexpected error on page {page}: {e}")
            break
    
    return repos_info

def download_repo_as_zip(repo_info, username):
    repo_name = repo_info["name"]
    
    # Create user directory
    os.makedirs(username, exist_ok=True)
    
    # Check if ZIP already exists
    zip_path = os.path.join(username, f"{repo_name}.zip")
    if os.path.exists(zip_path):
        print(f"Skipping already downloaded: {repo_name}")
        return True, "Already exists", repo_name

    zip_url = f"https://github.com/{username}/{repo_name}/archive/refs/heads/main.zip"
    
    try:
        print(f"Downloading: {repo_name}")
        
        # Try main branch first, then master
        response = requests.get(zip_url, timeout=30, stream=True)
        
        # If main branch not found, try master branch
        if response.status_code == 404:
            zip_url = f"https://github.com/{username}/{repo_name}/archive/refs/heads/master.zip"
            response = requests.get(zip_url, timeout=30, stream=True)
        
        # If still 404, try the default branch from API
        if response.status_code == 404:
            # Get default branch info
            repo_api_url = f"https://api.github.com/repos/{username}/{repo_name}"
            repo_response = requests.get(repo_api_url, timeout=10)
            if repo_response.status_code == 200:
                repo_data = repo_response.json()
                default_branch = repo_data.get("default_branch", "main")
                zip_url = f"https://github.com/{username}/{repo_name}/archive/refs/heads/{default_branch}.zip"
                response = requests.get(zip_url, timeout=30, stream=True)
        
        response.raise_for_status()
        
        # Get file size for progress tracking
        total_size = int(response.headers.get('content-length', 0))
        
        # Download and save the ZIP file
        with open(zip_path, 'wb') as f:
            if total_size == 0:
                f.write(response.content)
            else:
                downloaded = 0
                chunk_size = 8192
                
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # Show progress
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"   Progress: {progress:.1f}% ({downloaded}/{total_size} bytes)", end='\r')
        
        # Verify the ZIP file is valid
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                if zip_ref.testzip() is not None:
                    print(f"   Warning: ZIP file for {repo_name} may be corrupted")
                else:
                    # Count files in ZIP
                    file_count = len(zip_ref.namelist())
                    print(f"Downloaded: {repo_name}.zip ({file_count} files)")
                    return True, "Success", repo_name
                    
        except zipfile.BadZipFile:
            print(f" Invalid ZIP file for {repo_name}")
            os.remove(zip_path)  # Remove corrupted file
            return False, "Invalid ZIP", repo_name
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f" Repository not found or empty: {repo_name}")
            return False, "Not found", repo_name
        else:
            print(f" HTTP Error for {repo_name}: {e}")
            return False, f"HTTP Error: {e}", repo_name
    except requests.exceptions.RequestException as e:
        print(f" Network Error for {repo_name}: {e}")
        return False, f"Network Error: {e}", repo_name
    except Exception as e:
        print(f" Error downloading {repo_name}: {e}")
        return False, f"Error: {e}", repo_name

def download_all_repos(repos_info, username):
    if not repos_info:
        print("No repositories found to download.")
        return
    
    print(f"\nStarting download of {len(repos_info)} repositories")
    
    successful = 0
    failed = 0
    skipped = 0
        
    for i, repo_info in enumerate(repos_info, 1):
        print(f"\n[{i}/{len(repos_info)}] ", end='')
        
        # Download the repository
        success, status, repo_name = download_repo_as_zip(repo_info, username)
        
        # Update counters
        if status == "Already exists":
            skipped += 1
        elif success:
            successful += 1
        else:
            failed += 1
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
    # Summary
    print("\n" + "="*50)
    print("DOWNLOAD COMPLETED:")
    print(f"Successful downloads: {successful}")
    print(f"Already existed (skipped): {skipped}")
    print(f"Failed downloads: {failed}")
    print(f"Total repositories: {len(repos_info)}")
    print(f"Files saved to: {username}/")
    print("="*50)

def main():
    print("="*50)
    print("GitHub Repository Downloader (ZIP Format)")
    print("="*50)
    
    # Get username
    username = input("Enter GitHub username: ").strip()
    
    if not username:
        print("Username cannot be empty.")
        sys.exit(1)
    
    # Get repository information
    print(f"\nFetching information for {username}")
    repos_info = get_repos_info(username)
    
    # Check if user exists
    if repos_info is None:
        print(f"\nUser '{username}' does not exist on GitHub.")
        sys.exit(1)
    
    # Check if user has repositories
    if not repos_info:
        print(f"\n{username} has no public repositories.")
        sys.exit(1)
    
    # Display repository list
    for i, repo in enumerate(repos_info, 1):
        print(f"  {i:3d}. {repo['name']}")
        if repo['description']:
            print(f"       {repo['description'][:80]}...")
    
    # Confirm before downloading
    confirm = input("\nDo you want to continue? (y/n): ").strip().lower()
    
    if confirm not in ['y', 'yes']:
        print("Download cancelled by user.")
        return
    
    # Download all repositories
    download_all_repos(repos_info, username)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)