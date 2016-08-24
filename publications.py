#/usr/bin/env python
import numpy as np
import pandas as pd
import re
import requests
import warnings
import time
import sys
from IPython.display import display, HTML
import tabulate #sudo pip3 install tabulate
import utilities as ut
from bs4 import BeautifulSoup
from cmdlike import *
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_colwidth',200)
def update_column(ds,column,update=False):
    update_column=True
    if column in ds:
        if ds[column] and not update: #it update=True willreplace value
            update_column=False
    return update_column

def _get_doi(surname='Florez',\
        title=r'Baryonic violation of R-parity from anomalous $U(1)_H$',other=''):
        '''
        Search doi from http://search.crossref.org/ 
        '''
        doi={}
        search=''
        if surname:
            search=surname
        if title:
            if len(search)>0:
                search=search+', '+title
        if other:
            if len(search)>0:
                search=search+', '+other
                
        r=requests.get('http://search.crossref.org/?q=%s' %search)
        urldoi='http://dx.doi.org/'
        doitmp=''
        if len(r.text.split(urldoi))>1:
            doitmp=r.text.split(urldoi)[1].split("\'>")[0].replace('&lt;','<').replace('&gt;','>')
        #check doi is right by searching for all words in doi -> output title
        if doitmp:
            json='https://api.crossref.org/v1/works/'
            rr=requests.get( json+urldoi+doitmp )
            if rr.status_code==200:
                if 'message' in rr.json():
                    chktitle = re.sub(r"\$.*?\$","",title) # better remove all math expressions
                    chktitle = re.sub(r"[^a-zA-Z0-9 ]", " ", chktitle).split(' ')
                    if chktitle:
                        if not -1 in [(rr.json()["message"]['title'][0]).find(w)  for w in chktitle]:
                            doi=rr.json()["message"]
                        
        return doi
    
def _get_impact_factor_from_journal_name(journal_name='Physical Review D'):
    '''
      For the input Journal name obtain
      the pandas DataFrame with Years and IF as columns
    '''
    q=journal_name.lower().replace(' ','-')
    URL='http://www.journal-database.com/journal/%s.html' %q        
    r = requests.get(URL)
    return ut.html_to_DataFrame(r.content)
    #UDPATE in repo
    
def _get_quartil(issn='1550-7998',journal_hindex=False):
    URL='http://www.scimagojr.com/journalsearch.php?q='
    r=requests.get('%s%s' %(URL,issn))
    result=r.text.split('href="journalsearch.php?q=')
    quartil='';hindex_journal=''
    if type(result)==list and len(result)==3:
        id_jour=result[-1].split('">')[0]
        if id_jour:
            rr=requests.get('%s%s' %(URL,id_jour))
            quartil=grep('^\s+var dataquartiles = ',rr.text).split(';')
            quartil.remove('')
            if type(quartil)==list and len(quartil)>0:
                quartil=quartil[-1].replace('"','')
            hindex=rr.text.split('<div class="hindexnumber">')
            if type(hindex)==list and len(hindex)==2:
                hindex_journal=hindex[1].split('</div>')[0]
    if journal_hindex:
        return quartil,hindex_journal
    else:
        return quartil  
    
    
def _gs_profile_to_dataframes(user='-6mndWkAAAAJ',number_of_articles=100,sleep=10):
    '''
    Convert the first number_of_articles of a google scholar profile for user id
    to two dataframes
    1) Citations indices
    2) Article, Cites, Year columns
    '''
    i=0
     
    Citations_indices=pd.DataFrame()
    cited_articles=pd.DataFrame()
    chk_citations=False
    while True:
        if i>0:
            print('waiting %d sec. to avoid robot detection...' %sleep)
            time.sleep(sleep)
        iold=i
        i=i+100
        r=requests.get('https://scholar.google.com/citations?sortby=pubdate&hl=en&user=%s' %user\
                       +'&view_op=list_works&cstart=%d&pagesize=%d' %(iold,i) )
        
        if r.status_code==200:
            soup = BeautifulSoup(r.text,"lxml")
            s=soup.find_all("table")
            if len(s)==2: #proper formated profile output 
                chk_citations=True
                Citations_indices=Citations_indices.append( ut.html_to_DataFrame(s[0].decode(),\
                    headings=['Citations indices','All','Since %d' %(time.localtime().tm_year-5)]) )
                cited_articles=cited_articles.append(\
                                ut.html_to_DataFrame(s[1].decode(),headings=['Article','Cites','Year']) )
        if i>number_of_articles:
            break
                
        
    if chk_citations:
        cited_articles=cited_articles[\
                ~cited_articles.Article.isnull()].reset_index(drop=True)
        an=cited_articles[cited_articles.Year.isnull()]
        for i in an.index:
            cited_articles.loc[i,'Cites']=0
            cited_articles.loc[i,'Year']=an.ix[i]['Cites']
        
    return Citations_indices,cited_articles

class publications(object):
    '''Add Generic publication data'''
    pass
class articles(publications):
    '''Read csv file exported by Google Scholar Citations profile and
       automatically add informations about:
       DOI: from title and author
       Journal title: from DOI
       ISSN of Jornal
       Impact factor of journal
       Institution_Authors: requires Data Base
       '''
    journal=pd.Series()
    columns=pd.Series({'Full_Name':'Full_Name','Author_Names':'Author_Names','Control':'Control',\
                      'Institution_Authors':'Institution_Authors','Institution_Group':'Institution_Group'})
    cited_articles_hash=pd.Series()
    articles_hash=pd.Series()
    def __init__(self,csv_file='citations.csv',user='',citations_file=None,authors_file=None,group_file=None):
        #DEBUG: check file
        self.articles=pd.read_csv(csv_file).fillna('')
        #Fix problem with column Authors
        if self.articles.shape[0]>0 and self.articles.columns[0].find('Authors')>-1:
            self.articles=self.articles.rename(columns={self.articles.columns[0]:'Authors'})
        if citations_file:
            #DEBUG: check file
            self.citations=pd.read_csv(citations_file).fillna('')
            
        if authors_file:
            #DEBUG: chek is file exists,
            self.institution_authors=pd.read_csv(authors_file).fillna('')
            
        if group_file:
            #DEBUG: chek is file exists,
            self.institution_group=pd.read_csv(group_file).fillna('')
        if user:
            self.Citations_indices,self.cited_articles=_gs_profile_to_dataframes(\
                            user,number_of_articles=self.articles.shape[0],sleep=10)
            if self.cited_articles.shape[0]>0:
                self.cited_articles_hash=\
                    self.cited_articles.Article.str.replace(r"[^a-zA-Z0-9 ]", " ").str.lower().str.replace('\s+','')
                self.articles_hash=\
                    self.articles.Title.str.replace(r"[^a-zA-Z0-9 ]", " ").str.lower().str.replace('\s+','')
            
    def add_institution_author(self):
        #DEBUG: Check and load file
        full_name=input('Full name: ')
        #DEBUG: Ask for more author names and update author names separated by semicolons
        author_names=input('Author names\n(Example: Juan Perez; J. Perez; J. Pérez):\n')
        #DEBUG: default to 0
        control=input('Additional identitication number: ') 
        
        #DEBUG: if not file creates it
        iffile=False
        if not iffile:
            self.institution_authors=pd.DataFrame()
            
        self.institution_authors=self.institution_authors.append({self.columns.Full_Name:full_name,\
                                                              self.columns.Author_Names:author_names,\
                                                              self.columns.Control:control},ignore_index=True)
        self.institution_authors.to_csv('authors.csv',index=False)
        
    def add_institution_group(self):
        wrn='Author not found'
        search_query=input('Find author by first name and first surname\n(Example: Juan Pérez);\n')
        sql=search_query.split(' ')
        #DEBUG: low_case
        if len(sql)>0:
            sql_name=sql[0]
            if len(sql)>1:
                sql_surname=sql[1]
            else:
                sql_surname=''
            
            author_match=self.institution_authors[\
                             np.logical_and( self.institution_authors.Full_Name.str.contains(sql_name),\
                                             self.institution_authors.Full_Name.str.contains(sql_surname) )]
            if not author_match.shape[0]:
                author_match=self.institution_authors[\
                             np.logical_or( self.institution_authors.Full_Name.str.contains(sql_name),\
                                            self.institution_authors.Full_Name.str.contains(sql_surname) )]
            if not author_match.shape[0]:
                warnings.warn(wrn)
            else:    
                author_match=author_match.reset_index(drop=True)
                author_match['Number']=author_match.index
                if author_match.shape[0]==1:
                    author_Series=author_match.ix[0]
                    #print( tabulate.tabulate(author_match,headers='keys', tablefmt='psql'))
                else:
                    print( tabulate.tabulate(author_match,headers='keys', tablefmt='psql'))
                    ai=input('Give Number of line:')
                    author_Series=author_match.ix[ai]
                Group=input('Group name for\n%s\n(Example: IA: Inteligencia Artificial)' %author_Series.Full_Name)
                #DEBUG: if not file creates it
                iffile=False
                if not iffile:
                    self.institution_group=pd.DataFrame()  
                    self.institution_group=self.institution_group.append({self.columns.Full_Name:author_Series.Full_Name,\
                                                                  self.columns.Institution_Group:Group},ignore_index=True)
                    self.institution_group.to_csv('groups.csv',index=False)
        else:
            warnings.warn(wrn)

        
        
    def get_doi(self,surname='Florez',\
                     title=r'Baryonic violation of R-parity from anomalous $U(1)_H$',other=''):
        return _get_doi(surname='Florez',\
                        title=r'Baryonic violation of R-parity from anomalous $U(1)_H$',other='')
    
    def get_IF(self,journal_name='Physical Review D'):
        return _get_impact_factor_from_journal_name(journal_name='Physical Review D')
    
    def get_citations(self,user='-6mndWkAAAAJ',number_of_articles=100,sleep=10):
        self.Citations_indices,self.cited_articles=_gs_profile_to_dataframes(\
                        user=user,number_of_articles=number_of_articles,sleep=sleep)
        if self.cited_articles.shape[0]>0:
            self.cited_articles_hash=\
                    self.cited_articles.Article.str.replace(r"[^a-zA-Z0-9 ]", " ").str.lower().str.replace('\s+','')
            self.articles_hash=\
                    self.articles.Title.str.replace(r"[^a-zA-Z0-9 ]", " ").str.lower().str.replace('\s+','')
            
        return self.Citations_indices,self.cited_articles

    def article_index_cites(self,index=0): 
        if self.cited_articles_hash.shape[0]>0:
            mt=self.cited_articles[self.cited_articles_hash.str.match(self.articles_hash[index])]
            if len(mt)>0:
                if len(mt)>1: #multiple matches. Refine search with, e.g, volume
                    mtv=mt[mt.thash.str.contains(str(self.articles.Volume[index]))]
                    if len(mtv)>0:
                        mt=mtv
        
                return mt.Cites.replace('*','').replace('','0').astype(int).max()
        else:
            return ''
    
    def articles_update(self,cites=True,institution_authors=False,institution_groups=False,DOI=False,\
                        impact_factor=False):
        self.fulldoi=pd.DataFrame()
        journal_columns=['Impact_Factor','Quartil','Journal_Hindex']
        newcolumns=['Institution_Authors','Institution_Groups','DOI','ISSN','DOI_Journal','Cites']+journal_columns
        for newcolumn in newcolumns:
            if not newcolumn in self.articles.columns:
                self.articles[newcolumn]=''

        self.articles=self.articles.reset_index(drop=True).fillna('')
        print('Updating entry:',end="")
        dbj=pd.DataFrame()
        for i in range(self.articles.shape[0]):
            time.sleep(0.3) #avoid robot detection
            print('%d.' %i,end="")
            #Update Full names: TODO: Unify algorithm
            if not self.articles.ix[i].Institution_Authors:
                institution_authors=True
                
            if self.articles.ix[i].Authors and institution_authors:
                inst_auth=''
                inst_auth_sep=';'
                for a in filter(None, self.articles.ix[0].Authors.replace('; ',';').split(';') ):
                    af=self.institution_authors[self.institution_authors.Author_Names.str.contains(a)].reset_index(drop=True)
                    if af.shape[0]==1:
                        if inst_auth:
                            inst_auth=inst_auth+inst_auth_sep
                        if af.Full_Name.values.shape[0]==1:
                            inst_auth=inst_auth+af.Full_Name.values[0]
                    elif af.shape[0]>1:
                        print('Improve real name matching')
                    if update_column(self.articles.ix[i],'Institution_Authors'):
                        self.articles.loc[i,'Institution_Authors']=inst_auth
            #Update Groups:
            if not self.articles.ix[i].Institution_Groups:
                institution_groups=True
            if self.articles.ix[i].Institution_Authors and institution_groups:
                inst_grp=''
                inst_grp_sep=';'
                chka=self.articles.ix[i].Institution_Authors.split(';')
                if len(chka)>0:
                    for fa in chka:
                        qry=self.institution_group[self.institution_group.Full_Name.str.contains(fa)].reset_index(drop=True)
                        if qry.shape[0]==1:
                            g=qry.Institution_Group.values[0]
                        else:
                            print('DEBUG improve search group for %s' %fa)
                        if inst_grp:
                            inst_grp=inst_grp+inst_grp_sep
                        
                        inst_grp=inst_grp+g
                    
                if update_column(self.articles.ix[i],'Institution_Groups'):
                        self.articles.loc[i,'Institution_Groups']=inst_grp
                    
                
            #Update DOI:
            if not self.articles.ix[i].DOI:
                rr=_get_doi(surname=self.articles.ix[i].Authors.split(';')[0].split(',')[0],\
                            title=self.articles.ix[i].Title)
                if len(rr)>0:
                    rr=pd.Series(rr)
                    if update_column(self.articles.ix[i],'DOI') and 'URL' in rr:
                        self.articles.loc[i,'DOI']=rr['URL']
                    if update_column(self.articles.ix[i],'ISSN') and 'ISSN' in rr:
                        issn=''
                        if type(rr.ISSN)==list:
                            issn=';'.join(rr.ISSN)
                        else:
                            print('DEBUG: Improve DOI -> ISSN not a list')
                        self.articles.loc[i,'ISSN']=issn
                    if update_column(self.articles.ix[i],'DOI_Journal') and 'container-title' in rr:                        
                        journal=[ j for j in rr['container-title'] if j.find('.')<0] 
                        if len(journal)==1:
                            self.articles.loc[i,'DOI_Journal']=journal[0]
                        else:
                            print('DEBUG: Improve DOI_journal have dots')
                        
                        
                self.fulldoi=self.fulldoi.append(rr,ignore_index=True).fillna('')
            #Update Cites:
            if not self.articles.ix[i].Cites:
                if update_column(self.articles.ix[i],'Cites') and self.cited_articles_hash.shape[0]>0:
                        #DEBUG implement method like here with self.article_index_cites
                        self.articles.loc[i,'Cites']=self.article_index_cites(i)
                    
            
            #WARNING: Only specific journal info related code from here: See the continue !!!!
            #JOURNAL info:
            if i>0 and 'ISSN' in self.articles:
                dbj=self.articles[:i][self.articles[:i].ISSN.str.contains(\
                              self.articles.ISSN.ix[i].split(';')[0])].reset_index(drop=True)
            
            if dbj.shape[0]>0:
                for k in journal_columns:
                    if k in self.articles:
                        self.articles.loc[i,k]=dbj.ix[0][k]
                continue   
            
            #Update IF
            q=''
            if self.articles.ix[i].DOI_Journal:
                q=self.articles.ix[i].DOI_Journal.lower().replace(' ','-')
            elif self.articles.ix[i].Publication:
                q=self.articles.ix[i].Publication
            IFdf=_get_impact_factor_from_journal_name(q)
            if IFdf.shape[0]>0:
                if update_column(self.articles.ix[i],'Impact_Factor') and 'IF' in IFdf:
                    self.articles.loc[i,'Impact_Factor']=eval(IFdf.ix[0].IF)
            
            #Update quartil
            if self.articles.ix[i].ISSN.split(';')[0]:
                quartil,hindex_journal=_get_quartil(self.articles.ix[i].ISSN.split(';')[0],journal_hindex=True)
                if update_column(self.articles.ix[i],'Quartil') and  quartil:
                        self.articles.loc[i,'Quartil']=quartil
                if update_column(self.articles.ix[i],'Journal_Hindex') and hindex_journal:
                        self.articles.loc[i,'Journal_Hindex']=hindex_journal                    
            
        return self.fulldoi.fillna('')

    def to_csv(self,csvfile):
        self.articles.to_csv(csvfile,index=False)
        if self.fulldoi.shape[0]>0:
            self.fulldoi.to_json('fulldoi.json')
        
                        
            