from blogapp import app
if __name__ == '__main__':
    # DEBUG is SET to TRUE. CHANGE FOR PROD
    # db.create_all()

    app.run(port=5000, debug=True)
