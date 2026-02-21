from flask import Flask, request, redirect, session, render_template_string, send_file
import sqlite3
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Table
import io

app = Flask(__name__)
app.secret_key = "gdgoenka_secret"

# ---------------- DATABASE ----------------

def init_db():
    conn = sqlite3.connect("database.db")

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        password TEXT,
        role TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS complaints(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student TEXT,
        complaint TEXT,
        status TEXT
    )
    """)

    admin = conn.execute("SELECT * FROM users WHERE email='admin@gdgoenka.com'").fetchone()

    if not admin:
        conn.execute("""
        INSERT INTO users(name,email,password,role)
        VALUES('Admin','admin@gdgoenka.com','admin123','admin')
        """)

    conn.commit()
    conn.close()

def db():
    return sqlite3.connect("database.db")

init_db()

# ---------------- LOGIN PAGE ----------------

login_page = """

<!DOCTYPE html>
<html>
<head>

<title>GD GOENKA GRIEVANCE SYSTEM</title>

<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

<style>

body{
height:100vh;
display:flex;
justify-content:center;
align-items:center;
background: linear-gradient(-45deg,#667eea,#764ba2,#6a11cb,#2575fc);
background-size:400% 400%;
animation: gradient 10s ease infinite;
color:white;
}

@keyframes gradient{
0%{background-position:0% 50%;}
50%{background-position:100% 50%;}
100%{background-position:0% 50%;}
}

.card{
padding:30px;
border-radius:15px;
background:rgba(0,0,0,0.6);
}

</style>

</head>

<body>

<div class="card text-center col-4">

<h2 style="color:white; font-weight:bold;">GD GOENKA</h2>
<h4 style="color:white;">GRIEVANCE SYSTEM</h4>

<br>

<form method="post" action="/login">

<input class="form-control mb-3" name="email" placeholder="Email" required>

<input class="form-control mb-3" type="password" name="password" placeholder="Password" required>

<button class="btn btn-primary w-100">Student Login</button>

</form>

<br>

<a href="/admin_login" class="btn btn-danger w-100">Admin Login</a>

<p style="color:white; margin-top:10px; font-size:14px;">
Test Project by Surya
</p>

<br>

<a href="/register" class="btn btn-success w-100">Register</a>

</div>

</body>
</html>

"""

# ---------------- ADMIN LOGIN ----------------

admin_login_page = """

<html>
<head>
<title>Admin Login</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>

<body class="bg-dark text-white d-flex justify-content-center align-items-center vh-100">

<div class="card p-4 col-4 bg-secondary text-center">

<h3>Admin Login</h3>

<form method="post">

<input name="email" class="form-control mb-2" placeholder="Admin Email" required>

<input name="password" type="password" class="form-control mb-2" placeholder="Password" required>

<button class="btn btn-danger w-100">Login</button>

</form>

</div>

</body>
</html>

"""

# ---------------- REGISTER ----------------

register_page = """

<html>
<head>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>

<body class="bg-dark text-white">

<div class="container mt-5 col-4">

<h3>Register</h3>

<form method="post">

<input name="name" class="form-control mb-2" placeholder="Name">

<input name="email" class="form-control mb-2" placeholder="Email">

<input name="password" type="password" class="form-control mb-2" placeholder="Password">

<button class="btn btn-success">Register</button>

</form>

</div>

</body>
</html>

"""

# ---------------- STUDENT DASHBOARD ----------------

student_page = """

<html>
<head>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>

<body class="bg-light">

<nav class="navbar bg-dark navbar-dark">
<div class="container-fluid">
<span>Student Dashboard</span>
<a href="/logout" class="btn btn-danger">Logout</a>
</div>
</nav>

<div class="container mt-4">

<h4>Welcome {{name}}</h4>

<form method="post" action="/submit">
<textarea name="complaint" class="form-control mb-2"></textarea>
<button class="btn btn-primary">Submit Complaint</button>
</form>

<hr>

{% for c in complaints %}
<div class="card p-2 mb-2">
{{c[2]}} — <b>{{c[3]}}</b>
</div>
{% endfor %}

</div>

</body>
</html>

"""

# ---------------- ADMIN DASHBOARD ----------------

admin_page = """

<html>
<head>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>

<body class="bg-dark text-white">

<nav class="navbar navbar-dark bg-black">
<div class="container-fluid">
<span>Admin Dashboard</span>
<a href="/logout" class="btn btn-danger">Logout</a>
</div>
</nav>

<div class="container mt-4">

<form method="get">
<input name="search" class="form-control mb-2" placeholder="Search complaints">
</form>

<canvas id="chart"></canvas>

<script>
new Chart(document.getElementById('chart'),{
type:'line',
data:{
labels:['Pending','Resolved'],
datasets:[{
label:'Complaints',
data:[{{pending}},{{resolved}}],
borderColor:'cyan'
}]
}
});
</script>

<hr>

<a href="/download_pdf" class="btn btn-success mb-3">Download PDF Report</a>

{% for c in complaints %}
<div class="card bg-secondary p-2 mb-2">
{{c[1]}} : {{c[2]}} — {{c[3]}}
{% if c[3]=="Pending" %}
<a href="/resolve/{{c[0]}}" class="btn btn-success btn-sm">Resolve</a>
{% endif %}
</div>
{% endfor %}

</div>

</body>
</html>

"""

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return render_template_string(login_page)

@app.route("/admin_login", methods=["GET","POST"])
def admin_login():

    if request.method=="POST":

        if request.form["email"]=="admin@gdgoenka.com" and request.form["password"]=="admin123":
            session["role"]="admin"
            return redirect("/admin")

    return render_template_string(admin_login_page)

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method=="POST":

        conn=db()

        conn.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
        (request.form["name"],request.form["email"],request.form["password"],"student"))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template_string(register_page)

@app.route("/login", methods=["POST"])
def login():

    conn=db()

    user=conn.execute("SELECT * FROM users WHERE email=? AND password=?",
    (request.form["email"],request.form["password"])).fetchone()

    conn.close()

    if user:
        session["name"]=user[1]
        session["role"]="student"
        return redirect("/student")

    return "Invalid Login"

@app.route("/student")
def student():

    conn=db()

    complaints=conn.execute("SELECT * FROM complaints WHERE student=?",
    (session["name"],)).fetchall()

    conn.close()

    return render_template_string(student_page,name=session["name"],complaints=complaints)

@app.route("/submit", methods=["POST"])
def submit():

    conn=db()

    conn.execute("INSERT INTO complaints(student,complaint,status) VALUES(?,?,?)",
    (session["name"],request.form["complaint"],"Pending"))

    conn.commit()
    conn.close()

    return redirect("/student")

@app.route("/admin")
def admin():

    conn=db()

    search=request.args.get("search","")

    complaints=conn.execute("SELECT * FROM complaints WHERE complaint LIKE ?",
    ("%"+search+"%",)).fetchall()

    pending=conn.execute("SELECT COUNT(*) FROM complaints WHERE status='Pending'").fetchone()[0]

    resolved=conn.execute("SELECT COUNT(*) FROM complaints WHERE status='Resolved'").fetchone()[0]

    conn.close()

    return render_template_string(admin_page,complaints=complaints,pending=pending,resolved=resolved)

@app.route("/resolve/<int:id>")
def resolve(id):

    conn=db()

    conn.execute("UPDATE complaints SET status='Resolved' WHERE id=?",(id,))

    conn.commit()
    conn.close()

    return redirect("/admin")

@app.route("/download_pdf")
def download_pdf():

    conn=db()

    data=conn.execute("SELECT * FROM complaints").fetchall()

    conn.close()

    buffer=io.BytesIO()

    pdf=SimpleDocTemplate(buffer)

    table=Table(data)

    pdf.build([table])

    buffer.seek(0)

    return send_file(buffer,as_attachment=True,download_name="report.pdf")

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

# ---------------- RUN ----------------

app.run(debug=True)