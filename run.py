from flask import Flask, render_template
import random, sqlalchemy

app = Flask(__name__)

engine = sqlalchemy.create_engine('mysql+pymysql://root:@127.0.0.1/gamerecommend?charset=utf8mb4')

with open('./data/steam_user_id.txt', 'r') as f:
    lst_user_id = [i.rstrip('\n') for i in f.readlines() if not i.isspace()]

lst_popularity_based_recommendations = []
for app_id in [i[0] for i in engine.execute(\
        "SELECT steam_appid FROM tbl_results_popularity_based_jm LIMIT 5").fetchall()]:
    app_data = engine.execute("SELECT steam_appid, name, price, `header image` FROM tbl_app_info_jm WHERE steam_appid = {};"\
                              .format(app_id)).first()
    if app_data != None:
        lst_popularity_based_recommendations.append(app_data)

def ResultsData(favorite_app_id, tbl_results):
    lst_results = []
    engine = sqlalchemy.create_engine('mysql+pymysql://root:@127.0.0.1/gamerecommend?charset=utf8mb4')
    try:
        for appid in list(engine.execute("SELECT `0`,`1`,`2`,`3`,`4` from {} "
                                         "WHERE steam_appid = {};".format(tbl_results, favorite_app_id)).first()):
            app_data = engine.execute("SELECT steam_appid, name, price, `header image` FROM tbl_app_info_jm "
                                      "WHERE steam_appid = {};".format(appid)).first()
            if app_data != None:
                lst_results.append(app_data)
    except:
        lst_results = None
    return lst_results

@app.route('/')
def recommender():
    userid = random.choice(lst_user_id)
    #userid = 76561198200359959 # has everything
    #userid = 76561197960323774 # no purchase info
    #userid = 76561198080145886 # no favorite_app_data, has favorite_app_id
    favorite_app_id = engine.execute("SELECT `0` FROM tbl_user_favorite_app_jm "
                                     "WHERE steam_user_id = {};".format(userid)).first()[0]
    try:
        favorite_app_id = int(favorite_app_id)
        favorite_app_data = engine.execute("SELECT name, price, `header image` FROM tbl_app_info_jm "
                                       "WHERE steam_appid = {};".format(favorite_app_id)).first()
        if favorite_app_data == None or list(favorite_app_data)[0] == None:
            favorite_app_data = None
            lst_content_based_recommendations = None
            lst_item_based_recommendations = None
            lst_als_based_recommendations = None


        else:
            lst_als_based_recommendations = []
            for app_id in list(engine.execute("SELECT `0`,`1`,`2`,`3`,`4` FROM tbl_results_als_based_jm "
                                              "WHERE steam_user_id = {};".format(userid)).first()):
                app_data = engine.execute("SELECT steam_appid, name, price, `header image` FROM tbl_app_info_jm "
                                          "WHERE steam_appid = {};".format(app_id)).first()
                if app_data != None:
                    lst_als_based_recommendations.append(app_data)

            lst_content_based_recommendations = ResultsData(favorite_app_id, 'tbl_results_content_based_jm')
            lst_item_based_recommendations = ResultsData(favorite_app_id, 'tbl_results_item_based_jm')

    except:
        favorite_app_data = None
        lst_content_based_recommendations = None
        lst_item_based_recommendations = None
        lst_als_based_recommendations = None

    return render_template('recommendation.html',
                           userid=userid,
                           favorite_app_data=favorite_app_data,
                           lst_content_based_recommended_games=lst_content_based_recommendations,
                           lst_item_based_recommended_games=lst_item_based_recommendations,
                           lst_als_recommended_games=lst_als_based_recommendations,
                           lst_popularity_based_recommended_games=lst_popularity_based_recommendations)

if __name__ == '__main__':
    app.run(debug=True)
