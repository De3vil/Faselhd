# -*- coding: utf-8 -*-
# Author: Abdulrahman Mohammed (De3vil)
# Don't touch my code, it's art 
# +=============================
import os
import sys
import subprocess
import requests
import zipfile
import io
import shutil
import re
import asyncio
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeRemainingColumn, ProgressColumn
from rich.text import Text
if hasattr(sys, '_MEIPASS'):
    os.environ["PLAYWRIGHT_CLI_EXECUTABLE"] = os.path.join(sys._MEIPASS, "playwright.exe")
from playwright.async_api import async_playwright

console = Console()

os.system('start chrome fb.com/De3vil.3')

def download_and_extract_zip(url, extract_to):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        z.extractall(extract_to)

def add_path_to_environment(new_path):
    current_path = os.environ.get("PATH", "")
    if new_path.lower() not in current_path.lower():
        new_path_combined = new_path if not current_path else current_path + os.pathsep + new_path
        subprocess.run(["setx", "PATH", new_path_combined], capture_output=True, text=True, shell=True)

def find_ffmpeg_directory(root_dir):
    for dirpath, _, filenames in os.walk(root_dir):
        if "ffmpeg.exe" in filenames:
            return dirpath
    return None

def find_chromium_executable(root_dir):
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower() in ["chrome.exe", "chromium.exe"]:
                return dirpath
    return None

def is_ffmpeg_installed():
    try:
        result = subprocess.run(['ffmpeg', "-version"], capture_output=True, text=True)
        output = result.stdout.lower()
        if "ffmpeg version" in output:
            return True
        else:
            return False
    except Exception:
        return False

def is_chromium_installed(browsers_path):
    chromium_dir = find_chromium_executable(browsers_path)
    return chromium_dir is not None

def setup_ffmpeg():
    user_home = Path(os.getenv("APPDATA") or Path.home())
    extract_to = user_home / "ffmpeg"
    
    if is_ffmpeg_installed():
        return
    else:
        console.print("[blue]Downloading ffmpeg...")
        url = "https://github.com/De3vil/ffmpeg/releases/download/v1/ffmpeg-1009.zip"
        os.makedirs(extract_to, exist_ok=True)
        download_and_extract_zip(url, extract_to)
        ffmpeg_dir = find_ffmpeg_directory(extract_to)
        if ffmpeg_dir:
            add_path_to_environment(ffmpeg_dir)
            console.print("[green]ffmpeg downloaded and added to PATH.[/green]")
        else:
            console.print("[red]Failed to locate ffmpeg after extraction.[/red]")

def setup_chromium():
    browsers_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Roaming", "browsers")
    os.makedirs(browsers_path, exist_ok=True)
    
    if is_chromium_installed(browsers_path):
        console.print("[green]Chromium is already installed.[/green]")
        return
    else:
        console.print("[blue]Downloading Chromium...")
        url = "https://playwright-verizon.azureedge.net/builds/chromium/1117/chromium-win64.zip"
        download_and_extract_zip(url, browsers_path)
        chromium_dir = find_chromium_executable(browsers_path)
        if chromium_dir:
            add_path_to_environment(chromium_dir)
            console.print("[green]Chromium downloaded and added to PATH.[/green]")
        else:
            console.print("[red]Failed to locate Chromium after extraction.[/red]")

setup_ffmpeg()
setup_chromium()


banner = """
[red]███████ [yellow]███████ [cyan]██   ██ ██████  
[red]██      [yellow]██      [cyan]██   ██ ██   ██ 
[red]█████   [yellow]███████ [cyan]███████ ██   ██ 
[red]██       [yellow]    ██ [cyan]██   ██ ██   ██ 
[red]██      [yellow]███████ [cyan]██   ██ ██████                                
               [white][[red]=>[/red]][/white] [yellow]Created by[red]:[/red][bold red]Abdulrahman Mohammed[/bold red][white]([cyan]De3vil[/cyan])[/white] [white][[red]<=[/red]][/white]
             \___________________________________________________/  
"""
console.print(banner)

class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
    async def start(self):
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(os.environ["USERPROFILE"], "AppData", "Roaming", "browsers")
        self.playwright = await async_playwright().start()
        browsers_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Roaming", "browsers")
        chromium_dir = find_chromium_executable(browsers_path)
        if chromium_dir:
            executable = os.path.join(chromium_dir, "chrome.exe")
            self.browser = await self.playwright.chromium.launch(executable_path=executable, headless=True)
        else:
            self.browser = await self.playwright.chromium.launch(headless=True)
    async def new_page(self):
        return await self.browser.new_page()
    async def close(self):
        await self.browser.close()
        await self.playwright.stop()

async def search(browser_manager, user_input):
    search_URL = "https://www.faselhd.pro/?s=" + user_input.strip()
    page = await browser_manager.new_page()
    try:
        await page.goto(search_URL, timeout=60000)
        await page.wait_for_selector(".postDiv", timeout=30000)
        content = await page.content()
    except Exception as e:
        console.print(f"[red]Error during search: {e}[/red]")
        content = ""
    finally:
        await page.close()
    soup = BeautifulSoup(content, "html.parser")
    results = soup.select(".postDiv")
    tit_url = [(i.select_one(".h1").text.strip(), i.a["href"]) for i in results if i.select_one(".h1") and i.a]
    return dict(tit_url)

async def extract_seasons(browser_manager, series_url):
    base_url = "https://web184.faselhd.cafe"
    full_url = urljoin(base_url, series_url)
    seasons_links = []
    page = await browser_manager.new_page()
    try:
        await page.goto(full_url, timeout=60000)
        await page.wait_for_load_state('networkidle', timeout=60000)
        if await page.is_visible('div.seasonDiv'):
            await page.wait_for_selector('div.seasonDiv', timeout=30000)
            seasons = await page.query_selector_all('div.seasonDiv')
            for season in seasons:
                onclick_attr = await season.get_attribute('onclick')
                if onclick_attr and 'window.location.href' in onclick_attr:
                    link = onclick_attr.split("'")[1]
                    full_season_link = urljoin(base_url, link)
                    seasons_links.append(full_season_link)
    except Exception as e:
        console.print(f"[red]Error extracting seasons: {e}[/red]")
    finally:
        await page.close()
    return seasons_links

async def extract_episodes(browser_manager, season_url):
    episode_links = []
    page = await browser_manager.new_page()
    try:
        await page.goto(season_url, timeout=60000)
        await page.wait_for_load_state('networkidle', timeout=60000)
        await page.wait_for_selector('xpath=/html/body/div[4]/div/div[5]/div[1]/div/div[2]', timeout=30000)
        episodes = await page.query_selector_all('xpath=/html/body/div[4]/div/div[5]/div[1]/div/div[2]//a')
        for episode in episodes:
            href = await episode.get_attribute('href')
            if href:
                episode_links.append(href)
    except Exception as e:
        console.print(f"[red]Error extracting episodes: {e}[/red]")
    finally:
        await page.close()
    return episode_links

def filter_episode_links(links):
    return [link for link in links if "episodes" in link]

def normalize_url(url):
    return url.rstrip('/').lower()

async def extract_movie_links(browser_manager, movie_url):
    page = await browser_manager.new_page()
    try:
        await page.goto(movie_url, timeout=60000)
        selector = 'xpath=/html/body/div[5]/div[4]/div/div[2]/div[1]/div/div[2]/div/div/iframe'
        await page.wait_for_selector(selector, timeout=30000)
        iframe_element = await page.query_selector(selector)
        iframe_src = await iframe_element.get_attribute('src') if iframe_element else None
        if iframe_element and iframe_src:
            return [movie_url]
        return []
    except Exception as e:
        console.print(f"[red]Error extracting movie links: {e}[/red]")
        return []
    finally:
        await page.close()

class TightBarColumn(ProgressColumn):
    def __init__(self, width: int = 40):
        self.width = width
        super().__init__()
    def render(self, task):
        complete = int(task.percentage / 100 * self.width)
        incomplete = self.width - complete
        text = Text()
        text.append("━" * complete, style="magenta")
        text.append("━" * incomplete, style="grey37")
        return text

async def download_video_threaded(browser_manager, page_url, quality, video_name, progress, video_type="episode"):
    try:
        page = await browser_manager.new_page()
        await page.goto(page_url, timeout=60000)
        if video_type == "episode":
            selector = 'xpath=/html/body/div[5]/div[5]/div[1]/div/div[2]/div[1]/div/div[2]/div/div/iframe'
        else:
            selector = 'xpath=/html/body/div[5]/div[4]/div/div[2]/div[1]/div/div[2]/div/div/iframe'
        await page.wait_for_selector(selector, timeout=30000)
        iframe_element = await page.query_selector(selector)
        if not iframe_element:
            console.print(f"[red]Video source not found for {video_name}[/red]")
            await page.close()
            return
        iframe_src = await iframe_element.get_attribute('src')
        if not iframe_src:
            console.print(f"[red]Iframe src not found for {video_name}[/red]")
            await page.close()
            return
        iframe = await iframe_element.content_frame()
        iframe_content = await iframe.content()
        soup = BeautifulSoup(iframe_content, 'html.parser')
        quality_links = {'1080': [], '720': [], '360': []}
        for element in soup.find_all():
            for attr in ['href', 'src', 'data-url']:
                link = element.get(attr)
                if link and '.m3u8' in link:
                    absolute_link = urljoin(iframe_src, link)
                    if '1080' in absolute_link:
                        quality_links['1080'].append(absolute_link)
                    elif '720' in absolute_link:
                        quality_links['720'].append(absolute_link)
                    elif '360' in absolute_link:
                        quality_links['360'].append(absolute_link)
                    else:
                        quality_links['1080'].append(absolute_link)
        available_qualities = {k: v for k, v in quality_links.items() if v}
        if not available_qualities:
            console.print(f"[red]No available qualities found for {video_name}[/red]")
            await page.close()
            return
        quality_order = ['1080', '720', '360']
        highest_quality = next((q for q in quality_order if q in available_qualities), None)
        if quality in available_qualities:
            selected_link = available_qualities[quality][0]
            progress.console.print(f"\n[green]Starting download in {quality}p quality[/green]")
        else:
            progress.console.print(f"\n[red]Selected quality not available, downloading {highest_quality}p[/red]")
            selected_link = available_qualities[highest_quality][0]
        if selected_link:
            output_path = os.path.expanduser(
                f"~/Downloads/{video_name}.mp4" if video_type == "episode" 
                else f"~/Downloads/{video_name}_{highest_quality if quality not in available_qualities else quality}.mp4"
            )
            if hasattr(sys, '_MEIPASS'):
                downloadm3u8_path = os.path.join(sys._MEIPASS, "downloadm3u8.exe")
            else:
                downloadm3u8_path = "downloadm3u8.exe"
            command = [downloadm3u8_path, '-o', output_path, selected_link]
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            task_id = progress.add_task(f"Downloading {video_name}...", total=100)
            last_percent = 0
            while True:
                line_bytes = await process.stdout.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode('utf-8', errors='replace')
                percent_match = re.search(r'(\d{1,3})%', line)
                if percent_match:
                    new_percent = int(percent_match.group(1))
                    if new_percent > last_percent:
                        progress.update(task_id, completed=new_percent)
                        last_percent = new_percent
                if 'Download completed' in line:
                    progress.update(task_id, completed=100)
                    break
            progress.console.print()
            await process.wait()
        await page.close()
    except Exception as e:
        console.print(f"[red]Error downloading {video_name}: {e}[/red]")

async def De3vil():
    browser_manager = BrowserManager()
    await browser_manager.start()
    current_series = None
    is_movie = False
    try:
        while True:
            if current_series is None:
                user_input = console.input("\n[cyan]Enter the name (or [red]exit[/red] to quit)[red]:[/red] ")
                if user_input.lower() == 'exit':
                    break
                search_results = await search(browser_manager, user_input)
                if not search_results:
                    console.print("[red]No results found.[/red]")
                    continue
                console.print("\n[magenta]Search results:[/magenta]")
                items = list(search_results.items())
                for idx, (title, url) in enumerate(items, 1):
                    console.print(f"[blue]{idx}[/blue][red]:[/red][white] {title}[/white]")
                try:
                    choice = int(console.input("\nChoose a number: ")) - 1
                    selected_title, selected_url = items[choice]
                except (ValueError, IndexError):
                    console.print("[red]Invalid selection![/red]")
                    continue
                seasons = await extract_seasons(browser_manager, selected_url)
                current_series = {'title': selected_title, 'url': selected_url, 'seasons': seasons}
                is_movie = not bool(seasons)
            if is_movie:
                movie_links = await extract_movie_links(browser_manager, current_series['url'])
                if not movie_links:
                    console.print("[red]No movie links found.[/red]")
                    current_series = None
                    continue
                console.print("\n[green]Available qualities:[/green]")
                console.print("[white][[blue]1[/blue]] 1080[/white]")
                console.print("[white][[blue]2[/blue]] 720p[/white]")
                console.print("[white][[blue]3[/blue]] 360p[/white]")
                quality_choice = console.input("[cyan]Choose quality number [red]:[/red][/cyan] ")
                quality_map = {'1': '1080', '2': '720', '3': '360'}
                selected_quality = quality_map.get(quality_choice, '1080')
                movie_name = re.sub(r'[^a-zA-Z0-9_]', '', current_series['title'].replace(" ", "_"))
                with Progress(
                    SpinnerColumn(spinner_name="dots"),
                    TextColumn("[progress.description]{task.description}", style="white"),
                    TightBarColumn(width=40),
                    TextColumn("{task.percentage:>3.0f}%", style="bold white"),
                    TimeRemainingColumn()
                ) as progress:
                    await download_video_threaded(browser_manager, current_series['url'], selected_quality, movie_name, progress, video_type="movie")
                while True:
                    console.print("\n[green]What would you like to do next?[/green]")
                    console.print("[white][[blue]1[/blue]] Search again[/white]")
                    console.print("[white][[blue]2[/blue]] Exit[/white]")
                    next_choice = console.input("[cyan]Enter your choice [red]:[/red][/cyan] ")
                    if next_choice == '1':
                        current_series = None
                        break
                    elif next_choice == '2':
                        sys.exit(0)
                    else:
                        console.print("[red]Invalid choice![/red]")
                continue
            else:
                while True:
                    console.print(f"\n[yellow]Found {len(current_series['seasons'])} seasons:[/yellow]")
                    for idx, link in enumerate(current_series['seasons'], 1):
                        console.print(f"[blue]{idx}[/blue][red]:[/red][white] {link}[/white]")
                    season_choice = console.input("\n[cyan]Choose season number (or [bright_red]back[/bright_red] to search again)[red]:[/red][/cyan] ")
                    if season_choice.lower() == 'back':
                        current_series = None
                        break
                    try:
                        season_index = int(season_choice) - 1
                        season_number = season_index + 1
                        selected_season_url = current_series['seasons'][season_index]
                    except (ValueError, IndexError):
                        console.print("[red]Invalid season selection![/red]")
                        continue
                    episodes_raw = await extract_episodes(browser_manager, selected_season_url)
                    episode_links = filter_episode_links(episodes_raw)
                    if not episode_links:
                        console.print("[red]No episodes found.[/red]")
                        break
                    unique_links = []
                    seen = set()
                    for link in episode_links:
                        norm = normalize_url(link)
                        if norm not in seen:
                            seen.add(norm)
                            unique_links.append(link)
                    stored_episode_links = unique_links
                    while True:
                        console.print(f"\n[yellow]Found {len(stored_episode_links)} episodes:[/yellow]")
                        for idx, link in enumerate(stored_episode_links, 1):
                            decoded_url = unquote(link)
                            console.print(f"[blue]{idx}[/blue][red]:[/red][white] {decoded_url}[/white]")
                        episodes_input = console.input("\n[cyan]Enter episode numbers (e.g., 1 or 1,2,3)[red]:[/red][/cyan] ")
                        try:
                            selected_episode_indices = [int(x.strip()) - 1 for x in episodes_input.split(",")]
                        except ValueError:
                            console.print("[red]Invalid input![/red]")
                            continue
                        console.print("\n[green]Available qualities:[/green]")
                        console.print("[white][[blue]1[/blue]] 1080[/white]")
                        console.print("[white][[blue]2[/blue]] 720p[/white]")
                        console.print("[white][[blue]3[/blue]] 360p[/white]")
                        quality_choice = console.input("[cyan]Choose quality number [red]:[/red][/cyan] ")
                        quality_map = {'1': '1080', '2': '720', '3': '360'}
                        selected_quality = quality_map.get(quality_choice, '1080')
                        series_title_sanitized = re.sub(r'[^a-zA-Z0-9_]', '', current_series['title'].replace(" ", "_"))
                        progress = Progress(
                            SpinnerColumn(spinner_name="dots"),
                            TextColumn("[progress.description]{task.description}", style="white"),
                            TightBarColumn(width=40),
                            TextColumn("{task.percentage:>3.0f}%", style="bold white"),
                            TimeRemainingColumn()
                        )
                        tasks = []
                        with progress:
                            for ep_idx in selected_episode_indices:
                                if 0 <= ep_idx < len(stored_episode_links):
                                    episode_url = stored_episode_links[ep_idx]
                                    video_name = f"{series_title_sanitized}_S{season_number:02d}_E{ep_idx+1:02d}_{selected_quality}"
                                    tasks.append(
                                        download_video_threaded(
                                            browser_manager,
                                            episode_url,
                                            selected_quality,
                                            video_name,
                                            progress,
                                            "episode"
                                        )
                                    )
                                else:
                                    console.print(f"[red]Invalid episode number: {ep_idx + 1}[/red]")
                            await asyncio.gather(*tasks)
                        while True:
                            console.print("\n[green]What would you like to do next?[/green]")
                            console.print("[white][[blue]1[/blue]] Search again[/white]")
                            console.print("[white][[blue]2[/blue]] Choose another season[/white]")
                            console.print("[white][[blue]3[/blue]] Choose other episodes for the same season[/white]")
                            console.print("[white][[blue]4[/blue]] Exit[/white]")
                            next_choice = console.input("[cyan]Enter your choice [red]:[/red][/cyan] ")
                            if next_choice == '1':
                                current_series = None
                                break
                            elif next_choice == '2':
                                break
                            elif next_choice == '3':
                                break
                            elif next_choice == '4':
                                sys.exit(0)
                            else:
                                console.print("[red]Invalid choice![/red]")
                        if next_choice in ['1', '2']:
                            break
                        if next_choice == '3':
                            continue
                    if current_series is None:
                        break
                    else:
                        break
                if current_series is None:
                    continue
    finally:
        await browser_manager.close()

if __name__ == "__main__":
    asyncio.run(De3vil())
