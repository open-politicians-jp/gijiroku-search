import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

url = 'https://www.shugiin.go.jp/internet/itdb_annai.nsf/html/statics/syu/1giin.htm'
resp = requests.get(url, timeout=30)
resp.encoding = 'shift_jis'
soup = BeautifulSoup(resp.text, 'html.parser')
tables = soup.find_all('table')
print('tables', len(tables))
for idx, table in enumerate(tables):
    rows = table.find_all('tr')
    header = ''.join(cell.get_text(strip=True) for cell in rows[0].find_all(['th','td'])) if rows else ''
    sample = rows[1].get_text(strip=True) if len(rows) > 1 else ''
    print(idx, 'rows', len(rows), 'header', header[:40], 'sample', sample[:40])

nav_links = [urljoin(url, a['href']) for a in soup.select('a[href]') if 'giin' in a['href']]
print('nav links', nav_links[:10])
