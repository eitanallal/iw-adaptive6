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
    except Exception as e:
        return "Not found"  # If the IP address isn't found in the database


def read_file(file_path='./apache_log.txt'):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip().split('\n')
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return []

def is_bot(user_agent):
    return any(bot.lower() in user_agent.lower() for bot in BOT_KEYWORDS)

def extract_data(content):
    ip_list, os_list, browser_list= [], [], []
    ip_pattern = r'\d+\.\d+\.\d+\.\d+'
    os_pattern = r'(Windows|Mac OS X|Linux|Android|Darwin|iPhone|FreeBSD|OpenBSD|SunOS|Windows Phone)'
    browser_pattern = r'(MSIE|Chrome|Trident|Firefox|BonEcho|Safari|Opera|Edge)'

    for line in content:
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
            os=re.search(os_pattern, user_agent)
            browser = re.search(browser_pattern, user_agent)

            os_list.append(os.group() if os else "Unknown")
            browser_list.append(browser.group() if browser else "Unknown")
    return ip_list, os_list, browser_list


def create_dataframe(ip_list, os_list, browser_list):
    return pd.DataFrame({
        'IP country': ip_list,
        'OS': os_list,
        'Browser': browser_list
    })

def create_stats(dataframe):
    total_hits = len(dataframe)
    country_hits = dataframe.groupby('IP country').size().sort_values(ascending=False)
    country_percentage = country_hits/total_hits*100

    filtered_countries_percentage = country_percentage[country_percentage>1]
    other_countries = country_percentage[country_percentage<=1].sum()
    if other_countries > 0:
        filtered_countries_percentage['Other']= other_countries

    os_percentage = dataframe.groupby('OS').size().sort_values(ascending=False)/total_hits*100
    browser_percentage = dataframe.groupby('Browser').size().sort_values(ascending=False)/total_hits*100
    return filtered_countries_percentage, os_percentage, browser_percentage

def write_output(country_stats, os_stats, browser_stats, output_path='output/log_report.txt'):
    """Write the statistics to an output file."""
    with open(output_path, 'w') as f:
        f.write('Country:\n')
        for country, percentage in country_stats.items():
            f.write(f"{country}: {percentage:.2f}%\n")
        f.write("\nOS\n")
        for os, percentage in os_stats.items():
            f.write(f"{os}: {percentage:.2f}%\n")
        f.write("\nBrowser\n")
        for browser, percentage in browser_stats.items():
            f.write(f"{browser}: {percentage:.2f}%\n")

    print(f"Log saved to {output_path}")

if __name__ == "__main__":
    file_content = read_file()
    if file_content:
        ips, OSs, browsers = extract_data(file_content)
        df = create_dataframe(ips, OSs, browsers)
        country_statistics, os_statistics, browser_statistics = create_stats(df)
        write_output(country_statistics, os_statistics, browser_statistics)
