# Date: 06/10/20
# Author: Manoj Abhishetty
# Edition: 6

# + Modifying RegEx function: need to escape more metacharacters.

# 1. Defining important functions

# 1.1. This is a generator, we can call this multiple times to give the sublists we want.
# From: https://stackoverflow.com/questions/54372218/how-to-split-a-list-into-sublists-based-on-a-separator-similar-to-str-split

def list_splitter(list_to_split, delimiter):
    """
    Generator that gives sublists from a list.
    Inputs: list_to_split (list):
            delimiter: where splits should be done. Won't appear in sublists
    Output: sublist
    """
    sublist = []                                    # Set up an empty sublist
    for var in list_to_split:                       # Loop over the list to split
        if var == delimiter:                        # If we have reached the delimiter
            yield sublist                           # Return the sublist as assembled so far
            sublist = []                            # Reset the sublist (I think the next call will start from here, since it is a generator)
        else:                                       # If we are not yet at the delimiter
            sublist.append(var)                     # Add the current element to the sublist
    yield sublist                                   # For the last sublist. Or if there are no delimiters.

# 1.2. This function gives an output based the status of the website we are trying to access.
# https://developers.google.com/search/reference/robots_txt
def getSiteStatus(req_obj, crawl_instance):
    """
    Function to make sense of the status code from accessing a website.
    Input: requests.response object: contains status code
           crawl_instance: crawler instance, contains URL target
    Output: str_status_code: string containing status code.
    """
    str_status_code = str(req_obj.status_code)
    # We expect status codes to be 3 digits in length
    if len(str_status_code) != 3:
        print('Status code problem, url:', crawl_instance.current_target)
        return str_status_code

    if str_status_code[0] == '2':
        #"Robots acquisition successful. Conditional crawling is likely." - this should be the most likely outcome so won't bother printing it each time
        return str_status_code

    elif str_status_code[0] == '3':
        # We have been redirected.
        print('Redirect, url:', crawl_instance.current_target)
        return str_status_code

    elif str_status_code[0] == '4':
        # Not able to find the file, eg: error 404. Based on guidance from Google dev site, go ahead with crawl.
        print("Client error. Assuming no robots file exists, full crawling can proceed, url:", crawl_instance.current_target )
        return str_status_code

    elif str_status_code[0] == '5':
        # Some problem on the server-side. Don't crawl. eg, error 502: Bad Gateway.
        print('Server error. Assume a temporary error, no crawling shall proceed - url:', crawl_instance.current_target)
        return str_status_code

    else:
        print("Some other error, url:", crawl_instance.current_target)
        return str_status_code

# 1.3. This function takes a relative url (usually from a page as a link) and gives an absolute form. Then we will be able to do 'requests.get' on it.
def getAbsUrl(crtVerOfLink, doubleSlashSplitList, rootUrl, real_url_end):
#https://www.w3.org/TR/WD-html40-970917/htmlweb.html
#https://stackoverflow.com/questions/2005079/absolute-vs-relative-urls
    """
    Function to get the absolute URL provided with some starting URL.
    Inputs: currentVersionOfLink: (str), our current URL string - be it relative/absolute etc.
            doubleSlashSplitList: (list), our list of the Target site URL, split by '//'
            rootUrl: (str), the root url of our target site.
            real_url_end: (str), the 'true' URL of the site we are visiting. This comes from the response.url command - and ends in '/' if the target is a directory.
    Output: newLink (str), our absolute URL.
    """
    # Note: Links on pages may be absolute or relative. For absolute links, nothing needs to be done.
    # For relative links there are a few forms. //new, /new or new, for example.
    # The last is the most noteworthy. If the page we are currently on (on which the link has been found) is a directory, the link is beneath it in hierarchy.
    # However if the page is not a directory, then the link is on the same hierarchical level.
    # How do we know if the page we are on is a directory? We have stripped '/' which hurts us here. But even without that, directory links might appear without a slash on pages.
    # Therefore we use response.url attribute. This seems to give us what we want. Remember - we are interested in the .url of the page ON WHICH the link was found.

    # Policy here is only modify if necessary. 'None' and other problematic entries can be dealt with later.
    # Test this separately as '.startswith' method won't work on NoneType.
    if crtVerOfLink == None:
        newLink = crtVerOfLink
    elif crtVerOfLink.startswith('//'):
        newLink = doubleSlashSplitList[0] + crtVerOfLink                        # eg, 'https:' + '//www.google.com'
    elif crtVerOfLink.startswith('/'):                                          # /new
        newLink = root_url + crtVerOfLink                                       # https://www.mainsite.com/new
    elif crtVerOfLink.startswith('http'):                                       # includes both http and https
        newLink = crtVerOfLink
    elif crtVerOfLink.startswith('mailto') or crtVerOfLink.startswith('ftp') or crtVerOfLink.startswith('#'):
        newLink = crtVerOfLink                                                  # Don't change this entry. We will deal with it later.
    else:
        # A link such as: new. There are 2 possibilites: either the page is an end, or a directory.
        # In the former we have something like: https://www.main.com/here/there.html. The link resolves to: https://www.main.com/here/new
        # In the latter, we may be on a page: https://www.main.com/here/where. The link should resolve to: https://www.main.com/here/where/new
        # Here, note that doubleSlashSplitList comes from the page we are currently on - whose url will NOT end with a slash. So we don't get a '' in the list.
        FsingleSlashList_split = doubleSlashSplitList[1].split('/')              #['www.base.com','a','b','c']
        if real_url_end.endswith('/'):
            newLink = doubleSlashSplitList[0] + '//' + doubleSlashSplitList[1] + '/' + crtVerOfLink
        else:
            # Get all elements up to one level from current page. Then add slash and current link.
            newLink = doubleSlashSplitList[0] + '//' + '/'.join(FsingleSlashList_split[:-1]) + '/' + crtVerOfLink

    return newLink

# 2. Class definition

class Crawler():

    # 2.1. Initialisation. Need 4 arguments.
    def __init__(self, starting_site, num_to_visit, secured, no_goes):
        self.sites_to_visit = [starting_site]                                   # list of sites yet to visit. Starts with seed
        self.current_target = None                                              # Current target site
        self.sites_visited = []                                                 # List of sites that have been visited
        self.num_to_visit = num_to_visit                                        # Total number of sites that should be visited
        self.secured = secured                                                  # True if sites that are NOT secured should be visited
        self.no_goes = no_goes                                                  # List of sites that should NOT be visited
        self.cusHeaders = {'User-Agent':'CustomCrawler(+https://www.mycustomcrawlerexplanations.com)'}          #identifying string passed to server when HTTP request (in header) is made.
        self.sites_dict = {}                                                    # Dictionary that gives sites, with information. Will include all sites the program TRIES to visit.
        self.counter_attempts = 0                                               # Counter to give the current progress of the search.  Gives the number of all sites ATTEMPTED.
        self.counter_total = 0                                                  # Counter to give progress of search. Tracks only sites that have been visited.
        self.crawl_delay = 15                                                   # Number of seconds to wait between requests.

    # 2.2. Function that examines robots.txt file. Makes code cleaner.
    def robots_check(self):
        """
        Function to check whether we are prohibited from visiting a site based on /robots.txt restrictions.
        Inputs: object of class Crawler. Need: current_target, cusHeaders
        Outputs: crawlable (Bool), True if we can crawl. False otherwise.
                 str_status (int), For the dictionary
        """

        # 2.2.1. Get root of site url.
        site_pieces = self.current_target.split('//',1)                         # https://www.google.co.uk/themain/site -> ['https:', 'www.google.co.uk/themain/site']
        # Because the trailing '/' was removed from the url, there will be no mishaps with: https://www.mytest.com/ -> [www.mytest.com, '']
        second_list = site_pieces[1].split('/',1)                               # www.google.co.uk/themain/site -> ['www.google.co.uk', 'themain/site']
        # root_url will NOT end with a slash. We just split based on that.
        root_url = site_pieces[0] + '//' + second_list[0]                       # https: + // + www.google.co.uk

        # 2.2.2. Try to 'get' the robots file.
        robots_url = root_url + '/robots.txt'
        robots_req_obj = requests.get(robots_url, headers = self.cusHeaders)

        # 2.2.3. To get the extension of the site to visit. This will be used in the RegEx checking later:
        # tExtension = self.current_target - root_url
        try:
            tExtension = '/' + second_list[1]               # something like: /themain/site
        # If our target was the root, second_list only has 1 element. We make an exception and give the extension just as '/'. (This is likely to be unnecessary. Because for the case where the target URL is the root, I have made exceptions.)
        except IndexError:
            tExtension = '/'                                # No reason to have a space at the end of the string.

        # 2.2.4. Status codes with string conversion
        str_status = getSiteStatus(robots_req_obj, self)
        # There are many possible digits that 'str_status' could begin with. Those possibilities have been addressed in getSiteStatus
        if str_status[0] != '2':
            crawlable = False
            # Stop the function and return both the fact that we can't crawl, and the problematic status code of the .robots file.
            robots_req_obj.close()
            return crawlable, int(str_status)

        # 2.2.5. Split the text of the robots file into a list, delimited by newline characters.
        robots_list = robots_req_obj.text.split('\n')

        # 2.2.6. CLOSE object now that we are done with it (terminate connxn with server so we don't stress it)
        robots_req_obj.close()

        # 2.2.7. The 'robots_list' has all the content of the robots file, split by newlines.
            # Now we split this list into a number of other lists, all separated by ''. We have a generator iterator.
        generator_robots_list = list_splitter(robots_list,'')

        # 2.2.8. Extract rules from each sublist

        # Documentation: We iterate over each 'record' (defined between empty lines)
            # We get a 'list' for each of these. We iterate over each element in the list (split by newlines from before)
            # We strip any spaces. This is to make sure our 'startswith' commands work well later.
            # If the line starts with a '#', we add the content to a comment string.
            # If the line starts with user and ends with '*', we know that this is the record that we are interested in.
        # Store of commands from /robots.txt file.
        final_dict = {}
        # Used for numbering final_dict entries. See end of for loop.
        dict_title = 0
        # I'll look for comments in each of the sublists. Put this outside the loop or it gets overwritten.
        comment_string = ''
        for sublist in list_splitter(robots_list, ''):
            # We are only interested in the User-Agent '*' or 'CustomCrawler(+https://www.mycustomcrawlerexplanations.com)'
            flag = 0
            # Individual line in a record
            for en in sublist:
                flag += 1
                stripped_el = en.strip(' .')                                    # strings aren't mutable - need to get a new one!

                if stripped_el.startswith('#'):
                    comment_string += stripped_el                               # Making a string of all comments. If we reach this point, the elif is not executed. Goes to next iteration of 'for' loop.

                # if the entry is a user-agent and corresponds to all crawlers, we are interested in recording the entry.
                elif (stripped_el.startswith('user') and stripped_el.endswith('*')) or (stripped_el.startswith('User') and stripped_el.endswith('*')):

                    # The structure of the sublist is: ['UA: smth, UA: smth_else, Allow: smth, Allow: smth, Disallow: smth_else']
                    # We iterate over the remaining elements of that sublist and add entries to a dictionary. The prior elements in the sublist
                    # don't interest us because they will only be irrelevant UA strings. There is a chance we include irrelevant UA strings in final_dict
                    # if multiple UA's are referred to and UA: * came first. We will deal with this later.

                    # We look at the remaining elements of this sublist. We won't include the element we are on, since this is the 'UA: *' entry
                    for k in range(flag, len(sublist)):
                        # n-th element of sublist (record), flag = n. Indexing sublist with 'n' gives us (n+1)th element.
                        # So we go from (flag + 1)th element to (len(sublist) -1 +1)th element (since range doesn't include final val.)
                        element = sublist[k]
                        element = element.strip(' ')                           # We need this as we are going over elements not yet covered in that sublist.

                        # Add the comment to our comment string. We do this here because we won't go over the rest of the elements in this sublist later.
                        if element.startswith('#'):
                            comment_string += element
                            # Don't want to add this to our final dictionary. It isn't an allow/disallow command.
                            continue

                        # We are in the record that matches our crawler (UA: *). Therefore a crawl-delay in this record should be applied to our crawler.
                        # The entry will come in the form: 'crawl-delay: time'
                        elif element.startswith('crawl') or element.startswith('Crawl'):
                            delayEntry = element.split(':')
                            # Get the seconds, remove spaces and '.'s, and make it an integer.
                            self.crawl_delay = int(delayEntry[1].strip(' .'))
                            # Don't want to add crawl-delay to the final_dict.
                            continue

                        # For entries in record which don't start with '#' or 'crawl'. So either allow/disallow or other UA's.
                        # Ideally other UA's wouldn't be added. But we can fix this more easily later.
                        # Most important that crawl-delays are properly handled and comments don't arrive here (would throw an error)
                        entry = element.split(':')
                        dict_title += 1
                        # Add to the dictionary the 'number-command' that this is, and both the allow/disallow type and the directory/page in question.
                        # We use the strip command again because previously we didn't strip the end of '(dis)allow' or the start of the target.
                        final_dict.update({dict_title:{'command':entry[0].strip(' '),
                                                       'target':entry[1].strip(' ')}})

                    # The 'break' is within elif. If we reach this, we have found the end of our record of interest. No sense in going over all the elements of the same sublist again.
                    # So we break out of 'for en in sublist' loop.
                    break

                    # UA:* shouldn't occur more than once in a robots file. But if it does, this still works. dict_title is initialised OOTL.
                    # So for a second occurrence of UA:*, more entries are added to the final_dict - existing entries remain unmodified.
        # 2.2.9. Display comments in the /robots.txt file
        print('These are the comments from the .robots.txt file:', comment_string)
        shallWeContinue = input('Based on the comments from the robots file, do you wish to continue? (Y/N): ')
        if 'N' in shallWeContinue:
            crawlable = False
            return crawlable, int(str_status)

        # 2.2.10. Make sure that the entries are all 'allow' or 'disallow' commands and store.
        disallow_list = []
        allow_list = []

        # Loop over all dictionary entries. Because dict_title is not updated until absolutely necessary, entries will have contiguous dict_title values.
        # Start from '1' and go to len(final_dict) + 1 because max(i) will only be len(final_dict)
        for i in range(1, len(final_dict) + 1):
            # If 'allow' or 'disallow' are not in the first entry (we probably have a UA string)
            # Check disallow first, since 'disallow' also has the string 'allow' in it.
            if ('disallow' in (final_dict.get(i)).get('command')) or ('Disallow' in (final_dict.get(i)).get('command')):
                disallow_list.append((final_dict.get(i)).get('target'))

            # only executed if disallow not present.
            elif ('allow' in (final_dict.get(i)).get('command')) or ('Allow' in (final_dict.get(i)).get('command')):
                allow_list.append((final_dict.get(i)).get('target'))

            # get rid of UA entries.
            else:
                final_dict.pop(i)

        # 2.2.11 RegExps
        # We use Regular Expressions to match the extension of our current_target to sites in the /robots.txt file. This tells us if we can visit current_target.
        # First we need to convert the /robots.txt commands to RegExps. Then we will do the search.

        # This section is the most complex part of this whole script - and is the first place to check for bugs.
        # See: https://docs.python.org/3/howto/regex.html#regex-howto for a great explanation on Python RegEx's.

        allow_list_regex = []
        disallow_list_regex = []
        # Do the following process for disallow commands first, then allow commands (arbitrary)
        # Because lists are mutable, this will change the content in disallow_list and allow_list themselves. (sure??)
        for ii in range(1,3):
            if ii == 1:
                list_r = disallow_list
            else:
                list_r = allow_list

            # entries in this list are from the /robots.txt file. They are relative paths that will be allowed/disallowed.
            for el in list_r:

                # Prevent infinite loop. Remove certain characters: ends with '*' or '?' -> remove. Wildcards won't end a path - and query strings shouldn't either.
                wEndswithSafety = 0
                while el.endswith('*') or el.endswith('?'):
                    el = el[:-1]
                    wEndswithSafety += 1
                    if wEndswithSafety >= 500:
                        break

            # Now for the tricky part.
            # Remember: aim is to see if the extension of our current_target matches any of the paths in the Robots file - and decide whether or not to crawl accordingly.
            # This will be done by turning the robots paths into RegEx's.
            # The links in that Robots file contain certain characters (*,$,etc.) to represent 'patterns' and whole groups of paths in a few lines.
            # As explained in the documentation link above, RegEx's in a simple form match text easily.
            # However some RegEx's contain 'metacharacters' - which modify the RegExp. These, ordinarily, are interpreted by the RegEx engine to mean something special
            # The danger is that some of the paths may contain these metacharacters - and the RegEx engine will not seek to match the characters but will interpret them as metacharacters
            # The solution is to escape the metacharacters - so that the RegEx engine realises that we are trying to match those characters and not use them as metacharacters
            # This could be done with [], but we are better off with a '\' to escape.
            # We use raw strings so that Python understands we want to replace metacharacters with an backslash preceding them - not with an escape sequence.

                # First check for any metacharacters: ., ^, $, *, +, ?, {, }, [, ], \, |, (, ) - protect them.
                # Backslashes '\' or carets '^' are unlikely to appear in URLs. Include for completeness

                # replace a single slash with a double. Need to do this first because everywhere else we use slashes.
                el = el.replace("\\", r"\\")

                el = el.replace('.', r'\.')
                el = el.replace('^', r'\^')
                # If '$' is the last character, we don't want to replace it. It has some meaning.
                if '$' in el:
                    num_dollar = el.count('$')
                    # If the dollar is the final element
                    if '$' == el[-1]:
                        # Escape all instances of 'dollar' but the last one
                        el = el.replace('$', r'\$', num_dollar - 1)
                    else:
                        # Escape all instances of 'dollar'
                        el = el.replace('$', r'\$', num_dollar)
                # '*' dealt with later
                el = el.replace('+', r'\+')
                el = el.replace('?', r'\?')
                el = el.replace('{', r'\{')
                el = el.replace('}', r'\}')
                el = el.replace('[', r'\[')
                el = el.replace(']', r'\]')
                el = el.replace('|', r'\|')
                el = el.replace('(', r'\(')
                el = el.replace(')', r'\)')


                # Then replace any '*' with '.*'. This is for the RegExp. This allows us to match the command '*', which means any string.
                # Important that we do this AFTER protection of '.'. Otherwise the '.' that we add gets protected and loses the RegEx meaning - which we want in this case.
                # we are NOT escaping this symbol here.
                el = el.replace('*', '.*')

                # Then add '^' at the start
                el = '^' + el

                if ii == 1:
                    disallow_list_regex.append(el)
                else:
                    allow_list_regex.append(el)

        # 2.2.11. Check the URL against each of the rules.
        # If it passes the test, continue. Otherwise - exit, add the URL to the dictionary and explain the ROBOTS issue.
        # We'll have to check both lists. For example, you might disallow all but allow a few sites. So we need to check for that.
        # First check for exceptional circumstances. These are the: ' ' and '/' entries.
        # According to: http://www.robotstxt.org/robotstxt.html, 'everything not explicitly disallowed is considered fair game'

            # Another issue is with trailing '/'. For consistency, we have removed trailing slashes from URLs.
            # But this means a link we find, ending with a slash, will have its trailing character removed as it becomes current target.
            # Then if the robots file lists /.../dir/, our link may be accepted even though it shouldn't be.
            # In addition, in some places online a link that ought to end with a '/' may not have one. (%*)
            # We think that response.url gives us the true URL. But we can't use that as the purpose of the robots check is to determine if a requests.get is allowed.
            # We could simply avoid stripping trailing slashes. But that leads to inconsistencies in data storage and the problem in (%*).
            # Solution: strip trailing slashes from robots commands too. This does lead to some extra restrictions: certain sites that are (in theory) crawlable won't be crawled.
            # In practice this is not an issue. The number of extra prohibited sites is just equal to the number of disallows in the UA:* of the robots file.
            # I won't extend this to 'allows' - I will be more restrictive given the ambiguity.
            # eg, Disallow: /ex/dir/. If we have https://www.site.com/ex/dir, we don't know if it was dir/ before. But making
            # Disallow: /ex/dir prevents crawling if it was dir/ or just dir
        crawlable = True                                                        # F: Prohibited, T: allowed

        for el in disallow_list_regex:
            # A statement: 'Disallow: ' -> '^'. Disallowing nothing
            # We stripped spaces away. ' ' -> '' -> '^'
            if el == '^':
                pass
            # A statement: 'Disallow: /' -> '^/'. Disallowing everything        For the case where tExtension = '/'.
            elif el == '^/':
                crawlable = False
            else:
                if el.endswith('/'):
                    ModEl = el[:-1]
                else:
                    ModEl = el
                x = re.search(ModEl, tExtension)
                # If there is a match - our target url appears in disallow
                if x:
                    crawlable = False

        # Now we have been prohibited, lets check allow list
        if crawlable == False:
            for el in allow_list_regex:
                # A statement: 'Allow: ' -> '^'. Allow nothing
                if el == '^':
                    pass                                                        # Since we are currently prohibited, and nothing is allowed
                # A statement: 'Allow: /' -> '^/'. Allow everything.
                # From: 'https://developers.google.com/search/reference/robots_txt', In case of conflicting rules, including those with wildcards, the least restrictive rule is used.
                elif el == '^/':
                    crawlable = True
                else:
                    x = re.search(el, tExtension)
                    if x:
                        crawlable = True
        return crawlable, int(str_status)                                       # True: allowed, False: prohibited

    # 2.3. Function that examines the terms of service. Sees if we can crawl
    def ToS_check(self):
        """
        Function to check the Terms of Service on the webpage.
        Check both the root site and the ToS page, if they can be found.
        Inputs: crawler instance.
        Outputs: okContinue (Y/N) (str): can the crawl progress or are we prohibited?
                 ToS_status (int): status code of request [either for the Homepage or T&C's page]
        """
        # We will first go to the homepage of the target url. From there we will search for any links to a 'terms' site.
        # We will go to the 'terms' site and search for any reference to 'robots' - printing this for the user.
        # The user can then decide whether or not it is appropriate to crawl.

        # 2.3.1. Get root of site url.
        site_pieces = self.current_target.split('//',1)                         # ['https:','www.abcd.com....etc']
        second_list = site_pieces[1].split('/',1)                               # ['www.abcd.com','a','b','c']
        root_url = site_pieces[0] + '//' + second_list[0]                       # 'https://www.abcd.com'. Won't end with '/'

        # 2.3.2. Having just visited the robots page, we shall wait a certain amount of time before moving forward.
        # Time may have been updated from the /robots.txt file. Otherwise a standard 15s wait is used.
        time.sleep(self.crawl_delay)

        # 2.3.3. Visit root site (homepage)
        root_req_obj = requests.get(root_url, headers = self.cusHeaders)
        # for getAbsUrl
        actual_url_home = root_req_obj.url
        root_status = getSiteStatus(root_req_obj, self)
        # If we are unable to access the homepage (and therefore check the ToS - don't crawl.)
        if root_status[0] != '2':
            okContinue = 'N'
            print("Problem establishing connxn with Homepage")
            root_req_obj.close()
            return okContinue, int(root_status)

        homepage_soup = BeautifulSoup(root_req_obj.text, 'lxml')
        # CLOSE connxn so that we don't stress server.
        root_req_obj.close()

        # Search all the links on the homepage for any mention of 'terms'
        # If such a link is found, store the link
        #### Assumes only 1 terms link on the homepage. ####
        ToS_link = ''
        for link in homepage_soup.find_all('a'):
            try:
                if 'terms' in link.string or 'Terms' in link.string:
                    ToS_link = link.get('href')
            except TypeError:
                pass                                                            # In case the link is NoneType, link.string won't work.

        # 2.3.4. Head to the 'terms' page and search for 'robots'/'crawler'/'spider'
        # If no 'terms' link was found - go ahead with the crawl.
        if (ToS_link != '') and (ToS_link != None) and (not ToS_link.startswith('#')):
            # Some URLs are relative!!! getAbsUrl gives us the form of the link to access the site.
            ToS_link_full = getAbsUrl(ToS_link, site_pieces, root_url, actual_url_home)
            # Wait again - do this before each 'get' request.
            time.sleep(self.crawl_delay)
            terms_req_obj = requests.get(ToS_link_full, headers = self.cusHeaders)
            tos_status = getSiteStatus(terms_req_obj, self)
            # If we know that there is a ToS page but we are not able to access it - don't crawl.
            if tos_status[0] != 2:
                okContinue = 'N'
                print("Problem establishing connxn with ToS page")
                terms_req_obj.close()
                return okContinue, int(tos_status)
            # Get list of T&C's content
            listOf_TandCs = (terms_req_obj.text).split('\n')
            # CLOSE connxn now that we are done with it - so that we don't stress the server
            terms_req_obj.close()
            # Use the generator to loop over T&C's content - get a separate list separated by ''
            for sublist_TandCs in list_splitter(listOf_TandCs,''):
                pageStr = ' '.join(sublist_TandCs)
                if ('robot' in pageStr) or ('Robots' in pageStr) or ('crawler' in pageStr) or ('Crawler' in pageStr) or ('spider' in pageStr) or ('Spider' in pageStr):
                    # Show the user the 'terms'. If they read it and wish to continue, they may do so. Otherwise not.
                    print(pageStr)
            okContinue = input("Based on the above, will you continue with the crawl? Do the T&C's allow it? (Y/N) ")
        # If no 'terms' page was found, continue with the crawl.
        else:
            okContinue = 'Y'
            tos_status = 0

        return okContinue, int(tos_status)

# 3. Setup for main script.
# 3.1. Structure of dictionary in which we store site data.

#-0-0--0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0--0-0-0-0-0-0--0-0-0-0-0-0-0-0-0-0-0
#-0-0--0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0--0-0-0-0-0-0--0-0-0-0-0-0-0-0-0-0-0
# Format for sites_dict:
# {'url':(string),              - The url of this site, in string form.
# 'links':(NoneType),           - The links from this site. Will be a list of strings.
# 'status':(NoneType),          - The HTTP status code, 2xx, 3xx, 4xx, 5xx etc. Integers
# 'redirect':(NoneType),        - Whether or not we have been redirected. Bool, True if redirected
# 'duration':(NoneType),        - Returns a float with the time, in seconds, elapsed between making and receiving request contents.
# 'robots':(Bool),              - Are we prohibited from crawling due to the /robots.txt file? True if prohibited
# 'ToS':(Bool),                 - Are we prohibited from crawling due to the ToS? True if prohibited
# 'Repeat':(Bool),              - Is this site a repeat of a previous one? True if so
# 'no-go':(Bool)}               - Is this a no-go site? True if so.
# 'weird_url': (Bool)           - True if the url we ended up at is different to the one we wanted to go to (even without redirect?! - see Jupyter Notebook debugging for an example.)
#-0-0--0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0--0-0-0-0-0-0--0-0-0-0-0-0-0-0-0-0-0
#-0-0--0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0-0--0-0-0-0-0-0--0-0-0-0-0-0-0-0-0-0-0

# 3.2. Import modules: regExp, web requests, styling web content, exit and time (for delays)
import re
import requests
from bs4 import BeautifulSoup
from sys import exit
import time
import random

# 3.3. Ask user for inputs and check if they are appropriate.
print("""\
This script aims to crawl a small portion of the web to develop a network representation.
This is so that mathematical techniques can be used to analyse network structure.
You now need to give some inputs: """)
# 3.3.1. Ask for seed site, sites you want to avoid, https issues, how many to visit,
start_site = input("Type the website you wish to start from: ")
avoid_sites = input("Are there any sites you wish to avoid? Type them here, separated by a pipe (|). All sites in those domains won't be visited, so just type in the root and all sites beneath it will be avoided: ")
steps = input("How many sites would you like to visit. These are the sites we will actually go to: ")
secured = input("Enter 'True' if you would like to include sites that are not secured (http). Enter 'False' if not: ")
proportion_answer = input("Enter '1' if we should visit all links from sites. Otherwise, we will only visit a percentage (sigmoid curve). 1/0?: ")

# 3.3.2. Store all from inputs
# Note: URLs trailing with a '/' generally means that the page is a directory. That means that other pages will be beneath it.
# However we will store all URLs in the same format - with no trailing '/'. This makes checking visited sites easier.
# The distinction between directories and pages will be made later.
try:
    start_site_string = str(start_site)
    # As a rule, strip all trailing '/'
    if start_site_string.endswith('/'):
        start_site_string = start_site_string[:-1]
except:
    exit("Error while handling starting website string")

try:
    steps_number = int(steps)
except ValueError:
    exit("Error while handling the number of steps. Please enter an integer")
except:
    exit("Error while handling the number of steps.")

# Whether or not we will visit unsecured webpages.
if 'True' in secured:
    secured_bool = True
else:
    secured_bool = False

try:
    no_go_list = avoid_sites.split('|')
    # Stripping trailing '/'
    for k in range(0,len(no_go_list)):
        if no_go_list[k].endswith('/'):
            no_go_list[k] = (no_go_list[k])[:-1]
except:
    exit("Error when splitting the 'no-go' sites")

try:
    propAnswerFinal = int(proportion_answer)
except:
    exit("Error when interpreting percentage of sites to visit.")

# 3.3.3. Create object
myCrawler = Crawler(start_site_string, steps_number, secured_bool, no_go_list)

###------------------------------- LOOP START -------------------------------###
# 4. Main script
wMainLoopSafety = 0
while len(myCrawler.sites_visited) < myCrawler.num_to_visit:
    # 4.1. Reset the delay
    myCrawler.crawl_delay = 15
    # 4.2. Take a starting website
    try:
        myCrawler.current_target = myCrawler.sites_to_visit.pop(0)
    except IndexError:
        exit("Finished.")
    # 4.3. Check if we WANT to visit it. (if not, we can record it as an ending stub in the diagram)
    # What shall we exclude? (1) Sites we just don't want to visit, (2) 'mailto' or 'ftp' schemes, (3) None sites or (4) # sites (seen on https://www.riotgames.com, for example.)
    # This bit excludes (1) sites we just don't want to visit:
    skip = False
    for preventIterator in range(0, len(myCrawler.no_goes)):                # All elements in a list
        if myCrawler.current_target.startswith(myCrawler.no_goes[preventIterator]):
            skip = True

    # If we don't want to visit the site, record it in the dictionary and set 'nogo': True. Then move onto the next site.
    if skip or 'mailto' in myCrawler.current_target or 'ftp' in myCrawler.current_target or myCrawler.current_target is None or myCrawler.current_target.startswith('#'):
        myCrawler.counter_attempts += 1
        myCrawler.sites_dict.update({myCrawler.counter_attempts:{'url':myCrawler.current_target,
                                                                 'links':None,
                                                                 'status':None,
                                                                 'redirect':None,
                                                                 'duration':None,
                                                                 'robots':False,
                                                                 'ToS':False,
                                                                 'Repeat':False,
                                                                 'nogo':True,
                                                                 'weird_url':False}})
        # Skip the rest of this code and move onto the next iteration of the loop.
        time.sleep(myCrawler.crawl_delay)
        continue

    # 4.4. Check if we have already visited it. This is why it is important to have links stored consistently. A trailing slash could prevent a desired match.
    # If we already visited, skip and set 'Repeat':True
    if myCrawler.current_target in myCrawler.sites_visited:
        myCrawler.counter_attempts += 1
        myCrawler.sites_dict.update({myCrawler.counter_attempts:{'url':myCrawler.current_target,
                                                                 'links':None,
                                                                 'status':None,
                                                                 'redirect':None,
                                                                 'duration':None,
                                                                 'robots':False,
                                                                 'ToS':False,
                                                                 'Repeat':True,
                                                                 'nogo':False,
                                                                 'weird_url':False}})
        # Skip the rest of this code and move onto the next iteration of the loop.
        time.sleep(myCrawler.crawl_delay)
        continue

    # 4.5. Check if we are PERMITTED to visit it (robots file)
    # Returns a bool TRUE if we can crawl. Also get the status of the Robots file (though we aren't currently using that)
    m_crawlable, robot_status = myCrawler.robots_check()
     # If we are prevented from crawling by Robots file, move onto the next and set 'robots':True.
    if not m_crawlable:
        myCrawler.counter_attempts += 1
        myCrawler.sites_dict.update({myCrawler.counter_attempts:{'url':myCrawler.current_target,
                                                                 'links':None,
                                                                 'status':None,
                                                                 'redirect':None,
                                                                 'duration':None,
                                                                 'robots':True,
                                                                 'ToS':False,
                                                                 'Repeat':False,
                                                                 'nogo':False,
                                                                 'weird_url':False}})
        # Skip the rest of this code and move onto the next iteration of the loop.
        time.sleep(myCrawler.crawl_delay)
        continue

    # 4.6. Check if the TERMS allow us to access the desired site
    # Since we are not completely probited from crawling, it stands to reason that we can visit the Homepage -> T&C's to check homepage.
    # We get ToS_outcome: bool on whether we can crawl. Also get tos_code for either homepage or ToS page.
    ToS_outcome, tos_code = myCrawler.ToS_check()
    # Only occurs if we didn't access ToS page.
    if tos_code == 0:
        print('No ToS page found. Going ahead with crawl...')
    # If ToS prohibits us, add URL to dict and set ToS:True.
    if ToS_outcome != 'Y':
        myCrawler.counter_attempts += 1
        myCrawler.sites_dict.update({myCrawler.counter_attempts:{'url':myCrawler.current_target,
                                                                 'links':None,
                                                                 'status':None,
                                                                 'redirect':None,
                                                                 'duration':None,
                                                                 'robots':False,
                                                                 'ToS':True,
                                                                 'Repeat':False,
                                                                 'nogo':False,
                                                                 'weird_url':False}})
         # Skip the rest of this code and move onto the next iteration of the loop.
        time.sleep(myCrawler.crawl_delay)
        continue

    # 4.7. Now we know that we can visit the site.
    main_link_list = []
    # Wait again:
    time.sleep(myCrawler.crawl_delay)
    #### Visit the desired site and extract content
    main_siteContentStuff = requests.get(myCrawler.current_target, headers = myCrawler.cusHeaders)
    # For getAbsUrl function.
    actual_url_main = main_siteContentStuff.url
    main_code = getSiteStatus(main_siteContentStuff, myCrawler)
    # If we are not able to properly access the site, set 'status' to our code and move on.
    if main_code[0] != '2':
        myCrawler.counter_attempts += 1
        myCrawler.sites_dict.update({myCrawler.counter_attempts:{'url':myCrawler.current_target,
                                                                 'links':None,
                                                                 'status':int(main_code),
                                                                 'redirect':None,
                                                                 'duration':None,
                                                                 'robots':False,
                                                                 'ToS':False,
                                                                 'Repeat':False,
                                                                 'nogo':False,
                                                                 'weird_url':False}})
        # Close this here because we will not reach the close statement properly.
        main_siteContentStuff.close()
        time.sleep(myCrawler.crawl_delay)
        continue

    main_soup = BeautifulSoup(main_siteContentStuff.text, 'lxml')

    # 4.8. Get links from page.
    # Get root url
    url_split_list = myCrawler.current_target.split('//',1)                     # Should give smth like ['https:','www.abcd.com/1/2/3/4...']
    domain_split_list = url_split_list[1].split('/',1)                          # Should give smth like ['www.abcd.com','1/2/3/4...']
    root_url = url_split_list[0] + '//' + domain_split_list[0]                  # Gives 'https://www.abcd.com'

    # For all links, get their absolute form. Then strip trailing '/' for uniformity. Then add to our store.
    for main_link in main_soup.find_all('a'):
        # links have lots of attributes. 'href' has the URL.
        link_to_add = main_link.get('href')
        # Get the absolute form of that link. Include the true form of the URL of current page - so we know if we are on a directory or not.
        link_to_add_NOW = getAbsUrl(link_to_add, url_split_list, root_url, actual_url_main)
        # Strip trailing '/'
        try:
            if link_to_add_NOW.endswith('/'):
                link_to_add_NOW = link_to_add_NOW[:-1]
        except AttributeError:
            pass                                                                # If it's NoneType, [:-1] won't work

        main_link_list.append(link_to_add_NOW)
    # Now every link that is added will have a full, absolute web address.

    # 4.9. Now double-check that the url we have reached is the same as our target:
    # An issue is that, because we have stripped the trailing slash, there is a good chance that these will not be equal.
    # Therefore test against both the current_target and one with an appended '/'
    weird_urlVal = False
    if main_siteContentStuff.url.endswith('/'):
        if main_siteContentStuff.url != myCrawler.current_target + '/':
            weird_urlVal = True
    else:
        if main_siteContentStuff.url != myCrawler.current_target:
            weird_urlVal = True
        # This means a strange redirect has occured, may not have been picked up by status_code. https://www.riotgames.com had an example of this.

    # 4.10. Store the information:
    myCrawler.counter_attempts += 1
    myCrawler.sites_dict.update({myCrawler.counter_attempts:{'url':myCrawler.current_target,
                                                             'links':main_link_list,
                                                             'status':main_siteContentStuff.status_code,
                                                             'redirect':main_siteContentStuff.is_redirect,
                                                             'duration':(main_siteContentStuff.elapsed).total_seconds(),
                                                             'robots':False,
                                                             'ToS':False,
                                                             'Repeat':False,
                                                             'nogo':False,
                                                             'weird_url':weird_urlVal}})

# 4.11. Close connection with site (done for each as soon as we are done with the command - so that connxn is open for minimum time)
    main_siteContentStuff.close()

# 4.11.5. Decide on a percentage of links to add to the final store.
    # We use random.sample() to sample without replacement.
    if len(main_link_list) <= 10 or propAnswerFinal == 1:
        proportionToAdd = main_link_list

    elif len(main_link_list) in range(11,400):
        # Here use 10 links plus 10 percent of the number of links we have.
        num_fraction = round(len(main_link_list)/10) + 10
        proportionToAdd = random.sample(main_link_list, num_fraction)

    else:
        proportionToAdd = random.sample(main_link_list, 50)



# 4.12. Add links to the sites we have left to visit and add our current site to visited_sites list.
    myCrawler.sites_to_visit.extend(proportionToAdd)
    myCrawler.sites_visited.append(myCrawler.current_target)

# 4.13. Wait again - otherwise there might not be sufficient time between a request to the TARGET and to the next robots page
    time.sleep(myCrawler.crawl_delay)
#### 4.14. Delete excess content. Most variables in functions shall be automatically cleared as we leave scope.
    del main_link_list, main_siteContentStuff, main_soup
    # This variable prevents infinite while loops.
    wMainLoopSafety += 1
    if wMainLoopSafety >= 1000:
        break

###------------------------------- LOOP END -------------------------------###
