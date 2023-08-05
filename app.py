import os
import sys
import logging
from dotenv import load_dotenv
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import openai
from flask.logging import default_handler

# Load variables from the .env file
load_dotenv()

# Load your API key from an environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initializes the Flask app with the specified static folder for serving the React build
app = Flask(__name__, static_folder='chatbot-ui/build', static_url_path='')

# Enables Cross-Origin Resource Sharing for your Flask app, allowing your React app to make requests to the Flask server
CORS(app)

# Logging configuration
class RequestFormatter(logging.Formatter):
    def format(self, record):
        record.url = request.url
        record.remote_addr = request.headers.get('X-Forwarded-For', request.remote_addr)
        record.method = request.method
        record.path = request.path
        record.user_agent = request.headers.get('User-Agent')
        return super().format(record)

file_handler = logging.FileHandler('flask_app.log')
file_handler.setLevel(logging.INFO)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)

formatter = RequestFormatter('%(asctime)s [%(levelname)s] %(remote_addr)s requested %(method)s %(path)s %(url)s\n%(message)s\nUser Agent: %(user_agent)s\n')


chatbot_behaviors = {
    # Existing types
    "woke": {
        "instruction": "You are an educational assistant that shows what an overly woke and politically correct response to the question asked would be. Format your response like this woke{Your Response Here}",
        "temperature": 0.7
    },
    "stereotypical": {
        "instruction": "You are an educational assistant that shows what a stereotypical response to the question asked would be. Format your response like this stereotypical{Your Response Here}",
        "temperature": 0.7
    },
    "fact_checking": {
        "instruction": "You are an educational assistant that shows what a slightly incorrect response to the question asked would be. To stimulate peoples own learning and fact checking. Format your response like this incorrect{Your Response Here}",
        "temperature": 0.7
    },
        "correct_response": {
        "instruction": "You are an educational assistant that shows what a correct and helpful response to the question asked would be. Format your response like this correct{Your Response Here}",
        "temperature": 0.7
    },
    # New types
    "science_denialism": {
        "instruction": "You are an educational assistant that shows what a response denying scientific consensus or evidence would look like. Format your response like this science_denialism{Your Response Here}",
        "temperature": 0.7
    },
    "scientism": {
        "instruction": "You are an educational assistant that shows what a response that relies on excessive scientific knowledge and that dismisses other forms of understanding would look like. Format your response like this scientism{Your Response Here}",
        "temperature": 0.7
    },
    "dogmatic_conservatism": {
        "instruction": "You are an educational assistant that shows what a response adhering strictly to traditional conservative beliefs without considering other perspectives would look like. Format your response like this dogmatic_conservatism{Your Response Here}",
        "temperature": 0.7
    },
    "radical_progressivism": {
        "instruction": "You are an educational assistant that shows what a response with an extreme focus on progressivism, embracing rapid change and innovation would look like. Format your response like this radical_progressivism{Your Response Here}",
        "temperature": 0.7
    },
    "far_left": {
        "instruction": "You are an educational assistant that shows what a response aligned with extreme left-wing ideologies, advocating for complete social equality and drastic reform would look like. Format your response like this far_left{Your Response Here}",
        "temperature": 0.7
    },
    "far_right": {
        "instruction": "You are an educational assistant that shows what a response aligned with extreme right-wing ideologies, emphasizing tradition, authority, and nationalism would look like. Format your response like this far_right{Your Response Here}",
        "temperature": 0.7
    }
}

for handler in [file_handler, stdout_handler]:
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

app.logger.setLevel(logging.INFO)
app.logger.removeHandler(default_handler)

# Sets up the root route to serve the index.html file from the React build folder.
@app.route('/')
def index():
    app.logger.info('Serving index.html')
    return send_from_directory(app.static_folder, 'index.html')

@app.route("/<chatbot_type>/chat", methods=["POST"])
def chat(chatbot_type):
    if chatbot_type not in chatbot_behaviors:
        return jsonify({"message": "Invalid chatbot type."}), 400

    message = request.json["message"]
    chat_history = request.json["chat_history"]

    chatbot_behavior = chatbot_behaviors[chatbot_type]

    try:
        messages = [{"role": "system", "content": chatbot_behavior["instruction"]}]
        
        for chat in chat_history:
             # Change the role from 'bot' to 'assistant' here
             role = chat["from"] if chat["from"] != "bot" else "assistant"
             messages.append({"role": role, "content": chat["message"]})
        messages.append({"role": "user", "content": message})

        print("Request messages:", messages)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=700,
            temperature=chatbot_behavior["temperature"],  # Use the temperature from the behavior
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        # Rest of your code...

        ai_message = response.choices[0].message["content"].strip()

    except openai.error.APIError as e:
        print(f"OpenAI API returned an API Error: {e}")
        ai_message = "Error: API Error"

    except openai.error.APIConnectionError as e:
        print(f"Failed to connect to OpenAI API: {e}")
        ai_message = "Error: Connection Error"

    except openai.error.RateLimitError as e:
        print(f"OpenAI API request exceeded rate limit: {e}")
        ai_message = "Error: Rate Limit Exceeded"

        # You can also add additional logic here to further process
        # the response before sending it to the front-end.
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        ai_message = f"Error: Unexpected Error - {e}"


    return jsonify({"message": ai_message})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
