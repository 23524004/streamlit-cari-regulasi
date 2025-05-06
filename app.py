import streamlit as st
import sys
import os

# Add the src folder to sys.path
sys.path.append(os.path.join(os.getcwd(), 'src'))  # Make sure 'src' folder is in sys.path

# Now import GraphTraversal from query.py in src/
from query import GraphTraversal
import networkx as nx

# Path to the graph file
GRAPH_FILE_PATH = 'dataset/final_graph.graphml'

def perform_search(query):
    # Load the graph
    graph = nx.read_graphml(GRAPH_FILE_PATH)
    if graph is None or len(graph.nodes) == 0:
        st.error("Graph file could not be loaded or is empty.")
        return

    # Define traversal parameters
    similarity_threshold = 0.1
    max_depth = 2

    # Create a GraphTraversal object
    traversal = GraphTraversal(graph, query, similarity_threshold, max_depth)

    # Step 1: Get initial nodes based on query similarity
    initial_nodes = traversal.get_initial_nodes()

    # Step 2: Perform the graph traversal starting from the initial nodes
    results = traversal.traverse(initial_nodes)

    # Return results
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
        .result-body {
            font-size: 16px;
            margin: 10px 0;
            color: #555;
        }
        .similarity-score {
            color: #4CAF50;
            font-weight: bold;
        }
        .relation {
            font-style: italic;
            color: #777;
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
        # Get search results from the graph traversal
        results = perform_search(search_query)

        # Format the results for display
        formatted_results = format_results_for_display(results)

        # Display the results in Streamlit
        if formatted_results:
            for result in formatted_results:
                st.markdown(result, unsafe_allow_html=True)
        else:
            st.markdown('<div class="results">No results found.</div>', unsafe_allow_html=True)
