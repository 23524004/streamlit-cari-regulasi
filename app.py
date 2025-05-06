import streamlit as st
import sys
import os
import networkx as nx

# Add the src folder to sys.path
sys.path.append(os.path.join(os.getcwd(), 'src'))  # Make sure 'src' folder is in sys.path

# Now import GraphTraversal from query.py in src/
from query import GraphTraversal

# Path to the graph file
GRAPH_FILE_PATH = 'dataset/final_graph.graphml'

# Cache the graph loading process so it is only loaded once unless the graph file changes
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_graph():
    """Load the graph from the file."""
    return nx.read_graphml(GRAPH_FILE_PATH)

# Cache the search results, so identical queries get the same results
@st.cache_data(ttl=3600)  # Cache for 1 hour
def perform_search_cached(query):
    """Search the graph with the query and return the results."""
    graph = load_graph()  # Use cached graph
    if graph is None or len(graph.nodes) == 0:
        st.error("Graph file could not be loaded or is empty.")
        return []

    # Define traversal parameters
    similarity_threshold = 0.1
    max_depth = 2

    # Create a GraphTraversal object
    traversal = GraphTraversal(graph, query, similarity_threshold, max_depth)

    # Step 1: Get initial nodes based on query similarity
    initial_nodes = traversal.get_initial_nodes()

    # Step 2: Perform the graph traversal starting from the initial nodes
    results = traversal.traverse(initial_nodes)

    return results

def format_results_for_display(results):
    """Format the traversal results for displaying in Streamlit"""
    formatted_results = []
    seen_results = set()
    
    for result in results:
        from_node = result.get('from_node', 'Unknown')
        to_node = result.get('to_node', 'Unknown')
        relation = result.get('relation', 'N/A')
        similarity_score = result.get('similarity_score', 'N/A')
        isi = result.get('isi', 'N/A')

        formatted_result = f"""
        <div class="result">
            <div class="result-header">
                <strong>{to_node}</strong>
            </div>
            <div class="content">
                <strong>{isi}</strong> 
            </div>
        </div>
        """
        
        # Only unique result
        if formatted_result not in seen_results:
            formatted_results.append(formatted_result)
            seen_results.add(formatted_result)

    return formatted_results

# Streamlit layout
st.markdown("""
    <style>
        body {
            background-color: black;
        }
        .result {
            background-color: #f9f9f9;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        .result-header {
            font-size: 18px;
            font-weight: bold;
            color: #4CAF50;
            margin-bottom: 8px;
        }
        .content {
            font-size: 14px;
            color: #333;
            word-wrap: break-word;
        }
        .header {
            text-align: center;
            color: #eb6a6a;
            font-size: 36px;
            margin-bottom: 30px;
        }
        .search-box {
            padding: 10px;
            font-size: 18px;
            border-radius: 5px;
            border: 2px solid #4CAF50;
            width: 100%;
            height: 60px;
        }
    </style>
""", unsafe_allow_html=True)

# Header of the application
st.markdown('<div class="header">PENCARIAN REGULASI</div>', unsafe_allow_html=True)

# Text input for search query
search_query = st.text_input("", "", key="search", placeholder="Type your query and press Enter (iuran, peserta, bpjs kesehatan)", help="Start typing to search...", max_chars=25)

# If the user has entered a query, perform the search
if search_query:
    with st.spinner("Searching..."):
        # Get search results from the cached search function
        results = perform_search_cached(search_query)

        # Format the results for display
        formatted_results = format_results_for_display(results)

        # Display the results in Streamlit
        if formatted_results:
            for result in formatted_results:
                st.markdown(result, unsafe_allow_html=True)
        else:
            st.markdown('<div class="results">No results found.</div>', unsafe_allow_html=True)
