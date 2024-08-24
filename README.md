This is a streamlit app with pgsql backend i'm developing for choosing best stocks to invest in 
Currently:
    - it's able to download ~75 NASDAQ 100 stocks ( with yahoofinance ) 
    - calculate some metrics ( RSI, MACD, 2 custom metrics of mine )
    - display some charts to the user 

TO DO:
    - performance chart / gains vurves ( in progress ) 
        - to do: signum average gains curve 
        - to do: signum average gains curve integral for few points in time ( 3,5,15,30,45,60,90)
    - backtesting 
    - wrap downloads in airflow jobs 
    
![image](https://github.com/user-attachments/assets/93e95f43-6aab-471c-b7b5-cacb67185652)

![image](https://github.com/user-attachments/assets/70f2aa1c-e926-4d65-94af-69ee872e7e9a)

![image](https://github.com/user-attachments/assets/54cbbe70-7ef8-4eba-a310-b26be77485c5)


gains curves v1 
![image](https://github.com/user-attachments/assets/86988c1e-2733-485f-8e8f-b246b458bca4)

