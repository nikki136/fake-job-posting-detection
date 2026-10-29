import pandas as pd

# Load the dataset
df = pd.read_csv('fake_job_postings.csv')

# Display basic information
print(f"Total jobs: {len(df)}")
print(f"Fraudulent jobs: {df['fraudulent'].sum()}")
print(f"Legitimate jobs: {len(df) - df['fraudulent'].sum()}")

# Display column names
print("\nColumns in the dataset:")
for col in df.columns:
    print(f"- {col}")

# Show first few rows
print("\nFirst 3 rows:")
print(df.head(3))

# Show last few rows
print("\nLast 3 rows:")
print(df.tail(3))