import requests
import os
from datetime import datetime
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import timezone
import pytz
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


def analyze_commit_times(username, token=None, local_timezone=None):
    """
    Analyze GitHub commit patterns by hour of day for a given user.
    
    Parameters:
    username (str): GitHub username
    token (str, optional): GitHub personal access token for higher rate limits
    local_timezone (str, optional): Timezone name (e.g., 'America/New_York', 'Europe/London')
    """
    # Setup authentication headers if token is provided
    headers = {'Authorization': f'token {token}'} if token else {}
    
    # Set up timezone
    if local_timezone:
        local_tz = pytz.timezone(local_timezone)
    
    # Get user's repositories
    repos_url = f'https://api.github.com/users/{username}/repos'
    repos_response = requests.get(repos_url, headers=headers)
    
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
                            # Parse the UTC timestamp
                            utc_time = datetime.strptime(
                                commit['commit']['author']['date'],
                                '%Y-%m-%dT%H:%M:%SZ'
                            )
                            utc_time = utc_time.replace(tzinfo=timezone.utc)
                            
                            # Convert to local timezone if specified
                            if local_timezone:
                                local_time = utc_time.astimezone(local_tz)
                                commit_hours.append(local_time.hour)
                            else:
                                commit_hours.append(utc_time.hour)
        except Exception as e:
            print(f"Error processing repository: {e}")
            continue
    
    if not commit_hours:
        print("No commit data found")
        return
    
    # Create DataFrame and visualize
    df = pd.DataFrame({'hour': commit_hours})
    
    plt.figure(figsize=(12, 6))
    sns.histplot(data=df, x='hour', bins=24, stat='density', kde=False)
    timezone_label = f"({local_timezone})" if local_timezone else " (UTC)"
    plt.title(f'Github Commits by Hour - for {username}')
    plt.xlabel(f'Hour of Day {timezone_label}')
    plt.ylabel('Percentage of Commits')
    plt.xticks(range(0, 24, 3))  # Set x-axis labels every 3 hours
    plt.gca().xaxis.set_major_formatter(FuncFormatter(format_hour))
    plt.gca().yaxis.set_major_formatter(FuncFormatter(format_percentage))
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('results/commits_by_hour.png')
    plt.show()

def format_hour(x, pos):
    """Convert 24-hour format to 12-hour am/pm format."""
    hour = int(x) % 24
    if hour == 0:
        return "12 AM"
    elif hour < 12:
        return f"{hour} AM"
    elif hour == 12:
        return "12 PM"
    else:
        return f"{hour - 12} PM"

def format_percentage(y, pos):
    """Format y-axis labels as percentages."""
    return f'{100 * y:.0f}%'


if __name__ == "__main__":
    analyze_commit_times(
        username = "alecsharpie",
        token = os.environ.get('GITHUB_TOKEN'),
        local_timezone = "Australia/Sydney"
    )