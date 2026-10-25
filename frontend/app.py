import streamlit as st
import pandas as pd
import requests

# Base URL of the Flask backend (container name on the Docker network)
BACKEND_URL = "http://backend:7860"

# Reference year used to compute the age of the store (same as in training)
CURRENT_YEAR = 2025

# Product types that are considered perishable (same grouping as in training)
PERISHABLES = ["Dairy", "Meat", "Fruits and Vegetables", "Breakfast", "Breads", "Seafood"]
PRODUCT_TYPES = ["Baking Goods", "Breads", "Breakfast", "Canned", "Dairy", "Frozen Foods",
                 "Fruits and Vegetables", "Hard Drinks", "Health and Hygiene", "Household", "Meat",
                 "Others", "Seafood", "Snack Foods", "Soft Drinks", "Starchy Foods"]

# Set the title of the Streamlit app
st.set_page_config(page_title="SuperKart Sales Forecast", page_icon="🛒")
st.title("SuperKart – Product Sales Forecast")
st.write("Estimate the total revenue of a product in a given store for the upcoming quarter.")

# ----------------------------------------------------------------------
# Section for online prediction
# ----------------------------------------------------------------------
st.subheader("Online Prediction")

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Product attributes**")
    product_id = st.text_input("Product Id (e.g. FD6114, DR1234, NC5678)", value="FD6114")
    product_weight = st.number_input("Product Weight", min_value=1.0, max_value=30.0, value=12.66, step=0.01)
    product_sugar = st.selectbox("Product Sugar Content", ["Low Sugar", "Regular", "No Sugar"])
    product_area = st.number_input("Product Allocated Area (ratio)", min_value=0.0, max_value=1.0, value=0.027, step=0.001, format="%.3f")
    product_type = st.selectbox("Product Type", PRODUCT_TYPES)
    product_mrp = st.number_input("Product MRP", min_value=1.0, max_value=500.0, value=117.08, step=0.01)
with col2:
    st.markdown("**Store attributes**")
    store_year = st.number_input("Store Establishment Year", min_value=1950, max_value=CURRENT_YEAR, value=2009, step=1)
    store_size = st.selectbox("Store Size", ["Small", "Medium", "High"])
    store_city = st.selectbox("Store Location City Type", ["Tier 1", "Tier 2", "Tier 3"])
    store_type = st.selectbox("Store Type", ["Departmental Store", "Supermarket Type1", "Supermarket Type2", "Food Mart"])

# Feature engineering (must match the training notebook)
product_id_char = product_id.strip()[:2].upper()
store_age_years = CURRENT_YEAR - store_year
product_type_category = "Perishables" if product_type in PERISHABLES else "Non Perishables"

# Convert user input into the payload expected by the API
input_data = {
    "Product_Weight": product_weight,
    "Product_Sugar_Content": product_sugar,
    "Product_Allocated_Area": product_area,
    "Product_MRP": product_mrp,
    "Store_Size": store_size,
    "Store_Location_City_Type": store_city,
    "Store_Type": store_type,
    "Product_Id_char": product_id_char,
    "Store_Age_Years": int(store_age_years),
    "Product_Type_Category": product_type_category,
}

# Make prediction when the "Predict" button is clicked
if st.button("Predict", type="primary"):
    try:
        response = requests.post(f"{BACKEND_URL}/v1/predict", json=input_data, timeout=30)  # Send data to Flask API
        if response.status_code == 200:
            prediction = response.json()["Predicted Sales Total"]
            st.success(f"Predicted total sales for this product in this store: {prediction:,.2f}")
        else:
            st.error(f"The prediction API returned status code {response.status_code}.")
    except requests.exceptions.RequestException:
        st.error("Unable to connect to the prediction API.")

# ----------------------------------------------------------------------
# Section for batch prediction
# ----------------------------------------------------------------------
st.subheader("Batch Prediction")
st.write("Upload a CSV file with the columns: Product_Weight, Product_Sugar_Content, Product_Allocated_Area, "
         "Product_MRP, Store_Size, Store_Location_City_Type, Store_Type, Product_Id_char, Store_Age_Years, "
         "Product_Type_Category.")

# Allow users to upload a CSV file for batch prediction
uploaded_file = st.file_uploader("Upload CSV file for batch prediction", type=["csv"])

# Make batch prediction when the "Predict Batch" button is clicked
if uploaded_file is not None:
    if st.button("Predict Batch", type="primary"):
        try:
            response = requests.post(f"{BACKEND_URL}/v1/predictbatch", files={"file": uploaded_file}, timeout=120)  # Send file to Flask API
            if response.status_code == 200:
                predictions = response.json()
                st.success("Batch predictions completed!")
                uploaded_file.seek(0)
                result = pd.read_csv(uploaded_file)
                result["Predicted_Sales_Total"] = [predictions[str(i)] for i in range(len(result))]
                st.dataframe(result)  # Display the predictions next to the inputs
                st.download_button("Download predictions as CSV", result.to_csv(index=False).encode("utf-8"),
                                   file_name="superkart_predictions.csv", mime="text/csv")
            else:
                st.error(f"The prediction API returned status code {response.status_code}.")
        except requests.exceptions.RequestException:
            st.error("Unable to connect to the prediction API.")
