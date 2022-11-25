import networkx as net
import matplotlib.pyplot as plt
import requests
import time
import warnings
from decouple import config
from tabulate import tabulate
warnings.filterwarnings("ignore")

BEARER_TOKEN = config('BEARER_TOKEN')
USERNAME = config('USERNAME')

def get_user_id(USERNAME):
    url = 'https://api.twitter.com/2/users/by/username/'+USERNAME
    headers = {"Authorization": "Bearer "+BEARER_TOKEN}
    res = requests.get(url=url, headers=headers).json()
    if ('data' in res and 'errors' not in res):
        return res['data']['id']
    elif ('status' in res and res['status'] == 429):
        return 'TooManyRequests'
    else:
        return 'InvalidUsername'

def get_followers(USERID):
    url = 'https://api.twitter.com/2/users/'+USERID+'/followers'
    headers = {"Authorization": "Bearer "+BEARER_TOKEN}
    res = requests.get(url=url, headers=headers).json()
    if ('data' in res and 'errors' not in res):
        return res['data']
    elif ('status' in res and res['status'] == 429):
        return 'TooManyRequests'
    elif ('errors' in res and 'title' in res['errors'][0] and res['errors'][0]['title'] == 'Authorization Error'):
        return 'UnAuthRequest'
    else:
        return 'UnSucessRequest'

def retrieve_followers():
    f = open('edges.txt', 'w')
    USERID = get_user_id(USERNAME)
    while (USERID == 'TooManyRequests'):
        time.sleep(60)
        USERID = get_followers(USERNAME)
    followers = get_followers(USERID)
    while (followers == 'TooManyRequests'):
        time.sleep(60)
        followers = get_followers(USERID)

    for follower in followers:
        f.write(USERNAME+' - '+follower['username']+'\n')
        fo_followers = get_followers(follower['id'])
        while (fo_followers == 'TooManyRequests'):
            time.sleep(60)
            print('Retrying')
            fo_followers = get_followers(follower['id'])
        if (type(fo_followers) is str):
            print(fo_followers)
            continue
        for fo_follower in fo_followers:
            f.write(follower['username']+' - '+fo_follower['username']+'\n')
    f.close()

def create_graph():
    f = open('edges.txt', 'r')
    edges = f.readlines()
    g = net.Graph()
    for e in edges:
        [e1, e2] = e.split('-')
        e1 = e1[:-1]
        e2 = e2[1:-1]
        g.add_edge(e1, e2)
    f.close()
    return g

def draw_graph(g):
    pos = net.spring_layout(g)
    bc = net.betweenness_centrality(g, normalized=True, endpoints=True)
    node_color = [10000 * g.degree(v) for v in g]
    node_size =  [10000 * v for v in bc.values()]
    plt.figure(figsize=(20,20))
    net.draw_networkx(g, pos=pos, with_labels=False, node_color=node_color, node_size=node_size)
    plt.savefig("network.png")

def network_info(g):
    bc = net.betweenness_centrality(g, normalized=True, endpoints=True)
    cc = net.closeness_centrality(g)
    dc = net.degree_centrality(g)    
    ec = net.eigenvector_centrality(g, max_iter=100, tol=1e-06, nstart=None, weight=None)
    
    bcl = [[k,v] for k, v in sorted(bc.items(), key=lambda item: item[1], reverse=True)]
    popular = []
    for i in range(10):
        popular.append(bcl[i][0])

    table = [['Username', 'Betweenness Centrality', 'Closeness Centrality', 'Degree Centrality', 'Eigenvector Centrality']]
    for n in popular:
        table.append([n, '{:.5f}'.format(bc[n]), '{:.5f}'.format(cc[n]), '{:.5f}'.format(dc[n]), '{:.5f}'.format(ec[n])])
    print(tabulate(table, headers='firstrow', tablefmt='fancy_grid'))

def main():
    # retrieve_followers()
    g = create_graph()
    # draw_graph(g)
    network_info(g)

main()