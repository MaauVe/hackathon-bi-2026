import pandas as pd
import os

def clean_data(input_path, output_path):
    # Load dataset
    df = pd.read_csv(input_path)
    
    # 1. Handle missing values
    df['discount_code'] = df['discount_code'].fillna('None')
    df['discount_type'] = df['discount_type'].fillna('None')
    df['event_flag'] = df['event_flag'].fillna('None')
    
    # Note: delivery_timestamp and delivery_duration_actual are NaN for cancelled orders. 
    # Leaving them as is, but we could fill delivery_duration_actual with 0 if necessary.
    # The prompt didn't specify for these, but handling them might be good for EDA.
    
    # 2. Convert to datetime
    df['customer_signup_date'] = pd.to_datetime(df['customer_signup_date'])
    df['order_timestamp'] = pd.to_datetime(df['order_timestamp'])
    df['delivery_timestamp'] = pd.to_datetime(df['delivery_timestamp'])
    
    # 3. Remove duplicates
    df = df.drop_duplicates()
    
    # 4. Feature engineering
    # delivery_delay = actual - estimated
    df['delivery_delay'] = df['delivery_duration_actual'] - df['delivery_duration_estimated']
    
    # Extract hour and day of week (0=Monday, 6=Sunday)
    df['order_hour'] = df['order_timestamp'].dt.hour
    df['order_day_of_week'] = df['order_timestamp'].dt.day_of_week
    
    # 5. Verify total_amount consistency
    # calculated_total = item_price * quantity + delivery_fee + tip - discount_value
    df['calculated_total'] = (df['item_price'] * df['quantity'] + 
                             df['delivery_fee'] + 
                             df['tip'] - 
                             df['discount_value'])
    
    # Rounding to 2 decimal places to avoid float precision issues during comparison
    df['calculated_total'] = df['calculated_total'].round(2)
    df['total_amount_consistent'] = (df['total_amount'].round(2) == df['calculated_total'])
    
    inconsistent_count = (~df['total_amount_consistent']).sum()
    print(f"Inconsistent total_amount entries: {inconsistent_count}")
    
    # 6. Save cleaned dataset
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Cleaned dataset saved to {output_path}")

if __name__ == "__main__":
    input_file = 'data/raw/synthetic_food_delivery_transactions.csv'
    output_file = 'data/processed/clean_food_delivery.csv'
    clean_data(input_file, output_file)
