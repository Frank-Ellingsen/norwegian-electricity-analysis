import os
import pandas as pd
import logging
from catboost import CatBoostRegressor
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def train_model(train_df: pd.DataFrame, target_col: str = 'price') -> CatBoostRegressor:
    """
    Trains a CatBoost model using the provided DataFrame.
    Saves the trained model and its feature importance.
    """
    logging.info("Starting model training for a single zone (NO2).")
    
    # Categorical features as defined in GEMINI.md
    cat_features = ['hour', 'weekday', 'month', 'is_weekend']
    
    # Ensure target_col is not in features
    feature_cols = [col for col in train_df.columns if col not in [target_col, 'zone']]
    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    
    if X_train.empty or y_train.empty:
        logging.error("❌ Training DataFrame is empty. Cannot train model.")
        return None

    # Ensure categorical features are treated as such
    current_cat_features = [f for f in cat_features if f in X_train.columns]
    for col in current_cat_features:
        X_train[col] = X_train[col].astype(int)

    model = CatBoostRegressor(
        iterations=1000,
        learning_rate=0.05,
        depth=6,
        loss_function='RMSE',
        verbose=0, # Set to 0 to avoid verbose output during training
        random_seed=42, # For reproducibility
        early_stopping_rounds=50 # Stop if validation metric doesn't improve for 50 rounds
    )
    
    try:
        # For simplicity, using X_train as eval_set. In production, use a separate validation set.
        model.fit(X_train, y_train, cat_features=current_cat_features, eval_set=(X_train, y_train))
        
        # Save Model
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_dir = os.path.join(base_path, "models")
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, f"catboost_no2.cbm") # Specific to NO2
        model.save_model(model_path)
        logging.info(f"✅ Model trained and saved to {model_path}")
        
        # Save Feature Importance
        importance = model.get_feature_importance()
        feature_names = X_train.columns
        importance_df = pd.DataFrame({'feature': feature_names, 'importance': importance}).sort_values(by='importance', ascending=False)
        
        output_dir = os.path.join(base_path, "output")
        os.makedirs(output_dir, exist_ok=True)
        importance_path = os.path.join(output_dir, f"feature_importance_no2.csv") # Specific to NO2
        importance_df.to_csv(importance_path, index=False)
        logging.info(f"✅ Feature importance saved to {importance_path}")
        
        return model
        
    except Exception as e:
        logging.error(f"❌ Error training model: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_path, "data", "features_no2.csv")
    
    logging.info(f"Loading data from {data_path}")
    if not os.path.exists(data_path):
        logging.error(f"Data file not found at {data_path}. Please run feature_engineering.py first.")
    else:
        try:
            df = pd.read_csv(data_path, index_col=0, parse_dates=True)
            
            # Assuming the data is already filtered for NO2 or 'zone' column is handled upstream
            # For demonstration, we will assume df is ready for training.
            
            trained_model = train_model(df)
            
            if trained_model:
                logging.info("Dummy model training completed successfully in example usage.")
            else:
                logging.warning("Dummy model training failed in example usage.")
        except Exception as e:
            logging.error(f"An error occurred during example training: {e}")
            import traceback
            traceback.print_exc()