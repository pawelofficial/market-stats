

 
from .statsview import StatsView
from .calcview import calcview
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker  # Rename ticker to avoid conflicts


def compute_integrals(df):
    # Compute the integral of the curve using actual x, y values
    integrals = {}
    for span in [5, 10, 20, 50, 100]:
        # calculation of integral: 
        #x_values = df['ID'][:span] 
        #y_values = df['CLOSE_NORM'][:span] 
        #integral = np.trapz(y_values, x=x_values)
        #integral = integral - y_values.iloc[0]  # subtract the initial value
        
        # this shouldnt be an integral but last value minus first value 
        x_values = df['ID'][:span].values 
        y_values = df['CLOSE_NORM'][:span].values 
        integral=y_values[-1]/y_values[0]

        integrals[f'span_{span}'] = np.round(integral,2)

    integrals['avg']=np.mean(list(integrals.values()))
    integrals['min']=np.min(list(integrals.values()))
    integrals['max']=np.max(list(integrals.values()))
    return integrals



def compute_integrals_vectorized(df):
    # Define the spans you want to compute
    spans = [5, 10, 20, 50, 100]
    # Group the DataFrame by 'GID2' and collect 'CLOSE_NORM' into lists
    grouped = df.groupby('GID2')['CLOSE_NORM'].apply(list)
    # Initialize a DataFrame to hold the results
    integrals_df = pd.DataFrame(index=grouped.index)
    
    for span in spans:
        # Compute the ratios for each group
        def compute_ratio(values):
            if len(values) > 0:
                effective_span = min(len(values), span)
                return np.round(values[effective_span - 1] / values[0], 2)
            else:
                return np.nan  # No data available
            
        # Apply the computation to each group
        integrals_df[f'span_{span}'] = grouped.apply(compute_ratio)
    
    # Compute 'avg', 'min', and 'max' for each group
    integrals_df['avg'] = integrals_df.mean(axis=1, skipna=True)
    integrals_df['min'] = integrals_df.min(axis=1, skipna=True)
    integrals_df['max'] = integrals_df.max(axis=1, skipna=True)
    
    
    # reset ubdex 
    return integrals_df


def compute_integrals_and_plot(df, tickers):


    
    # Filter the dataframe for the specified tickers
    df_tickers = df[df['TICKER'].isin(tickers)]
    
    # Group the data by 'TICKER'
    grouped = df_tickers.groupby('TICKER')
    
    # Initialize a list to collect the results
    results_list = []
    
    # Create the figure and axis objects
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for name, group in grouped:
        # Compute the integrals for each group
        integrals_df = compute_integrals_vectorized(group)
        # Add a 'TICKER' column to keep track of the ticker
        integrals_df['TICKER'] = name
        results_list.append(integrals_df)
        
        # Plot the data for each ticker using the ax object
        if len(tickers)<10: # dont plot all tickers in legend if there are too many
            ax.plot(group['GID'], group['CLOSE_NORM'], '.', label=name)
        else:
            ax.plot(group['GID'], group['CLOSE_NORM'], '.')
    
    # Set the plot title and labels
    ax.set_title('Close Prices for Selected Tickers')
    ax.set_xlabel('ID')
    ax.set_ylabel('Close Price')
    ax.legend()
    
    # Combine the results into a single DataFrame
    results = pd.concat(results_list)
    
    cols=[c for c in results.columns if c not in ('TICKER','GID2')]

    #  compute means 
    means=results[cols].mean()
    means['TICKER'] = 'MEANS'
    means['GID2'] = 0
    # Insert means back to df at the first row
    results.loc[len(results)] = means
    # Reset the index and add it as a column
    results.reset_index(drop=False, inplace=True)
    results['index'] = results.index
    
    return results, means,fig



def make_gains_plot(ticker, metric, cutoff, base_df=None):
    # Show a spinner in Streamlit while the plot is being created
    
    if 1:
        # Query the gains data based on the provided ticker, metric, and cutoff
        df = StatsView().gains_query(ticker, metric, cutoff)
        
        # Create a figure with two subplots, arranged vertically
        fig, (ax, ax2) = plt.subplots(2, 1)
        
        # Dictionary to store integral values for each gain curve
        integrals_dic = {}
        n = 0  # Counter for the number of gain curves
        
        # Plot the primary price action on ax2
        ax2.plot(base_df['ID'], base_df['Close'], 'k')
        
        # Create a secondary y-axis on ax2 for the metric
        ax3 = ax2.twinx()
        
        # Separate the metric values into two series: above and below the cutoff
        above_cutoff = base_df[metric].where(base_df[metric] > cutoff, np.nan)  # Green for above cutoff
        below_cutoff = base_df[metric].where(base_df[metric] <= cutoff, np.nan)  # Red for below cutoff
        
        # Plot the metric values on the secondary y-axis
        ax3.plot(base_df['ID'], above_cutoff, '-g')
        ax3.plot(base_df['ID'], below_cutoff, '-r')
        
        # Customize the grid on ax2 for better visualization
        y_min, y_max = ax2.get_ylim()  # Get the current y-axis limits
        interval = (y_max - y_min) / 20  # Calculate the interval for grid lines
        ax2.yaxis.set_major_locator(mticker.MultipleLocator(interval))
        ax2.grid(True, which='both')  # Ensure gridlines are shown
        
        # Loop over each unique GID2 value to plot the gain curves
        for gid in df['GID2'].unique():
            df_ = df[df['GID2'] == gid]
            
            # Plot the normalized close price on the first subplot
            ax.plot(df_['GID'], df_['CLOSE_NORM'], '-')
            
            # Compute integrals for the current curve and store in dictionary
            integrals = compute_integrals(df_)
            integrals_dic[f'curve_{gid}'] = integrals
            
            # Plot the close price on the secondary subplot
            ax2.plot(df_['ID'], df_['CLOSE'])
            n += 1
            
            # Add a label at the end of each curve
            ax.text(df_['GID'].iloc[-1], df_['CLOSE_NORM'].iloc[-1], f"Curve {n}",
                    verticalalignment='center', horizontalalignment='left')
        
        # Convert the integrals dictionary to a DataFrame
        integrals_df = pd.DataFrame(integrals_dic).T
        
        # Calculate the mean of the integrals and add it to the DataFrame
        integrals_df.loc['mean'] = integrals_df.iloc[:-1].mean()
        
        # Set the title for the first subplot
        ax.set_title(f"Gains curves for {ticker} {metric}={cutoff}")
        
        # Display a message in Streamlit about the number of gain curves observed

        
        # Render the plot in Streamlit
        plt.savefig(f'./plots/{ticker}_gains.png')
    # Return the DataFrame containing the integral values
    return integrals_df




def compute(
    metric='RSI'
    ,cutoff=60
    ,span='span_50'
    ,tickers='AAPL'
    ):



    # take all data
    df=StatsView().gains_query(tickers, metric, cutoff)

    all_tickers=df['TICKER'].unique()
    results,means,fig=compute_integrals(df, all_tickers)
    
    means_avg=results[results['TICKER']=='MEANS'][span].values[0]
    n=len(results)
    final_result=n*means_avg-n
    print(f'Final result: {final_result} nrows {n}')

    # save fig 
    fig.savefig(f'./plots/{tickers}_integrals.png')
    
    # print df 
    print(results)
    
    # print df where gid2=1 
    print(results[results['GID2']==1])
    
    c=calcview(ticker)  
    df=c.get_cv(datefrom='2020-01-01' ) 
    integrals_df=make_gains_plot(tickers,metric,cutoff,df)
    return final_result



    # print results where ticker = means 
