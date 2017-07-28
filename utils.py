import re
from webbrowser import open_new_tab

import discogs_client  # https://github.com/discogs/discogs_client
from lxml import html
import requests

import wptools  # https://github.com/siznax/wptools updated for python 3

with open("token.txt", "r") as f:
    # A text file containing only a user token from https://www.discogs.com/settings/developers
    token = f.readline().strip()
discogs = discogs_client.Client('M4a_tagger/0.9', user_token=token)


def parse_dbpedia(input_title, url=""):
    def query(q, site="https://dbpedia.org/sparql", parameters=None):
        """
        Returns JSON result from given url
        Raises requests.RequestException if something goes wrong with the request
        """
        # TODO: generalise to allow for use in wiki function as well
        if not parameters:
            parameters = {"query": q}

        try:
            resp = requests.get(site, params=parameters, headers={"Accept": "application/json"})
        except requests.ConnectionError:
            print("Connection failed to: " + site)
            raise requests.RequestException()
        except requests.Timeout:
            print("Timeout to: " + site)
            raise requests.RequestException()
        except requests.TooManyRedirects:
            print("Too many redirects to: " + site)
            raise requests.RequestException()
        except requests.RequestException() as e:
            print(repr(e))
            raise

        if resp.status_code != 200:
            print("HTTP status code = " + resp.status_code)
            raise requests.RequestException()

        try:
            json = resp.json()
        except ValueError:
            print("No JSON object could be decoded from: " + resp.url)
            raise requests.RequestException()

        return json

    def get_property(data):
        pattern = """
                select ?{property} where {{
                <{uri}> {a}:{property} ?{property} }}"""
        json = query(pattern.format(**data))
        prop = json["results"]["bindings"][0][data["property"]]["value"]
        return prop

    tags = [""] * 5

    if url:
        dbpedia_uri = "https://dbpedia.org/resource/" + url.split("/")[-1]
    else:
        try:
            dbpedia_uri = query("",
                                site="https://lookup.dbpedia.org/api/search/KeywordSearch",
                                parameters={"QueryClass": "MusicalWork",
                                            "QueryString": input_title})["results"][0]["uri"]
            url = get_property({"a": "foaf", "property": "isPrimaryTopicOf", "uri": dbpedia_uri})
        except Exception as e:
            print("1", repr(e))
            return "", tags

    vars = ["name", "album", "artist", "year", "genre"]
    pattern = """
              select * where {{
               <{0}> foaf:name ?name .
               <{0}> dbo:album ?album .
               <{0}> dbo:musicalArtist ?artist .
               <{0}> dbo:releaseDate ?year .
               <{0}> dbo:genre ?genre .
              }} limit 1
              """

    try:
        json = query(pattern.format(dbpedia_uri))
        properties = json["results"]["bindings"][0]

        for i, var in enumerate(vars):
            value = properties[var]["value"]
            if properties[var]["type"] == "uri":
                try:
                    tags[i] = get_property({"a": "foaf", "property": "name", "uri": value})
                except IndexError:
                    tags[i] = get_property({"a": "rdfs", "property": "label", "uri": value})
            else:
                tags[i] = value
    except Exception as e:
        print("2", repr(e))

    tags[3] = tags[3].split("-")[0]

    return url, tags


def parse_wiki(title):
    if not title:
        return [""] * 5

    labels = ["Name",
              "from Album",
              "Artist",
              "Released",
              "Genre"]
    alt_labels = ["Name",
                  "Album",
                  "Artist",
                  "Released",
                  "Genre"]

    info_box = wptools.get_infobox(title)

    tags = [info_box.get(label, "") for label in labels]
    for i in range(len(tags)):
        if not tags[i]:
            tags[i] = info_box.get(alt_labels[i], "")
        if tags[i].startswith("<template"):
            text_list = html.fromstring(tags[i]).xpath("//text()")
            for text in text_list:
                if text.getparent().tag == "value":
                    tags[i] = text
                    break
        tags[i] = tags[i].replace("[", "").replace("]", "")

    year = re.search("(\d{4})", tags[3])
    if year:
        tags[3] = year.group(1)
    return tags


def parse_discogs(title, album):
    if not (title and album):
        return (0, 0), ["", "", "", (0, 0), "", ""]

    discogs_song = discogs.search(title, type="release")[0]
    discogs_album = discogs.search(album, type="release")[0]

    # Added to force loading of titles TODO: possible bug, possibly fixed?
    # _ = discogs_song.artists[0].name
    # _ = discogs_album.artists[0].name
    # ###

    # try:
    #     track_num = [track.title for track in discogs_album.tracklist].index(discogs_song.master.title) + 1
    # except ValueError:
    #     track_num = 0

    track_num = 0
    for track in discogs_album.tracklist:
        track_num += 1
        if track.title == discogs_song.master.title:
            break
    else:
        track_num = 0

    track_total = len(discogs_album.tracklist)
    tracks = (track_num, track_total)
    tags = [discogs_song.title,
            discogs_album.title,
            discogs_song.artists[0].name,
            tracks,
            str(discogs_song.year),
            discogs_song.genres[0]]

    return tracks, tags


def get_external_tags(title="", wiki_page="", browser=True):
    wiki_page, tags_dbpedia = parse_dbpedia(title, wiki_page)  # 3 secs

    if wiki_page and browser:
        open_new_tab(wiki_page)

    tags_wiki = parse_wiki(wiki_page.split("/")[-1])  # 3 secs

    track_nums, tags_discogs = parse_discogs(tags_wiki[0], tags_wiki[1])  # 5 secs

    tags_wiki.insert(3, track_nums)
    tags_dbpedia.insert(3, track_nums)

    return tags_dbpedia, tags_wiki, tags_discogs


if __name__ == '__main__':
    external_tags = get_external_tags(
        title="Tom's Diner")  # , wiki_page="http://en.wikipedia.org/wiki/Only_You_(Yazoo_song)")
    if external_tags:
        print(external_tags[0])
        print(external_tags[1])
        print(external_tags[2])
