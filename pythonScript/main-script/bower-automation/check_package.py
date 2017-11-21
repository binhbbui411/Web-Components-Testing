from datetime import datetime
from socket import error as SocketError
import mysql.connector
import sys
import re # regex
from urllib.request import urlopen
import simplejson
import time
import multiprocessing as mp
import errno

### GLOBAL section
# Define the database name
DB_NAME = 'bower_packages'

# Define the config for database connection
config = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'database': DB_NAME,
    'raise_on_warnings': True
}

# Define a list of keywords to check
wckeywords = ["web-components", "web-component", "custom-element", "custom-elements", "polymer"]

# Define a boolean to check dependencies after checking keywords
checkDependencies = True

# Query for adding checked time
add_checked = (
    "UPDATE registry "
    "SET checked = %s "
    "WHERE url = %s"
)

# Query for adding is_wc and checked
add_is_wc = (
    "UPDATE registry "
    "SET is_wc = %s, checked = %s "
    "WHERE url = %s"
)

# First I loop through the owner and repo I got from the query then I get the owner and repo using dictionary index. After that, actually add a column to the db as `is_github`. So that I can check if it's 0/1/null --> add to checked. Next, get the bowerjson, if fail then --> checked --> done. Check keywords, if fail --> checcked --> not. If not, check if wc, if wc --> is_wc = 1, if not --> go to dependencies, if wc --> is_wc = 1, if not is_wc = 0 --> checked.
def check_element(package):
    global checkDependencies

    # Store the values to simpler name for easy future use (except id because that's Python reserved name)
    repo = package['repo']
    owner = package['owner']
    url = package['url']
    checked = package['checked']
    is_wc = package['is_wc']
    is_github = package['is_github']
    package_id = package['package_id']

    # Define cursor for executing query
    cursor = cnx.cursor(buffered=True, dictionary=True)

    # Get the checked time in mysql datetime format
    checked_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    ### FIRST CONDITION STARTS: check if the element has been checked
    if not checked:
        # Keep track of the progress
        print("{0} {1}".format(package['id'], url))

        ### SECOND CONDTION STARTS: check if it's a github repo reading is_github column (0 or 1)
        if is_github:
            # Generate the raw bower.json link using rawgit.com. Is it reliable enough?
            bower_json_link = "https://rawgit.com/{0}/{1}/master/bower.json".format(owner, repo)

            try:
                # Retrieve the content read from bower.json
                data = urlopen(bower_json_link).read()
                # Loads it into a JSON
                package_json = simplejson.loads(data)
            except simplejson.scanner.JSONDecodeError:
                cursor.execute(add_checked, (checked_time, url))
                cnx.commit()
                return
            except SocketError as e:
                if e.errno != errno.ECONNRESET:
                    raise # Not error we are looking for
                # Handle error here.
                check_element(package)

            checkDependencies = True

            ### THIRD CONDITION STARTS: Check if there is keywords in bower.json. If there is, check if any of the legit keywords appearing there
            if 'keywords' in package_json:
                keywords = package_json['keywords']
                if keywords:
                    # Converting things to lowercase for the sake of using `in`
                    keywords = [x.lower() for x in keywords]
                    # Define a variable for checking if the keywords section contains any keywords related to web-compoents
                    hasKeyword = any(x in wckeywords for x in keywords)
                    if hasKeyword:
                        print("Qualified!")
                        checkDependencies = False
                        cursor.execute(add_is_wc, (1, checked_time, url))
                        cnx.commit()
                ### THIRD CONDITION ENDS: Do nothing, program will move on fourth condition
                else:
                    print("No matched keywords!")
                    pass

            ### FOURTH CONDITION STARTS: Check if there is polymer in dependencies. If there is, add checked and is_wc. If not, add is_wc and checked.
            if 'dependencies' in package_json and checkDependencies:
                dependencies = package_json['dependencies']
                if dependencies:
                    # Converting things to lowercase for the sake of using `in`
                    dependencies = [x.lower() for x in package_json['dependencies']]
                    if 'polymer' in dependencies:
                        print("Qualified!")
                        cursor.execute(add_is_wc, (1, checked_time, url))
                        cnx.commit()
                else:
                    print("no polymer!")
                    cursor.execute(add_is_wc, (0, checked_time, url))
                    cnx.commit()
                    pass

        ### SECOND CONDITION ENDS: add checked time
        else:
            print("Not a github repo!")
            cursor.execute(add_checked, (checked_time, url))
            cnx.commit()
    ### FIRST CONDITION ENDS: else just do nothing
    else:
        print("Already checked!")
        pass

if __name__ == "__main__":
    # Make a connection to database
    cnx = mysql.connector.connect(**config)

    # Define cursor for executing query
    cursor = cnx.cursor(buffered=True, dictionary=True)

    query = ("SELECT * FROM registry WHERE checked IS NULL")

    cursor.execute(query)

    for package in cursor:
        check_element(package)

    cursor.close()
    cnx.close()

    # print("There are a total of {0} repos to check.".format(len(urls)))
    #
    # # Create a pool with n processors
    # pool = mp.Pool(processes=16)
    #
    # # Get the start time
    # starttime = time.time()
    #
    # # r = pool.map(checkElement, urls)
    # for i in range(len(urls)):
    #     try:
    #         pool.apply_async(checkElement, args = (urls[i], ))
    #     except UnicodeDecodeError:
    #         pass
    # pool.close()
    # pool.join()
    #
    # elapsedtime = time.time() - starttime
    #
    # print("Times taken: {0}".format(elapsedtime))
    # checkElement("https://github.com/NawaraGFX/Counter-Up.git")