import os
import pandas as pd
import logging
from catboost import CatBoostRegressor
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def train_model(train_df: pd.DataFrame, target_col: str = 'price'):
    """
    Trains a CatBoost model on the provided training data.
    """
    logging.info("Starting model training.")
    
    # Categorical features as defined in GEMINI.md
    cat_features = ['hour', 'weekday', 'month', 'is_weekend']
    
    X_train = train_df.drop(columns=[target_col])
    y_train = train_df[target_col]
    
    # Ensure categorical features are treated as such
    for col in cat_features:
        if col in X_train.columns:
            X_train[col] = X_train[col].astype(int)

    model = CatBoostRegressor(
        iterations=1000,
        learning_rate=0.05,
        depth=6,
        loss_function='RMSE',
        verbose=100
    )
    
    model.fit(X_train, y_train, cat_features=cat_features)
    
    # Save Model
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(base_path, "models", "catboost_no2.cbm")
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    model.save_model(model_path)
    
    # Save Feature Importance
    importance = model.get_feature_importance()
    feature_names = X_train.columns
    importance_df = pd.DataFrame({'feature': feature_names, 'importance': importance}).sort_values(by='importance', ascending=False)
    
    output_path = os.path.join(base_path, "output", "feature_importance.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    importance_df.to_csv(output_path, index=False)
    
    logging.info(f"Model trained and saved. Feature importance saved to {output_path}")
    return model

if __name__ == "__main__":
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_path, "data", "features_no2.csv")
    
    logging.info(f"Loading data from {data_path}")
    if not os.path.exists(data_path):
        logging.error(f"Data file not found at {data_path}. Please run run_pipeline.py first.")
    else:
        try:
            df = pd.read_csv(data_path, index_col=0, parse_dates=True)
            from dataset_split import split_dataset
            train, _ = split_dataset(df)
            if not train.empty:
                train_model(train)
            else:
                logging.warning("Training set is empty. Check your data split and historical availability.")
        except Exception as e:
            logging.error(f"An error occurred during training: {e}")
            import traceback
            traceback.print_exc()
