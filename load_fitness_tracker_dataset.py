import pandas as pd
import numpy as np
from datetime import datetime
import os

class FitnessTrackerLoader:
    """Load and process the Fitness Tracker Dataset from Kaggle"""
    
    def __init__(self, folder_path='.'):
        self.folder_path = folder_path
        self.df = None
        self.columns_info = {}
        self.load_dataset()
    
    def load_dataset(self):
        """Load all CSV files and explore structure"""
        
        # Find all CSV files
        csv_files = [f for f in os.listdir(self.folder_path) if f.endswith('.csv')]
        
        print('📊 Available CSV files:')
        for file in csv_files:
            print(f'   - {file}')
        
        if not csv_files:
            print('❌ No CSV files found!')
            return
        
        # Try to load the main dataset
        main_file = None
        for file in csv_files:
            if 'fitness' in file.lower() or 'exercise' in file.lower() or 'data' in file.lower():
                main_file = file
                break
        
        if not main_file:
            main_file = csv_files[0]
        
        print(f'\n✅ Loading: {main_file}')
        self.df = pd.read_csv(f'{self.folder_path}/{main_file}')
        
        self._explore_structure()
    
    def _explore_structure(self):
        """Analyze dataset structure"""
        print('\n📋 Dataset Info:')
        print(f'   Rows: {len(self.df):,}')
        print(f'   Columns: {len(self.df.columns)}')
        print(f'\n📌 Column Names & Types:')
        
        for col in self.df.columns:
            dtype = self.df[col].dtype
            non_null = self.df[col].notna().sum()
            unique = self.df[col].nunique()
            print(f'   {col}: {dtype} ({unique} unique, {non_null:,} non-null)')
        
        print(f'\n📊 Data Sample:')
        print(self.df.head(3).to_string())
        
        print(f'\n📈 Statistics:')
        print(self.df.describe().to_string())
    
    def get_column_mapping(self):
        """Map dataset columns to our model format"""
        columns = {col.lower(): col for col in self.df.columns}
        
        mapping = {
            'heart_rate': None,
            'exercise': None,
            'calories': None,
            'duration': None,
            'user': None,
            'date': None,
            'stress': None,
            'spo2': None,
            'steps': None,
            'distance': None,
        }
        
        # Auto-map columns
        for key in columns:
            if 'heart' in key or 'hr' in key or 'pulse' in key:
                mapping['heart_rate'] = columns[key]
            elif 'exercise' in key or 'activity' in key or 'type' in key:
                mapping['exercise'] = columns[key]
            elif 'calor' in key:
                mapping['calories'] = columns[key]
            elif 'duration' in key or 'minute' in key:
                mapping['duration'] = columns[key]
            elif 'user' in key or 'id' in key:
                mapping['user'] = columns[key]
            elif 'date' in key or 'time' in key:
                mapping['date'] = columns[key]
            elif 'stress' in key:
                mapping['stress'] = columns[key]
            elif 'spo2' in key or 'oxygen' in key:
                mapping['spo2'] = columns[key]
            elif 'step' in key:
                mapping['steps'] = columns[key]
            elif 'distance' in key:
                mapping['distance'] = columns[key]
        
        return {k: v for k, v in mapping.items() if v is not None}
    
    def get_users(self):
        """Get unique users"""
        mapping = self.get_column_mapping()
        if 'user' in mapping and mapping['user'] in self.df.columns:
            return self.df[mapping['user']].unique()
        return []
    
    def get_exercises(self):
        """Get unique exercises"""
        mapping = self.get_column_mapping()
        if 'exercise' in mapping and mapping['exercise'] in self.df.columns:
            return self.df[mapping['exercise']].unique()
        return []
    
    def create_training_data(self):
        """Convert dataset to training format"""
        mapping = self.get_column_mapping()
        
        print('\n🔄 Converting to training format...')
        print(f'Column mapping: {mapping}')
        
        training_data = []
        
        for idx, row in self.df.iterrows():
            try:
                # Extract values
                heart_rate = float(row.get(mapping.get('heart_rate', 'HeartRate'), 70)) if 'heart_rate' in mapping else 70
                
                # Calculate form score
                if 'calories' in mapping and mapping['calories'] in self.df.columns and pd.notna(row.get(mapping['calories'])):
                    calories = float(row.get(mapping['calories'], 200))
                    form_score = min(100, (calories / 500) * 100)
                else:
                    form_score = 70
                
                # Duration
                duration = float(row.get(mapping.get('duration', 'Duration'), 30)) if 'duration' in mapping else 30
                
                # Stress
                stress = max(0, min(100, (heart_rate / 200) * 100))
                
                # SpO2
                spo2 = float(row.get(mapping.get('spo2', 'SpO2'), 95)) if 'spo2' in mapping else 95
                
                # Completion
                if 'steps' in mapping and mapping['steps'] in self.df.columns and pd.notna(row.get(mapping['steps'])):
                    steps = float(row.get(mapping['steps'], 0))
                    completion = min(1.0, steps / 10000)
                else:
                    completion = 0.7
                
                # Form trend
                form_trend = 0.5 + (form_score / 100) * 0.5
                
                # Classify difficulty
                if form_score < 70 or heart_rate < 100:
                    difficulty = 0  # Easy
                elif form_score < 85 or heart_rate < 130:
                    difficulty = 1  # Medium
                else:
                    difficulty = 2  # Hard
                
                training_data.append({
                    'user_id': row.get(mapping.get('user', 'UserID'), 'USER_001'),
                    'exercise': row.get(mapping.get('exercise', 'Exercise'), 'Unknown'),
                    'heart_rate': max(40, min(200, heart_rate)),
                    'form_score': max(0, min(100, form_score)),
                    'spo2': max(85, min(100, spo2)),
                    'stress': max(0, min(100, stress)),
                    'duration': duration,
                    'completion': completion,
                    'form_trend': form_trend,
                    'difficulty': difficulty,
                    'calories': row.get(mapping.get('calories', 'Calories'), 0),
                })
            except Exception as e:
                continue
        
        df_training = pd.DataFrame(training_data)
        print(f'✅ Created {len(df_training)} training samples')
        print(f'   Users: {df_training["user_id"].nunique()}')
        print(f'   Exercises: {df_training["exercise"].nunique()}')
        print(f'   Distribution - Easy: {sum(df_training["difficulty"]==0)}, Medium: {sum(df_training["difficulty"]==1)}, Hard: {sum(df_training["difficulty"]==2)}')
        
        return df_training
    
    def get_numpy_arrays(self, df_training=None):
        """Convert to numpy arrays"""
        if df_training is None:
            df_training = self.create_training_data()
        
        X = df_training[['form_score', 'heart_rate', 'spo2', 'stress', 'completion', 'form_trend']].values
        y = df_training['difficulty'].values
        
        return np.array(X), np.array(y), df_training

if __name__ == '__main__':
    loader = FitnessTrackerLoader()
    
    print('\n' + '='*60)
    print('EXPLORATION RESULTS')
    print('='*60)
    
    mapping = loader.get_column_mapping()
    print(f'\nColumn Mapping: {mapping}')
    
    users = loader.get_users()
    print(f'\nUsers: {users}')
    
    exercises = loader.get_exercises()
    print(f'\nExercises: {exercises}')
    
    df_training = loader.create_training_data()
    print(f'\nTraining DataFrame:\n{df_training.head(10)}')
    
    df_training.to_csv('fitness_tracker_training_data.csv', index=False)
    print('\n💾 Saved to fitness_tracker_training_data.csv')