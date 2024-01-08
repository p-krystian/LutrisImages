#!/usr/bin/env python3
import sqlite3, urllib.request, json
from os.path import exists as os_exists, expanduser as os_expanduser


def get_urls(slug:str) -> list:
  req = urllib.request.Request(
    url = "https://lutris.net/api/games",
    data = json.dumps({"games": [slug]}).encode("utf-8"),
    headers = {"Content-Type": "application/json"},
    method = "POST"
  )
  with urllib.request.urlopen(req, timeout=5) as request:
    info = json.loads(request.read())

  if len(info.get('results', [])) < 1:
    return ['', '']

  data = info['results'][0]
  return [data.get('banner_url') or '', data.get('coverart') or '']

def get_images(slug:str) -> dict:
  data = dict()

  while len(data.keys()) < 2:
    banner, cover = get_urls(slug)
    temp = dict()
    if banner: temp['banners'] = banner
    if cover: temp['coverart'] = cover
    temp.update(data)
    data.update(temp)
    if slug.count('-') < 3: break
    slug = '-'.join(slug.split('-')[:-1])

  return data

def download_images(slug:str, urls:dict) -> int:
  if len(urls.keys()) < 1:
    return 0
  path = f'{os_expanduser("~")}/.cache/lutris'
  downloaded = 1

  for kind,url in urls.items():
    extension = url.split('.')[-1]
    try: urllib.request.urlretrieve(url, f'{path}/{kind}/{slug}.{extension}')
    except: continue
    downloaded += 1

  return downloaded

def main(db_path:str) -> None:
  query = "SELECT name,slug from games WHERE NOT hidden OR hidden IS NULL;"
  print('Downloading...')

  with sqlite3.connect(db_path) as conn:
    cur = conn.cursor()
    for name,slug in cur.execute(query):
      print(f'{name} ->', end=' '*(48-len(name)))
      try: urls = get_images(slug)
      except:
        print('API connection error')
        continue
      downloaded = download_images(slug, urls)
      print(['Not found', 'Download error', '1/2', 'OK'][downloaded])

  print('Done!')


if __name__ == "__main__":
  db_path = f'{os_expanduser("~")}/.local/share/lutris/pga.db'
  c_path = f'{os_expanduser("~")}/.cache/lutris'

  if not (os_exists(f'{c_path}/banners') and os_exists(f'{c_path}/coverart')):
    print("Cache directories do not exist. Try running Lutris first")
  elif not os_exists(db_path):
    print("Lutris database not found!")
  elif input("This'll replace existing images. Continue? Y/N ").upper() == "Y":
    main(db_path)
