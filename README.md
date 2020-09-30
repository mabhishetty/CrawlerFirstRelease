# CrawlerFirstRelease
First release of my working (hopefully!) crawler script.

## **Disclaimer**:

I have written this code for non-commercial use only.
The code should not be used for commercial purposes.
Web-crawling can place large demands on web-servers - this should be avoided.
Therefore the code includes a number of measures to crawl responsibly.
These include:
- Respecting robots.txt restrictions
- Reading 'terms of service' sections of websites
- Respecting a crawl-delay if provided. If not, a standard delay shall be used.

**The code should not, under any circumstances, be used without these restrictions.**

For more information on this, see the website I created for my crawler: https://www.mycustomcrawlerexplanations.com

### Motivation:

The Networks book *(M. Newman - 2nd Ed, 2018)* describes in some detail the structure of both the internet and the Web.
More specifically the book describes experimental methods for determining the structure of the Web - given that there is no formal 'government' for the Web.
Web crawling is an established practice used by many - especially search engines for indexing pages on the Web.
I wanted to write this script to practise with Python and to practise Network analysis techniques as outlined in the Networks book.
In addition: most blogs that describe writing a web-crawler resort to some secondary library such as ScraPy. I wanted to do this from scratch.


### Structure:
The control-flow of the code can be broken down into a few coarse blocks:
1) Setting up the crawler instance with the necessary fields
2) Checking the /robots.txt file at the root of the target to see whether or not crawling of that site is permitted.
3) Provided step (2) is successful, we search for a Terms of Service page on the target domain. This might give more information about whether or not crawling is allowed.
4) Provided step (3) is successful, we proceed and crawl the target website.
5) Store the data in the appropriate format and select the next site to visit.

### Usage:
To run the script you can simply execute from Terminal:
`python3.x @/crawler_f1.py` where .x is the version of Python you are running (I used 3.6) and '@/' is the path of crawler_f1.py relative to the current directory

The script uses the modules: 
* 're' (RegExps)
* 'requests' (Web requests)
* 'bs4.BeautifulSoup' (formatting HTML content)
* 'sys.exit' (safe exiting)
* 'time' (crawl delays)
* 'random' (selection of links from a particular page to be visited)

You may need to install some of these yourself via 'pip'. This was the case for me. I ran:
`python3.6 -m pip install requests`
`python3.6 -m pip install beautifulsoup4`

User-input is required for inputting initial parameters along with confirmining that comments from /robots.txt files and ToS pages allow crawling.

### Known issues:
- https://www.bbc.co.uk/robots.txt is not formatted in the manner that: http://www.robotstxt.org suggests. I suggest that this site should not be crawled and be listed as a 'no-go' site where possible.

### Contact:
- Through the custom email set-up for this crawler: customcrawlerexplained@gmail.com (mailto:customcrawlerexplained@gmail.com)

### Further reading:
- *Networks (M. Newman, 2nd Ed - 2018)*
- http://www.robotstxt.org : generally accepted standard for the structure of /robots.txt files
- https://developers.google.com/search/reference/robots_txt : explaining Google's approach to crawling
- https://benbernardblog.com/web-scraping-and-crawling-are-perfectly-legal-right/ : great blog post that explains some of the issues surrounding crawling
- https://en.wikipedia.org/wiki/Web_crawler : good overview of crawling
- https://www.w3schools.com/python/default.asp : very helpful site for Python documentation


