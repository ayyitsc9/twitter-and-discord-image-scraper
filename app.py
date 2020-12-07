# - - - -  - - - - - - - - - - - - - - - - - - -  - - - - - - - -
import subprocess, sys, os, platform, glob, json, time
from pathlib import Path
import datetime
from datetime import datetime
# - - - -  - - - - - - - - - - - - - - - - - - -  - - - - - - - -

try:
    import wget, tweepy, requests
    from tweepy import OAuthHandler
    from colorama import init, Fore, Back, Style
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'wget'])
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'tweepy'])
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'colorama'])

# - - - -  - - - - - - - - - - - - - - - - - - -  - - - - - - - -
# Initializing Colorama || Utils
init(convert=True) if platform.system() == "Windows" else init()
print(f"{Fore.CYAN} {Style.BRIGHT} --- Script Created by @ayyitsc9 ---\n")
# - - - -  - - - - - - - - - - - - - - - - - - -  - - - - - - - -
# Initiliazing Tweepy
def init_tweepy():
    global api
    auth = tweepy.OAuthHandler(CONSUMER_API_KEY, CONSUMER_API_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

# - - - -  - - - - - - - - - - - - - - - - - - -  - - - - - - - -
# Initializing Settings
def init_settings():
    with open("settings.json", "r") as settings:
        data = json.load(settings)
        # Separated global calls for easier readability
        global path, number_of_tweets, screen_name, use_date_filter, date_filter
        global CONSUMER_API_KEY, CONSUMER_API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
        global bot_token, number_of_messages, channel_id

        # General Variables
        path = data['folder_path'] # When inputting path in settings.json, make sure to escape the slashes. (Make every single slash a double slash) Ex : C:\\Scripts\\Image Scraper\\Images
        if path == "" or path == None or not os.path.exists(path):
            path = os.path.realpath(sys.argv[0])
        print(path)
        use_date_filter = data['use_date_filter']
        date_filter = data['date_filter'] # Format : (YYYY/MM/DD HH:MM:SS) (Ex : [2020, 12, 5, 0, 0, 0])

        # Twitter Specific Variables
        number_of_tweets = data['number_of_tweets_to_scrape']
        screen_name = data['screen_name']

        CONSUMER_API_KEY = data['CONSUMER_API_KEY']
        CONSUMER_API_SECRET = data['CONSUMER_API_SECRET']
        ACCESS_TOKEN = data['ACCESS_TOKEN']
        ACCESS_TOKEN_SECRET = data['ACCESS_TOKEN_SECRET']
        
        # Discord Specific Variables
        bot_token = data['discord']['bot_token']
        number_of_messages = data['discord']['max_number_of_messages_to_scrape']
        channel_id = data['discord']['channel_id_to_scrape']

# - - - -  - - - - - - - - - - - - - - - - - - -  - - - - - - - -

lightblue = "\033[94m"
orange = "\033[33m"

class Logger:
    @staticmethod
    def timestamp():
        return str(datetime.now())[:-7]
    @staticmethod
    def normal(message):
        print(f"{lightblue}[{Logger.timestamp()}] {message}")
    @staticmethod
    def other(message):
        print(f"{orange}[{Logger.timestamp()}] {message}")
    @staticmethod
    def error(message):
        print(f"{Fore.RED}[{Logger.timestamp()}] {message}")
    @staticmethod
    def success(message):
        print(f"{Fore.GREEN}[{Logger.timestamp()}] {message}")

# - - - -  - - - - - - - - - - - - - - - - - - -  - - - - - - - -

class TwitterImageScraper:
    def __init__(self, path, num_tweets, screen_name):
        self.path, self.num_tweets, self.screen_name = path, num_tweets, screen_name
        Logger.normal(f"Starting Twitter Image Scraper on {screen_name}...")
        self.get_recent_tweets()
        self.download_media()

    def get_recent_tweets(self):
        # This will contain our media file urls
        self.media_files = []
        
        # This will contain the path to our images
        self.media_files_paths = []

        # Scrapes latest tweets on the specified users' timeline based on screen name and number of tweets to scrape provided
        try:
            for status in tweepy.Cursor(api.user_timeline, screen_name=self.screen_name, tweet_mode="extended").items(self.num_tweets):
                # Check if use_date_filter is True
                if use_date_filter:
                    # Setting date filter (YYYY/MM/DD HH:MM:SS)
                    self.date_filter = datetime(date_filter[0],  date_filter[1], date_filter[2], date_filter[3], date_filter[4], date_filter[5])
                    if self.date_filter <= status.created_at:
                        self.find_media_urls(status)
                    else:
                        Logger.other(f"Date filter reached ({str(date_filter)}). Stopped iteration!")
                        break
                else:
                    self.find_media_urls(status)
            Logger.success("Filtered through messages")
        except Exception as e:
            Logger.error(f"Make sure your keys and tokens in settings.json are correct! Error : {e}")
                
    def find_media_urls(self, status):
        try:
            media = status.retweeted_status.extended_entities.get('media', [])
            if (len(media) > 1):
                for x in range(len(media)):
                    self.media_files.append(media[x]['media_url_https'])
                    self.media_files_paths.append(media[x]['media_url_https'].split("/")[4])
            elif (len(media) > 0):
                self.media_files.append(media[0]['media_url_https'])
                self.media_files_paths.append(media[0]['media_url_https'].split("/")[4])
        except:
            Logger.error(f"Invalid tweet detected. Typical Causes : Non-retweeted tweet by {self.screen_name}/ YouTube or Other Link Post")
            pass

    def download_media(self):
        if len(self.media_files) == 0:
            Logger.normal(f"No files to download!")
        else:
            Logger.normal(f"Downloading {len(self.media_files)} files...")
        already_exists = 0
        downloaded = 0
        for x in range(len(self.media_files)):
            if not Path("{}\{}".format(self.path, self.media_files_paths[x])).exists():
                # Checks if file type of self is DiscordImageScraper object
                if type(self) is DiscordImageScraper:
                    response = requests.get(self.media_files[x], stream=True)
                    if response.status_code == 200:
                        with open(f"{self.path}\{self.media_files_paths[x]}", "wb") as save_file:
                            save_file.write(response.content)
                    else:
                        Logger.error(f"Failed Request! Status Code : {response.status_code}")
                # Checks if file type of self is TwitterImageScraper object
                elif type(self) is TwitterImageScraper:
                    wget.download(self.media_files[x], self.path)
                downloaded += 1
            else:
                already_exists += 1
        Logger.success(f"Downloaded [{str(downloaded)}]\t\t\tFile Already Exists [{str(already_exists)}]\n")

# - - - -  - - - - - - - - - - - - - - - - - - -  - - - - - - - -

class DiscordImageScraper(TwitterImageScraper):
    def __init__(self, path, num_messages, channel_id):
        self.path, self.num_messages, self.channel_id = path, num_messages, channel_id
        self.get_recent_messages()
        self.find_media_urls()
        self.download_media()
    
    def get_recent_messages(self):
        # This will contain our media file urls
        self.media_files = []
        
        # This will contain the path to our images
        self.media_files_paths = []

        # Scrapes latest messages based on channel id and number of messages to scrape provided
        url = f'https://discordapp.com/api/v8/channels/{self.channel_id}/messages?limit={str(self.num_messages)}'
        
        # Check if use_date_filter is True
        if use_date_filter:
            # Refer to Snowflakes in Pagination in https://discord.com/developers/docs/reference for explanation on syntax uses to generate snowflake_id
            _DISCORD_EPOCH = 1420070400000
            # Setting date filter (YYYY/MM/DD HH:MM:SS)
            self.date_filter = datetime(date_filter[0],  date_filter[1], date_filter[2])
            date_timestamp_in_ms = self.date_filter.timestamp() * 1000
            snowflake_id = int(date_timestamp_in_ms - _DISCORD_EPOCH) << 22
            url += f"&after={snowflake_id}"
        
        self.messages = requests.get(url, headers={'Authorization': f'Bot {bot_token}'})
        if self.messages.status_code == 200:
            # Turn response object (self.messages) to json object
            self.messages = self.messages.json()
            Logger.success(f'Pulled {str(len(self.messages))} messages!')
        else:
            Logger.error(f"Failed Request! Status Code : {self.messages.status_code}")


    def find_media_urls(self):
        try:
            valid_file_type = [".png", ".jpg", ".jpeg"]
            # Loops through all messages
            for x in range(len(self.messages)):
                    # Checks if message has more than 1 attachment
                if (len(self.messages[x]['attachments']) > 1):
                    # Loops through all attachments
                    for y in range(len(self.messages[x]['attachments'])):
                        media_url = self.messages[x]['attachments'][y]['url']
                        # Checks if the file type of the attachment is in valid_file_type list
                        if media_url[-4:].lower() in valid_file_type:
                            self.media_files.append(self.messages[x]['attachments'][y]['url'])
                            media_file_path = f"{media_url.split('/')[5]}-{media_url.split('/')[6].lower()}"
                            self.media_files_paths.append(media_file_path)
                # Checks if message has 1 attachment
                elif (len(self.messages[x]['attachments']) > 0):
                    media_url = self.messages[x]['attachments'][0]['url']
                    # Checks if the file type of the attachment is in valid_file_type list
                    if media_url[-4:].lower() in valid_file_type:
                        self.media_files.append(self.messages[x]['attachments'][0]['url'])
                        media_file_path = f"{media_url.split('/')[5]}-{media_url.split('/')[6].lower()}"
                        self.media_files_paths.append(media_file_path)
            Logger.success("Filtered through messages")
        except:
            Logger.error(f"Invalid message detected. Typical Cause : No image attachments")
            pass

# - - - -  - - - - - - - - - - - - - - - - - - -  - - - - - - - -

while True:
    print(Style.RESET_ALL)
    print("What would you like to do?\n")
    print("######################################\n")
    print("[1]Scrape Twitter Images\t\t[2]Scrape Discord Images\n")
    print("[3]Exit\n")
    print("######################################\n")
    task = input("Enter Option : ")
    if task == "1":
        try:
            init_settings()
            init_tweepy()
        except Exception as e:
            Logger.error(f"Make sure settings.json is properly filled! Error : {e}")
        TwitterImageScraper(path, number_of_tweets, screen_name)
    elif task == "2":
        try:
            init_settings()
        except Exception as e:
            Logger.error(f"Make sure settings.json is properly filled! Error : {e}")
        DiscordImageScraper(path, number_of_messages, channel_id)
    elif task == "3":
        Logger.other("Comment on my legit check @ https://twitter.com/ayyitsc9")
        Logger.other("Star the repository @ https://github.com/ayyitsc9/twitter-and-discord-image-scraper")
        Logger.error("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit()
    else:
        Logger.error("Invalid Input! Try again...\n")

# Thank you for giving my script a try! I hope you found it useful!
# If you have any questions or suggestions, feel free to message me on twitter
# https://twitter.com/ayyitsc9

