from bs4 import BeautifulSoup
import networkx as nx
import json
from urllib.request import urlopen
from datetime import datetime
import time
import pandas as pd
import numpy as np


class TweetJob:
    def __init__(self):
        self.twitter_handle = None
        self.follower_limit = 1
        self.following_limit = 1
        self.job_name = None
        self.json_name = None
        self.edges_name = None
        self.vertices_name = None
        self.followers = None
        self.profile = None
        self.dt = datetime.now().strftime('%H%M%S')  # add seconds
        self.followers_list = []
        self.following_list = []
        self.profile_html = None
        self.followers_html = None
        self.following_html = None
        self.following_bs = None
        self.profile_bs = None
        self.follower_bs = None
        self.following_start_page = None
        self.follower_start_page = None
        self.followers_to_crawl = 5
        self.followers_crawl_limit = 20
        self.sleep= 1
        self.graph_name = None

    def initial_information_input(self):
        self.twitter_handle = input('Enter twitter handle and press enter     ')
        followers_to_scrape = int(input('How many followers to collect?     '))
        following_to_scrape = int(input('How many accounts following to collect?     '))
        self.followers_to_crawl = int(input('How many of account 0 followers do you want to also scrape?     '))
        self.followers_crawl_limit = int(input('And how many of their followers to record?'))
        self.follower_limit = followers_to_scrape / 20
        self.following_limit = following_to_scrape / 20
        self.profile = 'https://mobile.twitter.com/'+str(self.twitter_handle)
        self.following_start_page = str(self.profile)+'/following'
        self.follower_start_page = str(self.profile)+'/followers'
        self.job_name = self.twitter_handle+"_"+self.dt
        self.json_name = self.job_name + '.json'
        self.edges_name = self.job_name + '_edges.csv'
        self.vertices_name = self.job_name + '_vertices.csv'
        self.graph_name = self.job_name + '.gexf'

    def load_initial_pages(self):
        self.profile_html = urlopen(self.profile).read()
        self.followers_html = urlopen(self.following_start_page).read()
        self.following_html = urlopen(self.following_start_page).read()
        self.following_bs = BeautifulSoup(self.following_html, 'html.parser')
        self.profile_bs = BeautifulSoup(self.profile_html, 'html.parser')
        self.follower_bs = BeautifulSoup(self.followers_html, 'html.parser')

    def get_user_info(self, bs):
        full_name = bs.find('div', {'class': 'fullname'}).get_text().strip()
        username = bs.find('span', {'class': 'screen-name'}).get_text().strip()
        username = '@'+username
        location = bs.find('div', {'class': 'location'}).get_text().strip()
        bio = bs.find('div', {'class': 'dir-ltr'}).get_text().strip()
        url = bs.find('div', {'class': 'url'}).get_text().strip()
        tweets = bs.findAll('div', {'class': 'statnum'})[0].get_text().replace(',', '')
        following = bs.findAll('div', {'class': 'statnum'})[1].get_text().replace(',', '')
        followers = bs.findAll('div', {'class': 'statnum'})[2].get_text().replace(',', '')
        date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return([full_name, username, location, bio, url, tweets, following, followers, date_time])

    def get_following(self, bs_object):
        following = []
        namelist = bs_object.findAll('span' , {'class': 'username'})
        for name in namelist:
            following.append(name.get_text())
        following = following[1:]
        return(following)

    def get_followers(self, bs_object):
        self.followers = []
        nameList = bs_object.findAll('span',{'class': 'username'})
        for name in nameList:
            self.followers.append(name.get_text())
        self.followers = self.followers[1:]

    def get_next_page(self, bs):
        next_div = bs.find('div', attrs={'class' : 'w-button-more'})
        try:
            next_page = next_div.a['href']
            return(next_page)
        except AttributeError:
            return("END")

    def following_scraping_process(self, page, limit):
        whole_following_list = []
        while limit >0:
            time.sleep(self.sleep)
            print(str(limit)+" pages remaining")
            following_html = urlopen(page).read()
            following_bs = BeautifulSoup(following_html, 'html.parser')
            page_following = self.get_following(following_bs)
            whole_following_list += page_following
            page = self.get_next_page(following_bs)
            print('page crawled, moving to next page...')
            print('next page is: '+str(page))

            if page =='END':
                limit = 0
            else:
                page = 'https://mobile.twitter.com'+str(page)
                limit -=1
        self.following_list = whole_following_list

    def followers_scraping_process(self, page, limit):
        whole_followers_list = []
        while limit >0:
            time.sleep(self.sleep)
            print(str(limit)+" pages remaining")
            followers_html = urlopen(page).read()
            followers_bs = BeautifulSoup(followers_html, 'html.parser')
            page_followers = self.get_following(followers_bs)
            whole_followers_list += page_followers
            page = self.get_next_page(followers_bs)
            print('page crawled, moving to next page...')
            print('next page is: '+str(page))

            if page =='END':
                limit = 0
            else:
                page = 'https://mobile.twitter.com'+str(page)
                limit -=1
        self.followers_list = whole_followers_list

    def compile_data(self, profile_data ):
        follower_list = self.followers_list
        following_list = self.following_list
        self.user_info = {
        'full_name':profile_data[0],
        'username': profile_data[1],
        'twitter_user_url': self.profile,
        'location': profile_data[2],
        'bio':profile_data[3],
        'bio_url':profile_data[4],
        'tweet_count':profile_data[5],
        'following_count': profile_data[6],
        'follower_count':profile_data[7],
        'following':following_list,
        'followers':follower_list,
        'date_updated': profile_data[8]
        }

    def write_job(self, write_mode):
        head =  None
        if write_mode == 'a':
            head = False
            user = self.twitter_handle
        if write_mode == 'w':
            head = True
            user = '@'+self.twitter_handle


        with open(self.json_name, write_mode) as outfile:
            json.dump(self.user_info, outfile)

        print('Job written to '+str(self.json_name))

        v = self.followers_list+self.following_list
        v.append(user)
        v=pd.DataFrame(v, columns=['vertices'])
        v = v.replace({'@@':'@'})

        e=pd.DataFrame(self.following_list, columns = ['following'])
        e['user']=user
        e=e[['user', 'following']]

        e2=pd.DataFrame(self.followers_list, columns = ['user'])
        e2['following']=user
        edges = e.append(e2)
        edges = edges.replace({'@@':'@'})

        edges.to_csv(self.edges_name, mode=write_mode, header = head)
        v.to_csv(self.vertices_name, mode = write_mode , header = head)


    def opening_sequence(self):
        flag =True
        while flag == True:
            #twitter_handle, follower_pages_to_scrape, following_pages_to_scrape = self.initial_information_input()
            self.initial_information_input()
            print(self.job_name)
            print(self.json_name)
            print(self.edges_name )
            print(self.vertices_name)
            if input(("Is this correct? y/n     "))== "y":
                flag =False
            else:
                print("ok lets try again...")
                flag = True
        print("ok, starting")

    def primary_crawl(self):
        self.load_initial_pages()
        print("initalized, scraping profile 0...")
        profile_data = self.get_user_info(self.profile_bs)
        #self.compile_data(profile_data)

        print('profile 0 scraped, getting followers...')

        self.following_scraping_process(self.following_start_page, self.following_limit)

        print('following scraped, moving to followers...')

        self.followers_scraping_process(self.follower_start_page, self.follower_limit)
        self.compile_data(profile_data)
        print('followers scraped, writing...')
        self.write_job('w')

    def get_new_list(self):
        with open(self.json_name) as f:
            data = json.load(f)

        new_crawl_list = data['following'][:self.followers_to_crawl]
        return(new_crawl_list)

    def secondary_crawl(self, new_list):
        for profile in new_list:
            # reset attributes
            self.followers_list = []
            self.following_list = []
            self.twitter_handle = profile
            self.profile = 'https://mobile.twitter.com/'+str(self.twitter_handle)
            self.following_start_page = str(self.profile)+'/following'
            self.follower_start_page = str(self.profile)+'/followers'
            self.following_limit = self.followers_crawl_limit
            self.followers_limit = self.followers_crawl_limit

            self.load_initial_pages()
            print("initalized, scraping profile 0...")
            profile_data = self.get_user_info(self.profile_bs)

            print('profile 0 scraped, getting followers...')

            self.following_scraping_process(self.following_start_page, self.following_limit)

            print('following scraped, moving to followers...')

            self.followers_scraping_process(self.follower_start_page, self.follower_limit)

            self.compile_data(profile_data)
            print('followers scraped, writing...')
            self.write_job('a')

    def make_graph(self):
        df = pd.read_csv(self.edges_name)
        G = nx.MultiGraph()
        G = nx.from_pandas_edgelist(df, 'user', 'following')
        nx.write_gexf(G, self.graph_name)

    def main(self):

        self.load_initial_pages()
        print('loaded, moving on to primary crawl')

        self.primary_crawl()
        print('Primary complete, moving to secondary')

        n_list = self.get_new_list()
        print(n_list)

        self.secondary_crawl(n_list)
        print('secondary crawl complete')

        self.make_graph()
        print('graph complete')


if __name__ == '__main__':
    tj=TweetJob()
    tj.opening_sequence()
    tj.main()
