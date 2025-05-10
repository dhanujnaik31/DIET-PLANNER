from flask import Flask, render_template, request
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# Load dataset
data = pd.read_csv('./dataset/food_exercise.csv')

# Ensure numeric columns are of correct type
data['Calories'] = pd.to_numeric(data['Calories'], errors='coerce')
data['Proteins'] = pd.to_numeric(data['Proteins'], errors='coerce')
data['Fats'] = pd.to_numeric(data['Fats'], errors='coerce')
data['Carbohydrates'] = pd.to_numeric(data['Carbohydrates'], errors='coerce')

# BMR calculation
def calculate_bmr(weight, height, age, gender):
    if gender.lower() == 'male':
        return 10 * weight + 6.25 * height - 5 * age + 5
    else:
        return 10 * weight + 6.25 * height - 5 * age - 161

# Nutritional chart
def generate_food_graph(proteins, fats, carbohydrates):
    labels = ['Proteins', 'Fats', 'Carbohydrates']
    values = [proteins, fats, carbohydrates]

    plt.figure(figsize=(5, 3))
    plt.plot(labels, values, marker='o', color='b', linestyle='-', linewidth=2, markersize=8)
    plt.title('Nutritional Breakdown')
    plt.xlabel('Nutrient')
    plt.ylabel('Amount (g)')
    plt.grid(True)

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{img_base64}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    if request.method == 'POST':
        age = int(request.form['age'])
        height = int(request.form['height'])
        weight = int(request.form['weight'])
        gender = request.form['gender']
        allergies = request.form['allergies'].lower()

        bmr = calculate_bmr(weight, height, age, gender)
        lower_bound = (bmr * 0.9) / 4
        upper_bound = (bmr * 1.1) / 4

        # Filter by allergies if provided
        if allergies.strip():
            filtered_data = data[~data['Name'].str.lower().str.contains(allergies, na=False)]
        else:
            filtered_data = data

        # Filter by calories
        filtered_data = filtered_data[
            (filtered_data['Calories'] >= lower_bound) & (filtered_data['Calories'] <= upper_bound)
        ]

        # Pick up to 5 recommendations
        filtered_foods = filtered_data['Name'].sample(n=min(5, len(filtered_data)))

        recommendations = []
        for food_name in filtered_foods:
            food_row = filtered_data[filtered_data['Name'] == food_name].iloc[0]
            graph_url = generate_food_graph(food_row['Proteins'], food_row['Fats'], food_row['Carbohydrates'])

            recommendations.append({
                'Name': food_name,
                'Type': food_row['Type'],
                'Calories': food_row['Calories'],
                'Proteins': food_row['Proteins'],
                'Fats': food_row['Fats'],
                'Carbohydrates': food_row['Carbohydrates'],
                'GraphURL': graph_url
            })

        return render_template('recommendations.html', recommendations=recommendations, bmr=round(bmr, 2))

    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)
