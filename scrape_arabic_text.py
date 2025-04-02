import argparse
import json
import pathlib
import re
import time

import bs4
from bs4 import BeautifulSoup
from playwright.sync_api import Browser, sync_playwright

WEBSITE = "https://learning.aljazeera.net/en"

def extract_cards(content: str):
    soup = BeautifulSoup(content, "html.parser")
    content_bottom = soup.find('div', class_='region region-content-bottom')
    # Find all divs with class="card col-md-4 col-sm-4 col-xs-12"
    cards = content_bottom.find_all('div', class_='card col-md-4 col-sm-4 col-xs-12')
    return cards

def extract_text(div):
    texts = []
    for d in div.find_all("p"):
        text = d.get_text()
        text = text.replace("\xa0", " ")
        text = re.sub(r'\s+', ' ', text).strip()
        texts.append(text)
    return texts
    

def extract_article_content(website: str):
    with sync_playwright() as pw:
        chrome = pw.chromium.launch()
        page = chrome.new_page()
        page.goto(website)
        page.wait_for_selector(".pull-left")
        soup = BeautifulSoup(page.content(), 'html.parser')
        div = list(soup.find_all('div', class_=re.compile('.*body-text field.*')))[0]
        rtl = extract_text(div)
        text = " ".join(rtl)
        tashkeel = None

        # Detect Tashkeel button
        all_li_elements = page.query_selector_all('li')
        filtered_buttons = []
        for li in all_li_elements:
            class_name = li.get_attribute('class')
            if class_name and 'pull-right' in class_name and 'btn' in class_name and 'tashkeel' in class_name:
                filtered_buttons.append(li)
        tashkeel_button = None if len(filtered_buttons) == 0 else filtered_buttons[0]
        
        # Extract tashkeel text
        if tashkeel_button:    
            div = list(soup.find_all('div', class_=re.compile('.*body-text hidden field.*')))[0]
            rtl_tashkeel = extract_text(div)
            tashkeel = " ".join(rtl_tashkeel)
            
        return text, tashkeel

    

def extract_article_links(website: str) -> dict[str, str]:
    res = {}
    with sync_playwright() as pw:
        chrome = pw.chromium.launch()
        page = chrome.new_page()
        page.goto(website)
        page.wait_for_selector('.region-content-bottom')
        
        # Find the div with class="region region-content-bottom"
        
        cards = extract_cards(page.content())
        print(f"Number of cards: {len(cards)}")

        while True:
            load_more = page.query_selector('a.button[title="Load more items"]')
            if not load_more or not load_more.is_visible():
                break
            
            # Scroll to button and click
            load_more.click()
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1000)



            cards = extract_cards(page.content())
            print(f"Number of cards: {len(cards)}")
            



        cards = extract_cards(page.content())
        print(f"Number of cards: {len(cards)}")

        soup = BeautifulSoup(page.content(), 'html.parser')
        # Find the div with class="region region-content-bottom"
        content_bottom = soup.find('div', class_='region region-content-bottom')

        # Find all divs with class="card col-md-4 col-sm-4 col-xs-12"
        cards = content_bottom.find_all('div', class_='card col-md-4 col-sm-4 col-xs-12')
        for card in cards:
            # Extract the href link
            a_content = card.find('a') 
            link = a_content['href']
            title = a_content.get_text(strip=True)

            # Extract the content of div with class="lang-break"
            lang_break = card.find('div', class_='lang-break')
            lang_break_content = lang_break.get_text(strip=True) if lang_break else None

            if lang_break_content is not None:
                res[title] = {
                    'link': f"{WEBSITE}/{link.split('/en/')[1]}",
                    'lang_break_content': lang_break_content
                }
    return res

def remove_tashkeel(text):
    # Regular expression pattern for Arabic tashkeel
    tashkeel_pattern = re.compile(r'[\u0617-\u061A\u064B-\u0652\u06D6-\u06ED\u08D4-\u08E1\u08D4-\u08ED\u08F4-\u08FF]')
    


    # Remove tashkeel
    text_without_tashkeel = re.sub(tashkeel_pattern, '', text)
    
    return text_without_tashkeel

def main(out_json: pathlib.Path):

    articles = extract_article_links(WEBSITE)
    for title, content in articles.items():
        print(title, content['link'], content["lang_break_content"])
        print("-"*20)
        try: 
            article, tashkeel = extract_article_content(content['link'])
        except Exception as e:
            print("Cannot extract article: continue", e)
            continue
        sentences = [s for s in re.split('[.]', article) if len(s.strip()) > 0]
        articles[title]["article"] = sentences
        if tashkeel is not None:
            sentences_tashkeel = [s for s in re.split('[.]', tashkeel) if len(s.strip()) > 0]
            sentences = [remove_tashkeel(sentence) for sentence in sentences_tashkeel]
            articles[title]["tashkeel"] = sentences_tashkeel
            articles[title]["article"] = sentences
            print(f"num sentence text {len(sentences)}. Num sentence tashkeel {len(sentences_tashkeel)}")
            

    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)

        



if __name__ == "__main__":
    parser = argparse.ArgumentParser("Scrape aljazeera learning to have a variety of text with tashkeel")
    parser.add_argument("--out-json", "-o", type=pathlib.Path)
    args = parser.parse_args()
    main(args.out_json)
    
