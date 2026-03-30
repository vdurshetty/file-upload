from flask import Flask, request, jsonify, render_template
# from flask_cors import CORS
import os


class RestPack:
    # Upload folder
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



    """A simple RESTful API pack using Flask."""
    def __init__(self):
        self.app = Flask(__name__, template_folder=os.getcwd()+"/templates")
        # CORS(self.app, resources={
        #     r"/*": {
        #         "origins": "http://127.0.0.1:7890"
        #    }
        # })
        self.setup_routes()

    def setup_routes(self):

        @self.app.route("/")
        def home():
            print("current path:", request.full_path)
            return render_template("upload.html")

        @self.app.route("/chat")
        def my_chat():
            print("current path:", request.full_path)
            return render_template("chat.html")

        @self.app.route("/upload")
        def my_upload():
            print("current path:", request.full_path)
            return render_template("upload.html")

        @self.app.route("/record")
        def my_record():
            print("current path:", request.full_path)
            return render_template("myrecord.html")

        @self.app.route("/aichat", methods=["POST"])
        def chat():
            user_msg = request.json.get("message")
            # bot_msg = llm_with_my_tools.ai_invoke(user_msg)
            return jsonify({"response": user_msg})

        def check_upload_file(request_file):
            if "file" not in request_file:
                return jsonify({"error": "No file part in request"}), 400
            file = request.files["file"]
            if file.filename == "":
                return jsonify({"error": "No selected file"}), 400
            return file

        def allowed_file(filename, file_type):
            print("File Type is ", file_type)
            if file_type == self.UPLOAD_TYPE[0]:
                return "." in filename and filename.rsplit(".", 1)[1].lower() in self.IMAGE_ALLOWED_EXTENSIONS
            elif file_type == self.UPLOAD_TYPE[1]:
                return "." in filename and filename.rsplit(".", 1)[1].lower() in self.VOICE_ALLOWED_EXTENSIONS
            elif file_type == self.UPLOAD_TYPE[2]:
                return "." in filename and filename.rsplit(".", 1)[1].lower() in self.DOCS_ALLOWED_EXTENSIONS

        @self.app.route("/upload_image", methods=["POST"])
        def upload_image():
            file = check_upload_file(request.files)
            if file and allowed_file(file.filename, self.UPLOAD_TYPE[0]):
                filepath = os.path.join(self.IMAGE_FOLDER, file.filename)
                file.save(filepath)
                # insert_image(filepath)
                return jsonify({"message": "File uploaded and inserted to Vector Database successfully",
                                "filename": file.filename}), 200
            else:
                print("in else part")
                return jsonify({"error": "File type not allowed"}), 400

        @self.app.route("/upload_voice", methods=["POST"])
        def upload_voice():
            file = check_upload_file(request.files)
            if file and allowed_file(file.filename, self.UPLOAD_TYPE[1]):
                print("ffile is saving,", file.filename)
                # filepath = os.getcwd() + "/" + os.path.join(self.VOICE_FOLDER, file.filename)
                filepath = os.path.join(self.VOICE_FOLDER, file.filename)
                print("File path is :", filepath)
                file.save(filepath)
                # insert_voice(filepath)
                return jsonify({"message": "File uploaded and inserted to Vector Database successfully",
                                "filename": file.filename}), 200
            else:
                print("in else part")
                return jsonify({"error": "File type not allowed"}), 400

        @self.app.route("/upload_docs", methods=["POST"])
        def upload_docs():
            file = check_upload_file(request.files)
            if file and allowed_file(file.filename, self.UPLOAD_TYPE[2]):
                print("ffile is saving,", file.filename)
                filepath = os.path.join(self.DOC_FOLDER, file.filename)
                file.save(filepath)
                # insert_pdf(filepath)
                return jsonify({"message": "File uploaded and inserted to Vector Database successfully",
                                "filename": file.filename}), 200
            else:
                print("in else part")
                return jsonify({"error": "File type not allowed"}), 400

    def run(self):
        self.app.run(host="0.0.0.0", port=7890, debug=True)


if __name__ == "__main__":
     RestPack().run()
