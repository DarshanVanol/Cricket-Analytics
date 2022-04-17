
import pandas as pd


player=pd.read_csv("Players.csv")
player=pd.DataFrame(player)
player["Player_Name"]="\""+player["Player_Name"]+"\","
print(player["Player_Name"])
filename = 'players.pkl'
pickle.dump(player["Player_Name"], open(filename, 'wb'))