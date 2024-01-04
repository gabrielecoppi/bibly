import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import time
import numpy as np 
import re
import copy

key_list = ['authors', 'title', 'doctype', 'eprint', 'archivePrefix', 'primaryClass', \
            'doi', 'journal', 'volume', 'number', 'pages', 'year', 'doctype', 'source']

class Scholar:

    def __init__(self, url):

        self.url = url

    @classmethod
    def from_user(cls, user, page_size = 1000, sort_by = 'citations'):  # sort_by='pubdate'

        if sort_by not in ['citations', 'pubdate']:
            sort_by = 'citations'

        url = 'https://scholar.google.com/citations?' \
              'user={}' \
              '&pagesize={}' \
              '&sortby={}'.format(user, page_size, sort_by)

        return cls(url)

    def get_pageinfo(self, page_url = None):
        
        if page_url is None:
            page_url = copy.copy(self.url)

        #download the page
        response=requests.get(page_url)

        # check successful response
        if response.status_code != 200:
            print('Status code:', response.status_code)
            raise Exception('Failed to fetch web page ')

        #parse using beautiful soup
        doc = BeautifulSoup(response.content,'html.parser')

        return doc

    def extract_from_author_profile(self):

        doc = self.get_pageinfo()
        
        self.scholar = doc.find('div', {'id': 'gsc_prf_in'}).text
        
        papers = doc.body.find_all('tr', attrs={'class': 'gsc_a_tr'})
        
        for paper in papers:
            paper_doc = BeautifulSoup(str(paper), features="html.parser")
            try:
                citations_a = paper_doc.find('a', {'class': 'gsc_a_ac gs_ibl'})
                if citations_a is None:
                    citations_a = paper_doc.find('a', {'class': 'gsc_a_ac gs_ibl gsc_a_acm'})

                this_paper = {'title': paper_doc.find('a').text,
                              'year': paper_doc.find_all('span')[-1].text,
                              'n_citations': citations_a.text,
                              'citations_url': citations_a['href'],
                              'authors': paper_doc.find_all('div', {'class': 'gs_gray'})[0].text,
                              'journal': paper_doc.find_all('div', {'class': 'gs_gray'})[1].text,
                              'url': '{}#d=gs_md_cita-d&u=%2F{}'.format(self.url,
                                                                        quote(paper_doc.find('a')['href'])[1:]),
                              'source': 'google_scholar'}

                if not this_paper['n_citations']:
                    this_paper['n_citations'] = "0"

                if this_paper['journal'].endswith(', ' + this_paper['year']):
                    this_paper['journal'] = this_paper['journal'][:-len(', ' + this_paper['year'])]
                self.parsed_papers.append(this_paper)
            except IndexError:
                print('Warning: error parsing paper.')
            except AttributeError:
                print('Warning: error parsing paper.')

    def extract_from_citation_page(self, doc):

        paper_tag = doc.select('[data-lid]')
        link_tag = doc.find_all('h3',{"class" : "gs_rt"})
        authors_tag = doc.find_all("div", {"class": "gs_a"})

        titles = []
  
        for tag in paper_tag:
            titles.append(tag.select('h3')[0].get_text())

        links = []

        for i in range(len(link_tag)) :
            links.append(link_tag[i].a['href'])

        years = []
        publication = []
        authors = []
        source = []
        for i in range(len(authors_tag)):
            authortag_text = (authors_tag[i].text).split()
            year = int(re.search(r'\d+', authors_tag[i].text).group())
            years.append(year)
            publication.append(authortag_text[-1])
            author = authortag_text[0] + ' ' + re.sub(',','', authortag_text[1])
            authors.append(author)
            source.append('google_scholar')

            return authors, titles, links, publication, years

    def extract_citations(self, title, num_citation):

        parser = {'authors': [],
                  'title': [],
                  'links': [],
                  'year': [],
                  'journal':[],
                  'source': []}

        for i in range(0, int(np.ceil(num_citation/10)*10), 10):

            idx = int(re.search('.com/scholar').span())

            page_num = 'start={}'.format(int(i))
            temp = self.url[:idx[1]+1]+page_num+self.url[idx[1]:]

            doc = self.get_pageinfo(page_url=temp)

            authors, titles, links, publication, years, source = self.extract_from_citation_page(doc)

            parser['authors'].append(authors)
            parser['title'].append(title)
            parser['links'].append(links)
            parser['year'].append(authors)
            parser['journal'].append(publication)
            parser['source'].append(source)

            time.sleep(30)

        return parser
