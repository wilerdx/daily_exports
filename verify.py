#!/usr/bin/env python3

import pandas as pd
import sys

def main():
    if len(sys.argv) != 3:
        print("Usage: python verify.py file1.csv file2.csv")
        print("Assumes SKU is in column I (8) and price is in column 5 for file1")
        print("Assumes SKU is in column 0 and price is in column 10 for file2")
        sys.exit(1)

    file1_path = sys.argv[1]
    file2_path = sys.argv[2]

    print("🔍 CSV Price Verification Tool")
    print("=" * 50)

    # Load CSVs
    try:
        df1 = pd.read_csv(file1_path, dtype=str, header=None)  # No header, read all as data
        df2 = pd.read_csv(file2_path, dtype=str, header=None)  # No header, read all as data
        print(f"📁 Loaded {file1_path}: {len(df1)} rows")
        print(f"📁 Loaded {file2_path}: {len(df2)} rows")
    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading files: {e}")
        sys.exit(1)

    # Extract relevant columns (fixed positions)
    df1_slim = df1.iloc[:, [8, 5]].copy()  # SKU in col I (8), price in col 5
    df1_slim.columns = ["SKU", "Price1"]

    df2_slim = df2.iloc[:, [0, 10]].copy()  # SKU in col 0, price in col 10
    df2_slim.columns = ["SKU", "Price2"]

    # Clean data
    df1_slim["SKU"] = df1_slim["SKU"].astype(str).str.strip()
    df2_slim["SKU"] = df2_slim["SKU"].astype(str).str.strip()
    df1_slim["Price1"] = df1_slim["Price1"].astype(str).str.strip()
    df2_slim["Price2"] = df2_slim["Price2"].astype(str).str.strip()

    # Remove empty SKUs
    df1_slim = df1_slim[df1_slim["SKU"] != ""]
    df2_slim = df2_slim[df2_slim["SKU"] != ""]

    print(f"📊 Cleaned data: {len(df1_slim)} rows from file1, {len(df2_slim)} rows from file2")

    # Debug: Show first few rows of each file
    print("\n🔍 Debug - First 3 rows from file1:")
    print(df1_slim.head(3).to_string(index=False))
    print("\n🔍 Debug - First 3 rows from file2:")
    print(df2_slim.head(3).to_string(index=False))

    # Merge like VLOOKUP
    print("\n🔄 Comparing SKUs and prices...")
    merged = pd.merge(df1_slim, df2_slim, on="SKU", how="outer")

    # Debug: Show merged data
    print(f"\n🔍 Debug - Merged data has {len(merged)} rows")
    print("First 5 rows of merged data:")
    print(merged.head(5).to_string(index=False))

    # Find SKUs in both files and calculate price differences
    skus_in_both = merged[
        (merged["Price1"].notna()) & 
        (merged["Price2"].notna())
    ]
    print(f"\n🔍 Debug - SKUs in both files: {len(skus_in_both)}")
    
    # Convert prices to numeric and calculate differences
    skus_in_both["Price1_num"] = pd.to_numeric(skus_in_both["Price1"], errors='coerce')
    skus_in_both["Price2_num"] = pd.to_numeric(skus_in_both["Price2"], errors='coerce')
    skus_in_both["Price_Difference"] = skus_in_both["Price1_num"] - skus_in_both["Price2_num"]
    
    # Find mismatches (difference not 0 or NA)
    mismatches = skus_in_both[
        (skus_in_both["Price_Difference"].notna()) & 
        (skus_in_both["Price_Difference"] != 0)
    ]
    
    print(f"\n🔍 Debug - Price differences:")
    for _, row in skus_in_both.head(5).iterrows():
        print(f"SKU: {row['SKU']}, Price1: {row['Price1_num']}, Price2: {row['Price2_num']}, Diff: {row['Price_Difference']}")

    # Report results
    if mismatches.empty:
        print("\n✅ All matching SKUs have the same price!")
    else:
        print(f"\n❌ Found {len(mismatches)} price mismatches:")
        print(mismatches[["SKU", "Price1", "Price2", "Price_Difference"]].to_string(index=False))

if __name__ == "__main__":
    main()