import re
import geoip2.database
import pandas as pd

db_path = './libs/GeoLite2-City.mmdb'
reader = geoip2.database.Reader(db_path)

BOT_KEYWORDS = [
    "UniversalFeedParser", "Tiny Tiny RSS", "python", "ruby", "java", "curl", "libwww", "Yahoo! Slurp",
    "DTS Agent", "irssi", "nutch", "wget", "superblock", "commafeed", "publish link validator", "ia_archiver",
    "bot", "Feedbin", "Xenu Link Sleuth", "portscout", "libfetch", "spider", "binlar", "theoldreader",
    "Microsoft Office Protocol Discovery", "Embedly", "Robosourcer", "FlipBoardRSS", "simplepie",
    "BingPreview", "SiteExplorer", "facebookexternalhit", "YandexImages", "HTTP_Request2", "distilator",
    "Ezooms", "LiveJournal.com", "Feedfetcher-Google", "FeedBurner",
]

def get_ip_country(ip):
    try:
        response = reader.city(ip)
        country = response.country.name if response.country.name else "Unknown"
        return country
    except:
        return "Not found"  # If the IP address isn't found in the database

def get_file(file_path = './apache_log.txt'):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().split('\n')[:-1]
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return content

def parse_file(content):
    ip_list = []
    os_list=[]
    browser_list=[]
    for line in content:
        ip_pattern = r'\d+\.\d+\.\d+\.\d+'
        ip = re.search(ip_pattern, line)
        if ip is not None:
            ip_list.append(get_ip_country(ip.group()))
        else:
            ip_list.append("Unknown")

        user_agent = line.split('"')[-2]

        if user_agent == "-" or not user_agent.strip() or any(bot.lower() in user_agent.lower() for bot in BOT_KEYWORDS):
            os_list.append("bot")
            browser_list.append("bot")

        else:
            os_pattern = r'(Windows|Mac OS X|Linux|Android|Darwin|iPhone|FreeBSD|OpenBSD|SunOS|Windows Phone)'
            os=re.search(os_pattern, user_agent)

            browser_pattern = r'(MSIE|Chrome|Trident|Firefox|BonEcho|Safari|Opera|Edge)'
            browser = re.search(browser_pattern, user_agent)

            if os is not None:
                os_list.append(os.group())
            else:
                os_list.append("Unknown")

            if browser is not None:
                browser_list.append(browser.group())
            else:
                browser_list.append("Unknown")

    df = pd.DataFrame({
        'IP country': ip_list,
        'OS': os_list,
        'Browser': browser_list
    })
    print(f"Number of identified bots: {os_list.count('bot')}")
    return df

def create_stats(df):
    total_hits = len(df)
    country_hits = df.groupby('IP country').size().sort_values(ascending=False)
    country_percentage = country_hits/total_hits*100

    filtered_countries_percentage = country_percentage[country_percentage>1]
    other_countries = country_percentage[country_percentage<=1].sum()
    if other_countries > 0:
        filtered_countries_percentage['Other']= other_countries

    os_hits = df.groupby('OS').size().sort_values(ascending=False)
    os_percentage = os_hits/total_hits*100

    browser_hits = df.groupby('Browser').size().sort_values(ascending=False)
    browser_percentage = browser_hits/total_hits*100
    return filtered_countries_percentage, os_percentage, browser_percentage

def write_output(country_stats, os_stats, browser_stats):
    with open('output/log_report.txt', 'w') as f:
        f.write('### Country Statistics ###\n')
        for country, percentage in country_stats.items():
            f.write(f"{country}: {percentage: .2f}%\n")
        f.write("\n")

        f.write('### OS Statistics ###\n')
        for os, percentage in os_stats.items():
            f.write(f"{os}: {percentage: .2f}%\n")
        f.write("\n")

        f.write('### Browser Statistics ###\n')
        for browser, percentage in browser_stats.items():
            f.write(f"{browser}: {percentage: .2f}%\n")
        f.write("\n")

    print("Log saved to output/log_report.txt")

if __name__ == "__main__":
    file_content = get_file()
    parsed = parse_file(file_content)
    countries, OSs, browsers = create_stats(parsed)
    write_output(countries, OSs, browsers)
