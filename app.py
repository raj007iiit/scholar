import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from scholarly import scholarly
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="IIIT Kottayam Faculty Scholar Dashboard", layout="wide")
st.title("📚 Google Scholar Citation Growth - IIIT Kottayam Faculty")

# Load faculty names
faculty_df = pd.read_csv("iiitkottayam_faculty_names.csv")
faculty_names = faculty_df["Name"].tolist()

# Sidebar selection
selected_faculty = st.sidebar.multiselect(
    "Select Faculty Members to Compare (⚠ Live scrape — keep it under 10)",
    faculty_names,
    default=faculty_names[:5]
)

# Move refresh button to main body
st.markdown("### 🔄 Click below to fetch latest data from Google Scholar")
refresh = st.button("🚀 Fetch Latest Data")

# Fetch author data from Google Scholar
def fetch_author_data(name):
    try:
        search = scholarly.search_author(name)
        author = scholarly.fill(next(search, {}), sections=["basics", "indices", "counts"])
        if not author or "cites_per_year" not in author:
            return {"error": f"No citation data found for {name}"}
        cpy = author.get("cites_per_year", {})
        df = pd.DataFrame(list(cpy.items()), columns=["Year", "Citations"])
        df["Name"] = name
        return df
    except Exception as e:
        return {"error": f"{name}: {e}"}

def load_data_parallel(names):
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_author_data, name): name for name in names}
        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                if isinstance(result, dict) and "error" in result:
                    st.error(f"❌ {result['error']}")
                else:
                    st.success(f"✅ {name} fetched successfully")
                results.append(result)
            except Exception as e:
                st.error(f"❌ {name} raised an exception: {e}")
    return results

# Live scrape on button press
if selected_faculty and refresh:
    with st.spinner("Fetching latest citation data from Google Scholar..."):
        dataframes = load_data_parallel(selected_faculty)

    clean_dfs = [df for df in dataframes if isinstance(df, pd.DataFrame)]
    if clean_dfs:
        combined = pd.concat(clean_dfs)
        st.subheader("📈 Citation Growth Over Time (Live Data)")
        for name in selected_faculty:
            df_plot = combined[combined["Name"] == name]
            if df_plot.empty:
                st.warning(f"No data for {name}")
                continue
            plt.figure(figsize=(10, 3))
            plt.plot(df_plot["Year"], df_plot["Citations"], marker="o")
            plt.title(name)
            plt.grid(True)
            st.pyplot(plt.gcf())

    st.warning("⚠ Some profiles may not be publicly available or could not be found.")

else:
    st.info("Please select faculty and click '🚀 Fetch Latest Data' to retrieve citation trends.")
