from flask import Flask, render_template,request,jsonify
import json 
import random 
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


    
@app.route('/AAPL', methods=['GET'])
def test():    
    cv=calcview('AAPL')
    cv.get_data()
    
    labels=cv.df['TS'].tolist()
    _labels=json.dumps(list(map(str,labels)))
    

    _data=json.dumps(cv.df['CLOSE'].tolist())

    

    #_labels = ["January", "February", "March", "April", "May", "June", "July"]
    #_data = [random.randint(0, 100) for _ in range(7)]
    return render_template('chartjs.html'
                           , labels=_labels
                           , data=_data
                           ,chartLabel=json.dumps('AAPL price action')
                           ,dropdown_stats=['foo','bar','kez']
                           ,start_date='2024-01-01'
                           ,end_date='2024-06-06'
                           )


@app.route('/recalculate', methods=['POST'])
def update_chart():
    # get data from frontent 
    data = request.get_json()
    _start_date = data['start_date']
    _end_date = data['end_date']

    # get data from db even though we did it already :( 
    cv=calcview('AAPL')
    cv.get_data()
    
    # filter the data 
    filtered_df=cv.df[(cv.df['TS']>=_start_date) & (cv.df['TS']<=_end_date)]
    labels=filtered_df['TS'].tolist()
    _labels = list(map(str, labels))
    
    _data = filtered_df['CLOSE'].tolist()


    print(_start_date,_end_date,filtered_df.shape)
    return jsonify({
        'labels': _labels,
        'data': _data,
        'chartLabel': 'AAPL price action'
    })
    


if __name__ == '__main__':
    app.run(debug=True)