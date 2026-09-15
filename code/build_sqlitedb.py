import sqlite3
import glob
import pandas as pd
from decimal import Decimal

def build_table(table_name, files):

    # Create SQLite database
    db_path = "SQLite-db/sessions.db"
    conn = sqlite3.connect(db_path)

    # Process files in batches of 8
    batch_size = 8
    for i in range(0, len(files), batch_size):
        batch_files = files[i:i+batch_size]
        
        # Read and concatenate parquet files in this batch
        dfs = [pd.read_parquet(file) for file in batch_files]
        df_batch = pd.concat(dfs, ignore_index=True)

        # Convert Decimal columns to float
        for col in df_batch.columns:
            if df_batch[col].dtype == 'object':
                try:
                    df_batch[col] = df_batch[col].apply(
                        lambda x: float(x) if isinstance(x, Decimal) else x
                    )
                except (ValueError, TypeError):
                    pass
        
        print(f"\n{table_name.replace('_', ' ').title()} Batch {i//batch_size + 1}:")
        print(f"  Shape: {df_batch.shape}")
        print(f"  Columns: {df_batch.columns.tolist()}")
        print(f"  Memory usage: {df_batch.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        
        # Write dataframe to SQLite table
        is_first = (i == 0)
        df_batch.to_sql(table_name, conn, if_exists="replace" if is_first else "append", index=False)

    # Verify table creation
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]
    print(f"\nSQLite table created: {db_path}")
    print(f"  Table name: {table_name}")
    print(f"  Total rows: {row_count:,}")

    # Show column info
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()
    print(f"\nTable schema:")
    for col in columns_info:
        print(f"  {col[1]} ({col[2]})")

    conn.close()
    print(f"\nDatabase connection closed. File ready at: {db_path}")


tables = [
    'digital_sessions',
    'viewer_sessions',
    'viewer_weights',
    'target_group_mappings',
]

for table_name in tables:
    files = sorted(glob.glob(rf"bucket/{table_name}_*.parquet"))
    build_table(table_name, files)