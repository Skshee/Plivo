# Plivo IVR Demo with Flask

This project is a Flask-based Interactive Voice Response (IVR) demo utilizing the Plivo Voice API. It implements an outbound call trigger, a hardcoded OTP verification via DTMF input, and a multi-level IVR system with branching for different languages, audio playback, and call forwarding.

## Prerequisites

1.  Python 3.7+ installed.
2.  A [Plivo account](https://www.plivo.com/).
3.  [Ngrok](https://ngrok.com/) to expose the local Flask server to the internet so Plivo can send webhooks to it.

## Features implemented

-   **Outbound call trigger** via `/make-call` API.
-   **OTP Authentication**: Prompts for a 4-digit OTP using DTMF (`1503`). Retries on incorrect input.
-   **Multi-level IVR**:
    -   **Level 1**: Language selection (1 for English, 2 for Spanish).
    -   **Level 2**: Action selection (1 to play audio, 2 to forward the call to an associate).
-   **XML Webhooks**: Dynamic generation of Plivo XML instructions like `<GetInput>`, `<Speak>`, `<Play>`, and `<Dial>`.
-   **Secure credentials**: Use of `.env` files to prevent hardcoding sensitive information.

## Setup Instructions

### 1. Install Dependencies

In your terminal, navigate to the project directory and install the required Python packages:

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the root directory (you can copy `.env.example`):

```bash
cp .env.example .env
```

Open the `.env` file and fill in your details:

```env
PLIVO_AUTH_ID=your_plivo_auth_id
PLIVO_AUTH_TOKEN=your_plivo_auth_token
PLIVO_NUMBER=+918035736861
TARGET_NUMBER=+91XXXXXXXXXX # The number you want to call
FORWARD_NUMBER=+91YYYYYYYYYY # The associate's number to forward the call to
BASE_URL=https://your-ngrok-url.app # Don't add a trailing slash
```

*Important: Do not commit your `.env` file to version control (e.g., GitHub).*

### 3. Start Ngrok

Plivo needs a publicly accessible HTTPS URL to send webhooks when the call is answered or DTMF inputs are provided.

Run Ngrok to expose port 5000:

```bash
ngrok http 5000
```

Copy the `https://...ngrok-free.app` URL and update the `BASE_URL` in your `.env` file.

### 4. Start the Flask App

In a new terminal window, start the Flask server:

```bash
python app.py
```

## How to Run the Demo

1.  Trigger the outbound call by making a `POST` request to the `/make-call` endpoint. You can use curl, Postman, or any API client:

    ```bash
    curl -X POST http://localhost:5000/make-call
    ```

2.  **The Call Flow**:
    -   Your `TARGET_NUMBER` will receive a call from your `PLIVO_NUMBER`.
    -   When you answer, you will be prompted: *"Welcome to the Plivo Interactive Voice Response demo. Please enter your four digit O T P."*
    -   **Wrong OTP**: Enter any 4 digits other than `1503`. The system will say *"Incorrect O T P. Please try again."* and prompt you again.
    -   **Correct OTP**: Enter `1503`. The system will say *"O T P verified successfully."*
    -   **Language Menu**: The system will prompt: *"Press 1 for English. Press 2 for Spanish."*
    -   **Action Menu**: Based on the language selected, it will prompt: *"Press 1 to play an audio message. Press 2 to forward the call to an associate."*
    -   **Audio Playback**: If you press `1`, an MP3 file will be played, followed by *"Thank you for using the demo. Goodbye."*
    -   **Call Forwarding**: If you press `2`, the system will forward the call to the `FORWARD_NUMBER` specified in your `.env`.

## Note on Demo Video

The requirements requested a demo video showing the full call flow (wrong OTP, correct OTP, menu navigation, audio, and call forwarding). Because this AI agent is text-based and its browser capabilities are limited to interacting with web pages (and cannot record physical phone calls or receive real PSTN audio natively), a video recording of the actual phone interaction cannot be generated.

To verify the flow, please run the application using your Plivo credentials and call a test phone device you possess. You can observe the webhook interactions in your Flask console and listen to the IVR prompts on the phone!
