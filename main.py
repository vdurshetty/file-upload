from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import json
from myrag.vectorless_rag import rag_response

VOICE_FOLDER = "uploads/voice"
IMAGE_FOLDER = "uploads/images"
DOC_FOLDER = "uploads/docs"
# app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

UPLOAD_TYPE = ["IMAGE", "VOICE", "DOCS"]

# Create folder if not exists
os.makedirs(VOICE_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)
os.makedirs(DOC_FOLDER, exist_ok=True)

# Allowed file extensions (optional)
IMAGE_ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
# Allowed file extensions (optional)
VOICE_ALLOWED_EXTENSIONS = {"webm", "wav"}
DOCS_ALLOWED_EXTENSIONS = {"pdf", "xls"}


def allowed_file(filename, file_type):
    print("File Type is ", file_type)
    if file_type == UPLOAD_TYPE[0]:
        return "." in filename and filename.rsplit(".", 1)[1].lower() in IMAGE_ALLOWED_EXTENSIONS
    elif file_type == UPLOAD_TYPE[1]:
        return "." in filename and filename.rsplit(".", 1)[1].lower() in VOICE_ALLOWED_EXTENSIONS
    elif file_type == UPLOAD_TYPE[2]:
        return "." in filename and filename.rsplit(".", 1)[1].lower() in DOCS_ALLOWED_EXTENSIONS


def check_upload_file(request_file):
    if "file" not in request_file:
        return jsonify({"error": "No file part in request"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    return file


# os.chdir("..")
print("Folder Path is :", os.getcwd())
app = Flask(__name__, template_folder=os.getcwd() + "/templates")
CORS(app)


@app.route("/")
def home():
    print("current path:", request.full_path)
    return render_template("upload.html")


@app.route("/chat")
def my_chat():
    print("current path:", request.full_path)
    return render_template("chat.html")


@app.route("/upload")
def my_upload():
    print("current path:", request.full_path)
    return render_template("upload.html")


@app.route("/list")
def my_files():
    print("current path:", request.full_path)
    return render_template("files.html")


@app.route("/record")
def my_record():
    print("current path:", request.full_path)
    return render_template("myrecord.html")


@app.route("/files")
def get_files():
    response = jsonify({"error": "valid query types are ?type=[docs/images/voice]"})
    upload_folder = os.getcwd() + "/uploads"
    fpath = request.args.get('type')
    if fpath is None:
        fpath = "docs"
    else:
        fpath = request.args.get('type')
    folder_path = upload_folder + "/" + fpath
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
        response = json.dumps({i: v for i, v in enumerate(pdf_files)})
    return response


@app.route("/deletefile", methods=["DELETE"])
def delete_file():
    response = jsonify({"error": "select file name"})
    upload_folder = os.getcwd() + "/uploads"
    fpath = request.args.get('type')
    filename = request.args.get('file')
    print("File name ", filename)
    if filename is not None:
        file_path = upload_folder + "/" + fpath + "/" + filename
        print(file_path)
        if os.path.isfile(file_path):
            os.remove(file_path)
            response = jsonify({"message": "File deleted successfully", "filename": filename}), 200
    return response


@app.route("/aichat", methods=["POST"])
def chat():
    user_msg = request.json.get("message")
    pdf_file = request.headers.get("filename")
    print("query message :", user_msg)
    print("file name :", pdf_file)
    bot_msg = rag_response(pdf_file, user_msg)
    return jsonify({"response": bot_msg})


@app.route("/ragchat", methods=["POST"])
def rag_chat():
    user_msg = request.json.get("message")
    print("query message :", user_msg)
    # req_obj = request.get_json()
    # result = []
    # # Loop through each key-value pair
    # for key, value in req_obj.items():
    #     print(f"{key} = {value}")
    #     result.append(value)

    bot_msg = "test" # fetch_query("/Users/venu/venus/ai_samples/file-upload/uploads/docs", user_msg)
    return jsonify({"response": bot_msg})


@app.route("/upload_image", methods=["POST"])
def upload_image():
    file = check_upload_file(request.files)
    if file and allowed_file(file.filename, UPLOAD_TYPE[0]):
        filepath = os.path.join(IMAGE_FOLDER, file.filename)
        file.save(filepath)
        # insert_image(filepath)
        return jsonify({"message": "File uploaded and inserted to Vector Database successfully",
                        "filename": file.filename}), 200
    else:
        print("in else part")
        return jsonify({"error": "File type not allowed"}), 400


@app.route("/upload_voice", methods=["POST"])
def upload_voice():
    file = check_upload_file(request.files)
    if file and allowed_file(file.filename, UPLOAD_TYPE[1]):
        print("ffile is saving,", file.filename)
        # filepath = os.getcwd() + "/" + os.path.join(self.VOICE_FOLDER, file.filename)
        filepath = os.path.join(VOICE_FOLDER, file.filename)
        print("File path is :", filepath)
        file.save(filepath)
        # insert_voice(filepath)
        return jsonify({"message": "File uploaded and inserted to Vector Database successfully",
                        "filename": file.filename}), 200
    else:
        print("in else part")
        return jsonify({"error": "File type not allowed"}), 400


@app.route("/upload_docs", methods=["POST"])
def upload_docs():
    file = check_upload_file(request.files)
    if file and allowed_file(file.filename, UPLOAD_TYPE[2]):
        print("ffile is saving,", file.filename)
        filepath = os.path.join(DOC_FOLDER, file.filename)
        file.save(filepath)
        # insert_pdf(filepath)
        return jsonify({"message": "File uploaded and inserted to Vector Database successfully",
                        "filename": file.filename}), 200
    else:
        print("in else part")
        return jsonify({"error": "File type not allowed"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7890, debug=True)
