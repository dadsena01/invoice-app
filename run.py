from app import create_app

app = create_app()

if __name__ == "__main__":
    print("Starting Server...")
    app.run(host="127.0.0.1", port=5001, debug=True)