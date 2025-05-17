import os
import pytz
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
# from nltk.tokenize import word_tokenize
# from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
# from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

class GraphTraversal:
    def __init__(self, graph, query, similarity_threshold, max_depth):
        self.graph = graph
        self.query = query
        self.similarity_threshold = similarity_threshold
        self.max_depth = max_depth
        self.vectorizer = TfidfVectorizer()

        # self.stopword_factory = StopWordRemoverFactory()
        # self.stop_words = set(self.stopword_factory.get_stop_words())
        # self.stemmer_factory = StemmerFactory()
        # self.stemmer = self.stemmer_factory.create_stemmer()

    def preprocess_text(self, text):
        return text.lower()  # Add additional preprocessing as needed

    # def preprocess_text_indonesian(self, text: str) -> str:
    #     """
    #     Preprocesses text specifically for Indonesian legal documents.
    #     """

    #     # Step 1: Tokenization and stop word removal (Modified)
    #     tokens = word_tokenize(text)
    #     # Keep tokens that are not stop words and have more than 1 character
    #     filtered_tokens = [w for w in tokens if w.lower() not in self.stop_words and len(w) > 1]

    #     # Step 2: Stemming (Modified)
    #     stemmed_tokens = [self.stemmer.stem(token) for token in filtered_tokens]

    #     # Join the stemmed tokens back into a string
    #     processed_text = " ".join(stemmed_tokens)

    #     return processed_text

    def get_initial_nodes(self):
        """Retrieve initial nodes based on similarity between query and 'isi'."""
        print("Getting initial nodes...")

        node_similarities = []

        # Iterate through all nodes to compute similarity with the query
        for node_id, node_data in self.graph.nodes(data=True):
            if 'isi' in node_data and 'Pasal' in node_data['tipeBagian']:
                isi = node_data['isi']
                vectorized_text = self.vectorizer.fit_transform([self.preprocess_text(self.query), isi])
                similarity = cosine_similarity(vectorized_text[0], vectorized_text[1])[0][0]

                if similarity >= self.similarity_threshold:
                    node_similarities.append((node_id, similarity))

        # Sort nodes by similarity in descending order
        node_similarities.sort(key=lambda x: x[1], reverse=True)
        return node_similarities

    def traverse(self, initial_nodes):
        """Perform traversal to retrieve nodes up to a certain depth."""
        print("Traversing from initial nodes...")

        results = []
        for initial_node, initial_similarity in initial_nodes:
            visited = set()
            queue = [(initial_node, 0)]  # (node, depth)

            results.append({
                "from_node": None,  # No parent for the initial node
                "to_node": initial_node,
                "relation": "query_similarity",
                "similarity_score": initial_similarity,
                "isi": self.graph.nodes[initial_node].get("isi", "")
            })

            while queue:
                current_node, depth = queue.pop(0)

                if depth > self.max_depth:
                    continue

                visited.add(current_node)

                # Get neighboring nodes
                for neighbor in self.graph.neighbors(current_node):
                    if neighbor in visited:
                        continue

                    edge_data = self.graph.get_edge_data(current_node, neighbor)
                    relation = edge_data.get("relation", "")
                    weight = edge_data.get("weight", None)

                    if 'Pasal' in self.graph.nodes[neighbor].get('tipeBagian', ''):
                        similarity_score = weight if relation == "miripDengan" else None
                        results.append({
                            "from_node": current_node,
                            "to_node": neighbor,
                            "relation": relation,
                            "similarity_score": similarity_score,
                            "isi": self.graph.nodes[neighbor].get("isi", "")
                        })
                        queue.append((neighbor, depth + 1))

                    elif relation == "mengingat":
                        results.append({
                            "from_node": current_node,
                            "to_node": neighbor,
                            "relation": relation,
                            "isi": None  # No content for 'mengingat' nodes
                        })

        return results

    def display_results(self, results):
        """Pretty display of traversal results."""
        print("Traversal Results:\n")
        for result in results:
            print(f"From Node: {result['from_node']}")
            print(f"To Node: {result['to_node']}")
            print(f"Relation: {result['relation']}")
            if result['similarity_score']:
                print(f"Similarity Score: {result['similarity_score']:.2f}")
            if result['isi']:
                print(f"Content (Isi): {result['isi']}\n")
            print("-" * 40)

    def display_results_grouped(self, results, output_file="result.txt"):
        """
        Display the results grouped by the source node, with output to both terminal and file.

        Args:
            results (list): List of traversal results.
            output_file (str): File to write the results to.
        """
        grouped_results = {}
        initial_results = []  # To store query-to-initial-node similarities

        # Separate initial query results from traversal results
        for result in results:
            if result["relation"] == "query_similarity":
                initial_results.append(result)  # Query-to-initial-node results
            else:
                source_node = result["from_node"]
                if source_node not in grouped_results:
                    grouped_results[source_node] = []
                grouped_results[source_node].append(result)

        # Group results by source node
        # for result in results:
        #     source_node = result["from_node"]
        #     if source_node not in grouped_results:
        #         grouped_results[source_node] = []
        #     grouped_results[source_node].append(result)

        output_file_folder = os.path.join("results", output_file)

        print("Writing to output file...")
        with open(output_file_folder, "w", encoding="utf-8") as f:
            # Display query-to-initial-node results
            header = "Initial Query Similarity Results:\n"
            print(header)
            f.write(header)

            for result in initial_results:
                similarity_score = result["similarity_score"]
                to_node = result["to_node"]
                content = result.get("isi", "N/A")

                query_info = (
                    f"  Initial Node: {to_node}\n"
                    f"  Similarity Score with Query: {similarity_score:.2f}\n"
                    f"  Content (Isi): {content}\n"
                    f"----------------------------------------\n"
                )
                print(query_info)
                f.write(query_info)

            # Display traversal results grouped by source node
            traversal_header = "Graph Traversal Results:\n"
            print(traversal_header)
            f.write(traversal_header)

            for source_node, edges in grouped_results.items():
                # Print the source node header
                source_header = f"From Node: {source_node}\n"
                # print(source_header)
                f.write(source_header)

                for edge in edges:
                    relation = edge["relation"]
                    to_node = edge["to_node"]
                    similarity_score = edge.get("similarity_score", "N/A")
                    content = edge.get("isi", "N/A")

                    edge_info = (
                        f"  To Node: {to_node}\n"
                        f"  Relation: {relation}\n"
                        f"  Similarity Score: {similarity_score:.2f}\n"
                        f"  Content (Isi): {content}\n"
                        f"----------------------------------------\n"
                    )

                    # print(edge_info)
                    f.write(edge_info)

        # with open(output_file, "w", encoding="utf-8") as f:
        #     for source_node, edges in grouped_results.items():
        #         # Print the source node header
        #         header = f"From Node: {source_node}\n"
        #         print(header)
        #         f.write(header)

        #         for edge in edges:
        #             # Print each edge under the same source node
        #             relation = edge["relation"]
        #             to_node = edge["to_node"]
        #             similarity_score = edge.get("similarity_score", "N/A")
        #             content = edge.get("isi", "N/A")

        #             edge_info = (
        #                 f"  To Node: {to_node}\n"
        #                 f"  Relation: {relation}\n"
        #                 f"  Similarity Score: {similarity_score:.2f}\n"
        #                 f"  Content (Isi): {content}\n"
        #                 f"----------------------------------------\n"
        #             )

        #             print(edge_info)
        #             f.write(edge_info)

# Example Usage
# def main():
#     # Load the graph (replace with your graphml file path)
#     print("Reading the initial graph...")
#     graph = nx.read_graphml("/content/drive/MyDrive/PROYEK PENERATAN TERAPAN/PPT K7/Dataset/kg_data_50_new_cont.graphml")

#     # User-defined parameters
#     query = str(input("Masukkan query Anda: "))

#     similarity_threshold = 0.5
#     max_depth = 3

#     print("Doing graph traversal...")
#     traversal = GraphTraversal(graph, query, similarity_threshold, max_depth)

#     # Step 1: Get initial nodes
#     initial_nodes = traversal.get_initial_nodes()

#     print("Initial Nodes:")
#     for node, sim in initial_nodes:
#         print(f"Node: {node}, Similarity: {sim:.2f}")
#     print("\n")

#     # Step 2: Traverse the graph
#     results = traversal.traverse(initial_nodes)

#     # Step 3: Display results
#     timezone = pytz.timezone('Asia/Jakarta')
#     current_time = datetime.now(timezone)
#     timestamp = current_time.strftime('%Y-%m-%d_%H-%M-%S')
#     # traversal.display_results(results)
#     traversal.display_results_grouped(results, f"Eksperimen1_result_50_{timestamp}.txt")

#     print("Done!")

# if __name__ == "__main__":
#     main()
