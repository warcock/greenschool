from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bcrypt import hashpw, gensalt, checkpw
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret-key"

# MongoDB setup
connection_string = "mongodb+srv://hello:helloskibidimark123@cluster0.tzi8u.mongodb.net/myDatabase?retryWrites=true&w=majority"
client = MongoClient(connection_string)
db = client['green_school']
collection = db['users']

@app.errorhandler(404)
def page_not_found(e):
    return "Page not found. Check your route and template.", 404

@app.errorhandler(500)
def internal_error(e):
    return f"Internal server error: {str(e)}", 500

# Routes

@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("main"))
    return render_template("login.html")  # Corrected to use the route name directly.

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"].encode("utf-8")

        user = collection.find_one({"username": username})
        if user and checkpw(password, user["password"]):
            session["username"] = username
            return redirect(url_for("profile"))  # Redirect to /main after login
        flash("Invalid username or password")
    return render_template("login.html")  # Correct to use the template properly.

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"].encode("utf-8")

        if collection.find_one({"username": username}):
            flash("Username already exists!")
            return render_template("signup.html")  # No change

        hashed_password = hashpw(password, gensalt())
        collection.insert_one({
            "username": username,
            "password": hashed_password,
            "points": 0,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "website"
        })
        flash("Signup successful!")
        return redirect(url_for("login"))  # Redirect to login page after successful signup.
    return render_template("signup.html")  # Correct to use template.

@app.route("/main")
def main():
    print("Main URL:", url_for("main"))  # Check the generated URL
    if "username" not in session:
        return redirect(url_for("login"))
    user = collection.find_one({"username": session["username"]})
    leaderboard = list(collection.find().sort("points", -1))
    return render_template("index.html", user=user, leaderboard=leaderboard)

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("index"))  # Redirect to the index (login page) after logging out.

@app.route("/help")
def help_page():
    return render_template("help.html")  # Correct template

@app.route('/leaderboard')
def leaderboard():
    leaderboard_data = list(collection.find().sort("points", -1))
    for rank, user in enumerate(leaderboard_data, start=1):
        user['rank'] = rank
        user['username'] = user.get('username', 'Unknown')  # Default to 'Unknown' if username is missing
        user['points'] = user.get('points', 0)  # Default to 0 if points are missing
    return render_template('leaderboard.html', leaderboard=leaderboard_data)

@app.route("/profile")
def profile():
    if "username" not in session:
        return redirect(url_for("login"))  # If not logged in, redirect to login page
    
    username = session["username"]
    user = collection.find_one({"username": username})
    
    if user:
        # Fetch user data
        user_name = user["username"]
        points = user["points"]
        
        # Get the leaderboard and find the user's rank
        leaderboard = list(collection.find().sort("points", -1))  # Sort by points in descending order
        rank = get_user_rank(username, leaderboard)
        
        # Pass data to the profile template
        return render_template("profile.html", user_name=user_name, points=points, rank=rank)
    else:
        return "User not found", 404

def get_user_rank(username, leaderboard):
    # Check if leaderboard is not empty
    if not leaderboard:
        return "No leaderboard data found"
    
    # Iterate through the leaderboard to find the rank based on points
    for index, user in enumerate(leaderboard):
        if isinstance(user, dict) and "username" in user:
            if user["username"] == username:
                return index + 1  # Rank is 1-based (e.g., first place = 1)
    
    # Return None if user is not found in the leaderboard
    return "User not in leaderboard"
    
@app.route('/qrscan')
def qrscan():
    return render_template('qrscan.html')  # Correct template

if __name__ == '__main__':
    app.run(debug=True)
