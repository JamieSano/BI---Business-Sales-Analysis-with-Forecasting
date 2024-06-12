import streamlit as st
import pandas as pd
import altair as alt
from datetime import date
from prophet import Prophet
from streamlit_extras.metric_cards import style_metric_cards
from PIL import Image
import base64
import seaborn as sns
import matplotlib.pyplot as plt

# Loading Image using PIL
im = Image.open('images/bi_logo.png')
# Adding Image to web app
st.set_page_config(page_title="Business Sales Analyzer", page_icon=im)

# Sidebar logo
st.sidebar.image("images/bi_logo.png")

# Function to encode the local image to base64
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

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
    border-width: 10px;
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
    # Image file path
    img_file = 'images/Home (2).png'
    img_base64 = get_base64(img_file)

    # Custom CSS for full-page background image
    page_bg_img = f'''
    <style>
    body {{
        background-image: url("data:image/png;base64,{img_base64}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    .stApp {{
        background: rgba(255, 255, 255, 0.00);  /*optional: to make content more readable */
        padding: 2rem; /* adjust padding if needed */
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)
    st.write("")  # Add any additional splash screen content here

# Cover page function
def cover_page():
    st.title("Welcome to Business Sales Analyzer")
    # Image file path
    img_file = 'images/bg.png'
    img_base64 = get_base64(img_file)

    # Custom CSS for full-page background image
    page_bg_img = f'''
    <style>
    body {{
        background-image: url("data:image/png;base64,{img_base64}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    .stApp {{
        background: rgba(255, 255, 255, 0.00);  /*optional: to make content more readable */
        padding: 2rem; /* adjust padding if needed */
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)
    st.write("Analyze your business sales with detailed metrics and visualizations.")

# Process file function
def process_file(uploaded_file):
    df = pd.read_excel(uploaded_file, sheet_name="Transactions")
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    df['hour'] = df['transaction_date'].dt.hour
    df['day_of_week'] = df['transaction_date'].dt.day_name()
    return df

# Calculate metrics function
def calculate_metrics(df):
    product_sales = df.groupby('product_detail')['transaction_qty'].sum().reset_index()
    most_sold_product = product_sales.loc[product_sales['transaction_qty'].idxmax()]
    least_sold_product = product_sales.loc[product_sales['transaction_qty'].idxmin()]
    type_sales = df.groupby('product_type')['transaction_qty'].sum().reset_index()
    most_sold_type = type_sales.loc[type_sales['transaction_qty'].idxmax()]
    category_sales = df.groupby('product_category')['transaction_qty'].sum().reset_index()
    most_sold_category = category_sales.loc[category_sales['transaction_qty'].idxmax()]
    hour_sales = df.groupby(df['transaction_date'].dt.hour)['transaction_qty'].sum().reset_index()
    busiest_hour = hour_sales.loc[hour_sales['transaction_qty'].idxmax()]
    day_sales = df.groupby('day_of_week')['transaction_qty'].sum().reset_index()
    busiest_day = day_sales.loc[day_sales['transaction_qty'].idxmax()]
    most_idle_day = day_sales.loc[day_sales['transaction_qty'].idxmin()]
    return {
        'most_sold_product': most_sold_product,
        'least_sold_product': least_sold_product,
        'most_sold_type': most_sold_type,
        'most_sold_category': most_sold_category,
        'busiest_hour': busiest_hour,
        'busiest_day': busiest_day,
        'most_idle_day': most_idle_day

    }

# Home page
def home_page():
    uploaded_file = st.sidebar.file_uploader("Upload your Excel file", type=["xlsx"])
    if uploaded_file:
        cover_page()
        df = process_file(uploaded_file)

        # Convert the time strings to datetime.time objects
        df['transaction_time'] = pd.to_datetime(df['transaction_time'], format='%H:%M:%S').dt.time
        # Add 'hour' column
        df['hour'] = pd.to_datetime(df['transaction_time'], format='%H:%M:%S').dt.hour

        # Date filter
        start_date = st.sidebar.date_input("Start Date", min(df['transaction_date']).date())
        end_date = st.sidebar.date_input("End Date", max(df['transaction_date']).date())

        # Filter data by date
        df_filtered = df[(df['transaction_date'] >= pd.Timestamp(start_date)) & (df['transaction_date'] <= pd.Timestamp(end_date))]

        # Sidebar filters
        st.sidebar.header("Please filter the data")
        city = st.sidebar.multiselect("Select Store Location", options=df_filtered["store_location"].unique(), default=df_filtered["store_location"].unique())
        category = st.sidebar.multiselect("Select Category", options=df_filtered["product_category"].unique(), default=df_filtered["product_category"].unique())
        product_type = st.sidebar.multiselect("Select Type", options=df_filtered["product_type"].unique(), default=df_filtered["product_type"].unique())

        df_selection = df_filtered.query("store_location == @city & product_category == @category & product_type == @product_type")

        if df_selection.empty:
            st.warning("No data available provided from the selection. Please select accordingly.")
        else:
            metrics = calculate_metrics(df_selection)
            # Metrics display
            st.subheader('Key Performance Metrics')

            col1, col2 = st.columns(2)
            col1.metric(label="Total Items Sold", value=df_selection.product_detail.count())
            col2.metric(label="Sum of Product Total Price USD", value=f"{df_selection.unit_price.sum():,.0f}")

            col3, col4 = st.columns(2)
            col3.metric(label="Maximum Price PHP", value=f"{df_selection.unit_price.max():,.0f}")
            col4.metric(label="Minimum Price PHP", value=f"{df_selection.unit_price.min():,.0f}")

            style_metric_cards(background_color="#00588E", border_left_color="#FF4B44", border_color="#1f66bd", box_shadow="#F71938")

            col5, col6 = st.columns(2)
            col5.metric(label="Most Sold Product", value=metrics['most_sold_product']['product_detail'], delta=int(metrics['most_sold_product']['transaction_qty']))
            col6.metric(label="Least Sold Product", value=metrics['least_sold_product']['product_detail'], delta=int(metrics['least_sold_product']['transaction_qty']))

            col7, col8 = st.columns(2)
            col7.metric(label="Most Sold Product Type", value=metrics['most_sold_type']['product_type'], delta=int(metrics['most_sold_type']['transaction_qty']))
            col8.metric(label="Most Sold Product Category", value=metrics['most_sold_category']['product_category'], delta=int(metrics['most_sold_category']['transaction_qty']))

            col9, col10 = st.columns(2)
            col9.metric(label="Most Idle Day", value=metrics['most_idle_day']['day_of_week'], delta=int(metrics['most_idle_day']['transaction_qty']))
            #col9.metric(label="Busiest Hour", value=f"{metrics['busiest_hour']['transaction_date']}h", delta=int(metrics['busiest_hour']['transaction_qty']))
            col10.metric(label="Busiest Day", value=metrics['busiest_day']['day_of_week'], delta=int(metrics['busiest_day']['transaction_qty']))

            # Show a table of the transactions
            st.subheader("Transactions Table")
            st.write(df_selection)

            # Plot transaction times by hour
            st.subheader('Transaction Times by Hour')
            plt.figure(figsize=(10, 6))
            sns.kdeplot(df_selection["hour"], bw_adjust=0.5)
            plt.xlabel('Hour of the Day')
            plt.ylabel('Density')
            plt.title('Density Plot of Transactions by Hour')

            # Calculate the busiest hours
            busiest_hours = df['hour'].value_counts().nlargest(3).index.tolist()  # Top 3 busiest hours

            description = f"The most busiest hours are: {', '.join(map(str, busiest_hours))}h"
            st.write(0.5, 0.01, description, wrap=True, horizontalalignment='center', fontsize=12)

            st.pyplot(plt.gcf())

            # Progress Bar
            def Progressbar(current, target, label):
                st.markdown("""<style>.stProgress > div > div > div > div { background-image: linear-gradient(to right, #99ff99 , #FFFF00)}</style>""", unsafe_allow_html=True)
                percent = round((current / target) * 100)
                mybar = st.progress(0)
                if percent > 100:
                    st.subheader(f"Target achieved for {label}!")
                else:
                    st.write(f"{label}: You have {percent}% of {target:,} Php")
                mybar.progress(min(percent, 100))  # Ensure the progress doesn't exceed 100%

            col11, col12 = st.columns(2)
            with col11:
                st.subheader("Target Percentage")
                Progressbar(df_selection["unit_price"].sum(), 30000000, "Revenue")
            
            # Bar chart for sales by day of the week
            st.subheader("Sales by Day of the Week")
            bar_chart = alt.Chart(df_selection).mark_bar().encode(
                x=alt.X('day_of_week', sort=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']),
                y='transaction_qty'
            ).properties(width=700, height=400)
            st.altair_chart(bar_chart)

            # Pie chart for product category distribution
            st.subheader("Product Category Distribution")
            category_distribution = df_selection['product_category'].value_counts().reset_index()
            category_distribution.columns = ['product_category', 'count']
            pie_chart = alt.Chart(category_distribution).mark_arc().encode(
                theta=alt.Theta(field="count", type="quantitative"),
                color=alt.Color(field="product_category", type="nominal"),
                tooltip=['product_category', 'count']
            ).properties(width=700, height=400)
            st.altair_chart(pie_chart)

            # Pie chart for store revenue distribution
            st.subheader("Store Revenue Distribution")
            store_revenue_distribution = df_selection.groupby('store_location')['unit_price'].sum().reset_index()
            store_revenue_distribution.columns = ['store_location', 'revenue']
            pie_chart_store = alt.Chart(store_revenue_distribution).mark_arc().encode(
                theta=alt.Theta(field="revenue", type="quantitative"),
                color=alt.Color(field="store_location", type="nominal"),
                tooltip=['store_location', 'revenue']
            ).properties(width=700, height=400)
            st.altair_chart(pie_chart_store)
            # Revenue forecast plot
            st.subheader("Revenue Forecast")
            revenue_df = df_selection.groupby(pd.Grouper(key='transaction_date', freq='D')).agg({'unit_price': 'sum'}).reset_index()
            revenue_df.columns = ['ds', 'y']

            m = Prophet(yearly_seasonality=True, daily_seasonality=True)
            m.fit(revenue_df)

            future = m.make_future_dataframe(periods=30)
            forecast = m.predict(future)

            fig = m.plot(forecast, xlabel='Date', ylabel='Revenue')
            st.pyplot(fig)
            st.write("""
            The graph above displays the forecasted revenue for the next 30 days. 

            ### Interpretation:
            - **Blue Line**: This represents the predicted revenue based on historical data.
            - **Shaded Area**: The light blue shaded region around the blue line shows the uncertainty intervals (confidence intervals) for the predictions. Wider intervals indicate more uncertainty.
            - **Black Dots**: These are the actual observed revenue values from the historical data.

            By analyzing this graph, you can anticipate potential future revenue trends and understand the expected variability. The model accounts for daily and yearly seasonality patterns, helping to identify recurring trends and any significant deviations from the expected revenue.

            ### Recommendations:
            1. **Prepare for High Demand**: If the forecast indicates a significant increase in revenue, ensure that inventory levels are adequate to meet the anticipated demand.
            2. **Marketing Campaigns**: Plan marketing campaigns around periods with expected revenue spikes to maximize sales.
            3. **Resource Allocation**: Allocate resources (e.g., staff, logistics) effectively during high-revenue periods to maintain service quality.
            4. **Risk Management**: Consider the uncertainty intervals in your planning to mitigate risks associated with revenue fluctuations.
            """)    
        

            # Aggregate unit price by date
            st.subheader("Unit Price Forecast")
            price_df = df_selection.groupby(pd.Grouper(key='transaction_date', freq='D')).agg({'unit_price': 'mean'}).reset_index()

            # Rename columns as Prophet expects 'ds' and 'y' column names
            price_df = price_df.rename(columns={'transaction_date': 'ds', 'unit_price': 'y'})

            # Train Prophet model for unit price
            price_model = Prophet()
            price_model.fit(price_df)

            # Make future predictions for unit price
            price_future = price_model.make_future_dataframe(periods=30)  # Predict unit price for the next 30 days
            price_forecast = price_model.predict(price_future)

            fig_price = price_model.plot(price_forecast)
            st.write(fig_price)
            st.write("""
            The graph above shows the forecasted average unit price for the next 30 days. 

            ### Interpretation:
            - **Blue Line**: This line represents the predicted average unit price over time.
            - **Shaded Area**: The light blue shaded region around the blue line indicates the uncertainty intervals (confidence intervals) for the predictions. Wider intervals mean greater uncertainty.
            - **Black Dots**: These dots are the actual observed unit prices from the historical data.

            This forecast helps in understanding potential price trends and fluctuations. By monitoring the forecasted prices, you can make informed decisions about pricing strategies, inventory management, and marketing efforts. The model captures daily and yearly seasonal effects, providing insights into regular patterns and potential anomalies in unit prices.
            
            ### Recommendations:
            1. **Pricing Strategy**: Adjust your pricing strategy based on the forecasted trends to optimize profitability.
            2. **Promotions and Discounts**: Plan promotions or discounts if the forecast suggests a decline in prices to stimulate demand.
            3. **Supplier Negotiations**: Use the forecasted price trends in negotiations with suppliers to secure better rates or terms.
            4. **Cost Management**: Monitor and manage costs effectively if the forecast predicts a decline in unit prices to maintain margins.
            5. **Inventory Decisions**: Align your inventory purchasing decisions with the forecasted price trends to avoid overstocking or stockouts.
            """)
            
    else :
        splash_screen()

# Function to process and analyze files for the analytics page
def process_and_analyze_file(uploaded_file1, uploaded_file2):
    df1 = process_file(uploaded_file1)
    df2 = process_file(uploaded_file(uploaded_file2))
    
    if df1 is not None and df2 is not None:
        st.subheader('Key Performance Metrics for First File')
        metrics1 = calculate_metrics(df1)

        col1, col2 = st.columns(2)
        col1.metric(label="Total Items Sold", value=df1.product_detail.count(), delta="Number of Items Sold")
        col2.metric(label="Sum of Product Total Price PHP", value=f"{df1.unit_price.sum():,.0f}", delta="Total Price")

        st.subheader('Key Performance Metrics for Second File')
        metrics2 = calculate_metrics(df2)

        col3, col4 = st.columns(2)
        col3.metric(label="Total Items Sold", value=df2.product_detail.count(), delta="Number of Items Sold")
        col4.metric(label="Sum of Product Total Price PHP", value=f"{df2.unit_price.sum():,.0f}", delta="Total Price")

# Print button function
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

# Analytics page
def analytics_page():
    cover_page()
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
