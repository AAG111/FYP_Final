import pandas as pd
import numpy as np
import os

try:
    from load_fitness_tracker_dataset import FitnessTrackerLoader
except:
    FitnessTrackerLoader = None

class KaggleDatasetPreprocessor:
    """Convert Kaggle dataset to preexisting training data"""
    
    def __init__(self):
        if FitnessTrackerLoader is None:
            print("⚠️ FitnessTrackerLoader not available")
            self.loader = None
        else:
            self.loader = FitnessTrackerLoader()
        self.training_data = None
    
    def prepare_foundation_data(self):
        """Prepare data for foundation model"""
        if self.loader is None:
            print("⚠️ Loader not initialized")
            return None
        
        self.training_data = self.loader.create_training_data()
        
        # Split by difficulty
        easy_data = self.training_data[self.training_data['difficulty'] == 0]
        medium_data = self.training_data[self.training_data['difficulty'] == 1]
        hard_data = self.training_data[self.training_data['difficulty'] == 2]
        
        # Convert to tuples
        easy_tuples = [
            (row['form_score'], row['heart_rate'], row['spo2'], row['stress'], 
             row['completion'], row['form_trend'])
            for _, row in easy_data.iterrows()
        ]
        
        medium_tuples = [
            (row['form_score'], row['heart_rate'], row['spo2'], row['stress'], 
             row['completion'], row['form_trend'])
            for _, row in medium_data.iterrows()
        ]
        
        hard_tuples = [
            (row['form_score'], row['heart_rate'], row['spo2'], row['stress'], 
             row['completion'], row['form_trend'])
            for _, row in hard_data.iterrows()
        ]
        
        return {
            'easy': easy_tuples,
            'medium': medium_tuples,
            'hard': hard_tuples,
        }
    
    def get_numpy_arrays(self):
        """Get training arrays"""
        if self.loader is None:
            print("⚠️ Loader not initialized")
            return np.array([]).reshape(0, 6), np.array([])
        
        return self.loader.get_numpy_arrays(self.training_data)

def get_preexisting_training_data():
    """Load Kaggle data as preexisting foundation"""
    processor = KaggleDatasetPreprocessor()
    
    if processor.loader is None:
        print("⚠️ Using fallback data")
        # Fallback data if Kaggle dataset not available
        X = np.array([
            [65, 85, 94, 72, 0.8, 0.5],
            [68, 88, 93, 75, 0.6, 0.6],
            [75, 110, 93, 55, 1.5, 0.8],
            [78, 108, 94, 52, 1.7, 0.85],
            [87, 135, 96, 35, 2.5, 0.95],
            [90, 132, 97, 30, 2.8, 0.98],
        ])
        y = np.array([0, 0, 1, 1, 2, 2])
        return X, y
    
    processor.training_data = processor.loader.create_training_data()
    
    X = processor.training_data[['form_score', 'heart_rate', 'spo2', 'stress', 'completion', 'form_trend']].values
    y = processor.training_data['difficulty'].values
    
    return np.array(X), np.array(y)

def get_preexisting_data_by_difficulty(difficulty):
    """Get preexisting data for specific difficulty"""
    processor = KaggleDatasetPreprocessor()
    
    if processor.loader is None:
        return np.array([]).reshape(0, 6)
    
    processor.training_data = processor.loader.create_training_data()
    
    if difficulty == 'easy':
        data = processor.training_data[processor.training_data['difficulty'] == 0]
    elif difficulty == 'medium':
        data = processor.training_data[processor.training_data['difficulty'] == 1]
    else:
        data = processor.training_data[processor.training_data['difficulty'] == 2]
    
    X = data[['form_score', 'heart_rate', 'spo2', 'stress', 'completion', 'form_trend']].values
    
    return np.array(X)

if __name__ == '__main__':
    processor = KaggleDatasetPreprocessor()
    foundation = processor.prepare_foundation_data()
    
    if foundation:
        print('✅ Foundation data prepared:')
        print(f'   Easy: {len(foundation["easy"])} samples')
        print(f'   Medium: {len(foundation["medium"])} samples')
        print(f'   Hard: {len(foundation["hard"])} samples')
    else:
        print('⚠️ Using fallback data')
    
    X, y = get_preexisting_training_data()
    print(f'\n✅ NumPy arrays:')
    print(f'   X shape: {X.shape}')
    print(f'   y shape: {y.shape}')