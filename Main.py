import configparser
import requests
import json
import matplotlib.pyplot as plt


class Token:
    def __init__(self, symbol, name, _id, mCap):
        self.symbol = symbol
        self.name = name
        self._id = _id
        self.articleLinks = []
        self.totalMentions = 0
        self.mCap = mCap


class Posts:
    def __init__(self, _id, title):
        self.comments = []
        self.id = _id
        self.title = title


def authenticate():
    _auth = requests.auth.HTTPBasicAuth(CLIENT_ID, SECRET_TOKEN)

    # passing login method
    _data = {'grant_type': 'password',
             'username': R_USERNAME,
             'password': R_PW}

    # setup our header info
    _headers = {'User-Agent': 'CryptoBot/0.0.1'}

    # send our request for an OAuth token
    res = requests.post('https://www.reddit.com/api/v1/access_token',
                        auth=_auth, data=_data, headers=_headers)

    # convert response to JSON and pull access_token value
    _token = res.json()['access_token']

    # Writes to ini file
    write_config = configparser.ConfigParser()
    write_config.read("keys.ini")
    write_config.set("Reddit API Keys", "TOKEN", _token)
    cfgfile = open("keys.ini", 'w')
    write_config.write(cfgfile)
    cfgfile.close()

    # add authorization to our headers dictionary
    _headers = {**_headers, **{'Authorization': f"bearer {_token}"}}
    return _headers


read_config = configparser.ConfigParser()
read_config.read("keys.ini")

CLIENT_ID = read_config.get("Reddit API Keys", "CLIENT_ID")
SECRET_TOKEN = read_config.get("Reddit API Keys", "SECRET_TOKEN")
TOKEN = read_config.get("Reddit API Keys", "TOKEN")
R_USERNAME = read_config.get("Reddit Credentials", "USERNAME")
R_PW = read_config.get("Reddit Credentials", "PW")
SUBREDDIT_QUERY_ENDPOINT = 'https://oauth.reddit.com/r/CryptoCurrency/top?t=week&?limit=100'
# SUBREDDIT_QUERY_ENDPOINT = 'https://oauth.reddit.com/r/SatoshiStreetBets/top?t=week&?limit=100'
# SUBREDDIT_QUERY_ENDPOINT = 'https://oauth.reddit.com/r/CryptoMarkets/top?t=week&?limit=100'

coingecko_request = requests.get(
    'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=200&page=1&sparkline=false')
coinJSON = json.loads(coingecko_request.content)

tokens = []
tokenCount = 0
for token in coinJSON:
    tokens.append(Token(token['symbol'], token['name'], token['id'], token['market_cap']))
    tokenCount = tokenCount + 1

headers = {'User-Agent': 'CryptoBot/0.0.1'}
headers = {**headers, **{'Authorization': f"bearer {TOKEN}"}}

r = requests.get(SUBREDDIT_QUERY_ENDPOINT, headers=headers)

if not r.status_code == 200:
    # if status is not OK then try again with new token
    headers = authenticate()
    r = requests.get(SUBREDDIT_QUERY_ENDPOINT, headers=headers)
if not r.status_code == 200:
    # if still not working then exit program
    print("Unable to retrieve response")
    exit()

jsonData = json.loads(r.content)
postsJson = jsonData['data']['children']
posts = []

for post in postsJson:
    posts.append(Posts(post['data']['id'], post['data']['title']))
    for token in tokens:
        symbolCount = post['data']['selftext'].upper().count(" " + token.symbol.upper() + " ")
        nameCount = post['data']['selftext'].upper().count(" " + token.name.upper() + " ")
        if symbolCount > 0 or nameCount > 0:
            token.totalMentions = token.totalMentions + symbolCount + nameCount
            if not token.articleLinks.__contains__(post['data']['url']):
                token.articleLinks.append(post['data']['url'])

# -----------------------------------------------------------------------------------------------------------
# PLOTTING
# -----------------------------------------------------------------------------------------------------------
x = []  # token name
y = []  # total token mentions
z = []  # count of individual posts
tCount = 0
for token in tokens:
    if tCount > 20:
        break
    if token.totalMentions > 0:
        x.append(token.name)
        y.append(token.totalMentions)
        z.append(len(token.articleLinks))
        tCount = tCount + 1

ax = plt.subplot()
ax.barh(x, y, label="Number of total mentions", color='#78ff9c')
ax.barh(x, z, label="Number of individual posts", color='#32bf57')

plt.title('Crypto mentions in the weekly top 100 posts on r/CryptoCurrency (Week 11th May - 18th of May)')
plt.ylabel('CryptoCurrency')
plt.xlabel('Number of total mentions')
plt.legend(loc="upper right")
plt.show()
