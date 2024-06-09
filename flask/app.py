from flask import Flask, render_template
import json 
# add dir above to paht 
import sys
sys.path.insert(0, '..')

from calcview import calcview
app = Flask(__name__)



@app.route('/')
def home():
    ticker='AAPL'
    
    links=['AAPL']
    return render_template('home.html', ticker=ticker,dropdown_stats=dropdown_stats,links=links)


@app.route('/AAPL')
def test():
    #labels = ["January", "February", "March", "April", "May", "June", "July"]
    #data = [10, 20, 30, 40, 50, 60, 70]
    cv=calcview('AAPL')
    cv.get_data(limit=50)
    labels=cv.df['TS'].tolist()
    _labels=json.dumps(list(map(str,labels)))
    _data=json.dumps(cv.df['CLOSE'].tolist())
    _chartLabel=json.dumps('AAPL price action')
    
    dropdown_stats=['foo','bar','kez']
    return render_template('chartjs.html', labels=_labels, data=_data,chartLabel=_chartLabel,dropdown_stats=dropdown_stats)

    


if __name__ == '__main__':
    app.run(debug=True)