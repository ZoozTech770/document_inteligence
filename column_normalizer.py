#!/usr/bin/env python3
"""
Column Normalizer for OCR Results
Normalizes duplicate columns that contain the same type of data
"""

import pandas as pd
from typing import Dict, List, Any
import json
import re

class ColumnNormalizer:
    def __init__(self, config_file='column_mapping.json'):
        self.config_file = config_file
        self.column_mapping = self.load_or_create_config()
    
    def load_or_create_config(self) -> Dict[str, List[str]]:
        """Load existing config or create default one"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Create default configuration based on your current findings
            default_config = {
                "ID": [
                    "Passport/ ID",
                    "מספר ת.ז", 
                    "תז",
                    "ת״ז",
                    "ת. ז",
                    "I.D.",
                    "ID",
                    "Passport",
                    "ת.ז",
                    "מספר זהות",
                    "תעודת זהות",
                    "ת.ז."
                ],
                "First Name": [
                    "First Name",
                    "שם פרטי",
                    "שם מלא",
                    "First Name\n:selected:",
                    "שם",
                    "פרטי",
                    "Student Name"
                ],
                "Last Name": [
                    "Last Name",
                    "שם משפחה",
                    "משפחה",
                    "surname"
                ],
                "Employee Number": [
                    "מספר עובד. ת",
                    "מספר עובד",
                    "Employee ID",
                    "עובד"
                ],
                "Signature": [
                    "חתימה",
                    "Signature",
                    "Sign"
                ],
                "Title/Position": [
                    "Title\n(Position/ Job description)",
                    "Title",
                    "Position",
                    "Job",
                    "תפקיד"
                ],
                "Date of Birth": [
                    "DOB\n(mm/dd/yyyy)",
                    "DOB",
                    "Date of Birth",
                    "תאריך לידה"
                ],
                "Nationality": [
                    "Nationality",
                    "לאום",
                    "אזרחות"
                ],
                "Product Description": [
                    "תאור מוצר",
                    "Product",
                    "Description",
                    "מוצר"
                ],
                "Quantity": [
                    "כמות",
                    "Quantity",
                    "Amount"
                ],
                "Price": [
                    "מחיר ליחידה",
                    "סה״כ מחיר",
                    "Price",
                    "Total",
                    "מחיר"
                ],
                "Supply Date": [
                    "ת. אספקה",
                    "Supply Date",
                    "תאריך אספקה"
                ],
                "Row Number": [
                    "שורה",
                    "Row",
                    "Line",
                    "Index",
                    "מספר",  # Sequential row numbers
                    "#",
                    "Number"
                ],
                "Balance": [
                    "יתרה לאספקה",
                    "Balance",
                    "Remaining",
                    "יתרה"
                ],
                "Phone Number": [
                    "Phone",
                    "טלפון",
                    "נייד",
                    "Mobile",
                    "Phone Number",
                    "מספר טלפון"
                ]
            }
            self.save_config(default_config)
            return default_config
    
    def clean_column_name(self, col_name: str) -> str:
        """Clean column name by removing special characters and trimming whitespace"""
        if not col_name:
            return ""
        
        # Convert to string and strip whitespace
        cleaned = str(col_name).strip()
        
        # Handle special cases
        if cleaned.startswith('Unnamed:'):
            return ""  # Empty unnamed columns
        
        # Remove problematic patterns
        # Remove :selected: and :unselected: patterns
        cleaned = re.sub(r':selected:', '', cleaned)
        cleaned = re.sub(r':unselected:', '', cleaned)
        
        # Remove Arabic/foreign characters mixed with Hebrew
        cleaned = re.sub(r'[\u0600-\u06FF]', '', cleaned)  # Arabic
        cleaned = re.sub(r'[\u0080-\u00FF]', '', cleaned)  # Latin extended
        
        # Remove various OCR artifacts
        cleaned = re.sub(r'[V\(\)]\s*PINVIS.*', '', cleaned)
        cleaned = re.sub(r'\d+Nd\s+DOIS.*', '', cleaned)
        cleaned = re.sub(r'Good\s*Neutral.*', '', cleaned)
        cleaned = re.sub(r'\d+/\d+/\d+', '', cleaned)  # Dates that became column names
        
        # Clean up newlines and multiple spaces
        cleaned = re.sub(r'\n+', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remove HTML-like patterns
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        
        # Remove common OCR artifacts
        cleaned = re.sub(r'[\(\)\"\']', '', cleaned)
        
        # Remove Unicode control characters and weird symbols
        cleaned = re.sub(r'[\u0000-\u001F\u007F-\u009F]', '', cleaned)
        
        # Keep Hebrew/English letters, numbers, dots, hyphens, and spaces
        cleaned = re.sub(r'[^\w\u0590-\u05FF\s\.\-]', '', cleaned)
        
        # Remove extra whitespace
        cleaned = ' '.join(cleaned.split())
        
        # Remove trailing dots unless it's a meaningful abbreviation
        if cleaned.endswith('.') and len(cleaned) > 3:
            cleaned = cleaned.rstrip('.')
        
        # Remove leading/trailing special characters
        cleaned = cleaned.strip('.-_')
        
        return cleaned
    
    def save_config(self, config: Dict[str, List[str]]) -> None:
        """Save configuration to file"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"Column mapping configuration saved to: {self.config_file}")
    
    def add_column_mapping(self, normalized_name: str, column_variants: List[str]) -> None:
        """Add or update column mapping"""
        self.column_mapping[normalized_name] = column_variants
        self.save_config(self.column_mapping)
        print(f"Added mapping: {normalized_name} -> {column_variants}")
    
    def find_matching_columns(self, df_columns: List[str]) -> Dict[str, List[str]]:
        """Find which columns in the DataFrame match our mapping"""
        matches = {}
        
        for normalized_name, variants in self.column_mapping.items():
            found_columns = []
            
            for col in df_columns:
                # Clean the column name first
                col_cleaned = self.clean_column_name(col)
                
                # Exact match (original)
                if col in variants:
                    found_columns.append(col)
                    continue
                
                # Exact match (cleaned)
                if col_cleaned in variants:
                    found_columns.append(col)
                    continue
                
                # Clean variants for comparison
                for variant in variants:
                    variant_cleaned = self.clean_column_name(variant)
                    
                    # Match cleaned versions (case insensitive)
                    col_lower = col_cleaned.lower()
                    variant_lower = variant_cleaned.lower()
                    
                    if col_lower == variant_lower:
                        found_columns.append(col)
                        break
                    
                    # Partial match for complex headers
                    if variant_lower in col_lower or col_lower in variant_lower:
                        # Only if it's a significant match (> 70% of the shorter string)
                        shorter_len = min(len(col_lower), len(variant_lower))
                        if shorter_len > 2:  # Avoid matching very short strings
                            found_columns.append(col)
                            break
            
            # Remove duplicates while preserving order
            found_columns = list(dict.fromkeys(found_columns))
            
            if found_columns:
                matches[normalized_name] = found_columns
        
        return matches
    
    def detect_data_as_headers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect if data content is being used as column headers"""
        if len(df) < 2:  # Need at least 2 rows to detect this pattern
            return df
        
        # Look for signs that column headers contain data instead of field names
        suspicious_headers = []
        total_cols = len(df.columns)
        
        for col in df.columns:
            if col == 'Source File':
                continue
                
            col_str = str(col).strip()
            if not col_str:
                continue
            
            # Check for patterns that suggest this is data, not a header:
            # 1. Contains multiple Hebrew/English names (like "ליאל גניש ואוהד שמח")
            # 2. Contains numbers that look like IDs or dates
            # 3. Contains phone numbers
            # 4. Contains long text that looks like content
            
            is_suspicious = False
            
            # Pattern 1: Multiple names (Hebrew or English)
            # Look for Hebrew names pattern: multiple Hebrew words with "ו" (and) or spaces
            hebrew_words = re.findall(r'[\u0590-\u05FF]+', col_str)
            english_words = re.findall(r'[a-zA-Z]+', col_str)
            
            if len(hebrew_words) >= 3 or len(english_words) >= 3:
                # Multiple words suggest this might be content, not a header
                is_suspicious = True
            
            # Pattern 2: Contains "ו" (Hebrew "and") which suggests multiple names
            if 'ו' in col_str and len(hebrew_words) >= 2:
                is_suspicious = True
            
            # Pattern 3: Contains numbers that look like IDs, phone numbers, or dates
            numbers = re.findall(r'\d+', col_str)
            for num in numbers:
                if len(num) >= 7:  # Long numbers (IDs, phones) shouldn't be headers
                    is_suspicious = True
                    break
            
            # Pattern 4: Very long text (more than 30 characters) is likely content
            if len(col_str) > 30:
                is_suspicious = True
            
            # Pattern 5: Contains common data separators like "|" or "," with meaningful content
            if ('|' in col_str or ',' in col_str) and len(col_str) > 10:
                is_suspicious = True
            
            if is_suspicious:
                suspicious_headers.append(col)
        
        # If more than 40% of headers look suspicious, check if we can find better headers
        if len(suspicious_headers) >= total_cols * 0.4 and total_cols > 2:
            print(f"\n🔍 DETECTED SUSPICIOUS COLUMN HEADERS (likely data content):")
            print("=" * 60)
            for col in suspicious_headers:
                print(f"  Suspicious: '{col}'")
            
            # Try to find real headers in the first few rows
            real_headers_found = False
            
            # Check first 3 rows for potential headers
            for row_idx in range(min(3, len(df))):
                current_row = df.iloc[row_idx]
                
                # Count how many cells look like proper column headers
                header_like_count = 0
                potential_headers = []
                
                for val in current_row:
                    if pd.notna(val) and str(val).strip():
                        val_str = str(val).strip()
                        
                        # Check if this looks like a proper header (not data)
                        looks_like_header = (
                            len(val_str) <= 25 and  # Not too long
                            not re.search(r'\d{7,}', val_str) and  # No long numbers
                            not ('ו' in val_str and len(re.findall(r'[\u0590-\u05FF]+', val_str)) >= 3) and  # Not multiple Hebrew names
                            val_str not in suspicious_headers  # Not already a suspicious header
                        )
                        
                        if looks_like_header:
                            header_like_count += 1
                            potential_headers.append(val_str)
                        else:
                            potential_headers.append(None)
                
                # If this row has mostly header-like content, use it
                if header_like_count >= total_cols * 0.6:
                    print(f"\n🔄 FOUND BETTER HEADERS IN ROW {row_idx + 1}:")
                    print("=" * 50)
                    
                    # Create new column names
                    new_columns = []
                    for i, (old_col, new_header) in enumerate(zip(df.columns, potential_headers)):
                        if new_header:
                            new_col_name = self.clean_column_name(new_header)
                            if new_col_name:
                                new_columns.append(new_col_name)
                                print(f"  Column '{old_col}' → '{new_col_name}'")
                            else:
                                new_columns.append(f"Column_{i+1}")  # Fallback name
                        else:
                            new_columns.append(f"Column_{i+1}")  # Fallback name
                    
                    # Convert suspicious headers to data
                    # Insert the old headers as a new first row
                    old_headers_row = pd.DataFrame([df.columns], columns=df.columns)
                    df_with_old_headers = pd.concat([old_headers_row, df], ignore_index=True)
                    
                    # Update column names
                    df_with_old_headers.columns = new_columns
                    
                    # Remove the row we used as headers
                    df_with_old_headers = df_with_old_headers.drop(df_with_old_headers.index[row_idx + 1]).reset_index(drop=True)
                    
                    print(f"  → Converted {len(suspicious_headers)} suspicious headers to data")
                    print(f"  → Updated {len(new_columns)} column headers")
                    
                    return df_with_old_headers
        
        return df
    
    def detect_and_fix_excel_headers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect if Excel column names are used but real headers are in first data row"""
        if len(df) < 1:
            return df
            
        excel_columns = [chr(i) for i in range(ord('A'), ord('Z')+1)]  # A-Z
        
        # Check if current column names are mostly Excel column names
        excel_col_count = sum(1 for col in df.columns if str(col).strip() in excel_columns)
        total_cols = len(df.columns)
        
        # If more than 50% of columns are Excel column names, check if first row has better headers
        if excel_col_count > total_cols * 0.5 and total_cols > 2:
            # Check if first row (index 0) has meaningful text that could be headers
            first_row = df.iloc[0] if len(df) > 0 else None
            
            if first_row is not None:
                # Count how many cells in first row contain meaningful text (Hebrew/English letters)
                meaningful_headers = 0
                for val in first_row:
                    if pd.notna(val) and str(val).strip():
                        val_str = str(val).strip()
                        # Check if contains letters (Hebrew or English)
                        if re.search(r'[\u0590-\u05FFa-zA-Z]', val_str) and len(val_str) > 1:
                            meaningful_headers += 1
                
                # If most cells in first row look like headers, use them
                if meaningful_headers >= total_cols * 0.6:
                    print(f"\n🔄 DETECTED EXCEL HEADERS WITH REAL HEADERS IN FIRST ROW:")
                    print("=" * 60)
                    
                    # Create new column names from first row
                    new_columns = []
                    for i, (old_col, new_val) in enumerate(zip(df.columns, first_row)):
                        if pd.notna(new_val) and str(new_val).strip():
                            new_col_name = str(new_val).strip()
                            # Clean the new column name
                            new_col_name = self.clean_column_name(new_col_name)
                            if new_col_name:
                                new_columns.append(new_col_name)
                                print(f"  Column '{old_col}' → '{new_col_name}'")
                            else:
                                new_columns.append(old_col)  # Keep original if cleaning failed
                        else:
                            new_columns.append(old_col)  # Keep original if no meaningful value
                    
                    # Update column names
                    df.columns = new_columns
                    
                    # Remove the first row since it's now used as headers
                    df = df.drop(df.index[0]).reset_index(drop=True)
                    
                    print(f"  → Updated {len(new_columns)} column headers")
                    print(f"  → Removed header row from data")
                    
                    return df
        
        return df
    
    def filter_excel_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove Excel column names (A, B, C, D, etc.) that are not valid data columns"""
        excel_columns = [chr(i) for i in range(ord('A'), ord('Z')+1)]  # A-Z
        
        columns_to_remove = []
        for col in df.columns:
            col_str = str(col).strip()
            if col_str in excel_columns:
                columns_to_remove.append(col)
        
        if columns_to_remove:
            print(f"\n🚫 REMOVING EXCEL COLUMN NAMES:")
            print("=" * 50)
            for col in columns_to_remove:
                non_null_count = df[col].notna().sum()
                print(f"  Removing '{col}' (Excel column name, {non_null_count} values)")
            
            df = df.drop(columns=columns_to_remove)
            print(f"  → Removed {len(columns_to_remove)} Excel column names")
        
        return df
    
    def filter_empty_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove columns that are empty or have no meaningful data"""
        columns_to_remove = []
        
        for col in df.columns:
            col_str = str(col).strip()
            
            # Skip Source File column
            if col == 'Source File':
                continue
            
            # Remove unnamed columns
            if col_str.startswith('Unnamed:') or col_str == '':
                # But only if they have very little data
                non_null_count = df[col].notna().sum()
                if non_null_count < 5:  # Less than 5 non-null values
                    columns_to_remove.append(col)
                    continue
            
            # Remove columns with only whitespace or meaningless data
            if len(col_str) == 0 or col_str.isspace():
                columns_to_remove.append(col)
                continue
            
            # Remove columns that are clearly OCR artifacts
            if (len(col_str) == 1 and col_str.isdigit()) or col_str in ['1', '2', '3', '4', '5']:
                # Single digit column names are usually artifacts
                non_null_count = df[col].notna().sum()
                if non_null_count < 10:  # Unless they have significant data
                    columns_to_remove.append(col)
        
        if columns_to_remove:
            print(f"\n🧹 CLEANING EMPTY/MEANINGLESS COLUMNS:")
            print("=" * 50)
            for col in columns_to_remove:
                non_null_count = df[col].notna().sum()
                col_display = f'"{col}"' if col.strip() == '' else col
                print(f"  Removing {col_display} ({non_null_count} values - low quality data)")
            
            df = df.drop(columns=columns_to_remove)
            print(f"  → Removed {len(columns_to_remove)} low-quality columns")
        
        return df
    
    def fix_misplaced_id_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect and fix columns that contain ID data but have wrong column names"""
        import re
        
        # Regular ID pattern (Israeli ID - 9 digits) vs Military ID pattern (7-8 digits)
        regular_id_pattern = re.compile(r'^\d{9}$')
        military_id_pattern = re.compile(r'^\d{7,8}$')
        general_id_pattern = re.compile(r'^\d{7,10}$')
        problematic_columns = []
        
        # Check for columns that might contain misplaced ID data
        for col in df.columns:
            if col in ['ID', 'Employee Number', 'Serial Number', 'Military ID', 'Phone Number', 'Phone', 'Source File']:
                continue  # Skip columns that should contain numbers
            
            # Check if this column contains mostly ID-like values
            sample_values = df[col].dropna().head(20)
            if len(sample_values) == 0:
                continue
                
            id_like_count = 0
            military_like_count = 0
            regular_id_like_count = 0
            
            for val in sample_values:
                val_str = str(val).strip()
                if regular_id_pattern.match(val_str):
                    regular_id_like_count += 1
                    id_like_count += 1
                elif military_id_pattern.match(val_str):
                    military_like_count += 1
                    id_like_count += 1
                elif general_id_pattern.match(val_str):
                    id_like_count += 1
            
            # If more than 60% of values look like IDs
            if id_like_count >= len(sample_values) * 0.6 and id_like_count >= 3:
                # Determine the type of ID based on the pattern
                if military_like_count > regular_id_like_count and military_like_count >= len(sample_values) * 0.6:
                    problematic_columns.append((col, id_like_count, len(sample_values), 'Military ID'))
                else:
                    problematic_columns.append((col, id_like_count, len(sample_values), 'ID'))
        
        if problematic_columns:
            print(f"\n🔧 FIXING MISPLACED ID DATA:")
            print("=" * 50)
            
            for col, id_count, total, target_type in problematic_columns:
                print(f"  Column '{col}' contains {id_count}/{total} ID-like values")
                
                # Merge into the appropriate target column
                if target_type in df.columns:
                    print(f"  → Merging '{col}' data into '{target_type}' column")
                    
                    # Merge the ID data
                    for idx in df.index:
                        current_id = df.loc[idx, target_type]
                        misplaced_id = df.loc[idx, col]
                        
                        if pd.notna(misplaced_id) and general_id_pattern.match(str(misplaced_id).strip()):
                            if pd.isna(current_id) or str(current_id).strip() == '':
                                # Target column is empty, move the misplaced ID
                                df.loc[idx, target_type] = str(misplaced_id).strip()
                                df.loc[idx, col] = None
                else:
                    # No target column exists, rename this column
                    print(f"  → Renaming '{col}' to '{target_type}'")
                    df = df.rename(columns={col: target_type})
        
        return df
    
    def filter_data_promoted_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove columns that are clearly data values (like dates) promoted to column headers"""
        columns_to_remove = []
        
        for col in df.columns:
            if col == 'Source File':
                continue
                
            col_str = str(col).strip()
            if not col_str:
                continue
            
            # Check if this column name looks like data content
            is_data = False
            
            # Pattern 1: Date patterns
            if (re.match(r'\d{1,2}/\d{1,2}/\d{2,4}', col_str) or 
                re.match(r'\d{4}-\d{2}-\d{2}', col_str) or
                re.match(r'\d{1,2}\.\d{1,2}\.\d{2,4}', col_str)):
                is_data = True
            
            # Pattern 2: ID numbers (7+ digits)
            elif re.match(r'^\d{7,12}$', col_str):
                is_data = True
            
            # Pattern 3: Phone numbers
            elif (re.match(r'^\d{3}-\d{3}-\d{4}$', col_str) or 
                  re.match(r'^\d{10}$', col_str)):
                is_data = True
            
            # Pattern 4: Multiple names (Hebrew or English)
            elif len(re.findall(r'[\u0590-\u05FF]+', col_str)) >= 3:
                is_data = True
            
            # Pattern 5: Hebrew "and" indicating multiple names
            elif 'ו' in col_str and len(re.findall(r'[\u0590-\u05FF]+', col_str)) >= 2:
                is_data = True
            
            # Pattern 6: Very long text (likely content)
            elif len(col_str) > 30:
                is_data = True
            
            # Pattern 7: Contains separators with meaningful content
            elif ('|' in col_str or ',' in col_str) and len(col_str) > 10:
                is_data = True
            
            # Pattern 8: OCR artifacts
            elif any(artifact in col_str for artifact in ['V(PINVIS', 'Nd DOIS', 'Good Neutral']):
                is_data = True
            
            if is_data:
                columns_to_remove.append(col)
        
        if columns_to_remove:
            print(f"\n🚫 REMOVING DATA-PROMOTED COLUMNS:")
            print("=" * 50)
            for col in columns_to_remove:
                non_null_count = df[col].notna().sum()
                print(f"  Removing '{col}' (data promoted to header, {non_null_count} values)")
            
            df = df.drop(columns=columns_to_remove)
            print(f"  → Removed {len(columns_to_remove)} data-promoted columns")
        
        return df
    
    def filter_low_quality_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove columns with very little meaningful data"""
        columns_to_remove = []
        total_rows = len(df)
        
        for col in df.columns:
            if col == 'Source File':
                continue
            
            # Count non-null, non-empty values
            meaningful_values = 0
            for val in df[col].dropna():
                val_str = str(val).strip()
                if val_str and val_str != '':
                    meaningful_values += 1
            
            # Remove columns with very low data density (less than 5% meaningful data)
            if total_rows > 100 and meaningful_values < (total_rows * 0.05):
                columns_to_remove.append(col)
            # Remove columns with less than 3 meaningful values regardless of density
            elif meaningful_values < 3:
                columns_to_remove.append(col)
        
        if columns_to_remove:
            print(f"\n🧹 REMOVING LOW-QUALITY COLUMNS:")
            print("=" * 50)
            for col in columns_to_remove:
                meaningful_count = sum(1 for val in df[col].dropna() if str(val).strip())
                print(f"  Removing '{col}' (only {meaningful_count} meaningful values)")
            
            df = df.drop(columns=columns_to_remove)
            print(f"  → Removed {len(columns_to_remove)} low-quality columns")
        
        return df
    
    def normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize DataFrame by merging duplicate columns"""
        df_normalized = df.copy()
        
        # First, remove columns that are clearly data promoted to headers
        df_normalized = self.filter_data_promoted_columns(df_normalized)
        
        # Then, detect if data content is being used as column headers
        df_normalized = self.detect_data_as_headers(df_normalized)
        
        # Then, detect and fix Excel headers where real headers are in first data row
        df_normalized = self.detect_and_fix_excel_headers(df_normalized)
        
        # Then, filter out remaining Excel column names
        df_normalized = self.filter_excel_column_names(df_normalized)
        
        # Filter out empty/unnamed columns with no useful data
        df_normalized = self.filter_empty_columns(df_normalized)
        
        # Filter out columns with very little meaningful data
        df_normalized = self.filter_low_quality_columns(df_normalized)
        
        # Detect and fix misplaced ID data
        df_normalized = self.fix_misplaced_id_data(df_normalized)
        
        # Find matching columns
        matches = self.find_matching_columns(df_normalized.columns.tolist())
        
        # Special handling: Don't merge Row Number with ID columns
        if 'ID' in matches and 'Row Number' in matches:
            # Check if any ID columns are actually row numbers that should stay separate
            id_columns = matches['ID']
            row_number_columns = matches['Row Number']
            
            # Check for overlap - if same column is in both categories
            overlap = set(id_columns) & set(row_number_columns)
            if overlap:
                print(f"\n⚠️  COLUMN CONFLICT DETECTED:")
                print(f"Columns found in both ID and Row Number categories: {list(overlap)}")
                
                # Analyze the data to determine which category is correct
                for col in overlap:
                    sample_values = df_normalized[col].dropna().head(10)
                    if len(sample_values) > 0:
                        # Check if values are sequential numbers (1, 2, 3, ...) - indicates row numbers
                        values_list = []
                        for val in sample_values:
                            try:
                                num_val = int(str(val).strip())
                                values_list.append(num_val)
                            except (ValueError, AttributeError):
                                continue
                        
                        if len(values_list) >= 3:
                            is_sequential = all(values_list[i] == values_list[0] + i for i in range(len(values_list)))
                            starts_with_low_number = values_list[0] <= 5  # Starts with 1, 2, 3, 4, or 5
                            max_value = max(values_list) if values_list else 0
                            has_reasonable_range = max_value <= 100  # Row numbers usually don't exceed 100
                            
                            if is_sequential and starts_with_low_number and has_reasonable_range:
                                print(f"  → '{col}' appears to be row numbers (sequential: {values_list[:5]}..., max: {max_value})")
                                # Remove from ID category, keep in Row Number
                                matches['ID'] = [c for c in matches['ID'] if c != col]
                                continue
                        
                        # Check if values look like actual IDs (7+ digits, not sequential)
                        long_id_count = sum(1 for val in sample_values if len(str(val).strip()) >= 7)
                        if long_id_count >= len(sample_values) * 0.8:  # 80% are long numbers
                            print(f"  → '{col}' appears to be actual IDs (long numbers)")
                            # Remove from Row Number category, keep in ID
                            matches['Row Number'] = [c for c in matches['Row Number'] if c != col]
                        else:
                            print(f"  → '{col}' appears to be row numbers (short numbers)")
                            # Remove from ID category, keep in Row Number
                            matches['ID'] = [c for c in matches['ID'] if c != col]
        
        print("\n🔄 COLUMN NORMALIZATION:")
        print("=" * 50)
        
        for normalized_name, found_columns in matches.items():
            if len(found_columns) > 1:
                print(f"Merging {len(found_columns)} columns into '{normalized_name}':")
                for col in found_columns:
                    # Check if column still exists (might have been renamed)
                    if col in df_normalized.columns:
                        non_null_count = df_normalized[col].notna().sum()
                        print(f"  • {col} ({non_null_count} values)")
                    else:
                        print(f"  • {col} (column no longer exists - may have been renamed)")
                
                # Merge columns by combining non-null values
                merged_series = pd.Series(index=df_normalized.index, dtype='object')
                
                # Filter to only existing columns
                existing_columns = [col for col in found_columns if col in df_normalized.columns]
                
                for idx in df_normalized.index:
                    values = []
                    for col in existing_columns:
                        val = df_normalized.loc[idx, col]
                        if pd.notna(val) and str(val).strip():
                            values.append(str(val).strip())
                    
                    if values:
                        # If multiple non-null values exist, prefer the first one
                        # or combine them if they're different
                        unique_values = list(set(values))
                        if len(unique_values) == 1:
                            merged_series.loc[idx] = unique_values[0]
                        else:
                            # Multiple different values - combine them
                            merged_series.loc[idx] = " | ".join(unique_values)
                
                # Remove the original columns FIRST (before adding the new one with potentially same name)
                columns_to_drop = [col for col in existing_columns if col in df_normalized.columns and col != normalized_name]
                if columns_to_drop:
                    df_normalized = df_normalized.drop(columns=columns_to_drop)
                    print(f"  → Dropped original columns: {columns_to_drop}")
                
                # Now add the normalized column
                df_normalized[normalized_name] = merged_series
                
                print(f"  → Created '{normalized_name}' with {merged_series.notna().sum()} values")
                print()
            
            elif len(found_columns) == 1:
                # Single column found - just rename it
                old_name = found_columns[0]
                if old_name != normalized_name:
                    df_normalized = df_normalized.rename(columns={old_name: normalized_name})
                    print(f"Renamed: '{old_name}' → '{normalized_name}'")
        
        # Reorder columns with Source File first, then normalized columns
        column_order = []
        if 'Source File' in df_normalized.columns:
            column_order.append('Source File')
        
        # Add normalized columns in a logical order
        preferred_order = [
            'ID', 'First Name', 'Last Name', 'Employee Number', 
            'Title/Position', 'Date of Birth', 'Nationality', 'Phone Number',
            'Product Description', 'Quantity', 'Price', 'Supply Date',
            'Row Number', 'Balance', 'Signature'
        ]
        
        for col in preferred_order:
            if col in df_normalized.columns and col not in column_order:
                column_order.append(col)
        
        # Add any remaining columns that weren't in the preferred order
        for col in df_normalized.columns:
            if col not in column_order:
                column_order.append(col)
        
        # Reorder columns
        df_normalized = df_normalized[column_order]
        
        # Post-processing: Move long Employee Numbers to ID column
        df_normalized = self.post_process_id_fields(df_normalized)
        
        print(f"\n✅ Normalization complete!")
        print(f"Original columns: {len(df.columns)}")
        print(f"Normalized columns: {len(df_normalized.columns)}")
        print(f"Columns reduced by: {len(df.columns) - len(df_normalized.columns)}")
        
        return df_normalized
    
    def show_current_mapping(self) -> None:
        """Display current column mapping configuration"""
        print("\n📋 CURRENT COLUMN MAPPING:")
        print("=" * 50)
        for normalized_name, variants in self.column_mapping.items():
            print(f"\n{normalized_name}:")
            for variant in variants:
                print(f"  • {variant}")
    
    def analyze_unknown_columns(self, df: pd.DataFrame) -> List[str]:
        """Find columns that don't match any mapping"""
        matches = self.find_matching_columns(df.columns.tolist())
        matched_columns = set()
        
        for found_columns in matches.values():
            matched_columns.update(found_columns)
        
        unknown_columns = [col for col in df.columns if col not in matched_columns and col != 'Source File']
        
        if unknown_columns:
            print("\n❓ UNKNOWN COLUMNS FOUND:")
            print("=" * 50)
            print("These columns don't match any existing mapping:")
            for col in unknown_columns:
                non_null_count = df[col].notna().sum()
                print(f"  • {col} ({non_null_count} values)")
            print("\nConsider adding these to your column mapping configuration.")
        
        return unknown_columns
    
    def post_process_id_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Post-process to move long Employee Numbers to ID column"""
        if 'Employee Number' not in df.columns or 'ID' not in df.columns:
            return df
        
        print("\n🔧 POST-PROCESSING: Moving long Employee Numbers to ID column...")
        
        moved_count = 0
        replaced_count = 0
        
        for idx in df.index:
            emp_num = df.loc[idx, 'Employee Number']
            current_id = df.loc[idx, 'ID']
            
            # Check if Employee Number exists and is longer than 7 chars
            if pd.notna(emp_num) and len(str(emp_num).strip()) > 7:
                emp_num_clean = str(emp_num).strip()
                
                # Check if this looks like a valid ID (numeric, reasonable length)
                # Handle cases with slashes (like "02/911490")
                emp_num_digits_only = ''.join(c for c in emp_num_clean if c.isdigit())
                
                if (emp_num_clean.isdigit() or 
                    (emp_num_clean.startswith('A') and len(emp_num_clean) <= 12) or
                    ('/' in emp_num_clean and len(emp_num_digits_only) >= 7)):
                    
                    if pd.isna(current_id) or str(current_id).strip() == '':
                        # ID is empty - just move it
                        df.loc[idx, 'ID'] = emp_num_clean
                        df.loc[idx, 'Employee Number'] = None
                        moved_count += 1
                    else:
                        # ID has data - check if current ID looks corrupted/invalid
                        current_id_str = str(current_id).strip()
                        
                        # Replace if current ID looks invalid (contains spaces, special chars, etc.)
                        if (len(current_id_str) < 6 or  # Too short for ID
                            ' ' in current_id_str or    # Contains spaces
                            any(c in current_id_str for c in ['/', '(', ')', "'", ',', 'j', 'H', 'O', 'D', 'S', 'N']) or  # Contains obvious OCR errors
                            not any(c.isdigit() for c in current_id_str)):  # No digits at all
                            
                            print(f"    Replacing invalid ID '{current_id_str}' with '{emp_num_clean}'")
                            df.loc[idx, 'ID'] = emp_num_clean
                            df.loc[idx, 'Employee Number'] = None
                            replaced_count += 1
        
        if moved_count > 0:
            print(f"  → Moved {moved_count} Employee Numbers to empty ID fields")
        if replaced_count > 0:
            print(f"  → Replaced {replaced_count} invalid IDs with Employee Numbers")
        if moved_count == 0 and replaced_count == 0:
            print("  → No Employee Numbers needed to be moved")
        
        return df

if __name__ == "__main__":
    # Example usage
    normalizer = ColumnNormalizer()
    
    # Show current mapping
    normalizer.show_current_mapping()
    
    # Example: Add new mapping
    # normalizer.add_column_mapping("Phone Number", ["טלפון", "Phone", "Mobile", "נייד"])

