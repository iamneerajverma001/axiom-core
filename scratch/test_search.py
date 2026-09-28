import urllib.request
import urllib.parse
import json

def search_wiki(query):
    wiki_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote_plus(query)}&limit=3&namespace=0&format=json"
    try:
        req = urllib.request.Request(wiki_url, headers={'User-Agent': 'AxiomOmni/1.0'})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data and len(data) >= 4 and data[3]:
                return [{"title": data[1][i], "url": data[3][i]} for i in range(len(data[3]))]
    except Exception as e:
        print("Wiki error:", e)
    return []

print("Results for 'Rajkiya Engineering College':", search_wiki("Rajkiya Engineering College"))
print("Results for 'Python':", search_wiki("Python"))

