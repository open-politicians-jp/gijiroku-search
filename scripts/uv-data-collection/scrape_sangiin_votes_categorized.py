import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import json
import os

def get_voting_results(voting_page_url):
    response = requests.get(voting_page_url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    party_votes = {}

    # Party-level results
    party_sections = soup.find_all('h4', class_='party')
    for party_section in party_sections:
        party_name = party_section.get_text(strip=True)
        sanpilist_dl = party_section.find_next_sibling('dl', class_='sanpilist')
        
        sansei_count = "0"
        hantai_count = "0"

        if sanpilist_dl:
            dt_tag = sanpilist_dl.find('dt', class_='party')
            if dt_tag:
                counts_text = dt_tag.get_text(strip=True)
                sansei_match = re.search(r'賛成票\s*(\d+)', counts_text)
                hantai_match = re.search(r'反対票\s*(\d+)', counts_text)
                sansei_count = sansei_match.group(1) if sansei_match else "0"
                hantai_count = hantai_match.group(1) if hantai_match else "0"
        
        party_votes[party_name] = {'賛成': sansei_count, '反対': hantai_count, '議員': []}

        # Individual voter results for this party
        ul_tag = sanpilist_dl.find('ul', class_='flex') if sanpilist_dl else None
        if ul_tag:
            for li_tag in ul_tag.find_all('li', class_='giin'):
                name_span = li_tag.find('span', class_='names')
                pros_span = li_tag.find('span', class_='pros')
                cons_span = li_tag.find('span', class_='cons')
                novote_span = li_tag.find('span', class_='novote')

                name = name_span.get_text(strip=True) if name_span else "不明"
                vote_cast = "不明"
                if pros_span and pros_span.get_text(strip=True) == "賛成":
                    vote_cast = "賛成"
                elif cons_span and cons_span.get_text(strip=True) == "反対":
                    vote_cast = "反対"
                elif novote_span:
                    vote_cast = "投票なし"
                
                party_votes[party_name]['議員'].append({'氏名': name, '投票': vote_cast})

    return party_votes

def main():
    base_url = "https://www.sangiin.go.jp/japanese/joho1/kousei/gian/217/"
    initial_url = urljoin(base_url, "gian.htm")
    output_dir = "/Users/hironeko/Work/private/new-jp-search/"

    try:
        response = requests.get(initial_url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all category headers and their corresponding tables
        category_headers = soup.find_all('h2', class_='title_text')
        
        file_counter = 2 # Start from tmp2.md/json

        for header in category_headers:
            category_name = header.get_text(strip=True)
            # Find the table immediately following this header
            current_table = header.find_next_sibling('table', class_='list_c')
            
            if not current_table:
                continue

            rows = current_table.find_all('tr')
            if not rows: # Skip empty tables
                continue

            for row in rows[1:]: # Skip header row
                cols = row.find_all('td')
                if len(cols) < 3: # Ensure enough columns for bill name and link
                    continue

                bill_name_tag = cols[2].find('a')
                if not bill_name_tag or not bill_name_tag.has_attr('href'):
                    continue

                bill_name = bill_name_tag.get_text(strip=True)
                detail_page_relative_url = bill_name_tag['href']
                detail_page_url = urljoin(base_url, detail_page_relative_url)

                # Fetch bill detail page to get voting results link
                detail_response = requests.get(detail_page_url)
                detail_response.encoding = 'utf-8'
                detail_soup = BeautifulSoup(detail_response.text, 'html.parser')

                saiketsu_header = detail_soup.find('th', string=re.compile(r"採決方法"))
                voting_page_url = None
                if saiketsu_header:
                    vote_link_cell = saiketsu_header.find_next_sibling('td')
                    vote_link = vote_link_cell.find('a') if vote_link_cell else None
                    if vote_link and vote_link.has_attr('href'):
                        # Construct the correct voting page URL, handling relative paths
                        voting_page_url = urljoin(detail_page_url, vote_link['href'])

                all_voting_data = {}
                if voting_page_url:
                    all_voting_data = get_voting_results(voting_page_url)
                
                # Generate unique filenames
                # Improved sanitization: allow Japanese characters, replace problematic ones with underscore
                safe_bill_name = re.sub(r'[\\/:*?"<>| ]', '_', bill_name)
                safe_bill_name = safe_bill_name[:100] # Limit length

                output_md_path = os.path.join(output_dir, f"tmp{file_counter}_{safe_bill_name}.md")
                output_json_path = os.path.join(output_dir, f"tmp{file_counter}_{safe_bill_name}.json")
                file_counter += 1

                # Save to JSON
                json_output = {bill_name: all_voting_data}
                with open(output_json_path, 'w', encoding='utf-8') as json_file:
                    json.dump(json_output, json_file, ensure_ascii=False, indent=4)
                print(f"投票結果が {output_json_path} に保存されました。")

                # Save to Markdown
                with open(output_md_path, 'w', encoding='utf-8') as md_file:
                    md_file.write(f"# 「{bill_name}」の投票結果\n\n")
                    md_file.write("## 政党別投票結果\n\n")
                    md_file.write("| 政党 | 賛成 | 反対 |\n")
                    md_file.write("|:---|---:|---:|\n")
                    for party, data in all_voting_data.items():
                        md_file.write(f"| {party} | {data['賛成']} | {data['反対']} |\n")
                    md_file.write("\n")

                    md_file.write("## 議員別投票結果（政党別）\n\n")
                    for party, data in all_voting_data.items():
                        md_file.write(f"### {party}\n\n")
                        md_file.write("| 氏名 | 投票 |\n")
                        md_file.write("|:---|:---|\n") 
                        for member in data['議員']:
                            md_file.write(f"| {member['氏名']} | {member['投票']} |\n")
                        md_file.write("\n")

                print(f"投票結果が {output_md_path} に保存されました。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()