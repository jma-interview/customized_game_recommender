import requests, json, os, sys, time, re
from bs4 import BeautifulSoup
from datetime import datetime
from multiprocessing import Pool
from sqlalchemy import *
import pandas as pd
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity
from pyspark.mllib.recommendation import ALS
from pyspark import SparkContext



##### Work Assistance ######

def show_work_status(totalCount, currentCount=0):
    percentage = currentCount / totalCount * 100.0
    status = '>' * int(percentage) + ' ' * (100 - int(percentage))
    sys.stdout.write('\r[{0}] {1:.2f}% '.format(status, percentage))
    sys.stdout.flush()
    if percentage >= 100:
        print('\n')

def split_list(lst_long, n):
    lst_splitted = []
    if len(lst_long) % n == 0:
        totalBatches = int(len(lst_long) / n)
    else:
        totalBatches = int(len(lst_long) / n) + 1
    for i in range(totalBatches):
        lst_short = lst_long[i * n:(i + 1) * n]
        lst_splitted.append(lst_short)
    return lst_splitted

##### Build MySQL Engine ######

engine = create_engine('mysql+pymysql://root:@127.0.0.1/GameRecommend?charset=utf8mb4')
engine.execute('ALTER DATABASE GameRecommend CHARACTER SET = utf8mb4')

###############################################
############ Extract Game Features ############
###############################################


def ParseDetails(RawStrList):
    dic_detail = {'name': {}, 'type': {}, 'header image': {}, 'score': {}, \
                  'recommendations': {}, 'release_date': {}, 'price': {}, 'currency':{}, \
                  'windows': {}, 'linux': {}, 'mac': {}, 'description': {}, \
                  'success': {}}

    for i in RawStrList:
        details = json.loads(i)
        steam_id, data = list(details.items())[0]
        data = data.get('data', {})
        if data == {}:
            dic_detail['success'].update({steam_id: False})
        else:
            game_name = data.get('name')
            dic_detail['name'].update({steam_id: game_name})

            game_type = data.get('type')
            dic_detail['type'].update({steam_id: game_type})

            hd_image = data.get('header_image')
            dic_detail['header image'].update({steam_id: hd_image})

            score = data.get('metacritic', {}).get('score')
            dic_detail['score'].update({steam_id: score})

            recommendations = data.get('recommendations', {}).get('total')
            dic_detail['recommendations'].update({steam_id: recommendations})

            if data.get('release_date', {}).get('coming_soon') == False:
                release_date = data.get('release_date',{}).get('date')
                if not release_date == '':
                    if re.search(',', release_date)== None:
                        release_date = datetime.strptime(release_date, '%b %Y')
                    else:
                        try:
                            release_date = datetime.strptime(release_date, '%b %d, %Y')
                        except:
                            release_date = datetime.strptime(release_date, '%d %b, %Y')
            else:
                 release_date = None
            dic_detail['release_date'].update({steam_id: release_date})

            if data.get('is_free') == True:
                price = 0
            else:
                price = data.get('price_overview', {}).get('initial')
                if price != None:
                    price = float(price)/100
            dic_detail['price'].update({steam_id: price})

            currency = data.get('price_overview', {}).get('currency')
            dic_detail['currency'].update({steam_id: currency})

            for (platforms, is_supported) in data.get('platforms', {}).items():
                if is_supported == True:
                    dic_detail[platforms].update({steam_id: 1})

            about_the_game = data.get('about_the_game', {})
            soup = BeautifulSoup(about_the_game, 'lxml')
            game_description = re.sub(r'(\s+)', ' ', soup.text).strip()
            dic_detail['description'].update({steam_id: game_description})

    return dic_detail


path_game_detail = './data/game_details_jm.txt' #apps' ids are from steamspy
with open(path_game_detail, 'r') as f:
    details_raw = f.readlines()

p = Pool(2)
TotalCount = len(details_raw)
CurrentCount = 0
show_work_status(TotalCount, CurrentCount)

df_game_detail = pd.DataFrame()

start = time.time()
for i in split_list(details_raw, 100):
    batchwork = p.map(ParseDetails, split_list(i, 50))
    for batch in batchwork:
        df_batch = pd.DataFrame(batch)
        df_game_detail = df_game_detail.append(df_batch)

    CurrentCount += len(i)
    show_work_status(TotalCount, CurrentCount)
end = time.time()
print('Time Spent:{} seconds'.format(end-start))

df_game_detail.index.name = 'steam_appid'
df_game_detail.windows.fillna(0, inplace=True)
df_game_detail.linux.fillna(0, inplace=True)
df_game_detail.mac.fillna(0, inplace=True)
df_game_detail.success.fillna(True, inplace=True)
df_game_detail['release_date'] = pd.to_datetime(df_game_detail['release_date'])
df_game_detail = df_game_detail[['name', 'success', 'type', 'release_date', 'price', 'currency',
                                 'header image', 'score', 'recommendations',
                                 'windows', 'linux', 'mac', 'description']]
df_game_detail.reset_index(inplace=True)
df_game_detail.to_sql('tbl_app_info_jm', engine, if_exists='replace', index=False)

###############################################
######### Most Played Games Per User ##########
###############################################

dic_user_favorite_app = {}
path_user_gamedata = './data/user_gamedata_jm.txt'
with open(path_user_gamedata, 'r') as f:
    for raw_string in f.readlines():
        user_id, lst_inventory = list(json.loads(raw_string).items())[0]
        if lst_inventory != None and lst_inventory != []:
            most_played_app_id = sorted(lst_inventory, key=lambda k: k['playtime_forever'])[-1].get('appid')
        else:
            most_played_app_id = None
        dic_user_favorite_app.update({user_id: most_played_app_id})
df_user_favorite_app = pd.Series(dic_user_favorite_app).to_frame().reset_index()
df_user_favorite_app.columns = ['steam_user_id', '0']
df_user_favorite_app.to_sql('tbl_user_favorite_app_jm', engine, if_exists='replace', index=False)



################################################
######### Build Recommendation Models ##########
################################################


df_steam_app = pd.read_sql('tbl_app_info_jm', engine) #export sql table as dataframe
df_valid_games = df_steam_app.query('success == True and type == "game" and release_date <= "{}" and price >= 0'.format(datetime.today().date()))
set_valid_game_id = set(df_valid_games.steam_appid)


######## Model1: Popularity Based ########################
print('Popularity Based Model')
start = time.time()

path_app_stats = './data/steamspy_gameinfo.json'
with open(path_app_stats, 'r') as f:
    dic_steamspy_raw = json.load(f)

lst_steamspy = list(dic_steamspy_raw.values())
dic_steamspy = {}

for steamspy in lst_steamspy:
    owner_count = steamspy.get('owners',{})
    appid = str(steamspy.get('appid'))
    dic_steamspy.update({appid: owner_count})

df_popularity_based_results = pd.Series(dic_steamspy).sort_values(ascending=False).to_frame()
df_popularity_based_results.index.name = 'steam_appid'
df_popularity_based_results.reset_index(inplace=True)
df_popularity_based_results.to_sql('tbl_results_popularity_based_jm', engine, if_exists='replace')

end = time.time()
print('Popularity Based Model Spent: {} seconds'.format(end-start))

######## Model 2: Content Based - Description ############
print('Content Based Model')
start = time.time()

tfidf = TfidfVectorizer(strip_accents='unicode',stop_words='english').fit_transform(list(df_valid_games['description']))
lst_app_id = list(df_valid_games.steam_appid)
dic_recommended = {}
total_count = len(lst_app_id)
current_count = 0
for index in range(tfidf.shape[0]):
    cosine_similarities = linear_kernel(tfidf[index:index+1], tfidf).flatten()
    related_docs_indices = cosine_similarities.argsort()[-1:-21:-1]  #from the second largest to the 22nd largest, descend order
    dic_recommended.update({lst_app_id[index]:[lst_app_id[i] for i in related_docs_indices]})

    current_count += 1
    show_work_status(total_count, current_count)

df_content_based_results = pd.DataFrame(dic_recommended).T #transpose index and columns
df_content_based_results.index.name = 'steam_appid'
df_content_based_results.reset_index(inplace=True)
df_content_based_results.to_sql('tbl_results_content_based_jm', engine, if_exists='replace')

end = time.time()
print('Content Based Model Spent: {} seconds'.format(end-start))

########## Model 3: Item Based ############################
print('Item Based Model')
start = time.time()

dic_purchase = {}
with open(path_user_gamedata, 'r') as f:
    gamedata = f.readlines()

total_count = len(gamedata)
current_count = 0

for i in gamedata:
    user_id, user_inventory = list(json.loads(i).items())[0]
    if user_inventory != [] and user_inventory != {} and user_inventory != None:
        dic_purchase[user_id] = {}
        for playtime_info in user_inventory:
            appid = playtime_info.get('appid')
            if str(appid) in set_valid_game_id:
                dic_purchase[user_id].update({appid: 1})

    current_count += 1
    show_work_status(total_count, current_count)

df_purchase = pd.DataFrame(dic_purchase).fillna(0)
purchase_matrix = df_purchase.values #matrix array: [[1,0,1...],[0,0,1...],...[1,1,0...]]
lst_user_id = df_purchase.columns
lst_app_id = df_purchase.index

total_count = purchase_matrix.shape[0]
current_count = 0

dic_recommended_item_based = {}
for index in range(total_count):
    cosine_similarities = linear_kernel(purchase_matrix[index:index+1], purchase_matrix).flatten() #measure whether two apps have similar sets of users
    lst_related_app = np.argsort(-cosine_similarities)[1:101]
    dic_recommended_item_based.update({lst_app_id[index]: [lst_app_id[i] for i in lst_related_app]})
    current_count += 1
    show_work_status(total_count, current_count)


df_item_based_result = pd.DataFrame(dic_recommended_item_based).T
df_item_based_result.index.name = 'steam_appid'
df_item_based_result.reset_index(inplace=True)
df_item_based_result.to_sql('tbl_results_item_based_jm', engine, if_exists='replace')

end = time.time()
print('Item Based Model Spent: {} seconds'.format(end-start))


########## Model 4: Collaborative Filtering ############################
# NOTE: This model requires PySpark
print('ALS Model')
start = time.time()

sc = SparkContext()

def parse_raw_string(raw_string):
    user_inventory = json.loads(raw_string)
    return list(user_inventory.items())[0]

def id_index(x):
    ((user_id, lst_inventory), index) = x
    return (index, user_id)

def create_tuple(x):
    ((user_id, lst_inventory), index) = x
    if lst_inventory != None:
        return (index, [(i.get('appid'), 1) for i in lst_inventory if str(i.get('appid')) in set_valid_game_id])
    else:
        return (index, [])

def reshape(x):
    (index, (appid, time)) = x
    return (index, appid, 1)

user_inventory_rdd = sc.textFile(path_user_gamedata).map(parse_raw_string).zipWithIndex()
dic_id_index = user_inventory_rdd.map(id_index).collectAsMap()
# training_rdd = user_inventory_rdd.map(create_tuple).flatMapValues(lambda x: x).map(\
                                                            # lambda (index, (appid,time)):(index,appid,time))
training_rdd = user_inventory_rdd.map(create_tuple).flatMapValues(lambda x: x).map(reshape)
model = ALS.train(training_rdd, 5)

dic_recommended = {}
for index in list(dic_id_index.keys()):
    try:
        lst_recommended = [i.product for i in model.recommendProducts(index, 10)]
        user_id = dic_id_index.get(index)
        dic_recommended.update({user_id: lst_recommended})
    except:
        pass

df_als_result = pd.DataFrame(dic_recommended).T
df_als_result.index.name = 'steam_user_id'
df_als_result.reset_index(inplace=True)
df_als_result.to_sql('tbl_results_als_based_jm', engine, if_exists='replace', index=False)

end = time.time()
print('ALS Model Spent:{} seconds'.format(end-start))
print('Finished')