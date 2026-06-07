import pandas as pd

def fix():
    df = pd.read_csv(r"C:\Users\krish\Documents\signalhire\submission.csv")
    
    # Ensure score is treated properly for sorting (descending), then ID (ascending)
    df = df.sort_values(by=['score', 'candidate_id'], ascending=[False, True])
    
    # Reassign rank
    df['rank'] = range(1, len(df) + 1)
    
    df.to_csv(r"C:\Users\krish\Documents\signalhire\submission.csv", index=False)
    print("Fixed tie-breakers.")

if __name__ == "__main__":
    fix()
