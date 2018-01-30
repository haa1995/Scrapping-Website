import requests
from goose3 import Goose
import spacy
import re
import json
from bs4 import BeautifulSoup
from spacy import displacy

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
        elif token.text == '.' and doc[i + 1].is_digit and doc[i - 1].is_digit == False:
            doc[i + 1].is_sent_start = True
        elif token.text == '.' and doc[i + 1].text.lower() != doc[i + 1].text:
            doc[i + 1].is_sent_start = True
        elif token.text == '.' and doc[i + 1].text == '"':
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
        for criteria in ['Informasi Menarik Terbaru', 'Membaca:', 'Baca juga', 'Baca :', 'BACA JUGA:', 'Artikel ini telah tayang di']:
            for i in soup.find_all("p"):
                if i.text.find(criteria) >=0 :
                    i.extract()


        for i in soup.find_all("strong"):
            if i.text.find('Baca:') >=0 :
                i.extract()
        raw_html = soup.prettify().replace("</strong>", "    </strong>")
        article = self.g.extract(raw_html=raw_html)

        content = self._getResult(article)

        doc = self.nlp(content)
        html = displacy.render(doc, style='ent')
        result = {
            "title": article.title,
            "url": url,
            "content": content,
            "html": html
        }

        return json.dumps(result)

    def _getResult(self, article):
        text = article.cleaned_text.replace(".", ". ").replace("“", '"').replace("”", '"').replace("Â", "")
        text = text.replace("\n", "")
        text = self._punct_check(text)
        text = text.replace("  ", " ").replace("  ", " ").replace("  ", " ").replace("  ", " ").replace("  ", " ").replace("--","- ")
        doc = self.nlp(u"{0}".format(text))
        sentences = []
        index = 0
        for i, sent in enumerate(doc.sents):
            txt = sent.text
            txt = txt.strip().replace("**y**", ".")
            if len(txt) > 50:
                index = index + 1
                if (index <= 1):
                    stat = False
                    txt = txt.replace("–", " – ").replace("—", "-").replace("â", ':')
                    doc_sent = self.nlp(u"{0}".format(txt))
                    start = 0
                    for token in doc_sent[:8]:
                        if token.is_punct and token.text in ["-", "—", "–", "|", ":"]:
                            if stat == False:
                                start = token.i + 1
                                stat = True

                    if stat == False:
                        sentences.append(txt)
                    else:
                        sentences.append(doc_sent[start:].text.strip())
                else:
                    sentences.append(txt)



        final = []
        for s in sentences:
            if len(s.strip().replace("\n", "")) > 0:
                final.append(s.strip().replace("\n", ""))
        sentences = "\n\n".join(final)
        return sentences