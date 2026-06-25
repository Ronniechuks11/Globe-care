from flask import Flask, request, redirect, render_template, session
import sqlite3

app = Flask(__name__)

app.secret_key = "globecare_secret"

conn = sqlite3.connect("globecare.db", check_same_thread=False)

conn.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
member_id TEXT,
name TEXT,
email TEXT,
phone TEXT,
password TEXT
)
""")

@app.route("/")
def home():
    return render_template("index.html")
    
@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/signup")
def signup_page():
    return render_template("signup.html")
    
@app.route("/login", methods=["POST"])
def login():

    email = request.form["email"]
    password = request.form["password"]

    cursor = conn.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, password)
    )

    user = cursor.fetchone()

    if user:

        session["user_id"] = user[0]

        return redirect("/user_dashboard")
    return "<h1>Invalid Email or Password</h1>"

@app.route("/register", methods=["POST"])
def register():

    name = request.form["name"]
    email = request.form["email"]
    phone = request.form["phone"]
    password = request.form["password"]
    confirm_password = request.form["confirm_password"]

    if not name or not email or not phone or not password:
        return "<h1>All fields are required</h1>"

    if password != confirm_password:
        return "<h1>Passwords do not match</h1>"

    cursor = conn.execute(
    "SELECT * FROM users WHERE email=?",
    (email,)
)

    existing_user = cursor.fetchone()

    if existing_user:
        return "<h1>Email already registered</h1>"

    if len(password) < 6:
        return "<h1>Password must be at least 6 characters</h1>"
    
    cursor = conn.execute(
    "SELECT COUNT(*) FROM users"
)

    count = cursor.fetchone()[0]

    member_id = f"GC{count + 1:04d}"
    
    conn.execute(
    "INSERT INTO users(member_id,name,email,phone,password) VALUES(?,?,?,?,?)",
    (member_id,name,email,phone,password)
)

    conn.commit()

    return f"""
    <h1>Registration Successful</h1>

    <p>{name}</p>

    <p>Member ID: {member_id}</p>

    <a href='/signup'>Go To Login</a>
    """

@app.route("/users")
def users():

    cursor = conn.execute(
    "SELECT member_id,name,email,phone FROM users"
)

    users = cursor.fetchall()

    total = len(users)

    output = f"""
<h1>Registered Users</h1>

<h3>Total Users: {total}</h3>

<a href='/'>Back To Dashboard</a>

<hr>
"""

    for user in users:

        output += f"""
        <p>
        Member ID: {user[0]}<br>
        Name: {user[1]}<br> 
        Email: {user[2]}<br>
        Phone: {user[3]}<br><br>

        <a href='/delete/{user[0]}'>Delete User</a>
        <br><br>

        <a href='/edit/{user[0]}'>Edit User</a>
        </p>
        <hr>
        """

    return output


@app.route("/delete/<int:user_id>")
def delete_user(user_id):

    conn.execute(
        "DELETE FROM users WHERE id=?",
        (user_id,)
    )

    conn.commit()

    return """
    <h1>User Deleted Successfully</h1>

    <a href='/users'>Back To Users</a>
    """

@app.route("/dashboard")
def dashboard():

    cursor = conn.execute(
        "SELECT COUNT(*) FROM users"
    )

    total = cursor.fetchone()[0]

    cursor = conn.execute(
        "SELECT name,email FROM users ORDER BY id DESC LIMIT 5"
    )

    latest = cursor.fetchall()

    output = f"""
    <h1>Globe-Care Dashboard</h1>

    <h2>Total Registered Users: {total}</h2>

    <a href='/users'>Manage Users</a>

    <br><br>

    <a href='/'>Logout</a>

    <hr>
    
    <form action="/search">

<input type="text" name="q" placeholder="Search User">

<button type="submit">Search</button>

</form>

<hr>

    <h2>Latest Registrations</h2>
    """

    for user in latest:

        output += f"""
        <p>
        {user[0]}<br>
        {user[1]}
        </p>
        """

    return output

@app.route("/search")
def search():

    keyword = request.args.get("q", "")

    cursor = conn.execute(
        "SELECT id,name,email,phone FROM users WHERE name LIKE ?",
        (f"%{keyword}%",)
    )

    users = cursor.fetchall()

    output = """
    <h1>Search Results</h1>

    <a href='/dashboard'>Back To Dashboard</a>

    <hr>
    """

    for user in users:

        output += f"""
        <p>
        Name: {user[1]}<br>
        Email: {user[2]}<br>
        Phone: {user[3]}
        </p>
        <hr>
        """

    return output


@app.route("/edit/<int:user_id>")
def edit_user(user_id):

    cursor = conn.execute(
        "SELECT id,name,email,phone FROM users WHERE id=?",
        (user_id,)
    )

    user = cursor.fetchone()

    return f"""
    <h1>Edit User</h1>

    <form method="POST" action="/update/{user[0]}">

        Name:<br>
        <input type="text" name="name" value="{user[1]}"><br><br>
 
        Email:<br>
        <input type="text" name="email" value="{user[2]}"><br><br>

        Phone:<br>
        <input type="text" name="phone" value="{user[3]}"><br><br>

        <button type="submit">Update User</button>

    </form>
    """


@app.route("/update/<int:user_id>", methods=["POST"])
def update_user(user_id):

    name = request.form["name"]
    email = request.form["email"]
    phone = request.form["phone"]

    conn.execute(
        """
        UPDATE users
        SET name=?, email=?, phone=?
        WHERE id=?
        """,
        (name, email, phone, user_id)
    )

    conn.commit()

    return redirect("/users")

@app.route("/user_dashboard")
def user_dashboard():

    user_id = session.get("user_id")

    if not user_id:
        return redirect("/signup")

    cursor = conn.execute(
        "SELECT member_id,name,email,phone FROM users WHERE id=?",
        (user_id,)
    )

    user = cursor.fetchone()

    return render_template(
        "dashboard.html",
        user=user
    )

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")
        
if __name__ == "__main__":
    app.run(debug=True)