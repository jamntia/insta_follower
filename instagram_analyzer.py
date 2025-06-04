import os
from dotenv import load_dotenv
from instagrapi import Client
from rich.console import Console
from rich.table import Table
from rich import print as rprint

def login_to_instagram(username, password):
    """Login to Instagram using provided credentials."""
    cl = Client()
    try:
        cl.login(username, password)
        return cl
    except Exception as e:
        rprint(f"[red]Error logging in: {str(e)}[/red]")
        return None

def get_non_followers(client):
    """Get list of users you follow who don't follow you back."""
    try:
        # Get your user ID
        user_id = client.user_id
        
        # Get followers and following
        followers = client.user_followers(user_id)
        following = client.user_following(user_id)
        
        # Find users you follow who don't follow you back
        non_followers = {
            user_id: user_info 
            for user_id, user_info in following.items() 
            if user_id not in followers
        }
        
        return non_followers
    except Exception as e:
        rprint(f"[red]Error getting non-followers: {str(e)}[/red]")
        return {}

def display_results(non_followers):
    """Display results in a formatted table."""
    console = Console()
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Username")
    table.add_column("Full Name")
    
    for user_info in non_followers.values():
        table.add_row(
            user_info.username,
            user_info.full_name
        )
    
    console.print("\n[bold green]Users who don't follow you back:[/bold green]")
    console.print(table)
    console.print(f"\nTotal: [bold cyan]{len(non_followers)}[/bold cyan] users don't follow you back")

def main():
    load_dotenv()
    
    # Get credentials from environment variables
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")
    
    if not username or not password:
        rprint("[red]Error: Please set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD in your .env file[/red]")
        return
    
    rprint("[yellow]Logging in to Instagram...[/yellow]")
    client = login_to_instagram(username, password)
    
    if client:
        rprint("[green]Successfully logged in![/green]")
        rprint("[yellow]Analyzing your followers and following...[/yellow]")
        
        non_followers = get_non_followers(client)
        if non_followers:
            display_results(non_followers)
        else:
            rprint("[red]Could not retrieve follower information.[/red]")
    
if __name__ == "__main__":
    main() 