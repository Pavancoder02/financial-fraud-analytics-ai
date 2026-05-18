from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
import pymysql
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
import tensorflow.keras as keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.linear_model import LogisticRegression
import joblib
from sklearn.ensemble import GradientBoostingClassifier
import json
from tensorflow.keras.models import load_model


app = Flask(__name__)
app.secret_key = "KG124789900900"

# MySQL Database Configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "frauddetectdb"
}

# Establish database connection
def get_db_connection():
    return pymysql.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database'],
        cursorclass=pymysql.cursors.DictCursor
    )

# Home page
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/remote_user/register", methods=["GET", "POST"])
def remote_user_register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        gender = request.form.get("gender")
        country = request.form.get("country")
        state = request.form.get("state")
        city = request.form.get("city")
        address = request.form.get("address")
        mobile = request.form.get("mobile")
        password = request.form.get("password")

        # Basic validation
        if not (name and email and gender and country and state and city and address and mobile and password):
            flash("All fields are required.", "danger")
            return redirect(url_for("remote_user_register"))
        
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Check for existing user by name, email, or mobile
                query = """
                SELECT * FROM users WHERE name = %s OR email = %s OR mobile = %s
                """
                cursor.execute(query, (name, email, mobile))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    flash("User already exists. Please use a different name, email, or mobile number.", "danger")
                    return redirect(url_for("remote_user_register"))
                
                # Insert new user
                query = """
                INSERT INTO users (name, email, gender, country, state, city, address, mobile, password, role)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'remote_user')
                """
                cursor.execute(query, (name, email, gender, country, state, city, address, mobile, password))
                conn.commit()
                flash("Registration successful! You can now login.", "success")
        except pymysql.MySQLError as e:
            flash(f"Error: {str(e)}", "danger")
        finally:
            conn.close()

    return render_template("remote_user_register.html")


@app.route("/remote_user/login", methods=["GET", "POST"])
def remote_user_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Check user in the database
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                query = "SELECT * FROM users WHERE email = %s AND password = %s AND role = 'remote_user'"
                cursor.execute(query, (email, password))
                user = cursor.fetchone()

                # Debugging: Check the user result
                print(f"User fetched from DB: {user}")

                if user is None:
                    flash("Invalid email or password.", "danger")
                    return redirect(url_for("remote_user_login"))

                # If user exists, store user ID in session (use dictionary key)
                session["user_logged_in"] = True
                session["user_id"] = user['id']  # Access 'id' using the dictionary key
                flash("Login successful!", "success")
                return redirect(url_for("remote_user_dashboard"))
        finally:
            conn.close()

    return render_template("remote_user_login.html")





@app.route("/service_provider/login", methods=["GET", "POST"])
def service_provider_login():
    # If the admin is already logged in, redirect them to the dashboard
    if session.get("admin_logged_in"):
        return redirect(url_for("service_provider_dashboard"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Hardcoded admin credentials
        if username == "admin" and password == "admin":
            session["admin_logged_in"] = True
            flash("Login successful!", "success")
            return redirect(url_for("service_provider_dashboard"))
        else:
            flash("Invalid username or password.", "danger")
            return redirect(url_for("service_provider_login"))

    # If it's a GET request and the user is not logged in, simply show the login form
    return render_template("service_provider_login.html")


@app.route("/service_provider/dashboard")
def service_provider_dashboard():
    if not session.get("admin_logged_in"):
        flash("Please login first.", "danger")
        return redirect(url_for("service_provider_login"))

    return render_template("service_provider_dashboard.html")

@app.route("/service_provider/view_users")
def view_all_remote_users():
    if not session.get("admin_logged_in"):
        flash("Please login first.", "danger")
        return redirect(url_for("service_provider_login"))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = "SELECT name, email, gender, address, mobile, country, state, city FROM users WHERE role='remote_user'"
            cursor.execute(query)
            users = cursor.fetchall()
    finally:
        conn.close()

    return render_template("view_all_remote_users.html", users=users)

@app.route("/logout")
def logout():
    session.clear()
    session.pop("admin_logged_in", None)
    return redirect(url_for("home"))

@app.route("/remote_user/logout")
def user_logout():
    session.clear() 
    return redirect(url_for("home"))

@app.route("/remote_user/dashboard")
def remote_user_dashboard():
    if not session.get("user_logged_in"):
        flash("Please login first.", "danger")
        return redirect(url_for("remote_user_login"))

    return render_template("remote_user_dashboard.html")

@app.route("/remote_user/view_profile")
def view_profile():
    if not session.get("user_logged_in"):
        flash("Please login first.", "danger")
        return redirect(url_for("remote_user_login"))

    user_id = session.get("user_id")
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = "SELECT name, email, gender, address, mobile, country, state, city FROM users WHERE id = %s"
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()
    finally:
        conn.close()

    return render_template("view_profile.html", user=user)

def deep_nn():
    # Load the dataset
    file_path = "updated_synthetic_fraud_dataset.csv"  # Replace with the correct file path
    # Data preprocessing
    data = pd.read_csv(file_path)
    # Convert categorical fields to numeric
    label_encoders = {}
    categorical_columns = ["Gender", "Bank_Name", "Trans_Type", "Location"]

    for col in categorical_columns:
        le = LabelEncoder()
        data[col] = le.fit_transform(data[col])
        label_encoders[col] = le

    # Separate features and target
    X = data.drop(["Fraud", "Fid", "Trans_Date", "Bank_Account"], axis=1)
    y = data["Fraud"]

    # Standardize numerical fields
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Build the deep learning model
    model = Sequential([
        Dense(64, input_dim=X_train.shape[1], activation='relu'),
        Dropout(0.3),
        Dense(32, activation='relu'),
        Dropout(0.2),
        Dense(16, activation='relu'),
        Dense(1, activation='sigmoid')  # Binary classification
    ])

    # Compile the model
    model.compile(optimizer=Adam(learning_rate=0.001), 
                loss='binary_crossentropy', 
                metrics=['accuracy'])

    # Train the model
    history = model.fit(X_train, y_train, 
                        epochs=150, 
                        batch_size=32, 
                        validation_split=0.2)
    # Access training and validation accuracy
    history_dict = history.history

    # Training accuracy
    training_accuracy = history_dict['accuracy']

    # Evaluate the model
    loss, accuracy = model.evaluate(X_test, y_test)
    print(f"Test Loss: {loss:.4f}")
    print(f"Test Accuracy: {accuracy:.4f}")

    # Make predictions
    y_pred = (model.predict(X_test) > 0.5).astype("int32")

    # Display results
    from sklearn.metrics import classification_report, confusion_matrix
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    # Save the model
    model_file_name = 'fraud_detection_dnn_model.h5'
    model.save("fraud_detection_dnn_model.h5") 
    return {"Model Type": "Deep Neural Network", "Accuracy": training_accuracy[len(training_accuracy)-1],
            "Saved Model": model_file_name}

def svm():
    # Load the dataset
    file_path = "updated_synthetic_fraud_dataset.csv"  # Replace with the correct file path
    data = pd.read_csv(file_path)

    # Data preprocessing
    # Convert categorical fields to numeric
    label_encoders = {}
    categorical_columns = ["Gender", "Bank_Name", "Trans_Type", "Location"]

    for col in categorical_columns:
        le = LabelEncoder()
        data[col] = le.fit_transform(data[col])
        label_encoders[col] = le

    # Separate features and target
    X = data.drop(["Fraud", "Fid", "Trans_Date", "Bank_Account"], axis=1)
    y = data["Fraud"]

    # Standardize numerical fields
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train an SVM model
    svm_model = SVC(kernel='rbf', C=1.0, gamma='scale', random_state=42)
    svm_model.fit(X_train, y_train)

    # Evaluate the model
    y_pred = svm_model.predict(X_test)

    # Calculate accuracy
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Test Accuracy: {accuracy:.4f}")

    # Display confusion matrix and classification report
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    model_filename = "svm_fraud_model.pkl"
    joblib.dump(svm_model, model_filename)

    return {"Model Type": "SVM", "Accuracy": accuracy,
            "Saved Model": model_filename}

def logistic_regression():
    # Load the dataset
    file_path = "updated_synthetic_fraud_dataset.csv"  # Replace with the correct file path
    data = pd.read_csv(file_path)

    # Data preprocessing
    # Convert categorical fields to numeric
    label_encoders = {}
    categorical_columns = ["Gender", "Bank_Name", "Trans_Type", "Location"]

    for col in categorical_columns:
        le = LabelEncoder()
        data[col] = le.fit_transform(data[col])
        label_encoders[col] = le

    # Separate features and target
    X = data.drop(["Fraud", "Fid", "Trans_Date", "Bank_Account"], axis=1)
    y = data["Fraud"]

    # Standardize numerical fields
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train a Logistic Regression model
    logistic_model = LogisticRegression(random_state=42, max_iter=1000)
    logistic_model.fit(X_train, y_train)

    # Evaluate the model
    y_pred = logistic_model.predict(X_test)

    # Calculate accuracy
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Test Accuracy: {accuracy:.4f}")

    # Display confusion matrix and classification report
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    # Save the trained logistic regression model to a file
    model_filename = "logistic_regression_fraud_model.pkl"
    joblib.dump(logistic_model, model_filename)
    return {"Model Type": "Logistic Regression", "Accuracy": accuracy,
            "Saved Model": model_filename}

def gradient_boosting():
    # Load the dataset
    file_path = "updated_synthetic_fraud_dataset.csv"  # Replace with the correct file path
    data = pd.read_csv(file_path)

    # Data preprocessing
    # Convert categorical fields to numeric
    label_encoders = {}
    categorical_columns = ["Gender", "Bank_Name", "Trans_Type", "Location"]

    for col in categorical_columns:
        le = LabelEncoder()
        data[col] = le.fit_transform(data[col])
        label_encoders[col] = le

    # Separate features and target
    X = data.drop(["Fraud", "Fid", "Trans_Date", "Bank_Account"], axis=1)
    y = data["Fraud"]

    # Standardize numerical fields
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train a Gradient Boosting Classifier
    gb_model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
    gb_model.fit(X_train, y_train)

    # Evaluate the model
    y_pred = gb_model.predict(X_test)

    # Calculate accuracy
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Test Accuracy: {accuracy:.4f}")

    # Display confusion matrix and classification report
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    # Save the trained model
    model_filename = "gradient_boosting_fraud_model.pkl"
    joblib.dump(gb_model, model_filename)
    print(f"Model saved as {model_filename}")
    return {"Model Type": "Gradient Boosting Classifier", "Accuracy": accuracy,
            "Saved Model": model_filename}


@app.route("/service_provider/browse_datasets")
def browse_datasets():
    if not session.get("admin_logged_in"):
        flash("Please login first.", "danger")
        return redirect(url_for("service_provider_login"))

    dnn_response = deep_nn()
    print(dnn_response)
    svm_response = svm()
    print(svm_response)
    lr_response = logistic_regression()
    print(lr_response)
    g_response = gradient_boosting()
    print(g_response)
    # Combine all models into a list
    all_models = [dnn_response, svm_response, lr_response, g_response]

    # Save combined models as a single JSON file
    json_file_path = "model_results.json"
    with open(json_file_path, "w") as json_file:
        json.dump(all_models, json_file, indent=4)

    return render_template("browse_datasets_accuracy_view.html")

@app.route("/service_provider/view_train_test_accuracy_bar_chart")
def view_train_test_accuracy_bar_chart():
    if not session.get("admin_logged_in"):
        flash("Please login first.", "danger")
        return redirect(url_for("service_provider_login"))
    # Load model results from the JSON file
    with open('model_results.json', 'r') as f:
        model_results = json.load(f)
    # Extract model types and accuracies
    model_types = [model['Model Type'] for model in model_results]
    accuracies = [model['Accuracy'] for model in model_results]

    
    # Pass the data to the template
    return render_template('view_train_test_accuracy_bar_chart.html', model_types=model_types, accuracies=accuracies)

@app.route("/service_provider/view_train_test_accuracy_results")
def view_train_test_accuracy_results():
    if not session.get("admin_logged_in"):
        flash("Please login first.", "danger")
        return redirect(url_for("service_provider_login"))
    # Load model results from the JSON file
    with open('model_results.json', 'r') as f:
        model_results = json.load(f)
    # Extract model types and accuracies
    model_types = [model['Model Type'] for model in model_results]
    accuracies = [model['Accuracy'] for model in model_results]

    
    # Pass the data to the template
    return render_template('view_train_test_accuracy_results.html', model_types=model_types, accuracies=accuracies)

@app.route("/remote_user/find_transaction", methods=["GET", "POST"])
def find_transaction():
    if not session.get("user_logged_in"):
        flash("Please login first.", "danger")
        return redirect(url_for("remote_user_login"))

    if request.method == "POST":
        fid = request.form.get("fid")
        gender = request.form.get("gender")
        age = request.form.get("age")
        bank_account_type = request.form.get("bank_account_type")
        bank_name = request.form.get("bank_name")
        transaction_amount = request.form.get("transaction_amount")
        transaction_number = request.form.get("transaction_number")
        balance = request.form.get("balance")
        transaction_type = request.form.get("transaction_type")
        transaction_date = request.form.get("transaction_date")
        location = request.form.get("location")

        # Load model results from the JSON file
        with open('model_results.json', 'r') as f:
            model_results = json.load(f)

        # Find the model with the highest accuracy
        highest_accuracy_model = max(model_results, key=lambda x: x['Accuracy'])
        
        # Extract details
        model_type = highest_accuracy_model['Model Type']
        accuracy = highest_accuracy_model['Accuracy']
        saved_model = highest_accuracy_model['Saved Model']
        df = pd.DataFrame({"Fid": [fid], "Gender": [gender], "Age": [age],
                           "Bank_Name": [bank_name], "Trans_Amount": [transaction_amount],
                           "Transno": [transaction_number], "Balance": [balance], "Trans_Type": [transaction_type],
                           "Trans_Date":[transaction_date],"Location":[location]})
        
        # Convert categorical fields to numeric
        label_encoders = {}
        categorical_columns = ["Gender", "Bank_Name", "Trans_Type", "Location"]

        for col in categorical_columns:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col])
            label_encoders[col] = le

        # Separate features and target
        X = df.drop(["Fid", "Trans_Date"], axis=1)
        # Standardize numerical fields
        scaler = StandardScaler()
        X = scaler.fit_transform(X)

        # Logic for predicting the financial transaction type can go here
        if model_type == 'Deep Neural Network':
            # Load the model
            model = load_model(saved_model)
        else:
            model = joblib.load(saved_model)
        predicted = round(model.predict(X)[0][0], 1)
        print("-------------------------------")
        print(predicted)
        print(round(predicted))

        threshold = 0.5
        print(predicted)
        if predicted >= threshold:
            predicted_type = "Fraud"
        else:
            predicted_type = "Not Fraud"
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Check for existing user by name, email, or mobile
                # Insert new user
                # Insert data into the table
                query = """
                INSERT INTO transactions (
                    fid, gender, age, bank_account_type, bank_name, 
                    transaction_amount, transaction_number, balance, 
                    transaction_type, transaction_date, location, trans_detection_type
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (fid, gender, age, bank_account_type, bank_name, 
                        transaction_amount, transaction_number, balance, 
                        transaction_type, transaction_date, location, predicted_type)
                cursor.execute(query, values)
                conn.commit()
                # Close connection
                cursor.close()
                conn.close()
            flash(f"Prediction: The transaction type is {predicted_type}.", "success")
            return render_template("find_transaction.html", predicted_type=predicted_type)
        except Exception as ex:
            flash(f"Prediction: DB Issue.", "Failed")
            return render_template("find_transaction.html", predicted_type="DB Issue")
       

    return render_template("find_transaction.html")

@app.route("/service_provider/view_financial_trans_detection_type")
def view_financial_trans_detection_type():
    if not session.get("admin_logged_in"):
        flash("Please login first.", "danger")
        return redirect(url_for("service_provider_login"))
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = "SELECT fid, gender, age, bank_account_type, bank_name, transaction_amount, transaction_number, balance, transaction_type, transaction_date, location, trans_detection_type FROM transactions"
            cursor.execute(query)
            trans_detection_type = cursor.fetchall()
    finally:
        conn.close()

   
    return render_template('view_financial_trans_detection_type.html', trans_detection_type=trans_detection_type)


# API route to serve JSON data
@app.route('/api/models')
def get_models():
    # Load model results from the JSON file
    with open('model_results.json', 'r') as f:
        model_results = json.load(f)
    return jsonify(model_results)

if __name__ == "__main__":
    app.run(debug=True)
