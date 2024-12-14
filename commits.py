import requests
from datetime import datetime
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def analyze_commit_times(username, token=None):
    """
    Analyze GitHub commit patterns by hour of day for a given user.
    
    Parameters:
    username (str): GitHub username
    token (str, optional): GitHub personal access token for higher rate limits
    """
    # Setup authentication headers if token is provided
    headers = {'Authorization': f'token {token}'} if token else {}
    
    # Get user's repositories
    repos_url = f'https://api.github.com/users/{username}/repos'
    repos_response = requests.get(repos_url, headers=headers)
    
    # Check if the request was successful
    if repos_response.status_code != 200:
        print(f"Error fetching repositories: {repos_response.status_code}")
        print(f"Response: {repos_response.text}")
        return
    
    repos = repos_response.json()
    
    if not repos:
        print("No repositories found or error in API response")
        return
    
    # Collect commit times
    commit_hours = []
    
    for repo in repos:
        try:
            if isinstance(repo, dict) and not repo.get('fork', False):
                commits_url = f"https://api.github.com/repos/{username}/{repo['name']}/commits"
                commits_response = requests.get(commits_url, headers=headers)
                
                if commits_response.status_code != 200:
                    print(f"Skipping {repo['name']}: {commits_response.status_code}")
                    continue
                
                commits = commits_response.json()
                
                if isinstance(commits, list):
                    for commit in commits:
                        if commit.get('commit', {}).get('author', {}).get('date'):
                            commit_time = datetime.strptime(
                                commit['commit']['author']['date'],
                                '%Y-%m-%dT%H:%M:%SZ'
                            )
                            commit_hours.append(commit_time.hour)
        except Exception as e:
            print(f"Error processing repository: {e}")
            continue
    
    if not commit_hours:
        print("No commit data found")
        return
    
    # Create DataFrame and visualize
    df = pd.DataFrame({'hour': commit_hours})
    
    plt.figure(figsize=(12, 6))
    sns.histplot(data=df, x='hour', bins=24)
    plt.title(f'Distribution of Commit Times for {username}')
    plt.xlabel('Hour of Day (24-hour format)')
    plt.ylabel('Number of Commits')
    plt.xticks(range(0, 24))
    plt.grid(True, alpha=0.3)
    plt.show()
    
    # Print summary statistics
    hourly_counts = df['hour'].value_counts().sort_index()
    peak_hour = hourly_counts.idxmax()
    print(f"\nPeak coding hour: {peak_hour:02d}:00")
    print("\nTop 3 most active hours:")
    for hour, count in hourly_counts.nlargest(3).items():
        print(f"{hour:02d}:00 - {count} commits")

# Example usage
if __name__ == "__main__":
    username = "sharproller"
    # If you have a token, pass it as: analyze_commit_times(username, "your_token")
    analyze_commit_times(username)