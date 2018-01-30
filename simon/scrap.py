import requests
from goose3 import Goose
import spacy
import re
import json
from bs4 import BeautifulSoup

USER_AGENT = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6)'
              ' AppleWebKit/537.36 (KHTML, like Gecko)'
              ' Chrome/58.0.3029.96 Safari/537.36')

KNOWN_PATTERNS = json.loads(open("config/pattern.json", "r").read())

LANG = "id"

def sbd_component(doc):
    for i, token in enumerate(doc[:-2]):
        if token.text == '.' and doc[i + 1].is_title:
            doc[i + 1].is_sent_start = True
        elif token.text == '.' and doc[i + 1].is_upper:
            doc[i + 1].is_sent_start = True
        elif token.text == '.' and doc[i + 1].is_punct:
            doc[i + 1].is_sent_start = True
        elif token.text == '.' and doc[i + 1].is_digit:
            doc[i + 1].is_sent_start = True
    return doc

nlp = spacy.load("model_postag_ner/")
nlp.add_pipe(sbd_component, before='parser')  # insert before the parser


class Scrap(object):
    def __init__(self):
        self.nlp = nlp
        self.KNOWN_PATTERNS = KNOWN_PATTERNS
        self.USER_AGENT = USER_AGENT
        self.LANG = LANG
        self.g = Goose({
            'enable_image_fetching': False,
            'use_meta_language': False,
            'target_language': self.LANG,
            'browser_user_agent': self.USER_AGENT,
            'known_context_patterns': self.KNOWN_PATTERNS,
        })


    def _punct_check(self, text):
        str_in_doublequotes = r'"([^"]*)"'
        in_quotes = re.findall(str_in_doublequotes, text)
        for z in in_quotes:
            text = text.replace(z, z.replace('.', '**y**'))
        return text


    def getURLContent(self, url):
        article = self.g.extract(url=url)

        return self._getResult(article)

    def getHTMLContent(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36',
            'Referer': 'https://www.optigura.com/uk/product/gold-standard-100-whey/',
            'X-Requested-With': 'XMLHttpRequest'
        }
        text = requests.get(url, timeout=10, headers=headers)
        raw_html = text.text
        soup = BeautifulSoup(raw_html, "html5lib")
        for i in soup.find_all("p"):
            if i.text.find('Membaca') >=0 :
                i.extract()
        for i in soup.find_all("p"):
            if i.text.find('Baca juga') >=0 :
                i.extract()
        for i in soup.find_all("p"):
            if i.text.find('Baca :') >=0 :
                i.extract()

        for i in soup.find_all("strong"):
            if i.text.find('Baca:') >=0 :
                i.extract()
        raw_html = soup.prettify().replace("</strong>", "    </strong>")
        article = self.g.extract(raw_html=raw_html)

        return self._getResult(article)

    def _getResult(self, article):
        text = article.cleaned_text.replace(".", ". ").replace("“", '"').replace("”", '"')
        text = text.replace("\n", "")
        text = self._punct_check(text)
        text = text.replace("  ", " ")
        doc = self.nlp(text)
        sentences = []
        index = 0
        for i, sent in enumerate(doc.sents):
            txt = sent.text
            txt = txt.strip().replace("**y**", ".")
            if len(txt) > 15:
                if (index == 0):
                    stat = False
                    txt = txt.replace("–", " – ")
                    doc_sent = nlp(txt)
                    start = 0
                    for token in doc[:10]:
                        if token.is_punct and token.text in ["-", "—", "–", "|", ":"]:
                            start = token.i + 1
                            print(start)
                            stat = True

                    if stat == False:
                        sentences.append(txt)
                    else:
                        sentences.append(doc_sent[start:].text.strip())
                else:
                    sentences.append(txt)
                index = index + 1

        final = []
        for s in sentences:
            if len(s.strip().replace("\n", "")) > 0:
                final.append(s.strip().replace("\n", ""))
        sentences = "\n\n".join(final)
        return sentences