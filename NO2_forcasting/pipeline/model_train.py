import os
import pandas as pd
import logging
from catboost import CatBoostRegressor
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def train_models_per_zone(train_dfs: dict, target_col: str = 'price'):
    """
    Trains CatBoost models for each zone provided in the train_dfs dictionary.
    Each model is saved with a zone-specific filename.
    """
    logging.info("Starting model training for each zone.")
    
    # Categorical features as defined in GEMINI.md
    cat_features = ['hour', 'weekday', 'month', 'is_weekend']
    
    trained_models = {}

    for zone, train_df in train_dfs.items():
        logging.info(f"Training model for zone: {zone}")

        # Drop 'zone' column as it's constant for this specific model
        # Ensure target_col is also not in features
        feature_cols = [col for col in train_df.columns if col not in [target_col, 'zone']]
        X_train = train_df[feature_cols]
        y_train = train_df[target_col]
        
        if X_train.empty or y_train.empty:
            logging.warning(f"Skipping training for zone {zone}: Training data is empty.")
            continue

        # Ensure categorical features are treated as such
        current_cat_features = [f for f in cat_features if f in X_train.columns]
        for col in current_cat_features:
            X_train[col] = X_train[col].astype(int)

        model = CatBoostRegressor(
            iterations=1000,
            learning_rate=0.05,
            depth=6,
            loss_function='RMSE',
            verbose=0, # Set to 0 to avoid verbose output during multiple training runs
            random_seed=42 # For reproducibility
        )
        
        try:
            model.fit(X_train, y_train, cat_features=current_cat_features, early_stopping_rounds=50, eval_set=(X_train, y_train))
            
            # Save Model
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_dir = os.path.join(base_path, "models")
            os.makedirs(model_dir, exist_ok=True)
            model_path = os.path.join(model_dir, f"catboost_{zone}.cbm")
            model.save_model(model_path)
            logging.info(f"Model for zone {zone} trained and saved to {model_path}")
            trained_models[zone] = model
            
            # Save Feature Importance
            importance = model.get_feature_importance()
            feature_names = X_train.columns
            importance_df = pd.DataFrame({'feature': feature_names, 'importance': importance}).sort_values(by='importance', ascending=False)
            
            output_dir = os.path.join(base_path, "output")
            os.makedirs(output_dir, exist_ok=True)
            importance_path = os.path.join(output_dir, f"feature_importance_{zone}.csv")
            importance_df.to_csv(importance_path, index=False)
            logging.info(f"Feature importance for zone {zone} saved to {importance_path}")
            
        except Exception as e:
            logging.error(f"Error training model for zone {zone}: {e}")
            import traceback
            traceback.print_exc()
            continue

    logging.info("Finished training models for all zones.")
    return trained_models

if __name__ == "__main__":
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_path, "data", "features_no2.csv")
    
    logging.info(f"Loading data from {data_path}")
    if not os.path.exists(data_path):
        logging.error(f"Data file not found at {data_path}. Please run feature_engineering.py first.")
    else:
        try:
            df = pd.read_csv(data_path, index_col=0, parse_dates=True)
            
            # Ensure 'zone' column is available for splitting
            if 'zone' not in df.columns:
                if 'zone' in df.index.names:
                    df = df.reset_index()
                else:
                    logging.error("The loaded DataFrame does not contain a 'zone' column, and 'zone' is not in the index. Cannot perform per-zone training.")
                    exit()

            from dataset_split import split_dataset
            splits = split_dataset(df) # This now returns a dictionary {'train': train_dfs, 'test': test_dfs}
            train_dfs = splits.get('train', {})

            if train_dfs:
                train_models_per_zone(train_dfs)
            else:
                logging.warning("No training sets available after splitting. Check your data split and historical availability.")
        except Exception as e:
            logging.error(f"An error occurred during training: {e}")
            import traceback
            traceback.print_exc()
