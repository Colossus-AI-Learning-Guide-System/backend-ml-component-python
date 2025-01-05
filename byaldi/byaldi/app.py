from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import os
from byaldi import RAGMultiModalModel
from claudette import *
from PyPDF2 import PdfReader
import tempfile

app = Flask(__name__)
CORS(app)

# Set environment variables
os.environ["HF_TOKEN"] = "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"  # Replace with your Hugging Face token
os.environ["ANTHROPIC_API_KEY"] = "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"  # Replace with your Claude API key

# Load Byaldi RAG model
RAG = RAGMultiModalModel.from_pretrained("vidore/colpali-v1.2", verbose=1)

@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        print("Received upload request")  # Log the incoming request
        data = request.json
        files = data.get('files', [])
        if not files:
            return jsonify({"error": "No files provided"}), 400

        # Save files temporarily (optional)
        for idx, file_base64 in enumerate(files):
            print(f"Processing file {idx + 1}")  # Log file processing
            file_bytes = base64.b64decode(file_base64)  # Decode base64 to binary

            # Save the binary data to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(file_bytes)
                temp_file_path = temp_file.name

            try:
                # Verify the file is a valid PDF
                reader = PdfReader(temp_file_path)
                print(f"File {idx + 1} is a valid PDF with {len(reader.pages)} pages.")

                # Index the document
                print("Indexing the document...")  # Log indexing
                RAG.index(
                    input_path=temp_file_path,  # Use the temporary file for indexing
                    index_name="attention",
                    store_collection_with_index=True,
                    overwrite=True
                )
            finally:
                # Ensure the temporary file is deleted after processing
                os.unlink(temp_file_path)

        return jsonify({"message": "Files uploaded and indexed successfully"}), 200
    except Exception as e:
        print("Error in upload_files:", str(e))  # Log the error
        return jsonify({"error": str(e)}), 500

@app.route('/query', methods=['POST'])
def handle_query():
    try:
        data = request.json
        query = data.get('query', '')
        if not query:
            return jsonify({"error": "Query is required"}), 400

        # Query the RAG model
        results = RAG.search(query, k=1)

        # Check if results are valid
        if not results or len(results) == 0:
            return jsonify({"error": "No results found"}), 404

        # Extract the image from the RAG result
        result = results[0]
        image_bytes = base64.b64decode(result.base64)  # Decode the base64 image

        # Pass the image and query to Claude
        chat = Chat(models[1])
        claude_response = chat([image_bytes, query])

        print("Claude response type:", type(claude_response))  # Log the type of Claude's response
        print("Claude response attributes:", dir(claude_response))  # Log all attributes of Claude's response
        print("Claude response content:", claude_response.content)  # Log the content of Claude's response

        # Extract text content from Claude's response
        claude_content = ""
        if hasattr(claude_response, "content"):  # Check if the response has a "content" attribute
            for block in claude_response.content:
                if hasattr(block, "text"):  # Check if the block has a "text" attribute
                    claude_content += block.text + "\n"
        else:
            claude_content = "No content available"

        # Parse the response into headings and descriptions
        structured_response = parse_response(claude_content)

        return jsonify(structured_response), 200
    except Exception as e:
        print("Error in handle_query:", str(e))  # Log the error
        return jsonify({"error": str(e)}), 500

def parse_response(response_text):
    """
    Parse the response text into headings and descriptions.
    """
    structured_response = []
    lines = response_text.split("\n")  # Split the response into lines

    current_heading = None
    current_description = []

    for line in lines:
        if line.strip().startswith(("1. ", "2. ", "3. ", "4. ", "5. ", "6. ", "7. ", "8. ", "9. ")):  # Detect numbered headings
            if current_heading:  # Save the previous heading and description
                structured_response.append({
                    "title": current_heading,
                    "content": "\n".join(current_description).strip()
                })
            current_heading = line.strip()  # Start a new heading
            current_description = []  # Reset the description
        else:
            current_description.append(line.strip())  # Add to the current description

    # Add the last heading and description
    if current_heading:
        structured_response.append({
            "title": current_heading,
            "content": "\n".join(current_description).strip()
        })

    return structured_response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)





# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import base64
# import os
# from byaldi import RAGMultiModalModel
# from claudette import *
# from PyPDF2 import PdfReader
# import tempfile

# app = Flask(__name__)
# CORS(app)

# # Set environment variables
# os.environ["HF_TOKEN"] = "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"  # Replace with your Hugging Face token
# os.environ["ANTHROPIC_API_KEY"] = "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"  # Replace with your Claude API key

# # Load Byaldi RAG model
# RAG = RAGMultiModalModel.from_pretrained("vidore/colpali-v1.2", verbose=1)

# @app.route('/upload', methods=['POST'])
# def upload_files():
#     try:
#         print("Received upload request")  # Log the incoming request
#         data = request.json
#         files = data.get('files', [])
#         if not files:
#             return jsonify({"error": "No files provided"}), 400

#         # Save files temporarily (optional)
#         for idx, file_base64 in enumerate(files):
#             print(f"Processing file {idx + 1}")  # Log file processing
#             file_bytes = base64.b64decode(file_base64)  # Decode base64 to binary

#             # Save the binary data to a temporary file
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
#                 temp_file.write(file_bytes)
#                 temp_file_path = temp_file.name

#             try:
#                 # Verify the file is a valid PDF
#                 reader = PdfReader(temp_file_path)
#                 print(f"File {idx + 1} is a valid PDF with {len(reader.pages)} pages.")

#                 # Index the document
#                 print("Indexing the document...")  # Log indexing
#                 RAG.index(
#                     input_path=temp_file_path,  # Use the temporary file for indexing
#                     index_name="attention",
#                     store_collection_with_index=True,
#                     overwrite=True
#                 )
#             finally:
#                 # Ensure the temporary file is deleted after processing
#                 os.unlink(temp_file_path)

#         return jsonify({"message": "Files uploaded and indexed successfully"}), 200
#     except Exception as e:
#         print("Error in upload_files:", str(e))  # Log the error
#         return jsonify({"error": str(e)}), 500

# @app.route('/query', methods=['POST'])
# def handle_query():
#     try:
#         data = request.json
#         query = data.get('query', '')
#         if not query:
#             return jsonify({"error": "Query is required"}), 400

#         # Query the RAG model
#         results = RAG.search(query, k=1)

#         # Check if results are valid
#         if not results or len(results) == 0:
#             return jsonify({"error": "No results found"}), 404

#         # Extract the image from the RAG result
#         result = results[0]
#         image_bytes = base64.b64decode(result.base64)  # Decode the base64 image

#         # Pass the image and query to Claude
#         chat = Chat(models[1])
#         claude_response = chat([image_bytes, query])

#         print("Claude response type:", type(claude_response))  # Log the type of Claude's response
#         print("Claude response attributes:", dir(claude_response))  # Log all attributes of Claude's response
#         print("Claude response content:", claude_response.content)  # Log the content of Claude's response

#         # Extract text content from Claude's response
#         claude_content = ""
#         if hasattr(claude_response, "content"):  # Check if the response has a "content" attribute
#             for block in claude_response.content:
#                 if hasattr(block, "text"):  # Check if the block has a "text" attribute
#                     claude_content += block.text + "\n"
#         else:
#             claude_content = "No content available"

#         # Structure the response for React Flow
#         structured_response = [
#             {
#                 "title": "Claude Response",
#                 "content": claude_content  # Use the extracted content from Claude
#             }
#         ]

#         return jsonify(structured_response), 200
#     except Exception as e:
#         print("Error in handle_query:", str(e))  # Log the error
#         return jsonify({"error": str(e)}), 500
    
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5001)