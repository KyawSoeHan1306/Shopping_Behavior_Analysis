import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt

st.set_page_config(page_title="Sales Dashboard", layout="wide")
st.title("🛒 Shopping Behaviour Analysis")

# Upload CSV file
uploaded_file = st.file_uploader("shopping_behavior_updated.csv", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Show raw data
    with st.expander("View Raw Data"):
        st.dataframe(df)

    # Sales & Customer Overview
    col_left, col_right = st.columns(2)

    # ==================
    # Left Side → Sales
    # ==================
    with col_left:
        st.subheader("Sales Overview")
        s1, s2 = st.columns(2)
        total_revenue = df['Purchase Amount (USD)'].sum()
        s1.metric(label="💰 Total Purchase Amount (USD)", value=f"${total_revenue:,.2f}")
        aov = total_revenue / len(df)
        s2.metric(label="💵 Average Order Value (AOV)", value=f"${aov:,.3f}")

        s3, s4, s5 = st.columns(3)
        customers = df.groupby('Customer ID').size().reset_index(name='Orders')
        repeaters = customers[customers['Orders'] > 1].shape[0]
        new_customers = customers[customers['Orders'] == 1].shape[0]
        s3.metric(label="🧾 Total Orders", value=f"{len(df):,}")
        s4.metric(label="🧾 Repeaters", value=f"{repeaters:,}")
        s5.metric(label="🧾 New Customers", value=f"{new_customers:,}")

    # =======================
    # Right Side → Customers
    # =======================
    with col_right:
        st.subheader("Customer Overview")
        s1, s2 = st.columns(2)
        customer_count = df['Customer ID'].nunique()
        s1.metric(label="Customer Count", value=f"{customer_count}")
    
        avg_rating = df['Review Rating'].mean()
        s2.metric(label="Average Rating", value=f"{avg_rating:.2f} / 5")
    
        s3, s4, s5 = st.columns(3)
        sub_per = df['Subscription Status'].eq('Yes').mean() * 100
        s3.metric(label="% of Subscription", value=f"{sub_per:.0f}%")
        
        disc_per = df['Discount Applied'].eq('Yes').mean() * 100
        s4.metric(label="% of Discount Used", value=f"{disc_per:.0f}%")
    
        promo_per = df['Promo Code Used'].eq('Yes').mean() * 100
        s5.metric(label="% of Promo Code Used", value=f"{promo_per:.0f}%")      

    
    # ========================
    # Average & Total Revenue
    # ========================
    col_left, col_right = st.columns(2)
    features = df.select_dtypes(include='object').columns.drop(['Location Code', 'Color', 'Item Purchased'])
    
    def plot_summary(df, column, agg_type, title):
        agg_func = 'sum' if agg_type == 'Total' else 'mean'
        label = f"{agg_type} Order Value (USD)"
        
        if column == 'Location':
            df_summary = (
                df.groupby(['Location', 'Location Code'], as_index=False)
                  .agg({'Purchase Amount (USD)': agg_func})
                  .rename(columns={'Purchase Amount (USD)': label})
            )

            fig = px.choropleth(
                df_summary,
                locations='Location Code',                 
                locationmode='USA-states',
                color=label,
                color_continuous_scale='plasma',
                scope='usa',
                hover_name='Location',             
                hover_data={
                    'Location Code': False,                
                    label: True                
                },
                title="🗺️ Total Purchase Amount by State"
            )
            fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})

        elif df[column].nunique() <= 5:
            df_summary = (
                df.groupby(column, as_index=False)
                  .agg({'Purchase Amount (USD)': agg_func})
                  .rename(columns={'Purchase Amount (USD)': label})
            )
    
            fig = px.pie(
                df_summary,
                names=column,
                values=label, 
                title=title,
                color_discrete_sequence=px.colors.sequential.Magma
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
        
        else:
            df_summary = (df.groupby(column, as_index=False)
                          .agg({'Purchase Amount (USD)': agg_func})
                          .rename(columns={'Purchase Amount (USD)': label})
                          .sort_values(by=label, ascending=False))
            df_summary['%'] = ((df_summary[label] / df_summary[label].sum()) * 100).round(2)
            fig = px.bar(df_summary, 
                         x=column, y=label, 
                         color=label, color_continuous_scale='plasma',
                         title=title, text='%'
                        )
        st.plotly_chart(fig, use_container_width=True)

    # ============================
    # Left Side → Average Revenue
    # ============================
    with col_left:
        st.subheader("💵 Average Order View")
        option_left = st.selectbox("Group by:", 
        features, 
        key='left_select')
        plot_summary(df, option_left, 'Average', f"Average Order Value by {option_left}")

    # ============================
    # Right Side → Total Revenue
    # ============================
    with col_right:
        st.subheader("💰 Total Order View")
        option_right = st.selectbox("Group by:", 
        features, 
        key='right_select')
        plot_summary(df, option_right, 'Total', f"Total Order Value by {option_right}")   

    
    # ============================
    # Top & Underperforming Items
    # ============================
    st.subheader("🛍️ Top & Underperforming Items — Seasonal & Frequency")
    col_left, col_right = st.columns(2)

    # ============================
    # Left Side → Seasonal Items
    # ============================
    with col_left:
        st.markdown("##### 🌸 Items by Season")
    
        seasons = df['Season'].dropna().unique().tolist()
        selected_season = st.selectbox("Select Season:", sorted(seasons), key='season_select')
    
        top_bottom = st.radio("View:", ['Top 5', 'Bottom 5'], horizontal=True, key='season_toggle')
    
        season_df = df[df['Season'] == selected_season]
        item_counts = season_df['Item Purchased'].value_counts()
    
        if top_bottom == 'Top 5':
            items_to_plot = item_counts.head(5)
        else:
            items_to_plot = item_counts.tail(5)
    
        df_season_plot = items_to_plot.reset_index().rename(columns={'index': 'Item Purchased', 'count': 'Count'})
        fig_season = px.pie(
            df_season_plot,
            names='Item Purchased',
            values='Count',
            title=f"{top_bottom} Items in {selected_season}",
            color_discrete_sequence=px.colors.sequential.Magma
        )
        fig_season.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_season, use_container_width=True)

    # ============================
    # Right Side → Frequency Items
    # ============================
    with col_right:
        st.markdown("##### 🔁 Items by Purchase Frequency")
    
        freq_options = df['Frequency of Purchases'].dropna().unique().tolist()
        selected_freq = st.selectbox("Select Frequency:", sorted(freq_options), key='freq_select')
    
        top_bottom_freq = st.radio("View:", ['Top 5', 'Bottom 5'], horizontal=True, key='freq_toggle')
    
        freq_df = df[df['Frequency of Purchases'] == selected_freq]
        item_counts_freq = freq_df['Item Purchased'].value_counts()
    
        if top_bottom_freq == 'Top 5':
            items_to_plot_freq = item_counts_freq.head(5)
        else:
            items_to_plot_freq = item_counts_freq.tail(5)
    
        df_freq_plot = items_to_plot_freq.reset_index().rename(columns={'index': 'Item Purchased', 'count': 'Count'})
        fig_freq = px.pie(
            df_freq_plot,
            names='Item Purchased',
            values='Count',
            title=f"{top_bottom_freq} Items ({selected_freq} Buyers)",
            color_discrete_sequence=px.colors.sequential.Magma
        )
        fig_freq.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_freq, use_container_width=True)
        

    # ============================
    # Season × Category × Item
    # ============================
    st.subheader("🛍️ Seasonal Category-wise Item Preferences & Total Revenue")
    col_left, col_right = st.columns(2)
    
    # =================================
    # Category → Item Purchased Treemap
    # =================================
    with col_left:
        st.markdown("##### 📦 Category → Item Purchased")
        filter_option = st.selectbox(
            "Filter by Season :",
            options=["All"] + sorted(df['Season'].dropna().unique().tolist()),
            key="treemap_season_filter"
        )
        if filter_option != "All":
            treemap_df = df[df['Season'] == filter_option]
        else:
            treemap_df = df.copy()
        
        treemap_summary = (
            treemap_df.groupby(['Category', 'Item Purchased'], as_index=False)
                      .agg({'Purchase Amount (USD)': 'sum'})
        )
        total_purchase = treemap_summary['Purchase Amount (USD)'].sum()
        treemap_summary['% of Total'] = (treemap_summary['Purchase Amount (USD)'] / total_purchase * 100).round(2)
    
        fig_treemap = px.treemap(
            treemap_summary,
            path=['Category', 'Item Purchased'],
            values='Purchase Amount (USD)',
            color='Purchase Amount (USD)',
            color_continuous_scale='plasma',
            custom_data=['Purchase Amount (USD)', '% of Total'],
            title="Total Purchase Amount by Category → Item"
        )
        fig_treemap.update_traces(
            texttemplate="%{label}<br>$%{customdata[0]:,.0f} (%{customdata[1]}%)",
            textposition='middle center'
        )
        st.plotly_chart(fig_treemap, use_container_width=True)

    
    # ============================
    # Season × Category Heatmap
    # ============================
    with col_right:
        st.markdown("##### 🌸 Season × Category Performance")
        season_category_summary = (
            df.groupby(['Season', 'Category'], as_index=False)
              .agg({'Purchase Amount (USD)': 'sum'})
        )
        heatmap_data = season_category_summary.pivot(index='Category', columns='Season', values='Purchase Amount (USD)').fillna(0)
        
        fig_heatmap = px.imshow(
            heatmap_data,
            text_auto=True,
            color_continuous_scale='plasma',
            aspect="auto",
            labels=dict(x="Season", y="Category", color="Purchase Amount (USD)"),
            title="Total Purchase Amount by Season & Category"
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)


    # ==============================
    # Multi-Features Visualizations
    # ==============================
    st.subheader("📊 Multi-Features Analysis")

    cat_features = df.select_dtypes(include='object').columns.tolist()
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        feat1 = st.selectbox("Feature 1:", ["None"] + cat_features, key='feat1')
    
    available2 = [f for f in cat_features if f != feat1]
    with col2:
        feat2 = st.selectbox("Feature 2:", ["None"] + available2, key='feat2')
    
    available3 = [f for f in available2 if f != feat2]
    with col3:
        feat3 = st.selectbox("Feature 3:", ["None"] + available3, key='feat3')
    
    available4 = [f for f in available3 if f != feat3]
    with col4:
        feat4 = st.selectbox("Feature 4:", ["None"] + available4, key='feat4')
    
    group_features = [f for f in [feat1, feat2, feat3, feat4] if f != "None"]
    
    if len(group_features) < 2:
        st.warning("Please select at least 2 categorical features for meaningful comparison.")
    else:
        df_summary = (
            df.groupby(group_features, as_index=False)['Purchase Amount (USD)']
              .sum()
              .sort_values(by='Purchase Amount (USD)', ascending=False)
        )
        max_rows = 50
        if len(df_summary) > max_rows:
            df_summary = df_summary.head(max_rows)
            st.info(f"Showing top {max_rows} combinations due to too many unique groups.")
    
        # Plot as stacked bar or sunburst depending on # of features
        if len(group_features) == 2:
            fig = px.bar(df_summary, x=group_features[0], y='Purchase Amount (USD)', color=group_features[1],
                         text='Purchase Amount (USD)')
        else:
            fig = px.sunburst(df_summary, path=group_features, values='Purchase Amount (USD)')
        st.plotly_chart(fig, use_container_width=True)
    
else:
    st.info("👆 Please upload your CSV file to start.")
