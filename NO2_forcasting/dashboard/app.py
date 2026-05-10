import streamlit as st
import sqlite3
import pandas as pd
import os
import plotly.express as px

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_PATH, "data/sqlite/forecast_tracking.db")

st.set_page_config(layout="wide") # Use wide layout for better visualization

st.title("⚡ NO2 Electricity Price Forecast Dashboard")

@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    
    # Load forecast_evaluation data
    df_eval = pd.read_sql("SELECT * FROM forecast_evaluation", conn)
    df_eval['timestamp'] = pd.to_datetime(df_eval['timestamp'])
    
    # Load forecast_predictions data
    df_pred = pd.read_sql("SELECT * FROM forecast_predictions", conn)
    df_pred['timestamp'] = pd.to_datetime(df_pred['timestamp'])
    df_pred['origin_timestamp'] = pd.to_datetime(df_pred['origin_timestamp'])
    
    conn.close()
    return df_eval, df_pred

df_eval, df_pred = load_data()

# --- Sidebar Filters ---
st.sidebar.header("Filters")
available_zones = df_eval['zone'].unique()
if len(available_zones) > 0:
    zone = st.sidebar.selectbox("Select Zone", available_zones, index=0)
    df_eval = df_eval[df_eval['zone'] == zone]
    df_pred = df_pred[df_pred['zone'] == zone]
else:
    st.warning("No data available for evaluation or predictions.")
    st.stop()


# Date range filter for evaluation data
min_eval_date = df_eval['timestamp'].min().date() if not df_eval.empty else None
max_eval_date = df_eval['timestamp'].max().date() if not df_eval.empty else None

if min_eval_date and max_eval_date:
    start_date = st.sidebar.date_input("Start Date (Evaluation)", value=min_eval_date)
    end_date = st.sidebar.date_input("End Date (Evaluation)", value=max_eval_date)
    
    if start_date <= end_date:
        df_eval = df_eval[(df_eval['timestamp'].dt.date >= start_date) & (df_eval['timestamp'].dt.date <= end_date)]
    else:
        st.sidebar.error("Error: Start date must be before or equal to end date.")
        st.stop()
else:
    st.sidebar.info("Adjust evaluation data filters if available.")

# --- Metrics ---
st.subheader("📊 Evaluation Metrics")
if not df_eval.empty:
    col1, col2, col3 = st.columns(3)
    with col1:
        mae = df_eval['abs_error'].mean()
        st.metric("Mean Absolute Error (MAE)", f"{mae:.2f}")
    with col2:
        rmse = (df_eval['error']**2).mean()**0.5
        st.metric("Root Mean Squared Error (RMSE)", f"{rmse:.2f}")
    with col3:
        # MAPE calculation - avoid division by zero
        df_eval_mape = df_eval[df_eval['actual_price'] != 0]
        if not df_eval_mape.empty:
            mape = (df_eval_mape['abs_error'] / df_eval_mape['actual_price']).mean() * 100
            st.metric("Mean Absolute Percentage Error (MAPE)", f"{mape:.2f}%")
        else:
            st.metric("Mean Absolute Percentage Error (MAPE)", "N/A (actual prices are zero)")
else:
    st.info("No evaluation data to display metrics.")

# --- Forecast vs Actual Plot ---
st.subheader("📉 Actual vs Predicted Prices Over Time")
if not df_eval.empty:
    fig_eval = px.line(
        df_eval,
        x="timestamp",
        y=["actual_price", "predicted_price"],
        title="Actual vs Predicted Prices",
        labels={"value": "Price", "timestamp": "Date/Time"},
        line_dash_map={"actual_price": "solid", "predicted_price": "dash"}
    )
    fig_eval.update_layout(hovermode="x unified")
    st.plotly_chart(fig_eval, use_container_width=True)
else:
    st.info("No evaluation data to plot actual vs predicted prices.")

# --- Latest 30-Day Forecast ---
st.subheader("🔮 Latest 30-Day Forecast")
if not df_pred.empty:
    latest_run_origin_timestamps = df_pred['origin_timestamp'].unique()
    if len(latest_run_origin_timestamps) > 0:
        latest_run_origin_timestamp = max(latest_run_origin_timestamps)
        st.write(f"Forecast generated from origin: {latest_run_origin_timestamp}")
        df_latest_forecast = df_pred[df_pred['origin_timestamp'] == latest_run_origin_timestamp]
        
        fig_forecast = px.line(
            df_latest_forecast,
            x="timestamp",
            y="predicted_price",
            title=f"30-Day Forecast from {latest_run_origin_timestamp.strftime('%Y-%m-%d %H:%M')}",
            labels={"predicted_price": "Predicted Price", "timestamp": "Date/Time"}
        )
        fig_forecast.update_layout(hovermode="x unified")
        st.plotly_chart(fig_forecast, use_container_width=True)
    else:
        st.info("No forecast runs available in the predictions data.")
else:
    st.info("No predictions data to display the latest forecast.")

# --- Lead-Time Analysis (Error by Lead Hour) ---
st.subheader("📈 Error by Forecast Lead Hour")
if not df_eval.empty:
    error_by_lead_hour = df_eval.groupby('lead_hours')['abs_error'].mean().reset_index()
    fig_lead_hour = px.line(
        error_by_lead_hour,
        x="lead_hours",
        y="abs_error",
        title="Mean Absolute Error by Forecast Lead Hour",
        labels={"lead_hours": "Lead Hours (Forecast Horizon)", "abs_error": "Mean Absolute Error"}
    )
    fig_lead_hour.update_traces(mode='lines+markers')
    st.plotly_chart(fig_lead_hour, use_container_width=True)
else:
    st.info("No evaluation data to perform lead-time analysis.")

# --- Raw Data Display ---
st.subheader("📋 Raw Evaluation Data")
if st.checkbox("Show raw evaluation data"):
    st.dataframe(df_eval.head())

st.subheader("📋 Raw Prediction Data")
if st.checkbox("Show raw prediction data"):
    st.dataframe(df_pred.head())