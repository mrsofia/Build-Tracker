from flask import Flask, render_template
from flask_bootstrap import Bootstrap
import urllib3
from lxml import etree
from io import StringIO, BytesIO
import re

app = Flask(__name__)
app.debug = False
http = urllib3.PoolManager()
Bootstrap(app)


@app.route('/')
def index():
    builds = get_build_html()
    if builds['app1_builds'].status != 200 or builds['app2_builds'].status != 200:
        return 'something messed up, the artifactory build links did not return a 200 status code.'
    app1_builds = extract_builds(builds['app1_builds'])
    app2_builds = extract_builds(builds['app2_builds'])

    app1_builds = remove_metadata(app1_builds[:])
    app2_builds = remove_metadata(app2_builds[:])

    app1_builds = clean_builds(app1_builds[::-1])
    app2_builds = clean_builds(app2_builds[::-1])

    latest_app1 = find_latest_build(remove_tagged_builds(app1_builds[:]))
    latest_app2 = find_latest_build(remove_tagged_builds(app2_builds[:]))

    return render_template("index.html", app1_builds=app1_builds[1:], app2_builds=app2_builds[1:],
                           latest_app1=latest_app1, latest_app2=latest_app2)


def clean_builds(builds):
    cleaned_builds = []
    for build in builds:
        cleaned_builds.append(str(build).replace('/',''))
    return cleaned_builds


def get_build_html():
    headers = urllib3.util.make_headers(basic_auth='username:password')
    app1_builds = http.request('GET', 'https://artifactory.yoursite.io/artifactory/gradle-dev-local/com/core/app1/',headers=headers)
    app2_builds = http.request('GET', 'https://artifactory.yoursite.io/artifactory/gradle-dev-local/com/devtools/app2/',headers=headers)
    builds = {'app1_builds': app1_builds, 'app2_builds': app2_builds}
    return builds


def extract_builds(builds_request):
    html = builds_request.data
    tree = etree.parse(BytesIO(html), etree.HTMLParser())
    builds = tree.xpath('//a/@href')
    return builds

def remove_metadata(builds):
    builds.remove('../')
    builds.remove('maven-metadata.xml')
    return builds


def find_latest_build(builds):
    results = []
    # place all versions with highest major number in a new list
    """ select links with highest major versions. 'select all until first period', then typecast them inline
        and add them to results list IFF they match the highest version number.
    """
    highest_major_version = -1
    for build in builds:
        major_version = build.split(".")[0]
        if int(major_version) > highest_major_version:
            highest_major_version = int(major_version)

    builds_with_highest_major_version = []
    for build in builds:
        major_version = build.split(".")[0]
        if int(major_version) == highest_major_version:
            builds_with_highest_major_version.append(build)

    """ place all links with the highest minor versions into another new list
    """
    highest_minor_version = -1
    for build in builds_with_highest_major_version:
        minor_version = build.split(".")[1]
        if int(minor_version) > highest_minor_version:
            highest_minor_version = int(minor_version)

    builds_with_highest_minor_version = []
    for build in builds_with_highest_major_version:
        minor_version = build.split(".")[1]
        if int(minor_version) == highest_minor_version:
            builds_with_highest_minor_version.append(build)

    """ place all links with the highest minor-minor versions into yet another new list
    """
    highest_dev_version = -1
    for build in builds_with_highest_minor_version:
        dev_version = build.split(".")[2].replace('/', '')
        if int(dev_version) > highest_dev_version:
            highest_dev_version = int(dev_version)

    builds_with_highest_dev_version = []
    for build in builds_with_highest_minor_version:
        dev_version = build.split(".")[2].replace('/', '')
        if int(dev_version) == highest_dev_version:
            builds_with_highest_dev_version.append(build)

    most_recent_version = builds_with_highest_dev_version[0].replace('/', '')
    return most_recent_version


def remove_tagged_builds(builds):
    # remove all versions with non-version-appropriate chars.
    builds_to_remove = []

    for build in builds:
        l = re.findall(r'[\D]', build)
        non_numeric_chars = list(filter(lambda a: a != '.' and a != '/', l))
        if len(non_numeric_chars) != 0:
            builds_to_remove.append(build)
    for build in builds_to_remove:
        builds.remove(build)

    return builds

if __name__ == "__main__":
    app.run(host='0.0.0.0')