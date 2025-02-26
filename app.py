from controllers.main_controller import app

if __name__ == "__main__":
    print("🚀 La aplicación está corriendo en:", os.getenv("REPLIT_APP_URL"))
    app.run(host="0.0.0.0", port=8080)
'''if __name__ == "__main__":
    app.run(debug=True)'''
