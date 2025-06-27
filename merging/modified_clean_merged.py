# import pandas as pd
# import re

# # Load the merged CSV
# df = pd.read_csv('merged_for_training.csv')

# def clean_text(text, is_geez=False):
#     # Remove numbers from both columns
#     text = re.sub(r'\d+', '', text)
    
#     # Remove Ge'ez punctuation (፤ = comma, ። = period) and word separators (፡)
#     if is_geez:
#         text = re.sub(r'[፤።፡]', '', text)  # Remove comma, period, and word separator
#     else:
#         # Clean English: keep standard punctuation but remove extra whitespace
#         text = re.sub(r'\s+', ' ', text)  # Collapse spaces
    
#     text = text.strip()
#     return text

# # Apply cleaning to both columns
# df['English'] = df['English'].apply(lambda x: clean_text(str(x), is_geez=False))
# df['Geez'] = df['Geez'].apply(lambda x: clean_text(str(x), is_geez=True))

# # Remove rows with empty entries and duplicates
# df = df[(df['English'].str.len() > 0) & (df['Geez'].str.len() > 0)]
# df = df.drop_duplicates(subset=['English', 'Geez']).reset_index(drop=True)

# # Save the cleaned CSV
# df.to_csv('final_cleanedfor_training.csv', index=False, encoding='utf-8')

# print(f"Cleaned file saved with {len(df)} rows!")
import csv
import re

# Read the CSV file
with open('final_cleanedfor_training.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    rows = list(reader)

# Preprocess the rows
for i, row in enumerate(rows):
    if i > 0:  # Skip the header row
        english_text = row[0]
        geez_text = row[1]

        # Remove double quotes from English text
        english_text = re.sub(r'["”“]', '', english_text)  # Replace straight quotes with nothing

        # Remove numbers from English text
        english_text = re.sub(r'\d+', '', english_text)

        # Remove punctuation from English text
        english_text = re.sub(r'[^\w\s]', '', english_text)

        # Remove numbers from Geez text
        geez_text = re.sub(r'\d+', '', geez_text)

        # Remove ፤ from Geez text
        geez_text = geez_text.replace('፤', '')

        # Remove ። from Geez text
        geez_text = geez_text.replace('።', '')

        # Remove other punctuation from Geez text
        geez_text = re.sub(r'[^\w\sአ-ያ፡-።]', '', geez_text)

        # Update the row with the preprocessed text
        rows[i] = [english_text, geez_text]

# Write the preprocessed rows to a new CSV file
with open('merged_preprocessed.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(rows)

print("Preprocessed CSV file generated.")
