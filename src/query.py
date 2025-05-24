import os
import networkx as nx

class GraphTraversal:
    MAX_INITIAL_NODES = 5000  # Konstan jumlah maksimal initial nodes yang akan diambil

    def __init__(self, graph, query, similarity_threshold, max_depth):
        self.graph = graph
        self.query = query
        self.similarity_threshold = similarity_threshold
        self.max_depth = max_depth

    def preprocess_text(self, text):
        return text.lower()  # Mengubah teks menjadi huruf kecil

    def get_initial_nodes(self):
        """Retrieve initial nodes based on a simple substring match with a threshold."""
        print("Getting initial nodes...")

        node_similarities = []

        # Menghitung kemiripan menggunakan pencocokan substring
        for node_id, node_data in self.graph.nodes(data=True):
            if 'isi' in node_data:
                isi = node_data['isi']
                processed_query = self.preprocess_text(self.query)
                processed_isi = self.preprocess_text(isi)

                # Menggunakan metode substring matching sederhana
                similarity = self.simple_substring_match(processed_query, processed_isi)

                if similarity >= self.similarity_threshold:
                    node_similarities.append((node_id, similarity))

        # Mengurutkan node berdasarkan kemiripan tertinggi
        node_similarities.sort(key=lambda x: x[1], reverse=True)

        # Hanya mengambil maksimal MAX_INITIAL_NODES node teratas
        return node_similarities[:self.MAX_INITIAL_NODES]

    def simple_substring_match(self, query, isi):
        """Hitung kemiripan berdasarkan kesamaan substring."""
        # Menggunakan pendekatan sederhana: hitung berapa banyak kata query ada dalam isi
        query_words = set(query.split())
        isi_words = set(isi.split())
        
        # Menghitung berapa banyak kata query yang ada dalam isi
        common_words = query_words.intersection(isi_words)
        
        # Kemiripan dihitung sebagai rasio kata yang cocok
        similarity = len(common_words) / len(query_words) if len(query_words) > 0 else 0
        return similarity

    def traverse(self, initial_nodes):
        """Perform traversal to retrieve nodes up to a certain depth."""
        print("Traversing from initial nodes...")

        results = []
        result_count = 0  # Track the number of results

        for initial_node, initial_similarity in initial_nodes:
            visited = set()
            queue = [(initial_node, 0)]  # (node, depth)

            # Add initial node as the first result
            results.append({
                "from_node": None,  # No parent for the initial node
                "to_node": initial_node,
                "relation": "query_similarity",
                "similarity_score": initial_similarity,
                "isi": self.graph.nodes[initial_node].get("isi", "")
            })
            result_count += 1  # Increase the result count

            # Stop if we already have 15 results
            if result_count >= 5000:
                break

            while queue and result_count < 5000:
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
                        result_count += 1
                        queue.append((neighbor, depth + 1))

                        # Stop if we already have 15 results
                        if result_count >= 5000:
                            break

                    elif relation == "mengingat":
                        results.append({
                            "from_node": current_node,
                            "to_node": neighbor,
                            "relation": relation,
                            "isi": None  # No content for 'mengingat' nodes
                        })
                        result_count += 1
                        queue.append((neighbor, depth + 1))

                        # Stop if we already have 15 results
                        if result_count >= 5000:
                            break

                # If we have 15 results, break out of the loop
                if result_count >= 5000:
                    break

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

                    f.write(edge_info)
