# Importing essential libraries
from flask import Flask, render_template, request
import pickle
import numpy as np
import pandas as pd


# Fantasy Points

Batsman_points = {'Run':1, 'bFour':1, 'bSix':2, '30Runs':4,
        'Half_century':8, 'Century':16, 'Duck':-2, '170sr':6,
                 '150sr':4, '130sr':2, '70sr':-2, '60sr':-4, '50sr':-6}

Bowling_points = {'Wicket':25, 'LBW_Bowled':8, '3W':4, '4W':8,
                  '5W':16, 'Maiden':12, '5rpo':6, '6rpo':4, '7rpo':2, '10rpo':-2,
                 '11rpo':-4, '12rpo':-6}

Fielding_points = {'Catch':8, '3Cath':4, 'Stumping':12, 'RunOutD':12,
                  'RunOutInd':6}

# Load the Random Forest CLassifier model
filename = 'first-innings-score-lr-model.pkl'
regressor = pickle.load(open(filename, 'rb'))
filename1 = 'players.pkl'
players=pickle.load(open(filename1, 'rb'))

byb=pd.read_csv('IPL Ball-by-Ball 2008-2020.csv')

app = Flask(__name__)

@app.route('/')
def home():
	return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    team1 = list()
    team2 = list()
    if request.method == 'POST':
        for i in range(1,12):
            team1.append(request.form["player"+str(i)])
            print(team1)
        for i in range(12,23):
            team2.append(request.form["player"+str(i)])
            print(team2)


        t1 = get_players(team1, team2)
        t2 = get_players(team2, team1)
        t3 = t1 + t2


        return render_template('result.html',team1=team1,team2=team2,result=t3[:11])



def get_players(team1, team2):
    fantasy_team_players = []

    for i in range(len(team1)):
        unq_ids = byb[byb["batsman"] == team1[i]]['id'].unique()
        mathces_played = len(unq_ids)
        #         print ( "Number of matches played" , len(unq_ids),team1[i])
        bbr = []
        for x in unq_ids:
            bat_run = sum(byb[(byb["batsman"] == team1[i]) & (byb['id'] == x)]['batsman_runs'])
            bbr.append(bat_run)

        r30, r50, r100 = 0, 0, 0
        for m in bbr:
            if m >= 100:
                r100 += 1
            elif m >= 50:
                r50 += 1
            elif m >= 30:
                r30 += 1
        try:
            catches = len(byb[(byb['fielder'] == team1[i]) & (byb['dismissal_kind'] == 'caught')]) / mathces_played
            run_outs = len(byb[(byb['fielder'] == team1[i]) & (byb['dismissal_kind'] == 'run out')]) / mathces_played
            extra_points = r30 / mathces_played * Batsman_points['30Runs'] + r50 / mathces_played * Batsman_points[
                'Half_century'] + r100 / mathces_played * Batsman_points['Century'] + catches * Fielding_points[
                               'Catch'] + run_outs * Fielding_points['RunOutInd']
        except:
            catches, run_outs, extra_points = 0, 0, 0

        # Extra Points for bowlers to be estimated here
        wickets_taken = []
        for x in unq_ids:
            twx = sum(byb[(byb["bowler"] == team1[i]) & (byb['id'] == x)]['is_wicket'])
            wickets_taken.append(twx)

        w3, w4, w5 = 0, 0, 0
        for z in wickets_taken:
            if z >= 5:
                w5 += 1
            elif z >= 4:
                w4 += 1
            elif z >= 3:
                w3 += 1
        try:
            lbws = len((byb[(byb['bowler'] == team1[i]) & (byb['dismissal_kind'] == 'lbw')])) / mathces_played
            bowled = len((byb[(byb['bowler'] == team1[i]) & (byb['dismissal_kind'] == 'bowled')])) / mathces_played
            wexp = w3 / mathces_played * Bowling_points['3W'] + w4 / mathces_played * Bowling_points[
                '4W'] + w5 / mathces_played * Bowling_points['5W'] + lbws * Bowling_points['LBW_Bowled'] + bowled * \
                   Bowling_points['LBW_Bowled']
        except:
            lbws, bowled, wexp = 0, 0, 0

        ffp = []
        for j in range(len(team2)):
            bat_vs_bowl = byb[(byb["batsman"] == team1[i]) & (byb["bowler"] == team2[j])]
            bowls_played = len(bat_vs_bowl.batsman_runs)
            runs_scored = sum(bat_vs_bowl.batsman_runs)
            fours = len(bat_vs_bowl[bat_vs_bowl['batsman_runs'] == 4])
            sixes = len(bat_vs_bowl[bat_vs_bowl['batsman_runs'] == 6])
            wicket = sum(bat_vs_bowl.is_wicket)
            if bowls_played <= 6 * 10 and wicket >= 5:
                penalty = -16
                print(team1[i], "ka wicket taken", wicket, "times by", team2[j])
            elif bowls_played <= 6 * 8 and wicket >= 4:
                penalty = -8
                print(team1[i], "ka wicket taken", wicket, "times by", team2[j])
            elif bowls_played <= 6 * 6 and wicket >= 3:
                penalty = -4
                print(team1[i], "'s wicket taken", wicket, "times by", team2[j])
            else:
                penalty = 0

            try:
                strike_rate = int(runs_scored / bowls_played * 100)
            except:
                strike_rate = 'NA'
            if bowls_played >= 10 and strike_rate != 'NA':
                if strike_rate >= 170:
                    print(team1[i], "beaten", team2[j], "Runs", runs_scored, "bowls", bowls_played, "strike rate",
                          strike_rate, 'Out', wicket, 'times', "Fours", fours, "Sixes", sixes)
                elif strike_rate >= 150:
                    print(team1[i], "beaten", team2[j], "Runs", runs_scored, "bowls", bowls_played, "strike rate",
                          strike_rate, 'Out', wicket, 'times', "Fours", fours, "Sixes", sixes)

            bowl_vs_bat = byb[(byb["bowler"] == team1[i]) & (byb["batsman"] == team2[j])]
            wicket_took = sum(bowl_vs_bat.is_wicket)
            fantasy_points1 = runs_scored + fours * Batsman_points['bFour'] + sixes * Batsman_points['bSix'] - wicket * \
                              Bowling_points['Wicket'] + wicket_took * Bowling_points['Wicket'] + penalty
            ffp.append(fantasy_points1)
        #             print (team1[i] ,"against", team2[j], "Runs", runs_scored,
        #                    "bowls",bowls_played,"strike rate", strike_rate,
        #                   'Out',wicket,'times', "Fours", fours,"Sixes", sixes, "fatansy points",fantasy_points1)
        sum_ffp = sum(ffp)
        # if team1_fp[team1[i]] > 0:
        #     recent_performace_points = np.log(team1_fp[team1[i]])
        # elif team1_fp[team1[i]] < 0:
        #     recent_performace_points = -np.log(abs(team1_fp[team1[i]]))
        # else:
        #     recent_performace_points = 0
        # Trying a new method for recent performancec point
        # recent_performace_points = team1_fp[team1[i]] / 3
        weight1 = 0.5
        weight2 = 1 - weight1
        final_fantasy_point = (sum_ffp + extra_points + wexp)
                              # * weight1 + recent_performace_points * weight2
        final_fantasy_point = round(final_fantasy_point, 2)
        fantasy_team_players.append((final_fantasy_point, team1[i]))
        fantasy_team_players.sort(reverse=True)
    #         print ("Fatasy points of",team1[i],final_fantasy_point)
    return fantasy_team_players

if __name__ == '__main__':
	app.run(debug=True)