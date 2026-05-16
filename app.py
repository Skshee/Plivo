from flask import Flask, request, jsonify, render_template_string
from plivo import RestClient
from plivo import plivoxml
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Constants and Configuration
PLIVO_AUTH_ID = os.environ.get('PLIVO_AUTH_ID')
PLIVO_AUTH_TOKEN = os.environ.get('PLIVO_AUTH_TOKEN')
PLIVO_NUMBER = os.environ.get('PLIVO_NUMBER')
TARGET_NUMBER = os.environ.get('TARGET_NUMBER')
BASE_URL = os.environ.get('BASE_URL') # e.g. https://your-ngrok.app
FORWARD_NUMBER = os.environ.get('FORWARD_NUMBER', '+910000000000') # Number to forward to

# Hardcoded OTP (DDMM)
CORRECT_OTP = "1503"
# Publicly hosted audio URL for Playback
AUDIO_URL = "https://s3.amazonaws.com/plivocloud/music.mp3"

# Initialize Plivo Client
client = None
if PLIVO_AUTH_ID and PLIVO_AUTH_TOKEN:
    client = RestClient(auth_id=PLIVO_AUTH_ID, auth_token=PLIVO_AUTH_TOKEN)

@app.route('/', methods=['GET'])
def index():
    """Serves the simple frontend to trigger the call."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Plivo IVR Demo</title>
        <style>
            body { font-family: 'Inter', sans-serif; display: flex; flex-direction: column; align-items: center; margin-top: 50px; background-color: #f4f7f6; color: #333; }
            .container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-align: center; }
            h1 { color: #2d3748; }
            button { padding: 15px 30px; font-size: 18px; cursor: pointer; background-color: #00b373; color: white; border: none; border-radius: 5px; transition: background-color 0.3s; margin-top: 20px;}
            button:hover { background-color: #009962; }
            #status { margin-top: 20px; font-size: 16px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Plivo IVR Demo</h1>
            <p>Click the button below to initiate an outbound call to your target number.</p>
            <button onclick="makeCall()">Trigger Outbound Call</button>
            <div id="status"></div>
        </div>

        <script>
            function makeCall() {
                const statusDiv = document.getElementById('status');
                statusDiv.innerText = "Initiating call...";
                statusDiv.style.color = "#555";
                
                fetch('/make-call', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if(data.error) {
                            statusDiv.innerText = "Error: " + data.error;
                            statusDiv.style.color = "red";
                        } else {
                            statusDiv.innerText = "Success! Call initiated. Please check your phone.";
                            statusDiv.style.color = "green";
                        }
                    })
                    .catch(error => {
                        statusDiv.innerText = "Failed to trigger call. Check server logs.";
                        statusDiv.style.color = "red";
                    });
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/make-call', methods=['POST'])
def make_call():
    """Initiates an outbound call using Plivo SDK"""
    if not client:
        return jsonify({"error": "Plivo client not initialized. Check credentials in .env file."}), 500
    
    if not BASE_URL:
        return jsonify({"error": "BASE_URL is not set. Please set it to your ngrok URL."}), 500

    try:
        response = client.calls.create(
            from_=PLIVO_NUMBER,
            to_=TARGET_NUMBER,
            answer_url=f"{BASE_URL}/answer",
            answer_method='POST'
        )
        return jsonify({
            "message": "Call initiated successfully", 
            "response": str(response)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/answer', methods=['GET', 'POST'])
def answer():
    """Initial webhook when call is answered. Returns XML asking for OTP."""
    response = plivoxml.ResponseElement()
    
    # Use GetInput to prompt for OTP via DTMF
    get_input = plivoxml.GetInputElement(
        action=f"{BASE_URL}/verify-otp",
        method="POST",
        input_type="dtmf",
        digit_end_timeout=5,
        num_digits=4
    )
    get_input.add(plivoxml.SpeakElement(
        "Welcome to the Plivo Interactive Voice Response demo. Please enter your four digit O T P.", 
        language="en-US", 
        voice="Polly.Joanna"
    ))
    response.add(get_input)
    
    # If no input is received, loop back to the same prompt
    response.add_speak("We did not receive any input.", language="en-US", voice="Polly.Joanna")
    response.add_redirect(f"{BASE_URL}/answer", method="POST")
    
    return response.to_string(), 200, {'Content-Type': 'application/xml'}

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Verifies entered digits and redirects to language menu if correct."""
    digits = request.form.get('Digits')
    response = plivoxml.ResponseElement()
    
    if digits == CORRECT_OTP:
        # OTP is correct, proceed to Level 1 IVR
        response.add_speak("O T P verified successfully.", language="en-US", voice="Polly.Joanna")
        response.add_redirect(f"{BASE_URL}/language-menu", method="POST")
    else:
        # Incorrect OTP, retry
        response.add_speak("Incorrect O T P. Please try again.", language="en-US", voice="Polly.Joanna")
        response.add_redirect(f"{BASE_URL}/answer", method="POST")
        
    return response.to_string(), 200, {'Content-Type': 'application/xml'}

@app.route('/language-menu', methods=['POST'])
def language_menu():
    """Level 1 IVR: Language selection menu."""
    response = plivoxml.ResponseElement()
    get_input = plivoxml.GetInputElement(
        action=f"{BASE_URL}/language-choice",
        method="POST",
        input_type="dtmf",
        digit_end_timeout=5,
        num_digits=1
    )
    get_input.add(plivoxml.SpeakElement("Press 1 for English. Press 2 for Spanish.", language="en-US", voice="Polly.Joanna"))
    response.add(get_input)
    
    # Retry logic
    response.add_speak("We did not receive any input.", language="en-US", voice="Polly.Joanna")
    response.add_redirect(f"{BASE_URL}/language-menu", method="POST")
    
    return response.to_string(), 200, {'Content-Type': 'application/xml'}

@app.route('/language-choice', methods=['POST'])
def language_choice():
    """Handles language selection."""
    digits = request.form.get('Digits')
    response = plivoxml.ResponseElement()
    
    if digits == '1':
        # English chosen
        response.add_redirect(f"{BASE_URL}/action-menu?lang=en", method="POST")
    elif digits == '2':
        # Spanish chosen
        response.add_redirect(f"{BASE_URL}/action-menu?lang=es", method="POST")
    else:
        # Invalid selection
        response.add_speak("Invalid input.", language="en-US", voice="Polly.Joanna")
        response.add_redirect(f"{BASE_URL}/language-menu", method="POST")
        
    return response.to_string(), 200, {'Content-Type': 'application/xml'}

@app.route('/action-menu', methods=['POST'])
def action_menu():
    """Level 2 IVR: Action selection menu based on language."""
    lang = request.args.get('lang', 'en')
    response = plivoxml.ResponseElement()
    
    get_input = plivoxml.GetInputElement(
        action=f"{BASE_URL}/action-choice",
        method="POST",
        input_type="dtmf",
        digit_end_timeout=5,
        num_digits=1
    )
    
    if lang == 'es':
        get_input.add(plivoxml.SpeakElement("Presione uno para reproducir un mensaje de audio. Presione dos para desviar la llamada a un asociado.", language="es-ES", voice="Polly.Conchita"))
    else:
        get_input.add(plivoxml.SpeakElement("Press 1 to play an audio message. Press 2 to forward the call to an associate.", language="en-US", voice="Polly.Joanna"))
    
    response.add(get_input)
    
    # Retry logic
    response.add_speak("We did not receive any input.", language="en-US", voice="Polly.Joanna")
    response.add_redirect(f"{BASE_URL}/action-menu?lang={lang}", method="POST")
        
    return response.to_string(), 200, {'Content-Type': 'application/xml'}

@app.route('/action-choice', methods=['POST'])
def action_choice():
    """Handles audio playback or call forwarding."""
    digits = request.form.get('Digits')
    response = plivoxml.ResponseElement()
    
    if digits == '1':
        # Play audio message
        response.add_speak("Playing audio message.", language="en-US", voice="Polly.Joanna")
        response.add_play(AUDIO_URL)
        response.add_speak("Thank you for using the demo. Goodbye.", language="en-US", voice="Polly.Joanna")
    elif digits == '2':
        # Forward call
        response.add_speak("Forwarding your call.", language="en-US", voice="Polly.Joanna")
        response.add_wait(length=1)
        dial = plivoxml.DialElement(caller_id=PLIVO_NUMBER)
        dial.add(plivoxml.NumberElement(FORWARD_NUMBER))
        response.add(dial)
    else:
        # Invalid selection
        response.add_speak("Invalid input.", language="en-US", voice="Polly.Joanna")
        # We need to know language to redirect back correctly, assuming English here or fallback
        response.add_redirect(f"{BASE_URL}/action-menu?lang=en", method="POST")
        
    return response.to_string(), 200, {'Content-Type': 'application/xml'}

if __name__ == '__main__':
    # Run the Flask app
    app.run(port=5000, debug=True)
