from django.shortcuts import render_to_response, redirect, render
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.template.context import RequestContext
import requests
from django.http import HttpResponse
import tweepy
from tweepy import OAuthHandler
import json
from google import search
import textrazor
import re
from collections import defaultdict
import urllib
import mechanize
import re
from bs4 import BeautifulSoup
from lxml import html

entities_dictionary = defaultdict(list)
score = {}



def login(request):
    # context = RequestContext(request, {
    #     'request': request, 'user': request.user})
    # return render_to_response('login.html', context_instance=context)
    return render(request, 'login.html')


@login_required(login_url='/')
def home(request):
     
    consumer_key = 'RmYhC39yrTsRahPrxpbTNIk9m'
    consumer_secret = 'SEjo3pHKsuK6jnXuLoOfX7cZMbRMAzRlfiiRs4anWirhYbnGbU'

    social = request.user.social_auth.get(provider='twitter')
    access_token = social.extra_data['access_token'].get('oauth_token')
    access_secret = social.extra_data['access_token'].get('oauth_token_secret')
    
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_secret)
 
    api = tweepy.API(auth)
    alltweets = ""
    public_tweets = api.home_timeline(count=500)
    print "tweet"
    for tweet in public_tweets:
        alltweets+=tweet.text
    user_tweets = api.user_timeline(count=100) 
    print "tweeeeeeet"   
    for tweet in user_tweets:
        alltweets+=tweet.text
    
    process_or_store(alltweets)
    
    return render(request,'home.html')


def logout(request):
    auth_logout(request)
    return redirect('/')

def process_or_store(alltweets):
    textrazor.api_key = "813c3fc408c749a28006cca97f5865dca86c569f77ed08728b151bc0"
    client = textrazor.TextRazor(extractors=["entities", "topics"])
    #client.set_cleanup_mode("stripTags")
    alltweets = re.sub(r"(?:\@|https?\://)\S+", "", alltweets)
    client.set_classifiers(["textrazor_iab"])
    response = client.analyze(alltweets)
    print "##############################################################################################"
    

    
    print "\n\n\nEntities"
    for entity in response.entities():    
        
        if entity.confidence_score > 0.7: 
            
            if entity.dbpedia_types: 
            
                for e in entity.dbpedia_types:
                    if entity.id not in entities_dictionary[e]:
                        entities_dictionary[e].append(entity.id)
                    if entity.id in score:
                        score[entity.id]+= 1
                    else:
                        score[entity.id] = 1


    #print entities_dictionary
    
    topics=""
    
    for topic in response.topics():
        topics+= topic.label + "\n"
    
    print "\n\nAfter Topics"
    
    #for category in response.categories():
     #   print category.category_id, category.label, category.score

    response = client.analyze(topics)
    
    for entity in response.entities():  
        if entity.confidence_score > 0.7: 
            
            if entity.dbpedia_types: 
            
                for e in entity.dbpedia_types:
                    if entity.id not in entities_dictionary[e]:
                        entities_dictionary[e].append(entity.id)
                        score[entity.id] = 1
                                              

    print entities_dictionary
    print score  
        
    
    

def results(request):
    if 'search_string' in request.GET:
        search_string = request.GET['search_string']
    #context = locals()
    together = []
    appends=[value for key, value in entities_dictionary.items() if search_string == key.lower()]
    myscores={}
    sorted_appends=[]
    if appends:
        
        print appends[0]
        for e in appends[0]:
            myscores[e] = score[e]

        print myscores

        sorted_appends = [key for key, value in sorted(myscores.iteritems(), key=lambda (k,v): (v,k), reverse=True)]
        print sorted_appends    

        for e in sorted_appends:
            print "in for="
            print search_string +" " + e
            r = google_search(search_string + " " + e)
            r1=[]
            if r[0][2]:
                r1.append(r[0])
            if r[1][2]:
                r1.append(r[1])
            if r[2][2]:
                r1.append(r[2])
            together.append(r1)

        print together
        #context['var1'] = "hello"
    else:
            together = google_search(search_string)
            print together
            return render(request, 'results1.html', {'together':together})
    #return render(request,'results.html')
    return render(request, 'results.html', {'together':together})
    #return render_to_response('results.html', context, context_instance=RequestContext(request))



def google_search(term):
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.set_handle_referer(False)
    br.set_handle_refresh(False)
    br.addheaders= [('User-agent','mychrome')]

    term=term.replace(" ", "+")
    #query="http://www.google.com/search?num=100&site=&source=hp&q="+term+"&oq="+term

    query="http://www.google.com/search?num=5&q=" + term 

    htmltext=br.open(query).read()

    soup=BeautifulSoup(htmltext,"lxml")

    search= soup.findAll('div',attrs={'id':'search'})

    searchtext=str(search[0])

    soup1=BeautifulSoup(searchtext,"lxml")
    list_items=soup1.findAll('div', attrs={'class':'g'})

    results=[]

    for div in list_items:
        soup2= BeautifulSoup(str(div),"lxml")
        links = soup2.find('cite')
        mylink = re.sub('<[^>]*>', '', str(links))
        
        if mylink is None: 
            print "none"
            continue
        else:
            desc_items=soup2.find('span',attrs={'class':'st'})
            mydesc = re.sub('<[^>]*>', '', str(desc_items))
            title= soup2.find('h3',attrs={'class':'r'})
            mytitle= re.sub('<[^>]*>', '', str(title))
            val1 = mylink.startswith('http')
            val2 = mylink.startswith('https')

            if not val1 and  not val2:
                #print val1
                #print val2
                #print "both false"
                mylink = "http://"+mylink    
            #print "title= " 
            #print mytitle
            #print str(mydesc)
            row=[]
            row.append(str(mylink))
            row.append(str(mytitle))
            row.append(mydesc)
            #row[1].encode('utf-8')
            results.append(row)
    return results
        