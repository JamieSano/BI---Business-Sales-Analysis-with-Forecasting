import streamlit as st
import pandas as pd
import altair as alt
from datetime import date
from prophet import Prophet  # Import Prophet for time series forecasting
from streamlit_extras.metric_cards import style_metric_cards

# Page layout
st.set_page_config(page_title="Analytics", page_icon="🌎", layout="wide")

# Streamlit theme=none
theme_plotly = None

# Sidebar logo
st.sidebar.image("images/bi_logo.png")

# Title
st.title("⏱ ONLINE ANALYTICS DASHBOARD")

# Load CSS Style
custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600&display=swap');

[data-testid=metric-container] {
    box-shadow: 0 0 1px #044f4f;
    padding: 1px;
    color: rgb(255, 255, 255);
    overflow-wrap: break-word;
    white-space: break-spaces;
    font-size: 100%;
    font-family: 'Montserrat', sans-serif;
}

.plot-container>div {
    box-shadow: 0 0 5px #140e0e;
    padding: 3px;
    border-width: 3px;
}

div[data-testid="stDataframe"] div[role="button"] p {
    font-size: 1.3rem;
    color: rgb(1, 84, 84);
    font-family: 'Montserrat', sans-serif;
}
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)
# Navigation
page = st.sidebar.selectbox("Choose a page", ["Home", "Analytics"])

# Splash screen function
def splash_screen():
    st.title("Welcome to the Analytics Dashboard")
    st.write("""
    ## Instructions:
    - Please upload your Excel file using the file uploader on the left sidebar.
    - Once uploaded, the dashboard will display analytics and insights based on the data in your file.
    """)
# File uploader
uploaded_file = st.sidebar.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    # Load dataset
    df = pd.read_excel(uploaded_file, sheet_name="Transactions")

    # Convert transaction_date to datetime
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])

    # Extract hour and day of week
    df['hour'] = df['transaction_date'].dt.hour
    df['day_of_week'] = df['transaction_date'].dt.day_name()

    # Date filter
    start_date = st.sidebar.date_input("Start Date", min(df['transaction_date']).date())
    end_date = st.sidebar.date_input(label="End Date")

    # Filter data by date
    df2 = df[(df['transaction_date'] >= pd.Timestamp(start_date)) & (df['transaction_date'] <= pd.Timestamp(end_date))]

    # Sidebar filters
    st.sidebar.header("Please filter")
    city = st.sidebar.multiselect(
        "Select Store Location",
        options=df2["store_location"].unique(),
        default=df2["store_location"].unique(),
    )
    category = st.sidebar.multiselect(
        "Select Category",
        options=df2["product_category"].unique(),
        default=df2["product_category"].unique(),
    )
    product_type = st.sidebar.multiselect(
        "Select Type",
        options=df2["product_type"].unique(),
        default=df2["product_type"].unique(),
    )

    df_selection = df2.query(
        "store_location == @city & product_category == @category & product_type == @product_type"
    )

    # Calculate most and least sold products
    product_sales = df_selection.groupby('product_detail')['transaction_qty'].sum().reset_index()
    most_sold_product = product_sales.loc[product_sales['transaction_qty'].idxmax()]
    least_sold_product = product_sales.loc[product_sales['transaction_qty'].idxmin()]

    # Calculate most sold product type
    type_sales = df_selection.groupby('product_type')['transaction_qty'].sum().reset_index()
    most_sold_type = type_sales.loc[type_sales['transaction_qty'].idxmax()]

    # Calculate most sold product category
    category_sales = df_selection.groupby('product_category')['transaction_qty'].sum().reset_index()
    most_sold_category = category_sales.loc[category_sales['transaction_qty'].idxmax()]

    # Calculate the busiest hour
    hour_sales = df_selection.groupby(df_selection['transaction_date'].dt.hour)['transaction_qty'].sum().reset_index()
    busiest_hour = hour_sales.loc[hour_sales['transaction_qty'].idxmax()]

    # Calculate the busiest day of the week
    day_sales = df_selection.groupby('day_of_week')['transaction_qty'].sum().reset_index()
    busiest_day = day_sales.loc[day_sales['transaction_qty'].idxmax()]

    # Calculate sales per store location
    location_sales = df_selection.groupby('store_location')['transaction_qty'].sum().reset_index()

    # Calculate percentage of total sales for each location
    total_sales = location_sales['transaction_qty'].sum()
    location_sales['percentage'] = (location_sales['transaction_qty'] / total_sales) * 100

    # Calculate revenue
    df_selection['revenue'] = df_selection['transaction_qty'] * df_selection['unit_price']

    # Aggregate revenue by date
    revenue_df = df_selection.groupby(pd.Grouper(key='transaction_date', freq='D')).agg({'revenue': 'sum'}).reset_index()

    # Time series forecasting with Prophet
    # Rename columns as Prophet expects 'ds' and 'y' column names
    revenue_df = revenue_df.rename(columns={'transaction_date': 'ds', 'revenue': 'y'})

    # Train Prophet model for revenue
    revenue_model = Prophet()
    revenue_model.fit(revenue_df)

    # Make future predictions for revenue
    revenue_future = revenue_model.make_future_dataframe(periods=30)  # Predict revenue for the next 30 days
    revenue_forecast = revenue_model.predict(revenue_future)

    # Aggregate unit price by date
    price_df = df_selection.groupby(pd.Grouper(key='transaction_date', freq='D')).agg({'unit_price': 'mean'}).reset_index()

    # Rename columns as Prophet expects 'ds' and 'y' column names
    price_df = price_df.rename(columns={'transaction_date': 'ds', 'unit_price': 'y'})

    # Train Prophet model for unit price
    price_model = Prophet()
    price_model.fit(price_df)

    # Make future predictions for unit price
    price_future = price_model.make_future_dataframe(periods=30)  # Predict unit price for the next 30 days
    price_forecast = price_model.predict(price_future)

    # Metrics
    st.subheader('Key Performance')

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="⏱ Total Items Sold", value=df_selection.product_detail.count(), delta="Number of Items Sold")
    col2.metric(label="⏱ Sum of Product Total Price USD:", value=f"{df_selection.unit_price.sum():,.0f}", delta=df_selection.unit_price.median())
    col3.metric(label="⏱ Maximum Price USD:", value=f"{df_selection.unit_price.max():,.0f}", delta="High Price")
    col4.metric(label="⏱ Minimum Price USD:", value=f"{df_selection.unit_price.min():,.0f}", delta="Low Price")
    style_metric_cards(background_color="#00588E", border_left_color="#FF4B44", border_color="#1f66bd", box_shadow="#F71938")

    col5, col6 = st.columns(2)
    col5.metric(label="🚀 Most Sold Product", value=most_sold_product['product_detail'], delta=int(most_sold_product['transaction_qty']))
    col6.metric(label="🐢 Least Sold Product", value=least_sold_product['product_detail'], delta=int(least_sold_product['transaction_qty']))
    
    col7, col8 = st.columns(2)
    col7.metric(label="🚀 Most Sold Product Type", value=most_sold_type['product_type'], delta=int(most_sold_type['transaction_qty']))
    col8.metric(label="🚀 Most Sold Product Category", value=most_sold_category['product_category'], delta=int(most_sold_category['transaction_qty']))

    col9, col10 = st.columns(2)
    col9.metric(label="⏰ Busiest Hour", value=f"{busiest_hour['transaction_date']}h", delta=int(busiest_hour['transaction_qty']))
    col10.metric(label="📅 Busiest Day", value=busiest_day['day_of_week'], delta=int(busiest_day['transaction_qty']))

    coll1, coll2 = st.columns(2)
    coll1.info("Business Metrics between [" + str(start_date) + "] and [" + str(end_date) + "]")

    # Bar chart
    with coll1:
        st.subheader("Product by Quantity")
        source = pd.DataFrame({
            "Quantity ($)": df_selection["transaction_qty"],
            "Product": df_selection["product_category"]
        })

        bar_chart = alt.Chart(source).mark_bar().encode(
            x="sum(Quantity ($)):Q",
            y=alt.Y("Product:N", sort="-x")
        ).properties(
            width='container',
            height=400
        ).configure_axis(
            grid=False
        ).configure_view(
            strokeWidth=0
        ).configure_mark(
            color='blue'
        )
        st.altair_chart(bar_chart, use_container_width=True, theme=theme_plotly)

    # Progress Bar
    def Progressbar():
        st.markdown("""<style>.stProgress > div > div > div > div { background-image: linear-gradient(to right, #99ff99 , #FFFF00)}</style>""", unsafe_allow_html=True)
        target = 30000000
        current = df_selection["unit_price"].sum()
        percent = round((current / target) * 100)
        mybar = st.progress(0)
        if percent > 100:
            st.subheader("Target achieved!")
        else:
            st.write(f"You have {percent}% of {target:,} USD")
        mybar.progress(min(percent, 100))  # Ensure the progress doesn't exceed 100%

    with coll1:
        st.subheader("Target Percentage")
        Progressbar()

    # Pie chart for sales per store location
    with coll2:
        st.subheader("Sales per Store Location")
        pie_chart = alt.Chart(location_sales).mark_arc().encode(
            theta=alt.Theta(field="transaction_qty", type="quantitative"),
            color=alt.Color(field="store_location", type="nominal"),
            tooltip=["store_location", "transaction_qty", alt.Tooltip('percentage:Q', format='.1f', title='Percentage')]
        ).properties(
            width=400,
            height=400
        )
        st.altair_chart(pie_chart, use_container_width=True, theme=theme_plotly)

    # Bar chart for product order date by quantity
    with coll2: 
        st.subheader("Product Order Date by Quantity")
        data = {
            'Category': df_selection['transaction_date'],
            'Value': df_selection['transaction_qty'],
        }
        df = pd.DataFrame(data)
        st.bar_chart(df.set_index('Category')['Value'], use_container_width=True, width=600, height=600)

    # Revenue forecast plot
    st.subheader("Revenue Forecast")
    st.write(revenue_forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']])

    fig_revenue = revenue_model.plot(revenue_forecast)
    st.write(fig_revenue)

    # Price forecast plot
    st.subheader("Price Forecast")
    st.write(price_forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']])

    fig_price = price_model.plot(price_forecast)
    st.write(fig_price)

    # Show a table of the transactions
    st.subheader("Transactions Table")
    st.write(df_selection)

else:
    st.sidebar.warning("Please upload an Excel file to proceed.")
    splash_screen()

# Function to process and analyze files for the analytics page
def process_and_analyze_file(uploaded_file1, uploaded_file2):
    df1 = process_file(uploaded_file1)
    df2 = process_file(uploaded_file2)
    
    if df1 is not None and df2 is not None:
        st.subheader('Key Performance Metrics for First File')
        metrics1 = calculate_metrics(df1)

        col1, col2 = st.columns(2)
        col1.metric(label="Total Items Sold", value=df1.product_detail.count(), delta="Number of Items Sold")
        col2.metric(label="Sum of Product Total Price USD", value=f"{df1.unit_price.sum():,.0f}", delta="Total Price")

        st.subheader('Key Performance Metrics for Second File')
        metrics2 = calculate_metrics(df2)

        col3, col4 = st.columns(2)
        col3.metric(label="Total Items Sold", value=df2.product_detail.count(), delta="Number of Items Sold")
        col4.metric(label="Sum of Product Total Price USD", value=f"{df2.unit_price.sum():,.0f}", delta="Total Price")

        # Print Button
        print_button()

# Function to print the page
def print_button():
    st.markdown("""
        <button onclick="window.print()">Print this page</button>
        <style>
            button {
                background-color: #00588E;
                color: white;
                border: none;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 12px;
            }
        </style>
    """, unsafe_allow_html=True)

def analytics_page():
    st.title("Analytics Page")
    st.sidebar.subheader("Upload your Excel files")
    
    uploaded_file1 = st.sidebar.file_uploader("Choose the first file", type=["xlsx"], key="file_uploader_analytics_1")
    uploaded_file2 = st.sidebar.file_uploader("Choose the second file", type=["xlsx"], key="file_uploader_analytics_2")
    
    if uploaded_file1 and uploaded_file2:
        process_and_analyze_file(uploaded_file1, uploaded_file2)
    else:
        st.sidebar.warning("Please upload both Excel files to proceed.")

# Main logic for page selection
if page == "Home":
    home_page()
elif page == "Analytics":
    analytics_page()
