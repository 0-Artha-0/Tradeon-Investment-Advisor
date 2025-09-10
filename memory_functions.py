import pandas as pd

# Create the query function to retrieve last 30 entries and entries with similar characteristics


def query_memory(next_pred, change, sentiment_score):
    memory_df = pd.read_excel('investment_memory.xlsx', engine='openpyxl')

    # Convert 'Datetime' to datetime type
    memory_df['Datetime'] = pd.to_datetime(memory_df['Datetime'])

    # Filter for the last 30 entries
    recent_entries = memory_df.tail(30)

    # Filter for entries with similar characteristics
    similar_entries = memory_df[
        (memory_df['Predicted_Price'].between(next_pred * 0.90, next_pred * 1.1)) &
        (memory_df['Predicted_Change_Percentage'].between(change * 0.90, change * 1.1)) &
        (memory_df['Sentiment_Score'].between(
            sentiment_score * 0.90, sentiment_score * 1.1))
    ]

    # If the memory is empty, return a message
    if recent_entries.empty and similar_entries.empty:
        return "No recent or similar entries found in memory."

    # Limit similar entries to 30 if there are too many
    if len(similar_entries) > 30:
        similar_entries = similar_entries.head(30)

    # Combine recent and similar entries
    combined_entries = pd.concat(
        [recent_entries, similar_entries]).drop_duplicates().reset_index(drop=True)

    # Get the total number of recent and similar entries found
    size = len(combined_entries)

    # Calculate the success rate of retrieved entries based on Ground_Truth_Decision
    success = ((combined_entries['Ground_Truth_Decision']
               == 1).sum() / size)*100 if size > 0 else 0

    # Ensure the combined DataFrame is sorted by Datetime
    combined_entries.sort_values(by='Datetime', ascending=False, inplace=True)

    # Convert Dataframe to JSON string for prompt
    combined_entries_json = combined_entries.to_json(
        orient='records', force_ascii=False)

    # Return the combined DataFrame and the number of recent and similar entries found
    return combined_entries_json, size, success

# Function to add a new entry to the memory


def insert_memory(end_date, next_pred, change, sentiment_score, news, decision, analysis, company_name="Aramco"):
    # Load the existing memory DataFrame
    memory_df = pd.read_excel('investment_memory.xlsx', engine='openpyxl')

    # Create a new entry
    new_entry = {
        'Datetime': end_date,
        'Company': company_name,
        'Predicted_Price': next_pred,
        'Predicted_Change_Percentage': change,
        'Sentiment_Score': sentiment_score,
        'News': news,
        'Analysis': analysis,
        'Decision': decision,
        'Actual_Price': '-',  # To be updated later
        'Ground_Truth_Change_Percentage': '-',  # To be updated later
        'Ground_Truth_Decision': '-'  # To be updated later
    }

    # Append the new entry to the DataFrame
    memory_df = pd.concat(
        [memory_df, pd.DataFrame([new_entry])], ignore_index=True)

    # Save the updated DataFrame back to the Excel file
    memory_df.to_excel('investment_memory.xlsx',
                       index=False, engine='openpyxl')
    print("New entry added to memory.")


def update_memory_daily(actual_price, ground_percentage):
    # Load the existing memory DataFrame
    memory_df = pd.read_excel('investment_memory.xlsx', engine='openpyxl')

    # if the memory is not empty
    if not memory_df.empty:
        yesterday_entry = memory_df.iloc[-1]
        # Check if last entry has none for ground truth and actual price
        if yesterday_entry['Actual_Price'] == '-' and yesterday_entry['Ground_Truth_Change_Percentage'] == '-' and yesterday_entry['Ground_Truth_Decision'] == '-':
            # Update the last entry with actual price and ground percentage
            memory_df.at[memory_df.index[-1], 'Actual_Price'] = actual_price
            memory_df.at[memory_df.index[-1],
                         'Ground_Truth_Change_Percentage'] = ground_percentage

            # Update ground_truth_decisin to evaluate and penelize the model decision after confirming the true stock movement (assuming a simple short term strategy)
            # set the accepted change percentage threshold
            accepted_threshold = 0.15

            # 1: the model decision is correct/acceptable , 2: the model decision was incorrect
            # if the change is less than the threshold, then any model decision is toleratable
            if abs(ground_percentage) <= accepted_threshold:
                memory_df.at[memory_df.index[-1], 'Ground_Truth_Decision'] = 1

            # if the model decision was HOLD, then extend the threshold a little, as it may acceptable as well
            elif memory_df.at[memory_df.index[-1], 'Decision'] == 'HOLD' and abs(ground_percentage) <= (accepted_threshold*2):
                memory_df.at[memory_df.index[-1], 'Ground_Truth_Decision'] = 1

            # otherwise, the change percentage is negative (drop in price) and the model last decision was SELL the shares
            elif memory_df.at[memory_df.index[-1], 'Decision'] == 'SELL' and ground_percentage < 0:
                # Then the model decision was correct
                memory_df.at[memory_df.index[-1], 'Ground_Truth_Decision'] = 1

            # otherwise, the change percentage is positive (increase in price) and the model last decision was BUY more shares
            elif memory_df.at[memory_df.index[-1], 'Decision'] == 'BUY' and ground_percentage > 0:
                # Then the model decision was correct
                memory_df.at[memory_df.index[-1], 'Ground_Truth_Decision'] = 1

            else:
                memory_df.at[memory_df.index[-1], 'Ground_Truth_Decision'] = 0

            # Save the updated DataFrame back to the Excel file
            memory_df.to_excel('investment_memory.xlsx',
                               index=False, engine='openpyxl')
            print(
                "Memory updated with today's actual price, ground change percentage, and ground truth decision.")
        else:
            print("Last entry already has contains ground truth.")
    else:
        print("Memory is empty, nothing to update.")


# Function to fetch the last 7 LSTM and Sentiment predictions for dashboard display

def fetch_lists():
    # Load the existing memory DataFrame
    memory_df = pd.read_excel('investment_memory.xlsx', engine='openpyxl')

    # Extract the 'Predicted_Price' and 'Sentiment_Score' columns as lists for dashboard display
    lstm_list = memory_df['Predicted_Price'].tolist()
    lstm_list = lstm_list[-7:]  # get the last 7 predictions only

    sentiment_list = memory_df['Sentiment_Score'].tolist()
    sentiment_list = sentiment_list[-7:]  # get the last 7 predictions only

    return [lstm_list, sentiment_list]
