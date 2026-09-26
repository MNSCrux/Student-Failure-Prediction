import pandas as pd
from sqlalchemy import create_engine

# Create database engine
engine = create_engine("sqlite:///student_portal.db")

# Read both CSV files
df_test = pd.read_csv("data/university_students_test.csv")
df_train = pd.read_csv("data/university_students_train.csv")

# Combine the datasets
df_combined = pd.concat([df_train, df_test], ignore_index=True)

# Load to database
df_combined.to_sql("students", engine, if_exists="replace", index=False)

print(f"Data loaded successfully!")
print(f"Train records: {len(df_train)}")
print(f"Test records: {len(df_test)}")
print(f"Total records: {len(df_combined)}")